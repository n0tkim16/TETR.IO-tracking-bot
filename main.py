import discord
from discord.ext import tasks
import datetime
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
  try:
    with open(filename, 'rb') as f:
      ret = pickle.load(f)
      f.close()
  except:
    return default
  return ret

def is_valid_date(y, m, d):
  days = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
  if y % 400 == 0 or (y % 100 != 0 and y % 4 == 0):
    days[2] =29
  if m < 1 or m > 12:
    return False
  if d < 0 or d > days[m]:
    return False
  return True

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
  if you == None:
    await ctx.respond('You have to link your discord account to your TETR.IO account.\n'
                      +"Here's how to do it.\n\n"
                      +'`1. Login to TETR.IO.`\n'
                      +'`2. Go to "config" -> "account".`\n'
                      +'`3. Go all the way down to "connections", then press "link".`', ephemeral = True)
    return
  if you in track_list:
    await ctx.respond('You are already being tracked!', ephemeral = True)
    return
  result = tetr.tetrio_get_match(you)
  if result == -1:
    await ctx.respond('You do not have Tetra League Rating!\n' +
                      'Play at least 10 Tetra League game to have your rating.', ephemeral = True)
    return
  track_list.add(you)
  dump_pickle('./tetrio/track.p',track_list)
  you_info = tetr.tetrio_fetch_user(you)
  await ctx.respond('Started tracking!\nTETR.IO username: `' + you_info['username'] + '`', ephemeral = True)

@bot.slash_command(description = "Bot stops tracking you")
async def untrack(ctx):
  track_list = open_pickle('./tetrio/track.p', set())
  you = tetr.tetrio_get_user(ctx.author.id)
  if you == None:
    await ctx.respond('You have to link your discord account to your TETR.IO account.\n'
                      +"Here's how to do it.\n\n"
                      +'`1. Login to TETR.IO.`\n'
                      +'`2. Go to "config" -> "account".`\n'
                      +'`3. Go all the way down to "connections", then press "link".`', ephemeral = True)
    return
  
  if you not in track_list:
    await ctx.respond('You are not being tracked!\n' +
                      'Use `/track` to be tracked', ephemeral = True)
    return
  
  track_list.remove(you)
  dump_pickle('./tetrio/track.p',track_list)
  await ctx.respond('Stopped tracking!', ephemeral = True)

