import pandas as pd
import requests
import json
import pickle

# df = pd.read_csv(r'./repo_and_article_info-Table 1.csv')

API_KEY = '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'
 
#read whole file to a string

URL = 'https://api.github.com/repos/'
repo_jsons = []

i = 1
with open('./all_repos.txt', 'r') as f:
    for line in f:
        print(i)
        headers = {
            "Authorization": "Bearer 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",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        r1 = requests.get(URL + line[:-1], headers=headers)
        r1 = json.loads(r1.text)
        r2 = requests.get(URL + line[:-1] + '/languages', headers=headers)
        r2 = json.loads(r2.text)
        repo_jsons.append((r1, r2))
        i += 1

with open('repo_jsons.pkl', 'wb') as f:
    pickle.dump(repo_jsons, f)

