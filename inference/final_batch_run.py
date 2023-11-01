"""
Interface for running locally inferenced models.
Takes these parameters:
num_gpus -> Number of GPUs in Cluster
gpus_per_script -> Assignment of GPUs per task
model_type -> What model to run
generation_version -> Backend version track
max_length -> Model max token length
max_generation -> Model max token output
PROMPT_AMOUNT -> Prompts numbers
use_summary_only -> distinguish between full sized and reduced prompts
"""

from transformers import AutoModelForCausalLM, AutoTokenizer
from tqdm import tqdm
from multiprocessing import Pool
import os, time, torch, argparse, transformers, re, tiktoken
import requests
import signal
import socket
import traceback
import io
import random

transformers.logging.set_verbosity_error()

num_gpus = 8
gpus_per_process = 1

model_name_or_path = "bigcode/santacoder"
generation_version = "v1"
prompt_basefolder = "data/prompts/Prompts"
base_folder_url = "data/generated"
max_length = 8192
max_generation = 256
PROMPT_AMOUNT = 20
use_summary_only = False
tolerance = 128

os.environ["HUGGING_FACE_HUB_TOKEN"] = "" # TODO: fill in an API key if necessary
# os.environ["TRANSFORMERS_CACHE"] = "/data" # uncomment this to set the model cache directory
discord_url = "DISCORD_WEBHOOK_URL"


base_folder_url = f"{base_folder_url}/{model_name_or_path}/{generation_version}"

message_id = None
def send_log(content):
    
    data = {
        "content": content
    }
    try:
        time.sleep(random.random()*2)
        requests.post(discord_url, data=data)
    except:
        time.sleep(1)
        requests.post(discord_url, data=data)
    
def send_update(content):
    if message_id is None:
        send_log("attempting update, but no message id")
        return
    data = {
        "content": content
    }
    new_url = discord_url + f"/messages/{message_id}"
    requests.patch(new_url, data=data)

def send_initial(content):
    data = {
        "content": content
    }
    new_url = discord_url + "?wait=true"
    global message_id
    try:
        response = requests.post(new_url, data=data)
        message_id = response.json()["id"]
    except Exception:
        time.sleep(1 + random.random()*3)
        response = requests.post(new_url, data=data)
        message_id = response.json()["id"]
        
    
    
def pbar_update(pbar, model, amount=1, file=None):
    hostname = socket.gethostname()
    pbar.update(amount)
    pbar.refresh()
    send_update(f"`[GPU{model.index}, {hostname}, {model.model_type}] [{pbar.n}/{pbar.total}]` {file}")
    
def adj_prompt(text, model, token_limit = 2000, save = False, dpath = "/home/ubuntu/CodeGen/BCE/AdjustedPrompts"):

    num_tokens = 0
    adj_prompt = ''

    is_file = False
    file_name = ''

    try:
        with open(text, 'r') as file:
            content = file.read()
            
        is_file = True
        file_name = os.path.basename(text)

    except Exception:
        content = text

    lines = content.split('\n')
    for _, line in enumerate(lines):
        s = line + '\n'

        num_tokens += model.get_num_tokens(s)

        if num_tokens > token_limit:
            s = s[:-1]
            break
        else:
            adj_prompt += s

    if save:
        if not os.path.exists(dpath):
            os.makedirs(dpath)

        if is_file:
            with open(os.path.join(dpath, file_name), 'w') as file:
                file.write(adj_prompt)

    return adj_prompt, num_tokens 


class Model:
    def __init__(self, index, model_type):
        self.index = index
        self.model_type = model_type

        self.device = torch.device(f"cuda:0")

        # TODO: model init, edit this
        self.tokenizer = AutoTokenizer.from_pretrained(model_type, cache_dir=os.environ["TRANSFORMERS_CACHE"])
        self.model = AutoModelForCausalLM.from_pretrained(model_type, trust_remote_code=True, cache_dir=os.environ["TRANSFORMERS_CACHE"], load_in_8bit=True, device_map="auto")

        self.inuse = False

    def predict(self, prompt, max_length) -> str:
        while self.inuse:
            time.sleep(0.1)
        self.inuse = True

        # TODO: prediction function, edit this. It should return the generated code given the prompt
        input_ids = self.tokenizer.encode(prompt, return_tensors="pt").to(self.device)

        output = self.model.generate(
            input_ids,
            max_length=max_length,
            do_sample=True,
            top_k=50,
            top_p=0.95,
            num_return_sequences=1,
            early_stopping=True,
            temperature=0.7,
            pad_token_id=self.tokenizer.eos_token_id,
        )

        self.inuse = False

        return self.tokenizer.decode(output[0], skip_special_tokens=True)

    def get_num_tokens(self, prompt):
        return len(self.tokenizer.encode(prompt, return_tensors="pt")[0])
    
    def isfree(self):
        return not self.inuse


