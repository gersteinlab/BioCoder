import os

import requests
import json
import subprocess
import shlex
import bs4
import zipfile
import base64

# INPUT: recieve metadata through testcase_biocoder.json located in /workspace/testing_files/testcase_biocoder.json,
# /workspace/context.txt, /workspace/testing_files/golden.txt, /workspace/testing_files/generated.txt
# OUTPUT: results_biocoder.json written to /workspace/testing_files/results_biocoder.json
# JSON File format of results_biocoder.json

from fuzzer_tester import FuzzerTester

error_words = ["error", "exception", "fail", "failed", "error:", "exception:", "fail:", "failed:"]
success_words = ["success", "passed", "success:", "passed:", "completed", "completed:", "finished", "finished:"]

fuzzer_num_tests = 10

# ========================== BEGIN FUNCTION DEFINITIONS ==========================

# override print function
import builtins


def print(*args, **kwargs):
    builtins.print(*args, **kwargs)
    with open("test_stdout.txt", "a") as f:
        builtins.print(*args, file=f, **kwargs)


def upload_log(test_case_id: str):
    global baseUrl
    with open("test_stdout.txt", "r") as f:
        log = f.read()
    response = requests.post(baseUrl + "/upload", json={"log": log, "test_case_id": test_case_id})
    if response.status_code == 200:
        return True
    else:
        return False


# replace the range between line_start and line_end in modify_file
def replace_functions(file: str, line_start: int, line_end: int, new_function: str):
    with open(file, "r") as f:
        lines = f.readlines()
    written = False
    print("Writing to file: " + file)
    correct_location = 0
    if "{" in lines[line_start - 1]:
        correct_location = line_start
    else:
        correct_location = line_start - 1
    with open(file, "w") as f:
        for i in range(len(lines)):
            if i >= line_start - 4 and i <= line_start - 1:
                print(lines[i], end="")
            if i >= correct_location and i <= line_end:
                if written: continue
                space_count = 0
                for j in range(len(lines[i])):
                    if lines[i][j] == " ":
                        space_count += 1
                    else:
                        break
                # get rid of first { in new_function, ignoring all whitespace
                if new_function[0] == "{":
                    new_function = new_function[1:]
                while new_function[0] == " ":  # most inefficient thing ever LOL but its okay
                    new_function = new_function[1:]

                f.write(" " * space_count + new_function + "\n\n")
                print("-" * 50)
                print(" " * space_count + new_function + "\n\n")
                print("-" * 50)
                written = True
            else:
                f.write(lines[i])
            if (i >= line_end and i <= line_end + 3):
                print(lines[i], end="")
    print("Done writing to file: " + file)
    print("+" * 25 + "File contents" + "+" * 25)
    with open(file, "r") as f:
        print(f.read())
    print("+" * 25 + "End file contents" + "+" * 25)


def can_ignore_string(string: str):
    # ignorable_characters are numbers, decimals, percents, and spaces
    ignorable_characters = "0123456789e.%():=-+, "
    # detect if string can be converted into a hex number
    try:
        int(string, 16)
        return True
    except:
        pass

    for i in range(len(string)):
        if string[i] not in ignorable_characters:
            return False
    return True


def longest_common_subsequence(s1: str, s2: str):
    # return the longest common subsequence between s1 and s2 as a string
    # also return the length of the letters in s1 not in the lcs
    m = len(s1)
    n = len(s2)
    L = [[None] * (n + 1) for i in range(m + 1)]
    for i in range(m + 1):
        for j in range(n + 1):
            if i == 0 or j == 0:
                L[i][j] = 0
            elif s1[i - 1] == s2[j - 1]:
                L[i][j] = L[i - 1][j - 1] + 1
            else:
                L[i][j] = max(L[i - 1][j], L[i][j - 1])
    index = L[m][n]
    lcs = [""] * (index + 1)
    lcs[index] = ""
    lcs_not_in_s1 = ""
    i = m
    j = n
    while i > 0 and j > 0:
        if s1[i - 1] == s2[j - 1]:
            lcs[index - 1] = s1[i - 1]
            i -= 1
            j -= 1
            index -= 1
        elif L[i - 1][j] > L[i][j - 1]:
            lcs_not_in_s1 += s1[i - 1]
            i -= 1
        else:
            j -= 1
    return "".join(lcs), "".join(list(reversed(lcs_not_in_s1)))


def submit_error(error: str):
    with open("/testing_files/results_biocoder.json", "w") as f:
        s = json.dumps({
            "result": "fail",
            "reason": error
        })
        f.write(s)
    exit(0)

