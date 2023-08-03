import requests
import os
import pickle
import math
from datetime import timedelta, date, datetime
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

########################################################################
# Classes                                                              #
########################################################################

class match: # Saved at ./tetrio/user/{id}/yy/mm/dd
  def __init__(self, player1_id, player1_TR, player1_username, player1_glicko, player1_wins, player2_id, player2_TR, player2_username, player2_glicko, player2_wins, date: datetime):
    self.player1 = {'id': player1_id, 'username': player1_username, 'TR': player1_TR, 'glicko': player1_glicko, 'wins': player1_wins}
    self.player2 = {'id': player2_id, 'username': player2_username, 'TR': player2_TR, 'glicko': player2_glicko, 'wins': player2_wins}
    self.date = date
  
  def get_scores(self):
    return self.player1['wins'], self.player2['wins']
  
  def get_TR_dif(self):
    return self.player2['TR'] - self.player1['TR']
  
  def get_glicko_dif(self):
    return self.player2['glicko'] - self.player1['glicko']
  
class tetrio_user: # Saved at ./tetrio/user/{id}
  def __init__(self, id, username, discord_id, TR, glicko):
    self.id = id
    self.username = username
    self.discord_id = discord_id
    self.TR = TR
    self.glicko = glicko
  
  def update(self):
    URL = "https://ch.tetr.io/api/users/" + self.id
    r = requests.get(url=URL)
    ret = r.json()
    data = ret['data']['user']
    self.username = data['username']
    self.TR = data['league']['rating']
    self.glicko = data['league']['glicko']

  def dir(self, yy = 0, mm = 0, dd = 0): # returns directory of the user
    if yy == 0:
      return './tetrio/user/' + self.id
    return './tetrio/user/' + self.id + '/' + str(yy) + '/' + str(mm) + '/' + str(dd)
  

########################################################################
# API stuffs                                                           #
########################################################################

def tetrio_get_user(discord_id): # Gets tetrio id of the discord user. If does not exist, return None
  discord_id_to_tetrio_id = open_pickle('./tetrio/index.p')
  if discord_id in discord_id_to_tetrio_id:
    return discord_id_to_tetrio_id[discord_id]
  
  URL = "https://ch.tetr.io/api/users/search/" + str(discord_id)
  r = requests.get(url=URL)
  ret = r.json()

  if ret['data'] == None:
    return None
  user_id = ret['data']['user']['_id']
  os.makedirs('./tetrio/users/' + user_id, exist_ok=True)
  discord_id_to_tetrio_id[discord_id] = user_id
  dump_pickle('./tetrio/index.p', discord_id_to_tetrio_id)

  user_data = tetrio_fetch_user(user_id)
  user = tetrio_user(user_id, ret['data']['user']['username'], discord_id, user_data['league']['rating'], user_data['league']['glicko'])
  dump_pickle('./tetrio/user/' + user_id + '/info.p', user)

  return user_id

def tetrio_fetch_user(tetrio_id): # Gets tetrio data of the tetrio user.
  URL = "https://ch.tetr.io/api/users/" + tetrio_id
  r = requests.get(url=URL)
  ret = r.json()
  return ret['data']['user']

