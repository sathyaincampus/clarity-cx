"""Base Agent — Abstract base class for all Clarity CX agents"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import logging
import time


class BaseClarityAgent(ABC):
    """Abstract base class for all Clarity CX agents"""

    name: str = "BaseAgent"
    description: str = "Base agent"
    system_prompt: str = ""

    def __init__(self):
        self.logger = logging.getLogger(f"clarity.agent.{self.name}")

    @abstractmethod
    async def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process state and return updates.

        Args:
            state: Current pipeline state dictionary

        Returns:
            Dictionary of state updates to merge
        """
        pass

    async def safe_process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process with error handling and timing.

        Wraps process() with logging, timing, and error handling.
        """
        start_time = time.time()
        self.logger.info(f"[{self.name}] Starting processing...")

        try:
            result = await self.process(state)
            elapsed_ms = int((time.time() - start_time) * 1000)
            self.logger.info(f"[{self.name}] Completed in {elapsed_ms}ms")

            # Add agent output to accumulated list
            agent_output = {
                "agent": self.name,
                "status": "success",
                "latency_ms": elapsed_ms,
                "result": result,
            }
            return {
                **result,
                "agent_outputs": [agent_output],
            }

        except Exception as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            self.logger.error(f"[{self.name}] Failed after {elapsed_ms}ms: {e}")

            error_output = {
                "agent": self.name,
                "status": "error",
                "latency_ms": elapsed_ms,
                "error": str(e),
            }
            return {
                "agent_outputs": [error_output],
                "error_log": [f"[{self.name}] {str(e)}"],
            }
