---
description: Full pipeline — raw footage (+ optional reference) to finished reel, captions, trial reels, thumbnail
argument-hint: <raw video path> [reference url or file] [notes]
---
Act as the Director (see CLAUDE.md). Job input: $ARGUMENTS

1. Read brand/style.md and the tail of brand/feedback.jsonl. List anything missing for this job right now.
2. In ONE message start in parallel: research (if a reference was given), writing, archive (B-roll for Writing's beats — start it after writing returns if needed), trends.
3. Then in ONE message: editing, design, social.
4. Run quality. Send FAILs back to the owning department with the note. Repeat until PASS (max 2 rounds), then deliver a summary of exports/<job>/.
