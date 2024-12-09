import re
from nltk.stem import PorterStemmer
import pickle
import time
import shelve
import math
import numpy as np
from posting import Posting
N_docs = 38679
table = {}
with open('index_table.pk1', 'rb') as f:
    table = pickle.load(f)
index = open('index.bin' , 'rb')

def compute_tf_idf(tokens, tf, df, N=N_docs):
    tf_idf = []
    for i in range(len(tokens)):
        if i < len(tf) and i < len(df) and df[i] > 0:  # valid index, nonzero df
            tf_idf.append((1 + math.log(tf[i])) * (math.log(N / df[i])))
        else:
            print(f"Skipping term '{tokens[i]}' due to zero document frequency or missing TF/DF.")
            tf_idf.append(0)  # 0 score for invalid terms
    magnitude = math.sqrt(sum(x**2 for x in tf_idf))
    return [x / magnitude for x in tf_idf] if magnitude != 0 else tf_idf


def make_query(string):
    index = open('index.bin', 'rb')
    english_text = re.sub(r"[^a-z0-9\s]", " ", string)
    words = english_text.split()
    ps = PorterStemmer()
    tokenized_query = {}
    query_list = []
    doc_freq = []

    for word in words:
        token = ps.stem(word)
        if token in tokenized_query.keys():
            tokenized_query[token] += 1
        else:
            tokenized_query[token] = 1
            query_list.append(token)

    posting_map = {}
    first = True

    for token in query_list:
        try:
            index_tuple = table[token]
            index.seek(index_tuple[0])
            data = index.read(index_tuple[1])
            posting_list = pickle.loads(data)
            doc_freq.append(len(posting_list))
            for posting in posting_list:
                if first:
                    posting_map[posting.doc_id] = [posting.count]
                elif posting.doc_id in posting_map:
                    posting_map[posting.doc_id].append(posting.count)
        except KeyError:
            print(f"Token '{token}' not found in the index.")
            doc_freq.append(0)
            continue
        first = False

    # filter valid terms
    valid_terms = [query_list[i] for i in range(len(query_list)) if doc_freq[i] > 0]
    valid_tfs = [tokenized_query[term] for term in valid_terms]
    valid_dfs = [doc_freq[i] for i in range(len(doc_freq)) if doc_freq[i] > 0]

    if not valid_terms:
        print("No valid terms found in the query.")
        return []

    # compute tf-idf
    query_tf_idf = compute_tf_idf(valid_terms, valid_tfs, valid_dfs)
    doc_tf_idf_scores = []
    for key in posting_map.keys():
        doc_tf_idf_scores.append(
            (key, np.dot(query_tf_idf, compute_tf_idf(valid_terms, posting_map[key], valid_dfs)))
        )

    doc_tf_idf_scores = sorted(doc_tf_idf_scores, key=lambda x: (-x[1], x[0]))

    # fetch urls
    url_list = []
    doc_ids = shelve.open('doc_id')
    for i in range(min(5, len(doc_tf_idf_scores))):
        doc_id = doc_tf_idf_scores[i][0]
        try:
            url_list.append(doc_ids[str(doc_id)])
        except KeyError:
            print(f"Document ID {doc_id} not found in doc_id.db.")
            continue

    return url_list


if __name__ == "__main__":
    while True:
        string = input ("Query: ").lower()
        if string == 'q':
            index.close()
            break
        start_time = time.time()
        response = make_query(string)
        end_time = time.time()
        for url in response:
            print(url)
        print(end_time - start_time)