def search_policy(state):
    message = state.get("message", "").lower()
    if "refund" in message:
        return {
            "route": "approved",
            "policy": "Refunds are available within 30 days when the order is eligible.",
        }
    return {
        "route": "needs_human",
        "policy": "No matching refund policy was found.",
    }
