"""
Seed Database — Populates SQLite with pre-analyzed call records.

Usage:
    python scripts/seed_database.py

This reads all transcripts from data/sample_transcripts/samples.json,
generates realistic pre-computed analyses, and inserts them via Database.save_analysis()
so the dashboard, history, and trends pages are populated for demos.
"""

import sys
import json
import random
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import Database

# ── Pre-computed analysis data keyed by call_id ──────────────────────────────

ANALYSES = {
    "SAMPLE-001": {
        "agent_name": "Sarah",
        "caller_id": "C-2024-1234",
        "duration_seconds": 96,
        "summary": {
            "summary": "Customer called about delayed order ORD-5678 needed for a weekend event. Agent identified carrier delay at regional hub and offered free expedited replacement. Customer accepted and was satisfied.",
            "key_points": ["Order delayed due to carrier weather issue", "Replacement shipped with next-day delivery at no cost", "New tracking number sent via email within 1 hour"],
            "action_items": ["Ship replacement within 24 hours", "Send tracking number to customer email", "Flag carrier for recurring delays"],
            "customer_intent": "Order status inquiry",
            "resolution_status": "resolved",
            "topics": ["shipping", "order_delay", "replacement"],
            "sentiment_trajectory": "negative_to_positive",
        },
        "quality_scores": {
            "overall_score": 8.2,
            "empathy": {"score": 9, "justification": "Acknowledged frustration immediately and apologized sincerely"},
            "resolution": {"score": 9, "justification": "Offered proactive replacement with expedited shipping at no extra cost"},
            "professionalism": {"score": 8, "justification": "Professional greeting, clear communication throughout"},
            "compliance": {"score": 8, "justification": "Proper greeting and closing, no PII issues"},
            "efficiency": {"score": 7, "justification": "Resolved within 2 minutes, efficient handling"},
            "flags": [],
            "recommendations": ["Continue excellent empathy practices"],
        },
    },
    "SAMPLE-002": {
        "agent_name": "Agent",
        "caller_id": "C-2024-2345",
        "duration_seconds": 68,
        "summary": {
            "summary": "Customer reported double billing on subscription for the third time. Agent confirmed the duplicate charge but offered only standard refund timeline. Customer escalated to supervisor due to lack of urgency.",
            "key_points": ["Recurring double charge issue — third occurrence", "Agent confirmed the error but showed no urgency", "Customer escalated to supervisor", "No resolution provided"],
            "action_items": ["Investigate root cause of recurring billing errors", "Follow up with supervisor on escalation", "Implement billing system fix"],
            "customer_intent": "Billing dispute",
            "resolution_status": "escalated",
            "topics": ["billing", "refund", "escalation"],
            "sentiment_trajectory": "negative_throughout",
        },
        "quality_scores": {
            "overall_score": 5.5,
            "empathy": {"score": 4, "justification": "Did not acknowledge the severity of a recurring issue"},
            "resolution": {"score": 4, "justification": "Failed to provide expedited resolution for repeat issue"},
            "professionalism": {"score": 5, "justification": "Dismissive tone when transferring — 'they'll tell you the same thing'"},
            "compliance": {"score": 7, "justification": "No PII violations, but poor greeting"},
            "efficiency": {"score": 7, "justification": "Short call but no resolution achieved"},
            "flags": ["pii_detected"],
            "recommendations": ["Train on empathy for recurring issues", "Empower agents to expedite refunds for repeat errors"],
        },
    },
    "SAMPLE-003": {
        "agent_name": "Mike",
        "caller_id": "C-2024-3456",
        "duration_seconds": 103,
        "summary": {
            "summary": "Customer experiencing intermittent router disconnections since firmware update. Agent identified the known firmware issue and guided customer through rollback process via admin panel.",
            "key_points": ["Disconnections started after firmware update", "Known issue affecting multiple users", "Agent guided firmware rollback via admin panel", "Offered technician visit as fallback"],
            "action_items": ["Follow up if issue persists after rollback", "Escalate firmware bug to engineering"],
            "customer_intent": "Technical support",
            "resolution_status": "resolved",
            "topics": ["technical_support", "firmware", "troubleshooting"],
            "sentiment_trajectory": "negative_to_positive",
        },
        "quality_scores": {
            "overall_score": 7.2,
            "empathy": {"score": 7, "justification": "Apologized and showed willingness to help solve the problem"},
            "resolution": {"score": 8, "justification": "Provided clear, actionable solution with fallback option"},
            "professionalism": {"score": 8, "justification": "Professional greeting, clear step-by-step guidance"},
            "compliance": {"score": 7, "justification": "Good greeting and closing, no issues"},
            "efficiency": {"score": 6, "justification": "Resolved in reasonable time but could have been faster"},
            "flags": [],
            "recommendations": ["Proactively mention known issues to reduce call volume"],
        },
    },
    "SAMPLE-004": {
        "agent_name": "Lisa",
        "caller_id": "C-2024-4567",
        "duration_seconds": 95,
        "summary": {
            "summary": "Customer requested subscription cancellation due to cost concerns. Agent listened empathetically and offered a lower-tier Basic plan at $9.99/month. Customer chose to downgrade instead of cancel, retaining the account.",
            "key_points": ["Customer found $29.99/month too expensive for basic usage", "Agent offered $9.99 Basic plan as alternative", "Customer chose downgrade over cancellation", "Saved the customer account"],
            "action_items": ["Process plan change for next billing cycle", "Send plan change confirmation email"],
            "customer_intent": "Account cancellation",
            "resolution_status": "resolved",
            "topics": ["cancellation", "retention", "plan_change"],
            "sentiment_trajectory": "neutral_to_positive",
        },
        "quality_scores": {
            "overall_score": 7.8,
            "empathy": {"score": 8, "justification": "Asked open-ended questions about dissatisfaction before offering solutions"},
            "resolution": {"score": 9, "justification": "Successfully retained customer with appropriate alternative"},
            "professionalism": {"score": 8, "justification": "Warm greeting, personalized approach to retention"},
            "compliance": {"score": 7, "justification": "Standard greeting and closing, no issues"},
            "efficiency": {"score": 7, "justification": "Efficient conversation with clear outcome"},
            "flags": [],
            "recommendations": ["Excellent retention technique — share as best practice"],
        },
    },
    "SAMPLE-005": {
        "agent_name": "Agent",
        "caller_id": "C-2024-5678",
        "duration_seconds": 85,
        "summary": {
            "summary": "Customer called about a damaged product unreplaced for two weeks. Agent was dismissive, offered no urgency, and refused to connect to a manager. Call ended with customer threatening BBB complaint.",
            "key_points": ["Damaged product unresolved for 2 weeks despite 4 calls", "Agent dismissive and unhelpful", "Manager unavailable — told customer to call back", "Customer threatened BBB complaint"],
            "action_items": ["Immediate manager follow-up required", "Ship replacement product urgently", "Review agent performance"],
            "customer_intent": "Damaged product replacement",
            "resolution_status": "unresolved",
            "topics": ["complaint", "damaged_product", "escalation"],
            "sentiment_trajectory": "negative_throughout",
        },
        "quality_scores": {
            "overall_score": 3.5,
            "empathy": {"score": 2, "justification": "No acknowledgment of customer's frustration or prior attempts"},
            "resolution": {"score": 2, "justification": "No resolution offered, just 'call back later'"},
            "professionalism": {"score": 3, "justification": "Abrupt greeting, dismissive language throughout"},
            "compliance": {"score": 5, "justification": "No PII issues but failed to follow escalation procedures"},
            "efficiency": {"score": 6, "justification": "Short call but zero value delivered"},
            "flags": ["escalation_failure", "poor_tone"],
            "recommendations": ["Mandatory empathy training", "Review escalation procedures", "Performance improvement plan"],
        },
    },
    "SAMPLE-006": {
        "agent_name": "Jessica",
        "caller_id": "C-2024-6789",
        "duration_seconds": 106,
        "summary": {
            "summary": "Loyal Standard plan member inquired about Premium upgrade. Agent provided comprehensive feature comparison, applied 20% loyalty discount, and completed the upgrade seamlessly.",
            "key_points": ["Customer loyal for 1 year on Standard plan", "Agent offered 20% loyalty discount on Premium", "Upgrade completed with 30-day money-back guarantee", "Welcome email with tips sent"],
            "action_items": ["Send Premium welcome email with tips", "Monitor customer satisfaction post-upgrade"],
            "customer_intent": "Plan upgrade inquiry",
            "resolution_status": "resolved",
            "topics": ["upgrade", "loyalty", "sales"],
            "sentiment_trajectory": "positive_throughout",
        },
        "quality_scores": {
            "overall_score": 9.0,
            "empathy": {"score": 9, "justification": "Thanked loyalty, personalized the interaction"},
            "resolution": {"score": 10, "justification": "Complete upgrade with discount and money-back guarantee"},
            "professionalism": {"score": 9, "justification": "Excellent greeting, thorough feature walkthrough"},
            "compliance": {"score": 9, "justification": "Mentioned refund policy proactively, proper script adherence"},
            "efficiency": {"score": 8, "justification": "Covered all topics efficiently without rushing"},
            "flags": [],
            "recommendations": ["Model agent — use as training example for upsell conversations"],
        },
    },
    "SAMPLE-007": {
        "agent_name": "David",
        "caller_id": "C-2026-0107",
        "duration_seconds": 86,
        "summary": {
            "summary": "Customer's laptop bag marked as delivered but never received. Agent offered reshipment with signature confirmation and proactively flagged the address for future orders.",
            "key_points": ["Package marked delivered but not received", "Reshipment with signature required delivery", "Delivery address flagged for signature default"],
            "action_items": ["Ship replacement with signature confirmation", "Send tracking within 2 hours"],
            "customer_intent": "Lost package claim",
            "resolution_status": "resolved",
            "topics": ["shipping", "lost_package", "reshipment"],
            "sentiment_trajectory": "negative_to_positive",
        },
        "quality_scores": {
            "overall_score": 7.8,
            "empathy": {"score": 8, "justification": "Acknowledged frustration and validated the customer's effort checking neighbors"},
            "resolution": {"score": 8, "justification": "Offered clear options and proactively prevented future issues"},
            "professionalism": {"score": 8, "justification": "Professional greeting, good communication"},
            "compliance": {"score": 8, "justification": "Proper procedures followed"},
            "efficiency": {"score": 7, "justification": "Efficient resolution within 90 seconds"},
            "flags": [],
            "recommendations": ["Good proactive behavior flagging the address"],
        },
    },
    "SAMPLE-008": {
        "agent_name": "Rachel",
        "caller_id": "C-2026-0208",
        "duration_seconds": 90,
        "summary": {
            "summary": "Customer received wrong item (red hiking boots instead of blue running shoes). Agent immediately apologized, shipped correct item with express delivery, provided prepaid return label, and applied 15% discount.",
            "key_points": ["Wrong item sent — fulfillment error", "Three-step resolution: reship, return label, discount", "15% discount applied for inconvenience", "30-day return window for wrong item"],
            "action_items": ["Ship correct shoes with express delivery", "Email prepaid return label"],
            "customer_intent": "Wrong item received",
            "resolution_status": "resolved",
            "topics": ["fulfillment", "wrong_item", "exchange"],
            "sentiment_trajectory": "negative_to_positive",
        },
        "quality_scores": {
            "overall_score": 8.6,
            "empathy": {"score": 9, "justification": "Sincere apology and took full ownership of the mistake"},
            "resolution": {"score": 9, "justification": "Comprehensive three-part solution exceeded expectations"},
            "professionalism": {"score": 9, "justification": "Professional, warm, and solution-oriented throughout"},
            "compliance": {"score": 8, "justification": "Proper procedures, good documentation"},
            "efficiency": {"score": 8, "justification": "Quick resolution with minimal back-and-forth"},
            "flags": [],
            "recommendations": ["Excellent handling — share as best practice for fulfillment errors"],
        },
    },
    "SAMPLE-009": {
        "agent_name": "Kevin",
        "caller_id": "C-2026-0309",
        "duration_seconds": 84,
        "summary": {
            "summary": "Customer's coupon code SAVE25 had expired. Agent explained the expiration was in fine print and offered a one-time 20% discount as compromise. Customer accepted reluctantly.",
            "key_points": ["Coupon expired without clear communication", "Agent offered 20% replacement code", "Customer accepted but was not fully satisfied"],
            "action_items": ["Review coupon email templates for clearer expiry messaging"],
            "customer_intent": "Promotional code issue",
            "resolution_status": "resolved",
            "topics": ["billing", "coupon", "promotion"],
            "sentiment_trajectory": "negative_to_neutral",
        },
        "quality_scores": {
            "overall_score": 6.2,
            "empathy": {"score": 6, "justification": "Acknowledged frustration but blamed fine print"},
            "resolution": {"score": 7, "justification": "Offered partial solution but not full original value"},
            "professionalism": {"score": 6, "justification": "Casual greeting, functional but not warm"},
            "compliance": {"score": 7, "justification": "No violations"},
            "efficiency": {"score": 6, "justification": "Resolved but could have been more proactive"},
            "flags": [],
            "recommendations": ["Improve greeting warmth", "Advocate for clearer coupon terms"],
        },
    },
    "SAMPLE-010": {
        "agent_name": "Amanda",
        "caller_id": "C-2026-0410",
        "duration_seconds": 93,
        "summary": {
            "summary": "Customer needed size exchange on a dress for daughter's wedding. Agent congratulated the customer, found the size in stock, arranged free express exchange, and waived the exchange fee.",
            "key_points": ["Size 8 to size 6 exchange for wedding dress", "Free express delivery arranged", "Exchange fee waived", "Prepaid return label included"],
            "action_items": ["Ship size 6 with express delivery", "Include prepaid return label"],
            "customer_intent": "Size exchange",
            "resolution_status": "resolved",
            "topics": ["returns", "exchange", "fashion"],
            "sentiment_trajectory": "positive_throughout",
        },
        "quality_scores": {
            "overall_score": 9.2,
            "empathy": {"score": 10, "justification": "Congratulated on wedding, personalized the interaction beautifully"},
            "resolution": {"score": 9, "justification": "Complete exchange with waived fees and proactive shipping"},
            "professionalism": {"score": 9, "justification": "Warm, enthusiastic, and professional greeting"},
            "compliance": {"score": 9, "justification": "Perfect script adherence with personal touch"},
            "efficiency": {"score": 9, "justification": "Efficient and thorough handling"},
            "flags": [],
            "recommendations": ["Outstanding agent — candidate for team lead mentoring"],
        },
    },
    "SAMPLE-011": {
        "agent_name": "Tom",
        "caller_id": "C-2026-0511",
        "duration_seconds": 78,
        "summary": {
            "summary": "Customer inquired about out-of-stock NoiseBlock Pro headphones. Agent set up a stock alert and recommended a comparable in-stock alternative with a comparison chart.",
            "key_points": ["Product out of stock, restock expected March 8th", "Stock alert set up for email and text", "Alternative product QuietMax X2 suggested", "Comparison chart emailed"],
            "action_items": ["Monitor restock and ensure alert fires", "Follow up if customer orders alternative"],
            "customer_intent": "Product availability inquiry",
            "resolution_status": "resolved",
            "topics": ["product", "inventory", "recommendation"],
            "sentiment_trajectory": "neutral_to_positive",
        },
        "quality_scores": {
            "overall_score": 7.2,
            "empathy": {"score": 7, "justification": "Understood urgency for work trip"},
            "resolution": {"score": 7, "justification": "Good alternatives offered but no guarantee on timeline"},
            "professionalism": {"score": 7, "justification": "Solid greeting, knowledgeable about products"},
            "compliance": {"score": 7, "justification": "No issues"},
            "efficiency": {"score": 8, "justification": "Efficient call with clear action items"},
            "flags": [],
            "recommendations": ["Good cross-selling technique with comparison chart"],
        },
    },
    "SAMPLE-012": {
        "agent_name": "Agent",
        "caller_id": "C-2026-0612",
        "duration_seconds": 91,
        "summary": {
            "summary": "Customer waited 21 days for a refund on a returned blender despite 7-10 day promise. Agent cited holiday backlog and submitted priority escalation with 3-5 more days. Customer dissatisfied with additional wait.",
            "key_points": ["Refund 21 days overdue (promised 7-10 days)", "Item stuck in warehouse inspection queue", "Priority escalation submitted with 3-5 day ETA", "Customer left dissatisfied"],
            "action_items": ["Track escalation to ensure refund processes", "Review warehouse inspection backlog"],
            "customer_intent": "Refund status inquiry",
            "resolution_status": "pending",
            "topics": ["returns", "refund", "delay"],
            "sentiment_trajectory": "negative_throughout",
        },
        "quality_scores": {
            "overall_score": 4.6,
            "empathy": {"score": 4, "justification": "Acknowledged frustration but with casual 'yeah' tone"},
            "resolution": {"score": 4, "justification": "Only option was more waiting with no guarantee"},
            "professionalism": {"score": 5, "justification": "Casual greeting, lack of urgency in tone"},
            "compliance": {"score": 6, "justification": "Followed escalation process but poor greeting/closing"},
            "efficiency": {"score": 5, "justification": "Quick call but no meaningful resolution"},
            "flags": ["sla_breach"],
            "recommendations": ["Empower agents to issue immediate refunds for SLA breaches", "Improve tone and urgency for delayed items"],
        },
    },
    "SAMPLE-013": {
        "agent_name": "Maria",
        "caller_id": "C-2026-0713",
        "duration_seconds": 102,
        "summary": {
            "summary": "Customer's $100 gift card showed only $25 balance due to unauthorized use. Agent identified fraud, deactivated the card, and issued a full replacement $100 digital gift card.",
            "key_points": ["$75 unauthorized transaction on gift card", "Card compromised before activation", "Full $100 replacement issued", "Fraud reported to security team"],
            "action_items": ["Send replacement digital gift card", "Security team to investigate fraud"],
            "customer_intent": "Gift card balance discrepancy",
            "resolution_status": "resolved",
            "topics": ["billing", "gift_card", "fraud"],
            "sentiment_trajectory": "negative_to_positive",
        },
        "quality_scores": {
            "overall_score": 8.2,
            "empathy": {"score": 9, "justification": "Validated the upsetting nature of the situation, wished happy birthday"},
            "resolution": {"score": 9, "justification": "Full replacement with no hassle, reported fraud proactively"},
            "professionalism": {"score": 8, "justification": "Warm, professional, and thorough"},
            "compliance": {"score": 7, "justification": "Collected email — PII noted but necessary for resolution"},
            "efficiency": {"score": 8, "justification": "Resolved quickly with clear communication"},
            "flags": ["pii_detected"],
            "recommendations": ["Excellent fraud handling — document as procedure example"],
        },
    },
    "SAMPLE-014": {
        "agent_name": "James",
        "caller_id": "C-2026-0814",
        "duration_seconds": 82,
        "summary": {
            "summary": "Customer needed to change delivery address on a recent order. Agent caught it before warehouse processing, updated the address, and proactively offered to update the default account address.",
            "key_points": ["Address change caught before warehouse processing", "No impact on delivery timeline", "Default account address updated proactively"],
            "action_items": ["Confirm address update via email"],
            "customer_intent": "Delivery address change",
            "resolution_status": "resolved",
            "topics": ["shipping", "address_change", "account"],
            "sentiment_trajectory": "anxious_to_positive",
        },
        "quality_scores": {
            "overall_score": 8.6,
            "empathy": {"score": 8, "justification": "Reassured customer quickly that it was fixable"},
            "resolution": {"score": 9, "justification": "Fixed issue and proactively prevented future occurrences"},
            "professionalism": {"score": 9, "justification": "Clear, efficient communication"},
            "compliance": {"score": 8, "justification": "Confirmed address details, proper handling"},
            "efficiency": {"score": 9, "justification": "Very efficient — resolved in under 90 seconds"},
            "flags": [],
            "recommendations": ["Great proactive behavior updating default address"],
        },
    },
    "SAMPLE-015": {
        "agent_name": "Agent",
        "caller_id": "C-2026-0915",
        "duration_seconds": 87,
        "summary": {
            "summary": "Customer received a shattered ceramic vase due to poor packaging. Agent was dismissive, blamed the carrier, and told customer to email photos with 10-day review and no manager available. Customer vowed never to return.",
            "key_points": ["Fragile item arrived shattered — inadequate packaging", "Agent blamed carrier and suggested shipping insurance", "10 business day review process with no expediting", "Manager unavailable on weekends", "Customer lost"],
            "action_items": ["Immediate manager callback required", "Review packaging standards for fragile items", "Agent performance review"],
            "customer_intent": "Damaged item replacement/refund",
            "resolution_status": "unresolved",
            "topics": ["returns", "damaged_product", "complaint"],
            "sentiment_trajectory": "negative_throughout",
        },
        "quality_scores": {
            "overall_score": 3.0,
            "empathy": {"score": 2, "justification": "Blamed customer for not buying insurance, zero empathy"},
            "resolution": {"score": 2, "justification": "No resolution — just told to email and wait"},
            "professionalism": {"score": 2, "justification": "Rude greeting, dismissive, adversarial tone"},
            "compliance": {"score": 4, "justification": "Failed to escalate, no proper closing"},
            "efficiency": {"score": 5, "justification": "Short call but zero value delivered"},
            "flags": ["poor_tone", "escalation_failure", "customer_churn_risk"],
            "recommendations": ["Immediate performance improvement plan", "Mandatory empathy and de-escalation training"],
        },
    },
    "SAMPLE-016": {
        "agent_name": "Nina",
        "caller_id": "C-2026-1016",
        "duration_seconds": 83,
        "summary": {
            "summary": "Customer found a coffee maker $30 cheaper at competitor. Agent verified the competitor price, applied price match within policy window, and highlighted the extra warranty value.",
            "key_points": ["$30 price difference with TechBargains.com", "Price match applied within 14-day window", "Refund of $30 to original payment", "Agent noted extra warranty value"],
            "action_items": ["Process $30 refund"],
            "customer_intent": "Price match request",
            "resolution_status": "resolved",
            "topics": ["billing", "price_match", "policy"],
            "sentiment_trajectory": "neutral_to_positive",
        },
        "quality_scores": {
            "overall_score": 7.8,
            "empathy": {"score": 7, "justification": "Enthusiastic and customer-friendly approach"},
            "resolution": {"score": 9, "justification": "Seamless price match with value-add warranty mention"},
            "professionalism": {"score": 8, "justification": "Warm greeting, knowledgeable about policy"},
            "compliance": {"score": 8, "justification": "Verified eligibility before applying match"},
            "efficiency": {"score": 7, "justification": "Efficient handling within reasonable time"},
            "flags": [],
            "recommendations": ["Good technique mentioning warranty advantage for retention"],
        },
    },
    "SAMPLE-017": {
        "agent_name": "Brian",
        "caller_id": "C-2026-1117",
        "duration_seconds": 75,
        "summary": {
            "summary": "Customer confused by three separate tracking numbers for one order. Agent explained the multi-warehouse shipping model and sent an organized tracking summary email. Also logged UX feedback.",
            "key_points": ["Three items shipped from different warehouses", "Agent explained rationale clearly", "Organized tracking email sent", "App UX feedback logged"],
            "action_items": ["Log app tracking UX feedback for product team"],
            "customer_intent": "Order tracking confusion",
            "resolution_status": "resolved",
            "topics": ["shipping", "tracking", "ux_feedback"],
            "sentiment_trajectory": "confused_to_neutral",
        },
        "quality_scores": {
            "overall_score": 6.6,
            "empathy": {"score": 6, "justification": "Acknowledged confusion but could have been warmer"},
            "resolution": {"score": 7, "justification": "Explained well and sent helpful email"},
            "professionalism": {"score": 6, "justification": "Casual greeting and closing could be improved"},
            "compliance": {"score": 7, "justification": "No issues"},
            "efficiency": {"score": 7, "justification": "Quick and informative"},
            "flags": [],
            "recommendations": ["Improve greeting warmth", "Good initiative logging feedback"],
        },
    },
    "SAMPLE-018": {
        "agent_name": "Priya",
        "caller_id": "C-2026-1218",
        "duration_seconds": 116,
        "summary": {
            "summary": "Customer's holiday triple points promotion wasn't applied to a $300+ order. Agent identified the system glitch, added 640 missing points, and proactively checked two other orders for consistency.",
            "key_points": ["System glitch prevented triple point multiplier", "640 missing points added to account", "Two other holiday orders verified as correct", "Customer 160 points from Gold status"],
            "action_items": ["Report points system glitch to engineering"],
            "customer_intent": "Loyalty points discrepancy",
            "resolution_status": "resolved",
            "topics": ["loyalty", "rewards", "promotion"],
            "sentiment_trajectory": "concerned_to_positive",
        },
        "quality_scores": {
            "overall_score": 8.2,
            "empathy": {"score": 8, "justification": "Validated concern and showed enthusiasm for the program"},
            "resolution": {"score": 9, "justification": "Fixed the issue and proactively checked other orders"},
            "professionalism": {"score": 8, "justification": "Thorough, knowledgeable, warm tone"},
            "compliance": {"score": 8, "justification": "Proper procedures followed"},
            "efficiency": {"score": 8, "justification": "Checked multiple orders efficiently"},
            "flags": [],
            "recommendations": ["Excellent thoroughness — proactively checking related orders"],
        },
    },
    "SAMPLE-019": {
        "agent_name": "Carter",
        "caller_id": "C-2026-1319",
        "duration_seconds": 138,
        "summary": {
            "summary": "Customer wanted to cancel a flash sale TV order placed by mistake. Agent initially cited final sale policy, but escalated to supervisor who approved one-time cancellation with store credit refund.",
            "key_points": ["Flash sale marked as final sale", "Customer ordered by mistake (meant wishlist)", "Supervisor approved one-time exception", "Refund as store credit, not card"],
            "action_items": ["Process store credit", "Flag account for one-time exception used"],
            "customer_intent": "Order cancellation",
            "resolution_status": "resolved",
            "topics": ["cancellation", "flash_sale", "policy_exception"],
            "sentiment_trajectory": "frustrated_to_neutral",
        },
        "quality_scores": {
            "overall_score": 5.2,
            "empathy": {"score": 5, "justification": "Understood the mistake but initially rigid on policy"},
            "resolution": {"score": 6, "justification": "Eventually cancelled but with store credit only, not ideal"},
            "professionalism": {"score": 5, "justification": "Casual greeting, functional but not warm"},
            "compliance": {"score": 6, "justification": "Followed policy but store credit compromise is less customer-friendly"},
            "efficiency": {"score": 4, "justification": "Long hold time waiting for supervisor"},
            "flags": ["long_hold"],
            "recommendations": ["Empower agents to handle simple cancellations within timeframe without supervisor"],
        },
    },
    "SAMPLE-020": {
        "agent_name": "Diana",
        "caller_id": "C-2026-1420",
        "duration_seconds": 123,
        "summary": {
            "summary": "Customer returning 3 of 5 items, one without tags. Agent explained full vs partial refund policy clearly: full refund for two items with tags, 80% for the belt without tags. Total $172 refund.",
            "key_points": ["3-item return from 5-item order", "Full refund for items with tags ($89 + $35)", "80% partial refund for tag-removed belt ($48 of $60)", "Single prepaid label for all returns"],
            "action_items": ["Process $172 refund upon receipt", "Send prepaid return label"],
            "customer_intent": "Multi-item return",
            "resolution_status": "resolved",
            "topics": ["returns", "partial_refund", "policy"],
            "sentiment_trajectory": "uncertain_to_satisfied",
        },
        "quality_scores": {
            "overall_score": 7.2,
            "empathy": {"score": 7, "justification": "Understood frustration about tag removal policy"},
            "resolution": {"score": 8, "justification": "Clear breakdown, fair policy application"},
            "professionalism": {"score": 7, "justification": "Professional, clear communication, offered pro tip"},
            "compliance": {"score": 7, "justification": "Policy correctly applied"},
            "efficiency": {"score": 7, "justification": "Efficient handling of complex multi-item return"},
            "flags": [],
            "recommendations": ["Good transparency in explaining policy rationale"],
        },
    },
}

