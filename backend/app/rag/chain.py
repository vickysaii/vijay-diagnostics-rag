from groq import Groq

from app.config import settings
from app.models import ChatMessage
from app.rag.retriever import RetrievedChunk

_client = Groq(api_key=settings.GROQ_API_KEY)

SYSTEM_PROMPT = """You are the official AI assistant for Vijay Diagnostics, a diagnostic and pathology lab chain.

Answer the user's question using ONLY the information given in the CONTEXT below.
- If the answer isn't in the context, say you don't have that specific information and \
suggest they call the helpline or visit the nearest branch. Do not invent details like \
prices, timings, or test results.
- Be concise, friendly, and clear. Use bullet points for lists (e.g. test prep steps, \
package contents, pricing).
- Never give medical advice or interpret what a test result means for the patient's \
health — that is the doctor's job. You only help with informational/logistics \
questions: timings, pricing, prep instructions, locations, policies, and bookings.
"""

# Used when retrieval finds nothing genuinely relevant - skips the LLM call
# entirely (faster, cheaper, and avoids the model trying to "make something
# work" out of irrelevant context).
NO_CONTEXT_FALLBACK = (
    "I'm sorry, I don't have information on that topic. I can help with test "
    "pricing, prep instructions, home sample collection, report timelines, "
    "health checkup packages, and branch details for Vijay Diagnostics. For "
    "anything else, please call our helpline or visit your nearest branch."
)

# How many previous turns (user+assistant pairs) to include for conversational
# continuity. Keeping this small keeps the prompt short and the LLM call fast/cheap.
MAX_HISTORY_MESSAGES = 6


class LLMGenerationError(Exception):
    """Raised when the underlying LLM call fails (timeout, rate limit, API error, etc.)."""


def _build_context_block(retrieved: list[RetrievedChunk]) -> str:
    return "\n\n".join(f"[{r.chunk.section}]\n{r.chunk.content}" for r in retrieved)


def generate_answer(
    query: str,
    retrieved_chunks: list[RetrievedChunk],
    history: list[ChatMessage],
) -> str:
    if not retrieved_chunks:
        return NO_CONTEXT_FALLBACK

    context_block = _build_context_block(retrieved_chunks)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Include recent conversation history so follow-up questions
    # ("what about for that one?") still make sense to the model.
    for msg in history[-MAX_HISTORY_MESSAGES:]:
        messages.append({"role": msg.role, "content": msg.content})

    messages.append(
        {
            "role": "user",
            "content": f"CONTEXT:\n{context_block}\n\nQUESTION:\n{query}",
        }
    )

    try:
        response = _client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=messages,
            temperature=0.2,
            max_tokens=600,
        )
    except Exception as e:
        # Covers Groq rate limits, timeouts, auth errors, network issues, etc.
        # We don't want any of these to surface as a raw 500 to the frontend.
        raise LLMGenerationError(f"LLM call failed: {e}") from e

    return response.choices[0].message.content
