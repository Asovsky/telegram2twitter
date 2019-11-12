#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from telegram.ext import Updater, MessageHandler, Filters

import traceback as tb
import json
import tweepy
import yaml
import time
import os
import urllib.request
import threading
from telegram_util import matchKey, parseUrl, isMeaningful, getTmpFile

with open('CREDENTIALS') as f:
	CREDENTIALS = json.load(f)

with open('KEYS') as f:
	KEYS = set(yaml.load(f, Loader=yaml.FullLoader))

with open('SUBSCRIPTION') as f:
	SUBSCRIPTION = yaml.load(f, Loader=yaml.FullLoader).keys()

LOOP_INTERVAL = 1 # change to 7200

test_channel = -1001159399317
queue = []

EXPECTED_ERRORS = ['Message to forward not found', "Message can't be forwarded"]

def tweet(msg, chat):
	if not matchKey(msg.text, KEYS) and not matchKey(chat.title, KEYS): 
		return
	if not isMeaningful(msg):
		return
	if msg.photo:
		filename = getTmpFile(msg)
		api.update_with_media(filename)
		os.system('rm ' + filename)
		return 
	# Deal with msg update
	api.update_status(parseUrl(msg.text))

# TODO: try catch decorator
def manage(update, context):
	global queue
	msg = update.effective_message 
	if not msg:
		return
	if not update.effective_chat:
		return
	if update.effective_chat.id not in SUBSCRIPTION:
		return
	queue.append((update.effective_chat.id, msg.message_id))

def backfill(chat_id, fill_range):
	for message_id in fill_range:
		queue.append((chat_id, message_id))
 
auth = tweepy.OAuthHandler(CREDENTIALS['twitter_consumer_key'], CREDENTIALS['twitter_consumer_secret'])
auth.set_access_token(CREDENTIALS['twitter_access_token'], CREDENTIALS['twitter_access_secret'])
api = tweepy.API(auth)

updater = Updater(CREDENTIALS['bot_token'], use_context=True)
updater.dispatcher.add_handler(MessageHandler(Filters.update.channel_posts, manage))

# TODO: try catch decorator
def loopImp():
	if not queue:
		return
	chat_id, msg_id = queue.pop()
	r = updater.bot.forward_message(
		chat_id = test_channel, message_id = msg_id, from_chat_id = chat_id)
	tweet(r, r.forward_from_chat)

def loop():
    loopImp()
    threading.Timer(LOOP_INTERVAL, loop).start() 

threading.Timer(1, loop).start()

updater.start_polling()
updater.idle()