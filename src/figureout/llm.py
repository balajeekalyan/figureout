"""LLM provider abstraction for FigureOut."""

import asyncio
import json
import os
from enum import Enum

from figureout.exceptions import OutputTokenLimitError, InputTokenLimitError
from figureout.utils import _with_retry


_ENV_KEY_MAP = {
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "claude": "ANTHROPIC_API_KEY",
    "meta": "META_API_KEY",
    "mistral": "MISTRAL_API_KEY",
    "groq": "GROQ_API_KEY",
}


class LLM(Enum):
    OPENAI = "openai"
    GEMINI = "gemini"
    CLAUDE = "claude"
    META = "meta"
    MISTRAL = "mistral"
    GROQ = "groq"


def _resolve_api_key(llm: LLM, api_key: str | None = None) -> str:
    """Resolve API key from: explicit param → environment variable.

    Raises ValueError with a clear message if no key is found.
    """
    if api_key:
        return api_key
    env_var = _ENV_KEY_MAP[llm.value]
    key = os.environ.get(env_var)
    if key:
        return key
    raise ValueError(
        f"No API key found for {llm.value}. "
        f"Either pass api_key directly or set the {env_var} environment variable."
    )



def _build_gemini_assistant_message(response):
    """Build a Gemini assistant message that preserves tool call parts."""
    assistant_parts = []
    if response.candidates and response.candidates[0].content:
        for part in response.candidates[0].content.parts:
            if hasattr(part, "function_call") and part.function_call:
                fc = part.function_call
                assistant_parts.append({
                    "function_call": {
                        "name": fc.name,
                        "args": dict(fc.args) if fc.args else {},
                    }
                })
            elif hasattr(part, "text") and part.text:
                assistant_parts.append({"text": part.text})
    return {"role": "model", "parts": assistant_parts if assistant_parts else [{"text": ""}]}


def _parse_openai_response(msg, usage, tool_calls_raw) -> dict:
    """Parse an OpenAI-compatible chat completion message into a standard response dict.

    Used by both OpenAI and Perplexity providers.
    """
    parsed_tool_calls = []
    if tool_calls_raw:
        for tc in tool_calls_raw:
            parsed_tool_calls.append({
                "id": tc.id,
                "name": tc.function.name,
                "arguments": json.loads(tc.function.arguments),
            })
    return {
        "text": msg.content or "",
        "input_tokens": usage.prompt_tokens,
        "output_tokens": usage.completion_tokens,
        "tools_used": [tc["name"] for tc in parsed_tool_calls],
        "tool_calls": parsed_tool_calls,
        "assistant_message": msg.to_dict() if hasattr(msg, "to_dict") else {
            "role": "assistant",
            "content": msg.content,
            "tool_calls": [
                {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in tool_calls_raw
            ] if tool_calls_raw else None,
        },
    }


def build_tool_result_messages(llm: LLM, assistant_message: dict, tool_results: list[dict]) -> list[dict]:
    """Build provider-specific messages to append after tool execution.

    Args:
        llm: The LLM provider enum.
        assistant_message: The assistant message from the LLM response.
        tool_results: List of dicts with keys "id", "name", "content".

    Returns:
        List of messages to append to the conversation.
    """
    if llm in (LLM.OPENAI, LLM.META, LLM.MISTRAL, LLM.GROQ):
        return [
            assistant_message,
            *[{"role": "tool", "tool_call_id": tr["id"], "content": tr["content"]} for tr in tool_results],
        ]
    elif llm == LLM.CLAUDE:
        return [
            assistant_message,
            {"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": tr["id"], "content": tr["content"]}
                for tr in tool_results
            ]},
        ]
    elif llm == LLM.GEMINI:
        return [
            assistant_message,
            {"role": "user", "parts": [
                {"function_response": {"name": tr["name"], "response": {"result": tr["content"]}}}
                for tr in tool_results
            ]},
        ]
    else:
        raise ValueError(f"Unsupported LLM for tool results: {llm}")


