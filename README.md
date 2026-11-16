# Garbage Collection: Reference Counting in CPython

**Author:** Eric Pan  
**Course:** COMP 211

## Topic Introduction

In COMP 211, we manage heap memory manually in C using `malloc()` and `free()`. While this gives us total control and compact memory (a C `int` is just 4 bytes with zero tracking overhead), a single missing `free()` causes a memory leak and freeing memory too early crashes the program. 

Python solves this through **Garbage Collection** by  using **Reference Counting** in **CPython** (the standard C implementation of Python). Under the hood, every Python object is wrapped in a C struct called `PyObject` on the heap that contains an integer reference counter (`ob_refcnt`), trading memory overhead (28 bytes for a single Python `int`) and CPU tracking time for automatic memory safety.

## What I Explored

For this project, I used Claude to generate runnable Python experiments so I could look under the hood of CPython and test how reference counting behaves in practice rather than just reading about it. Specifically, I explored:
* How CPython increments and decrements an object's reference count when variables are assigned, rebound, or go out of scope.
* Whether memory is freed immediately on the exact line a reference count drops to `0` or delayed until later.
* How `sys.getrefcount()` inspects live reference counts across different types of objects and Python versions.
* What happens when two objects point to each other in a **reference cycle**, and how CPython's backup cyclic garbage collector (`gc`) and `weakref` module handle it.

## Most Interesting Discoveries

* **Immediate, Deterministic Cleanup:** Using custom `__del__` destructors, I saw that `del obj` removes the variable name, and the moment an object's reference count hits `0`, CPython destroys it on that exact line—before the very next line of code even executes.
* **Immortal Objects (Python 3.12+):** While a brand-new list reports a raw `sys.getrefcount()` of `2`, checking `sys.getrefcount(5)` printed **`3221225472`**. Python 3.12+ pins frequently used objects like small integers (`-5` to `256`), `None`, and booleans to a special sentinel value so the interpreter never wastes CPU cycles updating their counts or freeing them.
* **Python 3.14 `getrefcount()` Quirk:** When I first ran Claude's script on Python 3.14, subtracting `1` from `sys.getrefcount()` inside a function printed a count of `0` for a live object. Investigating this taught me that Python 3.14 introduced a `LOAD_FAST_BORROW` optimization that borrows local references without adding `+1` temporary overhead.
* **Reference Cycles Need a Backup:** When two objects point to each other (`D <-> E`), deleting their variable names leaves both stuck at `refcount = 1`. Reference counting alone leaks this memory forever, requiring CPython's periodic **Cyclic Garbage Collector** (`gc.collect()`) or weak references (`weakref.ref`) to break the loop.

## How to Run the Demos

Requires standard **CPython** (Python 3.12+ recommended).

* **`python3 get_ref_count.py`**: Compares `sys.getrefcount()` on a new list (`2`) vs. the immortal integer `5` (`3221225472`).
* **`python3 refcount_del_demo.py`**: Uses a `__del__` destructor to demonstrate immediate cleanup with `del`, variable rebinding, function scope exit, reference cycles (`gc.collect()`), and `weakref.ref`.
* **`python3 del_timing_demo.py`**: Builds a parent-child tree with and without back-links, printing the exact line number where each node is destroyed and showing automatic cycle collection during a loop.