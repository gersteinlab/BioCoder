import pandas as pd

df = pd.read_json('data/parsing/keyword_scrape/outputs_test.json')

print(len(df))