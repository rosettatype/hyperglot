import timeit
from hyperglot import Languages, Language

print(timeit.timeit(lambda: Language("eng"), number=1))
print(timeit.timeit(lambda: Language("eng"), number=1))

print(timeit.timeit(lambda: Languages(inherit=False), number=1))
print(timeit.timeit(lambda: Languages(inherit=False), number=10))

print(timeit.timeit(lambda: Languages(inherit=True), number=1))
print(timeit.timeit(lambda: Languages(inherit=True), number=10))

print(timeit.timeit(lambda: Languages(), number=10))
print(timeit.timeit(lambda: Languages()["eng"], number=10))