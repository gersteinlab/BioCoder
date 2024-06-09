import os
import subprocess
import random
import re
import string

# language = ""
# def set_language(lang):
#     global language
#     language = lang

# use_env_var = None
# def set_use_env_var(use):
#     global use_env_var
#     use_env_var = use

# env_dict = {}
# env_prefix="PASSATK" #PASSATK0, PASSATK1, etc.
# index = 0

class ParsingStrategy:
    def __init__(self, language, use_env_var, env_prefix):
        if language == "":
            raise Exception("Language not set")
        if use_env_var == None:
            raise Exception("Use env var not set")
        
        self.language = language
        self.use_env_var = use_env_var
        self.env_prefix = env_prefix
    
    def get_env_syntax(self):
        syntaxes = {
            "python": "os.environ[\"{}\"]",
            "bash": "echo ${}",
            "c": "getenv(\"{}\")",
            "c++": "getenv(\"{}\")",
            "java": "System.getenv(\"{}\")",
            "javascript": "process.env[\"{}\"]",
            "php": "getenv(\"{}\")",
            "ruby": "ENV[\"{}\"]",
            "perl": "getenv(\"{}\")",
            "powershell": "$env:{}",
            "go": "os.Getenv(\"{}\")",
            "rust": "std::env::var(\"{}\")",
        }
        
        return syntaxes[self.language]
    
    def assign_variable(self, content, index):
        if self.use_env_var:
            var_name = self.env_prefix + str(index)
            return self.get_env_syntax().format(var_name)
        else:
            return content
    
    def package_function(self, syntax, content, index):
        if self.use_env_var:
            return True, syntax.format(self.assign_variable(content, index))
        else:
            return False, syntax.format(content)

    def get_arguments(self, arg_string):
        split_str = arg_string.split(";")[1:]
        return_dict = {}
        for arg in split_str:
            arg_name, arg_value = self.parse_single_argument(arg)
            return_dict[arg_name] = arg_value
        return return_dict

    def parse_single_argument(self, value: str):
        if "=" not in value:
            return value, True
        arg_name = value.split("=")[0]
        arg_value = value.split("=")[1]
        return arg_name, arg_value.split(",")

    def __call__(self, arg_string):
        self.str = arg_string
        return ""

class RandomIntegerStrategy(ParsingStrategy):
    def __init__(self, language, use_env_var, env_prefix):
        super().__init__(language, use_env_var, env_prefix)

        self.parse_int_syntaxes = {
            "python": "int({})",
            "bash": "{}",
            "c": "atoi({})",
            "c++": "atoi({})",
            "java": "Integer.parseInt({})",
            "javascript": "parseInt({})",
            "php": "intval({})",
            "ruby": "{}.to_i",
            "perl": "int({})",
            "powershell": "int({})",
            "go": "strconv.Atoi({})",
            "rust": "{}.parse::<i32>().unwrap()",
        }

    def __call__(self, arg_string, index):
        parsed_dict = self.get_arguments(arg_string)

        if "range" in parsed_dict:
            self.min = int(parsed_dict["range"][0])
            self.max = int(parsed_dict["range"][1])
        else:
            self.min = -100000
            self.max = 100000
        
        random_int = str(random.randint(self.min, self.max))
        use_env, ret = self.package_function(self.parse_int_syntaxes[self.language], random_int, index)
        
        return ret, random_int

