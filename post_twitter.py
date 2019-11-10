#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telegram.ext import Updater, MessageHandler, Filters

import traceback as tb
import json
import tweepy

with open('CREDENTIALS') as f:
	CREDENTIALS = json.load(f)

with open('KEYS') as f:
	KEYS = set(json.load(f))

def matchKey(t):
	for k in keys:
		if k in t:
			return True
	return False

def manage(update, context):
	try:
		msg = update.message 
		if (not msg) or msg.media_group_id or (not update.effective_chat):
			return
		if (not matchKey(msg.text)) and \
			(not matchKey(update.effective_chat.first_name)):
			return
		print(msg.photo)
		if msg.photo:
			return api.update_with_media(msg.photo[-1])
		api.update_status(msg.text)
	except Exception as e:
		print(e)
		tb.print_exc()

auth = tweepy.OAuthHandler(CREDENTIALS['twitter_consumer_key'], CREDENTIALS['twitter_consumer_secret'])
auth.set_access_token(CREDENTIALS['twitter_access_token'], CREDENTIALS['twitter_access_secret'])
api = tweepy.API(auth)

updater = Updater(CREDENTIALS['bot_token'], use_context=True)
dp = updater.dispatcher

dp.add_handler(MessageHandler(Filters.update.channel_posts, manage))