from bs4 import BeautifulSoup
from nltk.stem import PorterStemmer
import shelve
import pickle
import re
import lxml
import struct
import os
from posting import Posting
data = {}
file_count = 1
term_count = 1
if os.path.exists("terms.db"):
    print("Deleted Terms")
    os.remove("terms.db")
if os.path.exists("doc_id.db"):
    print("Deleted Doc_id dict")
    os.remove("doc_id.db")
terms = shelve.open('terms')
doc_ids = shelve.open('doc_id')
unique_docs = shelve.open("unique_docs")
def index_doc(url, html, doc_count, run = True):
    global term_count
    if not run:
        create_new_partial(file_count)
        print(term_count)
        return
    print(f"trying to index {doc_count}")
    if url not in unique_docs:
        return
    else:
        unique_docs[url] = str(doc_count)
    doc_ids[str(doc_count)] = url
    print(f"still trying {doc_count}, given url {doc_ids[str(doc_count)]}")
    try:
        soup = BeautifulSoup(html, 'lxml')
    except:
        print(f"Could not parse {url}")
        return
    print(f"sucessfully parsed {doc_count}")
    text = soup.get_text(separator = " ", strip = True).lower()
    english_text = re.sub(r"[^a-z0-9\s]", " ", text)
    words = english_text.split()
    ps = PorterStemmer()
    token_map = {}
    for word in words:
        token = ps.stem(word)
        if len(set(token)) == 1:
            continue
        if token.isdigit() and len(token) > 9:
            continue
        if token in token_map.keys():
            token_map[token] += 1
        else:
            token_map[token] = 1
    add_posting(token_map, doc_count)
    #print(doc_count)
def add_posting(token_map, doc_id):
    global file_count
    global data
    global term_count
    for token in token_map:
        if token not in terms:
            terms[token] = True
            term_count +=1
            #print(f"term count: {term_count}")
        current_posting = Posting(doc_id, token_map[token])
        #current_posting = (doc_id, token_map[token])
        if token in data.keys():
            data[token].append(current_posting)
        else:
            data[token] = list()
            data[token].append(current_posting)
    if((doc_id % 5000)==0):
        create_new_partial(file_count)
        file_count += 1
def create_new_partial(file_count):
    global data
    print(f"Creating file no.{file_count}")
    file_name = f"index{file_count}.bin"
    keys = data.keys()
    sorted_keys = sorted(keys)
    with open(file_name, 'wb') as f:
        for key in sorted_keys:
            store_tuple = (key, data[key])
            serialized_tuple = pickle.dumps(store_tuple)
            serialization_length = len(serialized_tuple)
            f.write(struct.pack('I', serialization_length))
            f.write(serialized_tuple)
            #print(key)
            #print(serialization_length)
    data.clear()