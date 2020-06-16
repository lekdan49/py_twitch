import requests
import re
import json


# converts received json response to a dict
def json_to_dict(data, video=None):
    if video == None:
        data = json.loads(data.text)
        return data

    # clean up video json data then make dict
    elif video == True:
        data = json.loads(data.text)
        data = data["data"]
        data = str(data)
        data = data[1:-1]
        data = data.replace("'", "\"")
        data = json.loads(data)
        return data


# get access token for new twitch API
def get_token(client_id, secret, data="access_token"):
    print("Authenticating to Twitch API...\n")
    token = requests.post("https://id.twitch.tv/oauth2/token?client_id=" +
                          client_id+"&client_secret="+secret+"&grant_type=client_credentials")

    if token.ok:
        print("Authentication Successful!\n ")
    else:
        raise Exception(
            "Token failed to authenticate. Please check client_id and secret are correct! ")

    # returns dictionary with dict ['access_token', 'expires_in', 'token_type']
    token = json_to_dict(token)

    # returns the access token from dict
    return token[data]


class ParseVideoData():
    def __init__(self, client_id, token, video_id, user_id=None):
        self.video_id = video_id
        self.user_id = user_id
        self.headers = {
            'Authorization': 'Bearer ' + token,
            'Client-ID': client_id
        }

    def get_video_data(self):
        data = requests.get(
            "https://api.twitch.tv/helix/videos?id=" + self.video_id, headers=self.headers)

        # video parameter tells json_to_dict that we are passing video API data
        data = json_to_dict(data, video=True)
        return data
