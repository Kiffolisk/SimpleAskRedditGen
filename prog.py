import requests
import json
import random
import gtts
from playsound import playsound
import os
from PIL import Image, ImageDraw, ImageFont
import textwrap
import re
from cv2 import VideoWriter, VideoWriter_fourcc
import cv2
from mutagen.mp3 import MP3
from pydub import AudioSegment

MAX_AUDIOS = 5
FPS = 15
WIDTH = 1024
HEIGHT = 600
VIDEO_OUTPUT_TIME = 0

CURRENT_COMMENT = -1
CURRENT_TIME = 0.0

AUDIO_TIMES = []

def get_reddit_post():
    url = 'https://www.reddit.com/r/askreddit/.json'
    headers = {'User-Agent': 'prog.py'}
    r = requests.get(url, headers=headers)
    data = json.loads(r.text)
    posts = data['data']['children']
    post = random.choice(posts)
    info = {}
    info["title"] = post["data"]["title"]
    info["author"] = post["data"]["author"]
    info["link"] = post["data"]["url"]
    return info

def get_reddit_post_comments(title):
    url = title + "/.json"
    headers = {'User-Agent': 'prog.py'}
    r = requests.get(url, headers=headers)
    data = json.loads(r.text)
    alreadyFound = []
    info = []
    posts = data[1]['data']['children']
    for x in range(0, MAX_AUDIOS):
        print(x)
        post = random.choice(posts)
        if post["kind"] == "more":
            x -= 1
            continue
        if post["data"]["body"] in alreadyFound:
            x -= 1
            continue
        if post["kind"] != "more":
            # print(post)
            lolinfo = {}
            lolinfo['text'] = post["data"]["body"]
            lolinfo['author'] = post["data"]["author"]
            # print(lolinfo)
            alreadyFound.append(lolinfo['text'])
            info.append(lolinfo)
    return info

def tts(text, filename = "synth.mp3"):
    engine = gtts.gTTS(text)
    engine.save("./voices/" + filename)

def is_file(file):
    return os.path.isfile(file)

def convert_avi_to_mp4(avi_file_path, output_name):
    os.system("ffmpeg -y -i '{input}' -ac 2 -b:v 2000k -c:a aac -c:v libx264 -b:a 160k -vprofile high -bf 0 -strict experimental -f mp4 '{output}.mp4'".format(input = avi_file_path, output = output_name))
    return True

