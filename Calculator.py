from typing import Callable
import os

class operation:
    key: str
    importance: int
    gather_values_func: Callable[..., tuple[tuple[float, float] | str, tuple[float, float]]]
    math_func: Callable[..., float]

    def __init__(self, key, importance, gather_values_func, math_func):
        self.key = key
        self.importance = importance
        self.gather_values_func = gather_values_func
        self.math_func = math_func
class Calculator:
    commands: dict[str, Callable[..., str]]     # Probaly is static but is a keyword followed by the function to run with it
    functions: dict[str, Callable[..., str]]    # A list of all functions
    operations: list[operation]
    variables: dict[str, str]                   # Dictionary of name for variable and the value to replace it with
    past_equations: list[tuple[str, str]]       # A list of two strings: input & output
    round_to: int                               # -1 means no auto rounding
    use_sigfigs: bool
    more_info: dict[str, dict[str, str]]

    def __init__(self):
        self.more_info = {
            "commands": {
                "var": "Adds or assigns to an existing variable with a number that can be used in equations.",
                "help": "Prints a menu with all important information to get started using this calcualator.",
                "clear": "Clears the console. Does not delete history of variables",
                "round_to": "Sets the ammount to round answers to.",
                "history": "Prints all past inputs and results",
                "info": "Prints all data for this specific calculator object",
                "sigfigs": "Enables/Disables whether to follow sigfigs."
            },
            "functions": {
                "avg": "Get the average of all te values",
                "sum": "Find the total of all values inside added up.",
                "mean": "Find the mean of any number of values."
            },
            "operations": {
                "+": "Addition",
                "-": "Subtraction",
                "*": "Multiplication. Do not need to include a '*' before parenthesis.",
                "/": "Division",
                "^": "Exponential; will take the left side and raise it to the power of the right.",
                "%": "Modulo operation; will output the remainder of a division of the two values. (ex: 3 % 5 is 3 or 5 % 3 is 2)",
                "|": "Absolute value; will always return the positive equivallent of the input. (ex: |-5| is 5 and |5| is 5)"
            }
        }
        self.past_equations = [ ]
        self.special_conditions = { }
        self.variables = { 
            "ans" : "0",
            "pi" : "3.1415926",
            "e" : "1.618"
        }
        self.commands = {
            "var": (add_variable, True),
            "help": (help, False),
            "clear": (clear_console, False),
            "round_to": (set_auto_round, True),
            "history": (print_history, True),
            "info": (print_info, True),
            "sigfigs": (set_sigfigs, True)
        }
        self.functions = {
            "avg" : average,
            "sum" : sum,
            "mean" : mean
        }
        self.operations = [
            operation("+", 1, two_around, lambda x, y: x + y),
            operation("-", 1, two_around, lambda x, y: x - y),
            operation("*", 2, two_around, lambda x, y: x * y),
            operation("/", 2, two_around, lambda x, y: x / y),
            operation("^", 2, two_around, lambda x, y: x ** y),
            operation("%", 2, two_around, lambda x, y: x % y),
            operation("|", 3, in_between, lambda x: abs(x))
        ]
        self.round_to = -1
        self.use_sigfigs = False
        return
    
    def solve(self, equation: str, clean: bool = False) -> str:
        if clean: equation = replace_vars(self, equation.replace(" ", ""))

        operator_index, operation = find_next_operator(self, equation)
        if operation is None: return equation                           #Just a number

        math_func = operation.math_func
        values_func = operation.gather_values_func
        values, bounds = values_func(equation, operator_index) 
        
        if type(values) == "str": result = str(math_func(self.solve(values)))
        else: result = str(math_func(*values))
        
        return self.solve(stitch_in(equation, bounds[0], bounds[1], result))
    
    def solve_f(self, equation: str) -> float | None:
        try: return float(self.solve(equation))
        except ValueError: return None

    def run(self, input: str) -> str:
        input = input.replace(" ", "")
        if (cmd_output := was_command(self, input)) is not None:
            return cmd_output
        
        input = replace_vars(self, input)
        if (equations := is_inequality(self, input)) is not None: return check_equality(self, *equations)

        result: str = self.solve(input)
        self.update_vars(input, result)
        return result
    
    def update_vars(self, input: str, solved: str) -> None:
        self.past_equations.append(input)
        self.variables["ans"] = solved
        return

