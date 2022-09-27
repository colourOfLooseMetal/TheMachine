import os

# importing the module
import json
import re
import string
import nltk

# Opening JSON file
text = []
names = []


def remove_non_ascii_2(text):
    return re.sub(r'[^\x00-\x7F]', ' ', text)


# assign directory
directory = './showMapData'

print('egg\\"'.replace('\\"','!'))
input()


# iterate over files in
# that directory
cumLen = 0
for filename in ['./showMapData\sm.json']:
    # checking if it is a file
    # print(filename)
    with open(filename) as json_file:
        data = json.load(json_file)
        # print(len(data))
        print(filename, ": ",cumLen)
        cumLen += len(data)
        # Print the type of data variable
        print("Type:", type(data))
        for dict in data:
            line = remove_non_ascii_2(dict["text"]).replace("  ", " ").replace("\n", " ")
            line = re.sub(r"\s*{.*}\s*", " ", line)
            line = re.sub('\s+',' ',line)
            line = line.replace("</b>", " ")
            line = line.replace("<b>", " ")
            line = line.replace("</i>", " ")
            line = line.replace("<i>", " ")
            line = line.replace('\\"','"')
            # if line[1] == "-":lots of things do the stutter like  i-i'm sorry...  i-i'm fine...  t-this is...?, we could remove the start stutter but idk yeah
            #     print(line)

            text.append(remove_non_ascii_2(line))

def has_numbers(inputString):
    return any(char.isdigit() for char in inputString)

# nltk.download('words')
# from nltk.corpus import words
# print(len(words.words('en')))
# input()
engWords = []
for line in open('words.txt','r').readlines():
    engWords.append(line.strip())
for line in open('words_alpha.txt','r').readlines():
    engWords.append(line.strip())
print(engWords[0:100])
engWords = set(engWords)
# print(engWords[0:100])
print(len(engWords))
# input()
lineIter = 0
for line in text:
    if lineIter%10000 == 0:
        print(lineIter)
    lineIter += 1
    line = re.sub(r'[^\w\d\s\']+', '', line)#remove everything except apostrophes
    wrds = line.split(" ")
    for word in wrds:
        if len(word) > 1:
            if word.endswith("'s"):
                word = word[0:-2]
            if word not in engWords and word.lower() not in engWords:
                # print(word)
                if word[0].isupper():
                    if not has_numbers(word):
                        names.append(word)
        #         print(word, "  is Not word")
        #     else:
        #         print(word, "  is a word")
        # input()

# names = list(dict.fromkeys(names))
# for name in names:
#     if any(substring in name for substring in engWords):
#         print(name)

mylist = list(dict.fromkeys(names))#remove duplicate
print(mylist)
# with open('smNames.txt', 'w') as out_file:
#     json.dump(text, out_file)
with open('smNames.txt', 'w') as filehandle:
    for name in mylist:
        filehandle.write('%s\n' % name)
filehandle.close()

namesUgh = []
for line in open('smNames -manuallyPickedOver.txt','r').readlines():
    namesUgh.append(line.strip())
names = []
for name in namesUgh:
    capCount = 0
    for letter in name:
        if letter.isupper():
            capCount += 1
    if capCount <= 1:
        names.append(name)
        # print(name)

with open('smNames.txt', 'w') as filehandle:
    for name in names:
        filehandle.write('%s\n' % name)
filehandle.close()