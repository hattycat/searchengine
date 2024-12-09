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
def compute_tf_idf(tokens, tf, df, N = N_docs):
    tf_idf = []
    for i in range(len(tokens)):
        tf_idf.append((1+math.log(tf[i]))*(math.log(N/df[i])))
    magnitude = math.sqrt(sum(x**2 for x in tf_idf))
    norm_idf = []
    
    if magnitude != 0:
        normalized_idf = [x / magnitude for x in tf_idf]
    else:
        # Return the original vector if magnitude is 0
        norm_idf = tf_idf
    return tf_idf
def make_query(string):
    index = open('index.bin', 'rb')
    english_text = re.sub(r"[^a-z0-9\s]", " ", string)
    words = english_text.split()
    print(words)
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

    posting_list = []
    posting_map = {}
    token_postings = {}  
    first = True

    if len(query_list) == 1:
        token = query_list[0]
        try:
            index_tuple = table[token]
            index.seek(index_tuple[0])
            data = index.read(index_tuple[1])
            posting_list = pickle.loads(data)
            url_list = []
            doc_ids = shelve.open('doc_id')
            for i in range(min(5, len(posting_list))):
                url_list.append(doc_ids[str(posting_list[i].doc_id)])
            return url_list

        except KeyError:
            print(f"Token '{token}' not found in the index.")
            return []

    for token in query_list:
        try:
            index_tuple = table[token]
            index.seek(index_tuple[0])
            data = index.read(index_tuple[1])
            posting_list = pickle.loads(data)
            print(posting_list)
            doc_freq.append(len(posting_list))
            token_postings[token] = posting_list
        except KeyError:
            print(f"Token '{token}' not found in the index.")
            doc_freq.append(0)  
            continue

        temp_posting_map = {}
        for posting in posting_list:
            if first:
                temp_posting_map[posting.doc_id] = [posting.count]
            elif posting.doc_id in posting_map:
                posting_map[posting.doc_id].append(posting.count)
                temp_posting_map[posting.doc_id] = posting_map[posting.doc_id]
        posting_map = temp_posting_map
        first = False

    valid_terms = [query_list[i] for i in range(len(query_list)) if doc_freq[i] > 0]
    valid_tfs = [tokenized_query[term] for term in valid_terms]
    valid_dfs = [doc_freq[i] for i in range(len(doc_freq)) if doc_freq[i] > 0]

    if not valid_terms:
        print("No valid terms found in the query.")
        return []

    query_tf_idf = compute_tf_idf(valid_terms, valid_tfs, valid_dfs)

    doc_tf_idf_scores = []
    for key in posting_map.keys():
        base_tf = [posting_map[key][valid_terms.index(term)] for term in valid_terms]
        doc_tf_idf_scores.append(
            (key, np.dot(query_tf_idf, compute_tf_idf(valid_terms, base_tf, valid_dfs)))
        )

    doc_tf_idf_scores = sorted(doc_tf_idf_scores, key=lambda x: (-x[1], x[0]))

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