def main():
    global VIDEO_OUTPUT_TIME
    global AUDIO_TIMES
    global CURRENT_TIME
    global CURRENT_COMMENT
    print("Cleaning up previous data...")
    if not os.path.exists("./voices"):
        print("Creating voices folder")
        os.makedirs("./voices/comments")
    else:
        print("Cleaning up title voice file...")
        for file in os.listdir("./voices/"):
            if is_file("./voices/" + file):
                os.remove("./voices/" + file)
        print("Cleaning up voices folder...")
        for file in os.listdir("./voices/comments"):
            if is_file("./voices/comments/" + file):
                os.remove("./voices/comments/" + file)
    if not os.path.exists("./imgs"):
        print("Creating comment images folder")
        os.makedirs("./imgs")
    else:
        print("Cleaning up image files...")
        for file in os.listdir("./imgs/"):
            if is_file("./imgs/" + file):
                os.remove("./imgs/" + file)
    if not os.path.exists("./result"):
        print("Creating results folder")
        os.makedirs("./result/")
    else:
        print("Cleaning up results folder...")
        for file in os.listdir("./result/"):
            print("Attempting to delete " + file)
            if is_file("./result/" + file):
                os.remove("./result/" + file)
                print("Deleted " + file)
    post = get_reddit_post()
    commentData = get_reddit_post_comments(post["link"])
    print("Found post at: " + post["link"])
    wrapper = textwrap.TextWrapper(width=50)
    word_list = wrapper.wrap(text=post["title"])
    txt = ""
    for word in word_list:
        txt += word + "\n"
    img = Image.new('RGB', (WIDTH, HEIGHT), color = (32, 32, 32))
    auth = ImageDraw.Draw(img)
    fontsize=32
    font2 = ImageFont.truetype("arial.ttf", fontsize)
    font = ImageFont.truetype("arial.ttf", 32)
    auth.text((0,0), "[OP] " + post["author"], font=font, fill=(0,0,255))
    lte = ImageDraw.Draw(img)
    lte.text((0,64), txt, font=font2, fill=(255,255,255))
    img.save('imgs/title.png')
    tts(post["title"])
    count = 0
    if commentData != []:
        x = 0
        for comment in commentData:
            if x == MAX_AUDIOS:
                break
            print("----------------------\n\n" + comment["text"] + "\n")
            wrapper = textwrap.TextWrapper(width=110)
            word_list = wrapper.wrap(text=comment["text"])
            txt = ""
            for word in word_list:
                txt += word + "\n"
            xj = re.findall("\[(.*?)\]\(.*?\)", txt)
            if xj != []:
                for xi in xj:
                    txt = re.sub("\[(.*?)\]\(.*?\)", xi, txt)
            img = Image.new('RGB', (WIDTH, HEIGHT), color = (32, 32, 32))
            auth = ImageDraw.Draw(img)
            font = ImageFont.truetype("arial.ttf", 32)
            font2 = ImageFont.truetype("arial.ttf", 16)
            auth.text((0,0), comment["author"], font=font, fill=(255,255,0))
            lte = ImageDraw.Draw(img)
            lte.text((0,64), txt, font=font2, fill=(255,255,255))
            img.save('imgs/comimg' + str(x) + '.png')
            tts(txt.replace("\n", " "), "comments/com" + str(x) + ".mp3")
            x = x + 1
            count += 1
    else:
        print("No comments found, restarting program...")
        main()
        return
    if count < MAX_AUDIOS:
        print("Not enough comments found, restarting program...")
        main()
        return
    for xj in range(-1, MAX_AUDIOS):
        if xj == -1:
            audio = MP3("./voices/synth.mp3")
            VIDEO_OUTPUT_TIME += audio.info.length
            AUDIO_TIMES.append(audio.info.length)
        else:
            audio = MP3("./voices/comments/com" + str(xj) + ".mp3")
            VIDEO_OUTPUT_TIME += audio.info.length
            AUDIO_TIMES.append(audio.info.length)
    audios = []
    for xj in range(-1, MAX_AUDIOS):
        if xj == -1:
            audio = AudioSegment.from_file("./voices/synth.mp3", format="mp3")
            audios.append(audio)
        else:
            audio = AudioSegment.from_file("./voices/comments/com" + str(xj) + ".mp3", format="mp3")
            audios.append(audio)
    combined = AudioSegment.empty()
    for audio in audios:
        combined += audio
    file_handle = combined.export("./result/finalaudio.mp3", format="mp3")
    fourcc = VideoWriter_fourcc(*'MP42')
    video = VideoWriter('./result/output.avi', fourcc, float(FPS), (WIDTH, HEIGHT))
    for _ in range(FPS*round(VIDEO_OUTPUT_TIME)):
        CURRENT_TIME += 0.06666666666666643
        print(CURRENT_TIME)
        if CURRENT_TIME >= AUDIO_TIMES[CURRENT_COMMENT+1] and CURRENT_COMMENT+2 != len(AUDIO_TIMES):
            CURRENT_TIME = 0
            CURRENT_COMMENT += 1
            print("increased comment counter")
        if CURRENT_COMMENT == -1:
            frame = cv2.imread('imgs/title.png')
            video.write(frame)
        else:
            frame = cv2.imread('imgs/comimg' + str(CURRENT_COMMENT) + '.png')
            video.write(frame)
    print("intended time: " + str(VIDEO_OUTPUT_TIME))
    video.release()
    os.system("ffmpeg -y -i ./result/output.avi -i ./result/finalaudio.mp3 -map 0:0 -map 1:0 -c:v copy -c:a copy ./result/output-final.avi")
    convert_avi_to_mp4("./result/output-final.avi", "./result/output-final")

main()
