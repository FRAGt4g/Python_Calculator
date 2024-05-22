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
    special_conditions: dict[str, any]          # Not sure if this is neccesary but holds any special conditions that dont fit anywhere else in a dictionary by name and value
    round_to: int                               # -1 means no auto rounding

    def __init__(self):
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
            "round_to": (set_auto_round, True)
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

    @staticmethod
    def static_solve(equation: str) -> str:
        operator_index, operation = find_next_operator(Calculator(), equation)
        # print(f"operator index @ solve: {operator_index} | equation = {equation}")
        if (operation == None):
            return equation

        math_func: Callable[..., float] = operation.math_func
        values_func = operation.gather_values_func
        values, bounds = values_func(equation, operator_index)

        result = str(math_func(*values))
        # print(f"before end: ({bounds[0]}, {bounds[1]}) was {equation[bounds[0]:bounds[1]]} but now is {result} | whole start: {equation} turned to {stitch_in(equation, bounds[0], bounds[1], result)}")
        return Calculator.static_solve(stitch_in(equation, bounds[0], bounds[1], result))

    #region Object Specific Functions
    def solve(self, equation: str, clean: bool = False) -> str:
        if clean:
            equation = equation.replace(" ", "")
            equation = replace_vars(self, equation)

        operator_index, operation = find_next_operator(self, equation)
        # print(f"operator index @ solve: {operator_index} | equation = {equation}")
        if (operation == None):
            return equation

        math_func: Callable[..., float] = operation.math_func
        values_func = operation.gather_values_func
        values, bounds = values_func(equation, operator_index)
        print("type: " + type(values)) 
        if type(values) == "str":
            result = str(math_func(self.solve(values)))
        else:
            result = str(math_func(*values))
        # print(f"before end: ({bounds[0]}, {bounds[1]}) was {equation[bounds[0]:bounds[1]]} but now is {result} | whole start: {equation} turned to {stitch_in(equation, bounds[0], bounds[1], result)}")
        return self.solve(stitch_in(equation, bounds[0], bounds[1], result))
    def solve_f(self, equation: str) -> float | None:
        try:
            return float(self.solve(equation))
        except ValueError as e:
            return None

    def run(self, input: str) -> str:
        input = input.replace(" ", "")
        if (cmd_output := was_command(self, input)) is not None:
            return cmd_output
        
        input = replace_vars(self, input)
        if (equations := is_inequality(self, input)) is not None:
            # print(f"is inequality: {equations}")
            return check_equality(self, *equations)

        return self.solve(input)
    #endregion

#region COMMANDS
def clear_console():
    os.system('cls')
    return ''

def help():
    return "This is the help function...not much here yet."

def set_auto_round(self: Calculator, input: int):
    self.round_to = input
    return f"Now will automatically round to {self.round_to} decimal places. You change it to round all digits by typing 'sigfigs: True'"

def add_variable(self: Calculator, input: str):
    var_name, var_value = input.split("=")

    if var_value is None: raise ValueError("Invalid syntax. Must have a '=' to assign a variable")

    self.variables[var_name] = self.solve(var_value, clean=True)
    return f"Added variable, '{var_name}' with a value of '{self.variables[var_name]}'"
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
        parameters = None

    for cmd in self.commands:
        if input == cmd:
            func, requires_calc_reference = self.commands[cmd]
            if requires_calc_reference: parameters.insert(0, self)
    
            if parameters is not None:
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