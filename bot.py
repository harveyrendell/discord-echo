import argparse
import asyncio
import platform
import logging

import discord
from discord.ext import commands

__version__ = '0.0.1'

bot = commands.Bot(
    description='',
    command_prefix=commands.when_mentioned,
)

extensions = []

@bot.event
async def on_ready():
    logging.info('Logged in as {}'.format(bot.user.name))
    logging.info('--------')
    logging.info('Pulse Bot Version: {}'.format(__version__))
    logging.info('Current Discord.py Version: {} | Current Python Version: {}'.format(discord.__version__, platform.python_version()))


@bot.event
async def on_message(message):
    if message.author.bot:
        return
    channel = message.channel
    bot.send_typing(channel)

    channel_log = bot.logs_from(message.channel, limit=2)
    async for msg in channel_log:
        message_to_react = msg

    search = message.content.strip(':')
    emoji_catalogue = bot.get_all_emojis()
    # get first 5 matching emojis
    emojis = [emoji for emoji in emoji_catalogue if search in emoji.name][:5]

    for emoji in emojis:
        await bot.add_reaction(message_to_react, emoji)
    await bot.send_typing(channel)
    await asyncio.sleep(5)
    for emoji in emojis:
        await bot.remove_reaction(message_to_react, emoji, bot.user)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--token', required=True, type=str)
    args = parser.parse_args()
    bot.run(args.token)
    bot.close()


if __name__ == "__main__":
    for extension in extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            logging.error('Failed to load extension {}'.format(extension))
            logging.error(e)
    main()
