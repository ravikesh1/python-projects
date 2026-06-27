# Publishing the `mysql-explorer` skill

How to get the skill from this repo into Claude. There are two targets, and they
work very differently.

## Key thing to remember

**GitHub and the Claude desktop chat app never sync.** Pushing or merging on
GitHub does **not** update the desktop app. The repo only holds the *source*; the
desktop app gets the skill only when you upload a `.zip` to it by hand.

Also: the `.zip` is **not stored in git** — `dist/` is gitignored. `skills/build.sh`
generates it fresh each time.

## Desktop chat app (manual upload)

1. **Edit the skill** in the repo: `skills/mysql-explorer/SKILL.md` (and
   `reference.md`).
2. **Commit and push** your changes (any branch; PR/merge optional — that's just
   version control).
3. **Build the zip:**
   ```bash
   bash skills/build.sh
   ```
   This writes `dist/mysql-explorer.zip` (top level is `mysql-explorer/SKILL.md`,
   the layout the uploader expects).
4. **Download** `dist/mysql-explorer.zip` to your computer.
5. **Upload it** in Claude desktop: **Settings → Capabilities → Skills → Upload
   skill**. Code Execution must be enabled, and Skills require a paid plan
   (Pro/Max/Team/Enterprise).

**Every time you change the skill, repeat steps 3–5** (re-build, re-download,
re-upload). There is no auto-update for the desktop app.

## Alternative: Claude Code (GitHub-linked, auto-updating)

For the **Claude Code** CLI/IDE — not the desktop chat app — this repo doubles as
a plugin marketplace, so installs come straight from GitHub and update on push:

```text
/plugin marketplace add ravikesh1/python-projects
/plugin install mysql-explorer@ravikesh-python-projects
```

Refresh later with `/plugin marketplace update`. Manifests live in
`.claude-plugin/`, reusing the same `skills/mysql-explorer/` folder as the zip.

## Quick reference

| Target | Install | Updates on `git push`? |
| --- | --- | --- |
| Desktop chat app | Build zip → upload in Settings → Capabilities → Skills | No — re-build + re-upload |
| Claude Code | `/plugin marketplace add` → `/plugin install` | Yes — `/plugin marketplace update` |
