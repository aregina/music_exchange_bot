import json
import re

import requests
import spotipy
from bs4 import BeautifulSoup
from spotipy.oauth2 import SpotifyClientCredentials


def get_title_from_yam(link):
    """
    link example link = 'https://music.yandex.ru/album/6062534/track/21491669'
                 link = 'https://music.yandex.ru/album/2489597'
                 link = 'https://music.yandex.ru/artist/519183'

    :param link:
    :return:
    """
    yam_page_html = requests.get(link).text
    yam_page = BeautifulSoup(yam_page_html, 'html.parser')
    track_title = yam_page.find_all('meta', {'property': 'og:title'})[0]['content']
    #track_title = yam_page.title.string.split('. Слушать онлайн на Яндекс.Музыке')[0]
    return track_title.replace(' — ', ' ')


def get_playlist_data_from_yam(link):
    """
    link example link = 'https://music.yandex.ru/users/music.partners/playlists/2084'
    :param link:
    :return:
    """
    yam_page_html = requests.get(link).text
    yam_page = BeautifulSoup(yam_page_html, 'html.parser')
    playlist_content = yam_page.script.contents[0]
    play_list_tracks = json.loads(playlist_content)['track']
    return [track['url'] for track in play_list_tracks]


def get_spotify_link(title, sp_client, type):
    spotify_search_result = sp_client.search(q=title, type=type)
    if spotify_search_result[f'{type}s']['items']:
        spotify_url = spotify_search_result[f'{type}s']['items'][0]['external_urls']
        return spotify_url['spotify']
    else:
        return "Sorry, Nothing found :("


def get_yam_track_link(title, obj_type):
    ya_music_search_page_html = requests.get('https://music.yandex.ru/search?text='+title).text
    ya_music_search_page = BeautifulSoup(ya_music_search_page_html, 'html.parser')
    links = None
    if obj_type == 'track':
        links = ya_music_search_page.find_all('div', {'class': 'd-track__name'})
    elif obj_type == 'album':
        links = ya_music_search_page.find_all('div',{'class': 'album__title'})
    elif obj_type == 'artist':
        links = ya_music_search_page.find_all('span',{'class': 'd-artists'})
    if links:
        first_track_link = links[0].contents[0]['href']
        return 'https://music.yandex.ru'+first_track_link
    else:
        return "Sorry, Nothing found :("


def get_obj_title_from_spotify(link, link_type, sp_client):
    """
    link example link = 'https://open.spotify.com/track/5Ic5QeBGzZO8wXm8JGSG31'
                 link = 'https://open.spotify.com/album/6rLuPANmVobaOWZ6qyLUph'
                 link = 'https://open.spotify.com/artist/7pmh8z3Pzz2u68OmucFSZz'
    :param link:
    :param sp_client:
    :return:
    """
    if link_type == 'track':
        sp_track = sp_client.track(link)
        title = sp_track['name'] + ' ' + sp_track['artists'][0]['name']
    elif link_type == 'album':
        sp_album = sp_client.album(link)
        title = sp_album['name'] + ' ' + sp_album['artists'][0]['name']
    elif link_type == 'artist':
        sp_artist = sp_client.artist(link)
        title = sp_artist['name']
    else:
        title = ''
    return title


def convert_yam_link_to_spotify(link):
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials())
    title_to_search = get_title_from_yam(link)
    type_to_search = yam_link_type(link)
    if type_to_search == 'unknown':
        return 'Unsupported link type. I can convert links to tracks, albums and artists only.'
    spotify_track_link = get_spotify_link(title_to_search, sp, type_to_search)
    response = f"Yandex Music: {link}\nSpotify: {spotify_track_link}"
    return response


def convert_spotify_link_to_yam(link):
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials())
    type_to_search = spotify_link_type(link)
    if type_to_search == 'unknown':
        return 'Unsupported link type. I can convert links to tracks, albums and artists only.'
    obj_title = get_obj_title_from_spotify(link, type_to_search, sp)
    yam_link = get_yam_track_link(obj_title, type_to_search)
    response = f"Yandex Music: {yam_link}\nSpotify: {link}"
    return response


def yam_link_type(link):
    if re.match('^https://music.yandex.ru/album/\d+/track/\d+$', link):
        link_type = 'track'
    elif re.match('^https://music.yandex.ru/album/\d+$', link):
        link_type = 'album'
    elif re.match('^https://music.yandex.ru/artist/\d+$', link):
        link_type = 'artist'
    else:
        link_type = 'unknown'
    return link_type


def spotify_link_type(link):
    if re.match('^https://open.spotify.com/track/.*', link):
        link_type = 'track'
    elif re.match('^https://open.spotify.com/album/.*', link):
        link_type = 'album'
    elif re.match('^https://open.spotify.com/artist/.*', link):
        link_type = 'artist'
    else:
        link_type = 'unknown'
    return link_type
