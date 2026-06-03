import sys
import os
from pythong.lib.runtime import run_file

def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: pythong-cong <file.cong> [args...]", file=sys.stderr)
        sys.exit(1)
    filepath = args[0]
    sys.argv = args
    if not os.path.isfile(filepath):
        print(f"pythong-cong: can't open file '{filepath}'", file=sys.stderr)
        sys.exit(1)
    run_file(filepath)

if __name__ == "__main__":
    main()
