import re
from parsing_strategies import parse_string

class FindAndReplacer:
    """
    Helper class that given a Python file, and start/end
    patterns that delimit random generation areas, finds,
    and inserts randomly generated input into said areas that
    match the patterns

    Attributes:
        start_pattern (str): the pattern that delimits the
        start of a random generation area

        end_pattern (str): the pattern that delimits the end
        of a random generation area

    Methods:
        __init__: initializes an instance of FindAndReplacer

        find_and_replace: given a Python file, finds and inserts
        randomly generated input into random generation areas
        that are enclosed by self.start_pattern and self.end_pattern

    """

    def __init__(self, start_pattern = '<|', end_pattern = '|>'):
        """
        Initializes an instance of FindAndReplacer

        Args:
            start_pattern (str): the attribute start_pattern is set
            to this

            end_pattern (str): the attribute end_pattern is set to this
        """

        self.start_pattern = start_pattern
        self.end_pattern = end_pattern

        return

    def find_and_replace(self, file_path):
        """
        This function given a Python file, finds and inserts
        randomly generated input into random generation areas
        that are enclosed by self.start_pattern and self.end_pattern

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

        for match in list(matches)[::-1]:
            start_idx = match.start()
            end_idx = match.end()

            replacement = str(parse_string(match.group()))

            file_copy = file_copy[:start_idx] + str(replacement) + file_copy[end_idx:]

        return file_copy
