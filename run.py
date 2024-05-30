from Calculator import Calculator
import sys
import os

calculator: Calculator = Calculator()

def main():
    while (usr := input("Type equation: ")) != "quit":
        result = calculator.run(usr, safe=(len(sys.argv) > 1 and sys.argv[1] == "safe"))
        if result != "":
            print(f"       Result: {result}")

if __name__ == '__main__':
    main()