from Calculator import Calculator

def main():
    calculator: Calculator = Calculator()

    setup_commands = [
        "x:100",
        "y:9",
        "z:33"
    ]

    tests = [
        ("112+9", "121.0"),
        ("100+-10", "90.0"),
        ("100--10", "110.0"),
        ("100*10", "1000.0"),
        ("3^3", "27.0"),
        ("3%4", "3.0"),
        ("4%3", "1.0"),
        ("4%3*10-6--9/3", "7.0"),
        ("12+2==14", "Correct"),
        ("12-2==9", "Incorrect"),
        ("12*2--6/3==12*2--6/3", "Correct"),
        ("x==z", "Incorrect"),
        ("x^2", "10000.0")
    ]

    for command in setup_commands:
        calculator.run(command)

    for num in range(len(tests)):
        test = tests[num]
        result: str = calculator.run(test[0])
        if (result == test[1]):
            print(f"PASSED TEST #{num + 1}! Input was '{test[0]}' and expected was '{test[1]}'. Result from run was '{result}'")
        else:
            print(f"Did not pass test #{num + 1}... Input was '{test[0]}' and expected was '{test[1]}'. Result from run was '{result}'")


if __name__ == '__main__':
    main()