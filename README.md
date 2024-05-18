# BioCoder

<p align="center"><a href="https://arxiv.org/abs/2308.16458">[📄 Paper]</a>
<a href="https://biocoder-benchmark.github.io">[🌐 Website]</a>

BioCoder is a challenging bioinformatics code generation benchmark for examining the capabilities of state-of-the-art large language models (LLMs).



# Project Structure

The repository comprises 4 main parts: evaluation, inference, parsing, and data. We use the data folder to store results between each step in the operations. Ensure that each step is run from the root directory, i.e. `python3 parsing/parse.py` and not `cd parsing && python3 parse.py` in order to avoid issues with relative paths.

Each section is described below.

## Parsing

The parsing section contains the code used to analyze, parse, and extract functions from the repositories.

Begin the process by going through a list of GitHub repositories. Download the list of repositories (named `pone.0205898.s005.xlsx`) from this paper first, then place it in the data directory.

[A large-scale analysis of bioinformatics code on GitHub](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0205898)

Then, open the notebook in GithubAnalysis to start the repository metadata-gathering process. Note that this may fully clone all available GitHub repositories in the list. This may take a long time. Then, use the scripts in FunctionSelection to filter the GitHub functions accordingly.

Next, we need to do the function extraction step. We have created parsers for Java and Python so far. The corresponding documentation can be found in the respective folders:
- [Java Parsing](parsing/FunctionExtractors/JavaFunctionExtractor/README.md)
- [Python Parsing](parsing/FunctionExtractors/PythonFunctionExtractor/README.md)

After parsing, the output should be a JSON format with consistent properties across all languages. The following columns are guaranteed, however, they may be extra columns for specific languages:
* `function_id`: A unique identifier for the function. This is the hashcode of the function's signature.
* `numParams`: The number of parameters the function has.
* `numLines`: The number of lines the function spans.
* `numChars`: The number of characters the function spans.
* `lineStart`: The line number the function starts on.
* `lineEnd`: The line number the function ends on.
* `returnType`: The return type of the function.
* `params`: A list of the function's parameters.
* `parentClass`: The class the function is in.
* `filePath`: The path to the file the function is in.
* `signature`: The function's signature.
* `content`: The function's content.
* `comment`: The function's comment.
* `numCommentLines`: The number of lines the function's comment spans.
* `numCommentChars`: The number of characters the function's comment spans.
* `packageName`: The package the function is in.
* `repoName`: The repository the function is in.
* `imports`: A list of the function's imports.
* `additionalImports`: A list of the function's additional imports.
* `intraClassFieldsUsed`: A list of the function's intra-class fields used.
* `intraClassFieldsUsed`: A list of the function's intra-class fields used.

Then, use the scripts in FunctionProcessing to process the functions. This includes filtering out functions that are too short, too long, or have too many parameters. It also includes filtering out functions that are too similar to each other. It also includes scripts to generate summaries, prompts, and other necessary prompt data with ChatGPT

Note that there are also some scripts that assist with the manual annotation of context generation. These are not necessary for the benchmark, but are included for completeness.

### Custom Python Parsing

In order to perform custom parsing on a Python repository, one can use the `parse.py` file under `parsing/FunctionExtractors/parse.py`. Before running one must make sure that a `json_files` folder must be in the same repository as `parse.py` as well as a`github_repos` folder must be in the same repository as `parse.py`. In the `github_repos` folder, one can include the physical repositories that one desires to parse. In order to run `parse.py` one must define the `PACKAGE_DIRECTORY`, `PACKAGE_NAME`, and `REPO_AUTHOR` variables. For instance, if you want to parse the files under the `Bio/AlignIO` folder in the `biopython` repository, with the author of the repository also being `biopython`, then you would set
```python
PACKAGE_DIRECTORY = biopython/Bio/AlignIO
PACKAGE_NAME = AlignIO
REPO_AUTHOR = biopython
```
and here is some sample code to run the parser:
```python
import os, subprocess

directory = 'biopython/Bio/AlignIO'
author = 'biopython'

os.environ['PACKAGE_DIRECTORY'] = os.path.join('./github_repos', directory)
package_name = directory.split('/')[-1]
os.environ['PACKAGE_NAME'] = package_name
os.environ['REPO_AUTHOR'] = author
subprocess.run('python3 parse.py', shell=True)
```

