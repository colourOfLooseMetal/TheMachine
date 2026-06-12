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

from pydub import AudioSegment
def saveAudioSegment(fileName, msStart,msEnd, fnameIter):
    sound = AudioSegment.from_mp3("./movies/audio/" +fileName)

    # len() and slicing are in milliseconds
    audioSlice = sound[msStart:msEnd]

    # Concatenation is just adding
    # second_half_3_times = second_half + second_half + second_half

    # writing mp3 files is a one liner
    audioSlice.export("./audioSlices/"+str(fnameIter)+".mp3", format="mp3")

def load_files_from_folder(folder, exts, savePicsTo):
    # uniqueImShapSrtNames = ['01 Carrie Remastered 1976.srt', '01 Clash Of The Titans (Fantasy) 1981.srt', '01 Doom Unrated Extended (Sci-Fi) 2005.srt', '01 Hellraiser I (Horror) 1987.srt', '01 Home Alone 1 Family (Comedy) 1990.srt', '01 Indiana Jones And The Raiders Of The Lost Ark 1981.srt', '01 Invasion Of The Body Snatchers Remastered 1956.srt', '01 RoboCop 1 (Sci-Fi) 1987.srt', '01 The War Of The Worlds Remastered (Sci-Fi) 1953.srt', '01 Tron Remastered (Sci-Fi) 1982.srt', '01 X Men (Action) 2000.srt', '02 Doom Annihilation (Sci-Fi) 2019.srt', '12 Angry Men 1957.eng.srt', '1935 The 39 Steps.eng.srt', '1940 Foreign Correspondent.eng.srt', '1942 Saboteur.eng.srt', '1946 Notorious.eng.srt', '1948 Rope.eng.srt', '1954 Rear Window.eng.srt', '1968 Planet of the Apes.srt', '1975 Monty Python And The Holy Grail movie.srt', '1982 Monty Python Live At The Hollywood Bowl movie.srt', '2001 A Space Odyssey 1968.srt', 'A Clockwork Orange 1971.eng.srt', 'A Night At The Opera 1935.srt', 'A Nightmare On Elm Street 1984.srt', 'Beetlejuice 1988.eng.srt', 'Ben Hur 1959.eng.srt', 'Blade Runner Final Cut 1997.srt', 'Brokeback Mountain 2005.srt', 'Cats 2019.eng.srt', 'Chitty Chitty Bang Bang 1968.eng.srt', 'Cinema Paradiso 1988.eng.srt', 'Citizen Kane 1941.srt', 'Cool Hand Luke 1967.eng.srt', 'D.E.B.S. (2004).srt', 'DoubleDown NeilBreen 2005.srt', 'Fuori Di Testa 1982.eng.srt', 'Gone With The Wind 1939.eng.srt', 'Good Time 2017.srt', 'Harry Potter And The Chamber Of Secrets 2002.srt', 'Harry Potter And The Goblet Of Fire 2005.srt', 'Harry Potter And The Order Of The Phoenix 2007.srt', 'I Am Here Now 2009.srt', 'Interstate 60 2002.eng.srt', 'Jurassic Park 1993.srt', 'M 1931.srt', 'Mad Max 1979.srt', 'Mallrats Extended (Comedy) 1995.srt', 'Musetta alla conquista di Parigi 1962.eng.srt', 'Nights Of Cabiria 1957.srt', 'Rear Window 1954.eng.srt', 'Strangers on a Train 1951.eng.srt', 'Sunset Boulevard Film Noir 1950.srt', 'Sweet Smell Of Success 1957.srt', 'The Adventures of Priscilla, Queen of the Desert.srt', 'The Battle of Algiers 1966.eng.srt', 'The Black Hole Il buco nero 1979.eng.srt', 'The Bride of Frankenstein 1935.eng.srt', 'The Elephant Man 1980.srt', 'The Green Mile 1999.srt', 'The King And I 1956.srt', 'The Lighthouse 2019.eng.srt', 'The Pianist.eng.srt', 'The Princess And The Pirate 1944.srt', 'The Terminator 1984.srt', 'Wild Strawberries.srt', 'die hard 1988.eng.srt', 'flash gordon 1980.eng.srt']
    issueMovies = []
    issueSubs = []
    fnameIter = 0
    # run = False

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
        # if subfile.startswith("1972 Frenzy"):
        #     run = True
        #     continue
        # if run == False:
        #     continue
        # if subfile not in uniqueImShapSrtNames:
        #     continue
        movFile = movies[i]
        # time.sleep(0.1)
        subs = pysrt.open(folder + subfile,encoding='iso-8859-1')
        # print("STARTING")


        # print(fps)
        subLength = len(subs)
        # print(subLength)
        finalSubm5 = len(subs)-5
        for w, sub in enumerate(subs):
            # print(w)
            if w == 5 or w == finalSubm5:
                # print("gonnaRUn")
                zzz =1
            else:
                continue

            text = sub.text
            if text == '':
                print("TEXT IS BLANK")
                input()
                # continue
            msStart = int(sub_time_to_ms(sub.start))
            msEnd = int(sub_time_to_ms(sub.end))
            #CHEWCK
            text = clean_html(text)
            # print(text)
            # saveAudioSegment(movies[i][:-4]+".mp3", msStart, msEnd, fnameIter)
            data.append([movies[i][:-4]+".mp3", fnameIter, text])
            # print(data)
            # print("input")
            # input()
            # textNORM = unicodedata.normalize('NFKC', text)
            # if textNORM != text:
            #     print("original, NORMALIZED: ",text, textNORM)


            screenShotTime = sub.start + int(sub_time_to_ms(sub.end - sub.start) * 0.6)
            sstMs = sub_time_to_ms(screenShotTime)



            fnameIter += 1
        print(fnameIter)

    # print(issueMovies)
    # print("printing issue list")
    # for problematicMovFileButShowingSub in issueSubs:
    #     print(problematicMovFileButShowingSub)








clean = re.compile('<.*?>')
load_files_from_folder("C:\\Users\\Jesse\\OneDrive\\Documents\\pythonPrograms\\videoMemeMaking\\moviesNstuff2024\\movies\\all\\", [".mp4",".avi",".mkv"], "/picsNoSubs/")
print(len(data))
# load_files_from_folder(path + "/vids/", ".mp4")
# load_files_from_folder(path + "/s2/", ".mp4")
# load_files_from_folder(path + "/s3/", ".mp4")
# load_files_from_folder(path + "/s4/", ".mp4")
# load_files_from_folder(path + "/s5/", ".mp4")

# save json data once all files have been ran
# json_string = json.dumps([ob.__dict__ for ob in data])For Dict
json_string = json.dumps(data)
f = open("audioSegmentInfo.txt", "w")
f.write(json_string)
f.close()
