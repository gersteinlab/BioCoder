from collections import Counter

def most_common_character(str):
    # Count the occurrences of each character in the string
    char_counts = Counter(str)

    # Get the character(s) with the highest count
    most_common = char_counts.most_common(1)

    # Return the most common character and its count
    if most_common:
        return most_common[0][0]
    else:
        return None