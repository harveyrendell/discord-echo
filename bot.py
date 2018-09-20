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
    logging.info('Current Discord.py Version: {} | Current Python Version: {}'.format(
        discord.__version__, platform.python_version()))


@bot.command(pass_context=True, help='')
async def react(ctx, arg):
    print(f'react called with [{arg}]')

    log_messages = []
    message = ctx.message
    search = arg.strip(':')
    
    channel_log = bot.logs_from(message.channel, limit=15)
    async for msg in channel_log:
        log_messages.append(msg)
    
    emoji_catalogue = bot.get_all_emojis()
    # get first 3 matching emojis
    emojis = [emoji for emoji in emoji_catalogue if search in emoji.name][:3]

    if not emojis:
        await bot.delete_message(message)
        return

    target = await get_target_message(message.author, log_messages)
    
    for emoji in emojis:
        await bot.add_reaction(target, emoji)
    await bot.send_typing(message.channel)
    await asyncio.sleep(9)
    for emoji in emojis:
        await bot.remove_reaction(target, emoji, bot.user)

    await bot.delete_message(message)
    await bot.send_message(
        ctx.message.author,
        content="Done!"
    )


async def get_target_message(author, log_messages):
    for msg in log_messages:
        for reaction in msg.reactions:
            if reaction.emoji == "🔖":
                if author not in await bot.get_reaction_users(reaction):
                    print("🔖 reaction found but not added by author")
                    continue
                print(
                    f'Removing {reaction.emoji} - added by {author.display_name} on "{msg.content}"')
                await bot.remove_reaction(msg, reaction.emoji, author)
                return msg
    # Message above the triggering message
    return log_messages[1] if len(log_messages) >= 2 else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--token', required=True, type=str)
    args = parser.parse_args()
    bot.run(args.token)
    bot.close()


if __name__ == "__main__":
    main()