def tetrio_get_match(tetrio_id): #Gets new match infos of the tetrio user.
  URL = "https://ch.tetr.io/api/streams/league_userrecent_" + tetrio_id
  r = requests.get(url=URL)
  ret = r.json()['data']['records']
  s = open_pickle('./tetrio/users/' + tetrio_id + '/save.p', set())
  for i in range(len(ret)):
    data = ret[i]
    if data['_id'] in s:
      break
    s.add(data['_id'])

    date_string = data['ts']
    yymmdd, hhmiss = date_string.split('T')
    yy, mm, dd = yymmdd.split('-')
    hh, mi, ss = hhmiss.split(':')
    ss = ss.split('.')[0]
    date = datetime(int(yy), int(mm), int(dd), int(hh), int(mi), int(ss))

    player1 = {'id': '', 'TR': 0, 'glicko': 0, 'wins': 0}
    player2 = {'id': '', 'TR': 0, 'glicko': 0, 'wins': 0}
    # implement here
    player1['id'] = data['endcontext'][0]['user']['_id']
    player1['username'] = data['endcontext'][0]['user']['username']

    player1_data = tetrio_fetch_user(player1['id'])

    player1['TR'] = player1_data['league']['rating']
    player1['glicko'] = player1_data['league']['glicko']
    player1['wins'] = data['endcontext'][0]['wins']

    player2['id'] = data['endcontext'][1]['user']['_id']
    player2['username'] = data['endcontext'][1]['user']['username']

    player2_data = tetrio_fetch_user(player2['id'])

    player2['TR'] = player2_data['league']['rating']
    player2['glicko'] = player2_data['league']['glicko']
    player2['wins'] = data['endcontext'][1]['wins']

    if player1['id'] != tetrio_id:
      player_temp = player1
      player1 = player2
      player2 = player_temp
    # end of implement
    match_data = match(player1['id'], player1['TR'], player1['username'], player1['glicko'], player1['wins'],
                       player2['id'], player2['TR'], player2['username'], player2['glicko'], player2['wins'],
                       date)

    os.makedirs('./tetrio/users/' + tetrio_id + '/matches/' + yy + '/' + mm + '/' + dd, exist_ok=True)
    os.makedirs('./tetrio/users/' + tetrio_id + '/matches/all', exist_ok=True)
    dump_pickle('./tetrio/users/' + tetrio_id + '/matches/' + yy + '/' + mm + '/' + dd + '/' + hh + '-' + mi + '-' + ss + '.p', match_data)
    dump_pickle('./tetrio/users/' + tetrio_id + '/matches/all/' + yy + '-' + mm + '-' + dd + '-' + hh + '-' + mi + '-' + ss + '.p', match_data)
  dump_pickle('./tetrio/users/' + tetrio_id + '/save.p', s)

########################################################################
# Processing data                                                      #
########################################################################

# Used smth similar to elo rating. May be less accurate
# Needs to consider RD value, should upgrade from getting data methods

def winrate_to_glicko(winrate):
  return math.log10((1 / winrate) - 1) * 400

def glicko_to_winrate(dif):
  return 1 / (1 + math.pow(10,dif/400))

def ranked_by_day(id, yy, mm, dd):
  dir = './tetrio/users/' + id + '/matches/' + str(yy) + '/' + str(mm) + '/' + str(dd)
  try:
    replays = os.listdir(dir)
    replays.sort()
  except:
    return None
  data = []
  for i in range(len(replays)):
    data.append(open_pickle(dir + '/' + replays[i])) # brings class "match"
  return data

def ranked_by_duration(id, y1, m1, d1, y2, m2, d2):
  date1 = date(y1, m1, d1)
  date2 = date(y2, m2, d2)
  delta = date2 - date1
  ret = []
  for i in range(delta.days + 1):
    current_date = (date1 + timedelta(days=i))
    yy, mm, dd = current_date.year, current_date.month, current_date.day
    if mm < 10:
      mm = '0' + str(mm)
    if dd < 10:
      dd = '0' + str(dd)
    data = ranked_by_day(id, yy, mm, dd)
    if data == [] or data == None:
      continue
    ret.append({'year': str(yy), 'month': mm, 'day': dd, 'data': data})
  return ret

def analyze_ranked_data(data):
  wins = 0
  loses = 0
  avg_glicko = 0
  glicko_dif = 0
  TR_dif = 0
  for i in range(len(data['data'])):
    w1, w2 = data['data'][i].get_scores()
    wins += w1
    loses += w2
    avg_glicko += (w1 + w2) * data['data'][i].player2['glicko']
    glicko_dif += data['data'][i].get_glicko_dif()
    TR_dif += data['data'][i].get_TR_dif()

  avg_glicko /= float(wins + loses)
  if wins == 0:
    performance = -1
  elif loses == 0:
    performance = -2
  else:
    performance = avg_glicko + winrate_to_glicko(wins / (wins + loses))
  glicko_dif /= float(wins + loses)
  TR_dif /= float(wins + loses)
  return wins, loses, avg_glicko, performance, glicko_dif, TR_dif

def tetrio_analyze(tetrio_id, y1, m1, d1, y2, m2, d2):
  ranked_data = ranked_by_duration(tetrio_id, y1, m1, d1, y2, m2, d2)
  ranked_analysis = []
  for i in range(len(ranked_data)):
    wins, loses, avg_glicko, performance, glicko_dif, TR_dif = analyze_ranked_data(ranked_data[i])
    ranked_analysis.append({'wins': wins, 'loses': loses, 'avg_glicko': avg_glicko, 'performance': performance, 'glicko_dif': glicko_dif, 'TR_dif': TR_dif})
  return ranked_data, ranked_analysis
