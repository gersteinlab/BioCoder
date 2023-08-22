# [BioCoder](https://biocoder-benchmark.github.io)

BioCoder is a challenging bioinformatics code generation benchmark for examining the capabilities of state-of-the-art large language models (LLMs)

# Project Structure

The repository comprises of 4 main parts: evaluation, inference, parsing, and data. We use the data folder to store results between each step in the operations. Ensure that each step is run from the root directory, i.e. `python3 parsing/parse.py` and not `cd parsing && python3 parse.py` in order to avoid issues with relative paths.

Each section is described below.

## Parsing

The parsing section contains the code used to analyze, parse, and extract functions from the repositories.

Begin the process by going through a list of GitHub repositories. Download the list of repositories (named `pone.0205898.s005.xlsx`) from this paper first, then place it in the data directory.

[A large-scale analysis of bioinformatics code on GitHub](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0205898)

Then, open the notebook in GithubAnalysis to start the repository metadata gathering process. Note that this may fully clone all available GitHub repositories in the list. This may take a long time. Then, use the scripts in FunctionSelection to filter the GitHub functions accordingly.

Next, we need to do the function extraction step. We have created parsers for Java and Python so far. The corresponding documentation can be found in the respective folders:
- [Java Parsing](parsing/FunctionExtractors/JavaFunctionExtractor/README.md)
- [Python Parsing](parsing/FunctionExtractors/PythonFunctionExtractor/README.md)

After parsing, the output should be a JSON format with consistent properties across all languages. The following columns are guaranteed, however they may be extra columns for specific languages:
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

## Inference
This section consists of all files necessary to generate the outputs across different models.

For convenience on running the script across multiple machines (output generation takes a long time, especially for these prompts), we have included a requirements.txt with the exact dependencies that we used.

The following steps are required to generate the outputs. They are all marked with `TODO` in the code.
- Change the parameters at the top of the code to fit your environment.
- Change the model name and initialization code starting with the line `# TODO: model init, edit this`
- Change the prediction code starting with the line `# TODO: prediction code, edit this`

Then, install the requirements with `python -m pip install inference/requirements.txt`, and run with `python inference/final_batch_run.py`.



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



## datasets

We provide our completed public dataset in this GitHub repository. It consists of the following files:

* `java_hidden.json`: A JSON of the 1243 Java functions that make up the Java part of the "hidden" dataset of the benchmark
* `java_public.json`: A JSON of the 50 Java functions that make up the Java part of the "public" dataset of the benchmark
* `java_simlar.json`: A JSON of the 50 Java functions that make up the Java part of the "similar" dataset of the benchmark
* `python_hidden.json`: A JSON of the 1026 Python functions that make up the Python part of the "hidden" dataset of the benchmark
* `python_public.json`: A JSON of the 50 Python functions that make up the Python part of the "public" dataset of the benchmark
* `python_simlar.json`: A JSON of the 50 Python functions that make up the Python part of the "similar" dataset of the benchmark
* `rosalind.json`: A JSON of the 253 Rosalind functions that make up the Rosalind part of the "public" dataset of the benchmark
