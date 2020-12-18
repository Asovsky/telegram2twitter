#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tweepy
import yaml
import time
import plain_db
import webgram
import post_2_album
from bs4 import BeautifulSoup
import cached_url
import os

with open('credential') as f:
	credential = yaml.load(f, Loader=yaml.FullLoader)

existing = plain_db.load('existing')

Day = 24 * 60 * 60

def getPosts(channel):
	start = time.time()
	result = []
	posts = webgram.getPosts(channel, force_cache=True)[1:]
	result += posts
	while posts and posts[0].time > time.time() - 2 * Day:
		posts = webgram.getPosts(channel, posts[0].post_id, 
			direction='before')[1:]
		result += posts
	return [post_2_album.get('https://t.me/' + post.getKey()) for post in result if post.time < time.time() - Day]

# there is channel specific optimization
def getText(channel, html):
	soup = BeautifulSoup(html, 'html.parser')
	for item in soup.find_all('a'):
		if item.get('href'):
			if 'telegra.ph' in item.get('href') and 'douban.com/note/' in html:
				item.decompose()
			elif 'douban.com/' in item.get('href'):
				item.replace_with('\n\n' + item.get('href'))
			else:
				item.replace_with(item.get('href'))
	for item in soup.find_all('br'):
		item.replace_with('\n')
	return soup.text.strip()

class ImgVideoTooLargeException(Exception):
	pass

def getMediaSingle(url, api):
	cached_url.get(url, force_cache=True, mode='b')
	path = cached_url.getFilePath(url)
	if os.stat(path).st_size >= 4883 * 1024: # twitter limit
		raise ImgVideoTooLargeException('img/video too large')
	print(url, path)
	return api.media_upload(path).media_id

def getMedia(album, api):
	if album.video:
		return [getMediaSingle(album.video, api)]
	return [getMediaSingle(img, api) for img in album.imgs[:4]]
		
def run():
	for channel in credential['channels']:
		auth = tweepy.OAuthHandler(credential['twitter_consumer_key'], credential['twitter_consumer_secret'])
		auth.set_access_token(credential['channels'][channel]['access_key'], credential['channels'][channel]['access_secret'])
		api = tweepy.API(auth)
		for album in getPosts(channel):
			status_text = getText(channel, album.cap_html)
			if len(status_text) > 280: 
				continue
			if existing.get(album.url):
				continue
			existing.update(album.url, 0) # place holder
			try:
				media_ids = getMedia(album, api)
			except ImgVideoTooLargeException:
				continue
			print('len_media_ids', len(media_ids))
			result = api.update_status(status=status_text, media_ids=media_ids)
			existing.update(album.url, result.id)
			time.sleep(600)
			
if __name__ == '__main__':
	run()