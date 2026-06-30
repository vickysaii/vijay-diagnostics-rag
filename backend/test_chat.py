"""
Quick sanity-check script for the running API. Run this any time after
starting uvicorn to confirm everything still works end-to-end.

Usage (with venv activated, uvicorn already running in another terminal):
    python test_chat.py
"""
import requests

BASE_URL = "http://127.0.0.1:8000"


def check(label: str, condition: bool, detail: str = ""):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}" + (f" — {detail}" if detail and not condition else ""))
    return condition


def main():
    all_passed = True

    # --- 1. Health check ---
    r = requests.get(f"{BASE_URL}/health")
    all_passed &= check("Health check returns 200", r.status_code == 200, r.text)

    # --- 2. First message - creates a new session ---
    r = requests.post(f"{BASE_URL}/chat", json={"message": "What is the cost of a CBC test?"})
    all_passed &= check("New chat returns 200", r.status_code == 200, r.text)
    data = r.json()
    session_id = data.get("session_id")
    all_passed &= check("Response includes a session_id", bool(session_id))
    all_passed &= check("Response includes an answer", bool(data.get("answer")))
    all_passed &= check(
        "Answer mentions the price (₹350)", "350" in data.get("answer", ""), data.get("answer")
    )
    all_passed &= check("Sources were returned", len(data.get("sources", [])) > 0)

    # --- 3. Follow-up message in the same session ---
    r = requests.post(
        f"{BASE_URL}/chat",
        json={"message": "Does it need fasting?", "session_id": session_id},
    )
    all_passed &= check("Follow-up message returns 200", r.status_code == 200, r.text)
    all_passed &= check(
        "Follow-up reuses the same session_id", r.json().get("session_id") == session_id
    )

    # --- 4. Off-topic question should trigger the no-context fallback, not a hallucination ---
    r = requests.post(
        f"{BASE_URL}/chat", json={"message": "What's the weather like in Hyderabad today?"}
    )
    all_passed &= check("Off-topic question returns 200", r.status_code == 200, r.text)
    answer_lower = r.json().get("answer", "").lower()
    all_passed &= check(
    "Off-topic question triggers fallback (not a hallucinated answer)",
    "don't have" in answer_lower or "do not have" in answer_lower,
    r.json().get("answer"),
)

    # --- 5. History endpoint ---
    r = requests.get(f"{BASE_URL}/chat/{session_id}/history")
    all_passed &= check("History endpoint returns 200", r.status_code == 200, r.text)
    history = r.json().get("messages", [])
    all_passed &= check("History contains 4 messages (2 user + 2 assistant)", len(history) == 4)

    # --- 6. Invalid session_id should 404, not 500 ---
    r = requests.get(f"{BASE_URL}/chat/00000000-0000-0000-0000-000000000000/history")
    all_passed &= check("Unknown session_id returns 404", r.status_code == 404)

    # --- 7. Empty message should be rejected cleanly ---
    r = requests.post(f"{BASE_URL}/chat", json={"message": "   "})
    all_passed &= check("Empty message returns 422", r.status_code == 422)

    print()
    print("ALL CHECKS PASSED ✅" if all_passed else "SOME CHECKS FAILED ❌ — see above")


if __name__ == "__main__":
    main()
