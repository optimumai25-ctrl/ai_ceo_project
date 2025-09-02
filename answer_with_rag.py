from typing import List, Dict, Optional

# OpenAI client
try:
    from openai import OpenAI
    client = OpenAI()
    use_client = True
except Exception:
    import openai
    use_client = False

from semantic_search import search

COMPLETIONS_MODEL = "gpt-4o-mini"
MAX_CONTEXT_CHARS = 8000


def build_context(topk: List[Dict]) -> str:
    parts, total = [], 0
    for r in topk:
        fname = r[2].get("filename", "unknown.txt")
        cid = r[2].get("chunk_id", 0)
        text = r[2].get("text_preview", "")
        snippet = f"[SOURCE: {fname} | CHUNK: {cid}]\n{text}\n"
        if total + len(snippet) > MAX_CONTEXT_CHARS:
            break
        parts.append(snippet)
        total += len(snippet)
    return "\n".join(parts)


def ask_gpt(query: str, context: str) -> str:
    system = (
        "You are a Virtual CEO assistant. Answer using ONLY the provided sources when possible. "
        "Cite sources by filename and chunk in square brackets, e.g., [Meeting_Notes_2025-08-20.txt#3]. "
        "If information is missing from sources, state that briefly and suggest next steps."
    )
    content = f"Query:\n{query}\n\nSources:\n{context}"
    if use_client:
        resp = client.chat.completions.create(
            model=COMPLETIONS_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": content},
            ],
            temperature=0.2,
        )
        return resp.choices[0].message.content
    else:
        resp = openai.ChatCompletion.create(
            model=COMPLETIONS_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": content},
            ],
            temperature=0.2,
        )
        return resp.choices[0].message["content"]


def answer(query: str, k: int = 5, chat_history: Optional[List[Dict]] = None) -> str:
    """
    Answers a query using top-k semantic matches from the local vector store.
    chat_history is accepted for API compatibility with callers but is not used.
    """
    hits = search(query, k=k)
    context = build_context(hits)
    out = ask_gpt(query, context)
    return out


if __name__ == "__main__":
    print(answer("Summarize key risks mentioned in July financials and any mitigation actions."))

