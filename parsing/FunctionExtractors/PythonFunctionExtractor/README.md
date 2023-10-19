# Python Parsing Instructions

## Step 1

In this folder create a new folder called `github_repos`, and clone all the repositories 
listed in [github-repos.csv](https://github.com/gersteinlab/BioCoder/blob/main/parsing/FunctionSelection/github-repos.csv) into the newly created `github_repos` folder.

## Step 2

Then copy [parse_github_repos.py](https://github.com/gersteinlab/BioCoder/blob/main/parsing/FunctionSelection/parse_github_repos.py) into this folder. 

## Step 3

In this folder create a new folder called `json_files`, and then run `python3 parse_github_repos.py`. For each repo, the parsed functions will be in a file called
`./json_files/{repo_name}_functions.json` and the parsed imports will be in a file called `./json_files/{repo_name}_file_imports.json`.
