import json

with open(f'./repos_all.json', 'r') as f:
    repo_json = json.load(f)


dictionary = {}

for i in range(len(repo_json)):
    if 'license' in repo_json[i][0].keys():
        if repo_json[i][0]['license'] == None:
            dictionary[repo_json[i][0]['full_name']] = None
        else:
            dictionary[repo_json[i][0]['full_name']] = repo_json[i][0]['license']['key']

with open(f'./license_map.json', 'w') as f:
    json.dump(dictionary, f)