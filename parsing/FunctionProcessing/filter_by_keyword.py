from tqdm import tqdm
import csv
import pandas as pd

# Replace 'input.csv' with the name of your CSV file
csv_file = '/home/ubuntu/CodeGen/BCE/FunctionProcessing/dictionary.txt' # Replace with your path to dictionary of keywords
inputs_path = '/home/ubuntu/CodeGen/BCE/FileStructure/Python/HelperFunctions/final_filtered-py_func.json' # Replace with your path to Python functions
inputs = pd.read_json(inputs_path)

print(len(inputs))

# Read the words from the CSV file into a list
words = []
with open(csv_file, 'r', newline='') as f:
    reader = csv.reader(f)
    next(reader)  # Skip the header
    for row in reader:
        words.append(row[0])  # Add the word from the first column of each row

def word_in_dictionary(input_string, dictionary): 
    count = 0
    for word in dictionary:
        if word in input_string:
            count += 1
            if count >= 15:
                return True
    return False

# Example usage:
outputs_df = pd.DataFrame()
track = 0
for i in tqdm(range(len(inputs))):
    input_string = inputs['prompt'].iloc[i]
    
    if word_in_dictionary(input_string, words):
        outputs_df = pd.concat([outputs_df, inputs.loc[[i]]], axis=0)
        track += 1
        if track % 25 == 0:
            print(outputs_df.iloc[[track - 1]])
            print(track)

# Rename the columns to ensure they are unique
outputs_df = outputs_df.rename(columns={'generated_code': 'code'})

# Convert the DataFrame to JSON with unique column names
outputs_df.to_json('outputs_test.json', orient='columns')