"""figureout - A Python package."""

__version__ = "0.1.2"

from figureout.roles import RoleDefinition
from figureout.exceptions import OutputTokenLimitError, InputTokenLimitError, LLMError
from figureout.llm import LLM
from figureout.engine import FigureOut
