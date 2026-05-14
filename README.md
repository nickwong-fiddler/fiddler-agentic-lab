# Fiddler Agentic Monitoring — Hands-On Lab

A 60-minute hands-on lab introducing Fiddler's agentic AI monitoring features. Participants build a working LangGraph ReAct agent that analyzes synthetic e-commerce data, then instrument it with Fiddler to gain real-time observability, auto-grade responses with an Answer Relevance evaluator, and add a Fast Safety Guardrail.

## Getting started

1. Read [`PREREQUISITES.md`](PREREQUISITES.md) and complete the pre-lab setup **before** the session.
2. On the day of the lab, open [`Fiddler_Ecommerce_Agent.ipynb`](Fiddler_Ecommerce_Agent.ipynb) and follow it from top to bottom.

## What you'll learn

- Auto-instrumenting a LangGraph agent with `fiddler-langgraph` (3 lines of code)
- Capturing hierarchical traces (chain → tool → llm spans) with conversation grouping
- Configuring Fiddler Evaluator Rules for continuous answer-relevance grading
- Calling Fiddler Guardrails (`/v3/guardrails/ftl-safety`) for real-time prompt safety

## Questions?

Contact your instructor.
