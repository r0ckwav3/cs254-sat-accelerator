from pathlib import Path
from importlib import import_module
import traceback

# find all test files
this_path = Path(__file__)
test_dir = this_path.parents[0]
test_suites = [] # pair (filename, list of functions)

for file in test_dir.iterdir():
    if file != this_path and file.suffix == ".py":
        print(f"found test file {file.name}")
        mod = import_module(file.stem)
        try:
            test_suites.append((file.name, mod.tests))
        except AttributeError as e:
            print(f"[!] failed to find tests list in {file.name}")

# run test suites
total_sucesses = 0
total_failures = 0
for suite in test_suites:
    print(f"Running test file {suite[0]}")
    for test in suite[1]:
        testname = test.__name__
        print(f" - test {testname}: ", end = "")
        try:
            test()
            print("\x1b[1;32msuccess\x1b[m")
            total_sucesses += 1
        except Exception:
            print("\x1b[1;31mfailure\x1b[m")
            traceback.print_exc()
            print()
            total_failures += 1

print(f"Tests Run: {total_sucesses + total_failures}")
print(f"Tests Successes: {total_sucesses}")
print(f"Tests Failures: {total_failures}")
