import argparse
import asyncio
import platform
import logging

from difflib import SequenceMatcher
from collections import namedtuple


import discord
from discord.ext import commands

__version__ = '0.0.1'

bot = commands.Bot(
    description='',
    command_prefix=commands.when_mentioned,
)

Recommendation = namedtuple('Recommendation', 'emoji name score')


def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


@bot.event
async def on_ready():
    logging.info('Logged in as {}'.format(bot.user.name))
    logging.info('--------')
    logging.info('Pulse Bot Version: {}'.format(__version__))
    logging.info('Current Discord.py Version: {} | Current Python Version: {}'.format(
        discord.__version__, platform.python_version()))

@bot.command(pass_context=True, help='Search for reactions which match the provided search')
async def search(ctx, arg):
    print(f'Command called: ', ctx.message)

    emoji_catalogue = [emoji for emoji in bot.get_all_emojis()]
    similarity_scores = [Recommendation(emoji, emoji.name, similar(arg, emoji.name)) for emoji in emoji_catalogue]
    similarity_scores.sort(key=lambda x: x.score, reverse=True)

    search_results = '\n'.join([f'{str(res.emoji)} - {res.name} ({res.score})' for res in similarity_scores[:5]])
    print(search_results)
    await bot.send_message(ctx.message.author, content=f"Search results for '{arg}':\n{search_results}")

    try:
        await bot.delete_message(ctx.message)
        print(f'Deleting message "{ctx.message.content}"')
        return
    except discord.errors.Forbidden as ex:
        print('Not able to delete trigger message: ', ex)


@bot.command(pass_context=True, help='React to the previous message, or to a message which has the 🔖 reaction')
async def react(ctx, arg):
    print(f'Command called: ', ctx.message.content)

    channel_log = bot.logs_from(ctx.message.channel, limit=15)
    log_messages = [msg async for msg in channel_log]

    emoji_catalogue = [emoji for emoji in bot.get_all_emojis()]
    # get first 3 matching emojis
    emojis = [emoji for emoji in emoji_catalogue if arg.strip(':') in emoji.name][:3]

    if not emojis:
        similarity_scores = [Recommendation(emoji, emoji.name, similar(arg, emoji.name)) for emoji in emoji_catalogue]
        similarity_scores.sort(key=lambda x: x.score, reverse=True)
        print(f'No results found for {arg}')
        rec = similarity_scores[0]
        print(f'{str(rec.emoji)} - {rec.name} ({rec.score})')

        await bot.send_message(ctx.message.author, content=f'''No match found for {arg}
        Were you looking for {similarity_scores[0]} instead?''')

        await bot.delete_message(ctx.message)
        return

    print(f'Found {len(emojis)} emoji: {[str(e) for e in emojis]} matching {arg}')
    target = await get_target_message(log_messages, requester=ctx.message.author)
    async with ReactionContext(client=bot, message=target, reactions=emojis):
        await bot.wait_for_reaction(message=target, emoji=emojis, user=ctx.message.author, timeout=6)
    
    try:
        await bot.delete_message(ctx.message)
        print(f'Deleting message "{ctx.message.content}"')
        return
    except discord.errors.Forbidden as ex:
        print('Not able to delete trigger message: ', ex)

async def get_target_message(message_log, requester):
    for msg in message_log:
        for reaction in msg.reactions:
            if reaction.emoji == "🔖":
                if requester not in await bot.get_reaction_users(reaction):
                    print("🔖 reaction found but not added by author")
                    continue
                print(f'Removing {reaction.emoji} - added by '
                      f'{requester.display_name} on "{msg.content}"')
                await bot.remove_reaction(msg, reaction.emoji, requester)
                return msg
    # Message above the triggering message
    return message_log[1] if len(message_log) >= 2 else None


class ReactionContext:
    '''Context manager for Discord message reactions.'''

    def __init__(self, client, message, reactions):
        self.client = client
        self.message = message
        self.reactions = reactions

    async def __aenter__(self):
        for reaction in self.reactions:
            await bot.add_reaction(self.message, reaction)

    async def __aexit__(self, *args):
        for reaction in self.reactions:
            await bot.remove_reaction(
                self.message,
                reaction,
                self.client.user)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--token', required=True, type=str)
    args = parser.parse_args()
    bot.run(args.token)
    bot.close()


if __name__ == "__main__":
    main()
