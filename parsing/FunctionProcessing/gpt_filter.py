import openai
import tenacity
from tenacity import retry, stop_after_attempt, wait_exponential  
import pandas as pd
filepath = "/home/ubuntu/CodeGen/BCE/FileStructure/Python/PythonSelected/all_functions.json"
data = pd.read_json(filepath)
gpt_outputs = []
openai.api_key = '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'  
test = data['content'].iloc[0]
@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=4, max=120))
def get_gpt_response(index):
  completion = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
      {"role": "user", "content": f"""I will provide you with a prompt to a function below these instructions. You will output exactly as follows, with the list as well. Text encased in <like this> will be replaced by your response, and text encased in (like this) is just a description for the response that you do not need to type up:
  (a) <Boolean> (Is it bioinformatics related?)
  (b) <words> (Give a list of 5 keywords of why it is bioinformatics related)
  (c) <integer> (Your confidence from 0 to 100 that your response in A is accurate, so for example, if you believe strongly that it is not bioinformatics related, you should also rate a high confidence level)
  The code must explicitly reference some bioinformatics methodology, terminology, or process. For example, an AVL Tree would not be a valid bioinformatics function, while a FASTQ processor would. The keywords are defined as important words that allowed you to make the determination that the function is bioinformatics related. The confidence should be your estimate of how confident you are of your responses.

  Make sure that in your response is explicitly as follows in the directions. Part A should only be one word and a boolean, either True or False. Part B should only be 5 words, no additional information, Part C should only be a single integer, from 0 to 100, it is a measure of your confidence in your response to Part A.

  After selecting keywords, please reverify that the words you used to make the decision for Part A is actually bioinformatics related.
  Again, as clarification, I will be providing the function. 

  The responses should be formatted as a list:
  Entry 1: The response to part A converted into a string
  Entry 2: A list of 5 words which are strings from the response to Part B
  Entry 3: The integer response to part C converted to a string
  Therefore, your output should follow this guideline. This will be your only output, there should be no additional outputs beyond the one highlighted in this prompt.

  Prompt begins here:
  {index}

  Prompt ends here.
  Give the output to the above code encased in "Prompt begins here:" and "Prompt ends here." Your keyword search should only encompass the words in the prompt, and ensure that keywords are related to bioinformatics, not statistics.
  """}]
  )
  return completion.choices[0].message['content']

print(get_gpt_response(test))


"""
for index, row in tqdm(data.iterrows(), total=len(data), desc="Processing rows"):
  gpt_outputs.append(get_gpt_response(index))
"""