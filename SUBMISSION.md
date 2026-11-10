# Submission kit — Great Indian AI Internship Challenge (deadline 10 Nov 2026, 11:59 PM IST)

## Form fields (paste-ready)
**Project title:** KiranaVoice AI (rename if you pick a new name)
**Problem:** Kirana shopkeepers track stock in their heads or notebooks. Inventory apps need typing and English menus, so stock-outs and wrong counts go unnoticed. Voice tools that act on raw transcripts can silently corrupt records.
**Who will use it:** Small kirana store owners who speak Hindi/Hinglish and prefer talking to tapping.
**Gnani AI models used:** Prisma v2.5 (speech-to-text, Hindi/Hinglish commands) and Timbre v2.5 (text-to-speech, spoken confirmations). (Evon not used.)
**Contribution:** Noor Ul Huda (solo): product idea, backend, voice command parser, safety rules, frontend, demo.
**Awards to aim at (one max can be won):** Real Deal (kirana), Mixed Vibes (Hinglish), Solo Ninja, Demo Day Drop.

## Unique angle (say this in video + post)
Voice never writes to the database directly: a rule-based engine validates product, unit and stock, asks for clarification, requires confirmation for big changes, and undo is a reversing entry so history is never deleted.

## 60-second demo script
0–5s  Problem: "Kirana owners can't type inventory, so they guess."
5–15s Say "chhota maggi ke das packet add karo" → spoken reply with new stock.
15–25s Say "paanch packet chhota maggi becha" → stock drops, low-stock alert if any.
25–35s Say "sau packet chhota maggi becha" → rejected: "You have 25, did you mean fewer?"
35–45s Say "maggi ke paanch packet add karo" → asks which Maggi.
45–55s Say "undo" → stock restored; show History tab (nothing deleted).
55–60s "Built on Gnani Prisma and Timbre. Hinglish in, safe records out."

## Post draft (LinkedIn / X) — must be LIVE before you submit
Kirana owners shouldn't need to type to know their stock. I built KiranaVoice AI: speak in Hinglish, it updates inventory, asks when unsure, and never deletes history (undo = reversal). Built on @GnaniAI Prisma (STT) + Timbre (TTS).
#GnaniAI #GreatIndianAIInternshipChallenge
[attach demo video; tag Gnani AI]

## Final checklist
[ ] python eval_commands.py -> note pass rate   [ ] real-mic test with key
[ ] record video  [ ] post on LinkedIn AND/OR X  [ ] copy post link(s)
[ ] submit before 11:59 PM IST 10 Nov (post first: engagement is counted at cutoff)
