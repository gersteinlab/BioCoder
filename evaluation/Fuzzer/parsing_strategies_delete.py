#example of string to parse: <|random_int;range=0,5|>

import string

class ParsingStrategy:
    def __init__(self):
        pass
    
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

import random
class RandomIntegerStrategy(ParsingStrategy):
    def __call__(self, arg_string):
        parsed_dict = self.get_arguments(arg_string)
        
        if "range" in parsed_dict:
            self.min = int(parsed_dict["range"][0])
            self.max = int(parsed_dict["range"][1])
        else:
            self.min = -100000
            self.max = 100000
        
        random_int = random.randint(self.min, self.max)
        return str(random_int)

class RandomStringStrategy(ParsingStrategy):
    def __init__(self):
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


    def __call__(self, arg_string):
        parsed_dict = self.get_arguments(arg_string)
        if "length" in parsed_dict:
            length = int(parsed_dict["length"][0])
        else:
            length = 10
        
            
        if "type" in parsed_dict:
            str_type = parsed_dict["type"][0]
        else:
            str_type = "ascii"
        
        if "custom" in parsed_dict:
            call_func = self.custom_types["custom"]
            res = call_func(length, parsed_dict["custom"])
        elif str_type in self.random_types:
            call_func = self.random_types[str_type]
            res = call_func(length)
        else:
            call_func = self.random_types["ascii"]
            res = call_func(length)
        
        if "quotes" in parsed_dict:
            quote_type = parsed_dict["quotes"][0]
        else:
            quote_type = "double"
        
        if quote_type == "double":
            startend_quote = "\""
        elif quote_type == "single":
            startend_quote = "'"
        else:
            startend_quote = ""
            
        return startend_quote + res + startend_quote
        
        
class RandomFloatStrategy(ParsingStrategy):
    def __call__(self, arg_string):
        parsed_dict = self.get_arguments(arg_string)
        if "range" in parsed_dict:
            self.min = float(parsed_dict["range"][0])
            self.max = float(parsed_dict["range"][1])
        else:
            self.min = -100000.0
            self.max = 100000.0
        random_float = random.uniform(self.min, self.max)
        return str(random_float)
    
class RandomBoolStrategy(ParsingStrategy):
    def __call__(self, arg_string, bool_type="python"):
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
        
        return str(random_bool)

strategies = {
    "int": RandomIntegerStrategy(),
    "string": RandomStringStrategy(),
    "float": RandomFloatStrategy(),
    "bool": RandomBoolStrategy()
}
    
def parse_string(string):
    if string[:2] == "<|" and string[-2:] == "|>":
        string = string[2:-2]
        strategy_name = string.split(";")[0]
        if strategy_name not in strategies:
            raise Exception("Invalid strategy name")
        strategy = strategies[strategy_name]
        return strategy(string)
    return string