The result will be a file named `{PACKAGE_NAME}_functions.json` which includes the main json file containing all the parsed functions. There will also be a file named `AlignIO_file_imports.json` which includes the import packages necessary to complete the parsing.

## Loading the dataset
The dataset is located in the `datasets` folder. Most of the following steps require the data to be structured as follows:
```
/data/Prompts/
- [Prompt Type 1]
  - [Prompt ID 1]
  - [Prompt ID 2]
  - ...
  - [Prompt ID N]
- [Prompt Type 2]
    - [Prompt ID 1]
    - [Prompt ID 2]
    - ...
    - [Prompt ID N]
- ...
```

We have already parsed the public dataset in this format. Just extract it with 
```bash
unzip datasets/Prompts.zip -d data/
```

## Inference
This section consists of all files necessary to generate the outputs across different models.

For convenience on running the script across multiple machines (output generation takes a long time, especially for these prompts), we have included a requirements.txt with the exact dependencies that we used.

The following arguments are available:

* `--num_gpus`: The number of GPUs in the cluster. This is used to determine the number of processes to spawn.
* `--gpus_per_process`: The number of GPUs per process. This is used to determine the number of processes to spawn.
* `--model_name_or_path`: The model name or path to use. This is used to determine the model to use.
* `--generation_version`: The generation version to use. This is used to determine the generation version to use.
* `--max_length`: The maximum length of the output. This is used to determine the maximum length of the output.
* `--max_generation`: The maximum number of generations to perform. This is used to determine the maximum number of generations to perform.
* `--PROMPT_AMOUNT`: The number of prompts to generate. This is used to determine the number of prompts to generate.
* `--use_summary_only`: Whether to use the summary only. This is used to determine whether to use the summary only.
* `--tolerance`: The tolerance to use. This is used to determine the tolerance to use.
* `--base_folder_url`: The base folder URL to use. This is used to determine the base folder URL to use.
* `--prompt_basefolder`: The prompt basefolder to use. This is used to determine the prompt basefolder to use.

After installing the dependencies, you can install everything with `pip3 install -r requirements.txt`.

Then, run the following command to generate the outputs:

```bash
python3 inference/final_batch_run.py --num_gpus 8 --gpus_per_process 1 --model_name_or_path bigcode/starcoder --generation_version 1 --max_length 8192 --max_generation 200 --PROMPT_AMOUNT 20 --use_summary_only True --tolerance 0.9 --base_folder_url data/ --prompt_basefolder prompts
```




# Evaluation
### Setting up the evaluation framework
The evaluation framework utilizes a combination of Lambda and SQS to assign tasks across multiple workers. The workers are Docker containers that are spun up on demand. The Docker containers are spun up repeatedly and query the Lambda function for tasks to perform. DynamoDB is used to store the results.

We will publish a version that runs completely locally in the future.

1. Create an AWS account
2. Create an AWS Lambda function with the following parameters:
  - Memory: 3072MB
  - Timeout: 1 minute
  - Enable Function URL
  - Python 3.9
  - Execution Role: Add the roles AmazonDynamoDBFullAccess, AmazonS3FullAccess, AmazonSQSFullAccess (although permission boundaries can be limited)
3. Copy the contents of `CentralServer/lambda_queue_handler.py` into the Lambda function
4. Click Deploy

5. Create an EC2 Launch Template with the following settings:
6. Create two SQS queues, for example, one named `bioqueue` and one named `bioqueue-inprogress`
7. Create an S3 bucket, for example, named `biodata` (names are globally unique so these names might not be available)
8. Create a DynamoDB table with the following settings:
  - Primary key: `test_case_id` (String)
  - Any capacity settings (would recommend on-demand)
  - Enable auto scaling

Load test cases with the following command:

`PROD=true python evaluation/TestCaseLoader/upload_test_cases.py`

