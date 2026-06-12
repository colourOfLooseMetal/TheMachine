import textwrap
import cv2
import os
import pysrt
import re
import time
import unicodedata
from PIL import ImageDraw
from PIL import ImageFont
from PIL import Image
import json

#THIS VERSION SHOULD ONLY GET ONE SHOT PER LINE OF DIALOGUE, zoop


def natural_key(string_):
    """See http://www.codinghorror.com/blog/archives/001018.html"""
    return [int(s) if s.isdigit() else s for s in re.split(r'(\d+)', string_)]

# the regex scripts to clean the html like tags from the subtitle text
tagCleaner = re.compile('<.*?>')
bracketCleanr = re.compile('{.*?}')

path = os.getcwd()



# def writeTextOnImage(cv2image, text):
#     imWidth = cv2image.shape[1]
#     imHeight = cv2image.shape[0]
#
#
#
#
#
#     # setWidth = int(wi/960 * 1700)
#     # print("FUNCSTART:", text)
#     # if text.count("\n") == 0:
#     #     wrapper = textwrap.TextWrapper(width=setWidth)
#     #     caption = text
#     #     word_list = wrapper.wrap(text=caption)
#     #     print("WL:", word_list)
#     #     caption_new = ''
#     #     for ii in word_list[:-1]:
#     #         caption_new = caption_new + ii + '\n'
#     #     caption_new += word_list[-1]
#     # else:
#     #     caption_new = text
#     #
#     #
#     #
#     # # print(fName, saveName, text)
#     # # input()
#     # image = Image.fromarray(cv2image)
#     # draw = ImageDraw.Draw(image)
#     # # Download the Font and Replace the font with the font file.
#     # setFontSize = int(hi/540 * 42)
#     # font = ImageFont.truetype("./arial.ttf", size=setFontSize)
#     # # print("::",caption_new,"::")
#     # w = 0
#     # # so wrapper.wrap splits if the lines are too long, but almost all lines are already split from text in the sub file... so we find the longest line
#     # # and base width on that
#     # for li in caption_new.split('\n'):
#     #     NewW, h = draw.textsize(li, font=font)
#     #     if NewW > w:
#     #         w = NewW
#     #
#     #     # print("--")
#     #     # print(li)
#     # W,H = image.size
#     # raw_string = r"{}".format(caption_new)
#     # print("RS:",raw_string)
#     # print("number of new lines:")
#     # print(caption_new.count('\n'))
#     # print(caption_new.split('\n'))
#     # print(caption_new)
#     # input()
#     # if w > W:
#     #     print("oh no")
#     #     # input()
#     # x,y = 0.5*(W-w),0.9*H-h
#     # # HEIGHT NEEDS SOME ADJUSTMENT BASED ON LINE NUMER
#     #
#     # # print(w," ", h)
#     # # print(W, " ", H)*
#
#     shadowcolor = "black"
#     borderThiccness = 3
#     #hell yeah
#     for btX in range(-borderThiccness,borderThiccness+1):
#         for btY in range(-borderThiccness, borderThiccness+1):
#             draw.multiline_text((x + btX, y + btY), caption_new, fill=shadowcolor, font=font,
#                                 align='center')
#
#     draw.multiline_text((x, y), caption_new, (255, 255, 255), font=font, align='center')
#     # print(x," ", y)
#     # print(saveName)
#
#     return(image)



# use regex to clean html like tags
def clean_html(textWithTags):
    something = False
    if "\n- " in textWithTags or "\n-" in textWithTags:
        # print(textWithTags)
        something = True
        textWithTags = textWithTags.replace("\n- ", "\n")
        textWithTags = textWithTags.replace("\n-","\n")
        # print(textWithTags)
        # input()
    if textWithTags.startswith("- "):
        # print(textWithTags)
        something = True
        textWithTags = textWithTags[2:]
        # print(textWithTags)
        # input()
    if textWithTags.startswith("-"):
        # print(textWithTags)
        something = True
        textWithTags = textWithTags[1:]
        # print(textWithTags)
        # input()

    cleanText = re.sub(tagCleaner, '', textWithTags)
    cleanText = re.sub(bracketCleanr, '', cleanText)
    # if something:
    #     print(cleanText)
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
  # holds the number for the filenam, is outside the function so we can do multiple seasons and not reset


class Meme:
    def __init__(self, num, text,
                 timeStamp):  # each image is given a number, and has its text and timestamp stored in the json file
        self.num = num
        self.text = text
        self.timeStamp = timeStamp


