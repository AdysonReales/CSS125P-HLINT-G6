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


# -------------------------------------------------------- semantic check
# works out the type of every expression, and makes sure variables are
# declared once, before they are used

def expression_type(expression, declared):
    kind = expression[0]

    if kind == "number":
        return expression[3]

    if kind == "var":
        name = expression[2]
        if name not in declared:
            raise HLError("variable '" + expression[1].value + "' is not declared", expression[1])
        return declared[name]

    left_type = expression_type(expression[3], declared)
    right_type = expression_type(expression[4], declared)
    if left_type == DOUBLE or right_type == DOUBLE:
        return DOUBLE
    return INTEGER


def check_statement(statement, declared):
    kind = statement[0]

    if kind == "declare":
        name = statement[2]
        if name in declared:
            raise HLError("variable '" + statement[1].value + "' is already declared", statement[1])
        declared[name] = statement[3]

    elif kind == "assign":
        name = statement[2]
        if name not in declared:
            raise HLError("variable '" + statement[1].value + "' is not declared", statement[1])
        value_type = expression_type(statement[3], declared)
        if declared[name] == INTEGER and value_type == DOUBLE:
            raise HLError("cannot assign a double value to integer variable '" + statement[1].value + "'", statement[1])

    elif kind == "output":
        if not isinstance(statement[2], str):
            expression_type(statement[2], declared)

    elif kind == "if":
        expression_type(statement[2], declared)
        expression_type(statement[4], declared)
        check_statement(statement[5], declared)


def check_program(statements):
    declared = {}
    for statement in statements:
        check_statement(statement, declared)
    return declared


# ---------------------------------------------------------------- engine

def format_value(value):
    # doubles are shown with a precision of 2
    if isinstance(value, float):
        return "{:.2f}".format(value)
    return str(value)


def evaluate(expression, variables):
    kind = expression[0]

    if kind == "number":
        return expression[2]

    if kind == "var":
        value = variables[expression[2]][1]
        if value is None:
            raise HLError("variable '" + expression[1].value + "' has no value yet", expression[1])
        return value

    left = evaluate(expression[3], variables)
    right = evaluate(expression[4], variables)
    if expression[2] == "+":
        return left + right
    return left - right


def compare(left, operator, right):
    if operator == "<":
        return left < right
    if operator == ">":
        return left > right
    if operator == "==":
        return left == right
    return left != right


def run_statement(statement, variables, output_lines):
    kind = statement[0]

    if kind == "declare":
        variables[statement[2]] = [statement[3], None]

    elif kind == "assign":
        variable = variables[statement[2]]
        value = evaluate(statement[3], variables)
        if variable[0] == DOUBLE:
            value = round(float(value), 2)
        variable[1] = value

    elif kind == "output":
        if isinstance(statement[2], str):
            output_lines.append(statement[2])
        else:
            output_lines.append(format_value(evaluate(statement[2], variables)))

    elif kind == "if":
        left = evaluate(statement[2], variables)
        right = evaluate(statement[4], variables)
        if compare(left, statement[3], right):
            run_statement(statement[5], variables, output_lines)


def run_statement_list(statements, variables, output_lines):
    for statement in statements:
        run_statement(statement, variables, output_lines)


# ----------------------------------------------------------- entry point

def interpret(tokens):
    """Prints ERROR or NO ERROR(S) FOUND, then the program output.
    Returns True when there was no error."""
    try:
        statements = Parser(tokens).parse_program()
        check_program(statements)
    except HLError as error:
        print("ERROR")
        print("  Line " + str(error.line) + ", Col " + str(error.column) + ": " + error.message)
        return False

    print("NO ERROR(S) FOUND")

    # a variable used before it has a value can only be seen while running,
    # so the lines printed before that point are still shown
    output_lines = []
    try:
        run_statement_list(statements, {}, output_lines)
        failed = None
    except HLError as error:
        failed = error

    for line in output_lines:
        print(line)

    if failed is not None:
        print("RUNTIME ERROR")
        print("  Line " + str(failed.line) + ", Col " + str(failed.column) + ": " + failed.message)
        return False

    return True
