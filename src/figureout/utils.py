"""Shared utilities for FigureOut."""

import asyncio
import json
import re

from figureout.exceptions import OutputTokenLimitError, InputTokenLimitError, LLMError

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def _parse_bool_env(value: str) -> bool:
    """Parse a boolean from an environment variable string."""
    return value.strip().lower() in ("true", "1", "yes")


def _extract_json(text: str) -> dict:
    """Extract and parse JSON from LLM response text.

    Handles markdown code blocks, surrounding prose, truncated responses,
    and unclosed code fences.
    """
    text = text.strip()
    # Try closed markdown code block first
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass
    # Try unclosed markdown code block (LLM truncated before closing fence)
    match = re.search(r"```(?:json)?\s*([\s\S]*)", text)
    if match:
        text = match.group(1).strip()
    # Try parsing as-is
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Try finding the outermost JSON object or array (string-aware bracket matching)
    for start_char, end_char in [('{', '}'), ('[', ']')]:
        start = text.find(start_char)
        if start == -1:
            continue
        depth = 0
        in_string = False
        escape_next = False
        for i in range(start, len(text)):
            c = text[i]
            if escape_next:
                escape_next = False
                continue
            if c == '\\' and in_string:
                escape_next = True
                continue
            if c == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if c == start_char:
                depth += 1
            elif c == end_char:
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i + 1])
                    except json.JSONDecodeError:
                        break
    raise json.JSONDecodeError("No valid JSON found in LLM response", text, 0)


def _is_transient(exc: Exception) -> bool:
    """Check if an exception is a transient provider error worth retrying."""
    transient_class_names = {
        "RateLimitError", "APITimeoutError", "APIConnectionError", "InternalServerError",
        "ResourceExhausted", "ServiceUnavailable", "DeadlineExceeded",
    }
    exc_class = type(exc).__name__
    if exc_class in transient_class_names:
        return True
    if isinstance(exc, (ConnectionError, TimeoutError)):
        return True
    exc_str = str(exc).lower()
    if any(term in exc_str for term in ("rate limit", "timeout", "connection", "503", "429", "500")):
        return True
    return False


async def _with_retry(coro_factory, max_retries: int, provider: str, model: str):
    """Call coro_factory() with retry and exponential backoff on transient errors."""
    last_exc = None
    for attempt in range(max_retries + 1):
        try:
            return await coro_factory()
        except (OutputTokenLimitError, InputTokenLimitError):
            raise
        except Exception as exc:
            last_exc = exc
            if not _is_transient(exc) or attempt >= max_retries:
                break
            await asyncio.sleep(0.5 * (2 ** attempt))
    raise LLMError(provider, model, last_exc) from last_exc
