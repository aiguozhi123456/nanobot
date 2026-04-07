Compare conversation history against memory files. Also scan memory files for stale content — even if not mentioned in history.

Output one line per finding:
[FILE] atomic fact (not already in memory)
[FILE-REMOVE] reason for removal

Files: USER (identity, preferences), SOUL (bot behavior, tone), MEMORY (knowledge, project context), KEYWORD (keyword-triggered injection rules in keyword_memory.json)

Rules:
- Atomic facts: "has a cat named Luna" not "discussed pet care"
- Corrections: [USER] location is Tokyo, not Osaka
- Capture confirmed approaches the user validated
- [KEYWORD] findings: suggest new rules when a recurring topic needs consistent handling (e.g., "[KEYWORD] user always requests backup before DB migration → add keyword rule for database/backup"). Also flag existing keyword rules that are outdated or conflicting with recent conversations. Reference existing keywords by name.

Staleness — flag for [FILE-REMOVE]:
- Time-sensitive data older than 14 days: weather, daily status, one-time meetings, passed events
- Completed one-time tasks: triage, one-time reviews, finished research, resolved incidents
- Resolved tracking: merged/closed PRs, fixed issues, completed migrations
- Detailed incident info after 14 days — reduce to one-line summary
- Superseded: approaches replaced by newer solutions, deprecated dependencies

Do not add: current weather, transient status, temporary errors, conversational filler.

[SKIP] if nothing needs updating.
