import os
import regex as re

# extensions = []
# for path, subdirs, files in os.walk("./movies/"):
#     for name in files:
#         # print(os.path.join(path, name))
#         dirToFile = os.path.join(path, name)
#         extension = dirToFile.split(".")[-1]
#         extensions.append(extension)
#         # input()
# extensions = set(extensions)
# print(extensions)#{'sub', 'txt', 'jpg', 'nfo', 'idx', 'avi', 'sfv', 'mp4', 'xml', 'srt', 'scr', 'mkv', 'png'}
splitOnFirstOccuranceOf = ["720p", "1080p", "eng", "bluray","dvd", "[","bdrip","1080","webrip","brrip", " cc", "blu","xvid", "t.c.r"]#and anything after year


# s = "the dude is a cool dude"
# print(s.find('dude'))#4
# print("'",s[0:4], "'++'",s[4:])
# print(s.find('egg'))#-1
# input()
finalNames = []
for path, subdirs, files in os.walk("./movies/needExtract"):
    for name in files:
        # print(subdirs)
        # input()
        # print(os.path.join(path, name))
        dirToFile = os.path.join(path, name)
        # print(name)
        if name.endswith(".avi") or name.endswith(".mp4") or name.endswith(".mkv"):
            r = re.findall(r'(?:[^\d]|\A)(\d{4})(?:[^\d]|\Z)', name)
            years = []
            for num in r:
                if int(num) > 1922 and int(num) < 2024:
                    years.append(num)
            # print(years)
            # print(name)
            splitOnFirstOccuranceOfIndices = []
            for match in splitOnFirstOccuranceOf:
                index = name.lower().find(match)
                if index == -1:
                    index = 999
                if index < 7:
                    index = 999
                splitOnFirstOccuranceOfIndices.append(index)
            yearsIndices = []
            for match in years:
                index = name.find(match)
                if index == -1:
                    index = 999
                if index < 7:
                    index = 999
                yearsIndices.append(index+4)
            allMatchIndices = yearsIndices + splitOnFirstOccuranceOfIndices
            allMatches = years + splitOnFirstOccuranceOf
            # print(allMatchIndices)
            # print(allMatches)
            firstMatch = allMatchIndices.index(min(allMatchIndices))
            # print(allMatchIndices.index(min(allMatchIndices)))
            finalName = name[0:allMatchIndices[firstMatch]]
            if allMatchIndices[firstMatch] == -1 or allMatchIndices[firstMatch] == 999:
                finalName = finalName[0:-4]
            finalName = finalName.replace("."," ")
            finalName = finalName.replace("-", " ")
            finalName = finalName.replace("(", "")
            finalName = finalName.replace(")", "")
            finalName = finalName.replace("  ", " ")
            finalName = finalName.replace("  ", " ")
            finalName = finalName.replace("  ", " ")
            finalName = finalName.replace("Sci Fi", "(Sci-Fi)")
            finalName = finalName.replace("comedy", "(comedy)")
            finalName = finalName.replace("horror", "(horror)")
            finalName = finalName.replace("fantasy", "(fantasy)")
            finalName = finalName.replace("adventure", "(adventure)")
            finalName = finalName.replace("Sci Fi", "(Sci-Fi)")
            finalName = finalName.replace("Comedy", "(Comedy)")
            finalName = finalName.replace("Horror", "(Horror)")
            finalName = finalName.replace("Fantasy", "(Fantasy)")
            finalName = finalName.replace("Action", "(Action)")
            finalName = finalName.replace("action", "(action)")
            finalName = finalName + "." + name.split(".")[-1]
            finalName = finalName.replace(" .mp4", ".mp4")
            finalName = finalName.replace(" .mkv", ".mkv")
            finalName = finalName.replace(" .avi", ".avi")

            #comedy horror fantasy adventure sci fi
            # print(path)
            # print(finalName)
            print("\n")
            finalNames.append(finalName)
            original = path + "\\" + name
            renamed = path + "\\" + finalName
            print(original)
            print(renamed)
            # os.rename(original, renamed)

    #         # input()
    #
    # with open('./MovieNames.txt', 'w') as f:
    #     for line in finalNames:
    #         f.write("%s\n" % line)
    #     # input()