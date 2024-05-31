from typing import Callable, Tuple
import os


#region Types
Bounds = Tuple[int, int]
MathValue = str | Tuple[float, float] | list[float]
MathInputs = Tuple[MathValue, Bounds]
MathFunction = Callable[[MathValue], str]

GrabFunction = Callable[[str, int], MathInputs]
CommandFunction = Callable[[str], str] | Callable[[], str]
#endregion

class operation:
    key: str
    importance: int
    gather_values_func: GrabFunction
    math_func: MathFunction

    def __init__(self, key: str, importance: int, gather_values_func: GrabFunction, math_func: MathFunction):
        self.key = key
        self.importance = importance
        self.gather_values_func = gather_values_func
        self.math_func = lambda values: str(math_func(values))
    
    @staticmethod
    def MathFunction(key: str, function: MathFunction):
        return operation(key, 99, in_between("[", "]", len(key)), function)


class Calculator:
    commands: dict[str, CommandFunction]     # Probaly is static but is a keyword followed by the function to run with it
    operations: list[operation]
    variables: dict[str, str]                   # Dictionary of name for variable and the value to replace it with
    past_equations: list[tuple[str, str]]       # A list of two strings: input & output
    round_to: int                               # -1 means no auto rounding
    use_sigfigs: bool
    more_info: dict[str, dict[str, str]]

    def __init__(self):
        self.past_equations = [ ]
        self.special_conditions = { }
        self.use_sigfigs = False
        self.round_to = -1

        self.more_info = {
            "commands": {
                "var": "Adds or assigns to an existing variable with a number that can be used in equations.",
                "help": "Prints a menu with all important information to get started using this calcualator.",
                "clear": "Clears the console. Does not delete history of variables",
                "round": "Sets the ammount to round answers to.",
                "history": "Prints all past inputs and results",
                "info": "Prints all data for this specific calculator object",
                "sigfigs": "Enables/Disables whether to follow sigfigs."
            },
            "operations": {
                "+": "Addition",
                "-": "Subtraction",
                "*": "Multiplication. Do not need to include a '*' before parenthesis.",
                "/": "Division",
                "^": "Exponential; will take the left side and raise it to the power of the right.",
                "%": "Modulo operation; will output the remainder of a division of the two values. (ex: 3 % 5 is 3 or 5 % 3 is 2)",
                "|": "Absolute value; will always return the positive equivallent of the input. (ex: |-5| is 5 and |5| is 5)",
                "!": "Factorial; returns all integers beneath it until 1 multiplied together. (ex: 4! = 4*3*2*1 and 1! = 1)",
                "?": "Summorial; returns all integers beneath it until 1 added together. (ex: 4? = 4+3+2+1 and 1! = 1)",
                "avg": "Returns the average of all the values put in. (ex: avg(1, 2, 3, 4, 5) = 3)",
                "median": "Returns the median of the values put in. (ex: median(1, 2, 10-3, 4, 5) = 7)",
                "sum": "Returns the sum of all the values put in. (ex: sum(1, 2, 3, 4, 5) = 15)",
            }
        }
        self.variables = { 
            "ans" : "0",
            "pi" : "3.1415926",
            "e" : "2.718281828"
        }
        self.commands = {
            "var": self.make_command("var"),
            "function": self.make_command("function"),
            "help": self.make_command("help"),
            "clear": self.make_command("clear"),
            "round": self.make_command("round"),
            "history": self.make_command("history"),
            "info": self.make_command("info"),
            "sigfigs": self.make_command("sigfigs")
        }
        self.operations = [
            operation("+", 1, two_around, lambda values: values[0] + values[1]),
            operation("-", 1, two_around, lambda values: values[0] - values[1]),
            operation("*", 2, two_around, lambda values: values[0] * values[1]),
            operation("/", 2, two_around, lambda values: values[0] / values[1]),
            operation("%", 2, two_around, lambda values: values[0] % values[1]),
            operation("^", 2, two_around, lambda values: values[0] ** values[1]),
            operation("!", 3, left_of, factorial),
            operation("?", 3, left_of, summorial),
            operation("|", 99, in_between("|", "|"), abs),
            operation("(", 100, in_between("(", ")"), lambda x: x[0]),
            operation.MathFunction("median", median),
            operation.MathFunction("avg", average),
            operation.MathFunction("sum", sum),
        ]
        return

    def add(self, values: list[float]) -> float:
        print("values: ", values)
        print("result: ", values[0] + values[1])
        return values[0] + values[1]

    def run_math_func(self, math_func: MathFunction, value: MathValue) -> str:
        if type(value) is str:
            print("is string")
            val_arr = seperate_arguments(value)
            # if len((val_arr := seperate_arguments(value))) == 1: 
            #     print("no args")
            #     return math_func(self.solve(value))
            
            arguments = [float(self.solve(value)) for value in val_arr]
            print("VAL ARR: ", val_arr)
            print("inputs: ", arguments, type(arguments[0]))
            x = math_func(arguments)
            print("math result: ", x)
            return x

        if type(value) is float or type(value) is int: return math_func(value)
        
        return math_func(value)

    def solve(self, equation: str, clean: bool = False) -> str:
        if clean: equation = replace_vars(self, equation.replace(" ", ""))

        operator_index, operation = find_next_operator(self, equation)
        if operation is None: return equation

        math_func = operation.math_func
        values_func = operation.gather_values_func
        values, bounds = values_func(equation, operator_index)
        print(f"values: {values}, bounds: {bounds}")
        result = self.run_math_func(math_func, values)
        print("done with math func")

        return self.solve(stitch_in(equation, bounds[0], bounds[1], result))
    
    def solve_f(self, equation: str) -> float | None:
        try: return float(self.solve(equation))
        except ValueError: return None

    def run(self, input: str, safe: bool = True) -> str:
        input = input.replace(" ", "")
        result: str = str()

        if safe:
            try:
                if (cmd_output := was_command(self, input)) is not None:
                    return cmd_output
                
                input = replace_vars(self, input)
                input = append_multipliers(self, input)
                if (equations := is_inequality(self, input)) is not None: return check_equality(self, *equations)

                result = self.solve(input)
                self.update_vars(input, result)
                return self.round(result)
            except Exception as e:
                return "Invalid input." 
        else:
            if (cmd_output := was_command(self, input)) is not None:
                return cmd_output
            
            input = replace_vars(self, input)
            input = append_multipliers(self, input)
            if (equations := is_inequality(self, input)) is not None: return check_equality(self, *equations)

            result = self.solve(input)
            self.update_vars(input, result)
            return self.round(result)

    def update_vars(self, input: str, solved: str) -> None:
        self.past_equations.append((input, solved))
        self.variables["ans"] = solved
        return

    def round(self, input: str) -> str:
        if self.round_to == -1: 
            return input

        try: 
            number = float(input)
        except ValueError: 
            return input
        
        return  f"{number:.{self.round_to}{"g" if self.use_sigfigs else "f"}}"

    def make_command(self, command: str) -> CommandFunction:
        match command:
            case "clear":
                def clear_console() -> str:
                    os.system('cls')
                    return ''
                return clear_console
            case "help":
                def help() -> str:
                    return "This is the help function...not much here yet."
                return help
            case "round":
                def set_auto_round(self, input: str) -> str:
                    if (input.lower() == "false" or input.lower() == "off"):
                        self.round_to = -1
                    else: 
                        self.round_to = max(int(input), -1)
                    return f"Now will automatically round to {self.round_to} decimal places. You change it to round all digits by typing 'sigfigs: True'"
                return lambda input: set_auto_round(self, input)
            case "var":
                def add_variable(self, input: str) -> str:
                    var_name, var_value = input.split("=")

                    if var_value is None: raise ValueError("Invalid syntax. Must have a '=' to assign a variable")

                    self.variables[var_name] = self.solve(var_value, clean=True)
                    print(f"variables: '{self.variables}'")
                    return f"Added variable, '{var_name}' with a value of '{self.variables[var_name]}'"
                return lambda input: add_variable(self, input)
            case "function":
                def init_new_function(self, input: str) -> str:
                    func_name, func_body = input.split("=")
                    variables = func_name[func_name.find("[")+1:func_name.find("]")].split(",")
                    func_name = func_name[:func_name.find("[")]
                    func_body = append_multipliers(self, func_body)
                    print("func body: ", func_body)
                    if func_body is None: raise ValueError("Invalid syntax. Must have a '=' to assign a function")
                    if func_name in self.more_info["operations"]: raise ValueError(f"Function '{func_name}' already exists")
                    self.more_info["operations"][func_name] = func_body

                    def new_function(function_body: str, args: list[float]) -> str:
                        print(f"calling! args = '{args}' | args[0] = '{args[0]}' | type = '{type(args[0])}'")
                        for index, arg in enumerate(args):
                            try: 
                                variable = variables[index]
                            except IndexError:
                                raise ValueError(f"Too many arguments for function '{func_name}'")
                            print("calling new function!", arg, function_body, variable)
                            function_body = function_body.replace(variable, str(arg))
                        
                        print(f"final result: {function_body}")
                        return function_body
                    
                    self.operations.append(operation.MathFunction(func_name, lambda *args: new_function(func_body, *args)))

                    return f"Added function, '{func_name}' with a body of '{func_body}'"
                return lambda input: init_new_function(self, input)
            case "history":
                def print_history(self: Calculator) -> str:
                    return f"This is the history of all inputs: {self.past_equations}"
                return lambda: print_history(self)
            case "info":
                def print_info(self) -> str:
                    output: str = "CALCULATOR INFO:\n"

                    output += "Variables:\n"
                    for var in self.variables:
                        output += f"   - {var}: {self.variables[var]}\n"

                    output += "Commands:\n"
                    for cmd in self.commands:
                        try: 
                            output += f"   - {cmd}: {self.more_info["commands"][cmd]}\n"
                        except KeyError:
                            output += f"   - '{ cmd }': No info provided.\n"

                    output += "Operations:\n"
                    for operation in self.operations:
                        try:
                            output += f"   - '{ operation.key }': {self.more_info["operations"][operation.key]}\n"
                        except KeyError:
                            output += f"   - '{ operation.key }': No info provided.\n"
                    
                    output += f"Rounds to {self.round_to} {"places" if self.use_sigfigs else "decimal places"}."

                    return output
                return lambda: print_info(self)
            case "sigfigs":
                def set_sigfigs(self, value: str) -> str:
                    if value.lower() == "true":
                        self.use_sigfigs = True
                        return "Enabled using significant figures for rounding."
                    elif value.lower() == "false":
                        self.use_sigfigs = False
                        return "Disabled using significant figures for rounding."
                    else:
                        return "Incorrect assignment | not either 'true' or 'false'"
                return lambda value: set_sigfigs(self, value)
        
        raise ValueError(f"Invalid command '{command}'")