def submit_pass():
    with open("/testing_files/results_biocoder.json", "w") as f:
        s = json.dumps({
            "result": "pass"
        })
        f.write(s)
    exit(0)


magic_string = "6SKLCZjnPzPdwztCY3wf5X1c9L1AsN2aHB4mWlmU"


def convert_command(command: str):
    global magic_string
    with open("/home/ubuntu/temp_command.sh", "w") as f:
        f.write("#!/bin/bash -il \n")
        f.write(command)
    command = "bash /home/ubuntu/temp_command.sh"
    command += "\necho $'\\n'; echo $'\\n'$?" + magic_string + "$'\\n'" + "\n"
    return command


def fileize_command(command: str):
    with open("/home/ubuntu/temp_command.sh", "w") as f:
        f.write("#!/bin/bash -il \n")
        f.write(command)
    return "/home/ubuntu/temp_command.sh"


def send_command(process, command, get_output=False):
    global magic_string
    new_command = convert_command(command)
    process.stdin.write(new_command.encode("utf-8"))
    process.stdin.flush()
    if get_output:
        output = []
        while True:
            line = process.stdout.readline().decode("utf-8")
            if magic_string in line:
                break
            if "\r" in line:
                continue
            output.append(line.strip())
            print(line.strip())
        return "\n".join(output)

# =========================== END FUNCTION DEFINITIONS ===========================

# ================================= BEGIN CLASSES ================================

class RunErrorException(Exception):
    def __init__(self, message, short_message=None):
        self.message = message
        self.short_message = short_message
        if self.short_message is None:
            self.short_message = "run_failed"


class BaseStrategy:
    def __init__(self, command, reference_output):
        global error_words, data
        self._command = command
        self._reference_output = reference_output
        self._run_output = []
        self._run_success = True
        # self._repo_metadata = repo_metadata
        # self._working_location = working_location
        # self._parse_options = parse_options
        self._error_words = error_words
        self._data = data

    def test_line(self, line: str, reference_line: str):
        """Return True if the line is correct, throw a RunErrorException otherwise"""
        return True

    def test_output(self, output: str, reference_output: str):
        """Return True if the output is correct, throw a RunErrorException otherwise"""
        return True

    def test_file(self, filename: str, method: str):
        """Return True if the file analysis is correct, throw a RunErrorException otherwise"""
        return True

    def test_return_code(self, return_code: int):
        """Return True if the return code is correct, throw a RunErrorException otherwise"""
        return True

    def test(self, command, working_directory: str) -> (int, str):
        global magic_string
        # print("Running run command: " + command)
        command_file = fileize_command(command)
        process = subprocess.Popen([command_file], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, cwd=working_directory)
        output_lines = []
        while True:
            line = process.stdout.readline().decode("utf-8")
            if line == '' and process.poll() is not None:
                break
            if line:
                print(line.strip())
                if line == "" and process.poll() is not None:
                    break
                # if magic_string in line:
                #     return_code = int(line.split(magic_string)[0].strip())
                #     return return_code, "\n".join(output_lines)
                if '\r' in line:
                    continue
                line_analysis = self.test_line(line, None)
                if not line_analysis:
                    self._run_success = False
                output_lines.append(line.strip())
        process.wait()
        return_code = process.poll()
        process.kill()
        return return_code, "\n".join(output_lines)

    def run(self):
        command = self._command
        # return_code, output = self.test(command, self._working_location)
        # self.test_return_code(return_code)
        # self.test_output(output, self._reference_output)
        # self.test_file(filename, method)
        return True