def create_prompt(instruction: str):
    # TODO: change this function to create a prompt given the instruction
    # get index of last line without a # in it
    index = 0
    for line in instruction.split("\n"):
        if not line.startswith("#"):
            index += 1
        else:
            break

    # add another line after that line with a #
    instruction = instruction.split("\n")

    instruction.insert(index, "# Do not write any comments in your code.")
    instruction = "\n".join(instruction)
    
    # remove all non ascii characters and replace with spaces
    
    instruction = "".join([i if ord(i) < 128 else ' ' for i in instruction])
    
    return instruction


def generate_code(model: Model, filename, pbar):
    start_time = time.time()

    new_folder_url = os.path.join(base_folder_url, filename)

    # if the code has already been generated
    if os.path.isdir(new_folder_url):
        pbar_update(pbar, model, PROMPT_AMOUNT, file=filename)
        return time.time() - start_time

    with io.open(os.path.join(prompt_basefolder, filename + '.txt'), mode="r", encoding="utf-8") as f:

        prompt = create_prompt(f.read())
        prompt, _ = adj_prompt(prompt, token_limit=(max_length - max_generation - tolerance), model=model)

        generated_total_tokens = max_generation + model.get_num_tokens(prompt)

        try:

            if generated_total_tokens > max_length:
                pbar_update(pbar, model, PROMPT_AMOUNT, file=filename)
                

                outputs = [f"token limit exceeded {str(generated_total_tokens)} > {str(max_length)}"] * PROMPT_AMOUNT
                
            else:
                outputs = []
                broken=False
                for i in range(PROMPT_AMOUNT):
                    generation = model.predict(prompt, generated_total_tokens)
                    if os.path.isdir(new_folder_url):
                        broken=True
                        break

                    outputs.append(generation)

                    pbar_update(pbar, model, 1, file=filename)

                if broken:
                    return time.time() - start_time
            if not os.path.isdir(new_folder_url):
                os.makedirs(new_folder_url)

            for i in range(len(outputs)):
                result = outputs[i]

                result = result.replace(prompt, "")

                result = re.sub(r'[^\x00-\x7F]', ' ', result)

                with open(os.path.join(new_folder_url, str(i)), "w") as f:
                    
                    f.write(result)

        except Exception as e:

            print(e)

            if not os.path.isdir(new_folder_url):
                os.makedirs(new_folder_url)

            pbar_update(pbar, model, PROMPT_AMOUNT, file=filename)

            for i in range(PROMPT_AMOUNT):
                with open(os.path.join(new_folder_url, str(i)), "w") as f:

                    f.write("error:\n")
                    f.write(str(e))
    
    return time.time() - start_time
    

def run_subset(files, cuda_index, position):
    # this function is for multiprocessing
    hostname = socket.gethostname()

    print("Initializing model on GPU "+str(cuda_index)+"...")
    os.environ["CUDA_VISIBLE_DEVICES"] = str(cuda_index)
    send_initial(f'`[GPU{cuda_index}, {hostname}, {model_name_or_path}]` Initializing...')
    model = Model(cuda_index, model_name_or_path)
    

    gpu_desc_base = "GPU "+str(cuda_index)
    pbar = tqdm(total=len(files*PROMPT_AMOUNT), position=position, desc=gpu_desc_base)
    try:
        
        for i in range(len(files)):
            file = files[i]

            desc = gpu_desc_base + " - " + file[:10] + "..."
            pbar.set_description(desc)
            
            generate_code(model, file, pbar)
    except Exception as e:
        send_update(f"`[GPU{cuda_index}, {hostname}, {model_name_or_path}]` ERROR\n{traceback.format_exc()}")
        raise e
    send_update(f"`[GPU{cuda_index}, {hostname}, {model_name_or_path}]` Done")


