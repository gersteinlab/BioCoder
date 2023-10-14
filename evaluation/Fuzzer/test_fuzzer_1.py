from fuzzer_tester import FuzzerTester

fuzzer = FuzzerTester(
    num_tests=10,
)

# Replace paths with to context, generated code, and golden code files
results = fuzzer.test_functions(context_path="/home/ubuntu/CodeGen/BCE/PassAtKRunner/Fuzzer/test_functions/python_test_function_6/context.py", 
                      generated_path="/home/ubuntu/CodeGen/BCE/PassAtKRunner/Fuzzer/test_functions/python_test_function_6/generated.py",
                        golden_path="/home/ubuntu/CodeGen/BCE/PassAtKRunner/Fuzzer/test_functions/python_test_function_6/golden.py")

print(len(results))