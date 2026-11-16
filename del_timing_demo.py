# PID: 730844553

"""
A parent/child tree, built two ways:
  Part 1: children do NOT point back to the parent  -> no cycle
  Part 2: children DO point back to the parent      -> reference cycle

Each __del__ reports the exact source line that was running when the
object was destroyed, so you can see *where* in your code it happened.

Run with:  python3 del_timing_demo.py   (CPython)
"""

import gc
import sys


def _measure_overhead():
    # Extra references sys.getrefcount() reports for a local variable:
    # 1 up to Python 3.13, 0 on 3.14+ (which "borrows" the argument reference).
    probe = object()
    return sys.getrefcount(probe) - 1


OVERHEAD = _measure_overhead()


DESTROYED = []   # names of nodes whose __del__ has run


class Node:
    def __init__(self, name):
        self.name = name
        self.children = []
        self.parent = None

    def __del__(self):
        DESTROYED.append(self.name)
        # The frame one level up is the Python code that dropped the last reference
        caller = sys._getframe(1)
        print(f"    💥 {self.name} destroyed  (while running line {caller.f_lineno}"
              f" in {caller.f_code.co_name}())")


def build_tree(label, with_back_links):
    root = Node(f"{label}-root")
    for i in (1, 2):
        child = Node(f"{label}-child{i}")
        root.children.append(child)
        if with_back_links:
            child.parent = root          # <- this creates the cycle
    return root


def part1_no_cycle():
    print("\nPART 1: no back-links (no cycle)")
    tree = build_tree("A", with_back_links=False)
    print(f"    refcount of A-root: {sys.getrefcount(tree) - OVERHEAD}")
    print(f"    line {sys._getframe().f_lineno + 1}: del tree")
    del tree
    print("    ✅ all three were destroyed on the `del` line, root first, then its children")


def part2_cycle():
    print("\nPART 2: children point back to the root (cycle)")

    def on_gc(phase, info):
        if phase == "start":
            print(f"    🧹 cycle collector starting (generation {info['generation']})")

    gc.callbacks.append(on_gc)
    try:
        tree = build_tree("B", with_back_links=True)
        print(f"    refcount of B-root: {sys.getrefcount(tree) - OVERHEAD}"
              "  (the name `tree` + two child.parent links)")
        print(f"    line {sys._getframe().f_lineno + 1}: del tree")
        del tree
        print("    ⏳ nothing destroyed: each node is still referenced from inside the cycle")

        print("    now doing unrelated work: allocating lots of small lists...")
        junk = []
        for i in range(1, 200_000):
            junk.append([i])                     # each new list counts toward a GC run
            if "B-root" in DESTROYED:
                print(f"    ✅ cycle cleaned up automatically during iteration {i:,}")
                break
        else:
            print("    collector never ran; forcing it with gc.collect()")
            gc.collect()
    finally:
        gc.callbacks.remove(on_gc)


if __name__ == "__main__":
    print(f"Python {sys.version.split()[0]}  automatic GC thresholds: {gc.get_threshold()}")
    part1_no_cycle()
    part2_cycle()
    print("\nDone.")
