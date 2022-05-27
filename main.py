import discord
import os
import sys
import subprocess
import pickle

from discord.utils import get
from discord.flags import Intents
from discord.ext import commands
from discord.ext import tasks
from discordpy_slash.slash import *
from discord.ext.commands import has_permissions

import datetime

import operator
from multiprocessing import Process

import urllib, json

py_version = str(sys.version_info[0]) + "." + str(sys.version_info[1]) + "." + str(sys.version_info[2])

upvote_emoji = "<:Upvote:";
downvote_emoji = "<:Downvote:";

posts = {}
post_depth = 5000

auto_del = {}

prev_debug_load = "0"

_log = []
loaded = False

Intents = discord.Intents.default()
Intents.reactions = True
Intents.members = True
client = commands.Bot(command_prefix="!", intents=Intents)#discord.Client()

command_dict = {
	"voterat" : [{}],
	"auto_delete" : [{
		"name" : "10 seconds", "value" : "10" },{
		"name" : "20 seconds", "value" : "20" },{
		"name" : "30 seconds", "value" : "30" },{
		"name" : "1 minute", "value" : "60" },{
		"name" : "2 minutes", "value" : "120" },{
		"name" : "10 minutes", "value" : "600"},{
		"name" : "30 minutes", "value" : "1800" },{
		"name" : "1 hour", "value" : "3600" },{
		"name" : "2 hour", "value" : "7200" },{
		"name" : "12 hour", "value" : "43200" },{
		"name" : "Reset", "value" : "none"
	}],
	"leaderboard" : [{
		"name" : "5", "value" : "5" },{
		"name" : "10", "value" : "10"
	}]
}

def log(item) :
	_log.append(item)
	with open('log.pkl', 'wb') as f:
		pickle.dump(_log, f)

async def renew_msg(msg):
	out = msg
	for guild in client.guilds:
		for channel in guild.text_channels:
			try :
				ctx = channel
				out = await ctx.fetch_message(msg.id)
			except :
				ctx = channel
	return out
				
async def nickname(member: discord.Member, nick):
	await member.edit(nick=nick)

async def redo_votes(channel):
	async with channel.typing():
		i = 1
		for item in posts:
			debug_load((i/len(posts))*100,"Loading posts")
			votes = 0
			for emoji in item.reactions:
			  if(str(emoji.emoji).startswith(upvote_emoji)):
			  	votes += emoji.count
			  if(str(emoji.emoji).startswith(downvote_emoji)):
			  	votes -= emoji.count
			posts[item] = votes
			i = i + 1
		print_status()

def server_print(text,queue):
		queue.append(text)

def debug_load(percent,prev) :
	global prev_debug_load
	if(prev_debug_load != str(round(percent))):
		os.system("clear")
		print(prev)
		print(str(round(percent)) + "%")
		prev_debug_load = str(round(percent))

def filter_posts(p,guild) :
	dict = {}
	for item in p:
		if isinstance(item.channel, discord.channel.DMChannel):
			p.pop[item]
		if(item.channel.guild.id == guild.id) :
			dict[item] = p[item]
	return dict

async def load_posts(amount = 5000):
	out = {}
	i1 = 0
	for guild in client.guilds:
		i1 = i1 + 1
		i2 = 0
		for channel in guild.text_channels:
			i2 = i2 + 1
			ctx = channel

			# Get messages:
			os.system("clear")
			print("Getting messages in channel '" + channel.name + "' from guild '" + guild.name +  "'")
			try :
				messages = await channel.history(limit=amount).flatten()
			except:
				print("Failed to get messages")
				pass
			# Build message dict:
			i3 = 0
			for msg in messages:
				out[msg] = 0
				debug_load((i3/len(messages))*100,"Loading posts in channel '" + channel.name + "' from guild '" + guild.name +  "'")
				i3=i3+1
				
			await client.change_presence(activity=discord.Game(name="Loading '" + guild.name + "'"))
	posts.clear()
	posts.update(out)

def print_status():
	os.system("clear")
	print('Logged in as {0.user}'.format(client))
	print("-------------------")
	print("Active servers (" + str(len(client.guilds)) + "):")
	for guild in client.guilds:
		print(guild.name)
	print("------------------")
	print("Console log: ")
	i = 0
	for item in _log:
		if(len(_log) - i <= 10) :
			print(item)
		i = i + 1

# Auto del loop
@tasks.loop(seconds=1.0)
async def loop(): 
	if(loaded) :
		print_status()
		if(os.environ["restartbot"] == "true"):
			await client.close()
			print("Restarting bot")
	now = datetime.datetime.now()
	try:
		for item in auto_del:
			channel = client.get_channel(item)
			messages = await client.get_channel(item).history(limit=5000).flatten()
			delqueue = []
			count = 0
			for msg in messages:
				if((now - msg.created_at).total_seconds() > auto_del[item]):
					if((now - msg.created_at).days > 13):
						count = count + 1
						await msg.delete()
					else:
						delqueue.append(msg)
			count = len(delqueue) + count
			if(len(delqueue) > 0) :
				await channel.delete_messages(delqueue)
			if(count > 0) :
				log(str(now) + " : Auto deleted " + str(count) + " messages from guild '" + channel.guild.name + "' in channel '" + channel.name + "'")
	except Exception as e:
		log(str(now) + " : Error in loop() " + str(e))

