import os

import requests
import json
import subprocess
import shlex
import bs4
import zipfile
import base64

# afdfadf setting up the environment
if "TESTING" in os.environ:
    baseUrl = "https://fhdsxjdwjuo4chghz7mlaw2cju0ppwfx.lambda-url.us-east-1.on.aws"
    bucket = "gersteincodegentest"
    ecr_repo = "passatkrunnertest"
elif "PROD" in os.environ:
    baseUrl="https://wnn2rjzzw2nkqj6yfbbp5igfmy0yxemy.lambda-url.us-east-1.on.aws"
    bucket = "gersteincodegenprod"
    ecr_repo = "passatkrunner"
else:
    raise Exception("No environment variable set")

s3Url = "http://gersteincodegenprod.s3-website-us-east-1.amazonaws.com"

try:
    from fuzzer_tester import FuzzerTester
except:
    # download fuzzer_tester.py
    url = s3Url + "/fuzzer_tester.py/fuzzer/fuzzer_tester.py"
    r = requests.get(url)
    with open("fuzzer_tester.py", "wb") as f:
        f.write(r.content)
    from fuzzer_tester import FuzzerTester

error_words = ["error", "exception", "fail", "failed", "error:", "exception:", "fail:", "failed:"]
success_words = ["success", "passed", "success:", "passed:", "completed", "completed:", "finished", "finished:"]

#========================== BEGIN FUNCTION DEFINITIONS ==========================

#override print function
import builtins
def print(*args, **kwargs):
    builtins.print(*args, **kwargs)
    with open("test_stdout.txt", "a") as f:
        builtins.print(*args, file=f, **kwargs)

def get_data():
    global baseUrl
    # check if DATA_BASE64 is set
    if "DATA_BASE64" in os.environ:
        # decode the data
        data = base64.b64decode(os.environ["DATA_BASE64"])
        # load the data
        json_data = json.loads(data)
        return json_data

    if "MANUAL_TEST_CASE" in os.environ:
        # manual test case is a filepath to a json file
        with open(os.environ["MANUAL_TEST_CASE"], "r") as f:
            json_data = json.load(f)
        return json_data
    response = requests.get(baseUrl + "/get")
    if response.status_code == 200:
        if (response.text == ""): return None
        json_res = json.loads(response.text)
        return json_res
    else:
        return None

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
def replace_functions(file: str, line_start : int, line_end: int, new_function: str):
    with open(file, "r") as f:
        lines = f.readlines()
    written=False
    print("Writing to file: " + file)
    correct_location =0
    if "{" in lines[line_start-1]:
        correct_location = line_start
    else:
        correct_location = line_start-1
    with open(file, "w") as f:
        for i in range(len(lines)):
            if i >= line_start-4 and i <=line_start-1:
                print(lines[i], end="")
            if i >= correct_location and i <= line_end:
                if written: continue
                space_count=0
                for j in range(len(lines[i])):
                    if lines[i][j] == " ": space_count+=1
                    else: break
                # get rid of first { in new_function, ignoring all whitespace
                if new_function[0] == "{":
                    new_function = new_function[1:]
                while new_function[0] == " ": #most inefficient thing ever LOL but its okay
                    new_function = new_function[1:]


                f.write(" "* space_count + new_function+"\n\n")
                print("-"*50)
                print(" "* space_count + new_function+"\n\n")
                print("-"*50)
                written=True
            else:
                f.write(lines[i])
            if (i >= line_end and i <= line_end+3):
                print(lines[i], end="")
    print("Done writing to file: " + file)
    print("+"*25 + "File contents" + "+"*25)
    with open(file, "r") as f:
        print(f.read())
    print("+"*25 + "End file contents" + "+"*25)

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

def longest_common_subsequence(s1: str,s2 : str):
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
            lcs_not_in_s1 += s1[i-1]
            i -= 1
        else:
            j -= 1
    return "".join(lcs), "".join(list(reversed(lcs_not_in_s1)))

def submit_error(test_case_id: int, error: str):
    global baseUrl
    response = requests.get(baseUrl + "/submit?test_case_id=" + str(test_case_id) + "&result=" + "fail"+ "&error=" + error)
    print("Error: " + error)
    upload_log(test_case_id)
    exit(0)

