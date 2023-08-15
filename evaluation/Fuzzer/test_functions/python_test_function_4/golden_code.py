def most_common_character(str):
    char_counts = {}
    for char in str:
        if char in char_counts:
            char_counts[char] += 1
        else:
            char_counts[char] = 1
    return max(char_counts, key=lambda k: char_counts[k])