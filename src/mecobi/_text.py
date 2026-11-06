"""Small helpers for user-facing message text (no chemistry, no dependencies)."""


def noun(n: int, word: str, plural_form: str | None = None) -> str:
    """``word`` for a count of 1, else its plural (``word + 's'`` unless given)."""
    return word if n == 1 else (plural_form or word + "s")


def plural(n: int, word: str, plural_form: str | None = None) -> str:
    """``"1 donor"`` / ``"2 donors"``: the count followed by the right form of ``word``."""
    return f"{n} {noun(n, word, plural_form)}"
