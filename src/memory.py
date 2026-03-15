"""
ChromaDB memory system (inference-time learning).

Stores past pipeline runs so the supervisor can make better agent selections
without any model fine-tuning — all learning happens at inference time.

What gets stored per function:
    - The function source (used as an embedding for similarity search)
    - Which agents were selected by the supervisor
    - Per-agent mutation kill counts and unique-kill counts
    - Overall kill rate

Key functions:
    store_result()          — save one function's results after mutation testing
    retrieve_similar()      — find K most similar past functions (few-shot examples)
    generate_reflections()  — ask the LLM to summarize lessons from a batch of results
    store_reflection()      — save a reflection string to the DB
    get_reflections()       — retrieve all stored reflections
    format_memory_context() — build a prompt string from retrieved examples + reflections
"""
import hashlib
import json
import os
from datetime import datetime, timezone

import chromadb
from langchain_core.messages import SystemMessage, HumanMessage

from src.agents import get_llm, TEST_TYPES


def get_db(path="data/memory_db"):
    os.makedirs(path, exist_ok=True)
    return chromadb.PersistentClient(path=path)


def get_collection(db):
    return db.get_or_create_collection("function_results")


def get_reflections_collection(db):
    return db.get_or_create_collection("reflections")


def _source_id(source):
    return hashlib.sha256(source.encode("utf-8")).hexdigest()[:16]


def store_result(collection, fn, selected_agents, agent_kills, agent_totals, mutant_count,
                 unique_kills):
    source = fn["source"]
    doc_id = _source_id(source)

    metadata = {
        "function_name": fn["name"],
        "file_path": fn.get("file_path", ""),
        "agents_selected": json.dumps(selected_agents),
        "total_mutants": mutant_count,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # store per-agent results as flattened keys (chromadb metadata must be flat)
    overall_killed = 0
    overall_total = 0
    for agent in TEST_TYPES:
        killed = len(agent_kills.get(agent, set()))
        total = agent_totals.get(agent, 0)
        rate = killed / total if total > 0 else 0.0
        unique = unique_kills.get(agent, 0)
        metadata[f"{agent}_killed"] = killed
        metadata[f"{agent}_total"] = total
        metadata[f"{agent}_rate"] = round(rate, 3)
        metadata[f"{agent}_unique"] = unique
        overall_killed += killed
        overall_total += total

    metadata["overall_kill_rate"] = round(
        overall_killed / overall_total if overall_total > 0 else 0.0, 3
    )

    collection.upsert(documents=[source], metadatas=[metadata], ids=[doc_id])


def retrieve_similar(collection, fn, k=5):
    try:
        count = collection.count()
    except Exception:
        return []
    if count == 0:
        return []

    n = min(k, count)
    results = collection.query(query_texts=[fn["source"]], n_results=n)

    records = []
    if results and results["metadatas"]:
        for meta in results["metadatas"][0]:
            records.append(meta)
    return records


def store_reflection(db, text):
    coll = get_reflections_collection(db)
    doc_id = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
    metadata = {"timestamp": datetime.now(timezone.utc).isoformat()}
    coll.upsert(documents=[text], metadatas=[metadata], ids=[doc_id])


def get_reflections(db, limit=10):
    coll = get_reflections_collection(db)
    try:
        count = coll.count()
    except Exception:
        return []
    if count == 0:
        return []

    results = coll.get(limit=limit)
    if not results or not results["documents"]:
        return []

    # pair with timestamps for sorting
    pairs = []
    for i, doc in enumerate(results["documents"]):
        ts = results["metadatas"][i].get("timestamp", "") if results["metadatas"] else ""
        pairs.append((ts, doc))

    pairs.sort(key=lambda x: x[0], reverse=True)
    return [doc for _, doc in pairs[:limit]]


def format_memory_context(similar_results, reflections):
    parts = []

    if similar_results:
        lines = ["## Past Examples\n"]
        for meta in similar_results:
            name = meta.get("function_name", "unknown")
            agents = meta.get("agents_selected", "[]")
            overall = meta.get("overall_kill_rate", 0)

            agent_details = []
            for agent in TEST_TYPES:
                killed = meta.get(f"{agent}_killed", 0)
                total = meta.get(f"{agent}_total", 0)
                unique = meta.get(f"{agent}_unique", 0)
                if total > 0:
                    rate = round(killed / total * 100, 1)
                    agent_details.append(f"{agent}: {rate}% ({unique} unique)")

            lines.append(f"- **{name}** — Agents: {agents}")
            if agent_details:
                lines.append(f"  Results: {', '.join(agent_details)}")
            lines.append(f"  Overall kill rate: {round(overall * 100, 1)}%")

        parts.append("\n".join(lines))

    if reflections:
        lines = ["## Lessons Learned\n"]
        for r in reflections:
            lines.append(f"- {r}")
        parts.append("\n".join(lines))

    return "\n\n".join(parts)


def generate_reflections(batch_records):
    if not batch_records:
        return []

    system = (
        "You are a test strategy analyst. Review the batch results below and generate "
        "exactly 2-3 concise lessons (one sentence each) about which agent combinations "
        "work best for which types of functions. Focus on actionable insights. "
        "Return a JSON array of strings, nothing else."
    )

    lines = []
    for rec in batch_records:
        name = rec["function_name"]
        agents = rec["agents_selected"]
        details = []
        for agent in TEST_TYPES:
            killed = rec.get(f"{agent}_killed", 0)
            total = rec.get(f"{agent}_total", 0)
            unique = rec.get(f"{agent}_unique", 0)
            if total > 0:
                rate = round(killed / total * 100, 1)
                details.append(f"{agent}={rate}% ({unique} unique)")
        overall = rec.get("overall_kill_rate", 0)
        lines.append(f"- {name}: agents={agents}, results=[{', '.join(details)}], overall={round(overall * 100, 1)}%")

    user_msg = "Batch results:\n" + "\n".join(lines)

    llm = get_llm()
    response = llm.invoke([SystemMessage(content=system), HumanMessage(content=user_msg)])

    text = response.content.strip()
    text = text.replace("```json", "").replace("```", "").strip()

    try:
        result = json.loads(text)
        if isinstance(result, list):
            return [str(r) for r in result]
    except json.JSONDecodeError:
        pass

    # fallback: find [...] in text
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        try:
            result = json.loads(text[start:end + 1])
            if isinstance(result, list):
                return [str(r) for r in result]
        except json.JSONDecodeError:
            pass

    # last fallback: split by newlines
    return [line.strip("- ").strip() for line in text.split("\n") if line.strip()][:3]
