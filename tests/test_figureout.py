import asyncio
import json
import os
from unittest.mock import patch, MagicMock, AsyncMock

import figureout
from figureout import RoleDefinition
from figureout.exceptions import LLMError
from figureout.llm import LLM, build_tool_result_messages
from figureout.engine import FigureOut, classify_role


# Minimal role set used across tests
ROLES = {
    "discovery": RoleDefinition(
        prompt="You are a discovery agent.",
        schema='{"results": [{"id": int, "name": str}], "summary": str}',
        guideline="finding things, searching, discovering",
    ),
    "off_topic": RoleDefinition(
        prompt="Politely decline off-topic queries.",
        schema='{"message": str}',
        guideline="anything unrelated",
    ),
}


def test_version():
    assert figureout.__version__ == "0.1.0"


@patch("figureout.engine.get_llm_client")
def test_booking_concierge_init_defaults(mock_get_llm):
    mock_get_llm.return_value = MagicMock()
    pkg = FigureOut(roles=ROLES)
    assert pkg.llm == LLM.OPENAI
    assert pkg.verbose is False
    assert pkg.llm_version is None
    assert pkg.max_retries == 2


@patch("figureout.engine.get_llm_client")
def test_booking_concierge_init_with_llm(mock_get_llm):
    mock_get_llm.return_value = MagicMock()
    pkg = FigureOut(llm=LLM.CLAUDE, roles=ROLES)
    assert pkg.llm == LLM.CLAUDE
    assert mock_get_llm.call_count == 2


@patch("figureout.engine.get_llm_client")
def test_booking_concierge_init_with_llm_string(mock_get_llm):
    mock_get_llm.return_value = MagicMock()
    pkg = FigureOut(llm="gemini", roles=ROLES)
    assert pkg.llm == LLM.GEMINI


@patch("figureout.engine.get_llm_client")
def test_booking_concierge_init_verbose(mock_get_llm):
    mock_get_llm.return_value = MagicMock()
    pkg = FigureOut(verbose=True, roles=ROLES)
    assert pkg.verbose is True


@patch("figureout.engine.get_llm_client")
def test_booking_concierge_env_llm(mock_get_llm):
    mock_get_llm.return_value = MagicMock()
    with patch.dict(os.environ, {"FIGUREOUT_LLM": "claude"}):
        pkg = FigureOut(roles=ROLES)
    assert pkg.llm == LLM.CLAUDE


@patch("figureout.engine.get_llm_client")
def test_booking_concierge_env_verbose(mock_get_llm):
    mock_get_llm.return_value = MagicMock()
    with patch.dict(os.environ, {"FIGUREOUT_VERBOSE": "true"}):
        pkg = FigureOut(roles=ROLES)
    assert pkg.verbose is True


@patch("figureout.engine.get_llm_client")
def test_booking_concierge_constructor_overrides_env(mock_get_llm):
    mock_get_llm.return_value = MagicMock()
    with patch.dict(os.environ, {"FIGUREOUT_LLM": "claude"}):
        pkg = FigureOut(llm=LLM.GEMINI, roles=ROLES)
    assert pkg.llm == LLM.GEMINI


@patch("figureout.engine.get_llm_client")
def test_booking_concierge_env_llm_version(mock_get_llm):
    mock_get_llm.return_value = MagicMock()
    with patch.dict(os.environ, {"FIGUREOUT_LLM_VERSION": "gpt-4o"}):
        pkg = FigureOut(roles=ROLES)
    assert pkg.llm_version == "gpt-4o"


@patch("figureout.engine.get_llm_client")
def test_booking_concierge_no_roles_raises(mock_get_llm):
    mock_get_llm.return_value = MagicMock()
    env = {k: v for k, v in os.environ.items() if k != "FIGUREOUT_ROLES"}
    with patch.dict(os.environ, env, clear=True):
        try:
            FigureOut()
            assert False, "Expected ValueError"
        except ValueError as e:
            assert "roles" in str(e).lower()


def test_classify_role():
    mock_chat = AsyncMock(return_value={
        "text": json.dumps({"roles": ["discovery"]}),
        "input_tokens": 10,
        "output_tokens": 5,
        "tools_used": [],
    })
    prompt = "You are a classifier."
    valid = {"discovery", "off_topic"}
    result = asyncio.run(classify_role(mock_chat, "find something", prompt, valid))
    assert result == ["discovery"]


def test_classify_role_filters_unknown():
    mock_chat = AsyncMock(return_value={
        "text": json.dumps({"roles": ["discovery", "nonexistent_role"]}),
        "input_tokens": 10,
        "output_tokens": 5,
        "tools_used": [],
    })
    prompt = "You are a classifier."
    valid = {"discovery", "off_topic"}
    result = asyncio.run(classify_role(mock_chat, "find something", prompt, valid))
    assert result == ["discovery"]


@patch("figureout.engine.get_llm_client")
def test_booking_concierge_init_max_retries(mock_get_llm):
    mock_get_llm.return_value = MagicMock()
    pkg = FigureOut(max_retries=5, roles=ROLES)
    assert pkg.max_retries == 5
    assert mock_get_llm.call_count == 2