import matplotlib.pyplot as plt
import numpy as np
# import imutils
def detect_blur_fft(image, size=60, thresh=10, vis=False):

    (h, w) = image.shape
    size = int(size * (w/400))
    (cX, cY) = (int(w / 2.0), int(h / 2.0))
    # compute the FFT to find the frequency transform, then shift
    # the zero frequency component (i.e., DC component located at
    # the top-left corner) to the center where it will be more
    # easy to analyze
    fft = np.fft.fft2(image)
    fftShift = np.fft.fftshift(fft)
    # check to see if we are visualizing our output
    if vis:
        # compute the magnitude spectrum of the transform
        magnitude = 20 * np.log(np.abs(fftShift))
        # display the original input image
        (fig, ax) = plt.subplots(1, 2, )
        ax[0].imshow(image, cmap="gray")
        ax[0].set_title("Input")
        ax[0].set_xticks([])
        ax[0].set_yticks([])
        # display the magnitude image
        ax[1].imshow(magnitude, cmap="gray")
        ax[1].set_title("Magnitude Spectrum")
        ax[1].set_xticks([])
        ax[1].set_yticks([])
        # show our plots
        plt.show()
    # zero-out the center of the FFT shift (i.e., remove low
    # frequencies), apply the inverse shift such that the DC
    # component once again becomes the top-left, and then apply
    # the inverse FFT
    fftShift[cY - size:cY + size, cX - size:cX + size] = 0
    fftShift = np.fft.ifftshift(fftShift)
    recon = np.fft.ifft2(fftShift)
    # compute the magnitude spectrum of the reconstructed image,
    # then compute the mean of the magnitude values
    magnitude = 20 * np.log(np.abs(recon))
    mean = np.mean(magnitude)


    # the image will be considered "blurry" if the mean value of the
    # magnitudes is less than the threshold value
    return(mean)


def detect_blur(image):

    # Convert image to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply binary thresholding for bright spot detection
    _, binary_image = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)

    # Apply Laplacian filter for edge detection
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    laplacian_variance = laplacian.var()
    return(laplacian_variance)


