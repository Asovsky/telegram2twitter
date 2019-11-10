#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telegram.ext import Updater, MessageHandler, Filters

import traceback as tb
import json
import tweepy
import yaml

with open('CREDENTIALS') as f:
	CREDENTIALS = json.load(f)

with open('KEYS') as f:
	KEYS = set(yaml.load(f, Loader=yaml.FullLoader))

def matchKey(t):
	print(t)
	if not t:
		return False
	for k in KEYS:
		if k in t:
			return True
	return False

def manage(update, context):
	try:
		msg = update.effective_message 
		if (not msg) or msg.media_group_id or (not update.effective_chat):
			return
		if (not matchKey(msg.text)) and \
			(not matchKey(update.effective_chat.title)):
			return
		if msg.photo:
			filename = 'tmp.' + msg.photo[-1].get_file().file_path.strip().split('/')[-1]
			msg.photo[-1].get_file().download(filename)
			return api.update_with_media(filename)
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

updater.start_polling()
updater.idle()