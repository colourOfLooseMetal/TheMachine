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
# splitOnFirstOccuranceOf = ["720p", "1080p", "eng", "bluray","dvd", "[","bdrip","1080","webrip","brrip", " cc", "blu"]#and anything after year


# s = "the dude is a cool dude"
# print(s.find('dude'))#4
# print("'",s[0:4], "'++'",s[4:])
# print(s.find('egg'))#-1
# input()
finalNames = []
needAttentionDirs = []
noSub = []
for path, subdirs, files in os.walk("./test2"):
    for name in files:
        # print(subdirs)
        # input()
        # print(os.path.join(path, name))
        dirToFile = os.path.join(path, name)
        # print(name)
        if name.endswith(".avi") or name.endswith(".mp4") or name.endswith(".mkv"):
            print("path:",path)
            print("movName:",name)
            subCount = 0
            anotherMovieFound = False
            for subfile in os.listdir(path):
                subName = ""
                if subfile.endswith(".avi") or subfile.endswith(".mp4") or subfile.endswith(".mkv"):
                    if subfile != name:
                        anotherMovieFound = True
                if subfile.endswith(".srt"):
                    subCount += 1
                    subName = subfile
                    print("subFound!")
                    print(subfile)
                    # input()
            # print("subcount ", subCount)
            if anotherMovieFound == True:
                needAttentionDirs.append(path)
                print("multiple movs")
            elif subName == "":
                needAttentionDirs.append(path)
                print("no sub")
                noSub.append((path))
            elif subCount > 1:
                print("multiple subs")
                needAttentionDirs.append(path)
            elif subfile[0:-4] == name[0:-4]:
                print("names already equal")
            else:
                print("sub ok to rename me thinks")
                original = path + "\\" + subName
                renamed = path + "\\" + name[0:-4] + ".srt"
                print(original)
                print(renamed)
                # os.rename(original, renamed)
                input()
            print("\n")
            # finalNames.append(finalName)
            # original = path + "\\" + name
            # renamed = path + "\\" + finalName
            # os.rename(original, renamed)
            # print(original)
            # print(renamed)
    #         # input()
    #
    # with open('./MovieNames.txt', 'w') as f:
    #     for line in finalNames:
    #         f.write("%s\n" % line)
    #     # input()
print(noSub)