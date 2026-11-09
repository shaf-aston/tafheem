"""The recorded picture cases (tests/nahw/picture_cases.jsonl): what `tree.build` was given for a
sentence and the picture it drew, so the picture code is checked alone, without the parser.

Each case was kept because breaking some line of `syntax/picture/` changes its picture, so together
they catch every break any of 2,971 rule sentences and 140 long Qur'an ayahs catch.

    python -m backend.scripts.nahw.picture_cases --rewrite   # after a deliberate picture change: redraw, then read the diff
    python -m backend.scripts.nahw.picture_cases --break     # break each line in turn and count the breaks the cases miss
"""
from __future__ import annotations

import argparse
import ast
import copy
import importlib
import json
import multiprocessing
import queue
from pathlib import Path

CASES = Path(__file__).resolve().parents[3] / "tests" / "nahw" / "picture_cases.jsonl"
PICTURE = "backend.services.nahw.syntax.picture"
PHASES = ["condition", "hang", "jobs", "layout", "names", "places", "rehang", "render", "units", "unwritten"]
HANG_SECONDS = 20  # every case together draws in well under a second; a break that loops is caught
FLIP = {ast.Eq: ast.NotEq, ast.NotEq: ast.Eq, ast.In: ast.NotIn, ast.NotIn: ast.In, ast.Is: ast.IsNot,
        ast.IsNot: ast.Is, ast.Lt: ast.GtE, ast.GtE: ast.Lt, ast.Gt: ast.LtE, ast.LtE: ast.Gt}


def load() -> list[dict]:
    """Every case, its tokens as `tree.build` takes them (`judged` is a frozenset there, a list in JSON)."""
    cases = [json.loads(line) for line in CASES.read_text(encoding="utf-8").splitlines()]
    for case in cases:
        case["tokens"] = [{**t, "judged": frozenset(t["judged"])} if "judged" in t else t for t in case["tokens"]]
    return cases


def drawn(case: dict) -> dict:
    """The picture for a case as the page receives it (JSON: int keys become strings, pairs lists).
    `build` edits the tokens it is given, so it draws from a copy and a case can be drawn again."""
    from backend.services.nahw.syntax import tree
    words, tokens, named = copy.deepcopy((case["words"], case["tokens"], case["named"]))
    return json.loads(json.dumps(tree.build(words, tokens, named), ensure_ascii=False))


def rewrite() -> None:
    cases = load()
    with CASES.open("w", encoding="utf-8", newline="\n") as f:
        for case in cases:
            case["tree"] = drawn(case)
            case["tokens"] = [{**t, "judged": sorted(t["judged"])} if "judged" in t else t for t in case["tokens"]]
            f.write(json.dumps(case, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(f"redrew {len(cases)} cases")


def _breaks(fn: ast.FunctionDef):
    """Every one-step break inside a function: a test turned round, a comparison flipped, and/or
    swapped, a statement dropped."""
    for n in ast.walk(fn):
        if isinstance(n, (ast.If, ast.IfExp, ast.While)):
            yield "negate", n
        if isinstance(n, ast.comprehension) and n.ifs:
            yield "negate", n
        if isinstance(n, ast.Compare) and type(n.ops[0]) in FLIP:
            yield "flip", n
        if isinstance(n, ast.BoolOp):
            yield "andor", n
        if isinstance(n, (ast.Assign, ast.AugAssign, ast.Expr)) and not isinstance(getattr(n, "value", None), ast.Constant):
            yield "drop", n


def _apply(kind: str, n: ast.AST):
    """Make the break; returns what undoes it."""
    if kind == "negate" and isinstance(n, ast.comprehension):
        old = n.ifs[0]
        n.ifs[0] = ast.UnaryOp(ast.Not(), old)
        return lambda: n.ifs.__setitem__(0, old)
    if kind == "negate":
        old = n.test
        n.test = ast.UnaryOp(ast.Not(), old)
        return lambda: setattr(n, "test", old)
    if kind == "flip":
        old = n.ops[0]
        n.ops[0] = FLIP[type(old)]()
        return lambda: n.ops.__setitem__(0, old)
    if kind == "andor":
        old = n.op
        n.op = ast.Or() if isinstance(old, ast.And) else ast.And()
        return lambda: setattr(n, "op", old)
    kept = n.__class__
    n.__class__ = ast.Pass
    return lambda: setattr(n, "__class__", kept)


def _every_break():
    for phase in PHASES:
        module = importlib.import_module(f"{PICTURE}.{phase}")
        path = Path(module.__file__)
        for fn in ast.parse(path.read_text(encoding="utf-8")).body:
            if isinstance(fn, ast.FunctionDef):
                for kind, n in _breaks(fn):
                    yield phase, getattr(module, fn.name), fn, kind, n, path


def _changes_a_picture(cases: list[dict]) -> bool:
    for case in cases:
        try:
            if drawn(case) != case["tree"]:
                return True
        except Exception:
            return True
    return False


def _worker(start: int, answers) -> None:
    """In a child process: make each break from number `start` on, one at a time, and say for
    each whether any case's picture changes. Announces each break first, so a loop is pinned on it."""
    cases = load()
    for at, (_phase, live, fn, kind, n, path) in enumerate(_every_break()):
        if at < start:
            continue
        answers.put(("trying", at))
        undo, original = _apply(kind, n), live.__code__
        code = compile(ast.fix_missing_locations(ast.Module([fn], [])), str(path), "exec")
        undo()
        live.__code__ = next(c for c in code.co_consts if getattr(c, "co_name", "") == fn.name)
        try:
            answers.put(("caught" if _changes_a_picture(cases) else "missed", at))
        finally:
            live.__code__ = original
    answers.put(("end", None))


def score() -> int:
    """Break each line in turn and print every break no case catches; a break that loops is stopped
    and counted as caught. Returns how many were missed."""
    cases = load()
    if _changes_a_picture(cases):
        raise SystemExit("the cases already draw differently; --rewrite first if that was meant")
    found = [(phase, fn.name, getattr(n, "lineno", None) or n.target.lineno, kind)
             for phase, _live, fn, kind, n, _path in _every_break()]
    missed, start = 0, 0
    while start is not None:
        answers = multiprocessing.Queue()
        child = multiprocessing.Process(target=_worker, args=(start, answers))
        child.start()
        trying, start = None, None
        while True:
            try:
                what, at = answers.get(timeout=HANG_SECONDS + (60 if trying is None else 0))  # the first waits for imports
            except queue.Empty:
                child.kill()
                if trying is None:
                    raise SystemExit("the worker never started a break")
                start = trying + 1  # it looped: caught; go on after it
                break
            if what == "end":
                break
            if what == "trying":
                trying = at
            elif what == "missed":
                missed += 1
                phase, name, line, kind = found[at]
                print(f"missed  picture/{phase}.py:{line}  {name}  {kind}", flush=True)
        child.join()
    print(f"{len(found)} breaks, {len(found) - missed} caught, {missed} missed")
    return missed


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--rewrite", action="store_true", help="redraw every stored picture from its stored inputs")
    group.add_argument("--break", dest="breaks", action="store_true", help="count the line breaks the cases miss")
    args = ap.parse_args()
    rewrite() if args.rewrite else score()
