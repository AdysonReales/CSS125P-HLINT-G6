# HLInt.XXX - Simple "HL" Language Interpreter

Welcome, team! This repository contains the source code and files for our CSS125L project. Below is a quick guide on our project structure, how to run the interpreter, and who is responsible for what.

---

## 👥 Group Members & Responsibilities

*   **Member 1 (Lexer & Preprocessor):** File I/O, whitespace removal (`NOSPACES.TXT`), and reserved word/symbol extraction (`RES_SYM.TXT`).
*   **Member 2 (Syntax Analyzer & Engine):** Syntax error checking (`ERROR` / `NO ERROR(S) FOUND`), variable management, expression evaluation, and screen output (`output<<`).
*   **Member 3 (QA, Documentation & Media):** Test cases, PDF documentation, screenshots, video demo production, and final archiving.

---

## 📂 File Architecture Guide

*   `src/main.py` — The main entry point script to run the program.
*   `src/lexer.py` — Member 1's code for preprocessing and tokenization.
*   `src/interpreter.py` — Member 2's code for parsing, validation, and execution.
*   `test_programs/` — Contains our `.HL` test files (`PROG1.HL`, `PROG2.HL`, `PROG3.HL`).
*   `outputs/` — Where `NOSPACES.TXT` and `RES_SYM.TXT` are generated automatically.
*   `group_members.txt` — Required text file listing our names and sections for submission.

---

## 🚀 How to Run the Interpreter

Make sure you have **Python 3** installed on your machine.

1. Open your terminal or command prompt in the project root folder.
2. Run the main script:
   ```bash
   python src/main.py
