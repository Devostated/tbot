import logging
from tbot.twitch_bot.bot_main import bot

badges = {}

@bot.on('PRIVMSG')
async def badge_log(nick, target, message, **kwargs):
    if not badges:
        for channel in bot.channels:
            badges[channel] = {}
        rows = await bot.db.fetchall('SELECT * FROM twitch_badges')
        for r in rows:
            if r['channel_id'] in badges:
                badges[r['channel_id']][r['user_id']] = {
                    'sub': r['sub'],
                    'bits': r['bits'],
                }
    if not kwargs['badges']:
        return

    sub = None
    bits = None
    for b in kwargs['badges'].split(','):
        b2 = b.split('/')
        if b2[0] == 'subscriber':
            sub = int(b2[1])
        elif b2[0] == 'bits':
            bits = int(b2[1])

    user_id = int(kwargs['user-id'])
    channel_id = int(kwargs['room-id'])

    update = False
    if user_id in badges[channel_id]:
        if badges[channel_id][user_id]['sub'] != sub:
            update = True        
        if badges[channel_id][user_id]['bits'] != bits:
            update = True
    else:
        update = True
        badges[channel_id][user_id] = {}

    if update:
        await bot.db.execute('''
            INSERT INTO twitch_badges (channel_id, user_id, sub, bits) 
            VALUES (%s, %s, %s, %s) 
            ON DUPLICATE KEY UPDATE sub=VALUES(sub), bits=VALUES(bits)
            ''', 
            (channel_id, user_id, sub, bits)
        )
        badges[channel_id][user_id]['sub'] = sub
        badges[channel_id][user_id]['bits'] = bits