#region COMMANDS
def clear_console() -> str:
    os.system('cls')
    return ''

def help() -> str:
    return "This is the help function...not much here yet."

def set_auto_round(self: Calculator, input: int) -> str:
    self.round_to = input
    return f"Now will automatically round to {self.round_to} decimal places. You change it to round all digits by typing 'sigfigs: True'"

def add_variable(self: Calculator, input: str) -> str:
    var_name, var_value = input.split("=")

    if var_value is None: raise ValueError("Invalid syntax. Must have a '=' to assign a variable")

    self.variables[var_name] = self.solve(var_value, clean=True)
    print(f"variables: '{self.variables}'")
    return f"Added variable, '{var_name}' with a value of '{self.variables[var_name]}'"

def print_history(self: Calculator) -> str:
    return f"This is the history of all inputs: {self.past_equations}"

def print_info(self: Calculator) -> str:
    output: str = "CALCULATOR INFO:\n"

    output += "Variables:\n"
    for var in self.variables:
        output += f"   - {var}: {self.variables[var]}\n"

    output += "Commands:\n"
    for cmd in self.commands:
        output += f"   - {cmd}: {self.more_info["commands"][cmd]}\n"

    output += "Functions:\n"
    for func in self.functions:
        output += f"   - {func}: {self.more_info["functions"][func]}\n"
    
    output += "Operations:\n"
    for operation in self.operations:
        output += f"   - '{ operation.key }': {self.more_info["operations"][operation.key]}\n"

    output += f"Rounds to {self.round_to} {"places" if self.use_sigfigs else "decimal places"}."

    return output

def set_sigfigs(self: Calculator, value: str) -> str:
    if value.lower() == "true":
        self.use_sigfigs = True
        return "Enabled using significant figures for rounding."
    elif value.lower() == "false":
        self.use_sigfigs = False
        return "Disabled using significant figures for rounding."
    else:
        return "Incorrect assignment | not either 'true' or 'false'"


#endregion

#region parsing equation
def is_number_char(input: str) -> bool:
    return input.isdigit() or input == "." or input == '-'

def num_leftof(equation: str, index: int) -> float:
    i = index - 1
    while i >= 0 and is_number_char(equation[i]):
        if equation[i] == '-':
            i -= 1
            break
        i -= 1
    return (float(equation[i + 1:index]), i + 1)

def num_rightof(equation: str, index: int) -> tuple[float, int]:
    i = index + 1
    while i < len(equation) and is_number_char(equation[i]):
        if (equation[i] == '-' and i != index + 1): break
        i += 1
    return (float(equation[index + 1: i]), i)

def two_around(equation: str, index: int) -> tuple[tuple[float, float], tuple[int, int]]:
    left_value, start_index = num_leftof(equation, index)
    right_value, end_index = num_rightof(equation, index)
    return ((left_value, right_value), (start_index, end_index))

def in_between(equation: str, start_index: int) -> float:
    for i in range(start_index+1, len(equation)):
        if equation[i] == equation[start_index]:
            return equation[start_index+1:i]
    raise ValueError("Does not have enclosing wrapper.")

#endregion

#region Math Functions
def average(*args: float):
    return sum(args)/len(args)

def sum(*args: float):
    sum: float = 0
    for num in args: sum += num
    return sum

def mean(*args: float):
    index: int = len(args) / 2
    return args[index]
#endregion

#region HELPERS
def starts_with_var(self: Calculator, substr: str) -> str | None:
    for var in sorted(self.variables, key=len, reverse=True):
        if substr.startswith(var):
            return var
    return None

def replace_vars(self: Calculator, input: str) -> str:
    i: int = 0
    while (i < len(input)):
        if (variable := starts_with_var(self, input[i:])) is not None:
            input = input[0:i] + self.variables[variable] + input[i+len(variable):]
        # elif input[i] == '-' and input[i-1] != '~':
        #     input = input[0:i] + '~' + input[i+1:]
        i += 1
    return input

