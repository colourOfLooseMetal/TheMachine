import os
import json
from playsound import playsound

with open('audioSegmentInfo.txt') as f:
    d = json.load(f)
    print(d[0])
# for audioSegementData in d:
#     print(audioSegementData[2]," #", audioSegementData[1])
# START AT 407
for i, audioSegementData in enumerate(d):
    if i < 407:
        continue
    fname = "./audioSlices/" + str(audioSegementData[1])+".mp3"
    print(audioSegementData[0]," #", audioSegementData[1])
    print("Text: ")
    print(audioSegementData[2])
    print("\n")

    playsound(fname)
    print("done")
    input()
