"""Reproduce the historical recursion failure in Python fractional-indexing 0.1.3.
This statement is version-specific. Later package releases may behave differently.
"""
import sys
try:
    import fractional_indexing as fi
except ImportError as exc:
    raise SystemExit('Install fractional-indexing==0.1.3 first') from exc

# Keep Python's normal recursion limit. Repeatedly allocate inside one interior gap.
left=fi.generate_key_between(None,None)
right=fi.generate_key_between(left,None)
for i in range(20000):
    try:
        left=fi.generate_key_between(left,right)
    except RecursionError:
        print('RecursionError after',i+1,'interior insertions; recursionlimit=',sys.getrecursionlimit())
        break
else:
    print('No RecursionError observed; check installed package version and Python runtime')
