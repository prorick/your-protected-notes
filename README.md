# your-protected-notes

**An MCP server that knows who is asking.** Minimal Neon Auth prototype:
one `notes` table, four tools, three modes —

| mode | trigger | what you see |
|---|---|---|
| **guest** | no `Authorization` header (or the declared-guest credential) | the shared guest commons |
| **user** | valid Neon Auth JWT (Managed Better Auth; legacy Stack still verifies) | your private shelf |
| **error** | invalid/expired token | a loud failure — never silent guest-ing (ADR-0001 D4) |

Tools: `user_status` (always answers) · `add_note` · `list_notes` ·
`clear_notes`. Notes get 4-char **Crockford Base32** petnames (`A7K2` —
no I/L/O/U, readable aloud), unique per shelf.

- **In class? Follow [COURSE-STEPS.md](COURSE-STEPS.md)** — the steps in
  class order, with the plain-words table of the three variables.
- **Setup (short form)**: Neon project → **Auth** → enable (provisions
  Managed Better Auth) → set `DATABASE_URL`, `NEON_AUTH_BASE_URL`,
  `PUBLIC_URL`. On Render the Blueprint asks for them; locally, copy
  `.env.example` to `.env` and run `uv run --env-file .env server.py`
  (the server itself only ever reads the environment — level 2's lesson).
  Legacy Stack projects: see the COURSE-STEPS appendix.
- **Start here if you're new**: [docs/adr/0001](docs/adr/0001-an-mcp-server-that-knows-who-is-asking.md)
  is the self-contained account — what this is, every technology it stands
  on, all four decisions with roads not taken, and two QSTs posed (and
  recommended, but deliberately NOT closed) before the code existed.
- **Already have a server storing in Neon?**
  [docs/RETROFIT-NEON-AUTH.md](docs/RETROFIT-NEON-AUTH.md) is written to be
  handed to your Claude.
- **When something misbehaves**: [docs/known-problems.md](docs/known-problems.md) — the honest ledger (symptom → cause → what to do).
- **Open**: how the token reaches the server from claude.ai ([ADR-0002](docs/adr/0002-how-does-the-token-reach-the-server.md) — spike pending).

*Founded 2026-10-08 from
[human-ai-collaboration-template-A](https://github.com/ADRs4AI/human-ai-collaboration-template-A),
fixtures stripped. CAM (CIS 7000, Penn, Fall 2026) · level 3 of the
instrument series.*
