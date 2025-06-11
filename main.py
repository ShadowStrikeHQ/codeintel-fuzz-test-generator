#!/usr/bin/env python3
import argparse
import inspect
import logging
import os
import sys
import random
import string

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Default values
DEFAULT_NUM_TESTS = 10
DEFAULT_STRING_LENGTH = 10
DEFAULT_INT_RANGE = (-100, 100)


def setup_argparse():
    """
    Sets up the argument parser for the command-line interface.
    """
    parser = argparse.ArgumentParser(
        description="Generates basic fuzz tests based on code structure and function signatures."
    )

    parser.add_argument(
        "module_path",
        help="Path to the Python module containing the functions to fuzz test."
    )

    parser.add_argument(
        "--num_tests",
        type=int,
        default=DEFAULT_NUM_TESTS,
        help="Number of fuzz tests to generate per function. Defaults to 10."
    )

    parser.add_argument(
        "--string_length",
        type=int,
        default=DEFAULT_STRING_LENGTH,
        help="Length of random strings used in fuzzing. Defaults to 10."
    )

    parser.add_argument(
        "--int_min",
        type=int,
        default=DEFAULT_INT_RANGE[0],
        help="Minimum integer value for fuzzing. Defaults to -100."
    )

    parser.add_argument(
        "--int_max",
        type=int,
        default=DEFAULT_INT_RANGE[1],
        help="Maximum integer value for fuzzing. Defaults to 100."
    )

    parser.add_argument(
        "--output_file",
        type=str,
        default=None,
        help="Optional file to save the generated tests to. If not provided, tests will be printed to stdout."
    )
    return parser


def generate_fuzz_input(param_type, string_length=DEFAULT_STRING_LENGTH, int_range=DEFAULT_INT_RANGE):
    """
    Generates a random input based on the specified parameter type.
    Supports int, float, str, bool, and None. Other types return None.
    """
    try:
        if param_type is int:
            return random.randint(int_range[0], int_range[1])
        elif param_type is float:
            return random.uniform(int_range[0], int_range[1])
        elif param_type is str:
            return ''.join(random.choice(string.ascii_letters) for _ in range(string_length))
        elif param_type is bool:
            return random.choice([True, False])
        elif param_type is type(None):
            return None
        else:
            logging.warning(f"Unsupported parameter type: {param_type}. Returning None.")
            return None  # Unsupported type
    except Exception as e:
        logging.error(f"Error generating fuzz input for type {param_type}: {e}")
        return None


def generate_fuzz_tests(module_path, num_tests=DEFAULT_NUM_TESTS, string_length=DEFAULT_STRING_LENGTH, int_range=DEFAULT_INT_RANGE):
    """
    Generates fuzz tests for functions in a given module.
    """
    try:
        # Dynamically import the module
        module_dir, module_file = os.path.split(module_path)
        module_name, module_ext = os.path.splitext(module_file)

        if module_dir not in sys.path:
            sys.path.append(module_dir)

        try:
            module = __import__(module_name)
        except ImportError as e:
            logging.error(f"Failed to import module {module_name}: {e}")
            return []


        test_cases = []
        for name, obj in inspect.getmembers(module):
            if inspect.isfunction(obj):
                try:
                    sig = inspect.signature(obj)
                    params = sig.parameters
                    for i in range(num_tests):
                        args = []
                        kwargs = {}
                        for param_name, param in params.items():
                            param_type = param.annotation if param.annotation != inspect.Parameter.empty else str  # Default to str if no annotation

                            # Handle variable positional arguments (*args)
                            if param.kind == inspect.Parameter.VAR_POSITIONAL:
                                args.extend([generate_fuzz_input(int, string_length, int_range) for _ in range(random.randint(0, 3))]) # fuzz *args
                                continue
                            # Handle variable keyword arguments (**kwargs)
                            elif param.kind == inspect.Parameter.VAR_KEYWORD:
                                #Create a dict of random inputs for kwargs. Limiting to 3 for clarity.
                                kwargs.update({
                                    ''.join(random.choice(string.ascii_lowercase) for _ in range(5)): generate_fuzz_input(int, string_length, int_range)
                                    for _ in range(random.randint(0, 3))
                                })
                                continue
                            else:
                                arg = generate_fuzz_input(param_type, string_length, int_range)

                            if param.kind == inspect.Parameter.KEYWORD_ONLY:
                                kwargs[param_name] = arg
                            else:
                                args.append(arg)

                        # Construct the test case string
                        args_str = ", ".join(repr(arg) for arg in args)
                        kwargs_str = ", ".join(f"{k}={repr(v)}" for k, v in kwargs.items())
                        if args_str and kwargs_str:
                            call_str = f"{obj.__name__}({args_str}, {kwargs_str})"
                        elif args_str:
                            call_str = f"{obj.__name__}({args_str})"
                        elif kwargs_str:
                            call_str = f"{obj.__name__}({kwargs_str})"
                        else:
                            call_str = f"{obj.__name__}()"

                        test_case = f"# Test case {i+1} for function: {obj.__name__}\n"
                        test_case += f"# Call: {call_str}\n"
                        test_case += f"try:\n"
                        test_case += f"    result = {call_str}\n"
                        test_case += f"    print(f'Function {obj.__name__} executed successfully. Result: {{result}}')\n"
                        test_case += f"except Exception as e:\n"
                        test_case += f"    print(f'Function {obj.__name__} raised an exception: {{e}}')\n\n"
                        test_cases.append(test_case)
                except Exception as e:
                    logging.error(f"Error generating test case for function {name}: {e}")

        return test_cases

    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return []

def main():
    """
    Main function to parse arguments, generate fuzz tests, and print/save them.
    """
    parser = setup_argparse()
    args = parser.parse_args()

    # Input validation
    if not os.path.exists(args.module_path):
        logging.error(f"Module path does not exist: {args.module_path}")
        sys.exit(1)

    if args.num_tests <= 0:
        logging.error("Number of tests must be greater than zero.")
        sys.exit(1)

    if args.string_length <= 0:
        logging.error("String length must be greater than zero.")
        sys.exit(1)

    if args.int_min > args.int_max:
        logging.error("Integer minimum must be less than or equal to integer maximum.")
        sys.exit(1)


    tests = generate_fuzz_tests(
        args.module_path,
        args.num_tests,
        args.string_length,
        (args.int_min, args.int_max)
    )

    if args.output_file:
        try:
            with open(args.output_file, "w") as f:
                for test_case in tests:
                    f.write(test_case)
            logging.info(f"Fuzz tests saved to: {args.output_file}")
        except Exception as e:
            logging.error(f"Error writing to output file: {e}")
            sys.exit(1)
    else:
        for test_case in tests:
            print(test_case)

if __name__ == "__main__":
    main()