loop.start()
				
# ON READY :

@client.event
async def on_ready():
		os.environ["restartbot"] = "false"
		await sync_all_commands(client,False,"Loading",False,["help","help2","scratchybot"],command_dict,None)
		await client.change_presence(activity=discord.Game(name="Loading..."))
		# Restore
		global _log
		global auto_del
		try:
			with open('auto_del.pkl', 'rb') as f:
				auto_del = pickle.load(f)
		except:
			print("auto_del.pkl file is not written")
			
		try:
			with open('log.pkl', 'rb') as f:
				_log = pickle.load(f)
		except:
			print("log.txt file is not written")
			
		await load_posts(post_depth)
		await client.change_presence(activity=discord.Game(name="/leaderboard for most upvoted/downvoted messages."))
		global loaded
		loaded = True

# / Commands:

@client.command()
async def voterat(ctx):
		now = datetime.datetime.now()
		log(str(now) + " : User '" + ctx.message.author.name + "' used command '/voterat' in guild '" + ctx.guild.name + "'")
		embed=discord.Embed(
			title="Voterat - 0.8.1", 
			description = """Random bot made by .muckrat, i add whatever the hell i want to this.
			Commands:
			--------
			/voterat - lists commands and gives bot info (duh)
			/leaderboard - displays the most liked post and the least liked post in the server
			/leaderboard [amount] - displays the top [amount] posts in the server
			/auto_delete [seconds] - makes all messages get deleted in the channel after [seconds], make [seconds] 'Reset' to disable auto delete in the channel

			Vote System:
			-----------
			Emojis called "Upvote" will be treated as upvotes and emojis called "Downvote" will be treated as downvotes.

			Other Info:
			----------
			Use this link for sharing this bot https://discord.com/api/oauth2/authorize?client_id=753498523659665468&permissions=295279258737&scope=bot%20applications.commands
			Message .muckrat#1991 if something goes wrong (which will probably happen)
			""", 
			color=0xFF5733
		)
		await ctx.send(embed=embed)

@client.command()
async def leaderboard(ctx,top="0"):
	now = datetime.datetime.now()
	log(str(now) + " : User '" + ctx.message.author.name + "' used command '/leaderboard' in guild '" + ctx.guild.name + "'")
	await redo_votes(ctx.channel)

	if(len(posts) == 0):
		await ctx.send("There are no recorded posts to send")
	else:
		a_dictionary = filter_posts(posts,ctx.guild)
		highest = max(a_dictionary, key=a_dictionary.get)
		lowest = min(a_dictionary, key=a_dictionary.get)

	if(top == "0") :
			#Define Embed (very messy)
			embed=discord.Embed(title="LEADERBOARD", description = "Most popular (upvoted) [**'" + highest.content + "'**](" + highest.jump_url +") by " + highest.author.mention + " in channel " + highest.channel.mention + " with " + str(posts[highest]) + " votes.\n" + "Most unpopular (downvoted) [**'" + lowest.content + "'**](" + lowest.jump_url + ") by " + lowest.author.mention + "in channel" + lowest.channel.mention +" with " + str(posts[lowest]) + " votes.\n" , color=0xFF5733)
			# End embed
			await ctx.send(embed=embed)
	else:
				senddict = dict(sorted(a_dictionary.items(), key=operator.itemgetter(1), reverse=True)[:int(top)])
				sendmsg = ""
				for key, value in senddict.items():
					sendmsg = sendmsg + '["' + str(key.content) + '"](' + key.jump_url + ') ('+ str(value) + ")\n"
				senddict = dict(sorted(a_dictionary.items(), key=operator.itemgetter(1), reverse=False)[:int(top)])
				sendmsg2 = ""
				for key, value in senddict.items():
					sendmsg2 = sendmsg2 + '["' + str(key.content) + '"](' + key.jump_url + ') ('+ str(value) + ")\n"
					
				embed=discord.Embed(title="LEADERBOARD", description = "Top " + (top) + " best posts:\n" + sendmsg + "\nTop " + (top) + " worst posts:\n" + sendmsg2 , color=0xFF5733)
				await ctx.send(embed=embed)

