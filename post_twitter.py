#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telegram.ext import Updater, MessageHandler, Filters

import traceback as tb
import json
import tweepy
import yaml
import time
import urllib.request

with open('CREDENTIALS') as f:
	CREDENTIALS = json.load(f)

with open('KEYS') as f:
	KEYS = set(yaml.load(f, Loader=yaml.FullLoader))

with open('SUBSCRIPTION') as f:
	SUBSCRIPTION = yaml.load(f, Loader=yaml.FullLoader).keys()

test_channel = -1001159399317

EXPECTED_ERRORS = ['Message to forward not found', "Message can't be forwarded"]

def matchKey(t):
	if not t:
		return False
	for k in KEYS:
		if k in t:
			return True
	return False

def isUrl(t):
	for key in ['telegra.ph', 'com/']:
		if key in t:
			return True
	return False

def parseUrl(t):
	r = t
	for x in t.split():
		if not isUrl(x):
			continue
		if '://' in x:
			x = x[x.find('://') + 3:]
		for s in x.split('/'):
			if '?' in s:
				continue
			r = r.replace(x, urllib.request.pathname2url(x))
	return r

def isMeaningful(msg):
	if msg.photo:
		return True
	if not msg.text:
		return False
	if msg.text[0] == '/':
		return False
	return len(msg.text) > 10

def tweet(msg, chat):
	if (not matchKey(msg.text)) and (not matchKey(chat.title)):
		return
	if not isMeaningful(msg):
		return
	if msg.photo:
		filename = 'tmp' + msg.photo[-1].get_file().file_path.strip().split('/')[-1]
		msg.photo[-1].get_file().download(filename)
		api.update_with_media(filename)
		os.system('rm ' + filename)
		return 
	api.update_status(parseUrl(msg.text))

def manage(update, context):
	try:
		msg = update.effective_message 
		if (not msg) or msg.media_group_id or (not update.effective_chat):
			return
		if update.effective_chat.id not in SUBSCRIPTION:
			return
		tweet(msg, update.effective_chat)
	except Exception as e:
		if str(e) in ['Message to forward not found']:
			return
		if 'a bit shorter' in str(e):
			print(str(e))
			print(r.text)
			return
		print(e)
		tb.print_exc()

def backfill(chat_id, limit):
	for message_id in range(300, limit):
		try:
			time.sleep(1)
			r = updater.bot.forward_message(
				chat_id = test_channel, message_id = message_id, from_chat_id = chat_id)
			tweet(r, r.forward_from_chat)
		except Exception as e:
			if str(e) in EXPECTED_ERRORS:
				continue
			if 'a bit shorter' in str(e):
				print(str(e))
				print(r.text)
				return
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