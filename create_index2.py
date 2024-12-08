import json
from pathlib import Path
from bs4 import BeautifulSoup
from nltk.stem import PorterStemmer
import shelve
import pickle
import re
import lxml
import os
import gc
gc.collect()
from create_postings2 import index_doc, data, file_count, term_count

start_folder = Path('DEV')

def create_index():
    global file_count
    global data
    global term_count
    doc_count = 1
    #print('Opened DEV')
    for folder in start_folder.iterdir():
        if folder.name.startswith('.'):
            continue
        print(f"opened {folder.name}")
        for file in folder.iterdir():
            with open(file, 'r') as json_file:
                data1 = json.load(json_file)
                if data1['encoding'] == 'utf-8' or data1['encoding'] == 'ascii':
                    print(f"parsing {data1['url']}")
                    index_doc(data1['url'], data1['content'], doc_count)
                    doc_count +=1
    #create partial w/ remaining data
    index_doc("", "", 0, False)

    #create_new_semifile(file_count)
    #print(term_count)


if __name__ == "__main__":
    create_index()

