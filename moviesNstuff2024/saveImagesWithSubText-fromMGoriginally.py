import textwrap
import cv2
import os
import pysrt
import re
import math
import json

from PIL import ImageDraw
from PIL import ImageFont
from PIL import Image
caption = "Obama warns far-left candidates says average American does not want to tear down the system"

dir = "C:\\Users\\Jesse\\Documents\\pythonPrograms\\videoMemeMaking\\movies2022\\MeanGirls\\"

def center_wrap(text, cwidth=80, **kw):
    lines = textwrap.wrap(text, **kw)
    return "\n".join(line.center(cwidth) for line in lines)


def writeTextOnImage(fName, saveName, text):
    wrapper = textwrap.TextWrapper(width=1700)
    caption = text
    word_list = wrapper.wrap(text=caption)
    caption_new = ''

    for ii in word_list[:-1]:
        caption_new = caption_new + ii + '\n'
    caption_new += word_list[-1]
    # print(fName, saveName, text)
    # input()
    image = Image.open(fName)
    draw = ImageDraw.Draw(image)
    # Download the Font and Replace the font with the font file.
    font = ImageFont.truetype("./arial.ttf", size=42)
    # print("::",caption_new,"::")
    w = 0
    # so wrapper.wrap splits if the lines are too long, but almost all lines are already split from text in the sub file... so we find the longest line
    # and base width on that
    for li in text.split('\n'):
        NewW, h = draw.textsize(li, font=font)
        if NewW > w:
            w = NewW
        # print("--")
        # print(li)
    W,H = image.size
    x,y = 0.5*(W-w),0.90*H-h

    # print(w," ", h)
    # print(W, " ", H)*

    shadowcolor = "black"
    borderThiccness = 3
    #hell yeah
    for btX in range(-borderThiccness,borderThiccness+1):
        for btY in range(-borderThiccness, borderThiccness+1):
            draw.multiline_text((x + btX, y + btY), text, fill=shadowcolor, font=font,
                                align='center')
    #fuk dis
    # draw.multiline_text((x + borderThiccness, y - borderThiccness), text, fill=shadowcolor, font=font, align='center')
    # draw.multiline_text((x - borderThiccness, y + borderThiccness), text, fill=shadowcolor, font=font, align='center')
    # draw.multiline_text((x + borderThiccness, y + borderThiccness), text, fill=shadowcolor, font=font, align='center')
    # draw.multiline_text((x - borderThiccness, y), text, fill=shadowcolor, font=font, align='center')
    # draw.multiline_text((x + borderThiccness, y), text, fill=shadowcolor, font=font, align='center')
    # draw.multiline_text((x, y + borderThiccness), text, fill=shadowcolor, font=font, align='center')
    # draw.multiline_text((x, y - borderThiccness), text, fill=shadowcolor, font=font, align='center')
    # draw.text((x - 2, y - 2), text, font=font, fill=shadowcolor)
    # draw.text((x + 2, y - 2), text, font=font, fill=shadowcolor)
    # draw.text((x - 2, y + 2), text, font=font, fill=shadowcolor)
    # draw.text((x + 2, y + 2), text, font=font, fill=shadowcolor)

    # draw.text((x,y), text, font=font)
    # print(text)
    draw.multiline_text((x, y), text, (255, 255, 255), font=font, align='center')
    # print(x," ", y)
    # print(saveName)

    image.save(saveName)



def natural_key(string_):
    """See http://www.codinghorror.com/blog/archives/001018.html"""
    return [int(s) if s.isdigit() else s for s in re.split(r'(\d+)', string_)]

# the regex scripts to clean the html like tags from the subtitle text
tagCleaner = re.compile('<.*?>')
bracketCleanr = re.compile('{.*?}')


# use regex to clean html like tags
def clean_html(textWithTags):
    cleanText = re.sub(tagCleaner, '', textWithTags)
    cleanText = re.sub(bracketCleanr, '', cleanText)
    return cleanText

fnameIter = 0  # holds the number for the filenam, is outside the function so we can do multiple seasons and not reset

def load_files_from_folder(folder, ext,loadFrom,saveTo):

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
            subs = pysrt.open(folder + filename[:-4] + ".srt", encoding='iso-8859-1')
            for sub in subs:
                text = sub.text
                if text == '':
                    continue
                text = clean_html(text)
                text = re.sub(clean, '', text)
                fName = "."+loadFrom+"/"+ str(fnameIter) + ".jpg"
                saveName = "."+saveTo+"/"+ str(fnameIter) + ".jpg"
                writeTextOnImage(fName, saveName, text)
                fnameIter += 1

clean = re.compile('<.*?>')
folderName = "/subScreenshots"
saveName = "/screenShotsSubbed"
path = os.getcwd()
try:
    os.makedirs(path + saveName)
except FileExistsError:
    print("Directory already exists")
folderName = "/subScreenshots"
load_files_from_folder("C:\\Users\\Jesse\\Documents\\pythonPrograms\\videoMemeMaking\\movies2022\\MeanGirls\\", ".mp4",folderName,saveName)

