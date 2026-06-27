---
name: qwen-cloud-call
description: Encodes the correct DashScope-compatible call pattern for Qwen Cloud models (qwen3.6-flash, qwen3.7-max) with LangGraph, including structured output and error handling.
---

# Qwen Cloud API Call Protocol

This skill dictates the exact protocol for interacting with Alibaba Cloud's Qwen models via the DashScope API. Adherence to this protocol is **mandatory** for all agent LLM calls to ensure evaluation rubric points for "Performance Optimization" and "Sophisticated Use of APIs".

## 1. Context & Rationale
The Hackathon judging rubric explicitly scores model routing efficiency. We must not waste large model cycles on deterministic tasks, nor under-resource the complex reasoning steps.

## 2. Model Routing Matrix
| Agent Role | Model Name | Capability Mode | Justification |
| :--- | :--- | :--- | :--- |
| **Orchestrator** | `qwen-max` | Thinking Mode (Reasoning) | Requires multi-hop logic to resolve competing proposals and evaluate trade-offs. |
| **Geo-Clustering Agent** | `qwen-turbo` | Function Calling | Narrow spatial mapping task using external MCP data. |
| **Temporal-Constraint Agent** | `qwen-turbo` | Function Calling | Narrow scheduling task. |
| **Dependency Agent** | `qwen-turbo` | Function Calling | Strict graph logic. |
| **Memory Agent** | `qwen-turbo` | Structured Output (JSON) | Pure extraction and summarization for DB persistence. |

## 3. Implementation Blueprint (LangGraph + DashScope)

### Authentication
Always rely on `DASHSCOPE_API_KEY` from the environment. Do not hardcode keys.

### Instantiation Pattern (Python)
Use `langchain-community` integration for DashScope.

```python
import os
from langchain_community.chat_models.tongyi import ChatTongyi

# Example: Orchestrator Instantiation
def get_orchestrator_llm():
    return ChatTongyi(
        model_name="qwen-max",
        dashscope_api_key=os.environ.get("DASHSCOPE_API_KEY"),
        # Enable extended reasoning parameters if supported via LangChain wrapper
        max_retries=3,
    )

# Example: Specialist Agent Instantiation
def get_specialist_llm():
    return ChatTongyi(
        model_name="qwen-turbo",
        dashscope_api_key=os.environ.get("DASHSCOPE_API_KEY"),
        max_retries=3,
    )
```

## 4. Error Handling & Resilience
- **Rate Limits (429)**: Wrap all calls in a retry loop using tenacity (`@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))`).
- **Context Window Exceeded**: Provide dynamic truncation logic for memory recall if history exceeds 32k tokens.

## 5. Security & Privacy
- Strip PII (Personal Identifiable Information) before passing memory states to the LLM.
- Never log raw prompts containing user location data.
