import requests
import os
import pickle
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