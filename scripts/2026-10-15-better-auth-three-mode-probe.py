#!/usr/bin/env python3
"""Better Auth three-mode probe for your-protected-notes (Lapidary 5, 2026-10-15).

The 2026-10-08 probe proves the three modes against LEGACY Stack sign-up —
a door no new student project can open (new Neon projects provision Managed
Better Auth only; docs/NEON-AUTH-TRANSITION.md). This is its Better-mode
twin, written for the session-7 dry run: (1) sign-up via the Managed Better
Auth REST the server itself uses (auth.py quirks: Origin header required,
session travels as a cookie, GET /token exchanges session -> EdDSA JWT);
(2) guest MCP session -> commons; (3) Bearer-JWT session -> private shelf,
invisible to a second guest; (4) the declared-guest credential
("guest-no-shelf") -> chosen commons, not an error; (5) garbled token ->
loud failure (ADR-0004).

Run: load env (DATABASE_URL, NEON_AUTH_BASE_URL) and start server.py on
:8000 first; then `uv run scripts/2026-10-15-better-auth-three-mode-probe.py`.
Loads ../.env itself if present (exported vars win).
"""
import asyncio, json, os, pathlib, urllib.request

_env = pathlib.Path(__file__).resolve().parents[1] / ".env"
if _env.exists():
    for line in _env.read_text().splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip().strip("'\""))

BA = os.environ["NEON_AUTH_BASE_URL"].rstrip("/")
ORIGIN = BA.split("/neondb")[0] if "/neondb" in BA else BA
BASE = "http://127.0.0.1:8000/mcp"
BA_COOKIE = "__Secure-neon-auth.session_token"   # auth.py:31 — Neon's Managed Better Auth cookie name


def better(path, payload=None, cookie=None, method=None):
    h = {"Content-Type": "application/json", "Origin": ORIGIN}
    if cookie:
        h["Cookie"] = f"{BA_COOKIE}={cookie}"
    req = urllib.request.Request(
        BA + path, json.dumps(payload).encode() if payload is not None else None, h, method=method)
    with urllib.request.urlopen(req) as r:
        session = ""
        for c in (r.headers.get_all("Set-Cookie") or []):
            first = c.split(";")[0]
            if first.startswith(BA_COOKIE + "="):
                session = first.split("=", 1)[1]
        return json.loads(r.read() or b"{}"), session


async def session(headers, label, calls):
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client
    async with streamablehttp_client(BASE, headers=headers) as (r, w, _):
        async with ClientSession(r, w) as s:
            await s.initialize()
            out = []
            for tool, args in calls:
                res = await s.call_tool(tool, args)
                text = res.content[0].text if res.content else "(no content)"
                print(f"[{label}] {tool}: {text[:140]}")
                out.append((bool(getattr(res, "isError", False)), text))
            return out


async def main():
    email = f"probe-{os.urandom(3).hex()}@example.com"
    _, cookie = better("/sign-up/email",
                       {"email": email, "password": "probe-Passw0rd!x", "name": email.split("@")[0]})
    assert cookie, "no session cookie from sign-up"
    tok, _ = better("/token", cookie=cookie, method="GET")
    token = tok["token"]
    print(f"signed up {email}; EdDSA JWT acquired ({len(token)} chars)")

    await session({}, "guest", [
        ("user_status", {}),
        ("add_note", {"note": "guest commons note from the BA probe"}),
        ("list_notes", {}),
    ])
    user_out = await session({"Authorization": f"Bearer {token}"}, "user ", [
        ("user_status", {}),
        ("add_note", {"note": "private shelf note from the BA probe"}),
        ("list_notes", {}),
    ])
    assert email in user_out[0][1], "user_status should display the signed-in email"
    g2 = await session({}, "guest2", [("list_notes", {})])
    assert "private shelf note" not in g2[0][1], "PRIVACY VIOLATION: guest sees a private note"
    print("[guest2] cannot see the private note — shelf isolation holds")

    dg = await session({"Authorization": "Bearer guest-no-shelf"}, "decl.g", [("user_status", {})])
    assert dg[0][1].startswith("guest"), "declared-guest token must mean guest mode"
    print("[decl.g] declared-guest credential -> chosen commons (ADR-0002 iter. 3 holds)")

    try:
        out = await session({"Authorization": "Bearer garbage.token.here"}, "bad  ", [("user_status", {})])
        is_err, text = out[0]
        if is_err or text.startswith("Error"):
            print("[bad  ] loud failure as designed (tool error, not silent guest) — ADR-0004 holds")
        else:
            print("[bad  ] ADR-0004 VIOLATED: invalid token answered as", text[:60])
    except Exception as e:
        print(f"[bad  ] loud failure as designed (transport): {type(e).__name__}")

asyncio.run(main())

# OUTCOME (2026-10-15, session-7 dry run, T-2h30 before class): all five
# behaviors proven against a FRESH Neon project (cam-s7-dryrun-2026-10-15,
# provisioned Managed Better Auth the same way a student's will be) and the
# server running locally via `uv run --env-file .env server.py`:
# guest commons (QZ9K), private shelf (DA40) invisible to guest2, email
# displayed, declared-guest -> chosen commons, garbled token -> loud tool
# error ("Invalid header padding"). One probe-side catch while writing it:
# the session cookie is __Secure-neon-auth.session_token (auth.py:31), not
# better-auth.session_token. The braid's falsifier did not fire.