def get_file_paths(root_dir):
    file_paths = []
    
    for subdir, _, files in os.walk(root_dir):
        for file in files:
            file_path = os.path.join(subdir, file)
                
            file_paths.append(file_path)

    file_paths = [os.path.relpath(path, root_dir) for path in file_paths]

    # only keep paths with prompts in them
    file_paths = [path for path in file_paths if ".txt" in path]

    if not use_summary_only:
        file_paths = [path for path in file_paths if "Rosalind" not in path]
    else:
        file_paths = [path for path in file_paths if "Rosalind" in path]

    file_paths = [path.split('.')[0] for path in file_paths]

    file_paths = [path for path in file_paths if not os.path.isdir(os.path.join(base_folder_url, path))]
    
    return file_paths


def signal_handler(sig, frame):
    print('stopped')
    hostname = socket.gethostname()
    send_log(f"Stopped {hostname}, was running model {model_name_or_path}")
    exit(0)
signal.signal(signal.SIGINT, signal_handler)


# use multiprocessing to generate code
if __name__ == "__main__":
    if use_summary_only:
        print("Only generating Rosalind prompts")
    files = get_file_paths(prompt_basefolder)
    files.sort()

    if not os.path.isdir(base_folder_url):
        os.makedirs(base_folder_url)
    
    # parse arguments
    parser = argparse.ArgumentParser()

    # add argument for --firstrun
    parser.add_argument("--firstrun", help="set to true if this is the first time you are running this script", action="store_true")
    # add all global variables as arguments
    parser.add_argument("--num_gpus", help="number of GPUs in cluster", type=int, default=num_gpus)
    parser.add_argument("--gpus_per_process", help="number of GPUs per process", type=int, default=gpus_per_process)
    parser.add_argument("--model_name_or_path", help="model name or path", type=str, default=model_name_or_path)
    parser.add_argument("--generation_version", help="generation version", type=str, default=generation_version)
    parser.add_argument("--max_length", help="max length", type=int, default=max_length)
    parser.add_argument("--max_generation", help="max generation", type=int, default=max_generation)
    parser.add_argument("--PROMPT_AMOUNT", help="prompt amount", type=int, default=PROMPT_AMOUNT)
    parser.add_argument("--use_summary_only", help="use summary only", type=bool, default=use_summary_only)
    parser.add_argument("--tolerance", help="tolerance", type=int, default=tolerance)
    parser.add_argument("--discord_url", help="discord url", type=str, default=discord_url)
    parser.add_argument("--base_folder_url", help="base folder url", type=str, default=base_folder_url)
    parser.add_argument("--prompt_basefolder", help="prompt basefolder", type=str, default=prompt_basefolder)
    args = parser.parse_args()

    # set all global variables to the arguments
    num_gpus = args.num_gpus
    gpus_per_process = args.gpus_per_process
    model_name_or_path = args.model_name_or_path
    generation_version = args.generation_version
    max_length = args.max_length
    max_generation = args.max_generation
    PROMPT_AMOUNT = args.PROMPT_AMOUNT
    use_summary_only = args.use_summary_only
    tolerance = args.tolerance
    discord_url = args.discord_url
    base_folder_url = args.base_folder_url
    prompt_basefolder = args.prompt_basefolder


    if args.firstrun:

        print("First run detected. Initializing models...")

        model = Model(0, model_name_or_path)

        print("Done initializing models")
        exit(0)
    
    hostname = socket.gethostname()
    # Initialize cuda devices and models
    cuda_devices = [','.join(map(str, range(i, i + gpus_per_process))) for i in range(0, num_gpus, gpus_per_process)]
    send_log(f"Started {hostname}, running model {model_name_or_path} on {len(cuda_devices)} GPUs")
    num_subsets = len(cuda_devices)

    subsets = []
    for i in range(num_subsets):
        subsets.append((files[i::num_subsets], cuda_devices[i], i))

    with Pool(num_subsets) as p:
        p.starmap(run_subset, subsets)

    print("Done generating code")
    send_log(f"Done generating code on {hostname}, running model {model_name_or_path} on {len(cuda_devices)} GPUs")