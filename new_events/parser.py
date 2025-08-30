from lark import Lark

# 1. The grammar we defined in Step 2.
basic_grammar = r"""
    // The 'start' rule is the entry point. A program is one or more lines.
    ?start: line+

    // A line can be a label definition, or a statement followed by a newline.
    // We use a general 'line' rule to handle the structure of the code.
    ?line: (statement | label) _NL+

    // A label is a name followed by a colon. e.g., "yay:"
    label: CNAME ":"

    ?statement: let_statement
              | if_statement
              | print_statement
              | goto_statement
              | return_statement

    // --- Statement Definitions ---

    let_statement: "let" CNAME "=" expression      // e.g., let myVar = 1
    print_statement: "print" expression          // e.g., print "Hello"
    goto_statement: "goto" CNAME                 // e.g., goto end
    return_statement: "return"                   // e.g., return

    // The 'if' statement requires a condition and a statement to execute.
    if_statement: "if" condition "then" goto_statement

    // --- Expressions and Conditions ---

    // A condition compares two expressions.
    condition: expression "==" expression

    // An expression is a simple value for now.
    ?expression: value

    // A value can be a number, a string, or a variable name.
    ?value: SIGNED_NUMBER
          | ESCAPED_STRING
          | CNAME

    // --- Terminals and Imports ---

    // Import common terminal rules from the Lark library.
    // CNAME is for identifiers (variables, labels).
    // ESCAPED_STRING handles quoted strings.
    // SIGNED_NUMBER handles integers and floats.

    %import common.CNAME
    %import common.ESCAPED_STRING
    %import common.SIGNED_NUMBER
    %import common.WS
    %import common.NEWLINE -> _NL
    %ignore WS
"""

# 2. Your example BASIC-like code.
# Note: I added a newline at the end, which the grammar expects.
code_to_parse = """
let myVar = 1
if myVar == 1 then goto yay
print "How did that happen?"
goto end

yay:
print "This was great!"

end:
return

"""


def main():
    # 3. Create the parser instance.
    # The 'start' argument tells Lark which rule to begin parsing with.
    basic_parser = Lark(basic_grammar, start='start')

    # 4. Parse the code!
    try:
        parse_tree = basic_parser.parse(code_to_parse)
        # The .pretty() method gives a nice, indented view of the tree.
        print(parse_tree.pretty())
    except Exception as e:
        print(f"Error parsing code: {e}")


if __name__ == '__main__':
    main()
