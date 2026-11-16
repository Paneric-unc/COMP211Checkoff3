# PID: 730844553

"""
Demonstrates when CPython calls __del__:
  - immediately, when an object's reference count drops to zero
  - later, when the object is stuck in a reference cycle and has to wait
    for the cyclic garbage collector

Run with:  python3 refcount_del_demo.py
(Behaviour shown is specific to CPython; PyPy and others may differ.)
"""

import gc
import sys
import weakref


def _measure_overhead():
    """How many extra references does sys.getrefcount() report for a local variable?

    Up to Python 3.13, passing a local to getrefcount() added one temporary
    reference, so the result was 1 too high. Python 3.14 "borrows" the reference
    instead (the LOAD_FAST_BORROW optimization), so nothing extra is added.
    A brand-new local object has exactly one real reference, so whatever
    getrefcount() reports above 1 is the overhead on this Python version.
    """
    probe = object()
    return sys.getrefcount(probe) - 1


OVERHEAD = _measure_overhead()


def refcount(raw):
    """Turn a raw sys.getrefcount() result into the real number of references."""
    return raw - OVERHEAD


class Tracked:
    def __init__(self, name):
        self.name = name
        self.partner = None
        print(f"    [created]   {self.name}")

    def __del__(self):
        print(f"    [__del__]   {self.name}")


def heading(title):
    print("\n" + "=" * 64)
    print(title)
    print("=" * 64)


def demo_del_statement():
    heading("1. No cycle: `del` removes the last reference")
    obj = Tracked("A")
    print(f"    refcount of A: {refcount(sys.getrefcount(obj))}  (only the name obj)")
    print("    about to run: del obj")
    del obj
    print("    line after `del obj` ran  <- __del__ already printed above")


def demo_rebinding():
    heading("2. No cycle: rebinding a name drops the old object")
    x = Tracked("B")
    y = x
    print(f"    refcount of B: {refcount(sys.getrefcount(x))}  (x and y)")
    print("    about to run: x = None   (y still holds B)")
    x = None
    print("    B still alive, nothing printed")
    print("    about to run: y = None   (last reference)")
    y = None
    print("    line after `y = None` ran")


def demo_function_scope():
    heading("3. No cycle: local variable goes away when the function returns")

    def make_and_drop():
        local = Tracked("C")
        print("    function is returning...")

    make_and_drop()
    print("    back in caller  <- C was destroyed as the function returned")


def demo_cycle():
    heading("4. Cycle: D and E point at each other")
    # Turn off the automatic collector so it can't run at a random moment
    # and blur the demonstration. We will trigger it by hand.
    gc.disable()
    try:
        d = Tracked("D")
        e = Tracked("E")
        d.partner = e
        e.partner = d
        print(f"    refcount of D: {refcount(sys.getrefcount(d))}  (name d + e.partner)")
        print(f"    refcount of E: {refcount(sys.getrefcount(e))}  (name e + d.partner)")

        print("    about to run: del d, e")
        del d, e
        print("    line after `del d, e` ran  <- NO __del__ yet!")
        print("    Both objects are unreachable, but each still has refcount 1,")
        print("    because the other one points to it. Refcounting alone is stuck.")

        print("\n    about to run: gc.collect()")
        found = gc.collect()
        print(f"    gc.collect() found {found} unreachable objects")
        print("    <- the cycle collector detected the loop and ran __del__")
    finally:
        gc.enable()


def demo_weakref_breaks_cycle():
    heading("5. Fix: use a weak reference for the back-link")
    gc.disable()
    try:
        f = Tracked("F")
        g = Tracked("G")
        f.partner = g                  # strong reference: F keeps G alive
        g.partner = weakref.ref(f)     # weak reference: does NOT raise F's count
        print(f"    refcount of F: {refcount(sys.getrefcount(f))}  (only the name f)")

        print("    about to run: del f")
        del f
        print("    F freed immediately. G lost F's reference but the name g still holds it")
        print("    about to run: del g")
        del g
        print("    G freed immediately too; no gc.collect() was needed")
    finally:
        gc.enable()


if __name__ == "__main__":
    print(f"Python {sys.version.split()[0]} ({sys.implementation.name})")
    print(f"sys.getrefcount() overhead for locals on this version: {OVERHEAD}")
    demo_del_statement()
    demo_rebinding()
    demo_function_scope()
    demo_cycle()
    demo_weakref_breaks_cycle()
    print("\nDone.")
