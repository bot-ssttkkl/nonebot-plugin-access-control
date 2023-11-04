from copy import copy
from collections.abc import Sequence

from .model import SubjectModel


class SubjectManager:
    def __init__(self):
        self.subjects: Sequence[SubjectModel] = []

    def index_of(self, tag: str) -> int:
        for i in range(len(self.subjects)):
            if self.subjects[i].tag == tag:
                return i
        return -1

    def append(self, *subject: SubjectModel):
        self.subjects = [*self.subjects, *subject]

    def insert_after(self, tag: str, *subject: SubjectModel):
        idx = self.index_of(tag)

        if idx != -1:
            if idx != len(self.subjects) - 1:
                self.subjects = [
                    *self.subjects[: idx + 1],
                    *subject,
                    *self.subjects[idx + 1 :],
                ]
            else:
                self.subjects = [*self.subjects, *subject]
        else:
            self.subjects = [*self.subjects, *subject]

    def insert_before(self, tag: str, *subject: SubjectModel):
        idx = self.index_of(tag)

        if idx != -1:
            self.subjects = [
                *self.subjects[:idx],
                *subject,
                *self.subjects[idx:],
            ]
        else:
            self.subjects = [*subject, *self.subjects]

    def replace(self, *subject: SubjectModel):
        self.subjects = copy(subject)

    def remove(self, tag: str):
        idx = self.index_of(tag)
        if idx != -1:
            self.subjects = [*self.subjects]
            self.subjects.pop(idx)
