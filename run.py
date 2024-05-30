from Calculator import Calculator
import os

calculator: Calculator = Calculator()

def main():
    while (usr := input("Type equation: ")) != "quit":
        result = calculator.run(usr)
        if result != "":
            print(f"       Result: {result}")

if __name__ == '__main__':
    main()