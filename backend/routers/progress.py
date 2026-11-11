"""What a learner has answered, and what it says about them.

Thin on purpose: every rule about what counts as still-to-review, and every
piece of SQL, lives in services/learner (attempts, accounts, circles). This file only turns a
request into a call and the answer into a response model.

Nothing here knows what an item is. The quiz sends the id of a meaning; the
tags that say what kind of word that is live in the page's own word list, which
is where the "what do I keep getting wrong" reading is made.
"""
from __future__ import annotations

import json
from contextlib import contextmanager

from fastapi import APIRouter, Depends, HTTPException, Query, Response

from backend.config import get_settings
from backend.identity import (
    DEVICE, NAMED, OWN, PROVEN, PROVEN_USER, SESSION, TOKEN, TYPED, USER, give_token, take_token,
)
from backend.services.core.ratelimit import ACCOUNT
from backend.models.progress import (
    Account,
    AccountNames,
    AttemptIn,
    AttemptSaved,
    CircleDetail,
    CircleIn,
    CircleItem,
    CircleList,
    FeedbackIn,
    Forgotten,
    InviteIn,
    LogInIn,
    ItemStats,
    Leaderboard,
    ModuleOverview,
    Overview,
    ParentIn,
    ProgressSummary,
    PublicIn,
    Recovery,
    ReviewList,
    Rewards,
    RoleIn,
    Shelf,
    SignedIn,
    SignUpIn,
)
from backend.services.core import audit
from backend.services.learner import accounts, attempts, circles, lifecycle, tokens
from backend.services.learner import identity as guest_identity
from backend.services.learner.username import GUEST, clean_name

router = APIRouter(prefix="/api/progress", tags=["progress"])

_MODULE = Query("quiz", min_length=1, max_length=32, description="Which panel is asking")
_TZ = Query(0, ge=-720, le=840, description="Minutes east of UTC on the learner's clock")


@router.post("/attempts", response_model=AttemptSaved)
async def record_attempt(attempt: AttemptIn, user: str = USER) -> AttemptSaved:
    """File one answer; return its XP and new totals. Only the old shared record earns none: it is many people's."""
    own = user != GUEST
    earns = own and attempt.correct and attempts.earns(attempt.module, attempt.item, user, attempt.tz)
    row_id = attempts.record(
        module=attempt.module,
        item=attempt.item,
        correct=attempt.correct,
        ms=attempt.ms,
        context=attempt.context,
        user=user,
    )
    return AttemptSaved(
        id=row_id,
        earned=get_settings().rewards_xp_per_answer if earns else 0,
        rewards=Rewards(**attempts.rewards(user, attempt.tz)) if own else None,
    )


@router.post("/feedback", response_model=AttemptSaved)
async def leave_feedback(note: FeedbackIn, user: str = USER) -> AttemptSaved:
    """File a report about a question that looks wrong."""
    message = note.message.strip()
    if not message:
        raise HTTPException(status_code=422, detail="message is empty")
    return AttemptSaved(id=attempts.leave_feedback(
        module=note.module, item=note.item, message=message, user=user,
    ))


@router.delete("", response_model=Forgotten)
async def forget_progress(user: str = PROVEN_USER) -> Forgotten:
    """Delete every answer and the shelf of this name. The Settings wipe calls it."""
    return Forgotten(deleted=lifecycle.forget(user))


@router.get("/summary", response_model=ProgressSummary)
def get_summary(module: str = _MODULE, user: str = USER) -> ProgressSummary:
    """Every item answered in this module, with its record and whether it is due or known."""
    return ProgressSummary(
        module=module,
        items=[
            ItemStats(
                item=row["item"],
                attempts=row["attempts"],
                wrong=row["wrong"],
                avgMs=row["avg_ms"],
                due=row["due"],
                known=row["known"],
                dueAt=row["due_at"],
                words=row["words"],
            )
            for row in attempts.summary(module, user)
        ],
    )


