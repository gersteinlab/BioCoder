
"""

# 1. Parse the requirements line by line.
# 2. Create a new dictionary to store the parsed requirements.
# 3. Split the requirement into a module name and a version and a comparison operator.
# 4. Remove all extra spaces.
# 5. Add the parsed requirement to the dictionary.
# 6. Return the dictionary.

def parse_requirements(requirements):
    """
    Parse a requirements line into a module and version parts.

    :param requirements: a string containing requirements to parse
    :return: a dictionary containing module names as keys and their version and comparison operators as values
    """
    result = {}
    for requirement in requirements:
        # If the requirement is empty, skip it.
        if requirement == '':
            continue
        # Split the requirement into a module name and a version and a comparison operator.
        module, version, operator = requirement.split()
        # Remove all extra spaces.
        module = module.strip()
        version = version.strip()
        operator = operator.strip()
        # Add the parsed requirement to the dictionary.
        result[module] = (version, operator)
    return result


# Tests

print(parse_requirements