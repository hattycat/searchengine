import hashlib
import re
from pathlib import Path
import json
from bs4 import BeautifulSoup
import shelve

def is_dupe(simhash1, simhash2, threshold=1):
    return hamming_distance(simhash1, simhash2) < threshold

def create_hash(token):
    return int(hashlib.md5(token.encode()).hexdigest(), 16) & ((1 << 64) - 1)

def compute_simhash(soup):
    text = soup.get_text(separator=' ', strip=True)
    english_text = re.sub(r"[^a-z\s]", "", text)
    words = english_text.lower().split()
    tokens=[]
    for i in range(len(words)-1):
        token = words[i] + ' ' + words[i+1]  
        tokens.append(token)

    vector = [0] * 64
    
    for token in tokens:
        token_hash = create_hash(token)  # Get 64-bit hash
        for i in range(64):
            bit = (token_hash >> i) & 1
            if bit:
                vector[i] += 1  # Weighted by frequency
            else:
                vector[i] -= 1
    
    simhash = 0
    for i, v in enumerate(vector):
        if v > 0:
            simhash |= (1 << i)
    return simhash

def hamming_distance(hash1, hash2):
    x = hash1 ^ hash2
    return bin(x).count('1')  # Count differing bits


if __name__ == "__main__":
    unique_docs = shelve.open('unique_docs')
    simhashes = []
    doc_count = 0
    start_folder = Path('Dev')
    for folder in start_folder.iterdir():
        if folder.name.startswith('.'):
            continue
        print(f"opened {folder.name}")
        for file in folder.iterdir():
            with open(file, 'r') as json_file:
                data = json.load(json_file)
                if data['encoding'] == 'utf-8' or data['encoding'] == 'ascii':
                    doc_count += 1
                    print(f"parsing {data['url']}")
                    print(f"doc no.{doc_count}")
                    html = data['content']
                    soup = BeautifulSoup(html, 'lxml')
                    currhash = compute_simhash(soup)
                    unique = True
                    for simhash in simhashes:
                        if is_dupe(simhash, currhash):
                            unique = False
                            break
                    if unique:
                        unique_docs[data['url']] = True
                        simhashes.append(currhash)
                    else:
                        print(f"Found Dupe: {data['url']}")
    print(doc_count)
    print(f"final number of unique pages found: {len(simhashes)}")
