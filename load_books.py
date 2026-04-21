from datasets import load_dataset
ds = load_dataset("stanfordnlp/imdb", split="train")
print(ds[0])
