"""LLM Provider Adapters — Multi-provider support for OpenAI, Anthropic, Google"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, AsyncIterator, Optional
import logging
import json

logger = logging.getLogger(__name__)


class LLMAdapter(ABC):
    """Abstract base for LLM providers"""

    provider_name: str
    model: str

    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        system: str = None,
        **kwargs,
    ) -> str:
        """Send a chat message and get a response"""
        pass

    @abstractmethod
    async def chat_with_functions(
        self,
        messages: List[Dict[str, str]],
        functions: List[Dict[str, Any]],
        system: str = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Chat with function calling for structured output"""
        pass

    async def stream(
        self,
        messages: List[Dict[str, str]],
        system: str = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """Stream a chat response token by token (optional override)"""
        response = await self.chat(messages, system, **kwargs)
        yield response


class OpenAIAdapter(LLMAdapter):
    """OpenAI GPT adapter"""

    provider_name = "openai"

    def __init__(self, model: str, api_key: str):
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def chat(self, messages, system=None, **kwargs):
        msgs = messages.copy()
        if system:
            msgs.insert(0, {"role": "system", "content": system})

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=msgs,
            temperature=kwargs.get("temperature", 0.3),
            max_tokens=kwargs.get("max_tokens", 4096),
        )
        return response.choices[0].message.content

    async def chat_with_functions(self, messages, functions, system=None, **kwargs):
        msgs = messages.copy()
        if system:
            msgs.insert(0, {"role": "system", "content": system})

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=msgs,
            tools=[{"type": "function", "function": f} for f in functions],
            tool_choice="auto",
            temperature=kwargs.get("temperature", 0.3),
        )

        message = response.choices[0].message
        if message.tool_calls:
            tool_call = message.tool_calls[0]
            return {
                "function_name": tool_call.function.name,
                "arguments": json.loads(tool_call.function.arguments),
            }
        return {"content": message.content}

    async def stream(self, messages, system=None, **kwargs):
        msgs = messages.copy()
        if system:
            msgs.insert(0, {"role": "system", "content": system})

        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=msgs,
            stream=True,
            temperature=kwargs.get("temperature", 0.3),
        )
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class AnthropicAdapter(LLMAdapter):
    """Anthropic Claude adapter"""

    provider_name = "anthropic"

    def __init__(self, model: str, api_key: str):
        from anthropic import AsyncAnthropic
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model

    async def chat(self, messages, system=None, **kwargs):
        response = await self.client.messages.create(
            model=self.model,
            system=system or "",
            messages=messages,
            max_tokens=kwargs.get("max_tokens", 4096),
            temperature=kwargs.get("temperature", 0.3),
        )
        return response.content[0].text

    async def chat_with_functions(self, messages, functions, system=None, **kwargs):
        tools = [
            {
                "name": f["name"],
                "description": f.get("description", ""),
                "input_schema": f["parameters"],
            }
            for f in functions
        ]
        response = await self.client.messages.create(
            model=self.model,
            system=system or "",
            messages=messages,
            tools=tools,
            max_tokens=kwargs.get("max_tokens", 4096),
        )
        for block in response.content:
            if block.type == "tool_use":
                return {
                    "function_name": block.name,
                    "arguments": block.input,
                }
        return {"content": response.content[0].text}


class GoogleAdapter(LLMAdapter):
    """Google Gemini adapter"""

    provider_name = "google"

    def __init__(self, model: str, api_key: str):
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self.genai_model = genai.GenerativeModel(model)
        self.model = model

    async def chat(self, messages, system=None, **kwargs):
        history = []
        for msg in messages[:-1]:
            history.append({
                "role": "user" if msg["role"] == "user" else "model",
                "parts": [msg["content"]],
            })

        chat = self.genai_model.start_chat(history=history)
        prompt = messages[-1]["content"]
        if system:
            prompt = f"System: {system}\n\n{prompt}"

        response = await chat.send_message_async(prompt)
        return response.text

    async def chat_with_functions(self, messages, functions, system=None, **kwargs):
        # Gemini function calling via simple prompt-based approach
        func_descriptions = json.dumps(functions, indent=2)
        enhanced_prompt = (
            f"You have access to these functions:\n{func_descriptions}\n\n"
            f"Respond with a JSON object containing 'function_name' and 'arguments' "
            f"if a function should be called. Otherwise respond normally.\n\n"
            f"{messages[-1]['content']}"
        )
        response = await self.chat(
            [{"role": "user", "content": enhanced_prompt}],
            system=system,
        )
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"content": response}


def get_llm_adapter(provider: str, model: str, api_key: str) -> LLMAdapter:
    """Factory function for LLM adapters"""
    adapters = {
        "openai": OpenAIAdapter,
        "anthropic": AnthropicAdapter,
        "google": GoogleAdapter,
    }
    if provider not in adapters:
        raise ValueError(
            f"Unknown provider: {provider}. "
            f"Supported: {', '.join(adapters.keys())}"
        )
    logger.info(f"Creating {provider} adapter with model {model}")
    return adapters[provider](model, api_key)


# Supported models reference
SUPPORTED_MODELS = {
    "openai": [
        {"id": "gpt-4o", "name": "GPT-4o", "best_for": "Summarization, scoring"},
        {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "best_for": "Fast analysis"},
        {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "best_for": "Complex tasks"},
    ],
    "anthropic": [
        {"id": "claude-sonnet-4-20250514", "name": "Claude Sonnet 4", "best_for": "Detailed analysis"},
        {"id": "claude-3-haiku-20240307", "name": "Claude 3 Haiku", "best_for": "Fast scoring"},
    ],
    "google": [
        {"id": "gemini-2.0-flash", "name": "Gemini 2.0 Flash", "best_for": "Budget analysis"},
        {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro", "best_for": "Long transcripts"},
    ],
}
