Compare conversation history against current memory files.
Output one line per finding:
[FILE] atomic fact or change description

Files: USER (identity, preferences, habits), SOUL (bot behavior, tone), MEMORY (knowledge, project context, tool patterns), KEYWORD (keyword-triggered injection rules in keyword_memory.json)

Rules:
- Only new or conflicting information — skip duplicates and ephemera
- Prefer atomic facts: "has a cat named Luna" not "discussed pet care"
- Corrections: [USER] location is Tokyo, not Osaka
- Also capture confirmed approaches: if the user validated a non-obvious choice, note it
- [KEYWORD] findings: suggest new rules when a recurring topic needs consistent handling (e.g., "[KEYWORD] user always requests backup before DB migration → add keyword rule for database/backup"). Also flag existing keyword rules that are outdated or conflicting with recent conversations. Reference existing keywords by name.

If nothing needs updating: [SKIP] no new information