class FuzzerStrategy(BaseStrategy):
    def __init__(self, command, reference_output):
        super().__init__(command, reference_output)
        self.num_tests = fuzzer_num_tests
        if "num_tests" in self._data:
            self.num_tests = int(self._data["num_tests"])
        print("Initialized fuzzer strategy with " + str(self.num_tests) + " tests")
        self._fuzzer = FuzzerTester(num_tests=self.num_tests)
        self.use_java = self._data["language"] == "java"

    def use_java_func(self):
        # check if the 3 files exist
        # if os.path.exists("context.java") and os.path.exists("generated.java") and os.path.exists("golden.java"):
        #     self.use_java = True
        # else:
        #     raise RunErrorException("Fuzzer analysis, java files not found", "fuzzer_java_files_not_found")
        print("Using java files for fuzzer analysis")
        self.use_java = True
        self._fuzzer = FuzzerTester(
            gen_code_test_file='Main',
            golden_code_test_file='Main',
            language='java',
            test_program='/sources/run_java.sh',
            num_tests=self.num_tests
        )

    def use_python_func(self):
        # check if the 3 files exist
        # if os.path.exists("testing_files/context.py") and os.path.exists("testing_files/generated.py") and os.path.exists(
        #         "testing_files/golden.py"):
        #     self.use_java = False
        # else:
        #     raise RunErrorException("Fuzzer analysis, python files not found", "fuzzer_python_files_not_found")
        print("Using python files for fuzzer analysis")
        self.use_java = False

    def analyze_language(self):
        extensions = {
            "java": self.use_java_func,
            "py": self.use_python_func
        }

        notable_files = ["context", "generated", "golden"]

        language_counts = {}

        # detect language
        for file in notable_files:
            for extension in extensions:
                if os.path.exists(file + "." + extension):
                    if extension not in language_counts:
                        language_counts[extension] = 0
                    language_counts[extension] += 1
        if len(language_counts) == 0:
            raise RunErrorException("Fuzzer analysis, no files found", "fuzzer_no_files_found")
        for language in language_counts:
            if language_counts[language] == 3:
                extensions[language]()
                return

    def run(self):

        print("Running fuzzer analysis")
        # self.analyze_language()

        context_filepath = "/testing_files/context.java" if self.use_java else "/testing_files/context.py"
        generated_filepath = "/testing_files/generated.java" if self.use_java else "/testing_files/generated.py"
        golden_filepath = "/testing_files/golden.java" if self.use_java else "/testing_files/golden.py"

        # context_filepath = "testing_files/context.java" if self.use_java else "testing_files/context.py"
        # generated_filepath = "testing_files/generated.java" if self.use_java else "testing_files/generated.py"
        # golden_filepath = "testing_files/golden.java" if self.use_java else "testing_files/golden.py"

        if not os.path.exists(context_filepath) or not os.path.exists(generated_filepath) or not os.path.exists(golden_filepath):
            raise RunErrorException("Fuzzer analysis, files not found", "fuzzer_files_not_found")

        if self._data["language"] == "java":
            self.use_java_func()
        else:
            self.use_python_func()

        print("=" * 10 + "CONTEXT" + "=" * 10)
        with open(context_filepath, "r") as f:
            print(f.read())
        print("=" * 10 + "GENERATED" + "=" * 10)
        with open(generated_filepath, "r") as f:
            print(f.read())
        print("=" * 10 + "GOLDEN" + "=" * 10)
        with open(golden_filepath, "r") as f:
            print(f.read())

        results = self._fuzzer.test_functions(
            context_path=context_filepath,
            generated_path=generated_filepath,
            golden_path=golden_filepath,
        )

        for item in results:
            if not item[0]:
                print("Fuzzer analysis, error found: ")
                print("DETAILS: ")
                print(item)
                raise RunErrorException("Fuzzer analysis, error found: " + item[1], "fuzzer_mismatch")
        print("Fuzzer analysis, all tests passed")
        return True


strategies = {
    "fuzzer": FuzzerStrategy
}


def init_strategy(analysis_method: str, command: str, reference_output: str) -> BaseStrategy:
    """Initializes a strategy based on the analysis method. Returns None if the analysis method is not supported."""
    global strategies
    if analysis_method not in strategies:
        return None
    return strategies[analysis_method](command, reference_output)


# ================= BEGIN IMPORTANT FUNCTION DEFINITIONS =========================


# =========================== BEGIN MAIN CODE ====================================
# =========================== START DATA DOWNLOAD ===============================
if __name__=="__main__":
    # get the test case via a mounted file
    try:
        with open("/testing_files/testcase_biocoder.json", "r") as f:
            data = json.load(f)
    except:
        submit_error("missing input file testcase.txt")
        exit(0)
    # data is a json file that should contain the following fields:
    # test_case_id: str
    # num_cases: int
    # language: str
    test_case_id = data["test_case_id"]

    try:
        # Extract: test case id
        print("TEST_CASE_ID: " + test_case_id)

        try:
            init_strategy("fuzzer", "echo Hi", "Hi").run()
        except RunErrorException as e:
            print("Test failed, killing process (error: \"" + e.message + "\")")
            submit_error(e.short_message)
            exit(0)

        submit_pass()
        exit(0)
    except Exception as e:
        import traceback

        exec_form = traceback.format_exc()
        print(exec_form)
        submit_error("generic_error")
        exit(0)
