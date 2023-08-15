from fuzzer_tester import FuzzerTester
import os
from tqdm import tqdm

cnt = 1
startAt = 146

context_path = '/home/ubuntu/CodeGen/BCE/Java/Context/'
generated_path = '/home/ubuntu/CodeGen/BCE/Java/GeneratedCode/'
golden_path = '/home/ubuntu/CodeGen/BCE/Java/GoldenCode/'

for filename in tqdm(os.listdir('/home/ubuntu/CodeGen/BCE/Java/Context')):
    # if cnt < startAt:
    #     cnt += 1
    #     continue 

    try:
        results = FuzzerTester(
            gen_code_test_file='Main',
            golden_code_test_file='Main',
            language='java',
            test_program='./run_java.sh'
        ).test_functions(
            context_path=os.path.join(context_path, filename),
            generated_path=os.path.join(generated_path, filename),
            golden_path=os.path.join(golden_path, filename)
        )

        test_failed = False

        for item in results:
            if not item[0]:
                print(filename)
                print(results)

                test_failed = True

                break       

        if test_failed:
            break 

    except Exception as e:
            print(filename)
            raise e

    finally:
        cnt += 1