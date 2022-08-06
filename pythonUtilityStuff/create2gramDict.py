import os

# importing the module
import json
import re
import string

import numpy
import numpy as np
# Opening JSON file
text = []
import binascii



#NOT WORTH MAKING A CHAR DICT OF ONE LETTER AND 2 letters WOULD BE BIG, unless we did only letters not punct
def remove_non_ascii_2(text):
    return re.sub(r'[^\x00-\x7F]',' ', text)

with open('./machineTextTextCombined.json') as json_file:
    text = json.load(json_file)

    # Print the type of data variable
    print("Type:", type(text))

    # Print the data of dictionary
#do this in get key from json so that they are the same then just use machinetextcombined
# for textLine in data:
#     text.append(remove_non_ascii_2(textLine).lower().replace("  ", " ").replace("\n", " "))

print(len(text))
# input() #365697

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
        twoLetterWordsMap[letter+secondLetter] = np.zeros((365704), dtype=bool)
print(len(twoLetterWordsMap))

for i, t in enumerate(text):
    if(i % 10000 == 0):
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
r = np.zeros((365704), dtype=np.int8)

for key in twoLetterWordsMap:
    print(key)
    print(twoLetterWordsMap[key])
    print(twoLetterWordsMap[key].sum())
for letterIndx in range(len(searchterm)-1):
    r = np.add(twoLetterWordsMap[searchterm[letterIndx]+searchterm[letterIndx+1]], r)
print(len(text))
unique, counts = np.unique(r, return_counts=True)
print(unique, counts)

# print(bytearray(numpy.packbits(np_bin_array)).decode().strip("\x00"))

# f=open('twoLetterWordsMap.txt','a')
# bsetNameIter = 0
for key in twoLetterWordsMap:
    # print(bytearray(numpy.packbits(twoLetterWordsMap[key])).decode().strip("\x00"))
    l = list(twoLetterWordsMap[key][0:16].astype(int))
    output = "0b" + "".join(str(i) for i in l)

    print(l)
    print(output)
    input()
#     #desired output
#     # std::bitset<searchTextLen> bset1(std::string("1000"));
#     # std::bitset<searchTextLen> bset2(std::string("0001"));
#     #
#     # std::map < std::string, std::bitset < searchTextLen >> sample_map
#     # {
#     #     {1, bset1},
#     #     {2, bset2}
#     # };
#
#     f.write('std::bitset<searchTextLen> bset'+str(bsetNameIter)+'(std::string("')
#     np.savetxt(f, twoLetterWordsMap[key].astype(int), fmt='%i', newline='', delimiter='')
#     f.write('"));'+"\n")
#     bsetNameIter += 1
#     # Open a file with access mode 'a'
#     # with open("twoLetterWordsMap.txt", "a") as file_object:
#         # Append 'hello' at the end of file
#         # file_object.write(twoLetterWordsMap[key])
# bsetNameIter = 0
# f.write("\n")
# f.write("std::map < std::string, std::bitset < searchTextLen >> sample_map\n{\n")
# for key in twoLetterWordsMap:
#     f.write('{"'+ key + '", bset' + str(bsetNameIter) +"},")
#     bsetNameIter += 1

# with open('machineTextTextCombined.txt', 'w') as out_file:
#     json.dump(text, out_file)


