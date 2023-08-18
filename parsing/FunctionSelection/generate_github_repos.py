"""
This script collects information about multiple GitHub repositories using the GitHub API.
It reads a list of repository URLs from a file, makes API requests to fetch data for each repository,
including repository details and language statistics, and then saves the collected data as a pickled file.
Please add your own API key for github, the authorization and X-GitHub-API-Version
"""
import requests
import json
import pickle


API_KEY = 'API_KEY'
#read whole file to a string

URL = 'https://api.github.com/repos/'
repo_jsons = []

i = 1
with open('./all_repos.txt', 'r') as f:
    for line in f:
        print(i)
        headers = {
            "Authorization": "YOUR INFORMATION HERE",
            "X-GitHub-Api-Version": "VERSION HERE"
        }
        r1 = requests.get(URL + line[:-1], headers=headers)
        r1 = json.loads(r1.text)
        r2 = requests.get(URL + line[:-1] + '/languages', headers=headers)
        r2 = json.loads(r2.text)
        repo_jsons.append((r1, r2))
        i += 1

with open('repo_jsons.pkl', 'wb') as f:
    pickle.dump(repo_jsons, f)