def get_llm_client(llm: LLM, api_key: str | None = None, llm_version: str | None = None, max_output_tokens: int = 16384, max_retries: int = 0, timeout: float = 120.0):
    """Return a callable (messages, tools=None) -> dict for the given LLM.

    Each call returns a dict with keys:
        text, input_tokens, output_tokens, tools_used

    tools should be a list of MCP-style tool dicts, each with keys:
        name, description, inputSchema (JSON Schema dict)

    llm_version: optional model version string to override the default.
    max_output_tokens: maximum number of output tokens for LLM responses.
    max_retries: number of retries on transient errors (0 = no retries).
    """
    if not llm_version:
        raise ValueError(f"No model version specified for {llm.value}. Pass llm_version= or set the FIGUREOUT_LLM_VERSION environment variable.")
    model = llm_version

    if llm == LLM.OPENAI:
        try:
            from openai import AsyncOpenAI, BadRequestError
        except ImportError:
            raise ImportError(
                "The 'openai' package is required to use LLM.OPENAI. "
                "Install it with: pip install figureout[openai]"
            )

        client = AsyncOpenAI(api_key=_resolve_api_key(llm, api_key))

        async def chat(messages: list[dict], tools: list[dict] | None = None, json_mode: bool = False, require_tool_use: bool = False) -> dict:
            kwargs = {"model": model, "messages": messages}
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            if tools:
                kwargs["tools"] = [
                    {
                        "type": "function",
                        "function": {
                            "name": t["name"],
                            "description": t.get("description", ""),
                            "parameters": t.get("inputSchema", {}),
                        },
                    }
                    for t in tools
                ]
                kwargs["parallel_tool_calls"] = True
                if require_tool_use:
                    kwargs["tool_choice"] = "required"

            async def _call():
                try:
                    return await client.chat.completions.create(**kwargs, timeout=timeout)
                except BadRequestError as e:
                    if "max_tokens" in str(e).lower() or "context" in str(e).lower() or "too long" in str(e).lower():
                        raise InputTokenLimitError("openai", model, str(e)) from e
                    raise

            response = await _with_retry(_call, max_retries, "openai", model)
            if response.choices[0].finish_reason == "length":
                raise OutputTokenLimitError("openai", model, max_output_tokens, response.usage.completion_tokens)
            msg = response.choices[0].message
            return _parse_openai_response(msg, response.usage, msg.tool_calls)

        return chat

    elif llm == LLM.GEMINI:
        try:
            from google import genai
            from google.genai import types
            from google.api_core.exceptions import InvalidArgument
        except ImportError:
            raise ImportError(
                "The 'google-genai' and 'google-api-core' packages are required to use LLM.GEMINI. "
                "Install them with: pip install figureout[gemini]"
            )

        client = genai.Client(api_key=_resolve_api_key(llm, api_key))

        async def chat(messages: list[dict], tools: list[dict] | None = None, json_mode: bool = False, require_tool_use: bool = False) -> dict:
            contents = []
            for msg in messages:
                role = "model" if msg["role"] == "assistant" else msg["role"]
                if role == "system":
                    role = "user"
                # Support pre-built Gemini messages with "parts" key
                if "parts" in msg:
                    contents.append({"role": role, "parts": msg["parts"]})
                else:
                    contents.append({"role": role, "parts": [{"text": msg["content"]}]})
            config_kwargs = {"max_output_tokens": max_output_tokens}
            if json_mode:
                config_kwargs["response_mime_type"] = "application/json"
            if tools:
                config_kwargs["tools"] = [
                    types.Tool(
                        function_declarations=[
                            types.FunctionDeclaration(
                                name=t["name"],
                                description=t.get("description", ""),
                                parameters=t.get("inputSchema", {}),
                            )
                            for t in tools
                        ]
                    )
                ]
                if require_tool_use:
                    config_kwargs["tool_config"] = types.ToolConfig(
                        function_calling_config=types.FunctionCallingConfig(mode="ANY")
                    )
            config = types.GenerateContentConfig(**config_kwargs)
            gen_kwargs = {"model": model, "contents": contents, "config": config}

            async def _call():
                try:
                    return await asyncio.wait_for(
                        client.aio.models.generate_content(**gen_kwargs),
                        timeout=timeout,
                    )
                except InvalidArgument as e:
                    if "token" in str(e).lower() or "too long" in str(e).lower() or "limit" in str(e).lower():
                        raise InputTokenLimitError("gemini", model, str(e)) from e
                    raise

            response = await _with_retry(_call, max_retries, "gemini", model)
            if response.candidates and response.candidates[0].finish_reason and response.candidates[0].finish_reason.name == "MAX_TOKENS":
                raise OutputTokenLimitError("gemini", model, max_output_tokens, response.usage_metadata.candidates_token_count)
            tools_used = []
            parsed_tool_calls = []
            text = ""
            if response.candidates and response.candidates[0].content:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, "function_call") and part.function_call:
                        fc = part.function_call
                        tools_used.append(fc.name)
                        parsed_tool_calls.append({
                            "id": fc.name,
                            "name": fc.name,
                            "arguments": dict(fc.args) if fc.args else {},
                        })
                    elif hasattr(part, "text") and part.text:
                        text += part.text
            return {
                "text": text,
                "input_tokens": response.usage_metadata.prompt_token_count,
                "output_tokens": response.usage_metadata.candidates_token_count,
                "tools_used": tools_used,
                "tool_calls": parsed_tool_calls,
                "assistant_message": _build_gemini_assistant_message(response),
            }

        return chat

    elif llm == LLM.CLAUDE:
        try:
            from anthropic import AsyncAnthropic, BadRequestError
        except ImportError:
            raise ImportError(
                "The 'anthropic' package is required to use LLM.CLAUDE. "
                "Install it with: pip install figureout[claude]"
            )

        client = AsyncAnthropic(api_key=_resolve_api_key(llm, api_key))

        async def chat(messages: list[dict], tools: list[dict] | None = None, json_mode: bool = False, require_tool_use: bool = False) -> dict:
            system = None
            non_system = []
            for msg in messages:
                if msg["role"] == "system":
                    system = msg["content"]
                else:
                    non_system.append(msg)
            kwargs = {"model": model, "max_tokens": max_output_tokens, "messages": non_system}
            if system:
                kwargs["system"] = system
            if tools:
                kwargs["tools"] = [
                    {
                        "name": t["name"],
                        "description": t.get("description", ""),
                        "input_schema": t.get("inputSchema", {}),
                    }
                    for t in tools
                ]
                if require_tool_use:
                    kwargs["tool_choice"] = {"type": "any"}

            async def _call():
                try:
                    return await client.messages.create(**kwargs, timeout=timeout)
                except BadRequestError as e:
                    if "token" in str(e).lower() or "too long" in str(e).lower() or "context" in str(e).lower():
                        raise InputTokenLimitError("claude", model, str(e)) from e
                    raise

            response = await _with_retry(_call, max_retries, "claude", model)
            if response.stop_reason == "max_tokens":
                raise OutputTokenLimitError("claude", model, max_output_tokens, response.usage.output_tokens)
            tools_used = []
            parsed_tool_calls = []
            text = ""
            for block in response.content:
                if block.type == "text":
                    text = block.text
                elif block.type == "tool_use":
                    tools_used.append(block.name)
                    parsed_tool_calls.append({
                        "id": block.id,
                        "name": block.name,
                        "arguments": block.input,
                    })
            # Build assistant message for multi-turn tool use
            assistant_content = []
            for block in response.content:
                if block.type == "text":
                    assistant_content.append({"type": "text", "text": block.text})
                elif block.type == "tool_use":
                    assistant_content.append({
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    })
            return {
                "text": text,
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "tools_used": tools_used,
                "tool_calls": parsed_tool_calls,
                "assistant_message": {"role": "assistant", "content": assistant_content},
            }

        return chat

    elif llm == LLM.META:
        try:
            from openai import AsyncOpenAI, BadRequestError
        except ImportError:
            raise ImportError(
                "The 'openai' package is required to use LLM.META. "
                "Install it with: pip install figureout[openai]"
            )

        client = AsyncOpenAI(
            api_key=_resolve_api_key(llm, api_key),
            base_url="https://api.llama.com/compat/v1/",
        )

        async def chat(messages: list[dict], tools: list[dict] | None = None, json_mode: bool = False, require_tool_use: bool = False) -> dict:
            kwargs = {"model": model, "max_tokens": max_output_tokens, "messages": messages}
            # Meta does not support json_object response_format; _extract_json handles parsing
            if tools:
                kwargs["tools"] = [
                    {
                        "type": "function",
                        "function": {
                            "name": t["name"],
                            "description": t.get("description", ""),
                            "parameters": t.get("inputSchema", {}),
                        },
                    }
                    for t in tools
                ]
                kwargs["parallel_tool_calls"] = True
                if require_tool_use:
                    kwargs["tool_choice"] = "required"

            async def _call():
                try:
                    return await client.chat.completions.create(**kwargs, timeout=timeout)
                except BadRequestError as e:
                    if "max_tokens" in str(e).lower() or "context" in str(e).lower() or "too long" in str(e).lower():
                        raise InputTokenLimitError("meta", model, str(e)) from e
                    raise

            response = await _with_retry(_call, max_retries, "meta", model)
            if response.choices[0].finish_reason == "length":
                raise OutputTokenLimitError("meta", model, max_output_tokens, response.usage.completion_tokens)
            msg = response.choices[0].message
            return _parse_openai_response(msg, response.usage, msg.tool_calls)

        return chat

    elif llm == LLM.MISTRAL:
        try:
            from openai import AsyncOpenAI, BadRequestError
        except ImportError:
            raise ImportError(
                "The 'openai' package is required to use LLM.MISTRAL. "
                "Install it with: pip install figureout[openai]"
            )

        client = AsyncOpenAI(
            api_key=_resolve_api_key(llm, api_key),
            base_url="https://api.mistral.ai/v1",
        )

        async def chat(messages: list[dict], tools: list[dict] | None = None, json_mode: bool = False, require_tool_use: bool = False) -> dict:
            kwargs = {"model": model, "max_tokens": max_output_tokens, "messages": messages}
            # Mistral does not support json_object response_format; _extract_json handles parsing
            if tools:
                kwargs["tools"] = [
                    {
                        "type": "function",
                        "function": {
                            "name": t["name"],
                            "description": t.get("description", ""),
                            "parameters": t.get("inputSchema", {}),
                        },
                    }
                    for t in tools
                ]
                kwargs["parallel_tool_calls"] = True
                if require_tool_use:
                    kwargs["tool_choice"] = "required"

            async def _call():
                try:
                    return await client.chat.completions.create(**kwargs, timeout=timeout)
                except BadRequestError as e:
                    if "max_tokens" in str(e).lower() or "context" in str(e).lower() or "too long" in str(e).lower():
                        raise InputTokenLimitError("mistral", model, str(e)) from e
                    raise

            response = await _with_retry(_call, max_retries, "mistral", model)
            if response.choices[0].finish_reason == "length":
                raise OutputTokenLimitError("mistral", model, max_output_tokens, response.usage.completion_tokens)
            msg = response.choices[0].message
            return _parse_openai_response(msg, response.usage, msg.tool_calls)

        return chat

    elif llm == LLM.GROQ:
        try:
            from openai import AsyncOpenAI, BadRequestError
        except ImportError:
            raise ImportError(
                "The 'openai' package is required to use LLM.GROQ. "
                "Install it with: pip install figureout[openai]"
            )

        client = AsyncOpenAI(
            api_key=_resolve_api_key(llm, api_key),
            base_url="https://api.groq.com/openai/v1",
        )

        async def chat(messages: list[dict], tools: list[dict] | None = None, json_mode: bool = False, require_tool_use: bool = False) -> dict:
            kwargs = {"model": model, "max_tokens": max_output_tokens, "messages": messages}
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            if tools:
                kwargs["tools"] = [
                    {
                        "type": "function",
                        "function": {
                            "name": t["name"],
                            "description": t.get("description", ""),
                            "parameters": t.get("inputSchema", {}),
                        },
                    }
                    for t in tools
                ]
                kwargs["parallel_tool_calls"] = True
                if require_tool_use:
                    kwargs["tool_choice"] = "required"

            async def _call():
                try:
                    return await client.chat.completions.create(**kwargs, timeout=timeout)
                except BadRequestError as e:
                    if "max_tokens" in str(e).lower() or "context" in str(e).lower() or "too long" in str(e).lower():
                        raise InputTokenLimitError("groq", model, str(e)) from e
                    raise

            response = await _with_retry(_call, max_retries, "groq", model)
            if response.choices[0].finish_reason == "length":
                raise OutputTokenLimitError("groq", model, max_output_tokens, response.usage.completion_tokens)
            msg = response.choices[0].message
            return _parse_openai_response(msg, response.usage, msg.tool_calls)

        return chat

    else:
        raise ValueError(f"Unsupported LLM: {llm}")
