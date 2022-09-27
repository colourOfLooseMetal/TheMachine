import os

# importing the module
import json
import re

# Opening JSON file
text = []


def remove_non_ascii_2(text):
    return re.sub(r'[^\x00-\x7F]', ' ', text)


# assign directory
directory = './showMapData'

print('egg\\"'.replace('\\"','!'))
input()


# iterate over files in
# that directory
cumLen = 0
for filename in ['./showMapData\sm.json',
                 './showMapData\cw.json',
                 './showMapData\sw.json',
                 './showMapData\\rc.json',
                 './showMapData\dispix.json',
                 './showMapData\jb.json',
                 './showMapData\gib.json',
                 './showMapData\lt.json',
                 './showMapData\db.json',
                 './showMapData\dbz.json',
                 './showMapData\dbzm.json',
                 './showMapData\jojo.json'
                 ]:
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
            line = remove_non_ascii_2(dict["text"]).lower().replace("  ", " ").replace("\n", " ")
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
print(cumLen)

# with open('machineTextTextCombined.json', 'w') as out_file:
#     json.dump(text, out_file)



# maxlen = 1;
# for string in text:
#     if len(string) > maxlen:
#         maxlen = len(string)
#         print(maxlen)
#         print(string)
# input()
# #
# eachTextLen = []
# for string in text:
#     eachTextLen.append(len(string))
#
# print(len(text))
# # with open('machineTextTextCombined.json', 'w') as f:
# #     for line in text:
# #         f.write("%s\n" % line)
#
#
# with open('strLens.json', 'w') as out_file:
#     json.dump(eachTextLen, out_file)
