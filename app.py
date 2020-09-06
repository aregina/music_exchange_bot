import json
import logging
import os
import re

import boto3
import requests
from chalice import Chalice

from chalicelib.utils import convert_yam_link_to_spotify, convert_spotify_link_to_yam

app = Chalice(app_name='music-exchange-api')
app.log.setLevel(logging.INFO)

secrets_manager = boto3.client('secretsmanager')
music_exchange_bot_secrets = json.loads(
    secrets_manager.get_secret_value(SecretId='music_exchange_bot_secret')['SecretString']
)

bot_token = music_exchange_bot_secrets['music_exchange_bot_token']
BOT_URL = f'https://api.telegram.org/bot{bot_token}/'

# spotify access
os.environ['SPOTIPY_CLIENT_ID'] = music_exchange_bot_secrets['spotify_client_id']
os.environ['SPOTIPY_CLIENT_SECRET'] = music_exchange_bot_secrets['spotify_client_secret']


@app.route('/convert_link', methods=['POST'])
def convert_link():
    request_body = app.current_request.json_body
    app.log.info(f"{request_body=}")
    chat_id = request_body['message']['chat']['id']
    link = request_body['message'].get('text')
    app.log.info(f"{chat_id=}, {link=}")
    if link:
        if link in ['/help', '/start']:
            response = "Just post Spotify or Yandex Music track link here and I'll convert it respectively"
        elif re.match('^https://music.yandex.ru/.*', link):
            response = convert_yam_link_to_spotify(link)
        elif re.match('^https://open.spotify.com/.*', link):
            response = convert_spotify_link_to_yam(link)
        else:
            response = "It doesn't look like a link to Spotify or Yandex Music. Try again"
    else:
        response = "Send me link to Yandex.Music or Spotify"
    app.log.info(response)
    send_message_to_bot(response, chat_id)
    return {'statusCode': 200}


def send_message_to_bot(text, chat_id):
    url = BOT_URL + f'sendMessage?text={text}&chat_id={chat_id}'
    requests.get(url)
