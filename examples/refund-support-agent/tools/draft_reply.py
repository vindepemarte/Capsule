def create_draft(state):
    policy = state.get("policy", "We need to review your request.")
    message = state.get("message", "your request")
    return {
        "final_reply": (
            "Thanks for reaching out. Based on our policy, "
            f"{policy} We reviewed this request: {message}"
        )
    }
