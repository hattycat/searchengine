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
    """
    Compute the TF-IDF scores for the given tokens.
    Skip terms with document frequency of 0.
    """
    tf_idf = []
    for i in range(len(tokens)):
        if df[i] > 0:  
            tf_idf.append((1 + math.log(tf[i])) * (math.log(N / df[i])))
        else:
            print(f"Skipping term '{tokens[i]}' due to zero document frequency.")
            tf_idf.append(0) 


    magnitude = math.sqrt(sum(x**2 for x in tf_idf))
    return [x / magnitude for x in tf_idf] if magnitude != 0 else tf_idf


def compute_proximity_score(query_words, doc_token_postings):
    """
    Compute a proximity bonus based on how close query terms appear.
    
    :param query_words: List of query words
    :param doc_token_postings: Dictionary of tokens to postings for a specific document
    :return: Proximity score (higher score means terms are closer)
    """
    if not all(doc_token_postings.get(token) for token in query_words):
        return 0

    term_positions = {}
    for token in query_words:

        term_positions[token] = [p.positions for p in doc_token_postings[token]][0]

    if not all(term_positions.values()):
        return 0

    # find minimum diff between query terms
    min_distance = float('inf')
    for base_pos in term_positions[query_words[0]]:
        current_max_distance = 0
        for other_term in query_words[1:]:
            closest_dist = min(
                abs(base_pos - other_pos) 
                for other_pos in term_positions[other_term]
            )
            current_max_distance = max(current_max_distance, closest_dist)
        
        min_distance = min(min_distance, current_max_distance)

    proximity_score = math.exp(-min_distance / 10) if min_distance != float('inf') else 0
    return proximity_score

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
    token_postings = {}
    first = True

    for token in query_list:
        try:
            index_tuple = table[token]
            index.seek(index_tuple[0])
            data = index.read(index_tuple[1])
            posting_list = pickle.loads(data)
            doc_freq.append(len(posting_list))
            token_postings[token] = posting_list

            temp_posting_map = {}
            for posting in posting_list:
                if first:
                    temp_posting_map[posting.doc_id] = [posting.count]
                elif posting.doc_id in posting_map:
                    posting_map[posting.doc_id].append(posting.count)
                    temp_posting_map[posting.doc_id] = posting_map[posting.doc_id]
            posting_map = temp_posting_map
            first = False
        except KeyError:
            print(f"Token '{token}' not found in the index.")
            doc_freq.append(0)  
            continue

    # skip terms with 0 df to avoid divide by 0
    valid_terms = [query_list[i] for i in range(len(query_list)) if doc_freq[i] > 0]
    valid_tfs = [tokenized_query[query] for query in valid_terms]
    valid_dfs = [doc_freq[i] for i in range(len(query_list)) if doc_freq[i] > 0]

    if not valid_terms:
        return [] 

    query_tf_idf = compute_tf_idf(valid_terms, valid_tfs, valid_dfs)

    doc_tf_idf_scores = []
    for key in posting_map.keys():
        doc_token_postings = {
            token: [p for p in token_postings[token] if p.doc_id == key]
            for token in valid_terms if token in token_postings
        }

        # base tf-idf score
        base_score = np.dot(query_tf_idf, compute_tf_idf(valid_terms, posting_map[key], valid_dfs))
        # proximity score
        proximity_bonus = compute_proximity_score(valid_terms, doc_token_postings)
        # combined
        final_score = 0.7 * base_score + 0.3 * proximity_bonus

        doc_tf_idf_scores.append((key, final_score))

    doc_tf_idf_scores = sorted(doc_tf_idf_scores, key=lambda x: (-x[1], x[0]))

    url_list = []
    doc_ids = shelve.open('doc_id')
    for i in range(min(5, len(doc_tf_idf_scores))):
        doc_id = doc_tf_idf_scores[i][0]
        try:
            url_list.append(doc_ids[str(doc_id)])
        except KeyError:
            print(f"Document ID {doc_id} not found in doc_id.db")
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