@router.get("/overview", response_model=Overview)
def get_overview(tz: int = _TZ, user: str = USER) -> Overview:
    """Every module this learner answered in, with totals and the streak of days."""
    return _overview(attempts.overview(user, tz))


@router.get("/rewards", response_model=Rewards)
def get_rewards(tz: int = _TZ, user: str = OWN) -> Rewards:
    """XP, level, streak, for an account or a device's guest. Cheap (no FSRS replay), for the header."""
    return Rewards(**attempts.rewards(user, tz))


def _overview(found: dict) -> Overview:
    modules = [ModuleOverview(**{**row, "lastAt": row["last_at"]}) for row in found.pop("modules")]
    return Overview(modules=modules, **found)


@router.get("/review", response_model=ReviewList)
def get_review(module: str = _MODULE, user: str = USER) -> ReviewList:
    """Items due for review now, earliest first."""
    return ReviewList(module=module, items=attempts.review_items(module, user))


@router.post("/signup", response_model=SignedIn, dependencies=[Depends(ACCOUNT)])
async def sign_up(body: SignUpIn, response: Response, user: str = TYPED, device: str = DEVICE,
                  held: str | None = TOKEN) -> SignedIn:
    """Take a free username; the account handed back holds its one spelling, which the page keeps, and the
    account's first recovery code. This browser gets the device token (services/learner/tokens.py).

    `keep` moves this device's guest answers onto it. A page that names no device (one cached from before
    devices had ids) keeps nothing: the shared record it wrote to holds every such guest's answers, not its own.
    """
    if (minted := tokens.open_account(user)) is None:
        audit.event("signup_taken", user=user)
        raise HTTPException(status_code=409, detail="That username is taken")
    if body.keep:
        guest_identity.merge(device, user)
    audit.event("signup", user=user, kept=body.keep)
    return _signed_in(user, minted, response, held)


_NEEDS_CODE = "Type this account's recovery code"


@router.post("/login", response_model=SignedIn, dependencies=[Depends(ACCOUNT)])
async def log_in(response: Response, body: LogInIn | None = None, user: str = TYPED,
                 held: str | None = TOKEN) -> SignedIn:
    """The account of a signed-up username, holding its one spelling, with this browser proven to be its.

    - This browser already holds the account's token (the page forgot the name, not the cookie): no code.
    - With the recovery code: a token for this browser, and the next code (each code works once).
    - An account from before tokens that nobody has claimed, while claims are open: the first browser to log
      in claims it (trust on first use, logged so the owner can see and undo a race; the global ranking hides
      unclaimed names meanwhile, so there is no list of them to race for).

    A wrong or missing code is a 403, not a 401: the page asks for the code rather than logging out.
    """
    body = body or LogInIn()
    if accounts.account(user) is None:
        audit.event("login_unknown", user=user)
        raise HTTPException(status_code=404, detail="No account with that username")
    if held is not None and tokens.owner(held) == user:
        audit.event("login", user=user, by="token")
        return _signed_in(user, None, response, None)
    if body.code:
        if (minted := tokens.recover(user, body.code)) is None:
            audit.event("login_refused", user=user)
            raise HTTPException(status_code=403, detail="That recovery code is not this account's")
        audit.event("login", user=user, by="code")
        return _signed_in(user, minted, response, held)
    if get_settings().account_claims_open and (minted := tokens.claim(user)) is not None:
        audit.event("token_claimed", user=user)
        return _signed_in(user, minted, response, held)
    audit.event("login_needs_code", user=user)
    raise HTTPException(status_code=403, detail=_NEEDS_CODE)


def _signed_in(user: str, minted: tuple[str, str] | None, response: Response, held: str | None) -> SignedIn:
    """The account, with the new token set as this browser's cookie. A token the browser held for another
    account goes: one browser, one account at a time, and no token is left behind that nobody holds."""
    recovery = None
    if minted is not None:
        token, recovery = minted
        if held is not None:
            tokens.revoke(held)
        give_token(response, token)
    return SignedIn(**accounts.account(user), recovery=recovery)


