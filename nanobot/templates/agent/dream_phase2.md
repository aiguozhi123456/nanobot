Update memory files based on the analysis below.

## Quality standards
- Every line must carry standalone value — no filler
- Concise bullet points under clear headers
- Remove outdated or contradicted information

## Editing
- File contents provided below — edit directly, no read_file needed
- Batch changes to the same file into one edit_file call
- Surgical edits only — never rewrite entire files
- Do NOT overwrite correct entries — only add, update, or remove
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
