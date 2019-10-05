import logging
from tbot import config, utils
from tbot.twitch_bot.bot_main import bot
from tbot.twitch_bot.var_filler import fill_from_dict
from .badge_log import badge_log

sub_mystery_gift = {}
sub_plan_names = {
    'Prime': 'Twitch Prime',
    '1000': 'Tier 1',
    '2000': 'Tier 2',
    '3000': 'Tier 3',
}


@bot.on('USERNOTICE')
async def usernotice(**kwargs):
    
    if kwargs['msg-id'] not in ('sub', 'resub', 'subgift', 
        'anonsubgift', 'giftpaidupgrade', 'submysterygift',
        'anonsubmysterygift'):
        return


    data = {
        'twitch_message': kwargs['system-msg'],
    }


    if kwargs['msg-id'] in ('sub', 'resub'):
        data['user'] = kwargs['display-name']
        data['months'] = kwargs['msg-param-cumulative-months']
        data['months_streak'] = kwargs['msg-param-streak-months']
        data['plan'] = sub_plan_names.get(kwargs['msg-param-sub-plan'], 'Unknown')

        alert = await bot.db.fetchone('''
            SELECT message FROM twitch_chat_alerts 
            WHERE channel_id=%s and type="sub" AND min_amount<=%s
            ORDER BY min_amount DESC
        ''', (
            kwargs['room-id'],
            data['months'],
        ))



    if kwargs['msg-id'] == 'giftpaidupgrade':
        data['user'] = kwargs['display-name']
        data['from_user'] = kwargs['msg-param-sender-name']
        alert = await bot.db.fetchone('''
            SELECT message FROM twitch_chat_alerts 
            WHERE channel_id=%s and type="giftpaidupgrade"
        ''', (
            kwargs['room-id'],
        ))


    
    if kwargs['msg-id'] in ('submysterygift', 'anonsubmysterygift',):
        gift_users = sub_mystery_gift.setdefault(kwargs['room-id'], {})
        gift_users[kwargs['user-id']] = {
            'count': int(kwargs['msg-param-mass-gift-count']),
            'data': kwargs,
        }



    if kwargs['msg-id'] in ('subgift', 'anonsubgift',):
        # Prevent spamming the chat when mystery subs are gifted
        if kwargs['room-id'] in sub_mystery_gift:
            if kwargs['user-id'] in sub_mystery_gift[kwargs['room-id']]:
                mg = sub_mystery_gift[kwargs['room-id']][kwargs['user-id']]
                mg['count'] -= 1
                if 0 == mg['count']:                 
                    data['user'] = mg['data']['display-name']
                    data['amount'] = mg['data']['msg-param-mass-gift-count']
                    data['plan'] = sub_plan_names.get(mg['data']['msg-param-sub-plan'], 'Unknown')
                    alert = await bot.db.fetchone('SELECT message FROM twitch_chat_alerts WHERE channel_id=%s and type="submysterygift"', (
                        kwargs['room-id'],
                    ))                    
                    del sub_mystery_gift[kwargs['room-id']][kwargs['user-id']]
                else:
                    return
        data['user'] = kwargs['display-name']
        data['to_user'] = kwargs['msg-param-recipient-display-name']
        data['plan'] = sub_plan_names.get(kwargs['msg-param-sub-plan'], 'Unknown')
        data['months'] = kwargs['msg-param-months']
        alert = await bot.db.fetchone('SELECT message FROM twitch_chat_alerts WHERE channel_id=%s and type="subgift"', (
            kwargs['room-id'],
        ))



    if alert:
        bot.send("PRIVMSG", target=kwargs['channel'], 
            message=fill_from_dict(alert['message'], data))

       
    await badge_log( 
        nick=kwargs['login'],
        target=kwargs['channel'],
        **kwargs
    )