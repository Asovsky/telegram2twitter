#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tweepy
import yaml
import time
import plain_db
import webgram
import post_2_album

with open('credential') as f:
	credential = yaml.load(f, Loader=yaml.FullLoader)

existing = plain_db.load('existing')

Day = 24 * 60 * 60

# def tweetMsg(msg):
# 	if msg.photo:
# 		filename = getTmpFile(msg)
# 		r = api.update_with_media(filename)
# 		os.system('rm ' + filename)
# 		return r
# 	return api.update_status(parseUrl(msg.text))

# def tweet(msg, chat):
# 	if not matchKey(msg.text, KEYS) and not matchKey(chat.title, KEYS): 
# 		return
# 	if not isMeaningful(msg):
# 		return
# 	tweetMsg(msg)

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

def run():
	for channel in credential['channels']:
		for album in getPosts(channel)[:1]:
			print(album)


if __name__ == '__main__':
	run()

 
auth = tweepy.OAuthHandler(credential['twitter_consumer_key'], credential['twitter_consumer_secret'])
auth.set_access_token(credential['twitter_access_token'], credential['twitter_access_secret'])
api = tweepy.API(auth)