def load_files_from_folder(folder, exts, savePicsTo):
    # uniqueImShapSrtNames = ['01 Carrie Remastered 1976.srt', '01 Clash Of The Titans (Fantasy) 1981.srt', '01 Doom Unrated Extended (Sci-Fi) 2005.srt', '01 Hellraiser I (Horror) 1987.srt', '01 Home Alone 1 Family (Comedy) 1990.srt', '01 Indiana Jones And The Raiders Of The Lost Ark 1981.srt', '01 Invasion Of The Body Snatchers Remastered 1956.srt', '01 RoboCop 1 (Sci-Fi) 1987.srt', '01 The War Of The Worlds Remastered (Sci-Fi) 1953.srt', '01 Tron Remastered (Sci-Fi) 1982.srt', '01 X Men (Action) 2000.srt', '02 Doom Annihilation (Sci-Fi) 2019.srt', '12 Angry Men 1957.eng.srt', '1935 The 39 Steps.eng.srt', '1940 Foreign Correspondent.eng.srt', '1942 Saboteur.eng.srt', '1946 Notorious.eng.srt', '1948 Rope.eng.srt', '1954 Rear Window.eng.srt', '1968 Planet of the Apes.srt', '1975 Monty Python And The Holy Grail movie.srt', '1982 Monty Python Live At The Hollywood Bowl movie.srt', '2001 A Space Odyssey 1968.srt', 'A Clockwork Orange 1971.eng.srt', 'A Night At The Opera 1935.srt', 'A Nightmare On Elm Street 1984.srt', 'Beetlejuice 1988.eng.srt', 'Ben Hur 1959.eng.srt', 'Blade Runner Final Cut 1997.srt', 'Brokeback Mountain 2005.srt', 'Cats 2019.eng.srt', 'Chitty Chitty Bang Bang 1968.eng.srt', 'Cinema Paradiso 1988.eng.srt', 'Citizen Kane 1941.srt', 'Cool Hand Luke 1967.eng.srt', 'D.E.B.S. (2004).srt', 'DoubleDown NeilBreen 2005.srt', 'Fuori Di Testa 1982.eng.srt', 'Gone With The Wind 1939.eng.srt', 'Good Time 2017.srt', 'Harry Potter And The Chamber Of Secrets 2002.srt', 'Harry Potter And The Goblet Of Fire 2005.srt', 'Harry Potter And The Order Of The Phoenix 2007.srt', 'I Am Here Now 2009.srt', 'Interstate 60 2002.eng.srt', 'Jurassic Park 1993.srt', 'M 1931.srt', 'Mad Max 1979.srt', 'Mallrats Extended (Comedy) 1995.srt', 'Musetta alla conquista di Parigi 1962.eng.srt', 'Nights Of Cabiria 1957.srt', 'Rear Window 1954.eng.srt', 'Strangers on a Train 1951.eng.srt', 'Sunset Boulevard Film Noir 1950.srt', 'Sweet Smell Of Success 1957.srt', 'The Adventures of Priscilla, Queen of the Desert.srt', 'The Battle of Algiers 1966.eng.srt', 'The Black Hole Il buco nero 1979.eng.srt', 'The Bride of Frankenstein 1935.eng.srt', 'The Elephant Man 1980.srt', 'The Green Mile 1999.srt', 'The King And I 1956.srt', 'The Lighthouse 2019.eng.srt', 'The Pianist.eng.srt', 'The Princess And The Pirate 1944.srt', 'The Terminator 1984.srt', 'Wild Strawberries.srt', 'die hard 1988.eng.srt', 'flash gordon 1980.eng.srt']
    issueMovies = []
    issueSubs = []
    fnameIter = 0
    run = False

    count = 0

    movies = []
    srts = []
    for filename in sorted(os.listdir(folder), key=natural_key):
        if filename.endswith(exts[0]) or filename.endswith(exts[1]) or filename.endswith(exts[2]):
            movies.append(filename)
        if filename.endswith(".srt"):
            srts.append(filename)
    srts.sort()
    movies.sort()
    print(len(movies))
    print(len(srts))
    # input()
    for i in range(len(movies)):
        # print(movies[i] + " :: " + srts[i])

        lenMovString = len(movies[i])
        # print(movies[i][:-4] + "::" + srts[i][0:lenMovString - 4])
        if movies[i][:-4] != srts[i][0:lenMovString-4]:
            print(movies[i][:-4]+"::"+srts[i][0:lenMovString-4])
            print(movies[i], movies[i][:-4])
            print("wuh woh")
            input()

    for i, subfile in enumerate(srts):
        picSaved = False
        print(subfile)
        if subfile.startswith("1972 Frenzy"):
            run = True
            continue
        if run == False:
            continue
        # if subfile not in uniqueImShapSrtNames:
        #     continue
        movFile = movies[i]
        time.sleep(0.1)
        subs = pysrt.open(folder + subfile,encoding='iso-8859-1')

        vidcap = cv2.VideoCapture(folder + movies[i])
        fps = (vidcap.get(cv2.CAP_PROP_FPS))
        # print(fps)
        subLength = len(subs)
        # print(subLength)
        for w, sub in enumerate(subs):

            # if w >= 11 or w < 7:
            #     continue
            # print(w)
            # if w == 7 or w == int(subLength*.1) or w == int(subLength*.2) or w == int(subLength*.3) or w == int(subLength*.4) or w == int(subLength*.5) or w == int(subLength*.6) or w == int(subLength*.7):
            #     lwidjak= 0
            #     # print("shouldbegood")
            # else:
            #     continue

            # print("zoopee", w)
            text = sub.text
            # print(text)
            if text == '':
                continue

            #CHEWCK
            # text = clean_html(text)
            # textNORM = unicodedata.normalize('NFKC', text)
            # if textNORM != text:
            #     print("original, NORMALIZED: ",text, textNORM)


            screenShotTime = sub.start + int(sub_time_to_ms(sub.end - sub.start) * 0.6)
            sstMs = sub_time_to_ms(screenShotTime)
            imInit = False
            vidcap.set(cv2.CAP_PROP_POS_MSEC, sstMs)
            res, image = vidcap.read()

            if res:
                imInit = True

            else:
                # print("errorEE" + str(folder + filename))
                print(movies[i])
                print(srts[i])
                input()
                issueMovies.append(movies[i])
                issueSubs.append(srts[i])
            if imInit == False:
                print("hmmzoop")
                print("pause")
                # print("init falsze" + str(folder + filename))
                input()
            new_filename = "." + savePicsTo + "" + str(fnameIter) + ".jpg"


            cv2.imwrite(new_filename, image,
                        [int(cv2.IMWRITE_JPEG_QUALITY), 91])
            picSaved = True
            movieTitle = movies[i][:-4]
            # m1 = Meme(fnameIter, textNORM, movieTitle)
            # data.append(m1)

            fnameIter += 1
        vidcap.release()
        print(fnameIter)

    # print(issueMovies)
    print("printing issue list")
    for problematicMovFileButShowingSub in issueSubs:
        print(problematicMovFileButShowingSub)








clean = re.compile('<.*?>')
load_files_from_folder("C:\\Users\\Jesse\\OneDrive\\Documents\\pythonPrograms\\videoMemeMaking\\moviesNstuff2024\\movies\\all\\", [".mp4",".avi",".mkv"], "/picsNoSubs/")
print(len(data))
# load_files_from_folder(path + "/vids/", ".mp4")
# load_files_from_folder(path + "/s2/", ".mp4")
# load_files_from_folder(path + "/s3/", ".mp4")
# load_files_from_folder(path + "/s4/", ".mp4")
# load_files_from_folder(path + "/s5/", ".mp4")

# save json data once all files have been ran
# json_string = json.dumps([ob.__dict__ for ob in data])
# f = open("movFileMap24.txt", "w")
# f.write(json_string)
# f.close()
