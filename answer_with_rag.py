# answer_with_rag.py

from typing import List, Dict

# OpenAI client fallback logic
try:
    from openai import OpenAI
    client = OpenAI()
    use_client = True
except Exception:
    import openai
    use_client = False

from semantic_search import search

COMPLETIONS_MODEL = "gpt-4o"
MAX_CONTEXT_CHARS = 8000


def build_context(topk: List[Dict]) -> str:
    parts, total = [], 0
    for r in topk:
        fname = r[2].get("filename", "unknown.txt")
        cid = r[2].get("chunk_id", 0)
        text = r[2].get("text_preview", "")
        snippet = f"[{fname}#{cid}]\n{text}\n"
        if total + len(snippet) > MAX_CONTEXT_CHARS:
            break
        parts.append(snippet)
        total += len(snippet)
    return "\n".join(parts)


def ask_gpt(query: str, context: str) -> str:
    system_prompt = (
        "You are a helpful AI CEO assistant. "
        "Use ONLY the provided context to answer the user's query. "
        "Cite sources using the format [filename#chunk]. "
        "If the context lacks sufficient information, say so clearly and suggest next steps."
    )

    user_content = f"Question:\n{query}\n\nContext:\n{context}"

    if use_client:
        resp = client.chat.completions.create(
            model=COMPLETIONS_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=0.2,
        )
        return resp.choices[0].message.content
    else:
        resp = openai.ChatCompletion.create(
            model=COMPLETIONS_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=0.2,
        )
        return resp["choices"][0]["message"]["content"]


def answer(query: str, k: int = 5, chat_history: List[Dict] = None) -> str:
    hits = search(query, k=k)
    context = build_context(hits)
    reply = ask_gpt(query, context)
    return reply


if __name__ == "__main__":
    print(answer("What were the key decisions made in the July financial review?"))
