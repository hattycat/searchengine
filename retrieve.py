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
    first = True
    if len(query_list) == 1:
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
            return []
    for token in query_list:
        try:
            index_tuple = table[token]
            index.seek(index_tuple[0])
            data = index.read(index_tuple[1])
            posting_list = pickle.loads(data)
            #print(posting_list)
            doc_freq.append(len(posting_list))

            #print(obj)
            #print()
        except KeyError:
            for key in posting_map.keys():
                posting_map[key].append(0)
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
    print(posting_map)
    tfs = []
    for query in query_list:
        tfs.append(tokenized_query[query])
    query_tf_idf = compute_tf_idf(query_list, tfs, doc_freq)
    doc_tf_idf_scores = []
    for key in posting_map.keys():
        print(key)
        score_tuple = (key, np.dot(query_tf_idf, compute_tf_idf(query_list, posting_map[key], doc_freq)))
        print(score_tuple)
        doc_tf_idf_scores.append(score_tuple)
        #print(posting_list)
        #print()
    doc_tf_idf_scores = sorted(doc_tf_idf_scores, key = lambda x: (-x[1], x[0]))
    #print(posting_list)
    #print()
    url_list = []
    doc_ids = shelve.open('doc_id')
    print(doc_tf_idf_scores)
    for i in range(min(5,len(doc_tf_idf_scores))):
        doc_id = doc_tf_idf_scores[i][0]
        #print(doc_id)
        #print(doc_ids[str(doc_id)])
        url_list.append(doc_ids[str(doc_id)])
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