# One guest record per device

Date 2026-10-24 · `/lifecycle`. Follows the user-flow walk (PR 667), which found that a new beginner
skipped the ال lesson because someone else had done it.

## 1 · Requirements

**Problem.** If nobody is logged in, every request goes to one shared server record (`GUEST = "local"`). Every
guest on every device reads and writes that same record, which causes four problems:

- Grow and the Quiz plan from someone else's answers. A first-time beginner gets the ال lesson marked as
  done, and Review fills with other people's mistakes.
- When a guest presses "Clear it all", every guest's answers are deleted.
- When someone signs up with "keep my answers", they take every guest's answers, not just their own.
- Nothing about a guest can be told apart, so a guest can never be given XP or a streak.

**How premium apps do it.** Each device gets its own hidden guest identity. On sign-up that identity is
upgraded, so nothing is lost. Identities nobody upgrades are cleaned away after a while. The app asks for
sign-up when it is needed, not at the door. (Firebase anonymous auth and its "best practices for
anonymous authentication"; Duolingo plays the first lessons before any profile exists.)

| # | Criterion | Check |
|---|---|---|
| G1 | Two devices with no login never see each other's answers: summary, review, overview and forget are each one device's own | pytest: two device ids, two records |
| G2 | Sign-up with `keep` moves **this device's** answers and reports only. Other devices and the legacy shared record are untouched | pytest |
| G3 | A guest's "Clear it all" deletes only this device's answers on the server, and the device id survives the wipe so the delete reaches the right record | pytest + vitest (`ownKeys` leaves the id out) |
| G4 | The device id is never copied into an account's shelf (`copyGuestShelf`) | vitest |
| G5 | The device id is 128 random bits (`crypto.getRandomValues`, which also works on plain-http LAN testing) as 32 lowercase hex. The server takes only `^[0-9a-f]{32}$` and answers anything else with 422 | pytest + vitest |
| G6 | A guest id can never be a username. The record key is `guest:<hex>`, and `:` is refused by `clean_name`. Sign-up, log-in and every account-only route refuse a guest | pytest |
| G7 | A request with no header still uses the legacy shared record, so a page cached before this ships keeps working | the existing suite stays green |
| G8 | Guest records with no answer for `progress_guest_days` (default 180) are deleted at startup, and their reports are kept under nobody (`''`). Named accounts and the legacy record are never swept | pytest |
| G9 | If storage is blocked (private mode), the id holds for the visit in memory, and nothing throws | vitest |
| G10 | Logged-in behaviour is unchanged: the same routes and the same responses for a username | the existing suite stays green |
| G11 | Mutation: every hand-made mutant of the new branches is killed. pytest, vitest, eslint and ruff are green, and a real-app walk with two browser profiles shows two separate records | mutants + Playwright |

**Out of scope here (slice 2, its own PR):** XP, streak and level evidence for guests (§8).

## 2 · Context: where "guest" lives today

- Backend:
  - `backend/identity.py`: no header → `GUEST`.
  - `services/learner/username.py` holds `GUEST`.
  - `progress_store.claim_guest` moves `GUEST` rows.
  - `routers/progress.py` sets `named = user != GUEST`, so guests earn 0 XP.
  - `main.py`'s crash log logs the profile header.
- Frontend:
  - `lib/learner/profile.js` `profileHeaders()` sends nothing for a guest.
  - `api.js` adds those headers to every call.
  - `lib/store/stored.js` `ownKeys()` treats every bare key except the username as the guest's shelf. **A new
    bare key for the device id would be wiped by "Clear it all" before `forgetProgress` runs, and copied into
    a new account's shelf.** Both have to be closed (G3, G4).
- The guest record is read for guests by `summaryQuery` and `reviewQuery` (Grow worlds, the Quiz, Similar, Colloquial
  words). `overviewQuery` is signed-in only.

## 3 · Designs scored

| Criterion | A · server record per device id | B · guest answers kept in the browser | C · a generated hidden account |
|---|---|---|---|
| Isolation (G1) | yes | yes | yes |
| One source of truth (FSRS, overview on the server) | yes, unchanged | no: FSRS, overview and review rebuilt in JS | yes |
| Size of change | small: identity, claim, sweep, one header | large: every summary and review reader | medium |
| Security | 128-bit secret, never listed | nothing leaves the device | **bad**: a name with no password can be typed by anyone, and it shows in the beta account list and the ranking |
| Upgrade on sign-up | the existing `keep`, re-pointed | a bulk upload of rows with no history | a rename of an account |
| Old cached pages | no header → legacy record | — | — |

**How A carries the id: a header, not a signed cookie** (strategy Pick 0.1 said a cookie).
- A header is how the username already travels (`X-Tafheem-Profile`, set in one axios interceptor).
- A cookie is sent by the browser on cross-site requests too, so every write route would then need a CSRF
  guard.
- Signing guards against a forged id, but a forged id here only opens an empty record of the forger's
  own choosing. The secret is the 128 random bits, which no one else sees.

**Picked A.** B duplicates the store's rules in the page, which the codebase rules out ("lib/learner/progress.js
stays the only code that talks to the store"). C puts guessable, password-less names into the account list.

## 4 · Contract

```
frontend  lib/learner/profile.js
  deviceId(): string                      32 hex; made once, kept under config profile.deviceKey ("guest"),
                                          held in memory if storage throws
  profileHeaders(name = getProfile())     name ? { X-Tafheem-Profile } : { X-Tafheem-Guest: deviceId() }
                                          (sign-up sends its typed name; api.js then adds the device header,
                                          so the server knows which device to claim from)
frontend  lib/store/stored.js
  ownKeys(): the guest's keys leave out PROFILE.storageKey and PROFILE.deviceKey

backend   services/learner/username.py
  GUEST = "local"                          the legacy shared record (no header)
  DEVICE = "guest:"                        prefix of a device's record key
  device_key(raw: str) -> str              "guest:<hex>"; ValueError unless ^[0-9a-f]{32}$
  is_guest(user: str) -> bool              GUEST, or a device key
backend   identity.py
  guest(sent = Header(None, alias="X-Tafheem-Guest")) -> str
                                           device_key(sent), GUEST when absent, 422 when malformed
  typed_name(...) -> str                   the profile name when sent (the device id is then not read, so a
                                          bad one never blocks someone logged in), else the device's record
  current_user                             passes any is_guest through (was GUEST only: a device would get 401)
  typed / named                            refuse any is_guest (not only GUEST)
  GUEST_OF = Depends(guest)                for sign-up's keep
backend   services/learner/progress_store.py
  SCHEMA's account backfill                leaves out `guest:%`: it re-runs on every connection and makes every
                                          other `user` an account (public, listed), so a device record would
                                          become a listed, typeable account
  claim_guest(user, guest=GUEST)           moves that guest's attempts and feedback only
  sweep_guests(days) -> int                deletes device records idle `days`; feedback → ''. One write
                                          transaction whose statements each pick the idle devices themselves,
                                          so an answer landing meanwhile is never swept; a key range, not LIKE,
                                          so the (user, …) index serves it
backend   services/core/startup.py         "guest_sweep" step (startup_background)
backend   config.py                        progress_guest_days: int = Field(default=180, gt=0)
backend   routers/progress.py              named = not is_guest(user); sign_up(keep) → claim_guest(user, device),
                                          and nothing when the page names no device (the shared record is
                                          every old page's, not the signer's)
```

**Why 180 days, not Firebase's 30:** spaced review spaces a known word out by weeks. A guest coming back to
review on day 40 must still find their words. Rows are small, so the storage cost is low.

## 5 · Threat model

| Threat | Answer |
|---|---|
| Guessing another device's id | 2^128 ids, never listed, and logs keep the path only (the crash log names the profile header, which a guest does not send) |
| Header injection or SQL | strict regex before use; every query has parameters |
| Minting many ids to grow the database | rows per answer are the same as today, the existing rate limit applies, and the sweep clears idle ids |
| A guest id passed off as a username | `:` is not a name character, and `typed` and `named` refuse `is_guest` |
| Shared computer | one device = one record by design. "Clear it all" and sign-up with keep both empty it |
| The id leaking into an account's shelf (sent to the server under a name) | `ownKeys` leaves it out (G4) |
| Old page with no header | the legacy record, as before (G7); its sign-up with keep takes nothing |
| A device record turned into an account by the backfill on connection open | the backfill leaves out `guest:%`; a test reopens the connection |

## 6 · Migration

Decision: the old shared `local` record is **not adopted** by any device. Its rows are many guests' answers
mixed together, so no device can honestly claim them, which is the bug itself. After this ships, a guest's
Review and Grow plans start from their own answers only. The browser's own Grow steps (`progress:` keys) stay,
because they were always this device's. The rows stay where they are, and pages cached from before this
change keep writing there until they reload.

Found by the review but not changed here. It is older than this plan, and deciding it is a product
call:
- Other bare device keys are counted as the guest's shelf, so sign-up with keep copies them into the
  account and "Clear it all" wipes them: `recorder-key` (`record/Studio.jsx`) and `install-dismissed`.
- The fix is the same rule as G4, a list of device-only keys in `ownKeys`. It ships on its own.

## 7 · Slices (tests first)

1. Backend identity: `device_key`, `is_guest`, the `guest` dependency, and `typed`/`named` refusals. Tests: a malformed id → 422,
   two ids → two records, a guest id refused at sign-up, log-in and account routes.
2. Claim and forget: `claim_guest(user, guest)`. Tests: keep moves only this device's rows, and leaves other
   devices and the legacy record alone.
3. Sweep: `sweep_guests` + config + startup step. Tests: an idle device swept, a fresh device kept, a named
   account and the legacy record never swept, reports kept under ''.
4. Frontend: `deviceId`, the headers, `ownKeys`. Tests: stable across calls, 32 hex, made fresh when the stored
   value is malformed, memory fallback when storage throws, not in a guest's shelf, both headers on sign-up.
5. Docs: plan (this), comments that said "every guest shares one record", `config/profile.json` `_comment`.
6. Verify: pytest, vitest, eslint, mutants, Playwright with two browser profiles. A fresh-context review of
   this plan against the code ran before the build; its findings are in §4, §5 and §6.

Pre-mortem:

- *"Clear it all" stops deleting a guest's server answers.* Guarded by the G3 test.
- *A cached old page breaks.* Guarded by G7: no header still works.
- *`crypto.randomUUID` fails on http LAN.* Avoided: `getRandomValues` is used instead.

## 8 · Slice 2 (next PR): guests earn XP, a streak and level evidence

Once records are separate, a guest's XP is truly theirs. The routes stay the same:

- `record_attempt` earns for any learner.
- `rewards` and `overview` take a guest.
- The page shows the level ring, streak and "Your Arabic" evidence for a guest.
- "Log in to earn XP" becomes "Log in to keep your XP on any device".

The leaderboard stays accounts only. This is product copy across Home, Grow and the header, so it ships
on its own, after this one is merged and walked.
