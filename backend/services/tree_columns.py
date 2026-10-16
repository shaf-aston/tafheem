"""Cutting a tree into the columns a chart draws: one place for both the
treebank ayah and the derived one, so neither needs the other's engine."""
from __future__ import annotations


def cut(result: dict) -> dict:
    """An ayah's tree in the shape every chart is drawn from: a connector glued onto
    a word (فَ / وَ, marked `prefix_arabic`) cut into its own column, and `written`
    naming the written word each column came from, as the typed sentence already has.

    The chart only ever folds columns back together (its Merged view), so a word is
    cut in one place only. Runs at the API edge: the scorers keep whole words.
    """
    words, tree = result["words"], result.get("tree")
    cuts: dict[int, tuple[str, dict]] = {}  # word -> (connector text, its piece)

    def find(node: dict) -> None:
        for child in node.get("children") or ():
            find(child)
        # the connector is written first, so it is always the word's first piece
        text, word = node.get("prefix_arabic"), node.get("word")
        if text and not node.get("children") and node.get("parts") \
                and words[word].startswith(text) and len(text) < len(words[word]):
            cuts[word] = (text, node["parts"][0])

    if tree:
        find(tree)
    columns, written, own = [], [], {}  # own: old word -> the column of what is left of it
    for i, full in enumerate(words):
        text = cuts[i][0] if i in cuts else ""
        if text:
            columns.append(text)
            written.append(i)
        own[i] = len(columns)
        columns.append(full[len(text):])
        written.append(i)

    def renumber(node: dict) -> list[dict]:
        if node.get("children"):
            return [{**node, "children": [n for child in node["children"] for n in renumber(child)]}]
        if node.get("word") is None:
            return [node]
        word = node["word"]
        remainder = {k: v for k, v in node.items() if k != "prefix_arabic"}  # read here, never sent
        remainder["word"] = own[word]
        if word not in cuts:
            return [remainder]
        piece, *rest = node["parts"]
        # a word left with one piece is named by it alone (وَ + قَامَ: just فعل)
        remainder.update(parts=rest if len(rest) > 1 else [],
                         **({} if len(rest) > 1 else {"role": rest[0]["role"], "tone": rest[0]["tone"]}))
        connector = {"word": own[word] - 1, "role": piece["role"], "tone": piece["tone"], "ghair_aamil": True}
        return [connector, remainder]

    return {**result, "words": columns, "written": written,
            "tree": renumber(tree)[0] if tree else tree}
