# Contributing to FigureOut

Thank you for your interest in contributing! FigureOut is a lightweight project and contributions of all sizes are welcome — bug fixes, new provider support, documentation improvements, and example applications.

## Table of Contents

- [Getting Started](#getting-started)
- [Ways to Contribute](#ways-to-contribute)
- [Development Setup](#development-setup)
- [Running Tests](#running-tests)
- [Submitting a Pull Request](#submitting-a-pull-request)
- [Adding a New LLM Provider](#adding-a-new-llm-provider)
- [Code Style](#code-style)
- [Reporting Bugs](#reporting-bugs)

---

## Getting Started

1. [Fork the repository](https://github.com/balajeekalyan/figureout/fork)
2. Clone your fork:
   ```bash
   git clone https://github.com/<your-username>/figureout.git
   cd figureout
   ```
3. Create a branch for your change:
   ```bash
   git checkout -b your-feature-or-fix
   ```

---

## Ways to Contribute

- **Bug fixes** — open an issue first if the bug isn't already tracked
- **New LLM provider support** — see [Adding a New LLM Provider](#adding-a-new-llm-provider)
- **New example applications** — add a folder under `examples/` following the existing structure
- **Documentation** — improve the README, fix typos, or add docstrings
- **Tests** — increase coverage for existing modules

---

## Development Setup

Install the package in editable mode with all development dependencies:

```bash
pip install -e ".[dev]"
```

To work with a specific provider locally, install its extra as well:

```bash
pip install -e ".[dev,openai]"   # or gemini, claude, meta, mistral, groq
```

Copy `.env.example` to `.env` and add your API keys for any providers you intend to test:

```bash
cp .env.example .env
```

---

## Running Tests

```bash
pytest                                          # full suite
pytest tests/test_figureout.py::test_name      # single test
```

Tests use mocking and do not require live API keys. All new code should include tests. Keep coverage in line with existing modules.

---

## Submitting a Pull Request

1. Make sure `pytest` passes with no failures.
2. Keep changes focused — one fix or feature per PR.
3. Write a clear PR description explaining what changed and why.
4. Reference any related issue (e.g. `Closes #42`).

PRs that add a new feature without tests will not be merged.

---

## Adding a New LLM Provider

Provider implementations live in `figureout/llm.py`. To add support for a new provider:

1. Add a new member to the `LLM` enum.
2. Implement the `_call_llm` branch (and tool-handling logic if the provider supports tools).
3. Add the provider's SDK as an optional extra in `pyproject.toml`.
4. Add a row to the **Supported LLM Providers** table in `README.md`.
5. Add tests covering at least the basic call path (mock the SDK client).

Look at the existing OpenAI and Gemini implementations as reference — they cover the two main patterns (OpenAI-compatible tool_calls vs. provider-specific formats).

---

## Code Style

- Follow the existing async/await patterns throughout.
- Use type hints for all new public functions and methods.
- Do not introduce new required dependencies in the base install — use optional extras.
- Keep the core library lean. If something is only needed for one provider, gate it behind a lazy import.

There is no formatter enforced yet; just match the surrounding code style.

---

## Reporting Bugs

Open a [GitHub Issue](https://github.com/balajeekalyan/figureout/issues) and include:

- FigureOut version (`pip show figureout`)
- Python version
- LLM provider and model
- Minimal code snippet that reproduces the problem
- Full error traceback

---

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
