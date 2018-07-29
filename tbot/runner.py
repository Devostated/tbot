import click
import asyncio
from tbot import config, config_load, logger

@click.group()
@click.option('--config', default=None, help='path to the config file')
@click.option('--log_path', '-lp', default=None, help='a folder to store the log files in')
@click.option('--log_level', '-ll', default=None, help='notset, debug, info, warning, error or critical')
def cli(config, log_path, log_level):
    config_load(config)
    if log_path != None:
        config['logging']['path'] = log_path
    if log_level:
        config['logging']['level'] = log_level

@cli.command()
def twitch():
    logger.set_logger('twitch.log')
    import tbot.twitch_bot.bot_main
    tbot.twitch_bot.bot_main.main()

@cli.command()
def web():
    logger.set_logger('web.log')
    import tbot.web.app
    tbot.web.app.main() 

@cli.command()
def discord():
    logger.set_logger('discord.log')
    import tbot.discord_bot.bot_main
    tbot.discord_bot.bot_main.main() 

def main():
    cli()

if __name__ == "__main__":
    main()