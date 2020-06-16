import json
import math
import os
import re
import shutil
import subprocess
import time
from multiprocessing.pool import ThreadPool as Pool

import ffmpeg
import requests
from progress.bar import Bar

from modules.classes import *


def get_duration(data):

    # data is currently present like 2h21m32s
    duration = data["duration"]

    # put duration into readable list format "HH","MM","SS" using re
    if 'h' not in duration:
        duration = (re.split('h|m|s', duration))
        duration.insert(0, "")
    elif 'h' in duration:
        duration = (re.split('h|m|s', duration))
        if len(duration) > 3:
            l = len(duration)
            l = l - 3
            del duration[-l]
    elif 's' not in duration:
        duration = (re.split('h|m|s', duration))
        duration.insert(2, "")
    elif 'm' not in duration:
        duration = re.split('h|m|s', duration)
        duration.insert(1, "")

    # remove blank list value

    return duration

# create download URL using thumbnail URL


def parse_thumbnail_url(data):
    thumbnail = data["thumbnail_url"]
    username = data["user_name"]
    url = (re.split('_|/', thumbnail))
    username_pos = url.index(username.lower())
    url_part_1 = url[username_pos - 1]
    url_part_2 = url[username_pos + 1]
    url_part_3 = url[username_pos + 2]
    # print(url_part_1, url_part_2)
    return url_part_1, url_part_2, url_part_3


"""
How make_urls() works:
The video duration list is obtained from the get_duration() function, we then
assign the variables hour, minute and second to the respective places from the list video_duration.

We multiply the hour variable by 60 then add and convert the minute and hour variables to seconds.
Twitch transmits video through .ts files. Each .ts file is ~10 seconds long. We can calculate the total number of .ts files
that are in a Twitch Vod by dividing the total seconds of the Vod that we calculated earlier by 10.


"""


def make_urls(data):

    video_duration = get_duration(data)
    try:
        hour = int(video_duration[0])
    except:
        hour = 0
        pass
    try:
        minute = int(video_duration[1])
    except:
        minute = 0
        pass
    try:
        second = int(video_duration[2])
    except:
        second = 0
        pass

    hour = hour * 60
    minute = hour + minute
    second = (minute * 60) + second
    total_ts_files = (second / 10) + 10

    # round up
    total_ts_files = math.ceil(total_ts_files)

    # print(data["thumbnail_url"])
    username = data["user_name"].lower()
    url_1, url_2, url_3 = parse_thumbnail_url(data)

    # hold urls after creating them
    ts_url_list = []

    # initialise urls_done to increment every loop
    urls_done = 0

    # progress bar
    bar = Bar("Creating downloads", max=total_ts_files)

    # _ means we aren't using the variable
    for _ in range(total_ts_files):
        urls_done = str(urls_done)

        # make url
        url = "https://d2nvs31859zcd8.cloudfront.net/" + url_1 + "_" + \
            username + "_" + url_2 + "_" + url_3 + "/720p60/" + urls_done + ".ts"

        # add url to list
        ts_url_list.append(url)

        urls_done = int(urls_done)

        # advance counter for urls_done
        urls_done += 1

        # advance progress bar
        bar.next()

    # stop bar
    bar.finish()

    return ts_url_list

# use url from created urls instead


def download(url, file_name, data):
    if url.ok:
        with open(data + '/' + file_name, 'wb') as out_file:
            shutil.copyfileobj(url.raw, out_file)
    elif url.status_code == 429:
        print("rate limited! Pausing for a minute! ")
        time.sleep(60)
        download(url, file_name, data)
    # if file does not exist skip
    elif url.status_code == 403:
        pass


def schedule_downloads(file_name, url, data, headers, bar):
    file_name = str(file_name)
    url = requests.get(url, stream=True, headers=headers)
    download(url, file_name, data)

    bar.next()


def start(urls, data, token, threads, client_id):
    # Downloading from urls created
    file_name = 0
    bar = Bar("Downloading video files:", max=len(urls))
    headers = {
        'Authorization': 'Bearer ' + token,
        'Client-ID': client_id
    }

    pool_size = int(threads)
    pool = Pool(pool_size)

    for url in urls:
        file_name = (re.split('/', url))
        file_name = file_name[5]
        pool.apply_async(schedule_downloads,
                         (file_name, url, data, headers, bar))
        # schedule_downloads(file_name, url, data, headers, bar)

    pool.close()
    pool.join()
    bar.finish()


def download_video(video_id, token, client_id):

    # get video data from API in dict format
    # ['id', 'user_id', 'user_name', 'title', 'description', 'created_at', 'published_at', 'url', 'thumbnail_url', 'viewable', 'view_count', 'language', 'type', 'duration']
    data = ParseVideoData(client_id, token, video_id).get_video_data()

    # make download urls using API data and store in list
    urls = make_urls(data)

    # create folder to store videos
    directory = data["user_name"]
    try:
        os.mkdir("videos")
    except:
        pass

    try:
        os.mkdir("videos/" + directory)
    except:
        pass

    # create subfolder from video id
    directory = "videos" + "/" + directory + "/" + data["id"]
    try:
        os.mkdir(directory)
    except:
        pass

    # create info file with dict data in created folder
    with open(directory + '/' + 'info.txt', 'w') as file:
        x = json.dumps(data)
        file.write(x)

    get_thread_input = input(
        "How many threads would you like to run? (I recommend 4-6 if potato internet) ")
    # attempt to download all urls from list
    start(urls, directory, token, get_thread_input, client_id)

    try:
        os.remove(directory + '/' + video_id + '.mp4')
    except:
        pass

    vid_files = os.listdir(directory)
    return vid_files, directory


def join_videos(vid_files, directory, video_id):
    directory = directory + '/'
    # remove 'info.txt'
    vid_files.remove('info.txt')

    vid_files = [s[:-3] for s in vid_files]

    vid_files.sort(key=int)
    vid_files = [s + '.ts' for s in vid_files]

    try:
        os.remove('ffmpeg.txt')
        os.remove('output.mp4')
    except:
        pass

    for item in vid_files:
        with open('ffmpeg.txt', 'a') as f:
            f.write('file ' + "'" + directory + item + "'")
            f.write('\n')

    subprocess.call(
        'ffmpeg -f concat -safe 0 -i ffmpeg.txt -c copy output.mp4')
    shutil.move('output.mp4', directory + video_id + '.mp4')
    os.remove("ffmpeg.txt")
    print("Removing fragments...\n")

    for file in os.listdir(directory):
        if '.ts' in file:
            os.remove(directory + file)
    print("done")
