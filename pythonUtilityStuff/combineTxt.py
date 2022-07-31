import os


text = ""
for filename in os.listdir("./texts"):
    f = os.path.join("./texts/", filename)
    print(f)
    if f.endswith(".txt"):
        with open(f) as file:
            lines = file.read()
            text = text + lines


words = text.split(" ")
while(1):
    query = input("enter search term: ")
    for i, word in enumerate(words):
        if word.__contains__(query):
            s = ' '.join(words[i-15:i+15])
            print(s)
            print("/n/nf")
# with open('hpLovecraftAll.txt', 'w', encoding='utf-8') as f:
#     f.write(text)