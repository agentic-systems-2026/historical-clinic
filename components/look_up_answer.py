"""Disposable component: Look up answer.

Exact match of the confirmed query against the physician-verified responses;
fallback message if there is no match.
Input:  confirmed_query (str or None), verified_responses (list[dict]) read
        from data/verified_responses.json by the glue
Output: response to the patient (str)
"""

FALLBACK = (
    "I'm sorry, it looks like we are not prepared to assist you with that topic, "
    "is there something else we can do to help?"
)


def look_up_answer(confirmed_query, verified_responses):
    if confirmed_query is None:
        return FALLBACK
    if not isinstance(confirmed_query, str):
        raise ValueError("confirmed_query must be a string or None")
    target = confirmed_query.strip()
    for physician in verified_responses:
        queries = physician.get("matching_queries", [])
        responses = physician.get("matching_responses", [])
        for index, query in enumerate(queries):
            if query.strip() == target and index < len(responses):
                name = physician.get("name", "Unknown Physician")
                year = physician.get("year_of_birth", "Unknown Year")
                return f"Our physician, {name}, b. {year}, recommends: {responses[index]}"
    return FALLBACK
