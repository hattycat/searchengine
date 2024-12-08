import shelve
import struct
import pickle
from posting import Posting

terms = shelve.open('terms')

keys = list(terms.keys())
keys.sort()

print(len(keys))

class Partial:
    def __init__(self, file_name):
        self.file = open(file_name, 'rb')
        self.current_token = None
        self.current_list = None

    def get_next_token(self):
        byte = self.file.read(4)
        if byte == b'':
            self.current_token = None
            self.current_list = None
            return
        value = struct.unpack('I', byte)[0]
        serialized_tuple = self.file.read(value)
        obj = pickle.loads(serialized_tuple)
        self.current_token = obj[0]
        self.current_list = obj[1]


partial_list = []

for i in range(1, 12):
    file_name = f"index{i}.bin"
    partial_list.append(Partial(file_name))
    partial_list[i-1].get_next_token()

#for partial in partial_list:
    #print(partial.current_token)
    #`print(partial.current_list)


index = open('index.bin', 'wb')
table = {}

current_index = 0
for key in keys:
    print(f"serializing {key}")
    temp_list = []
    for partial in partial_list:
        if partial.current_token == key:
            temp_list += partial.current_list
            partial.get_next_token()
    temp_list = sorted(temp_list, key = lambda x: (-x.count, x.doc_id))
    serialization = pickle.dumps(temp_list)
    serialization_length = len(serialization)
    index.write(serialization)
    table[key] = (current_index, serialization_length)
    #print(serialization_length)
    current_index += serialization_length

for partial in partial_list:
    partial.file.close()

index.close()

count = 0
index = open('index.bin', 'rb')
for key in table.keys():
    
    index.seek(table[key][0])
    data = index.read(table[key][1])
    obj = pickle.loads(data)
    print(count)
    print(key)
    print(obj)
    count += 1

with open('index_table.pk1', 'wb') as f:
    pickle.dump(table,f)