"""Disposable component: Select theme.

Returns the highest-scoring theme the patient hasn't rejected.
Input:  themes (list[str]), scores (list[float], same order), rejected (set[str])
Output: selected theme (str), or None if every theme has been rejected
Ties go to the theme listed first.
"""


def select_theme(themes, scores, rejected):
    if len(themes) != len(scores):
        raise ValueError("themes and scores must have the same length")
    best = None
    for theme, score in zip(themes, scores):
        if theme in rejected:
            continue
        if best is None or score > best[1]:
            best = (theme, score)
    return None if best is None else best[0]