@patch("figureout.engine.get_llm_client")
def test_booking_concierge_env_max_retries(mock_get_llm):
    mock_get_llm.return_value = MagicMock()
    with patch.dict(os.environ, {"FIGUREOUT_MAX_RETRIES": "3"}):
        pkg = FigureOut(roles=ROLES)
    assert pkg.max_retries == 3


@patch("figureout.engine.get_llm_client")
def test_run_all_roles_fail_returns_error_dict(mock_get_llm):
    mock_chat = AsyncMock(side_effect=Exception("LLM unavailable"))
    mock_get_llm.return_value = mock_chat
    pkg = FigureOut(roles=ROLES)

    result = asyncio.run(pkg.run("find something", role="discovery"))
    assert "error" in result
    assert result["error"] == "All role executions failed."
    assert "roles_attempted" in result
    assert "discovery" in result["roles_attempted"]


@patch("figureout.engine.get_llm_client")
def test_booking_concierge_init_lite_override(mock_get_llm):
    mock_get_llm.return_value = MagicMock()
    pkg = FigureOut(lite_llm_version="my-custom-model", roles=ROLES)
    assert pkg.lite_llm_version == "my-custom-model"
    mock_get_llm.assert_any_call(LLM.OPENAI, api_key=None, llm_version="my-custom-model", max_output_tokens=16384, max_retries=2, timeout=120.0)


@patch("figureout.engine.get_llm_client")
def test_booking_concierge_env_lite_llm_version(mock_get_llm):
    mock_get_llm.return_value = MagicMock()
    with patch.dict(os.environ, {"FIGUREOUT_LITE_LLM_VERSION": "gpt-4.1-nano"}):
        pkg = FigureOut(roles=ROLES)
    assert pkg.lite_llm_version == "gpt-4.1-nano"


@patch("figureout.engine.get_llm_client")
def test_classification_cache_hit(mock_get_llm):
    mock_classify_chat = AsyncMock(return_value={
        "text": json.dumps({"roles": ["discovery"]}),
        "input_tokens": 10,
        "output_tokens": 5,
        "tools_used": [],
    })
    mock_main_chat = AsyncMock(return_value={
        "text": json.dumps({"results": [], "summary": "No results"}),
        "input_tokens": 20,
        "output_tokens": 10,
        "tools_used": [],
        "tool_calls": [],
        "assistant_message": {"role": "assistant", "content": "{}"},
    })
    mock_get_llm.side_effect = [mock_main_chat, mock_classify_chat]
    pkg = FigureOut(roles=ROLES)
    pkg.chat_lite = mock_classify_chat
    pkg.chat = mock_main_chat
    pkg._classification_cache.clear()

    asyncio.run(pkg.run("find something"))
    assert mock_classify_chat.call_count == 1
    asyncio.run(pkg.run("find something"))
    assert mock_classify_chat.call_count == 1  # cache hit
    assert mock_main_chat.call_count == 2
    pkg._classification_cache.clear()


@patch("figureout.engine.get_llm_client")
def test_classification_cache_miss(mock_get_llm):
    mock_classify_chat = AsyncMock(return_value={
        "text": json.dumps({"roles": ["discovery"]}),
        "input_tokens": 10,
        "output_tokens": 5,
        "tools_used": [],
    })
    mock_main_chat = AsyncMock(return_value={
        "text": json.dumps({"results": [], "summary": "No results"}),
        "input_tokens": 20,
        "output_tokens": 10,
        "tools_used": [],
        "tool_calls": [],
        "assistant_message": {"role": "assistant", "content": "{}"},
    })
    mock_get_llm.side_effect = [mock_main_chat, mock_classify_chat]
    pkg = FigureOut(roles=ROLES)
    pkg.chat_lite = mock_classify_chat
    pkg.chat = mock_main_chat
    pkg._classification_cache.clear()

    asyncio.run(pkg.run("find something"))
    assert mock_classify_chat.call_count == 1
    asyncio.run(pkg.run("find something else"))
    assert mock_classify_chat.call_count == 2  # cache miss
    pkg._classification_cache.clear()