@router.post("/recovery", response_model=Recovery, dependencies=[Depends(ACCOUNT)])
async def new_recovery(who: tuple[str, str] = SESSION) -> Recovery:
    """A new recovery code for this account, to move to another phone or because the old one was seen.
    The old code stops working; logged-in devices stay logged in."""
    user, _ = who
    audit.event("recovery_new", user=user)
    return Recovery(code=tokens.new_recovery(user))


@router.delete("/session", response_model=Forgotten)
async def log_out(response: Response, who: tuple[str, str] = SESSION) -> Forgotten:
    """Log this browser out: its token opens nothing again, and the cookie goes. The account stays."""
    user, token = who
    tokens.revoke(token)
    take_token(response)
    audit.event("logout", user=user)
    return Forgotten(deleted=1)


@router.delete("/sessions", response_model=Forgotten)
async def log_out_others(who: tuple[str, str] = SESSION) -> Forgotten:
    """Log out every other device of this account (a lost or shared phone); this one stays logged in."""
    user, token = who
    gone = tokens.revoke_others(user, token)
    audit.event("logout_others", user=user, devices=gone)
    return Forgotten(deleted=gone)


@router.get("/account", response_model=Account)
def get_account(response: Response, user: str = NAMED, held: str | None = TOKEN) -> Account:
    """The profile page's facts about this username, and whether this browser holds its token. The page asks
    on every load, so this is where the cookie is renewed: a reader who keeps coming back stays logged in."""
    if held is not None:
        give_token(response, held)
    return Account(**accounts.account(user), proven=held is not None)


@router.delete("/account", response_model=Forgotten)
async def delete_account(user: str = PROVEN) -> Forgotten:
    """Delete this username, every answer it gave and its shelf; the name is free again."""
    deleted = lifecycle.delete_account(user)
    audit.event("account_deleted", user=user, answers=deleted)
    return Forgotten(deleted=deleted)


@router.get("/saved", response_model=Shelf)
def get_shelf(user: str = NAMED) -> Shelf:
    """What the page kept for this account, so it follows the name to another device."""
    return Shelf(data=accounts.shelf(user))


@router.put("/saved", response_model=Shelf)
async def put_shelf(body: Shelf, user: str = PROVEN) -> Shelf:
    """Replace this account's shelf whole with what the page holds now."""
    if len(json.dumps(body.data, ensure_ascii=False).encode()) > get_settings().saved_max_bytes:
        raise HTTPException(status_code=413, detail="Too much saved for one account")
    accounts.keep_shelf(user, body.data)
    return body


@router.put("/account/public", response_model=Account)
def put_public(body: PublicIn, user: str = PROVEN) -> Account:
    """Show in, or hide from, the global ranking."""
    accounts.set_public(user, body.public)
    audit.event("account_public", user=user, public=body.public)
    return Account(**accounts.account(user))


@router.get("/leaderboard", response_model=Leaderboard)
def get_leaderboard(module: str = _MODULE, circle: int | None = None, user: str = USER) -> Leaderboard:
    """A circle's joined members by words learnt, or the global top accounts plus the asker's own place."""
    if circle is not None:
        with _refused():
            return Leaderboard(rows=circles.circle_ranking(circle, module, user), you=None)
    rows, you = accounts.leaderboard(module, user)
    return Leaderboard(rows=rows[: get_settings().leaderboard_size], you=you)


@router.get("/accounts", response_model=AccountNames)
def list_accounts() -> AccountNames:
    """Every username, for the log-in box while in beta; not found once that is switched off."""
    if not get_settings().beta_list_accounts:
        raise HTTPException(status_code=404, detail="Not found")
    return AccountNames(names=accounts.account_names())


