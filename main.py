import shutil
import time

from modules.classes import get_token
from modules.download import download_video, join_videos

"""
Goal of this program is to download videos from a streamers channel.
If a new video is available it will check if the video is already downloaded then download it.
"""

client_id = ""
secret = ""


if __name__ == '__main__':
    video_id = input('Please enter the video ID you want to download: ')
    # get_input = str(get_input)

    # get OAuth token
    # parameter 'data=' can be 'access_token', 'expires_in', 'token_type'. Defaults to 'access_token'
    token = get_token(client_id, secret, data="access_token")

    if video_id.isnumeric():
        vid_files, directory = download_video(video_id, token, client_id)
        # remove info.txt from list
        join_videos(vid_files, directory, video_id)

    else:
        print('Please enter a valid ID ')
