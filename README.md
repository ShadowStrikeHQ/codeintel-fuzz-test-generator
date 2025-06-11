# codeintel-Fuzz-Test-Generator
Generates basic fuzz tests based on code structure and function signatures, focusing on boundary conditions and common error patterns. - Focused on Tools for static code analysis, vulnerability scanning, and code quality assurance

## Install
`git clone https://github.com/ShadowStrikeHQ/codeintel-fuzz-test-generator`

## Usage
`./codeintel-fuzz-test-generator [params]`

## Parameters
- `-h`: Show help message and exit
- `--num_tests`: Number of fuzz tests to generate per function. Defaults to 10.
- `--string_length`: Length of random strings used in fuzzing. Defaults to 10.
- `--int_min`: Minimum integer value for fuzzing. Defaults to -100.
- `--int_max`: Maximum integer value for fuzzing. Defaults to 100.
- `--output_file`: Optional file to save the generated tests to. If not provided, tests will be printed to stdout.

## License
Copyright (c) ShadowStrikeHQ
