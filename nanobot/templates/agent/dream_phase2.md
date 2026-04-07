Update memory files based on the analysis below.
- [FILE] entries: add the described content to the appropriate file
- [FILE-REMOVE] entries: delete the corresponding content from memory files

## File paths (relative to workspace root)
- SOUL.md
- USER.md
- memory/MEMORY.md
- memory/keyword_memory.json

Do NOT guess paths.

## Editing rules
- Edit directly — file contents provided below, no read_file needed
- Use exact text as old_text, include surrounding blank lines for unique match
- Batch changes to the same file into one edit_file call
- For deletions: section header + all bullets as old_text, new_text empty
- Surgical edits only — never rewrite entire files
- If nothing to update, stop without calling tools

## keyword_memory.json editing
- Only edit when [KEYWORD] findings are present in the analysis
- Relevant existing entries are provided above — use edit_file for surgical changes
- For new entries: append before the closing `]` of the JSON array
- For updates: replace the specific entry text with an improved version
- For removals: delete the entry including its comma separator
- Format: {"keywords": ["word1", "word2"], "prompt": "concise instruction"}
- Keep prompts concise and action-oriented
- Preserve all existing entries not mentioned in the analysis

## Quality
- Every line must carry standalone value
- Concise bullets under clear headers
- When reducing (not deleting): keep essential facts, drop verbose details
- If uncertain whether to delete, keep but add "(verify currency)"
