---
title: "FigureOut: A Python package for routing user queries to specialized AI agents"
tags:
    - Python
    - artificial intelligence
    - large language models
    - multi-agent
    - query routing

authors:
    - name: Balajee Kalyanasundaram 
      affiliation: "1"
affiliations:
    - name: Independent Researcher
      index: 1
date: 8 March 2026
bibliography: paper.bib
---

# Summary

`FigureOut` is a Python package designed to help developers easily add Artificial Intelligence (AI) to any use case. It classifies users’ natural language queries and routes them to an agent defined by the developer. If Large Language Models (LLM) orchestration is needed, developers can define Model Context Protocol (MCP) [@MCP2024] tools using FastMCP [@FastMCP2024] and provide the instance to the package.

The package comes with 10 core capabilities:

1. Classifies the user’s query and routes it to dedicated agents
2. Developers can define custom system prompts, guidelines, and a JavaScript Object Notation (JSON) output schema. They can configure the off-topic role using RoleDefinition to assign specific behavior for handling irrelevant queries.
3. The package supports integration with six major LLMs: Google's Gemini [@GeminiTeam2023], OpenAI's ChatGPT [@Vaswani2017], Anthropic's Claude [@Brown2020], Meta's Llama [@Touvron2023], Groq Meta Llama 3 inference model [@Groq2024] and Mistral [@Jiang2023].
4. The package connects to real-time data using FastMCP, a framework for managing rapid message protocols. Developers use FastMCP to link databases or external APIs, then pass the FastMCP instance to the package. The agent uses MCP tools, a set of utilities for handling MC protocol queries, to resolve the request.
5. Developers can configure multiple roles per agent, each with its own set of agent actions. Several roles may resolve a single query, and if tool execution is needed, the package runs them in parallel.
6. The package always returns a structured JSON response and ensures the LLM follows the developer-defined output structure.
7. The package injects the server date into the LLM context. This enables the LLM to answer date-related queries, including those with expressions like “today” or “this week.” Developers can disable this feature in the configuration settings.
8. By default, the package interprets tool responses by summarizing and explaining results from external programs. Developers can disable this to receive raw responses and save tokens. A Least Recently Used (LRU) cache stores tokens for repeat queries and results.
9. Verbose debug mode gives detailed troubleshooting information, including role selection, token counts, tool calls, and assistant messages. 
10. The package retries LLM calls after failures, with configurable retry limits. Failed roles or tool responses will not cause the whole request to fail.

# Statement of Need

Agentic AI’s popularity is surging. Many companies are exploring ways to embed LLMs into existing applications to upgrade user experiences. When integrating LLMs, it is essential to supply precise context so that the model can deliver accurate answers to user queries. For example, if you are building an app to discover restaurants and book reservations, you want the LLM agent to discern the user’s intent. Responses must be customized to the data in your dataset. With `FigureOut`, you can accomplish that with a few lines of code. The developer can orchestrate based on the LLM's response, or let the LLM orchestrate by providing the tools it needs using MCP. Because of its simplicity, getting started is easier. 

Another big pain point with LLM integrations is Observability. Developers need to know the LLM’s interpretation of the user’s query, the number of tokens used to process the request, the tokens used to send the response, the roles selected, and the tool calling. `FigureOut` provides these in-depth insights within the package so developers can see under the hood, set up analytics, and debug when issues arise. 

LLM integrations could considerably increase costs. Many developers are looking for ways to reduce the number of LLM calls. `FigureOut` proactively provides ways to save tokens by caching repeated user requests and LLM responses, and by returning raw JSON tool responses. Developers do not need to install other packages, as these features are self-contained in the package and are available implicitly.

This package was created solely to help the developer community to integrate AI into any use case they choose. It is very flexible, with configuration control for most of its features. When developers use `FigureOut`, they do not need to install many dependencies to achieve robustness, resilience, and observability, as the package provides them by default. The package abstracts most of the integration code and provides a single entry point, dramatically reducing the lines of code a developer needs to write to onboard a single LLM provider.

# References
