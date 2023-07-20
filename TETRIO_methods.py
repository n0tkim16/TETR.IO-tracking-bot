import requests
import os
import pickle
import math
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
    return ret

def tetrio_fetch_user(tetrio_id):
    URL = "https://ch.tetr.io/api/users/" + tetrio_id
    r = requests.get(url=URL)
    ret = r.json()
    return ret

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
  power_of_dif = (1 / winrate) - 1
  dif400 = math.log10(power_of_dif)
  return dif400 * 400

def glicko_to_winrate(dif):
  return 1 / (1 + math.pow(10,dif/400))

def analyze_by_day(id, yy, mm, dd):
  dir = './tetrio/users/' + id + '/matches/' + str(yy) + '/' + str(mm) + '/' + str(dd)
  replays = os.listdir(dir)
  my_win = 0
  my_lose = 0
  rounds = 0
  ur_glicko = 0
  for replay in replays:
    replay_info = open_pickle(dir + '/' + replay, {})
    if replay_info['ur_TR'] == -1 or replay_info['my_TR'] == -1:
      continue
    my_win += replay_info['my_score']
    my_lose += replay_info['ur_score']
    rounds += replay_info['my_score'] + replay_info['ur_score']
    ur_glicko += (replay_info['my_score'] + replay_info['ur_score']) * replay_info['ur_glicko']
  ur_glicko /= float(rounds)
  if my_lose == 0:
    return "You won every round, so I cannot evaluate your performance!"
  if my_win == 0:
    return "You lost every round, so I cannot evaluate your performance!"
  expected_win_rate = (my_win * my_win) / (my_win * my_win + my_lose * my_lose) # pythagorean win percentage
  expected_glicko_dif = winrate_to_glicko(expected_win_rate)
  performance = ur_glicko + expected_glicko_dif
  return performance


def analyze_by_duration(id, y1, m1, d1, y2, m2, d2):
  yy = y1
  mm = m1
  dd = d1
  monthes = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
  while True:
    y = str(yy)
    m = str(mm)
    if mm < 10:
      m = '0' + m
    d = str(dd)
    if dd < 10:
      d = '0' + d
    if yy == y2 and mm == m2 and dd == d2:
      break
    eval = analyze_by_day(id, y, m, d)
    if type(eval) == type('asdf'):
      pass
    if yy % 400 == 0 or (yy % 100 != 0 and yy % 4 == 0):
      monthes[2] = 29
    else:
      monthes[2] = 28
    dd += 1
    if dd > monthes[mm]:
      dd = 1
      mm += 1
    if mm == 13:
      mm = 1
      yy += 1
