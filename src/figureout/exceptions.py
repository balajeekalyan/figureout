"""Exception classes for FigureOut."""


class OutputTokenLimitError(Exception):
    """Raised when an LLM response is truncated due to hitting the max output token limit."""
    def __init__(self, llm: str, model: str, max_output_tokens: int, output_tokens: int):
        self.llm = llm
        self.model = model
        self.max_output_tokens = max_output_tokens
        self.output_tokens = output_tokens
        super().__init__(
            f"{llm} ({model}) response truncated: generated {output_tokens} tokens, "
            f"hitting the max_output_tokens limit of {max_output_tokens}. "
            f"Increase max_output_tokens via the FIGUREOUT_MAX_OUTPUT_TOKENS env var "
            f"or the max_output_tokens constructor param."
        )


class InputTokenLimitError(Exception):
    """Raised when the input exceeds the model's context window limit."""
    def __init__(self, llm: str, model: str, detail: str = ""):
        self.llm = llm
        self.model = model
        detail_suffix = f" {detail}" if detail else ""
        super().__init__(
            f"{llm} ({model}) request rejected: input exceeds the model's context window limit.{detail_suffix} "
            f"Reduce the input size by lowering max_roles, shortening the context/query, "
            f"or using fewer tools."
        )


class LLMError(Exception):
    """Transient LLM provider error (rate limit, timeout, connection)."""
    def __init__(self, llm: str, model: str, cause: Exception):
        self.llm = llm
        self.model = model
        self.cause = cause
        super().__init__(
            f"{llm} ({model}) failed after retries: {cause}"
        )