@patch("figureout.engine.get_llm_client")
def test_native_tool_calling_loop(mock_get_llm):
    """Test that native tool calling executes tools and loops back to LLM."""
    tool_call_response = {
        "text": "",
        "input_tokens": 10,
        "output_tokens": 5,
        "tools_used": ["get_results"],
        "tool_calls": [
            {"id": "call_1", "name": "get_results", "arguments": {"query": "test"}},
        ],
        "assistant_message": {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {"id": "call_1", "type": "function", "function": {"name": "get_results", "arguments": '{"query": "test"}'}}
            ],
        },
    }
    final_response = {
        "text": json.dumps({"results": [{"id": 1, "name": "Thing"}], "summary": "Found it"}),
        "input_tokens": 20,
        "output_tokens": 15,
        "tools_used": [],
        "tool_calls": [],
        "assistant_message": {"role": "assistant", "content": "{}"},
    }
    mock_chat = AsyncMock(side_effect=[tool_call_response, final_response])
    mock_get_llm.return_value = mock_chat

    mock_tool = MagicMock()
    mock_tool.description = "Search for results"
    mock_tool.parameters = {"type": "object", "properties": {"query": {"type": "string"}}}
    mock_tool.fn = AsyncMock(return_value=json.dumps([{"id": 1, "name": "Thing"}]))
    mock_server = MagicMock()
    mock_server._tool_manager._tools = {"get_results": mock_tool}

    pkg = FigureOut(mcp_server=mock_server, roles=ROLES)

    result = asyncio.run(pkg.run("find something", role="discovery"))
    assert "results" in result
    assert mock_chat.call_count == 2
    mock_tool.fn.assert_called_once_with(query="test")


@patch("figureout.engine.get_llm_client")
def test_no_tools_no_loop(mock_get_llm):
    """Test that without tools, no tool execution happens."""
    final_response = {
        "text": json.dumps({"results": [], "summary": "No results"}),
        "input_tokens": 20,
        "output_tokens": 10,
        "tools_used": [],
        "tool_calls": [],
        "assistant_message": {"role": "assistant", "content": "{}"},
    }
    mock_chat = AsyncMock(return_value=final_response)
    mock_get_llm.return_value = mock_chat

    pkg = FigureOut(roles=ROLES)
    result = asyncio.run(pkg.run("find something", role="discovery"))
    assert "results" in result
    assert mock_chat.call_count == 1


@patch("figureout.engine.get_llm_client")
def test_json_mode_passed_to_chat(mock_get_llm):
    """Test that json_mode=True is passed to the chat callable."""
    final_response = {
        "text": json.dumps({"results": [], "summary": "No results"}),
        "input_tokens": 20,
        "output_tokens": 10,
        "tools_used": [],
        "tool_calls": [],
        "assistant_message": {"role": "assistant", "content": "{}"},
    }
    mock_chat = AsyncMock(return_value=final_response)
    mock_get_llm.return_value = mock_chat

    pkg = FigureOut(roles=ROLES)
    asyncio.run(pkg.run("find something", role="discovery"))

    assert mock_chat.call_count == 1
    _, kwargs = mock_chat.call_args
    assert kwargs.get("json_mode") is True


@patch("figureout.engine.get_llm_client")
def test_interpret_tool_response_default_none(mock_get_llm):
    mock_get_llm.return_value = MagicMock()
    pkg = FigureOut(roles=ROLES)
    assert pkg.interpret_tool_response is None


@patch("figureout.engine.get_llm_client")
def test_interpret_tool_response_constructor_true(mock_get_llm):
    mock_get_llm.return_value = MagicMock()
    pkg = FigureOut(interpret_tool_response=True, roles=ROLES)
    assert pkg.interpret_tool_response is True


@patch("figureout.engine.get_llm_client")
def test_interpret_tool_response_constructor_false(mock_get_llm):
    mock_get_llm.return_value = MagicMock()
    pkg = FigureOut(interpret_tool_response=False, roles=ROLES)
    assert pkg.interpret_tool_response is False


@patch("figureout.engine.get_llm_client")
def test_interpret_tool_response_env(mock_get_llm):
    mock_get_llm.return_value = MagicMock()
    with patch.dict(os.environ, {"FIGUREOUT_INTERPRET_TOOL_RESPONSE": "false"}):
        pkg = FigureOut(roles=ROLES)
    assert pkg.interpret_tool_response is False


@patch("figureout.engine.get_llm_client")
def test_interpret_tool_response_false_returns_raw_output(mock_get_llm):
    """Test that interpret_tool_response=False returns raw tool output with only 1 LLM call."""
    tool_call_response = {
        "text": "",
        "input_tokens": 10,
        "output_tokens": 5,
        "tools_used": ["get_results"],
        "tool_calls": [
            {"id": "call_1", "name": "get_results", "arguments": {"query": "test"}},
        ],
        "assistant_message": {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {"id": "call_1", "type": "function", "function": {"name": "get_results", "arguments": '{"query": "test"}'}}
            ],
        },
    }
    mock_chat = AsyncMock(return_value=tool_call_response)
    mock_get_llm.return_value = mock_chat

    mock_tool = MagicMock()
    mock_tool.description = "Search for results"
    mock_tool.parameters = {"type": "object", "properties": {"query": {"type": "string"}}}
    mock_tool.fn = AsyncMock(return_value=json.dumps([{"id": 1, "name": "Thing"}]))
    mock_server = MagicMock()
    mock_server._tool_manager._tools = {"get_results": mock_tool}

    pkg = FigureOut(mcp_server=mock_server, interpret_tool_response=False, roles=ROLES)

    result = asyncio.run(pkg.run("find something", role="discovery"))
    assert mock_chat.call_count == 1
    mock_tool.fn.assert_called_once_with(query="test")
    assert isinstance(result, list)
    assert result[0]["id"] == 1
