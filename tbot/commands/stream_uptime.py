from tbot.command import command
from tbot import utils
from datetime import datetime

@command('streamuptime', alias='sup')
async def stream_uptime(client, nick, channel, channel_id, target, args, **kwargs):
    if not client.channels[channel_id]['is_live']:
        msg = '@{}, the stream is offline'.format(kwargs['display-name'])
        client.send("PRIVMSG", target=target, message=msg)
        return

    if not client.channels[channel_id]['went_live_at']:
        msg = '@{}, the stream start time is unknown to me'.format(kwargs['display-name'])
        client.send("PRIVMSG", target=target, message=msg)
        return

    seconds = (datetime.utcnow() - client.channels[channel_id]['went_live_at']).total_seconds()
    msg = 'This stream has been live for {}'.format(utils.seconds_to_pretty(seconds))
    client.send("PRIVMSG", target=target, message=msg)