@bot.slash_command(description = "Analyzes your Tetra League games at given duration.")
async def analyze(ctx,
                  duration: discord.Option(str, 'Choose duration', choices = ['Today', 'Yesterday', 'Last 7 days']), # add Last 28 days, Last month, custom duration later
                  display: discord.Option(str, 'Choose display style', choices = ['Normal', 'Detailed']),
                  public: discord.Option(str, 'Choose if others can see the analysis', choices = ['True', 'False'])): 
  index = open_pickle('./tetrio/index.p')
  if ctx.author.id not in index:
    await ctx.respond('You are not being tracked!\nUse `/track` to be tracked and be able to use this command.', ephemeral = True)
    return
  tetrio_id = index[ctx.author.id]
  today = datetime.date.today()
  if duration == 'Today':
    data, analysis = tetr.tetrio_analyze(tetrio_id, today.year, today.month, today.day, today.year, today.month, today.day)
  if duration == 'Yesterday':
    today = today - datetime.timedelta(days = 1)
    data, analysis = tetr.tetrio_analyze(tetrio_id, today.year, today.month, today.day, today.year, today.month, today.day)
  if duration == 'Last 7 days':
    today1 = today - datetime.timedelta(days = 6)
    data, analysis = tetr.tetrio_analyze(tetrio_id, today1.year, today1.month, today1.day, today.year, today.month, today.day)
  # if duration == 'Last 28 days':
  #   today1 = today - todaytime.timedelta(days = 27)
  #   analyze_data = tetr.tetrio_analyze(tetrio_id, today1.year, today1.month, today1.day, today.year, today.month, today.day)
  # if duration == 'Last month':
  #   pass
  # if duration == 'Custom duration':
  #   await ctx.respond("Use `/analyze_custom` instead. Here's how to use it.\n" +
  #                     "`/analyze_custom 2023 01 01 2023 06 30` means you want to analyze your matches\n" +
  #                     "from January 1st 2023 to June 30th 2023.", ephemeral = True)
  # Output format:
  # 2023-07-01
  # vs asdf(24900 TR, 2950 glicko) 7:6
  # ...

  # 13 Rounds, 7 wins, 6 loses ??.??%
  # Performance 24900 TR, 2950 glicko
  # ...

  # 26 Rounds, 13 wins, 13 loses 50.00%
  # Average Performance 24900 TR, 2950 glicko

  # data, analysis is list of {'year': yy, 'month': mm, 'day': dd, 'data': ranked_by_day(id, yy, mm, dd)}, 
  # list of {'wins': wins, 'loses': loses, 'avg_glicko': avg_glicko, 'performance': performance, 'glicko_dif': glicko_dif, 'TR_dif': TR_dif}
  msg = ''
  detail_msg = ''
  wins = 0
  loses = 0
  avg_glicko = 0
  print(data)
  for i in range(len(data)):
    wins_local = 0
    loses_local = 0
    msg = msg + data[i]['year'] + '-' + data[i]['month'] + '-' + data[i]['day'] + '\n'
    detail_msg = detail_msg + data[i]['year'] + '-' + data[i]['month'] + '-' + data[i]['day'] + '\n'
    for j in range(len(data[i]['data'])):
      match = data[i]['data'][j]
      wins += match.player1['wins']
      loses += match.player2['wins']
      wins_local += match.player1['wins']
      loses_local += match.player2['wins']
      detail_msg = detail_msg + 'vs `' + match.player2['username'] + '`(' + str(int(match.player2['TR'])) + 'TR, ' + str(int(match.player2['glicko'])) + ') ' + str(match.player1['wins']) + ':' + str(match.player2['wins']) + '\n'
    msg = msg + str(wins_local + loses_local) + ' rounds, ' + str(wins_local) + ' wins, ' + str(loses_local) + ' loses, ' + str(round(float(100 * wins_local / (wins_local + loses_local)), 2)) + '%\n\n'
    detail_msg = detail_msg + str(wins_local + loses_local) + ' rounds, ' + str(wins_local) + ' wins, ' + str(loses_local) + ' loses, ' + str(round(float(100 * wins_local / (wins_local + loses_local)), 2)) + '%\n\n'
    
    avg_glicko += (wins_local + loses_local) * analysis[i]['avg_glicko']
  if wins + loses == 0:
    await ctx.respond(str(today.year) + ' ' + str(today.month) + ' ' + str(today.day), ephemeral = True)
    # await ctx.respond('There is nothing to analyze!', ephemeral = True)
    return
  avg_glicko /= (wins + loses)
  if display == 'Normal':
    if public == 'True':
      await ctx.respond(msg)
    else:
      await ctx.respond(msg, ephemeral = True)
  else:
    if public == 'True':
      await ctx.respond(detail_msg)
    else:
      await ctx.respond(detail_msg, ephemeral = True)

@bot.slash_command(description = 'Gives information about other commands')
async def help(ctx):
  await ctx.respond('`/help` : Gives information about other commands\n' + 
                 '`/track` : Bot starts tracking you\n' + 
                 '`/untrack` : Bot stops tracking you\n' + 
                 '`/analyze (duration) (display) (public)` : Analyzes your Tetra League games at given duration.\n' + 
                 '(duration) sets the duration to analyze your Tetra League games.\n' +
                 '(display) sets the detailness of the analysis.\n' + 
                 '(public) sets if the analysis is public or not.')



    

# @bot.slash_command(description = 'Analyzes your Tetra League games at given duration.')
# async def analyze_custom(ctx,
#                          y1: discord.Option(int),
#                          m1: discord.Option(int, choices = [i for i in range(1,13)]),
#                          d1: discord.Option(int, choices = [i for i in range(1,32)]),
#                          y2: discord.Option(int),
#                          m2: discord.Option(int, choices = [i for i in range(1,13)]),
#                          d2: discord.Option(int, choices = [i for i in range(1,32)])):
#   index = open_pickle('./tetrio/user/index.p')
#   if ctx.author.id not in index:
#     await ctx.respond('You are not being tracked!\n' +
#                    'Use `/track` to be tracked and be able to use this command.', ephemeral = True)
#     return
#   if (not is_valid_date(y1, m1, d1)) or (not is_valid_date(y2, m2, d2)):
#     await ctx.respond('Invalid date.', ephemeral = True)
#     return
#   date1 = date(y1, m1, d1)
#   date2 = date(y2, m2, d2)
#   if date1 > date2:
#     await ctx.respond('Starting date should be prior to the end date.', ephemeral = True)
#     return

# @bot.slash_command(description = "Gives detailed informations about commands")
# async def help(ctx,
#                command: discord.Option(str, 'Choose commands', choices = ['analyze'])):
#   if command == 'analyze':
#     pass

@tasks.loop(seconds=30)
async def update_user():
  track_list = open_pickle('./tetrio/track.p', set())
  for id in track_list:
    tetr.tetrio_get_match(id)

if __name__ == "__main__":
  bot.run(config.token_tetrio)
