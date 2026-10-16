MAGIC_PASSWORDS = {
    "banana": "banana-mode",
    "echo": "mirror-mode",
    "shimmer": "haze-mode",
    "penguin": "penguin-mode",
}


def resolve_mood(password: str) -> str | None:
    return MAGIC_PASSWORDS.get(password)