class RandomStringStrategy(ParsingStrategy):
    def __init__(self, language, use_env_var, env_prefix):
        super().__init__(language, use_env_var, env_prefix)

        self.random_types = {
            "ascii": self.generate_random_string_ascii,
            "alpha": self.generate_random_strin_alpha,
            "alphanumeric": self.generate_random_string_alphanumeric,
            "alphanumeric_special": self.generate_random_string_alphanumeric_special,
            "alphanumeric_allcases": self.generate_random_string_alphanumeric_allcases
        }
        self.custom_types = {
            "custom": self.generate_random_string_custom
        }
        self.parse_string_syntaxes = {
            "python": "{}",
            "bash": "{}",
            "c": "{}",
            "c++": "{}",
            "java": "{}",
            "javascript": "{}",
            "php": "{}",
            "ruby": "{}",
            "perl": "{}",
            "powershell": "{}",
            "go": "{}",
            "rust": "{}",
        }
    
    def generate_random_string_ascii(self, length):
        return ''.join(random.choice(string.ascii_letters) for i in range(length))
    def generate_random_strin_alpha(self, length):
        return ''.join(random.choice(string.ascii_lowercase) for i in range(length))
    def generate_random_string_alphanumeric(self, length):
        return ''.join(random.choice(string.ascii_lowercase + string.digits) for i in range(length))
    def generate_random_string_alphanumeric_special(self, length):
        return ''.join(random.choice(string.ascii_lowercase + string.digits + string.punctuation) for i in range(length))
    def generate_random_string_alphanumeric_allcases(self, length):
        return ''.join(random.choice(string.ascii_letters + string.digits) for i in range(length))
    def generate_random_string_custom(self, length, custom):
        return ''.join(random.choice(custom) for i in range(length))


    def __call__(self, arg_string, index):
        parsed_dict = self.get_arguments(arg_string)
        # get the length
        length = 10
        if "length" in parsed_dict:
            length_arr = parsed_dict["length"]
            if len(length_arr) == 1:
                length = int(length_arr[0])
            elif len(length_arr) == 2:
                length = random.randint(int(length_arr[0]), int(length_arr[1]))
            else:
                print("Warning: length argument has more than 2 values. Using default value of 10")
        
        str_type = "ascii"
        if "type" in parsed_dict:
            str_type = parsed_dict["type"][0]
            
        call_func = self.random_types["ascii"]
        random_str = call_func(length)
        
        if "custom" in parsed_dict:
            call_func = self.custom_types["custom"]
            random_str = call_func(length, parsed_dict["custom"])
        elif str_type in self.random_types:
            call_func = self.random_types[str_type]
            random_str = call_func(length)

        use_env, res = self.package_function(self.parse_string_syntaxes[self.language], random_str, index)
        if use_env:
            return res, random_str
        
        quote_type = "double"
        if "quotes" in parsed_dict: quote_type = parsed_dict["quotes"][0]
        
        startend_quote = ""
        if quote_type == "double": startend_quote = "\""
        elif quote_type == "single": startend_quote = "'"
        
        return startend_quote + res + startend_quote, random_str

        
class RandomFloatStrategy(ParsingStrategy):
    def __init__(self, language, use_env_var, env_prefix):
        super().__init__(language, use_env_var, env_prefix)

        self.parse_float_syntaxes = {
            "python": "float({})",
            "bash": "{}",
            "c": "atof({})",
            "c++": "atof({})",
            "java": "Float.parseFloat({})",
            "javascript": "parseFloat({})",
            "php": "floatval({})",
            "ruby": "{}.to_f",
            "perl": "float({})",
            "powershell": "float({})",
            "go": "strconv.ParseFloat({})",
            "rust": "{}.parse::<f32>().unwrap()",
        }

    def __call__(self, arg_string, index):
        parsed_dict = self.get_arguments(arg_string)
        if "range" in parsed_dict:
            self.min = float(parsed_dict["range"][0])
            self.max = float(parsed_dict["range"][1])
        else:
            self.min = -100000.0
            self.max = 100000.0
        random_float = str(random.uniform(self.min, self.max))
        use_env, ret = self.package_function(self.parse_float_syntaxes[self.language], random_float, index)
        return ret, random_float

class RandomBoolStrategy(ParsingStrategy):
    def __init__(self, language, use_env_var, env_prefix):
        super().__init__(language, use_env_var, env_prefix)

        self.parse_bool_syntaxes = {
            "python": "bool({})",
            "bash": "{}",
            "c": "bool({})",
            "c++": "bool({})",
            "java": "Boolean.parseBoolean({})",
            "javascript": "Boolean({})",
            "php": "boolval({})",
            "ruby": "{}.to_b",
            "perl": "bool({})",
            "powershell": "bool({})",
            "go": "strconv.ParseBool({})",
            "rust": "{}.parse::<bool>().unwrap()",
        }

    def __call__(self, arg_string, index, bool_type="python"):
        parsed_dict = self.get_arguments(arg_string)
        if "type" in parsed_dict:
            bool_type = parsed_dict["type"][0]
        else:
            bool_type = "lower"
            
        if bool_type == "upper" or bool_type == "python":
            random_bool = random.choice(["True", "False"])
        elif bool_type == "lower":
            random_bool = random.choice(["true", "false"])
        elif bool_type == "int":
            random_bool = random.choice(["1", "0"])
        else:
            raise Exception("Invalid bool type")
        
        use_env, ret = self.package_function(self.parse_bool_syntaxes[self.language], random_bool, index)
        return ret, random_bool

