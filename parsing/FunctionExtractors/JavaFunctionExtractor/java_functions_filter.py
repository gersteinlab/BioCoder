import pandas as pd
import json

import os
import pandas as pd
import numpy as np
from nltk.probability import FreqDist
import tiktoken

print('starting')
# TODO: change url
with open("methods.json", "r") as f:
    methods = json.load(f)

arr = []
methods=methods["methods"]
for method in methods:
    arr.append(method)
  
df = pd.DataFrame(arr)



print(df.columns)
num_rows_before = df.shape[0]
print(num_rows_before)
df = df[df['numCommentLines'] > 0]
# TODO: offset the numLines by the size of the comment and signature
# # IMPORTANT ^^^^^^^^^^^^^^^^^^


df = df[df['numLines'] -df['numCommentLines'] > 5]
df = df[df['numLines'] - df['numCommentLines'] < 10]






function_hashes = []

for i in range(len(df)):
    function_hashes.append(hash(df.iloc[i].filePath + df.iloc[i].signature))

df['hash'] = function_hashes

df.to_json('outputs_with_hashes.json')

df = pd.read_json('outputs_with_hashes.json')

print(df.columns)