@contextmanager
def _refused():
    """The store's rules as the answers a page expects: unknown 404, not allowed 403, not valid 422."""
    try:
        yield
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from None
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from None
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from None


def _circles(user: str) -> CircleList:
    mine = [CircleItem(**{**row, "invitedBy": row.pop("invited_by")}) for row in circles.my_circles(user)]
    return CircleList(kinds=circles.circle_kinds(), circles=mine)


def _member_name(typed: str) -> str:
    with _refused():
        return clean_name(typed)


@router.get("/circles", response_model=CircleList)
def list_circles(user: str = PROVEN) -> CircleList:
    """Every circle I am in, and every invite waiting for me."""
    return _circles(user)


@router.post("/circles", response_model=CircleDetail)
def create_circle(body: CircleIn, user: str = PROVEN) -> CircleDetail:
    """Make a circle, with me as its admin."""
    with _refused():
        return CircleDetail(**circles.circle_detail(
            circles.create_circle(user, body.name, body.kind, body.parent), user))


@router.get("/circles/{circle}", response_model=CircleDetail)
def get_circle(circle: int, user: str = PROVEN) -> CircleDetail:
    """One circle and the people the asker may see in it."""
    with _refused():
        return CircleDetail(**circles.circle_detail(circle, user))


@router.delete("/circles/{circle}", response_model=CircleList)
def delete_circle(circle: int, user: str = PROVEN) -> CircleList:
    with _refused():
        circles.delete_circle(circle, user)
    return _circles(user)


@router.post("/circles/{circle}/members", response_model=CircleDetail)
def invite_member(circle: int, body: InviteIn, user: str = PROVEN) -> CircleDetail:
    """An admin invites an existing username; they see nothing until they accept."""
    member = _member_name(body.member)
    with _refused():
        circles.invite(circle, user, member, body.role)
        return CircleDetail(**circles.circle_detail(circle, user))


@router.post("/circles/{circle}/accept", response_model=CircleList)
def accept_invite(circle: int, user: str = PROVEN) -> CircleList:
    with _refused():
        circles.accept(circle, user)
    return _circles(user)


@router.post("/circles/{circle}/decline", response_model=CircleList)
def decline_invite(circle: int, user: str = PROVEN) -> CircleList:
    with _refused():
        circles.decline(circle, user)
    return _circles(user)


@router.post("/circles/{circle}/leave", response_model=CircleList)
def leave_circle(circle: int, user: str = PROVEN) -> CircleList:
    with _refused():
        circles.leave(circle, user)
    return _circles(user)


@router.delete("/circles/{circle}/members/{member}", response_model=CircleDetail)
def remove_member(circle: int, member: str, user: str = PROVEN) -> CircleDetail:
    name = _member_name(member)
    with _refused():
        circles.remove(circle, user, name)
        return CircleDetail(**circles.circle_detail(circle, user))


@router.put("/circles/{circle}/members/{member}", response_model=CircleDetail)
def set_member_role(circle: int, member: str, body: RoleIn, user: str = PROVEN) -> CircleDetail:
    name = _member_name(member)
    with _refused():
        circles.set_role(circle, user, name, body.role)
        return CircleDetail(**circles.circle_detail(circle, user))


@router.put("/circles/{circle}/parent", response_model=CircleDetail)
def set_circle_parent(circle: int, body: ParentIn, user: str = PROVEN) -> CircleDetail:
    """An admin moves a circle inside another circle they admin, or out to stand on its own."""
    with _refused():
        circles.move_circle(circle, user, body.parent)
        return CircleDetail(**circles.circle_detail(circle, user))


@router.get("/circles/{circle}/members/{member}/overview", response_model=Overview)
def get_member_overview(circle: int, member: str, user: str = PROVEN) -> Overview:
    """A joined member's overview, for whoever the circles' rules let see it."""
    name = _member_name(member)
    with _refused():
        return _overview(circles.member_overview(circle, user, name))
