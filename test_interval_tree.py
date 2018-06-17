from intervaltree import IntervalTree
from iteration_utilities import tail
from intervaltree import Interval


class IntContainer:
    private = 0

    def __str__(self):
        return str(self.private)

    def __iadd__(self, other):
        self.private += other.private


tree = IntervalTree()
tree.addi(2, 4, IntContainer())  # key: 3, +-1
tree.addi(3, 5, IntContainer())  # key: 4, +-1
print(tree.search(3.5))
res = tree.search(3, 5, strict=True)

if len(res) == 1:
    for entry in res:
        entry.data.private += 1
        print(entry.data)

res = tree.search(3, 5, strict=True)
if len(res) == 1:
    for entry in res:
        entry.data.private += 1
        print(entry.data)