class FindAndReplacer:
    """
    Helper class that given a Python file, and start/end
    patterns that delimit random generation areas, finds,
    and inserts randomly generated input into said areas that
    match the patterns

    Also takes in a number of fuzzy test cases that need to be
    generated and generates num_test_cases number of random
    values for each random generation area that it finds
    and stores the result of this random generation into
    its attribute self.fuzzy_testcases

    Attributes:
        start_pattern (str): the pattern that delimits the
        start of a random generation area

        end_pattern (str): the pattern that delimits the end
        of a random generation area

        num_tests (int): the number of fuzzy test cases to generate

        fuzzy_testcases (list): a list of dictionaries, with one
        dictionary for each fuzzy test case; each dictionary
        contains the random values to set each environment
        variable for each fuzzy test case; the length of
        fuzzy_testcases should be equal to num_tests

        langauge (str): the programming language of the code
        that we are performing the find and replace algorithm in

        use_env_var (bool): determines whether or not we use
        the environment variable strategy to randomly
        generate fuzzy test cases

        env_prefix (str): the prefix that is attached to the front
        of every fuzzy test case number

    Methods:
        __init__: initializes an instance of FindAndReplacer

        find_and_replace: given a Python file, finds and inserts
        randomly generated input into random generation areas
        that are enclosed by self.start_pattern and self.end_pattern
    """

    def __init__(self, start_pattern='<|', end_pattern='|>', num_tests=10, 
                 language='python', use_env_var=True, env_prefix='PASSATK'):
        """
        Initializes an instance of FindAndReplacer

        Args:
            start_pattern (str): the attribute start_pattern is set
            to this

            end_pattern (str): the attribute end_pattern is set to this

            num_tests (int): the attribute num_tests is set to this

            language (str): the attribute language is set to this

            use_env_var (bool): the attribute use_env_var is set to this

            env_prefix (str): the attribute env_prefix is set to this
        """

        self.start_pattern = start_pattern
        self.end_pattern = end_pattern
        self.num_tests = num_tests

        self.fuzzy_testcases = [{} for _ in range(num_tests)]

        self.language = language
        self.use_env_var = use_env_var
        self.env_prefix = env_prefix

        self.strategies = {
            'int': RandomIntegerStrategy(
                language=language,
                use_env_var=use_env_var,
                env_prefix=env_prefix
            ),
            'string': RandomStringStrategy(
                language=language,
                use_env_var=use_env_var,
                env_prefix=env_prefix
            ),
            'float': RandomFloatStrategy(
                language=language,
                use_env_var=use_env_var,
                env_prefix=env_prefix
            ),
            'bool': RandomBoolStrategy(
                language=language,
                use_env_var=use_env_var,
                env_prefix=env_prefix
            )
        }

        return

    def parse_string(self, string, strategies, index):
        """
        This function takes a parsed string found in a 
        context file and a dictionary of parsing strategies,
        as well as the index of the environment variable
        we are parsing, and then randomly generates a value
        according to the appropriate strategy, and then returns
        the langauge-specific syntax to query said environment
        variable.

        Args:
            string (str): the parsed string found in a context
            file that outlines what to generate and how to generate
            a random value that will be stored in an environment
            variable

            strategies (dict): a dictionary containing all 
            the pertinent parsing strategies

            index (int): an integer that indexes what 
            environment variable we need to query

        Returns:
            tuple: a tuple, with the first value in the tuple
            being the language-specific string used to query
            the specified environment variable, and the second
            value in the tuple being the randomly generated
            value according to the parsed strategy
        """

        if string[:2] == "<|" and string[-2:] == "|>":
            string = string[2:-2]
            strategy_name = string.split(";")[0]
            if strategy_name not in strategies:
                raise Exception("Invalid strategy name")
            strategy = strategies[strategy_name]
            return strategy(string, index)
        return string

    def find_and_replace(self, file_path):
        """
        This function given a code file, finds and inserts
        randomly generated input into random generation areas
        that are enclosed by self.start_pattern and self.end_pattern

        Also populates the attribute self.fuzzy_testcases with 
        randomly generated values for each environment
        variable that satisfy the requirements of the parsed
        strings that find_and_replace finds

        Args:
            file_path (str): the path to the file in which to 
            perform the find and replace routine

        Returns:
            str: the file with all random generation areas
            replaced with randomly generated input in the form of
            a string
        """

        with open(file_path, 'r') as file:
            file_contents = file.read()

        regex_pattern = re.escape(self.start_pattern) + r'(.*?)' + re.escape(self.end_pattern)

        matches = re.finditer(
            pattern = regex_pattern,
            string = file_contents,
            flags = re.DOTALL
        )

        file_copy = file_contents[:]

        index = 0

        for match in list(matches)[::-1]:
            start_idx = match.start()
            end_idx = match.end()

            for test_case in range(self.num_tests):
                replacement, rand_val = self.parse_string(match.group(), self.strategies, index)

                self.fuzzy_testcases[test_case][f'{self.env_prefix}{index}'] = rand_val

            file_copy = file_copy[:start_idx] + str(replacement) + file_copy[end_idx:]

            index += 1

        return file_copy

