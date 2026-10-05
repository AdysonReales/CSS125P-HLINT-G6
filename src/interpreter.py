# interpreter.py - checks the syntax of the tokens, then runs the program
#
# Grammar (keywords and variable names are not case sensitive):
#   program     -> statement* EOF
#   statement   -> declaration | assignment | output | if
#   declaration -> IDENT ":" ("integer" | "double") ";"
#   assignment  -> IDENT (":=" | "=") expression ";"
#   output      -> "output" "<<" (STRING | expression) ";"
#   if          -> "if" "(" expression RELOP expression ")" statement
#   expression  -> term (("+" | "-") term)*
#   term        -> INTEGER | DOUBLE | IDENT | "(" expression ")"
#   RELOP       -> "<" | ">" | "==" | "!="

from lexer import TokenType

INTEGER = "integer"
DOUBLE = "double"

RELATIONAL_OPERATORS = ["<", ">", "==", "!="]


class HLError(Exception):
    def __init__(self, message, token):
        Exception.__init__(self, message)
        self.message = message
        self.line = token.line
        self.column = token.column


# ---------------------------------------------------------------- parser
# each statement becomes a tuple with the token it started at, so errors
# found later can still point to a line and column
#   ("declare", token, name, type)
#   ("assign", token, name, expression)
#   ("output", token, string_or_expression)
#   ("if", token, left, operator, right, statement)
# expressions are
#   ("number", token, value, type)  ("var", token, name)
#   ("binary", token, operator, left, right)

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.position = 0

    def current(self):
        return self.tokens[self.position]

    def advance(self):
        token = self.current()
        if token.type != TokenType.EOF:
            self.position = self.position + 1
        return token

    def is_symbol(self, value):
        token = self.current()
        return token.type == TokenType.SYMBOL and token.value == value

    def is_keyword(self, word):
        token = self.current()
        return token.type == TokenType.KEYWORD and token.value.lower() == word

    def describe(self, token):
        if token.type == TokenType.EOF:
            return "end of file"
        return "'" + token.value + "'"

    def expect_symbol(self, value):
        if not self.is_symbol(value):
            raise HLError("expected '" + value + "' but found " + self.describe(self.current()), self.current())
        return self.advance()

    def parse_program(self):
        statements = []
        while self.current().type != TokenType.EOF:
            statements.append(self.parse_statement(True))
        return statements

    def parse_statement(self, allow_declaration):
        token = self.current()

        if token.type == TokenType.IDENTIFIER:
            following = self.tokens[self.position + 1]
            if following.type == TokenType.SYMBOL and following.value == ":":
                if not allow_declaration:
                    raise HLError("a declaration is not allowed here", token)
                return self.parse_declaration()
            return self.parse_assignment()

        if self.is_keyword("output"):
            return self.parse_output()

        if self.is_keyword("if"):
            return self.parse_if()

        raise HLError("unexpected " + self.describe(token), token)

    def parse_declaration(self):
        name_token = self.advance()
        self.expect_symbol(":")

        type_token = self.current()
        if not (self.is_keyword(INTEGER) or self.is_keyword(DOUBLE)):
            raise HLError("expected 'integer' or 'double' but found " + self.describe(type_token), type_token)
        self.advance()
        self.expect_symbol(";")

        return ("declare", name_token, name_token.value.lower(), type_token.value.lower())

    def parse_assignment(self):
        name_token = self.advance()

        if self.is_symbol(":=") or self.is_symbol("="):
            self.advance()
        else:
            raise HLError("expected ':=' but found " + self.describe(self.current()), self.current())

        value = self.parse_expression()
        self.expect_symbol(";")
        return ("assign", name_token, name_token.value.lower(), value)

    def parse_output(self):
        output_token = self.advance()
        self.expect_symbol("<<")

        if self.current().type == TokenType.STRING:
            value = self.advance().value
        else:
            value = self.parse_expression()

        self.expect_symbol(";")
        return ("output", output_token, value)

    def parse_if(self):
        if_token = self.advance()
        self.expect_symbol("(")

        left = self.parse_expression()

        operator_token = self.current()
        if operator_token.type == TokenType.SYMBOL and operator_token.value in RELATIONAL_OPERATORS:
            self.advance()
        else:
            raise HLError("expected one of < > == != but found " + self.describe(operator_token), operator_token)

        right = self.parse_expression()
        self.expect_symbol(")")

        statement = self.parse_statement(False)
        return ("if", if_token, left, operator_token.value, right, statement)

    def parse_expression(self):
        left = self.parse_term()

        while self.is_symbol("+") or self.is_symbol("-"):
            operator_token = self.advance()
            right = self.parse_term()
            left = ("binary", operator_token, operator_token.value, left, right)

        return left

    def parse_term(self):
        token = self.current()

        if token.type == TokenType.INTEGER:
            self.advance()
            return ("number", token, int(token.value), INTEGER)

        if token.type == TokenType.DOUBLE:
            self.advance()
            return ("number", token, float(token.value), DOUBLE)

        if token.type == TokenType.IDENTIFIER:
            self.advance()
            return ("var", token, token.value.lower())

        if self.is_symbol("("):
            self.advance()
            inner = self.parse_expression()
            self.expect_symbol(")")
            return inner

        raise HLError("expected a value but found " + self.describe(token), token)
