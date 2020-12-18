#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tweepy
import yaml

with open('credential') as f:
	credential = yaml.load(f, Loader=yaml.FullLoader)

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
 
auth = tweepy.OAuthHandler(credential['twitter_consumer_key'], credential['twitter_consumer_secret'])
# auth.set_access_token(credential['twitter_access_token'], credential['twitter_access_secret'])
# api = tweepy.API(auth)