@client.command()
async def auto_delete(ctx,time="10"):
	now = datetime.datetime.now()
	log(str(now) + " : User '" + ctx.message.author.name + "' used command '/auto_delete' in guild '" + ctx.guild.name + "'")
	if(ctx.message.author.guild_permissions.manage_channels):
		if(time=="none"):
			auto_del.pop(ctx.channel.id)
			await ctx.send("Removed auto delete")
			with open('auto_del.pkl', 'wb') as f:
				pickle.dump(auto_del, f)
		else:
			auto_del[ctx.channel.id] = int(time)
			await ctx.send("Making channel '" + ctx.channel.name + "' auto delete your dirty messages after " + time + " seconds")
			with open('auto_del.pkl', 'wb') as f:
				pickle.dump(auto_del, f)
	else :
		await ctx.send("Insufficient permissions")

		
# ! Commands

@client.event
async def on_message(message):
		if not ( message in posts ):
			votes = 0
			for emoji in message.reactions:
				if(str(emoji.emoji).startswith(upvote_emoji)):
					votes += 1
				if(str(emoji.emoji).startswith(downvote_emoji)):
					votes -= 1
			posts[message] = votes
		bot_mod = False
		try:
			if(not bot_mod) :
				if(message.author.name == ".muckrat"):	
					bot_mod = True

		except:
			bot_mod = True
		if message.author == client.user:
				return

		# Bot admin commands
		if message.content.startswith('!log') and bot_mod:
			# write to file
			with open("log.txt", "w") as file:
				file.write("\n".join(_log))
    
			# send file to Discord in message
			with open("log.txt", "rb") as file:
				await message.channel.send("Latest log: ", file=discord.File(file, "log.txt"))

			os.remove("log.txt")
				
		if message.content.startswith('!auto_del') and bot_mod:
			for item in auto_del:
				channel = client.get_channel(item)
				await message.channel.send("'" + channel.name + "' in guild '" + channel.guild.name + "', delete time: " + str(auto_del[item]))
				
		if message.content.startswith('!send ') and bot_mod:
				commands = message.content.split(' ')
				for guild in client.guilds:
					if(guild.name == commands[1].replace('_',' ')):
						sendchannel = discord.utils.get(guild.text_channels, name="general")
						await sendchannel.send(commands[2].replace('_',' '))
						await message.channel.send('Sent message "' + commands[2].replace('_',' ') + '" in guild "' + commands[1].replace('_',' ') + '"')
						return
				await message.channel.send("failed to send")
		if message.content.startswith('!grab ') and bot_mod:
				commands = message.content.split(' ')
				for guild in client.guilds:
					if(guild.name == commands[1].replace('_',' ')):
						invite = await guild.text_channels[0].create_invite(reason="wanted to do a little trolling")
						await message.channel.send(f"Here's your invite: {invite}")
						return
				await message.channel.send("failed to create invite")
		if message.content.startswith('!sb.guilds') and bot_mod:
				await message.channel.send("Active servers (" + str(len(client.guilds)) + "):")
				for guild in client.guilds:
					await message.channel.send(guild.name)
		if message.content.startswith("!sb.config") and bot_mod:
				ctx = message.channel
				await ctx.send('configuring bot...')
				embed=discord.Embed(title="Scratchy Bot v-0.8.5", description = "Using discord.py on python3.\n !leaderboard to veiw most upvoted/downvoted posts.\nMade by big man Scratchy" , color=0xFF5733)
				await ctx.send(embed=embed)
		if message.content.startswith('!sb.home') and bot_mod:
				await message.channel.send('Set bot home to #' + message.channel.name)
				home = message.channel
				f = open("home.dat", "w")
				f.write(str(home.id))
				f.close()
		if message.content.startswith('!shutdown') and bot_mod:
				log(message.author.name + " shut down the bot.")
				await message.channel.send("Shutting down...")
				await client.close()
		if message.content.startswith('!restart') and bot_mod:
				log(message.author.name + " restarted the bot.")
				os.environ["restartbot"] = "true"

@client.event
async def on_reaction_add(reaction, user):
	if str(reaction.emoji).startswith(upvote_emoji):
		try :
			posts[(reaction.message)] = posts[(reaction.message)] + 1
		except :
			posts[(reaction.message)] = 1
		await redo_votes(reaction.message.channel)
	elif str(reaction.emoji).startswith(downvote_emoji):
		try :
			posts[(reaction.message)] = posts[(reaction.message)] - 1
		except :
			posts[(reaction.message)] = -1
		await redo_votes(reaction.message.channel)
	else:
		print(reaction.emoji)

@client.event
async def on_raw_reaction_add(payload):
	for item in posts:
		if item.id == payload.message_id:
			posts.pop(item)
	posts[await client.get_channel(payload.channel_id).fetch_message] = 0

@client.event
async def on_raw_reaction_remove(payload):
	for item in posts:
		if item.id == payload.message_id:
			posts.pop(item)
	posts[await client.get_channel(payload.channel_id).fetch_message] = 0

post_depth = int(sys.argv[1])
if(sys.argv[2] == 'Y'):
	client.run(sys.argv[3])
else:
	client.run(sys.argv[3], bot=False)