# TODO: Write docstrings for everything

class FuzzerTesterError(Exception):
    """
    Custom exception class made for FuzzerTester errors.

    Attributes:
        message (str): the error message associated
        with the FuzzerTesterError instance

        failure_reason (str): if the FuzzerTesterError
        was raised due to a golden/generated program
        failing, this will give the reason of the failure;
        can be one of the following: timeout, syntax, runtime

    Methods:
        __init__: initializes an instance of FuzzerTesterError

        __str__: standard override of the __str__ method
        to determine how a FuzzerTesterError instance
        will be displayed to the console
    """

    def __init__(self, message, failure_reason=None):
        """
        Initializes an instance of FuzzerTesterError

        Args:
            message (str): the attribute message is set
            to this

            failure_reason (str): the attribute
            failure_reason is set to this
        """

        self.message = message
        self.failure_reason = failure_reason

        return
    
    def __str__(self):
        """
        Standard override of the __str__ method; defines
        how to display an instance of FuzzerTesterError
        to the console

        Returns:
            str: the string to be displayed to the console
        """

        return f'FuzzerTesterError: {self.message}'

# TODO: finish writing docstrings for the methods

class FuzzerTester:
    """
    Helper class that performs fuzzer testing using an
    environment variable based strategy. Takes in an input
    folder that contains 3 files:

        1. A context file with a marked location to 
        insert the generated or golden code, as well as random
        generation areas where the randomly generated
        test cases will be inserted

        2. A generated code file that contains the generated
        code that will be tested against the golden code

        3. A golden code file that contains the golden
        code that will be used as the standard to help
        test the generated code

    Given this input data, the FuzzerTester, using its method
    run_fuzzer_tests, can run a specified number of randomly 
    generated unit tests to test the correctness of the
    given generated code. 

    The way FuzzerTester does this is that it inserts the 
    generated and golden code into the context, then 
    inserts the language-specific code to access environment
    variables in the random generation areas, and then
    if needed, compiles this newly generated file. All of these
    new files can be found in a temporary folder which is 
    automatically generated by the tester. 

    Simultaneously to creating the runnable generated and golden
    code files, the FuzzerTester also randomly generates a 
    specified number of unit test input data. 

    Afterwords, the FuzzerTester will run each unit test
    by loading in the unit test data into environment variables
    and then running the files.

    Attributes:
        language_to_extension (dict): dictionary used to map
        programming languages to their respective file extension

        language (str): the programming language that the generated
        code we are testing is written in

        extension (str): the file extension of the programming language
        that we are testing in

        tmp_folder_path (str): the path to the temporary folder where
        the runnable code files that are generated by FuzzerTester
        are stored

        input_path (str): the path to the input folder, which contains
        a context file, and the generated and golden code snippets

        context_file (str): the name of the context file, which must
        be found in the folder pointed to by input_path, and also must
        have the file extension self.extension

        gen_code_file (str): the name of the generated code snippet,
        which must be found in the folder pointed to by input_path, and
        also must have the file extension self.extension

        golden_code_file (str): the name of the golden code snippet,
        which must be found in the folder pointed to by input_path, and
        also must have the file extension self.extension

        gen_code_test_folder (str): the name of the folder where
        gen_code_test_file will reside in; must be in the folder pointed
        to by tmp_folder_path

        gen_code_test_folder_path (str): the path of gen_code_test_folder

        golden_code_test_folder (str): the name of the folder where
        golden_code_test_file will reside in; must be in the folder
        pointed to by tmp_folder_path

        golden_code_test_folder_path (str): the path of
        golden_code_test_folder_path

        gen_code_test_file (str): the name of the runnable file that consists
        of the context, with the generated code and test cases inserted in;
        must be in the folder pointed to by gen_code_test_folder_path

        golden_code_test_file (str): the name of the runnable file that
        consists of the context, with the golden code and test cases inserted in;
        must be in the folder pointed to by golden_code_test_folder_path

        insert_solution_text (str): the string that delimits where to insert
        the generated/golden code into the context

        num_tests (int): the number of randomly generated unit tests to run

        use_env_var (bool): whether or not to use the environment
        variable testing strategy; for now must be true

        env_prefix (str): the prefix to all the environment variables
        used by FuzzerTester for testing unit tests
        
        test_program (str): the path to the program that can
        run the programs generated by an instance of FuzzerTester

        find_and_replacer (FindAndReplacer): an instance of FindAndReplacer
        that is used to insert in the language specific code
        to query environment variables, and is also used to generate
        the random unit test input data

    Methods:
        __init__: initializes an instance of FuzzerTester as well as
        an instance of its FindAndReplacer helper class

        _create_folder: creates a folder at the given folder path location

        _remove_folder: removes a folder and all of its contents
        at the given folder path location

        _get_file_path: gets the path of a file in a given folder, with
        a given name, and with a given extension

        _create_file: creates a file in a given folder, with a given name
        and extension

        _generate_runnable_code: helper function that generates the
        runnable code files and places them in their correct locations,
        i.e. under gen_code_test_folder_path and golden_code_test_folder_path;
        generates the runnable code files by inserting the generated/golden
        code into the context, and then uses find_and_replacer to insert
        the language specific code for querying environment variable, and
        then also generates the unit_test data and stores it in find_and_replacer,
        each unit_test consists of a dictionary with the keys being the name
        of the environment variable, while the value of the dict is the randomly
        generated value; note assumes that all the temporary folder 
        structure is already created before it is called

        _determine_failure_reason: helper function that given an error
        message, determines if it was a runtime or syntax error; only works
        for Python and Java functions at the moment

        _run_program: helper function that given a path to a runnable
        program, runs the program with the FuzzerTester's 
        self.test_program; returns the output of the program
        if the program ran successfully, otherwise it raises a FuzzerTesterError
        with the error message, as well as the failure reason

        _compare_program_outputs: helper function that takes a
        path to a runnable generated program and a runnable golden
        program; runs both programs and compares their outputs; if there are any
        errors with the program, this function returns false, the error message
        , and the failure reason; if the outputs are different
        between the programs, this function also returns false, and gives
        the failure reason as differing outputs; finally if the outputs 
        are the same, then the function returns true, and it means the
        generated code passes the particular test case; note this function
        requires the environment variables to be set before being run

        _get_test_result: helper function that given an index
        of a unit test, loads in the corresponding environment
        variables for the unit test, these are stored in the FuzzerTester's
        FindAndReplacer instance; afterwords, it runs and compares
        the output of the generated and golden code; it returns the results
        which are detailed in _compare_program_outputs

        run_fuzzer_tests: runs all the unit tests and collects the results, 
        the results for each unit test are detailed in _compare_program_outputs;
        note run_fuzzer_tests runs early stopping for syntax erorrs
        for better performance
    """

    def __init__(self, start_pattern='<|', end_pattern='|>', tmp_folder_path='./tmp', input_path='./input',
                 context_file='context', gen_code_file='generated_code', golden_code_file='golden_code',
                 gen_code_test_file='generated_code_test', golden_code_test_file='golden_code_test',
                 gen_code_test_folder='generated_code_test', golden_code_test_folder='golden_code_test',
                 insert_solution_text='<<insert solution here>>', num_tests=10, language='python', 
                 use_env_var=True, test_program='python3', env_prefix='PASSATK'):
        
        if use_env_var == False:
            raise FuzzerTesterError(f'non environment variable based fuzzer methods are not supported at the moment')

        self.language_to_extension = {
            'python': 'py',
            'java': 'java'
        }

        self.language = language
        self.extension = self.language_to_extension[self.language]

        # if not os.path.isdir(input_path):
        #     raise FuzzerTesterError(f'{input_path} does not exist')

        # context_file_path = self._get_file_path(input_path, context_file, self.extension)
        # if not os.path.isfile(context_file_path):
        #     raise FuzzerTesterError(f'{context_file_path} does not exist')

        # gen_code_file_path = self._get_file_path(input_path, gen_code_file, self.extension)
        # if not os.path.isfile(gen_code_file_path):
        #     raise FuzzerTesterError(f'{gen_code_file_path} does not exist')

        # golden_code_file_path = self._get_file_path(input_path, golden_code_file, self.extension)
        # if not os.path.isfile(golden_code_file_path):
        #     raise FuzzerTesterError(f'{golden_code_file_path} does not exist')

        self.tmp_folder_path = tmp_folder_path
        self.input_path = input_path

        self.context_file = context_file
        self.gen_code_file = gen_code_file
        self.golden_code_file = golden_code_file

        self.gen_code_test_file = gen_code_test_file
        self.gen_code_test_folder = gen_code_test_folder
        self.gen_code_test_folder_path = os.path.join(self.tmp_folder_path, self.gen_code_test_folder)

        self.golden_code_test_file = golden_code_test_file
        self.golden_code_test_folder = golden_code_test_folder
        self.golden_code_test_folder_path = os.path.join(self.tmp_folder_path, self.golden_code_test_folder)

        self.insert_solution_text = insert_solution_text

        self.test_program = test_program

        self.use_env_var = use_env_var
        self.env_prefix = env_prefix

        self.num_tests = num_tests

        self.find_and_replacer = FindAndReplacer(
            start_pattern=start_pattern,
            end_pattern=end_pattern,
            num_tests=self.num_tests,
            language=self.language,
            use_env_var=self.use_env_var,
            env_prefix=self.env_prefix
        )   

        return

    def _create_folder(self, folder_path):
        if not os.path.isdir(folder_path):
            os.makedirs(folder_path)

        return
    
    def _remove_folder(self, folder_path):
        if os.path.isdir(folder_path):
            subprocess.run(f'rm -rf {folder_path}', shell=True)

        return

    def _get_file_path(self, folder_path, file_name, extension):
        return os.path.join(folder_path, f'{file_name}.{extension}')

    def _create_file(self, folder_path, file_name, extension):
        file_path = self._get_file_path(folder_path, file_name, extension)

        if not os.path.isfile(file_path):
            subprocess.run(f'touch {file_path}', shell=True)

        return
    
    def _generate_runnable_code(self):
        self._create_file(self.gen_code_test_folder_path, self.gen_code_test_file, self.extension)
        self._create_file(self.golden_code_test_folder_path, self.golden_code_test_file, self.extension)

        context_with_tests = self.find_and_replacer.find_and_replace(
            file_path=self._get_file_path(self.input_path, self.context_file, self.extension)
        )

        insert_start_idx = context_with_tests.find(self.insert_solution_text)
        insert_end_idx = insert_start_idx + len(self.insert_solution_text)
        
        in_class = insert_start_idx != 0 and context_with_tests[insert_start_idx - 1] != '\n'

        with open(self._get_file_path(self.input_path, self.gen_code_file, self.extension), 'r') as file:
            gen_code = file.read()

        if gen_code is None:
            gen_code = ''

        if in_class:
            lines = gen_code.split('\n')

            if len(lines) > 1:
                gen_code_with_tests = context_with_tests[:insert_start_idx] + lines[0] + '\n'

                for i in range(1, len(lines)):
                    gen_code_with_tests += '    ' + lines[i] + '\n'
                
                gen_code_with_tests += context_with_tests[insert_end_idx:]
            else:
                gen_code_with_tests = context_with_tests[:insert_start_idx] + lines[0] + context_with_tests[insert_end_idx:]
        else:
            gen_code_with_tests = context_with_tests[:insert_start_idx] + gen_code + context_with_tests[insert_end_idx:]

        with open(self._get_file_path(self.gen_code_test_folder_path, self.gen_code_test_file, self.extension), 'w') as file:
            file.write(gen_code_with_tests)

        with open(self._get_file_path(self.input_path, self.golden_code_file, self.extension), 'r') as file:
            golden_code = file.read()

        if golden_code is None:
            golden_code = ''

        if in_class:
            lines = golden_code.split('\n')

            if len(lines) > 1:
                golden_code_with_tests = context_with_tests[:insert_start_idx] + lines[0] + '\n'

                for i in range(1, len(lines)):
                    golden_code_with_tests += '    ' + lines[i] + '\n'
                
                golden_code_with_tests += context_with_tests[insert_end_idx:]
            else:
                golden_code_with_tests = context_with_tests[:insert_start_idx] + lines[0] + context_with_tests[insert_end_idx:]
        else:
            golden_code_with_tests = context_with_tests[:insert_start_idx] + golden_code + context_with_tests[insert_end_idx:]

        with open(self._get_file_path(self.golden_code_test_folder_path, self.golden_code_test_file, self.extension), 'w') as file:
            file.write(golden_code_with_tests)

        return
    
    def _determine_failure_reason(self, message):
        if self.language == 'python':
            python_runtime_error_pattern = r'\ATraceback'

            if re.match(python_runtime_error_pattern, message):
                return 'runtime'
            else:
                return 'syntax'
        elif self.language == 'java':
            java_compile_error_pattern = r'\AMain\.java:\d+'

            if re.match(java_compile_error_pattern, message):
                return 'syntax'
            else:
                return 'runtime'
        else:
            return None

    def _run_program(self, program_path):
        try:
            completed_process = subprocess.run(
                f'{self.test_program} {program_path}', 
                shell=True, 
                timeout=30, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                env=os.environ
            )

            if completed_process.returncode != 0:
                message = completed_process.stderr.decode('utf-8')

                failure_reason = self._determine_failure_reason(message)

                raise FuzzerTesterError(message, failure_reason=failure_reason)

            output = completed_process.stdout.decode('utf-8')
        except subprocess.TimeoutExpired:
            raise FuzzerTesterError('program timed out', failure_reason='timeout')
        except FuzzerTesterError as e:
            raise FuzzerTesterError(e.message, failure_reason=e.failure_reason)
        except Exception as e:
            # Theoretically should never get to this part of the code
            raise FuzzerTesterError('something went very wrong')

        return output

    def _compare_program_outputs(self, gen_program_path, golden_program_path):
        try:
            golden_program_output = self._run_program(golden_program_path)
        except FuzzerTesterError as e:
            return False, e.failure_reason, f'golden program failed: {e.message}'
    
        try:
            gen_program_output = self._run_program(gen_program_path)
        except FuzzerTesterError as e:
            return False, e.failure_reason, f'generated program failed: {e.message}'

        if golden_program_output.strip() != gen_program_output.strip():
            return False, 'differing output', (gen_program_output, golden_program_output)

        return True, 'passed', None

    def _get_test_result(self, index):
        for environment_variable in self.find_and_replacer.fuzzy_testcases[index].keys():
            os.environ[environment_variable] = self.find_and_replacer.fuzzy_testcases[index][environment_variable]

        res = self._compare_program_outputs(
            gen_program_path=self._get_file_path(self.gen_code_test_folder_path, self.gen_code_test_file, self.extension),
            golden_program_path=self._get_file_path(self.golden_code_test_folder_path, self.golden_code_test_file, self.extension)
        )

        return res
    
    def run_fuzzer_tests(self):
        self._create_folder(self.tmp_folder_path)
        self._create_folder(self.gen_code_test_folder_path)
        self._create_folder(self.golden_code_test_folder_path)

        self._generate_runnable_code()

        results = []
        for i in range(self.num_tests):
            results.append(self._get_test_result(i))

            if results[i][0] == False and results[-1][1] == 'syntax':
                for _ in range(i + 1, self.num_tests):
                    results.append(results[i])

                break

        self._remove_folder(self.tmp_folder_path)
        return results
    
    def test_functions(self, context_path, generated_path, golden_path):
        if not os.path.isdir(self.input_path):
            os.makedirs(self.input_path)
        
        if not os.path.isfile(self._get_file_path(self.input_path, self.context_file, self.extension)):
            with open(self._get_file_path(self.input_path, self.context_file, self.extension), 'w'):
                pass
        
        if not os.path.isfile(self._get_file_path(self.input_path, self.gen_code_file, self.extension)):
            with open(self._get_file_path(self.input_path, self.gen_code_file, self.extension), 'w'):
                pass

        if not os.path.isfile(self._get_file_path(self.input_path, self.golden_code_file, self.extension)):
            with open(self._get_file_path(self.input_path, self.golden_code_file, self.extension), 'w'):
                pass

        subprocess.run(f'cp {context_path} {self._get_file_path(self.input_path, self.context_file, self.extension)}', shell=True)
        subprocess.run(f'cp {generated_path} {self._get_file_path(self.input_path, self.gen_code_file, self.extension)}', shell=True)
        subprocess.run(f'cp {golden_path} {self._get_file_path(self.input_path, self.golden_code_file, self.extension)}', shell=True)

        results =  self.run_fuzzer_tests()

        self._remove_folder(self.input_path)

        return results
    
    def _run_rosalind_program(self, program_path, cwd):
        try:
            completed_process = subprocess.run(
                f'{self.test_program} {program_path}', 
                shell=True, 
                timeout=30, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                env=os.environ,
                cwd=cwd
            )

            if completed_process.returncode != 0:
                message = completed_process.stderr.decode('utf-8')

                failure_reason = self._determine_failure_reason(message)

                raise FuzzerTesterError(message, failure_reason=failure_reason)

            output = completed_process.stdout.decode('utf-8')
        except subprocess.TimeoutExpired:
            raise FuzzerTesterError('program timed out', failure_reason='timeout')
        except FuzzerTesterError as e:
            raise FuzzerTesterError(e.message, failure_reason=e.failure_reason)
        except Exception as e:
            # Theoretically should never get to this part of the code
            raise FuzzerTesterError('something went very wrong')

        return output

    def rosalind_test(self, problem_name, context_path, generated_code_path, tmp_path, outputs_path, testcase_path):

        RS_INSERT_TEXT = '<<insert solution here>>'

        RS_TMP_PATH = tmp_path

        RS_OUTPUTS_PATH = outputs_path

        RS_TESTCASE_PATH = testcase_path

        golden_outputs_path = os.path.join(RS_OUTPUTS_PATH, problem_name)

        with open(context_path, 'r') as f:
            context = f.read()

        start = context.find(RS_INSERT_TEXT)
        end = start + len(RS_INSERT_TEXT)

        with open(generated_code_path, 'r') as f:
            generated_code = f.read()

        program = context[:start] + generated_code + context[end:]

        if not os.path.isdir(RS_TMP_PATH):
            os.makedirs(RS_TMP_PATH)

        program_path = os.path.join(RS_TMP_PATH, 'generated.py')

        with open(program_path, 'w') as f:
            f.write(program)

        input_path = os.path.join(RS_TMP_PATH, 'input.txt')

        results = []

        for test_case_num in range(10):

            test_case_path = os.path.join(RS_TESTCASE_PATH, f'test_case_{test_case_num}', f'rosalind_{problem_name}.txt')

            with open(test_case_path, 'r') as f:
                test_case_content = f.read()

            with open(input_path, 'w') as f:
                f.write(test_case_content)

            try:
                gen_program_output = self._run_rosalind_program(program_path, RS_TMP_PATH)

                golden_testcase_path = os.path.join(golden_outputs_path, f'{test_case_num}.txt')

                with open(golden_testcase_path, 'r') as f:
                    golden_program_output = f.read()

                if golden_program_output.strip() != gen_program_output.strip():
                    results.append((False, 'differing output', (gen_program_output, golden_program_output)))
                else:
                    results.append((True, 'passed', None))

            except FuzzerTesterError as e:
                results.append((False, e.failure_reason, f'generated program failed: {e.message}'))

        subprocess.run(f'rm -rf {RS_TMP_PATH}', shell=True)

        return results

