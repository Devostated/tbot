import logging, re
from tbot.twitch_bot.bot_base import bot
from tbot import utils

from . import base

filters = {}

async def check(target, message, kwargs):
    if kwargs['room-id'] not in filters:
        return
    f = filters[kwargs['room-id']]

    excluded = await base.is_excluded(bot, f, kwargs)
    if excluded:
        return
    
    matches = utils.link.find_links(message)
    if matches: # check if the user is permitted to post links
        has_permit = await base.has_permit(bot, kwargs)
        if has_permit:
            return
    else:
        return

    for m in matches:
        if m[2] in f['whitelist']:
            continue
        await base.warn_or_timeout(bot, 'link', target, f, kwargs)
        return True

@bot.on('AFTER_CONNECTED')
async def connected(**kwargs):
    if not filters:
        await load()

@bot.on('REDIS_SERVER_COMMAND')
async def redis_server_command(cmd, cmd_args):
    if cmd == 'reload_filter_link':
        await load(cmd_args[0])

async def load(channel_id=None):
    global filters
    sql = '''
        SELECT f.*, l.whitelist 
        FROM twitch_filters f 
            LEFT JOIN twitch_filter_link l 
                ON (l.channel_id=f.channel_id) 
        WHERE 
            type="link"
    '''
    args = []
    if channel_id:
        sql += ' AND f.channel_id=%s'
        args.append(channel_id)
    rows = await bot.db.fetchall(sql, args)
    filters_ = filters if channel_id else {}
    for r in rows:
        r['whitelist'] = utils.json_loads(r['whitelist']) if r['whitelist'] else []
        filters_[r['channel_id']] = r
    filters = filters_
