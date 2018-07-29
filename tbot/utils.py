import re
import logging
from tbot import config

def safe_username(user):
    return re.sub('[^a-zA-Z0-9_]', '', user)[:25]

def seconds_to_pretty(seconds):
    seconds = round(seconds)
    if seconds < 60:
        return '{} seconds'.format(seconds)

    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)

    ts = []
    if hours == 1:
        ts.append('1 hour')
    elif hours > 1:
        ts.append('{} hours'.format(hours))
    if minutes == 1:
        ts.append('1 min')
    elif minutes > 1:
        ts.append('{} mins'.format(minutes))

    return ' '.join(ts)

async def twitch_request(ahttp, url, params=None, headers={}):    
    headers.update({
        'Authorization': 'Bearer {}'.format(config['twitch']['token'])
    })
    async with ahttp.get(url, params=params, headers=headers) as r:
        if r.status == 200:
            data = await r.json()
            return data

_cached_user_ids = {}
async def twitch_lookup_usernames(ahttp, usernames):
    global _cached_user_ids
    url = 'https://api.twitch.tv/helix/users'
    users = []
    lookup_usernames = list(usernames)
    for u in usernames:
        ul = u.lower()
        if ul in _cached_user_ids:
            lookup_usernames.remove(u)
            users.append({
                'id': _cached_user_ids[ul],
                'user': ul, 
            })
    if lookup_usernames:
        for unames in chunks(lookup_usernames, 100):
            params = [('login', name) for name in unames]
            data = await twitch_request(ahttp, url, params)
            if data:
                for d in data['data']:
                    _cached_user_ids[d['login'].lower()] = d['id']
                    users.append({'id': d['id'], 'user': d['login']})
    return users

async def twitch_lookup_user_id(ahttp, username):
    users = await twitch_lookup_usernames(ahttp, [username])
    if not users:
        return
    return users[0]['id']

def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]

def pluralize(num, word):
    if num != 1:
        word += 's'
    return '{} {}'.format(num, word)