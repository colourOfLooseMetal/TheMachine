import os

# importing the module
import json
import re
# Opening JSON file
text = []

def remove_non_ascii_2(text):
    return re.sub(r'[^\x00-\x7F]',' ', text)

with open('./machineTestText.json') as json_file:
    data = json.load(json_file)

    # Print the type of data variable
    print("Type:", type(data))

    # Print the data of dictionary
for dict in data:
    text.append(remove_non_ascii_2(dict["text"]).lower().replace("  ", " ").replace("\n", " "))

with open('machineTextTextCombined.txt', 'w') as out_file:
    json.dump(text, out_file)