Create a Docker image with `evaluation/DockerServers/Dockerfile`

### Setting up Rosalind Evaluation Framework

1. First do all the Rosalind evaluations in the folder named "TestRosalind", and ensure that the following files are available: "run_script.sh", "skeleton.py", and "tester.py"
2. Make sure the code generation outputs are in a folder called "outputs" with the following structure: under "outputs" there is a folder for each Rosalind problem, i.e. there will be a folder named "2sat", a folder named "2sum", etc. Under each of these folders there will be 20 code generation text files, numbered "1.txt" through "20.txt". Here is a visual representation
  
outputs/<br>
├─ 2sat/<br>
│  &nbsp;├─ 1.txt<br>
│  &nbsp;├─ 2.txt<br>
│  &nbsp;...<br>
│  &nbsp;├─ 20.txt<br>
├─ 2sum/<br>
├─ afrq/<br>
,,,

3. When the "outputs" folder is currently formated as explained above, you can run the "tester.py" file under "TestRosalind". After this file finishes running, there will be a "results.json" file that stores a spreadsheet of the results of the code generation outputs. There are three columns: "Problem", "Generation", and "Passed". "Problem" indicates the name of the problem that was tested, "Generation" indicates the generation number, and "Passed" will be a boolean of whether the specified generation number of the specified problem actually resulted in accurate code. For instance if a row in the spreadsheet is ["2sat", 3, True], then this means that the generated code in "TestRosalind/outputs/2sat/3.txt" is correct and passes the problem.

4. Here is some sample code that can be used to extract Pass@K results from the "results.json" file

```python
import numpy as np
import pandas as pd
import os

def pass_at_k(n, c, k):
    if n - c < k: return 1.0
    return 1.0 - np.prod(1.0 - k / np.arange(n - c + 1, n + 1))

df = pd.read_json('results.json')

pk_df = pd.DataFrame(columns=['Problem', 'NumPassed', 'PassAt1', 'PassAt5', 'PassAt10', 'PassAt20'])

num_passed = {}
for prob in os.listdir('./TestRosalind/outputs'):
    num_passed[prob] = 0

for _, row in df.iterrows():
    if row['Passed']:
        num_passed[row['Problem']] += 1

for prob in num_passed.keys():
    c = num_passed[prob]
    pk_df.loc[len(pk_df)] = [prob, c, pass_at_k(20, c, 1), pass_at_k(20, c, 5), pass_at_k(20, c, 10), pass_at_k(20, c, 20)]

print(pk_df['PassAt1'].mean())
print(pk_df['PassAt5'].mean())
print(pk_df['PassAt10'].mean())
print(pk_df['PassAt20'].mean())
```

## Datasets

We provide our completed public dataset in this GitHub repository. It consists of the following files:

* `java_hidden.json`: A JSON of the 1243 Java functions that make up the Java part of the "hidden" dataset of the benchmark
* `java_public.json`: A JSON of the 50 Java functions that make up the Java part of the "public" dataset of the benchmark
* `java_simlar.json`: A JSON of the 50 Java functions that make up the Java part of the "similar" dataset of the benchmark
* `python_hidden.json`: A JSON of the 1026 Python functions that make up the Python part of the "hidden" dataset of the benchmark
* `python_public.json`: A JSON of the 50 Python functions that make up the Python part of the "public" dataset of the benchmark
* `python_simlar.json`: A JSON of the 50 Python functions that make up the Python part of the "similar" dataset of the benchmark
* `rosalind.json`: A JSON of the 253 Rosalind functions that make up the Rosalind part of the "public" dataset of the benchmark

## Citation
If you find our work useful in your research, please kindly consider cite:
```
@article{tang2023biocoder,
  title={BioCoder: A Benchmark for Bioinformatics Code Generation with Large Language Models},
  author={Tang, Xiangru and Qian, Bill and Gao, Rick and Chen, Jiakang and Chen, Xinyun and Gerstein, Mark},
  journal={Bioinformatics},
  year={2024},
  publisher={Oxford University Press}
}
```