def submit_result(test_case_id: str):
    global baseUrl
    # result = "pass" if result else "fail"
    response = requests.get(baseUrl + "/submit?test_case_id=" + str(test_case_id) + "&result=" + "pass")
    print("Result: " + "pass")
    upload_log(test_case_id)
    exit(0)

magic_string = "6SKLCZjnPzPdwztCY3wf5X1c9L1AsN2aHB4mWlmU"
def convert_command(command: str):
    global magic_string
    with open("/home/ubuntu/temp_command.sh", "w") as f:
        f.write("#!/bin/bash -il \n")
        f.write(command)
    command = "bash /home/ubuntu/temp_command.sh"
    command+="\necho $'\\n'; echo $'\\n'$?" + magic_string + "$'\\n'" + "\n"
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



# def run_build_normal(build_command: str, working_location: str):
#     build_command = shlex.split(build_command)
#     process = subprocess.Popen(build_command, cwd=working_location, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#     stdout, stderr = process.communicate()
#     return_code = process.returncode
#     return return_code, stdout, stderr
#
# def run_test_normal(run_command: str, working_location: str):
#     run_command = shlex.split(run_command)
#     process = subprocess.Popen(run_command, cwd=working_location, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#     stdout, stderr = process.communicate()
#     return_code = process.returncode
#     return return_code, stdout, stderr
#=========================== END FUNCTION DEFINITIONS ===========================

#================================= BEGIN CLASSES ================================

class RunErrorException(Exception):
    def __init__(self, message, short_message=None):
        self.message = message
        self.short_message = short_message
        if self.short_message is None:
            self.short_message = "run_failed"


class BaseStrategy:
    def __init__(self, command, reference_output):
        global repo_metadata, working_location, parse_options, error_words, data
        self._command = command
        self._reference_output = reference_output
        self._run_output = []
        self._run_success = True
        self._repo_metadata = repo_metadata
        self._working_location = working_location
        self._parse_options = parse_options
        self._error_words = error_words
        self._data = data

    def test_line(self, line: str, reference_line: str):
        """Return True if the line is correct, throw a RunErrorException otherwise"""
        return True

    def test_output(self, output: str, reference_output: str):
        """Return True if the output is correct, throw a RunErrorException otherwise"""
        return True

    def test_file(self, filename : str, method : str):
        """Return True if the file analysis is correct, throw a RunErrorException otherwise"""
        return True

    def test_return_code(self, return_code: int):
        """Return True if the return code is correct, throw a RunErrorException otherwise"""
        return True

    def test(self, command, working_directory: str) -> (int, str):
        global magic_string
        # print("Running run command: " + command)
        command_file = fileize_command(command)
        process = subprocess.Popen([command_file], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=working_directory)
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
        return_code, output = self.test(command, self._working_location)
        self.test_return_code(return_code)
        self.test_output(output, self._reference_output)
        # self.test_file(filename, method)
        return True


class LiveStrategy(BaseStrategy):
    def __init__(self, command, reference_output):
        super().__init__(command, reference_output)
        self._run_success = True
        self._reference_index = 0
        self._reference_output = reference_output.split("\n")

    def test_line(self, line: str, reference_line: str = None):
        if "\r" in line:
            return True
        if reference_line is None:
            if self._reference_index < len(self._reference_output):
                reference_line = self._reference_output[self._reference_index]
                self._reference_index += 1
            else:
                raise RunErrorException("Live analysis, no more reference lines to compare to.", "no_more_reference_lines")
        line = line.strip()
        lcs, lcs_remaining = longest_common_subsequence(line, reference_line)
        acceptable = can_ignore_string(lcs_remaining)
        if not acceptable:
            print("Expected line: " + reference_line)
            print("Actual line: " + line)
            raise RunErrorException("Live analysis, line does not match reference. Difference: " + lcs_remaining, "lcs_difference")
        return True


