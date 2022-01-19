#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telethon import TelegramClient
import asyncio
import tweepy
import yaml
import time
import plain_db
import webgram
import post_2_album
from bs4 import BeautifulSoup
import cached_url
import os
import export_to_telegraph
import sys
from telegram_util import isCN, removeOldFiles, matchKey, isUrl
from moviepy.editor import VideoFileClip

with open('credential') as f:
    credential = yaml.load(f, Loader=yaml.FullLoader)

existing = plain_db.load('existing')

Day = 24 * 60 * 60

def getCutoffTime(channel, posts):
    return time.time() - credential['channels'][channel]['padding_days'] * Day

def getPosts(channel):
    start = time.time()
    result = []
    posts = webgram.getPosts(channel)[1:]
    result += posts
    while posts and posts[0].time > (time.time() - 
            credential['channels'][channel]['back_days'] * Day):
        pivot = posts[0].post_id
        posts = webgram.getPosts(channel, posts[0].post_id, 
            direction='before')[1:]
        result += posts
    cutoff_time = getCutoffTime(channel, result)
    for post in result:
        if post.time > cutoff_time:
            continue
        try:
            yield post_2_album.get('https://t.me/' + post.getKey()), post
        except Exception as e:
            print('post_2_album failed', post.getKey(), str(e))

def getLinkReplace(url, album, item, all_text):
    if item.text.strip() == 'source':
        if 'douban.com/note/' in url and matchKey(all_text, ['telegra.ph', 'douban.com/note/']):
            return ''
        return '\n\n' + url + '\n' * len(item.find_all('br'))

    if 'telegra.ph' in url:
        soup = BeautifulSoup(cached_url.get(url, force_cache=True), 'html.parser')
        try:
            url = soup.find('address').find('a')['href']
        except:
            return ''

    title = export_to_telegraph.getTitle(url)
    if title in ['No Title', '[no-title]'] or matchKey(url, ['facebook', 'twitter', 'tumblr']):
        return '\n\n' + url
    return '\n\n【%s】 %s' % (title, url)

def getText(album, post):
    soup = BeautifulSoup(album.cap_html, 'html.parser')
    for item in soup.find_all('a'):
        if item.get('href'):
            item.replace_with(getLinkReplace(item.get('href'), album, item, soup.text))
    for item in soup.find_all('br'):
        item.replace_with('\n')
    text = soup.text.strip()
    if post.file:
        text += '\n\n' + album.url
    return text

async def getMediaSingle(api, post):
    fn = await post.download_media('tmp/')
    if not fn:
        return
    if fn.endswith('.mp4'):
        clip = VideoFileClip(fn)
        if clip.duration > 30: # twitter api limit video length limit, web/app limit is 140
            return
    # if os.stat(fn).st_size >= 4883 * 1024: # twitter limit
    #     return
    try:
        return api.media_upload(fn).media_id
    except Exception as e:
        print('media upload failed:', str(e))

async def getMedia(api, posts):
    result = []
    for post in posts:
        media = await getMediaSingle(api, post)
        if media:
            result.append(media)
        if len(result) >= 4:
            return result
    return result

# def matchLanguage(channel, status_text):
#     if not credential['channels'][channel].get('chinese_only'):
#         return True
#     return isCN(status_text)

twitter_api_cache = {}
def getTwitterApi(channel):
    user = credential['channels'][channel]['twitter_user']
    if user in twitter_api_cache:
        return twitter_api_cache[user]
    auth = tweepy.OAuthHandler(credential['twitter_consumer_key'], credential['twitter_consumer_secret'])
    auth.set_access_token(credential['twitter_users'][user]['access_key'], credential['twitter_users'][user]['access_secret'])
    api = tweepy.API(auth)
    twitter_api_cache[user] = api
    return api

client_cache = {}
async def getTelethonClient():
    if 'client' in client_cache:
        return client_cache['client']
    client = TelegramClient('session_file', credential['telegram_api_id'], credential['telegram_api_hash'])
    await client.start(password=credential['telegram_user_password'])
    client_cache['client'] = client   
    return client_cache['client']

async def getChannelImp(client, channel):
    if channel not in credential['id_map']:
        entity = await client.get_entity(channel)
        credential['id_map'][channel] = entity.id
        with open('credential', 'w') as f:
            f.write(yaml.dump(credential, sort_keys=True, indent=2, allow_unicode=True))
        return entity
    return await client.get_entity(credential['id_map'][channel])
        
channels_cache = {}
async def getChannel(client, channel):
    if channel in channels_cache:
        return channels_cache[channel]
    channels_cache[channel] = await getChannelImp(client, channel)
    return channels_cache[channel]

def getGroupedPosts(posts):
    grouped_id = None
    result = []
    for post in posts[::-1]:
        if not grouped_id and not post.grouped_id:
            return [post]
        if not grouped_id:
            grouped_id = post.grouped_id
        if post.grouped_id == grouped_id:
            result.append(post)
    return result

async def getMediaIds(api, channel, post, album):
    client = await getTelethonClient()
    entity = await getChannel(client, channel)
    posts = await client.get_messages(entity, min_id=post.post_id - 1, max_id = post.post_id + 9)
    media_ids = await getMedia(api, getGroupedPosts(posts))
    return list(media_ids)

async def post_twitter(channel, post, album, status_text):
    api = getTwitterApi(channel)
    media_ids = []
    if post.hasVideo() or album.video or album.imgs:
        media_ids = await getMediaIds(api, channel, post, album)
        if not media_ids:
            if 'debug' in sys.argv:
                print('all media upload failed: ', album.url)
            return
    try:
        return api.update_status(status=status_text, media_ids=media_ids)
    except Exception as e:
        if 'Tweet needs to be a bit shorter.' not in str(e):
            print('send twitter status failed:', str(e), album.url)
        

def lenOk(text, has_link):
    return sum([2 if isCN(char) else 1 for char in text]) <= 280 - 24 * has_link

def cutText(text, cut_text_retain_link, splitter):
    if not text:
        return ''
    result = ''
    last_good = text
    suffix = ''
    if cut_text_retain_link and isUrl(text.split()[-1]):
        suffix = ' ' + text.split()[-1]
    for substr in text.split(splitter)[:-1]:
        result += substr + splitter
        if lenOk(result, not not suffix):
            last_good = result
        else:
            return last_good + suffix
    result += text.split(splitter)[-1]
    if lenOk(result):
        return text
    else:
        return last_good + suffix

async def runImp():
    removeOldFiles('tmp', day=0.1)
    for channel in credential['channels']:
        for album, post in getPosts(channel):
            if existing.get(album.url):
                continue
            status_text = getText(album, post) or album.url
            if credential['channels'][channel].get('cut_text'):
                print('before cut', status_text)
                status_text = cutText(status_text, 
                    credential['channels'][channel].get('cut_text_retain_link'),
                    credential['channels'][channel].get('cut_text_splitter'))
                print('after cut', status_text)
            if len(status_text) > 280: 
                continue
            existing.update(album.url, -1) # place holder
            result = await post_twitter(channel, post, album, status_text)
            if not result:
                continue
            existing.update(album.url, result.id)
            return # only send one item every 10 minute

async def run():
    await runImp()
    if 'client' in client_cache:
        await client_cache['client'].disconnect()
        
if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run())
    loop.close()