#endregion

#region parsing equation
def is_number_char(input: str) -> bool:
    return input.isdigit() or input == "." or input == '-'

def is_operation(self: Calculator, input: str) -> bool:
    return any([operation.key in input for operation in self.operations])

def isUnknown(self: Calculator, input: str) -> bool:
    for operation in self.operations:
        if operation.key in input: return False
    for var in self.variables:
        if var in input: return False
    return not (input.isdigit() or input == ")" or input == "]")

def append_multipliers(self: Calculator, equation: str) -> str:
    index: int = 1
    while index < len(equation):
        if (equation[index] == '(' and equation[index - 1].isdigit()) or (equation[index - 1].isdigit() and isUnknown(self, equation[index])):
            equation = equation[ :index] + "*" + equation[index: ]
            index += 1
        index += 1

    print(f"eq: {equation}")
    return equation

def num_leftof(equation: str, index: int) -> tuple[float, int]:
    i: int = index - 1
    while i >= 0 and is_number_char(equation[i]):
        i -= 1
        if equation[i] == '-': 
            i -= 1
            break

    return (float(equation[i + 1:index]), i + 1)

def num_rightof(equation: str, index: int) -> tuple[float, int]:
    i = index + 1
    while i < len(equation) and is_number_char(equation[i]):
        if (equation[i] == '-' and i != index + 1): break
        i += 1
    print(f"equation: {equation}")
    return (float(equation[index + 1: i]), i)

