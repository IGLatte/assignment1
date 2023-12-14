import pandas as pd

reviews_data = pd.read_csv('data/amazon-reviews.csv')

reviews_in_city = reviews_data
word_counts = reviews_in_city['review'].str.split(expand=True).stack().value_counts()
word_counts_dict = dict(word_counts)
# word_counts[:] = 0
print(pd.__version__)