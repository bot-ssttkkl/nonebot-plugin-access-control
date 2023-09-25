from typing import Optional, NamedTuple


class SubjectModel(NamedTuple):
    content: str
    offer_by: str
    tag: Optional[str]

    def __str__(self):
        return self.content

    def __repr__(self):
        return f"{self.content} (tag: {self.tag}, offer by: {self.offer_by})"
