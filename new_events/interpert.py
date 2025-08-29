from lark import Interpreter

class BasicInterpreter(Interpreter):
    def __init__(self):
        self.vars = {} # A dictionary to store variable values

    def let_statement(self, tree):
        var_name = tree.children[0].value
        # We need to resolve the expression's value.
        # This would require a more complex 'visit' call.
        # For a simple value, we can just get it.
        value = tree.children[1].children[0].children[0].value
        
        # Convert to number if possible
        try:
            value = int(value)
        except (ValueError, TypeError):
            # It's a string or something else, leave it
            pass
            
        self.vars[var_name] = value
        print(f"Set variable '{var_name}' to {value}")

    def print_statement(self, tree):
        # This also needs to be smarter to handle variables vs. literals
        val_node = tree.children[0].children[0]
        if val_node.data == 'value':
            token = val_node.children[0]
            if token.type == 'CNAME':
                # It's a variable, look it up
                var_name = token.value
                print(self.vars.get(var_name, "NULL")) # Print NULL if not found
            else:
                # It's a literal string or number
                print(token.value.strip('"')) # Strip quotes from strings

# --- In your main script, after parsing ---
# parse_tree = basic_parser.parse(code_to_parse)
# interpreter = BasicInterpreter()
# interpreter.visit(parse_tree)
# print("Final variables:", interpreter.vars)