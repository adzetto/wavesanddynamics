import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
s = open("dyn.md", encoding="utf-8").read()
print("headings      :", len(re.findall(r"^#{1,4} ", s, re.M)))
print("images        :", len(re.findall(r"!\[", s)))
print("inline maths  :", len(re.findall(r"\$[^$\n]{1,200}\$", s)))
print("display maths :", len(re.findall(r"\$\$", s)) // 2)
print("table rows    :", len(re.findall(r"^\|", s, re.M)))
print("\nheadings:")
for h in re.findall(r"^#{1,4} .*", s, re.M)[:14]:
    print("  ", h[:95])
print("\nfirst figure line:")
for line in s.split("\n"):
    if line.startswith("!["):
        print("  ", line[:200])
        break
print("\nmaths samples:")
for x in re.findall(r"\$[^$\n]{3,140}\$", s)[:8]:
    print("  ", x)
print("\ncaption lines:")
for line in s.split("\n"):
    if line.strip().startswith("Figure ") or "**Figure" in line:
        print("  ", line[:120])
