import discord
from discord.ext import tasks
import pickle
import os
import config
import TETRIO_methods as tetr
intents = discord.Intents.all()
intents.members = True
intents.guilds = True
bot = discord.Bot(command_prefix = '!', intents = intents)

def dump_pickle(filename: str, data):
  try:
    with open(filename, 'wb') as f:
      pickle.dump(data, f)
      f.close()
  except:
    return

def open_pickle(filename: str, default = {}):
  ret = default
  try:
    with open(filename, 'rb') as f:
      ret = pickle.load(f)
      f.close()
  except:
    with open(filename, 'wb') as f:
      pickle.dump(ret, f)
      f.close()
  return ret

########################################################################
# Actual bot                                                           #
########################################################################

@bot.event
async def on_ready():
  print('We have logged in as {0.user}'.format(bot))
  os.makedirs('./tetrio', exist_ok = True)
  update_user.start()

@bot.slash_command(description = "Bot starts tracking you")
async def track(ctx):
  track_list = open_pickle('./tetrio/track.p', set())
  you = tetr.tetrio_get_user(ctx.author.id)
  if you['data'] == None:
    await ctx.respond('You have to link your discord account to your TETR.IO account.\n'
                      +"Here's how to do it.\n\n"
                      +'`1. Login to TETR.IO.`\n'
                      +'`2. Go to "config" -> "account".`\n'
                      +'`3. Go all the way down to "connections", then press "link".`', ephemeral = True)
    return
  you_id = you['data']['user']['_id']
  if you_id in track_list:
    await ctx.respond('You are already being tracked!', ephemeral = True)
    return
  track_list.add(you_id)
  tetr.tetrio_get_match(you_id)
  dump_pickle('./tetrio/track.p',track_list)
  await ctx.respond('Started tracking!\n'
                    +'TETR.IO username: ' + you['data']['user']['username'], ephemeral = True)

@bot.slash_command(description = "Bot stops tracking you")
async def untrack(ctx):
  track_list = open_pickle('./tetrio/track.p', set())
  you = tetr.tetrio_get_user(ctx.author.id)
  if you['data'] == None:
    await ctx.respond('You are not being tracked!', ephemeral = True)
    return
  you_id = you['data']['user']['_id']
  if you_id not in track_list:
    await ctx.respond('You are not being tracked!', ephemeral = True)
    return
  track_list.remove(you_id)
  dump_pickle('./tetrio/track.p',track_list)
  await ctx.respond('Stopped tracking!', ephemeral = True)


@tasks.loop(seconds=30)
async def update_user():
  track_list = open_pickle('./tetrio/track.p', set())
  for id in track_list:
    tetr.tetrio_get_match(id)

if __name__ == "__main__":
  bot.run(config.token_tetrio)