import logging, random
import asyncio, aiohttp, aiomysql
import sqlalchemy as sa
from sqlalchemy_aio import ASYNCIO_STRATEGY
from datetime import datetime
from tbot.twitch_bot.unpack import rfc2812_handler
from tbot import config
from tbot.twitch_bot import bot
from tbot.twitch_bot import commands, tasks

bot.channels = {}

@bot.on('CLIENT_CONNECT')
async def connect(**kwargs):
    if not bot.http_session:
        bot.http_session = aiohttp.ClientSession()
    if not bot.pool:
        bot.pool = await aiomysql.create_pool(
            host=config['mysql']['host'], 
            port=config['mysql']['port'],
            user=config['mysql']['user'], 
            password=config['mysql']['password'],
            db=config['mysql']['database'], 
            loop=bot.loop,
            charset='utf8mb4',
            use_unicode=True,
            echo=False,
        )

    if bot.pong_check_callback:
        bot.pong_check_callback.cancel()

    logging.info('IRC Connecting to {}:{}'.format(config['twitch']['irc_host'], config['twitch']['irc_port']))
    if config['twitch']['token']:
        bot.send('PASS', password='oauth:{}'.format(config['twitch']['token']))
    bot.send('NICK', nick=config['twitch']['user'])
    bot.send('USER', user=config['twitch']['user'], realname=config['twitch']['user'])

    # Don't try to join channels until the server has
    # sent the MOTD, or signaled that there's no MOTD.
    done, pending = await asyncio.wait(
        [bot.wait("RPL_ENDOFMOTD"),
         bot.wait("ERR_NOMOTD")],
        loop=bot.loop,
        return_when=asyncio.FIRST_COMPLETED
    )

    bot.send_raw('CAP REQ :twitch.tv/tags')
    bot.send_raw('CAP REQ :twitch.tv/commands')
    bot.send_raw('CAP REQ :twitch.tv/membership')

    # Cancel whichever waiter's event didn't come in.
    for future in pending:
        future.cancel()

    channels = await get_channels()
    for c in channels:
        bot.send('JOIN', channel='#'+c['name'])

    if not bot.channels:
        for c in channels:
            bot.channels[c['channel_id']] = {
                'channel_id': c['channel_id'],
                'name': c['name'],
            }

    if bot.pong_check_callback:
        bot.pong_check_callback.cancel()
    if bot.ping_callback:
        bot.ping_callback.cancel()
    bot.ping_callback = asyncio.ensure_future(send_ping())
    bot.trigger('AFTER_CHANNEL_JOIN')

async def send_ping():
    await asyncio.sleep(random.randint(120, 240))
    logging.debug('Sending ping')
    bot.pong_check_callback = asyncio.ensure_future(wait_for_pong())
    bot.send('PING')

async def wait_for_pong():
    await asyncio.sleep(10)

    logging.error('Didn\'t receive a PONG in time, reconnecting')
    if bot.ping_callback:
        bot.ping_callback.cancel()
    bot.ping_callback = asyncio.ensure_future(send_ping())
    await bot.connect()

async def get_channels():
    q = await bot.conn.execute('SELECT channel_id, name FROM channels WHERE active="Y";')
    rows = await q.fetchall()
    l = []
    for r in rows:
        l.append({
            'channel_id': r['channel_id'],
            'name': r['name'].lower(),
        })
    return l

@bot.on('CLIENT_DISCONNECT')
async def disconnect(**kwargs):
    logging.info('Disconnected')

@bot.on('PING')
def keepalive(message, **kwargs):
    logging.debug('Received ping, sending PONG back')
    bot.send('PONG', message=message)

@bot.on('PONG')
async def pong(message, **kwargs):
    logging.debug('Received pong')
    if bot.pong_check_callback:
        bot.pong_check_callback.cancel()
    if bot.ping_callback:
        bot.ping_callback.cancel()
    bot.ping_callback = asyncio.ensure_future(send_ping())

def main():
    bot.host = config['twitch']['irc_host'] 
    bot.port = config['twitch']['irc_port'] 
    bot.ssl = config['twitch']['irc_use_ssl']
    bot.raw_handlers = [rfc2812_handler(bot)]
    bot.conn = sa.create_engine(config['sql_url'],
        convert_unicode=True,
        echo=False,
        pool_recycle=3599,
        encoding='UTF-8',
        connect_args={'charset': 'utf8mb4'},
        strategy=ASYNCIO_STRATEGY,
    )
    bot.http_session = None
    bot.pool = None
    bot.pong_check_callback = None
    bot.ping_callback = None
    bot.starttime = datetime.utcnow()

    loop = asyncio.get_event_loop()
    loop.create_task(bot.connect())
    loop.run_forever()

if __name__ == '__main__':
    from tbot import config_load, logger
    config_load('../../tbot.yaml')
    logger.set_logger('bot.log')
    main()