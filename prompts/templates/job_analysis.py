prompt_template="""
TASK:
Analyze the job posting below and return ONLY a JSON object. There must be no explanation, no markdown, and no commentary.

INSTRUCTIONS:

1. health_science_related
    - Look ONLY at the "Course Title:" and "Course Code:" fields.
    - If both are blank or unspecified, return "No".
    - IGNORE the unit name or faculty name when determining this.

2. masters_required
    - Return "Yes" ONLY if a master's degree is the minimum requirement (e.g. "MSc required", "MSc or PhD").
    - Return "No" if a bachelor's degree is sufficient (e.g. "Bachelor, MSc or PhD").

3. doctorate_required
    - Return "Yes" ONLY if a doctorate is the minimum requirement (e.g. "PhD required").
    - Return "No" if a bachelor's or master's degree is sufficient (e.g. "Bachelor, MSc or PhD").

4. language_of_work
    - Look ONLY at the "Language of Work:" field in the job posting.
    - If the field is blank or unspecified, default to "English".
    - Return "English", "French", or "Bilingual" based strictly on that field.
    - IGNORE any mention of the university being bilingual — that is boilerplate.
    - Example: if the posting says "Language of Work:" with nothing after it → return "English"
    - Example: if the posting says "Language of Work: French" → return "French"
    - Example: if the posting says "Language of Work: English/French" → return "Bilingual"

RESPONSE FORMAT (JSON only, no other text):
{
    "health_science_related": "Yes" | "No",
    "masters_required": "Yes" | "No",
    "doctorate_required": "Yes" | "No",
    "language_of_work": "English" | "French" | "Bilingual"
}

HEALTH SCIENCE COURSES (reference list):
{{health_science_courses}}

JOB POSTING:
{{job}}

INSTRUCTIONS:

1. health_science_related
    - Look ONLY at the "Course Title:" and "Course Code:" fields.
    - If both are blank or unspecified, return "No".
    - IGNORE the unit name or faculty name when determining this.

2. masters_required
    - Return "Yes" ONLY if a master's degree is the minimum requirement (e.g. "MSc required", "MSc or PhD").
    - Return "No" if a bachelor's degree is sufficient (e.g. "Bachelor, MSc or PhD").

3. doctorate_required
    - Return "Yes" ONLY if a doctorate is the minimum requirement (e.g. "PhD required").
    - Return "No" if a bachelor's or master's degree is sufficient (e.g. "Bachelor, MSc or PhD").

4. language_of_work
    - Look ONLY at the "Language of Work:" field in the job posting.
    - If the field is blank or unspecified, default to "English".
    - Return "English", "French", or "Bilingual" based strictly on that field.
    - IGNORE any mention of the university being bilingual — that is boilerplate.
    - Example: if the posting says "Language of Work:" with nothing after it → return "English"
    - Example: if the posting says "Language of Work: French" → return "French"
    - Example: if the posting says "Language of Work: English/French" → return "Bilingual"

RESPONSE FORMAT (JSON only, no other text):
{
    "health_science_related": "Yes" | "No",
    "masters_required": "Yes" | "No",
    "doctorate_required": "Yes" | "No",
    "language_of_work": "English" | "French" | "Bilingual"
}
"""