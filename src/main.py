# main.py
# Entry point for HLInt. Usage: python src/main.py [file.HL]

import sys

from lexer import process_source_file


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "test_programs/PROG1.HL"

    try:
        process_source_file(path, output_dir="outputs")
    except FileNotFoundError:
        print(f"Error: File '{path}' not found.")
        sys.exit(1)

    print(f"Processing source file: {path}")
    print("Generated: outputs/NOSPACES.TXT")
    print("Generated: outputs/RES_SYM.TXT")


if __name__ == "__main__":
    main()
