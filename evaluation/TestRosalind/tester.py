import multiprocessing, os, shutil, signal, subprocess
from pathlib import Path
import pandas as pd
from tqdm.contrib.concurrent import process_map

def timeout_handler(signum, frame):
    raise TimeoutError("Function execution timed out")

def worker(args):
    prob, gen_num = args

    base_path = Path('/home/ubuntu/CodeGen/rebuttal_jiakang/TestRosalind')
    output_path = base_path / 'outputs'
    skeleton_path = base_path / 'skeleton.py'
    testcase_path = base_path / 'testcases'

    MAX_TIME = 60

    with open(output_path / prob / f'{gen_num}.txt') as f:
        output = f.read()
        
    tmp_path = base_path / f'tmp{prob}{gen_num}'
    tmp_path.mkdir(parents=True, exist_ok=True)

    with open(skeleton_path) as f:
        skeleton = f.read()
    gen_code = output + '\n\n\n\n' + skeleton

    with open(tmp_path / 'generated.py', 'w') as f:
        f.write(gen_code)

    with open(testcase_path / f'rosalind_{prob}.txt') as f:
        testcase = f.read()
    with open(tmp_path / 'input.txt', 'w') as f:
        f.write(testcase)
    
    with open(testcase_path / f'rosalind_{prob}sol.txt') as f:
        expected_output = f.read()
    
    with open(base_path / f'run_script.sh') as f:
        script = f.read()
    with open(tmp_path / 'run_script.sh', 'w') as f:
        f.write(script)

    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(MAX_TIME)

    run_command_str = 'chmod +x run_script.sh && ./run_script.sh generated.py'

    successful_run = True
    try:
        subprocess.run(run_command_str, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=tmp_path, shell=True)
    except TimeoutError:
        successful_run = False
    except:
        successful_run = False
    finally:
        signal.alarm(0)
    
    passed_test = False
    if successful_run:
        gen_path = tmp_path / 'output.txt'
        if gen_path.exists() and gen_path.is_file():
            with open(gen_path) as f:
                output = f.read()
                if output.strip() == expected_output.strip():
                    passed_test = True

    if tmp_path.exists() and tmp_path.is_dir():
        shutil.rmtree(tmp_path)

    return [prob, gen_num, passed_test]

if __name__ == '__main__':
    base_path = Path('/home/ubuntu/CodeGen/rebuttal_jiakang/TestRosalind')
    output_path = base_path / 'outputs'

    data = []
    for prob in os.listdir(output_path):
        for i in range(1, 21):
            data.append((prob, i))

    results = process_map(worker, data, max_workers=multiprocessing.cpu_count(), chunksize=10)

    df = pd.DataFrame(columns=['Problem', 'Generation', 'Passed'])
    for result in results:
        df.loc[len(df)] = result
    df.to_json(base_path / 'results.json')