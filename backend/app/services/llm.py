import json
import logging

import anthropic

from app.config import settings

logger = logging.getLogger(__name__)

client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)


async def call_agent(system_prompt: str, user_prompt: str) -> dict:
    """Call Sonnet for agent reasoning. Returns parsed JSON."""
    response = await client.messages.create(
        model=settings.sonnet_model,
        max_tokens=1024,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    text = response.content[0].text
    # Extract JSON from response — handle markdown code blocks
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        text = text.split("```")[1].split("```")[0]
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        logger.error(f"Failed to parse agent response: {text[:200]}")
        return {
            "position": 0.0,
            "reasoning": "Failed to parse response",
            "public_statement": "No comment.",
            "willingness_to_settle": 50,
        }


async def call_summary(prompt: str) -> str:
    """Call Haiku for summaries."""
    response = await client.messages.create(
        model=settings.haiku_model,
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text
