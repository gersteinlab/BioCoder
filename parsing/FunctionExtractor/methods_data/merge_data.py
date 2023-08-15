import json
import pandas as pd
import os
import hashlib

def primitive(arg1):
    return arg1 == 'String' or arg1 == 'int' or arg1 == 'boolean' or arg1 == 'long' or arg1 == 'float' or arg1 == 'double' or arg1 == 'char'

directory = '/home/ubuntu/CodeGen/BCE/FunctionExtractor/methods_data'

save_location = '/home/ubuntu/CodeGen/BCE/Java/java_functions.json'

df = pd.DataFrame()

for filename in os.listdir(directory):
    if os.path.isfile(os.path.join(directory, filename)) and filename.split('.')[-1] == 'json':
        full_path = os.path.join(directory, filename)

        with open(full_path, 'r') as f:
            tmp = pd.DataFrame(json.loads(f.read())['methods'])

        df = pd.concat([df, tmp], ignore_index=True)

df = df[df['numLines'] < 30]
df = df[df['numLines'] >= 5]

df = df[(df['returnType'] == 'String') | (df['returnType'] == 'int') | (df['returnType'] == 'boolean') | (df['returnType'] == 'int') | (df['returnType'] == 'long') | (df['returnType'] == 'float') | (df['returnType'] == 'double') | (df['returnType'] == 'char')]

mask = []
for row_idx, row in df.iterrows():
    keep_row = True
    for param in row['params']:
        if not primitive(param.split(' ')[0]):
            keep_row = False
            break
    mask.append(keep_row)
    

df = df[mask]

hash_idx = []

sha256_hash = hashlib.sha256()

for row_idx, row in df.iterrows():
    hash_str = '_'.join([row['filePath'], str(row['lineStart']), str(row['lineEnd']), row['content'], 'java'])

    sha256_hash.update(hash_str.encode('utf-8'))

    hash_idx.append(sha256_hash.hexdigest())

df['hashIdx'] = hash_idx

df.set_index('hashIdx', inplace=True)

df.to_json(save_location)