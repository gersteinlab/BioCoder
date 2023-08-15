import pandas as pd
import json

package = 'htsint'

df = pd.read_json(f'../json_files/{package}_functions.json')

with open(f"../json_files/{package}_file_imports.json", "r") as infile:
    file_imports = json.load(infile)

prompts = []

for i in range(len(df)):
    prompt = '# Python 3\n'
    for external_import in df.iloc[i].imports:
        prompt += '"""\n'
        prompt += f'{external_import} exposes the following functions and classes:\n\n'
        prompt += file_imports[external_import][0]
        prompt += '"""\n'
    prompt += '"""\nThe following functions and classes will also be exposed:\n\n'
    prompt += file_imports[df.iloc[i].packageName][0]
    prompt += '"""\n\n'
    prompt += file_imports[df.iloc[i].packageName][1]
    prompt += '# Complete the following function\n'
    prompt += df.iloc[i].signature + ':\n'
    if df.iloc[i].comment != None:
        prompt += '\t"""\n'
        for line in df.iloc[i].comment.split('\n'):
            prompt += '\t' + line + '\n'
        prompt += '\t"""\n'
    prompts.append(prompt)

df['prompts'] = prompts

df.to_json(f'../json_files/{package}_functions.json')