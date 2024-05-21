from typing import Callable
import os

def stitch_in(str: str, start: int, end: int, stitch_in: str) -> str:
    if start < 0: raise ValueError("start must be greater than or equal to 0.")
    if end > len(str): raise ValueError("end must be less than or equal to length of template string.")
    if start > end: raise ValueError("Start can not be larger than end.")

    left_str = str[ :start]
    right_str = str[end: ]
    return left_str + stitch_in + right_str

class operation:
    key: str
    importance: int
    gather_values_func: Callable[..., list[float]]
    math_func: Callable[..., float]

    def __init__(self, key, importance, gather_values_func, math_func):
        self.key = key
        self.importance = importance
        self.gather_values_func = gather_values_func
        self.math_func = math_func

#region COMMANDS
def clear_console():
    os.system('cls')
    return ''

def echo(*input: str):
    return f"Echoing message: ({" | ".join(input)})"

def help():
    return "This is the help function...not much here yet."
#endregion

#region Math Functions
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
    ...

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

class Calculator:
    commands: dict[str, Callable[..., str]]     # Probaly is static but is a keyword followed by the function to run with it
    functions: dict[str, Callable[..., str]]    # A list of all functions
    operations: list[operation]
    variables: dict[str, str]                  # Dictionary of name for variable and the value to replace it with
    past_equations: list[tuple[str, str]]       # A list of two strings: input & output
    special_conditions: dict[str, any]          # Not sure if this is neccesary but holds any special conditions that dont fit anywhere else in a dictionary by name and value

    def __init__(self):
        self.past_equations = [ ]
        self.special_conditions = { }
        self.variables = { 
            "ans" : "0",
            "pi" : "3.1415926",
            "e" : "1.618"
        }
        self.commands = {
            "help": help,
            "echo": echo,
            "clear": clear_console
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
            # "|": (in_between, lambda x: abs(x))
        ]

    #region Object Specific Functions
    def solve(self, equation: str) -> str:
        operator_index, operation = find_next_operator(self, equation)
        # print(f"operator index @ solve: {operator_index} | equation = {equation}")
        if (operation == None):
            return equation

        math_func: Callable[..., float] = operation.math_func
        values_func: Callable[..., list[float]] = operation.gather_values_func
        values, bounds = values_func(equation, operator_index)

        result = str(math_func(*values))
        # print(f"before end: ({bounds[0]}, {bounds[1]}) was {equation[bounds[0]:bounds[1]]} but now is {result} | whole start: {equation} turned to {stitch_in(equation, bounds[0], bounds[1], result)}")
        return self.solve(stitch_in(equation, bounds[0], bounds[1], result))
    
    def run(self, input: str) -> str:
        input = input.replace(" ", "")
        if (cmd_output := was_command(self, input)) is not None:
            return cmd_output
        
        input = replace_vars(self, input)
        # print(f"formatted equation: {input}")
        return self.solve(input)

    def add_var(self, new_var: tuple[str, str]) -> None:
        self.variables[new_var[0]] = new_var[1]
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

def was_command(self: Calculator, input: str) -> str | None:
    if len((vars := tuple(input.split(":")))) > 1:
        self.add_var(vars)
        return f"Added variable '{vars[0]}' with value '{vars[1]}'"
    else:
        if (param_start := input.find("[")) != -1:
            parameters: list[str] = input[param_start + 1 : input.find("]")].split(",") # list of all values split by a comma within the brackets
            input = input[ :param_start] #Set input to be just the command
        else:
            parameters = None

        for cmd in self.commands:
            if input == cmd:
                if parameters is not None:
                    return self.commands[cmd](parameters)
                else:
                    return self.commands[cmd]()
            
    return None

def find_next_operator(self: Calculator, equation: str) -> tuple[int, operation]:
    current_operation = (-1, None)
    for i in range(0 if equation[0] != '-' else 1, len(equation)):
        for operator in self.operations:
            if equation[i:i+len(operator.key)] == operator.key:
                if (current_operation[1] is None or operator.importance > current_operation[1].importance):
                    current_operation = (i, operator)
                break
    
    return current_operation
#endregion