def two_around(equation: str, index: int) -> tuple[tuple[float, float], tuple[int, int]]:
    left_value, start_index = num_leftof(equation, index)
    right_value, end_index = num_rightof(equation, index)
    return ((left_value, right_value), (start_index, end_index))

def in_between(start_str: str, end_str: str ="", index_offset: int = 0) -> GrabFunction:
    def internal(equation: str, start_index: int) -> tuple[str, tuple[int, int]]:
        nesting_count: int = 0
        start_index += index_offset
        for i in range(start_index+1, len(equation)):
            if equation[i] == start_str and end_str != "": nesting_count += 1
            elif equation[i] == end_str:
                if end_str != "" and nesting_count > 0: 
                    nesting_count -= 1
                    continue
                
                return (equation[start_index+1:i], (start_index - index_offset, i+1))
        raise ValueError("Does not have enclosing wrapper.")
    return internal

def left_of(equation: str, index: int) -> tuple[float, tuple[int, int]]:
    value, left = num_leftof(equation, index)
    return value, (left, index + 1)

def seperate_arguments(input: str) -> list[str]:
    base_split = input.split(",")
    for index, value in enumerate(base_split):
        if "]" in value: 
            backtrack_index: int = index
            while backtrack_index >= 0:
                if "[" in base_split[backtrack_index]:
                    for _ in range(backtrack_index + 1, index + 1):
                        base_split[backtrack_index] += "," + base_split[backtrack_index + 1]
                        base_split.pop(backtrack_index + 1)
                    break
                backtrack_index -= 1
    
    return base_split
        