def find_next_operator(self: Calculator, equation: str) -> tuple[int, operation]:
    print(f"NEW NEW NEW Input: '{equation}'")
    current_operation = (-1, None)
    start_index = 0 if equation[0] != '-' else 1
    for i in range(start_index, len(equation)):
        print(f"i: {i} | len: {len(equation)}")
        for operator in self.operations:
            if i+len(operator.key) < len(equation) and equation[i:i+len(operator.key)] == operator.key:
                if (current_operation[1] is None or operator.importance > current_operation[1].importance):
                    current_operation = (i, operator)
                break

    return current_operation

def stitch_in(str: str, start: int, end: int, stitch_in: str) -> str:
    if start < 0: raise ValueError("start must be greater than or equal to 0.")
    if end > len(str): raise ValueError("end must be less than or equal to length of template string.")
    if start > end: raise ValueError("Start can not be larger than end.")

    left_str = str[ :start]
    right_str = str[end: ]
    return left_str + stitch_in + right_str
#endregion

def was_command(self: Calculator, input: str) -> str | None:
    if (param_start := input.find(":")) != -1:
        parameters: list[str] = input[param_start + 1: ].split(",") # list of all values split by a comma within the brackets
        input = input[ :param_start] #Set input to be just the command
    else:
        parameters = [ ]

    for cmd in self.commands:
        if input == cmd:
            func, requires_calc_reference = self.commands[cmd]
            if requires_calc_reference: parameters.insert(0, self)
    
            if len(parameters) != 0:
                return func(*parameters)
            else:
                return func()
        
    return None

def is_inequality(self: Calculator, input: str) -> tuple[str, str, str] | None:
    equal = input.find("=")
    greater = input.find(">")
    less = input.find("<")

    if equal != -1:
        if greater == equal - 1:
            return (input[ :greater], input[equal+1: ], "greater or equal")
        elif less == equal - 1:
            return (input[ :less], input[equal+1: ], "less or equal")
        elif input[equal+1] == '=':
            return (input[ :equal], input[equal+2: ], "equal")
        else:
            raise ValueError("Should not be possible. Misstyped")
    elif greater != -1:
        return (input[ :greater], input[greater+1: ], "greater")
    elif greater != -1:
        return (input[ :less], input[less+1: ], "less")

    return None

def check_equality(self: Calculator, left_equation: str, right_equation: str, equality_check: str) -> str:
    match equality_check:
        case "equal":
            if (left_solve := self.solve_f(left_equation)) == (right_solve := self.solve_f(right_equation)):
                return f"Correct. Results: (left: {left_solve}, right: {right_solve})"
            else:
                return f"Incorrect. Results: (left: {left_solve}, right: {right_solve})"
        case "greater":
            if (left_solve := self.solve_f(left_equation)) > (right_solve := self.solve_f(right_equation)):
                return f"Correct. Results: (left: {left_solve}, right: {right_solve})"
            else:
                return f"Incorrect. Results: (left: {left_solve}, right: {right_solve})"
        case "less":
            if (left_solve := self.solve_f(left_equation)) < (right_solve := self.solve_f(right_equation)):
                return f"Correct. Results: (left: {left_solve}, right: {right_solve})"
            else:
                return f"Incorrect. Results: (left: {left_solve}, right: {right_solve})"
        case "greater or equal":
            if (left_solve := self.solve_f(left_equation)) >= (right_solve := self.solve_f(right_equation)):
                return f"Correct. Results: (left: {left_solve}, right: {right_solve})"
            else:
                return f"Incorrect. Results: (left: {left_solve}, right: {right_solve})"
        case "less or equal":
            if (left_solve := self.solve_f(left_equation)) <= (right_solve := self.solve_f(right_equation)):
                return f"Correct. Results: (left: {left_solve}, right: {right_solve})"
            else:
                return f"Incorrect. Results: (left: {left_solve}, right: {right_solve})"
        case _:
            raise ValueError("Invalid equality check value. Please have it be greater, less, equal or some combination.")