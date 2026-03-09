"""Core engine for FigureOut."""

import asyncio
import json
import logging
import os
from collections import OrderedDict
from datetime import date

logger = logging.getLogger(__name__)

from figureout.llm import LLM, get_llm_client, build_tool_result_messages
from figureout.roles import RoleDefinition, build_classification_prompt
from figureout.utils import _extract_json, _parse_bool_env


def _cache_key(query: str, context: str | None = None) -> str:
    key = query.strip().lower()
    if context:
        key += f"\x00{context.strip().lower()}"
    return key


async def classify_role(chat, user_query: str, classification_prompt: str, valid_roles: set[str]) -> list[str]:
    """Use the LLM to determine the appropriate roles from a user query."""
    messages = [
        {"role": "system", "content": classification_prompt},
        {"role": "user", "content": user_query},
    ]
    result = await chat(messages, json_mode=True)
    parsed = _extract_json(result["text"])
    return [r for r in parsed["roles"] if r in valid_roles]


class FigureOut:
    def __init__(
        self,
        llm: LLM | str | None = None,
        llm_version: str | None = None,
        lite_llm_version: str | None = None,
        mcp_server=None,
        verbose: bool | None = None,
        max_roles: int | None = None,
        max_output_tokens: int | None = None,
        max_retries: int | None = None,
        interpret_tool_response: bool | None = None,
        cache_enabled: bool | None = None,
        cache_size: int | None = None,
        max_tool_rounds: int | None = None,
        api_key: str | None = None,
        roles: dict[str, RoleDefinition] | None = None,
        timeout: float | None = None,
        inject_date: bool | None = None,
    ):
        # Resolve LLM from constructor arg or env, default to OPENAI
        if llm is not None:
            self.llm = LLM(llm) if isinstance(llm, str) else llm
        else:
            env_llm = os.environ.get("FIGUREOUT_LLM")
            self.llm = LLM(env_llm) if env_llm else LLM.OPENAI

        # Resolve LLM version from constructor arg or env, default to None
        if llm_version is not None:
            self.llm_version = llm_version
        else:
            self.llm_version = os.environ.get("FIGUREOUT_LLM_VERSION") or None

        # Resolve verbose from constructor arg or env, default to False
        if verbose is not None:
            self.verbose = verbose
        else:
            env_verbose = os.environ.get("FIGUREOUT_VERBOSE")
            self.verbose = _parse_bool_env(env_verbose) if env_verbose else False

        # Resolve max_roles from constructor arg or env, default to 1
        if max_roles is not None:
            self.max_roles = max_roles
        else:
            env_val = os.environ.get("FIGUREOUT_MAX_ROLES")
            self.max_roles = int(env_val) if env_val else 1

        # Resolve max_output_tokens from constructor arg or env, default to 16384
        if max_output_tokens is not None:
            self.max_output_tokens = max_output_tokens
        else:
            env_val = os.environ.get("FIGUREOUT_MAX_OUTPUT_TOKENS")
            self.max_output_tokens = int(env_val) if env_val else 16384

        # Resolve max_retries from constructor arg or env, default to 2
        if max_retries is not None:
            self.max_retries = max_retries
        else:
            env_val = os.environ.get("FIGUREOUT_MAX_RETRIES")
            self.max_retries = int(env_val) if env_val else 2

        # Resolve interpret_tool_response from constructor arg or env, default to None
        # None = normal loop, LLM responds naturally after tool calls
        # True = force LLM interpretation via bridge messages after tool calls
        # False = return raw tool output without sending back to LLM
        if interpret_tool_response is not None:
            self.interpret_tool_response = interpret_tool_response
        else:
            env_val = os.environ.get("FIGUREOUT_INTERPRET_TOOL_RESPONSE")
            self.interpret_tool_response = _parse_bool_env(env_val) if env_val else None

        # Resolve cache_enabled from constructor arg or env, default to True
        if cache_enabled is not None:
            self.cache_enabled = cache_enabled
        else:
            env_val = os.environ.get("FIGUREOUT_CACHE_ENABLED")
            self.cache_enabled = _parse_bool_env(env_val) if env_val else True

        # Resolve cache_size from constructor arg or env, default to 128
        if cache_size is not None:
            self.cache_size = cache_size
        else:
            env_val = os.environ.get("FIGUREOUT_CACHE_SIZE")
            self.cache_size = int(env_val) if env_val else 128

        # Resolve max_tool_rounds from constructor arg or env, default to 3
        if max_tool_rounds is not None:
            self.max_tool_rounds = max_tool_rounds
        else:
            env_val = os.environ.get("FIGUREOUT_MAX_TOOL_ROUNDS")
            self.max_tool_rounds = int(env_val) if env_val else 3

        # Resolve timeout from constructor arg or env, default to 120.0
        if timeout is not None:
            self.timeout = timeout
        else:
            env_val = os.environ.get("FIGUREOUT_TIMEOUT")
            self.timeout = float(env_val) if env_val else 120.0

        # Resolve inject_date from constructor arg or env, default to True
        if inject_date is not None:
            self.inject_date = inject_date
        else:
            env_val = os.environ.get("FIGUREOUT_INJECT_DATE")
            self.inject_date = _parse_bool_env(env_val) if env_val else True

        if self.max_roles < 1:
            raise ValueError("max_roles must be >= 1")
        if self.max_output_tokens < 1:
            raise ValueError("max_output_tokens must be >= 1")
        if self.max_retries < 0:
            raise ValueError("max_retries must be >= 0")
        if self.cache_size < 1:
            raise ValueError("cache_size must be >= 1")
        if self.max_tool_rounds < 0:
            raise ValueError("max_tool_rounds must be >= 0")
        if self.timeout <= 0:
            raise ValueError("timeout must be > 0")

        # Resolve role registry from constructor arg or env
        if roles is not None:
            self._roles = roles
        else:
            env_val = os.environ.get("FIGUREOUT_ROLES")
            if env_val:
                raw = json.loads(env_val)
                self._roles = {
                    name: RoleDefinition(**defn)
                    for name, defn in raw.items()
                }
            else:
                raise ValueError(
                    "No roles defined. Pass roles= or set the FIGUREOUT_ROLES environment variable."
                )

        if not self._roles:
            raise ValueError("roles dictionary cannot be empty.")

        self._classification_prompt = build_classification_prompt(self._roles)
        self._valid_roles = set(self._roles.keys())

        self.api_key = api_key
        self._classification_cache: OrderedDict[str, list[str]] = OrderedDict()

        # Create LLM client once at init
        self.chat = get_llm_client(self.llm, api_key=self.api_key, llm_version=self.llm_version, max_output_tokens=self.max_output_tokens, max_retries=self.max_retries, timeout=self.timeout)

        # Create lite LLM client for classification
        if lite_llm_version is not None:
            self.lite_llm_version = lite_llm_version
        else:
            env_val = os.environ.get("FIGUREOUT_LITE_LLM_VERSION")
            self.lite_llm_version = env_val if env_val else self.llm_version

        self.chat_lite = get_llm_client(self.llm, api_key=self.api_key, llm_version=self.lite_llm_version, max_output_tokens=self.max_output_tokens, max_retries=self.max_retries, timeout=self.timeout)

        if mcp_server is not None:
            self.tools = [
                {
                    "name": name,
                    "description": tool.description,
                    "inputSchema": tool.parameters,
                }
                for name, tool in mcp_server._tool_manager._tools.items()
            ]
            self.tool_handlers = {
                name: tool.fn
                for name, tool in mcp_server._tool_manager._tools.items()
            }
        else:
            self.tools = None
            self.tool_handlers = {}

    async def _execute_tool(self, tool_name: str, tool_args) -> str:
        """Execute a tool by name and return its result as a string."""
        handler = self.tool_handlers.get(tool_name)
        if not handler:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})
        if isinstance(tool_args, dict):
            result = await handler(**tool_args)
        elif isinstance(tool_args, list):
            result = await handler(*tool_args)
        else:
            result = await handler(tool_args)
        if isinstance(result, str):
            return result
        return json.dumps(result)

    @staticmethod
    def _merge_responses(role_results: list[tuple[str, dict]]) -> dict:
        """Return role results to the consumer without merging.

        Single role: return the result directly.
        Multiple roles: return a role-keyed dict so the consumer can
        combine or render each result however they see fit.
        """
        if len(role_results) == 1:
            return role_results[0][1]

        return {role_name: parsed for role_name, parsed in role_results}

    async def run(
        self,
        user_query: str,
        role: str | None = None,
        context: str | None = None,
        output_schema: str | None = None,
    ) -> dict:
        """Send query to LLM with role-based system prompt, return result."""
        if role is not None:
            roles = [role]
        else:
            cache_key = _cache_key(user_query, context)
            if self.cache_enabled and cache_key in self._classification_cache:
                roles = self._classification_cache[cache_key]
                self._classification_cache.move_to_end(cache_key)
            else:
                try:
                    roles = await classify_role(self.chat_lite, user_query, self._classification_prompt, self._valid_roles)
                except Exception as exc:
                    raise RuntimeError(f"Role classification failed: {exc}") from exc
                if self.cache_enabled:
                    self._classification_cache[cache_key] = roles
                    if len(self._classification_cache) > self.cache_size:
                        self._classification_cache.popitem(last=False)

        # Select roles: filter off-topic, cap by max_roles
        selected_roles = [r for r in roles if r != "off_topic"][:self.max_roles]

        if not selected_roles:
            off_topic_response = {"message": "I'm sorry, I'm not able to help with that query."}
            if self.verbose:
                return {
                    "response": off_topic_response,
                    "debug": {
                        "user_query": user_query,
                        "context": context,
                        "roles_matched": roles,
                        "roles_selected": [],
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "tools_used": [],
                        "assistant_messages": [],
                    },
                }
            return off_topic_response

        if context:
            user_content = f"Context:\n{context}\n\nQuery:\n{user_query}"
        else:
            user_content = user_query

        assistant_messages = []
        total_input_tokens = 0
        total_output_tokens = 0

        # LLM calls — one per selected role, in parallel, with native tool calling loop
        async def _run_role(role_to_run: str) -> tuple[str, dict]:
            defn = self._roles[role_to_run]
            system_prompt = defn.prompt
            schema = output_schema if output_schema else defn.schema
            system_prompt += (
                "\n\nIMPORTANT: Respond with ONLY a valid JSON object. "
                "Do not include any explanation, markdown, or text outside the JSON. "
                f"The JSON must follow this schema: {schema}"
            )

            if self.inject_date:
                system_prompt += f"\n\nToday's date is {date.today().isoformat()}."

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ]

            role_tools_used = []
            role_input_tokens = 0
            role_output_tokens = 0

            for round_idx in range(self.max_tool_rounds + 1):
                # Pass tools on all rounds except the last safety round
                pass_tools = self.tools if round_idx < self.max_tool_rounds else None
                # Only enforce JSON mode on the final round (no tools); on tool rounds,
                # json_mode can prevent some LLMs from making tool calls at all.
                json_mode = pass_tools is None
                # Force tool use on the first round when tools are available
                require_tool_use = pass_tools is not None and round_idx == 0
                result = await self.chat(messages, tools=pass_tools, json_mode=json_mode, require_tool_use=require_tool_use)
                role_input_tokens += result["input_tokens"]
                role_output_tokens += result["output_tokens"]

                if not result["tool_calls"]:
                    # When interpret_tool_response=True and the LLM responded on a
                    # non-json_mode round, append bridge messages and force one
                    # json_mode=True round to produce properly structured output.
                    if not json_mode and role_tools_used and self.interpret_tool_response is True:
                        messages.extend([
                            {"role": "assistant", "content": "I have retrieved the data from the tools."},
                            {"role": "user", "content": "Based on the tool results, provide your final response as a JSON object following the required output schema exactly."},
                        ])
                        result = await self.chat(messages, tools=None, json_mode=True, require_tool_use=False)
                        role_input_tokens += result["input_tokens"]
                        role_output_tokens += result["output_tokens"]
                    break  # Final text response

                # Execute tool calls in parallel
                tc_list = result["tool_calls"]
                outputs = await asyncio.gather(
                    *(self._execute_tool(tc["name"], tc["arguments"]) for tc in tc_list),
                    return_exceptions=True,
                )

                tool_results = []
                for tc, output in zip(tc_list, outputs):
                    role_tools_used.append(tc["name"])
                    if isinstance(output, Exception):
                        content = json.dumps({"error": f"Tool '{tc['name']}' failed: {output}"})
                        if self.verbose:
                            logger.warning("Tool '%s' failed: %s", tc["name"], output)
                    else:
                        content = output
                    tool_results.append({"id": tc["id"], "name": tc["name"], "content": content})

                if self.interpret_tool_response is False:
                    # Return raw tool outputs without sending back to LLM
                    combined = []
                    for tr in tool_results:
                        try:
                            combined.append(json.loads(tr["content"]))
                        except (json.JSONDecodeError, TypeError):
                            combined.append(tr["content"])
                    raw_text = json.dumps(combined[0] if len(combined) == 1 else combined)
                    result = {
                        "text": raw_text,
                        "input_tokens": role_input_tokens,
                        "output_tokens": role_output_tokens,
                        "tools_used": role_tools_used,
                        "tool_calls": [],
                        "assistant_message": result["assistant_message"],
                    }
                    return role_to_run, result

                messages.extend(build_tool_result_messages(self.llm, result["assistant_message"], tool_results))

            # Merge accumulated stats into the final result
            result["input_tokens"] = role_input_tokens
            result["output_tokens"] = role_output_tokens
            result["tools_used"] = role_tools_used
            return role_to_run, result

        role_results_raw = await asyncio.gather(*[_run_role(r) for r in selected_roles], return_exceptions=True)

        # Parse all results with isolation
        all_tools_used = []
        role_results = []
        for i, result_or_exc in enumerate(role_results_raw):
            role_run = selected_roles[i]
            if isinstance(result_or_exc, Exception):
                if self.verbose:
                    logger.warning("Role '%s' LLM call failed: %s", role_run, result_or_exc)
                continue
            role_run, result = result_or_exc
            total_input_tokens += result["input_tokens"]
            total_output_tokens += result["output_tokens"]
            all_tools_used.extend(result.get("tools_used", []))
            assistant_messages.append(result["assistant_message"])
            try:
                parsed = _extract_json(result["text"])
                role_results.append((role_run, parsed))
            except Exception as exc:
                if self.verbose:
                    logger.warning("Role '%s' JSON parse failed: %s", role_run, exc)

        # All roles failed — return error dict
        if not role_results:
            error_response = {"error": "All role executions failed.", "roles_attempted": selected_roles}
            if self.verbose:
                return {
                    "response": error_response,
                    "debug": {
                        "user_query": user_query,
                        "context": context,
                        "roles_matched": roles,
                        "roles_selected": selected_roles,
                        "input_tokens": total_input_tokens,
                        "output_tokens": total_output_tokens,
                        "tools_used": all_tools_used,
                        "assistant_messages": assistant_messages,
                    },
                }
            return error_response

        # Merge if multiple roles, otherwise return single result
        merged = self._merge_responses(role_results)

        if self.verbose:
            return {
                "response": merged,
                "debug": {
                    "user_query": user_query,
                    "context": context,
                    "roles_matched": roles,
                    "roles_selected": selected_roles,
                    "input_tokens": total_input_tokens,
                    "output_tokens": total_output_tokens,
                    "tools_used": all_tools_used,
                    "assistant_messages": assistant_messages,
                },
            }

        return merged
