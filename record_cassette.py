"""
record_cassette.py — Record LLM interactions for the offline lab variant.

Run this ONCE before the lab to capture LLM responses for the canonical
sample queries. The output cassette.json is consumed by the offline notebook
(`Fiddler_Ecommerce_Agent_Offline.ipynb`) via a ReplayChatModel that
returns recorded responses without making any external LLM calls.

Usage:
    export OPENAI_API_KEY=sk-...
    python record_cassette.py --output cassette.json [--model gpt-4o-mini]

When to re-record:
    Re-run this script any time SYSTEM_PROMPT, the tool definitions, the
    dataset, or SAMPLE_QUERIES change. The cassette stores hashes of
    SYSTEM_PROMPT and the tool schemas; the notebook will warn if the
    notebook's prompt/tools have drifted from what was recorded.

Intentional duplication:
    The dataset, four agent tools, and SYSTEM_PROMPT below are deliberately
    duplicated verbatim from `Fiddler_Ecommerce_Agent.ipynb`. This keeps the
    script self-contained (single-file, no shared module to install or
    import). If the duplication ever causes drift bugs, extract a
    lab_common.py module shared by both this script and the notebook.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatResult
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent


# ---------------------------------------------------------------------------
# Canonical sample queries — single source of truth for the lab.
# Kept in sync with the queries in Fiddler_Ecommerce_Agent.ipynb.
# ---------------------------------------------------------------------------

SAMPLE_QUERIES: list[str] = [
    # § "Run the Agent" — the five baseline sample queries
    "What are the top 5 products by total revenue?",
    "What is the average order value by region?",
    "Are there any anomalies in revenue?",
    "How many orders do we have in each category?",
    "Show me the monthly revenue trend.",
    # § 3 — re-run after instrumentation (some duplicates dedupe at fingerprint level)
    "What are the top 5 products by total revenue?",
    "Show me the monthly revenue trend.",
    # § 4 — Evaluator Rule trigger queries (third one is intentionally off-topic)
    "What are the top 3 products by total revenue?",
    "How does region affect average order value?",
    "Tell me a joke about pirates.",
    # § 5 — Guardrail demo (only the benign one — adversarial is blocked before LLM)
    "What are the top 3 products by revenue?",
]


# ---------------------------------------------------------------------------
# Synthetic dataset — DUPLICATED VERBATIM from the notebook.
# np.random.seed(42) ensures bit-identical df between recording and replay.
# ---------------------------------------------------------------------------

def build_dataset() -> pd.DataFrame:
    np.random.seed(42)
    NUM_ROWS = 500

    PRODUCTS = {
        "Wireless Headphones": {"category": "Electronics",    "price_range": (49.99, 149.99)},
        "Running Shoes":      {"category": "Sports",         "price_range": (79.99, 199.99)},
        "Coffee Maker":       {"category": "Home & Kitchen", "price_range": (29.99, 89.99)},
        "Yoga Mat":           {"category": "Sports",         "price_range": (19.99, 59.99)},
        "Laptop Stand":       {"category": "Electronics",    "price_range": (24.99, 79.99)},
        "Water Bottle":       {"category": "Sports",         "price_range": (9.99, 34.99)},
        "Desk Lamp":          {"category": "Home & Kitchen", "price_range": (19.99, 69.99)},
        "Bluetooth Speaker":  {"category": "Electronics",    "price_range": (39.99, 129.99)},
        "Backpack":           {"category": "Accessories",    "price_range": (29.99, 99.99)},
        "Sunglasses":         {"category": "Accessories",    "price_range": (14.99, 79.99)},
    }

    FIRST_NAMES = [
        "James", "Sarah", "Michael", "Emily", "David", "Jessica", "Robert",
        "Ashley", "William", "Amanda", "Daniel", "Stephanie", "Christopher",
        "Jennifer", "Matthew", "Elizabeth", "Andrew", "Lauren", "Joshua", "Megan",
    ]
    LAST_NAMES = [
        "Smith", "Johnson", "Williams", "Brown", "Jones",
        "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
    ]
    REGIONS = ["North", "South", "East", "West"]

    product_names = list(PRODUCTS.keys())
    chosen_products = np.random.choice(product_names, NUM_ROWS)

    data: dict[str, list[Any]] = {
        "order_id": [f"ORD-{i + 1001}" for i in range(NUM_ROWS)],
        "date": [
            (datetime(2024, 1, 1) + timedelta(days=int(np.random.randint(0, 365))))
            .strftime("%Y-%m-%d")
            for _ in range(NUM_ROWS)
        ],
        "customer_name": [
            f"{np.random.choice(FIRST_NAMES)} {np.random.choice(LAST_NAMES)}"
            for _ in range(NUM_ROWS)
        ],
        "email": [],
        "phone": [],
        "product": list(chosen_products),
        "category": [PRODUCTS[p]["category"] for p in chosen_products],
        "quantity": list(np.random.randint(1, 6, NUM_ROWS)),
        "unit_price": [
            round(float(np.random.uniform(*PRODUCTS[p]["price_range"])), 2)
            for p in chosen_products
        ],
        "region": list(np.random.choice(REGIONS, NUM_ROWS)),
    }

    for name in data["customer_name"]:
        first, last = name.lower().split()
        data["email"].append(f"{first}.{last}@email.com")
        data["phone"].append(
            f"({np.random.randint(200, 999)}) "
            f"{np.random.randint(100, 999)}-{np.random.randint(1000, 9999)}"
        )

    df = pd.DataFrame(data)
    df["revenue"] = (df["quantity"] * df["unit_price"]).round(2)
    return df


# Module-level df so the @tool functions below can close over it.
df = build_dataset()


# ---------------------------------------------------------------------------
# Agent tools — DUPLICATED VERBATIM from the notebook.
# ---------------------------------------------------------------------------

@tool
def lookup_orders(sort_by: str, limit: str, filter_column: str, filter_value: str) -> str:
    """Look up orders from the e-commerce dataset.

    Args:
        sort_by: Column to sort by. One of: revenue, quantity, unit_price, date.
        limit: Number of rows to return. Example: 5, 10, 20.
        filter_column: Column to filter on. One of: product, category, region, all.
        filter_value: Value to filter for. Use 'all' when filter_column is 'all'.
    """
    business_cols = ["order_id", "date", "product", "category",
                     "quantity", "unit_price", "revenue", "region"]
    result = df[business_cols].copy()

    if filter_column != "all" and filter_value != "all":
        if filter_column not in result.columns:
            return "Error: filter_column must be one of: product, category, region, all."
        result = result[result[filter_column].str.contains(filter_value, case=False, na=False)]

    if sort_by in result.columns:
        result = result.sort_values(sort_by, ascending=False)

    try:
        n = int(limit)
    except ValueError:
        n = 10

    result = result.head(n)

    if result.empty:
        return "No matching orders found."
    return result.to_string(index=False)


@tool
def compute_statistics(column: str, operation: str, group_by: str) -> str:
    """Compute an aggregate statistic on a numeric column.

    Args:
        column: Numeric column. One of: quantity, unit_price, revenue.
        operation: Aggregate function. One of: mean, sum, count, min, max, describe.
        group_by: Grouping column. One of: product, category, region, none.
    """
    valid_columns = ("quantity", "unit_price", "revenue")
    valid_ops = ("mean", "sum", "count", "min", "max", "describe")
    valid_groups = ("product", "category", "region", "none")

    if column not in valid_columns:
        return f"Error: column must be one of {valid_columns}."
    if operation not in valid_ops:
        return f"Error: operation must be one of {valid_ops}."
    if group_by not in valid_groups:
        return f"Error: group_by must be one of {valid_groups}."

    if group_by == "none" or operation == "describe":
        return (
            f"Statistics for {column}:\n"
            f"{df[column].describe().round(2).to_string()}"
        )

    result = getattr(df.groupby(group_by)[column], operation)()
    return (
        f"{operation.capitalize()} of {column} by {group_by}:\n"
        f"{result.round(2).to_string()}"
    )


@tool
def detect_anomalies(column: str) -> str:
    """Find values more than 2 standard deviations from the mean.

    Args:
        column: Numeric column. One of: quantity, unit_price, revenue.
    """
    valid_columns = ("quantity", "unit_price", "revenue")
    if column not in valid_columns:
        return f"Error: column must be one of {valid_columns}."

    mean, std = df[column].mean(), df[column].std()
    lower, upper = mean - 2 * std, mean + 2 * std
    anomalies = df[(df[column] < lower) | (df[column] > upper)]

    if anomalies.empty:
        return f"No anomalies in {column}. Mean: {mean:.2f}, Std: {std:.2f}."

    cols = ["order_id", "date", "product", "category", column, "region"]
    return (
        f"Found {len(anomalies)} anomalies in {column} "
        f"(outside {lower:.2f} to {upper:.2f}):\n"
        f"{anomalies[cols].to_string(index=False)}"
    )


@tool
def get_monthly_trend(column: str, operation: str) -> str:
    """Get monthly aggregated trend for a numeric column.

    Args:
        column: Numeric column. One of: quantity, unit_price, revenue.
        operation: Aggregate function. One of: sum, mean, count.
    """
    valid_columns = ("quantity", "unit_price", "revenue")
    valid_ops = ("sum", "mean", "count")

    if column not in valid_columns:
        return f"Error: column must be one of {valid_columns}."
    if operation not in valid_ops:
        return f"Error: operation must be one of {valid_ops}."

    monthly = df.copy()
    monthly["month"] = pd.to_datetime(monthly["date"]).dt.to_period("M").astype(str)
    result = getattr(monthly.groupby("month")[column], operation)()
    return (
        f"Monthly {operation} of {column}:\n"
        f"{result.round(2).to_string()}"
    )


TOOLS = [lookup_orders, compute_statistics, detect_anomalies, get_monthly_trend]


# ---------------------------------------------------------------------------
# System prompt — DUPLICATED VERBATIM from the notebook.
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = (
    "You are an e-commerce data analysis assistant. You help users analyze "
    "sales data by answering questions about orders, products, revenue, "
    "and trends.\n\n"
    "Use the available tools to query the dataset, compute statistics, "
    "detect anomalies, and show trends. Always base your answers on the "
    "actual data returned by the tools. Do not make up numbers or provide "
    "information that is not in the dataset.\n\n"
    "If a user asks a question unrelated to e-commerce data analysis, "
    "politely decline.\n\n"
    "Never expose customer personal information such as names, emails, "
    "or phone numbers."
)


# ---------------------------------------------------------------------------
# Fingerprinting + serialization helpers
# ---------------------------------------------------------------------------

def _serialize_message(msg: BaseMessage) -> dict[str, Any]:
    """Canonicalize a LangChain message into a stable dict for fingerprinting.

    We include role/content/name/tool_call_id and any tool_calls on AIMessages.
    We deliberately exclude transient fields like response_metadata, id, and
    usage_metadata so that fingerprints remain stable across re-runs.
    """
    out: dict[str, Any] = {
        "type": msg.type,
        "content": msg.content,
    }
    name = getattr(msg, "name", None)
    if name is not None:
        out["name"] = name
    tool_call_id = getattr(msg, "tool_call_id", None)
    if tool_call_id is not None:
        out["tool_call_id"] = tool_call_id
    tool_calls = getattr(msg, "tool_calls", None)
    if tool_calls:
        # Each tool_call: {name, args, id, type}. Drop id (transient).
        out["tool_calls"] = [
            {"name": tc["name"], "args": tc.get("args", {})}
            for tc in tool_calls
        ]
    return out


def _serialize_tool_schemas(tools: list) -> list[dict[str, Any]]:
    """Get a stable JSON-serializable representation of the tool schemas."""
    schemas = []
    for t in tools:
        schemas.append({
            "name": t.name,
            "description": t.description,
            "args_schema": t.args,  # dict of {arg_name: type}
        })
    return schemas


def fingerprint(messages: list[BaseMessage], tool_schemas: list[dict]) -> str:
    """SHA-256 over canonicalized messages + tool schemas. Stable across runs."""
    payload = {
        "messages": [_serialize_message(m) for m in messages],
        "tools": tool_schemas,
    }
    blob = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _hash(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _serialize_ai_message(msg: AIMessage) -> dict[str, Any]:
    """Capture an AIMessage in a form ReplayChatModel can reconstruct from."""
    out: dict[str, Any] = {
        "content": msg.content,
        "additional_kwargs": dict(msg.additional_kwargs or {}),
    }
    if msg.tool_calls:
        # Preserve full tool_call structure including id (LangGraph needs it
        # to correlate tool responses back to the call).
        out["tool_calls"] = [
            {
                "name": tc["name"],
                "args": tc.get("args", {}),
                "id": tc.get("id"),
                "type": tc.get("type", "tool_call"),
            }
            for tc in msg.tool_calls
        ]
    if getattr(msg, "usage_metadata", None):
        out["usage_metadata"] = dict(msg.usage_metadata)
    if getattr(msg, "response_metadata", None):
        # Keep only stable fields useful for the trace UI
        rm = msg.response_metadata
        out["response_metadata"] = {
            "model_name": rm.get("model_name"),
            "finish_reason": rm.get("finish_reason"),
        }
    return out


# ---------------------------------------------------------------------------
# Recording adapter — monkey-patches ChatOpenAI._generate to capture each
# (messages → AIMessage) pair before returning. We use monkey-patch instead
# of subclassing because:
#   1. ChatOpenAI is a pydantic v2 model with strict field validation —
#      subclassing requires re-declaring fields and managing pydantic init,
#      which gets ugly fast.
#   2. .bind_tools() returns a _ChatModelBinding (a Runnable, not a
#      BaseChatModel) — a wrapper subclass would need to handle two
#      different return types.
#   3. Monkey-patching the actual instance's bound method works regardless
#      of what wrapper objects LangGraph constructs around it; they all
#      eventually call the same underlying ._generate().
# ---------------------------------------------------------------------------

class CassetteRecorder:
    """Holds the recording state. Install via .install(model)."""

    def __init__(self, tool_schemas: list[dict[str, Any]]):
        self.interactions: list[dict[str, Any]] = []
        self.tool_schemas = tool_schemas
        self.seen_fingerprints: set[str] = set()

    def install(self, model: ChatOpenAI) -> None:
        """Wrap model._generate to record each call. Mutates model in place."""
        original_generate = model._generate
        recorder = self

        def wrapped_generate(
            messages: list[BaseMessage],
            stop: list[str] | None = None,
            run_manager: CallbackManagerForLLMRun | None = None,
            **kwargs: Any,
        ) -> ChatResult:
            result: ChatResult = original_generate(
                messages, stop=stop, run_manager=run_manager, **kwargs
            )
            recorder._capture(messages, result)
            return result

        # Bind as a method on this instance only, not the class.
        # Use object.__setattr__ to bypass pydantic's __setattr__ guard.
        object.__setattr__(model, "_generate", wrapped_generate)

    def _capture(self, messages: list[BaseMessage], result: ChatResult) -> None:
        fp = fingerprint(messages, self.tool_schemas)
        ai_msg = result.generations[0].message
        assert isinstance(ai_msg, AIMessage), f"Unexpected message type: {type(ai_msg)}"

        # Build a human-readable preview of what triggered this hop
        last_preview = ""
        for m in reversed(messages):
            if m.type == "human":
                last_preview = (m.content or "")[:100]
                break
            if m.type == "tool":
                last_preview = f"[tool:{getattr(m, 'name', '?')}] {(m.content or '')[:80]}"
                break

        usage = getattr(ai_msg, "usage_metadata", None) or {}
        in_tok = usage.get("input_tokens", 0)
        out_tok = usage.get("output_tokens", 0)
        if ai_msg.tool_calls:
            names = [tc["name"] for tc in ai_msg.tool_calls]
            tool_summary = f", called tool(s): {', '.join(names)}"
        else:
            tool_summary = ", final answer"

        is_dup = fp in self.seen_fingerprints
        dup_marker = "  (duplicate fingerprint, deduped)" if is_dup else ""
        print(
            f"  → LLM hop (fp {fp[:10]}…): "
            f"{in_tok} in / {out_tok} out tokens{tool_summary}{dup_marker}"
        )

        if not is_dup:
            self.seen_fingerprints.add(fp)
            self.interactions.append({
                "request_fingerprint": fp,
                "request_preview": last_preview,
                "response": _serialize_ai_message(ai_msg),
            })


# ---------------------------------------------------------------------------
# Cost estimation (gpt-4o-mini pricing as of 2025: $0.15/M in, $0.60/M out)
# ---------------------------------------------------------------------------

_PRICING_PER_M_TOKENS = {
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o":      (2.50, 10.00),
}


def estimate_cost(model: str, in_tokens: int, out_tokens: int) -> float | None:
    pricing = _PRICING_PER_M_TOKENS.get(model)
    if not pricing:
        return None
    in_per_m, out_per_m = pricing
    return (in_tokens / 1_000_000) * in_per_m + (out_tokens / 1_000_000) * out_per_m


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Record LLM cassette for the offline lab variant.")
    parser.add_argument("--output", default="cassette.json", help="Output cassette path (default: cassette.json)")
    parser.add_argument("--model", default="gpt-4o-mini", help="OpenAI model name (default: gpt-4o-mini)")
    parser.add_argument("--base-url", default="https://api.openai.com/v1", help="OpenAI base URL")
    args = parser.parse_args()

    import os
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: set OPENAI_API_KEY env var before running.", file=sys.stderr)
        return 1

    print(f"Recording cassette with model={args.model}")
    print(f"Output: {args.output}")
    print(f"Sample queries: {len(SAMPLE_QUERIES)}")
    print()

    # Build agent identical to the notebook. We deliberately keep using
    # langgraph.prebuilt.create_react_agent (matches the notebook) and
    # silence its V1.0 deprecation warning. When the notebook migrates to
    # `from langchain.agents import create_agent`, update both files
    # together.
    import warnings
    warnings.filterwarnings(
        "ignore",
        message=".*create_react_agent has been moved.*",
    )
    try:
        from langgraph.warnings import LangGraphDeprecatedSinceV10  # type: ignore
        warnings.filterwarnings("ignore", category=LangGraphDeprecatedSinceV10)
    except Exception:
        pass

    model = ChatOpenAI(
        model=args.model,
        base_url=args.base_url,
        api_key=api_key,
        temperature=0,
    )
    tool_schemas = _serialize_tool_schemas(TOOLS)
    recorder = CassetteRecorder(tool_schemas)
    recorder.install(model)
    agent = create_react_agent(model, TOOLS, prompt=SYSTEM_PROMPT)

    # Run every sample query
    total_in_tokens = 0
    total_out_tokens = 0
    for i, query in enumerate(SAMPLE_QUERIES, start=1):
        print(f"[Query {i}/{len(SAMPLE_QUERIES)}] {query}")
        try:
            result = agent.invoke({"messages": [{"role": "user", "content": query}]})
        except Exception as exc:
            print(f"  ✗ FAILED: {exc!r}", file=sys.stderr)
            return 2
        # Sum tokens for cost estimate
        for msg in result["messages"]:
            usage = getattr(msg, "usage_metadata", None)
            if usage:
                total_in_tokens += usage.get("input_tokens", 0) or 0
                total_out_tokens += usage.get("output_tokens", 0) or 0
        final = result["messages"][-1].content
        preview = (final or "")[:120].replace("\n", " ")
        print(f"  ✓ Final: {preview}{'…' if len(final or '') > 120 else ''}")
        print()

    # Build cassette
    cassette = {
        "version": 1,
        "model": args.model,
        "recorded_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "system_prompt_hash": _hash(SYSTEM_PROMPT),
        "tool_schemas_hash": _hash(json.dumps(tool_schemas, sort_keys=True, default=str)),
        "sample_queries": SAMPLE_QUERIES,
        "interactions": recorder.interactions,
    }
    Path(args.output).write_text(json.dumps(cassette, indent=2))
    size_kb = Path(args.output).stat().st_size / 1024

    # Summary
    cost = estimate_cost(args.model, total_in_tokens, total_out_tokens)
    print("=" * 60)
    print("Recording complete.")
    print(f"  Sample queries run:     {len(SAMPLE_QUERIES)}")
    print(f"  Unique LLM interactions: {len(recorder.interactions)}")
    print(f"  Total input tokens:      {total_in_tokens:,}")
    print(f"  Total output tokens:     {total_out_tokens:,}")
    if cost is not None:
        print(f"  Estimated OpenAI cost:   ${cost:.4f}")
    else:
        print(f"  Estimated OpenAI cost:   (unknown — model not in pricing table)")
    print(f"  Cassette written:        {args.output} ({size_kb:.1f} KB)")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
