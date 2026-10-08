# lexer.py - reads the .HL file, makes NOSPACES.TXT and RES_SYM.TXT

import os
import sys


class TokenType:
    KEYWORD = "KEYWORD"
    IDENTIFIER = "IDENTIFIER"
    INTEGER = "INTEGER"
    DOUBLE = "DOUBLE"
    STRING = "STRING"
    SYMBOL = "SYMBOL"
    UNKNOWN = "UNKNOWN"
    EOF = "EOF"


RESERVED_WORDS = ["integer", "double", "output", "if"]

# check these first so := doesn't become : and =
TWO_CHAR_SYMBOLS = [":=", "==", "!=", "<<"]
ONE_CHAR_SYMBOLS = [":", ";", "=", "+", "-", "<", ">", "(", ")"]

# specs use curly quotes in output<<“hello”;
QUOTES = ['"', "“", "”"]


class Token:
    def __init__(self, token_type, value, line, column):
        self.type = token_type
        self.value = value
        self.line = line
        self.column = column

    def __repr__(self):
        return "Token(" + self.type + ", '" + self.value + "', L" + str(self.line) + ":C" + str(self.column) + ")"


class Lexer:
    def __init__(self, source_code):
        self.source_code = source_code
        self.position = 0
        self.line = 1
        self.column = 1

    def is_at_end(self):
        return self.position >= len(self.source_code)

    def peek(self, offset=0):
        index = self.position + offset
        if index < len(self.source_code):
            return self.source_code[index]
        return ""

    def advance(self):
        current_char = self.peek()
        self.position = self.position + 1

        if current_char == "\n":
            self.line = self.line + 1
            self.column = 1
        else:
            self.column = self.column + 1

        return current_char

    def skip_whitespace(self):
        while not self.is_at_end():
            current_char = self.peek()

            if current_char == " " or current_char == "\t" or current_char == "\r" or current_char == "\n":
                self.advance()

            # comments
            elif current_char == "#" or (current_char == "/" and self.peek(1) == "/"):
                while not self.is_at_end() and self.peek() != "\n":
                    self.advance()

            else:
                break

    def read_string(self):
        start_line = self.line
        start_column = self.column

        opening_quote = self.advance()

        if opening_quote == '"':
            closing_quotes = ['"']
        else:
            closing_quotes = QUOTES

        text = ""
        while not self.is_at_end() and self.peek() != "\n":
            if self.peek() in closing_quotes:
                self.advance()
                return Token(TokenType.STRING, text, start_line, start_column)

            text = text + self.advance()

        # no closing quote
        return Token(TokenType.UNKNOWN, text, start_line, start_column)

    def read_number(self):
        start_line = self.line
        start_column = self.column

        number = ""
        while self.peek().isdigit():
            number = number + self.advance()

        if self.peek() == "." and self.peek(1).isdigit():
            number = number + self.advance()
            while self.peek().isdigit():
                number = number + self.advance()
            return Token(TokenType.DOUBLE, number, start_line, start_column)

        return Token(TokenType.INTEGER, number, start_line, start_column)

    def read_word(self):
        start_line = self.line
        start_column = self.column

        word = ""
        while self.peek().isalnum() or self.peek() == "_":
            word = word + self.advance()

        # specs write "If" and "Output" sometimes
        if word.lower() in RESERVED_WORDS:
            return Token(TokenType.KEYWORD, word, start_line, start_column)
        else:
            return Token(TokenType.IDENTIFIER, word, start_line, start_column)

    def tokenize(self):
        tokens = []

        while True:
            self.skip_whitespace()
            if self.is_at_end():
                break

            current_char = self.peek()
            next_char = self.peek(1)
            start_line = self.line
            start_column = self.column

            if current_char in QUOTES:
                token = self.read_string()

            elif current_char.isdigit():
                token = self.read_number()

            elif current_char.isalpha() or current_char == "_":
                token = self.read_word()

            elif current_char + next_char in TWO_CHAR_SYMBOLS:
                self.advance()
                self.advance()
                token = Token(TokenType.SYMBOL, current_char + next_char, start_line, start_column)

            elif current_char in ONE_CHAR_SYMBOLS:
                self.advance()
                token = Token(TokenType.SYMBOL, current_char, start_line, start_column)

            else:
                self.advance()
                token = Token(TokenType.UNKNOWN, current_char, start_line, start_column)

            tokens.append(token)

        tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return tokens


def remove_spaces(source_code):
    result_lines = []

    for line in source_code.splitlines():
        line = line.replace(" ", "")
        line = line.replace("\t", "")
        if line != "":
            result_lines.append(line)

    return "\n".join(result_lines)


def build_res_sym(tokens):
    reserved_words_found = []
    symbols_found = []
    in_order = []

    for token in tokens:
        if token.type == TokenType.KEYWORD:
            word = token.value.lower()
            if word not in reserved_words_found:
                reserved_words_found.append(word)
            in_order.append(token)

        elif token.type == TokenType.SYMBOL:
            if token.value not in symbols_found:
                symbols_found.append(token.value)
            in_order.append(token)

    lines = []
    lines.append("==================================================")
    lines.append("          HLInt - RESERVED WORDS & SYMBOLS        ")
    lines.append("==================================================")
    lines.append("")

    lines.append("RESERVED WORDS FOUND:")
    if len(reserved_words_found) == 0:
        lines.append("  (None)")
    for word in sorted(reserved_words_found):
        lines.append("  - " + word)
    lines.append("")

    lines.append("SYMBOLS FOUND:")
    if len(symbols_found) == 0:
        lines.append("  (None)")
    for symbol in sorted(symbols_found):
        lines.append("  - " + symbol)
    lines.append("")

    lines.append("EXTRACTED IN ORDER OF OCCURRENCE:")
    for token in in_order:
        if token.type == TokenType.KEYWORD:
            kind = "RESERVED WORD"
        else:
            kind = "SYMBOL"

        line_number = str(token.line).rjust(2)
        column_number = str(token.column).rjust(2)
        kind = kind.ljust(13)

        lines.append("  Line " + line_number + " | Col " + column_number + " | [" + kind + "] " + token.value)
    lines.append("")

    return "\n".join(lines)


def write_file(path, text):
    with open(path, "w", encoding="utf-8") as file:
        file.write(text)


def process_source_file(file_path, output_dir="outputs"):
    if not os.path.exists(file_path):
        raise FileNotFoundError("Source file not found: " + file_path)

    with open(file_path, "r", encoding="utf-8") as file:
        source_code = file.read()

    os.makedirs(output_dir, exist_ok=True)

    no_spaces = remove_spaces(source_code)
    write_file(os.path.join(output_dir, "NOSPACES.TXT"), no_spaces)

    lexer = Lexer(source_code)
    tokens = lexer.tokenize()
    res_sym = build_res_sym(tokens)
    write_file(os.path.join(output_dir, "RES_SYM.TXT"), res_sym)

    return source_code, tokens


# for testing: python3 src/lexer.py test_programs/PROG1.HL
if __name__ == "__main__":
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        path = "test_programs/PROG1.HL"

    try:
        source_code, tokens = process_source_file(path)
    except FileNotFoundError as error:
        print(error)
        sys.exit(1)

    print("Wrote outputs/NOSPACES.TXT and outputs/RES_SYM.TXT")
    print()
    print("Tokens found:")
    for token in tokens:
        if token.type != TokenType.EOF:
            print(token)