class KeywordStrategy(BaseStrategy):
    def __init__(self, command, reference_output):
        super().__init__(command, reference_output)
        self._run_success = True
        self._reference_index = 0
        self._keywords = parse_options["build_analysis_keywords"]
        self._error_words_added = self._error_words + self._keywords

    def test_line(self, line: str, reference_line: str = None):
        output_tokens = line.split(" ")
        for token in output_tokens:
            if token in self._error_words_added:
                raise RunErrorException("Keyword analysis, error word found: " + token, "error_word_found")
        return True


class ReturnCodeStrategy(BaseStrategy):
    def __init__(self, command, reference_output):
        super().__init__(command, reference_output)
        self._run_success = True
        self._reference_index = 0
        self._reference_output = reference_output.split("\n")

    def test_return_code(self, return_code: int):
        if return_code != 0:
            raise RunErrorException("Return code analysis, return code not 0.", "return_code")
        return True


class IgnoreStrategy(BaseStrategy):
    def __init__(self, command, reference_output):
        super().__init__(command, reference_output)
        self._run_success = True
        self._reference_index = 0
    # do nothing


class FileStrategy(BaseStrategy):
    def __init__(self, command, reference_output):
        super().__init__(command, reference_output)
        self._run_success = True
        self._reference_index = 0
        self._reference_output = reference_output.split("\n")
    def analyze(self):
        if analysis_method == "passive":
            print("Running passive analysis")
            lcs, lcs_remaining = longest_common_subsequence(reference_output, run_output)
            acceptable = can_ignore_string(lcs_remaining)
            if not acceptable:
                print("Run failed, killing process (passive analysis difference: \"" + lcs + "\")")
                return 1, "run_failed"
            return 0, None
        elif analysis_method == "live":
            return 0, None
        elif analysis_method == "file":
            # TODO: implement file-based parsing
            if "file" not in parse_options:
                print("No file specified for parsing")
                return 1, "no_analysis_file_specified"
            file = parse_options["file"]
            if not os.path.exists(working_location + "/" + file):
                print("File does not exist")
                return 1, "analysis_file_does_not_exist"

            # detect file type: html, json, or xml
            if file.endswith(".html"):
                # TODO: currently hardcoded to htsjdk
                with open(file, "r") as f:
                    html = f.read()
                soup = bs4.BeautifulSoup(html, "html.parser")
                results = soup.find_all("div", {"id": "failures"})
                results = results[0].find_all("div", {"class": "counter"})
                print(results[0].text)
                try:
                    failed_tests = int(results[0].text)
                except:
                    failed_tests = failed_tests
                if failed_tests > 0:
                    return 1, "run_failed"
            else:
                print("File type not supported")
                return 1, "analysis_file_type_not_supported"
        else:
            print("Unknown analysis method")
            return 1, "unknown_analysis_method"

class FuzzerStrategy(BaseStrategy):
    def __init__(self, command, reference_output):
        super().__init__(command, reference_output)
        if "iterations" in parse_options:
            self.num_tests = int(parse_options["iterations"])
        else:
            self.num_tests = 10
        if "num_tests" in self._data:
            self.num_tests = int(self._data["num_tests"])
        print("Initialized fuzzer strategy with " + str(self.num_tests) + " tests")
        self._fuzzer = FuzzerTester(num_tests=self.num_tests)
        self.use_java = False
    def use_java_func(self):
        # check if the 3 files exist
        if os.path.exists("context.java") and os.path.exists("generated.java") and os.path.exists("golden.java"):
            self.use_java = True
        else:
            raise RunErrorException("Fuzzer analysis, java files not found", "fuzzer_java_files_not_found")
        print("Using java files for fuzzer analysis")
        self.use_java = True
        self._fuzzer = FuzzerTester(
            gen_code_test_file='Main',
            golden_code_test_file='Main',
            language='java',
            test_program='./run_java.sh',
            num_tests=self.num_tests
        )
    def use_python_func(self):
        # check if the 3 files exist
        if os.path.exists("context.py") and os.path.exists("generated.py") and os.path.exists("golden.py"):
            self.use_java = False
        else:
            raise RunErrorException("Fuzzer analysis, python files not found", "fuzzer_python_files_not_found")
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
        self.analyze_language()
        
        if self.use_java:
            print("="*10 + "CONTEXT" + "="*10)
            with open("context.java", "r") as f:
                print(f.read())
            print("="*10 + "GENERATED" + "="*10)
            with open("generated.java", "r") as f:  
                print(f.read())
            print("="*10 + "GOLDEN" + "="*10)
            with open("golden.java", "r") as f:
                print(f.read())
            results = self._fuzzer.test_functions(
                context_path="context.java",
                generated_path="generated.java",
                golden_path="golden.java",
            )
        else:
            print("="*10 + "CONTEXT" + "="*10)
            with open("context.py", "r") as f:
                print(f.read())
            print("="*10 + "GENERATED" + "="*10)
            with open("generated.py", "r") as f:
                print(f.read())
            print("="*10 + "GOLDEN" + "="*10)
            with open("golden.py", "r") as f:
                print(f.read())
            
            results = self._fuzzer.test_functions(
                context_path="context.py",
                generated_path="generated.py",
                golden_path="golden.py",
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
    "live": LiveStrategy,
    "keyword": KeywordStrategy,
    "return_code": ReturnCodeStrategy,
    "ignore": IgnoreStrategy,
    "file": FileStrategy,
    "fuzzer": FuzzerStrategy
}

