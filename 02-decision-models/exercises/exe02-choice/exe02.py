"""EXE02 — choosing one option. Task: see README.md in this folder."""

from declab.exercise import run

# Application data: requests sent to the IT helpdesk.
CASES = [
    "The printer on floor 2 keeps jamming and prints blank pages.",
    "I cannot connect to the Wi-Fi in the meeting room since this morning.",
    "My password expired and now I am locked out of my account.",
    "My laptop screen flickers and then goes black.",
    "Where can I find the menu of the canteen for next week?",
]

# Step 1 of the README: the option keys only. Then complete it (step 2).
QUESTIONS = {
    "queue": {
        "type": "choice",
        "instructions": "Which IT support queue should handle this request?",
        "criteria": {
            "printer": None,
            "network": None,
            "account": None,
        },
    },
}

# What the application does for every option.
QUEUES = {
    "printer": "assign to the print team",
    "network": "assign to the network team",
    "account": "assign to the identity team",
    "hardware": "assign to the hardware desk",
    "none": "reply: this helpdesk only handles IT requests",
}


# TODO: return the QUEUES entry of the option the model chose.
def act(request: str, answers: dict) -> str:
    raise NotImplementedError


if __name__ == "__main__":
    run(QUESTIONS, CASES, __file__, act=act)
