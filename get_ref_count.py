# PID: 730844553

import sys

my_list = [1, 2, 3]
print("Refcount of new list:", sys.getrefcount(my_list)) # Prints 2

x = 5
print("Refcount of 5:", sys.getrefcount(x)) # ???
