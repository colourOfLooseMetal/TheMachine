import os

# importing the module
import json
import re
import string

import numpy
import numpy as np
# Opening JSON file
text = []



#NOT WORTH MAKING A CHAR DICT OF ONE LETTER AND 2 letters WOULD BE BIG, unless we did only letters not punct
def remove_non_ascii_2(text):
    return re.sub(r'[^\x00-\x7F]',' ', text)

with open('./machineTextTextCombined.json') as json_file:
    data = json.load(json_file)

    # Print the type of data variable
    print("Type:", type(data))

    # Print the data of dictionary
for textLine in data:
    text.append(remove_non_ascii_2(textLine).lower().replace("  ", " ").replace("\n", " "))

print(len(text))
input() #365697

allLetters = list(string.ascii_lowercase)#set(("a","b"))
allLetters.append(" ")
# for line in text:
#     for char in line:
#         allLetters.add(char)
# print(len(allLetters))
# print(allLetters)
# input()
twoLetterWordsMap= {}
for letter in allLetters:
    for secondLetter in allLetters:
        twoLetterWordsMap[letter+secondLetter] = np.zeros((len(text)), dtype=bool)
print(len(twoLetterWordsMap))

for i, t in enumerate(text):
    if(i % 1000 == 0):
        print(i)
        print(t)
    for letterIndx in range(len(t)-1):
        # print(t[letterIndx],t[letterIndx+1])
        if t[letterIndx]+t[letterIndx+1] in twoLetterWordsMap.keys():
            twoLetterWordsMap[t[letterIndx]+t[letterIndx+1]][i] = 1


# with open('./listfile.txt', 'w') as filehandle:
#     for listitem in ["egg1", "egg2", "egg3"]:
#         filehandle.write('%s\n' % listitem)
print(type(twoLetterWordsMap))
print(type(twoLetterWordsMap["aa"]))
# input()
searchterm = "hello there"
r = np.zeros((len(text)), dtype=np.int8)

for key in twoLetterWordsMap:
    print(key)
    print(twoLetterWordsMap[key])
    print(twoLetterWordsMap[key].sum())
for letterIndx in range(len(searchterm)-1):
    r = np.add(twoLetterWordsMap[searchterm[letterIndx]+searchterm[letterIndx+1]], r)
print(len(text))
unique, counts = np.unique(r, return_counts=True)
print(unique, counts)



# with open('machineTextTextCombined.txt', 'w') as out_file:
#     json.dump(text, out_file)


