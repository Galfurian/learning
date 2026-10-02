"""EXE02 — solution."""

from declab.exercise import run

# Application data: requests sent to the IT helpdesk.
CASES = [
    "The printer on floor 2 keeps jamming and prints blank pages.",
    "I cannot connect to the Wi-Fi in the meeting room since this morning.",
    "My password expired and now I am locked out of my account.",
    "My laptop screen flickers and then goes black.",
    "Where can I find the menu of the canteen for next week?",
]

QUESTIONS = {
    "queue": {
        "type": "choice",
        "instructions": "Which IT support queue should handle this request?",
        "criteria": {
            "printer": "Printers and scanners: paper jams, print quality, toner.",
            "network": "Wi-Fi, cables, VPN, internet access.",
            "account": "Passwords, logins, locked accounts, permissions.",
            "hardware": "Laptops, screens, keyboards and other devices that are broken.",
            "none": "Not an IT request.",
        },
    },
}

QUEUES = {
    "printer": "assign to the print team",
    "network": "assign to the network team",
    "account": "assign to the identity team",
    "hardware": "assign to the hardware desk",
    "none": "reply: this helpdesk only handles IT requests",
}


def act(request: str, answers: dict) -> str:
    return QUEUES[answers["queue"]["choice"]]


if __name__ == "__main__":
    run(QUESTIONS, CASES, __file__, act=act)
