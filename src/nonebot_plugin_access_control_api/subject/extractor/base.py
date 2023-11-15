from typing import Union, Callable
from collections.abc import Sequence

from ..model import SubjectModel

T_SubjectExtractor = Callable[[...], Union[Sequence[SubjectModel], None]]
