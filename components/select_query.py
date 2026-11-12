"""Disposable component: Select query.

Returns the highest-scoring verified query the patient hasn't rejected.
Input:  queries (list[str]), scores (list[float], same order), rejected (set[str])
Output: selected query (str), or None if every query has been rejected
Ties go to the query listed first.
"""


def select_query(queries, scores, rejected):
    if len(queries) != len(scores):
        raise ValueError("queries and scores must have the same length")
    best = None
    for query, score in zip(queries, scores):
        if query in rejected:
            continue
        if best is None or score > best[1]:
            best = (query, score)
    return None if best is None else best[0]