#endregion

#region Math Functions
def average(numbers: list[float]) -> float:
    return sum(numbers)/len(numbers)

def sum(numbers: list[float]) -> float:
    sum: float = 0
    for num in numbers: sum += num
    return sum

def median(numbers: list[float]) -> float:
    index: int = int(len(numbers) / 2)
    return numbers[index]

def factorial(number: float) -> float:
    if number == 1: return 1
    return number * factorial(number - 1)

def summorial(number: float) -> float:
    if number == 1: return 1
    return number + summorial(number - 1)
#endregion

#region HELPERS
def starts_with_var(self: Calculator, substr: str) -> str | None:
    for var in sorted(self.variables, key=len, reverse=True):
        if substr.startswith(var):
            return var
    return None

def part_of_function(self: Calculator, input: str, index: int) -> bool:
    while input[index].isalpha():
        index += 1
        if index == len(input): return False
        if input[index] == "[": return True 
    
    return False

def replace_vars(self: Calculator, input: str) -> str:
    i: int = 0
    while (i < len(input)):
        if (variable := starts_with_var(self, input[i:])) is not None and not part_of_function(self, input, i):
            input = input[0:i] + self.variables[variable] + input[i+len(variable):]
        i += 1
    return input

def find_next_operator(self: Calculator, equation: str) -> tuple[int, operation | None]:
    current_operation: tuple[int, operation | None] = (-1, None)
    start_index = 0 if equation[0] != '-' else 1
    for i in range(start_index, len(equation)):
        for operator in self.operations:
            if i+len(operator.key) <= len(equation) and equation[i:i+len(operator.key)] == operator.key:
                if (current_operation[1] is None or operator.importance > current_operation[1].importance):
                    current_operation = (i, operator)
                break

    return current_operation

def stitch_in(str: str, start: int, end: int, stitch_in: str) -> str:
    if start < 0: raise ValueError("start must be greater than or equal to 0.")
    if end > len(str): raise ValueError("end must be less than or equal to length of template string.")
    if start > end: raise ValueError("Start can not be larger than end.")

    print(f"stiching: {str}, {start}, {end}, {stitch_in}")
    left_str = str[ :start]
    right_str = str[end: ]
    x  = left_str + stitch_in + right_str
    
    print("done with stich: ", x)
    return x
#endregion

def was_command(self: Calculator, input: str) -> str | None:
    passed_value: str = str()
    if (param_start := input.find(":")) != -1:
        passed_value = input[param_start + 1: ]
        input = input[ :param_start] #Set input to be just the command

    for cmd in self.commands:
        if input == cmd:
            func = self.commands[cmd]
    
            return func() if passed_value == "" else func(passed_value)
        
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
    left_solution = self.solve_f(left_equation)
    right_solution = self.solve_f(right_equation)
    if left_solution is None or right_solution is None: return "Invalid"

    match equality_check:
        case "equal":
            if left_solution == right_solution:
                return f"Correct. Results: (left: {left_solution}, right: {right_solution})"
            else:
                return f"Incorrect. Results: (left: {left_solution}, right: {right_solution})"
        case "greater":            
            if left_solution > right_solution:
                return f"Correct. Results: (left: {left_solution}, right: {right_solution})"
            else:
                return f"Incorrect. Results: (left: {left_solution}, right: {right_solution})"
        case "less":
            if left_solution < right_solution:
                return f"Correct. Results: (left: {left_solution}, right: {right_solution})"
            else:
                return f"Incorrect. Results: (left: {left_solution}, right: {right_solution})"
        case "greater or equal":
            if left_solution >= right_solution:
                return f"Correct. Results: (left: {left_solution}, right: {right_solution})"
            else:
                return f"Incorrect. Results: (left: {left_solution}, right: {right_solution})"
        case "less or equal":
            if left_solution <= right_solution:
                return f"Correct. Results: (left: {left_solution}, right: {right_solution})"
            else:
                return f"Incorrect. Results: (left: {left_solution}, right: {right_solution})"
        case _:
            raise ValueError("Invalid equality check value. Please have it be greater, less, equal or some combination.")