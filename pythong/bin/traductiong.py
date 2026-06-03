import sys
import os
from pythong.lib.core import transform_py_to_cong

def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: pythong-traductiong <file.py> [output.cong]", file=sys.stderr)
        sys.exit(1)
    infile = args[0]
    outfile = args[1] if len(args) > 1 else os.path.splitext(infile)[0] + ".cong"
    if not os.path.isfile(infile):
        print(f"pythong-traductiong: can't open file '{infile}'", file=sys.stderr)
        sys.exit(1)
    with open(infile, "r", encoding="utf-8") as f:
        source = f.read()
    cong_source = transform_py_to_cong(source)
    with open(outfile, "w", encoding="utf-8") as f:
        f.write(cong_source)
    print(f"Written: {outfile}")

if __name__ == "__main__":
    main()