# ── Agent names for variety ──────────────────────────────────────────────────

AGENT_NAMES = [
    "Sarah", "Agent", "Mike", "Lisa", "Agent", "Jessica", "David", "Rachel",
    "Kevin", "Amanda", "Tom", "Agent", "Maria", "James", "Agent", "Nina",
    "Brian", "Priya", "Carter", "Diana",
]


def seed():
    """Seed the database with pre-analyzed call records."""
    samples_path = Path(__file__).parent.parent / "data" / "sample_transcripts" / "samples.json"

    with open(samples_path) as f:
        samples = json.load(f)

    db = Database()
    now = datetime.now()
    seeded = 0

    for i, sample in enumerate(samples):
        call_id = sample["call_id"]
        analysis = ANALYSES.get(call_id)
        if not analysis:
            print(f"  ⚠ No pre-computed analysis for {call_id}, skipping")
            continue

        # Spread call dates over past 30 days
        days_ago = random.randint(1, 30)
        hours_ago = random.randint(8, 17)
        call_date = now - timedelta(days=days_ago, hours=hours_ago)

        # Build the transcript text
        transcript_text = "\n".join(
            f"{seg['speaker']}: {seg['text']}" for seg in sample["transcript"]
        )

        report = {
            "call_metadata": {
                "caller_id": analysis.get("caller_id", f"C-2026-{i:04d}"),
                "agent_name": analysis.get("agent_name", AGENT_NAMES[i % len(AGENT_NAMES)]),
                "duration_seconds": analysis.get("duration_seconds", 90),
                "call_date": call_date.isoformat(),
                "file_path": "",
                "source": "json_seed",
                "language": "en",
            },
            "transcript_preview": transcript_text[:500],
            "transcript_word_count": len(transcript_text.split()),
            "summary": analysis["summary"],
            "quality_scores": analysis["quality_scores"],
        }

        try:
            saved_id = db.save_analysis(report)
            seeded += 1
            score = analysis["quality_scores"]["overall_score"]
            print(f"  ✅ {call_id} — {sample['scenario']} (score: {score}) → {saved_id}")
        except Exception as e:
            print(f"  ❌ {call_id} — {e}")

    print(f"\n🎉 Seeded {seeded}/{len(samples)} records into database")


if __name__ == "__main__":
    print("🌱 Seeding Clarity CX database with sample data...\n")
    seed()