def init_strategy(analysis_method: str, command: str, reference_output: str) -> BaseStrategy:
    """Initializes a strategy based on the analysis method. Returns None if the analysis method is not supported."""
    global strategies
    if analysis_method not in strategies:
        return None
    return strategies[analysis_method](command, reference_output)

#================= BEGIN IMPORTANT FUNCTION DEFINITIONS =========================


#=========================== BEGIN MAIN CODE ====================================
#=========================== START DATA DOWNLOAD ===============================
data = get_data()
if data is None:
    print("No data")
    exit(0)
test_case_id = data["test_case_id"]

try:
    # Extract: test case id
    print("TEST_CASE_ID: " + test_case_id)

    # Verify: check if method body only contains whitespace

    # Extract: repo name
    repo_name = data["test_case_repo"]
    repo_name_escaped = repo_name.replace("/", ",")
    working_location = repo_name_escaped + "/"

    # Download: repo metadata
    print("Requesting repository metadata from: ", f"{s3Url}/outputs/{repo_name}.json")
    temp_req = requests.get(f"{s3Url}/outputs/{repo_name}.json")
    if temp_req.status_code != 200:
        submit_error(test_case_id, "no_repo_metadata")
        exit(0)
    try:
        repo_metadata = temp_req.json()
    except:
        submit_error(test_case_id, "repo_metadata_error")
        exit(0)

    print("REPO_METADATA: ", repo_metadata)
    # Download Function archive
    # Format should be:
    # - app/
    #   - context.py
    #   - generated.py
    #   - golden.py
    function_data_url = f"{s3Url}/functions/{test_case_id[0]}/{test_case_id}.zip"
    print("Requesting function archive from: ", function_data_url)
    function_archive_req = requests.get(function_data_url)
    if function_archive_req.status_code != 200:
        submit_error(test_case_id, "no_function_archive")
        exit(0)
    with open("function_archive.zip", "wb") as f:
        f.write(function_archive_req.content)
    # unzip function_archive.zip using unzip
    try:
        process = subprocess.Popen(["unzip", "-q", "function_archive.zip"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        return_code = process.returncode
        if return_code != 0:
            raise Exception("Unzip failed")
    except:
        submit_error(test_case_id, "unzip_error")
        exit(0)
    
    # Download: repo archive
    # temp_req = requests.get(f"{s3Url}/repos/{repo_name}.zip")
    # print("Requesting repository data from: ", f"{s3Url}/repos/{repo_name}.zip")
    # if temp_req.status_code != 200:
    #     print("Requesting repository data from: ", f"{s3Url}/repos/{repo_name_escaped}.zip")
    #     temp_req = requests.get(f"{s3Url}/repos/{repo_name_escaped}.zip")
    #     if temp_req.status_code != 200:
    #         submit_error(test_case_id, "no_repo_archive")
    #         exit(0)
    #
    # with open(repo_name_escaped + ".zip", "wb") as f:
    #     f.write(temp_req.content)
    #
    # # unzip repo archive using unzip
    # process = subprocess.Popen(["unzip", "-q", repo_name_escaped + ".zip"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # stdout, stderr = process.communicate()
    # return_code = process.returncode
    # if return_code != 0:
    #     submit_error(test_case_id, "unzip_error")
    #     exit(0)


    # working_location = "htsjdk/" # TODO: comment this out later
    # Action: modify file
    # =========================== END DATA DOWNLOAD ==============================

    build_commands = repo_metadata["build_commands"]
    """
    Each build command is a dictionary with the following keys:
    - name: the name of the build
    - command: the command to run
    - analysis_method: the analysis method to use
    - parse_options: the options to use when parsing the output
    - reference_output: the reference output to compare against
    """

    for build_command in build_commands:
        print("BUILD_COMMAND: ", build_command["command"])
        name = build_command["name"]
        command = build_command["command"]
        analysis_method = build_command["analysis_method"]
        parse_options = build_command["parse_options"]
        reference_output = build_command["reference_output"]
        print("Running test command: " + command + " with analysis method: " + analysis_method)
        try:
            runner = init_strategy(analysis_method, command, reference_output)
            if runner is None:
                submit_error(test_case_id, "invalid_analysis_method")
                exit(0)
            runner.run()
        except RunErrorException as e:
            print("Build failed, killing process (error: \"" + e.message + "\")")
            submit_error(test_case_id, "build_failed")
            exit(0)

    # Extract: reference_output
    # build_reference_output = repo_metadata["build_output"]
    # build_reference_output_split = build_reference_output.split("\n") if build_reference_output is not None else None
    # build_reference_index=0
    #
    # build_success = True
    # # Extract: build command
    # # run the build step and capture the output for live processing
    # build_command = repo_metadata["build_command"]
    # build_output = []
    # print("ANALYSIS METHOD: " + build_analysis_method)

        # If we get to here, then build was successful

    # ====================== END BUILD STEP ======================

    # ====================== BEGIN TEST STEP ======================
    # Extract: test commands
    test_commands = repo_metadata["run_commands"]
    """
    Each test command is a dictionary with the following keys:
    - name: the name of the test
    - command: the command to run
    - analysis_method: the analysis method to use
    - parse_options: the parse options to use
    - reference_output: the reference output to use
    """

    if test_commands is None:
        submit_error(test_case_id, "no_run_commands")
        exit(0)
    if len(test_commands) == 0:
        submit_error(test_case_id, "no_run_commands")
        exit(0)


    for test_command in test_commands:
        name = test_command["name"]
        command = test_command["command"]
        analysis_method = test_command["analysis_method"]
        parse_options = test_command["parse_options"]
        reference_output = test_command["reference_output"]
        print("Running test command: " + command + " with analysis method: " + analysis_method)
        try:
            runner = init_strategy(analysis_method, command, reference_output)
            if runner is None:
                submit_error(test_case_id, "invalid_analysis_method")
                exit(0)
            runner.run()
        except RunErrorException as e:
            print("Test failed, killing process (error: \"" + e.message + "\")")
            submit_error(test_case_id, e.short_message)
            exit(0)
    
    # ====================== END TEST STEP ======================
    # ====================== BEGIN FUZZER STEP ======================
    # print("Initializing fuzzer")
    # try:
    #     parse_options["iterations"] = data["num_tests"]
    #     runner = init_strategy("fuzzer", "fuzz", "fuzz")
    #     if "Java" in test_case_id:
    #         print("Using Java fuzzer")
    #         runner.use_java()
    #     elif "Python" in test_case_id:
    #         print("Using Python fuzzer")
    #         runner.use_python()
    #     else:
    #         submit_error(test_case_id, "invalid_language")
    #         exit(0)
    #     if runner is None:
    #         submit_error(test_case_id, "fuzzer_initialization_error")
    #         exit(0)
    #     runner.run()
    # except RunErrorException as e:
    #     print("Fuzzer failed, killing process (error: \"" + e.message + "\")")
    #     print(e)
    #     submit_error(test_case_id, e.short_message)
    #     exit(0)
    submit_result(test_case_id)
    exit(0)
except Exception as e:
    import traceback
    exec_form = traceback.format_exc()
    print(exec_form)
    submit_error(test_case_id, "generic_error")
    exit(0)
