import os
import json
import pandas as pd
import hashlib

allowed_types = ['String', 'int', 'boolean', 'long', 'float', 'double', 'char']
def is_primitive(arg1):
    return arg1 in allowed_types

def load_data_from_directory(directory):
    df = pd.DataFrame()
    for filename in os.listdir(directory):
        if os.path.isfile(os.path.join(directory, filename)) and filename.split('.')[-1] == 'json':
            full_path = os.path.join(directory, filename)
            with open(full_path, 'r') as f:
                tmp = pd.DataFrame(json.loads(f.read())['methods'])
            df = pd.concat([df, tmp], ignore_index=True)
    return df

def filter_data(df):
    df = df[(df['numLines'] < 30) & (df['numLines'] >= 5)]
    df = df[df['returnType'].isin(allowed_types)]
    return df

def filter_by_params(df):
    mask = []
    for row_idx, row in df.iterrows():
        keep_row = all(is_primitive(param.split(' ')[0]) for param in row['params'])
        mask.append(keep_row)
    return df[mask]

def add_hash_index(df):
    sha256_hash = hashlib.sha256()
    hash_idx = []
    for row_idx, row in df.iterrows():
        hash_str = '_'.join([row['filePath'], str(row['lineStart']), str(row['lineEnd']), row['content'], 'java'])
        sha256_hash.update(hash_str.encode('utf-8'))
        hash_idx.append(sha256_hash.hexdigest())
    df['hashIdx'] = hash_idx
    df.set_index('hashIdx', inplace=True)
    return df

def save_to_json(df, save_location):
    df.to_json(save_location)

def main():
    directory = 'parsing/JavaFunctionExtractor/methods_data'
    save_location = 'data/parsing/languages/Java/java_functions.json'
    df = load_data_from_directory(directory)
    df = filter_data(df)
    df = filter_by_params(df)
    df = add_hash_index(df)
    save_to_json(df, save_location)

if __name__ == "__main__":
    main()
