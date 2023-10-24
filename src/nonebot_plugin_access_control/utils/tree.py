from io import StringIO
from typing import Protocol, Optional, TypeVar, Callable
from collections.abc import Collection

from typing_extensions import Self


class TreeNode(Protocol):
    parent: Optional[Self]
    children: Collection[Self]
    name: str


T = TypeVar("T")


def get_tree_summary(
    root: T, children: Callable[[T], Collection[T]], value: Callable[[T], str]
) -> str:
    with StringIO() as sio:

        def walk(node: T, prefix: str = ""):
            node_children = children(node)
            for i, child in enumerate(node_children):
                if i == len(node_children) - 1:
                    sio.write(prefix + "└── " + value(child) + "\n")
                    walk(child, prefix + "    ")
                else:
                    sio.write(prefix + "├── " + value(child) + "\n")
                    walk(child, prefix + "│   ")

        sio.write(value(root) + "\n")
        walk(root)
        return sio.getvalue().strip()
