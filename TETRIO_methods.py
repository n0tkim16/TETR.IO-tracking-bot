import requests
import os
import pickle
import math
from datetime import timedelta, date
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
# API stuffs                                                           #
########################################################################

def tetrio_get_user(discord_id):
  URL = "https://ch.tetr.io/api/users/search/" + str(discord_id)
  r = requests.get(url=URL)
  ret = r.json()
  if ret['data'] == None:
    return None
  user_id = ret['data']['user']['_id']
  os.makedirs('./tetrio/users/' + user_id, exist_ok=True)
  return user_id

def tetrio_fetch_user(tetrio_id):
  URL = "https://ch.tetr.io/api/users/" + tetrio_id
  r = requests.get(url=URL)
  ret = r.json()
  return ret

def tetrio_fetch_username(tetrio_id):
  data = tetrio_fetch_user(tetrio_id)
  return data['data']['user']['username']

def tetrio_get_match(user_id):
  URL = "https://ch.tetr.io/api/streams/league_userrecent_" + user_id
  r = requests.get(url=URL)
  ret = r.json()['data']['records']
  s = open_pickle('./tetrio/users/' + user_id + '/save.p', set())
  for i in range(len(ret)):
    if ret[i]['_id'] in s:
      break
    s.add(ret[i]['_id'])
    date_string = ret[i]['ts']
    yymmdd, hhmiss = date_string.split('T')
    yy, mm, dd = yymmdd.split('-')
    hh, mi, ss = hhmiss.split(':')
    ss = ss.split('.')[0]
    round_info = {'win': None,
                  'my_id': user_id, 'ur_id': '',
                  'my_name': '', 'ur_name': '',
                  'my_score': 0, 'ur_score': 0,
                  'my_glicko': 0, 'ur_glicko': 0,
                  'my_TR': 0, 'ur_TR': 0,
                  'date': {'year': yy, 'month': mm, 'day': dd, 'hour': hh, 'minute': mi, 'second': ss}}
    me = None
    you = None
    me_ctx = None
    you_ctx = None
    if ret[i]['endcontext'][0]['user']['_id'] == user_id:
      round_info['win'] = True
      me = tetrio_fetch_user(ret[i]['endcontext'][0]['user']['_id'])
      me_ctx = ret[i]['endcontext'][0]
      you = tetrio_fetch_user(ret[i]['endcontext'][1]['user']['_id'])
      you_ctx = ret[i]['endcontext'][1]
      round_info['ur_id'] = ret[i]['endcontext'][1]['user']['_id']
    else:
      round_info['win'] = False
      me = tetrio_fetch_user(ret[i]['endcontext'][1]['user']['_id'])
      me_ctx = ret[i]['endcontext'][1]
      you = tetrio_fetch_user(ret[i]['endcontext'][0]['user']['_id'])
      you_ctx = ret[i]['endcontext'][0]
      round_info['ur_id'] = ret[i]['endcontext'][0]['user']['_id']
    round_info['my_name'] = tetrio_fetch_username(round_info['my_name'])
    round_info['ur_name'] = tetrio_fetch_username(round_info['ur_name'])
    round_info['my_score'] = me_ctx['wins']
    round_info['ur_score'] = you_ctx['wins']
    round_info['my_glicko'] = me['data']['user']['league']['glicko']
    round_info['ur_glicko'] = you['data']['user']['league']['glicko']
    round_info['my_TR'] = me['data']['user']['league']['rating']
    round_info['ur_TR'] = you['data']['user']['league']['rating']
    os.makedirs('./tetrio/users/' + user_id + '/matches/' + yy + '/' + mm + '/' + dd, exist_ok=True)
    os.makedirs('./tetrio/users/' + user_id + '/matches/all', exist_ok=True)
    dump_pickle('./tetrio/users/' + user_id + '/matches/' + yy + '/' + mm + '/' + dd + '/' + hh + '-' + mi + '-' + ss + '.p', round_info)
    dump_pickle('./tetrio/users/' + user_id + '/matches/all/' + yy + '-' + mm + '-' + dd + '-' + hh + '-' + mi + '-' + ss + '.p', round_info)
  dump_pickle('./tetrio/users/' + user_id + '/save.p', s)

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
  replays = os.listdir(dir)
  data = []
  for replay in replays:
    replay_info = open_pickle(dir + '/' + replay, {})
    data.append({'my_name': replay_info['my_name'], 'ur_name': replay_info['ur_name'], 'wins': replay_info['my_score'], 'loses': replay_info['ur_score'],
                    'my_TR': replay_info['my_TR'], 'ur_TR': replay_info['ur_TR'],
                    'my_glicko': replay_info['my_glicko'], 'ur_glicko': replay_info['ur_glicko']})
  return data

def ranked_by_duration(id, y1, m1, d1, y2, m2, d2):
  date1 = date(y1, m1, d1)
  date2 = date(y2, m2, d2)
  delta = date2 - date1
  ret = []
  for i in range(delta.days + 1):
    current_date = (date1 + timedelta(days=i))
    yy, mm, dd = current_date.year, current_date.month, current_date.day
    ret.append({'year': yy, 'month': mm, 'day': dd, 'data': ranked_by_day(yy, mm, dd)})
  return ret

def analyze_ranked_data(data):
  wins = 0
  loses = 0
  avg_glicko = 0
  return_string = ''
  for i in range(len(data)):
    
    wins += data[i]['wins']
    loses += data[i]['loses']
    avg_glicko += (data[i]['wins'] + data[i]['loses']) * data[i]['ur_glicko']

  avg_glicko /= float(wins + loses)
