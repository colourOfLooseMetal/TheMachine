import cv2
import os
import pysrt
import re
import math
import json

#THIS VERSION SHOULD ONLY GET ONE SHOT PER LINE OF DIALOGUE, zoop


def natural_key(string_):
    """See http://www.codinghorror.com/blog/archives/001018.html"""
    return [int(s) if s.isdigit() else s for s in re.split(r'(\d+)', string_)]

# the regex scripts to clean the html like tags from the subtitle text
tagCleaner = re.compile('<.*?>')
bracketCleanr = re.compile('{.*?}')

path = os.getcwd()


# use regex to clean html like tags
def clean_html(textWithTags):
    cleanText = re.sub(tagCleaner, '', textWithTags)
    cleanText = re.sub(bracketCleanr, '', cleanText)
    return cleanText


# convert the subtitle time format to ms
def sub_time_to_ms(subStart):
    ms = subStart.milliseconds
    s = subStart.seconds
    m = subStart.minutes
    h = subStart.hours
    ms = (h * 60 * 60 * 1000) + (m * 60 * 1000) + (s * 1000) + ms
    return (ms)


data = []  # list to hold all the meme objects, later used as json data
fnameIter = 0  # holds the number for the filenam, is outside the function so we can do multiple seasons and not reset


class Meme:
    def __init__(self, num, text,
                 timeStamp):  # each image is given a number, and has its text and timestamp stored in the json file
        self.num = num
        self.text = text
        self.timeStamp = timeStamp


def load_files_from_folder(folder, ext,savePicsTo):

    count = 0
    # ends with /s1/ sp this jsut gets the 1
    # print("hey")
    # print(folder.split("/")[-2])
    # season = str(folder.split("/")[-2])
    global fnameIter
    for filename in sorted(os.listdir(folder), key=natural_key):
        currentIter = fnameIter
        # For every video file that is a mp4 in the folder
        if filename.endswith(ext):
            print(filename)
            # get the video file
            vidcap = cv2.VideoCapture(folder + filename)
            # get the srt file, they should have the same name
            subs = pysrt.open(folder + filename[:-4] + ".srt", encoding='iso-8859-1')
            fps = (vidcap.get(cv2.CAP_PROP_FPS))
            print(fps)
            # ex 1.mp4 becomes 1
            episodeNum = filename[:-4]
            # if episode num is one character, ex 1 2 3 to 01 02 03
            if len(episodeNum) == 1:
                episodeNum = "0" + episodeNum
            for sub in subs:
                # save the details for the json data, #time is in the format s1e01 1:41
                #end - start is the durration, get that in ms and add half (or 0.6) to the sub to be in the middle
                screenShotTime = sub.start + int(sub_time_to_ms(sub.end - sub.start)*0.6)
                sstMs = sub_time_to_ms(screenShotTime)
                vidcap.set(cv2.CAP_PROP_POS_MSEC, sstMs)
                res, image = vidcap.read()
                if res:
                    #cv2.imshow("imageyeeeee", image)
                    mn = str(screenShotTime.minutes)
                    # if min or sec num is one character, ex 1 2 3 to 01 02 03
                    if len(mn) == 1:
                        mn = "0" + mn
                    sec = str(screenShotTime.seconds)
                    if len(sec) == 1:
                        sec = "0" + sec
                    time = str(screenShotTime.hours) + ":" + mn + ":" + sec
                    # time = str("s" + season + "e" + episodeNum + " " + time)
                    time = str("Mean Girls" + " " + time)
                    #time = str(episodeNum + " " + time)
                    # text is the current subs text
                    text = sub.text
                    if text == '':
                        continue
                    text = clean_html(text)
                    # take a screenshot, the screenshots are numbered incrementially from 0 up
                    new_filename = "."+savePicsTo+"/"+ str(fnameIter) + ".jpg"
                    # print(new_filename)
                    # input()
                    h, w = image.shape[0:2]
                    # width = 640
                    # scaleFactor = 640/w
                    # height = h*scaleFactor
                    # if(w == 1920 and h == 816):
                    #     crop_img = image[0:h, 240:1920-240]
                    #     h, w = crop_img.shape[0:2]
                    #     #print(h,w)
                    #     image = cv2.resize(crop_img, (int(w*4/9), int(h*4/9)))
                    # elif(w == 1920 and h != 816):
                    #     image = cv2.resize(image, (int(w/3), int(h/3)))
                    # elif(w > 1100 and w < 1500):
                    #     image = cv2.resize(image, (int(w/2), int(h/2)))
                    # else:
                    resize = cv2.resize(image, (int(w/2), int(h/2)))
                    cv2.imwrite(new_filename, resize,
                                 [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                    text = re.sub(clean, '', text)
                    m1 = Meme(fnameIter, text, time)
                    # append to the list that will be come the json file
                    data.append(m1)
                    # since there was a screenshot fnameIter goes up 1
                    fnameIter += 1
                else:
                    print("error" + str(folder+filename))
            print("imgs in episode: "+str(fnameIter - currentIter))
folderName = "/subScreenshots"
try:
    os.makedirs(path + folderName)
except FileExistsError:
    print("Directory already exists")

clean = re.compile('<.*?>')
load_files_from_folder("C:\\Users\\Jesse\\Documents\\pythonPrograms\\videoMemeMaking\\movies2022\\MeanGirls\\", ".mp4",folderName)

# load_files_from_folder(path + "/vids/", ".mp4")
# load_files_from_folder(path + "/s2/", ".mp4")
# load_files_from_folder(path + "/s3/", ".mp4")
# load_files_from_folder(path + "/s4/", ".mp4")
# load_files_from_folder(path + "/s5/", ".mp4")

# save json data once all files have been ran
json_string = json.dumps([ob.__dict__ for ob in data])
f = open("JohnnyBravoMap.txt", "w")
f.write(json_string)
f.close()
