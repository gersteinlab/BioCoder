import pandas as pd
import os
import json

directory = os.environ['PACKAGE_DIRECTORY']
package_name = os.environ['PACKAGE_NAME']
author = os.environ['REPO_AUTHOR']

project = directory.split('/')[2]

df = pd.read_json(f'./python-functions/{author},{project},{package_name}_functions.json')

with open(f'./license_map.json', 'r') as f:
    repo_json = json.load(f)

license = []
for i in range(len(df)):
    if df.iloc[i].repoAuthor + '/' + df.iloc[i].repoName in repo_json.keys():
        license.append(repo_json[df.iloc[i].repoAuthor + '/' + df.iloc[i].repoName])
    else:
        license.append(None)

df['license'] = license

df.to_json(f'./python-functions/{author},{project},{package_name}_functions.json')