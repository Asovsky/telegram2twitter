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
	posts = webgram.getPosts(channel)[1:]
	result += posts
	while posts and posts[0].time > (time.time() - 
			credential['channels'][channel]['back_days'] * Day):
		posts = webgram.getPosts(channel, posts[0].post_id, 
			direction='before', force_cache=True)[1:]
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

def getMediaSingle(url, api, album):
	cached_url.get(url, force_cache=True, mode='b')
	path = cached_url.getFilePath(url)
	if os.stat(path).st_size >= 4883 * 1024: # twitter limit
		return
	try:
		return api.media_upload(path).media_id
	except Exception as e:
		print('media upload failed:', str(e), album.url, url, path)

def getMedia(album, api):
	# tweepy does not support video yet. 
		# Hopefully they will support it soon: https://github.com/tweepy/tweepy/pull/1414
	# if album.video:
		# result = getMediaSingle(album.video, api, album)
		# if result:
		# 	return [result]
	result = [getMediaSingle(img, api, album) for img in album.imgs]
	return [item for item in result if item][:4]
		
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
			existing.update(album.url, -1) # place holder
			media_ids = [item for item in getMedia(album, api) if item]
			if not media_ids and (album.video or album.imgs):
				print('all media upload failed: ', album.url)
				continue
			try:
				result = api.update_status(status=status_text, media_ids=media_ids)
			except Exception as e:
				if 'Tweet needs to be a bit shorter.' not in str(e):
					print('send twitter status failed:', str(e), album.url)
				continue
			existing.update(album.url, result.id)
			
if __name__ == '__main__':
	run()