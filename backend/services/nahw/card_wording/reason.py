"""A card's reason held as its parts while the passes word it, and written out once.

    [front، ...] lead لأنه because[، extra ...]. rule[، tail ...]

مرفوع لأنه خبر إن. القاعدة: ... is lead «مرفوع », because «خبر إن», rule «القاعدة: ...». A pass
changes a part (the because a sister names, a line said first), never searches the whole text,
so the rule's own words are never rewritten. Read and written back unchanged, a reason is the
same text."""
from __future__ import annotations

from dataclasses import dataclass, field

BECAUSE = "لأنه "
COMMA = "، "
STOP = ". "


@dataclass
class Reason:
    lead: str
    because: str | None  # what follows لأنه; None when the reason gives no because
    rule: str | None  # what follows the first full stop
    front: list[str] = field(default_factory=list)  # said before the word's own reason
    extras: list[str] = field(default_factory=list)  # said after the because, before the rule
    tail: list[str] = field(default_factory=list)  # said after the rule

    @classmethod
    def read(cls, text: str) -> Reason:
        head, stop, rule = text.partition(STOP)
        lead, sep, because = head.partition(BECAUSE)
        return cls(lead, because if sep else None, rule if stop else None)

    def says(self, role: str) -> bool:
        """The because names this role first (لأنه خبر إن ...)."""
        return self.because is not None and self.because.startswith(role)

    def rename(self, role: str, name: str) -> None:
        """لأنه اسم كان → لأنه اسم ليس: the because's first words, the rest kept."""
        if self.says(role):
            self.because = name + self.because[len(role):]

    def swap(self, old: str, new: str) -> None:
        """The first `old` in the reason, in reading order, becomes `new` (لما قبله → لـ«زيدٌ»)."""
        for name in ("front", "lead", "because", "extras", "rule", "tail"):
            part = getattr(self, name)
            for i, said in enumerate(part if isinstance(part, list) else [part]):
                if said and old in said:
                    said = said.replace(old, new, 1)
                    if isinstance(part, list):
                        part[i] = said
                    else:
                        setattr(self, name, said)
                    return

    def text(self) -> str:
        head = self.lead + (BECAUSE + self.because if self.because is not None else "")
        head = COMMA.join([*self.front, head, *self.extras])
        return head + (STOP + self.rule if self.rule is not None else "") + "".join(COMMA + t for t in self.tail)
