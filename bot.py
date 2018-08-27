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


@bot.command(pass_context=True, help='Count the messages in the channel.')
async def count(ctx):
    result = bot.logs_from(ctx.message.channel, limit=9999)
    user_messages = {}
    async for message in result:
        name = message.author.name
        new_user_messages = user_messages.get(name, []) + [message]
        user_messages[name] = new_user_messages
    response = ['Messages in {}'.format(ctx.message.channel)]
    for author, messages in user_messages.items():
        line = 'User {} has posted {} messages'.format(author, len(messages))
        response.append(line)

    await bot.say('\n'.join(response))


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
