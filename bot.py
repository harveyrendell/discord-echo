import asyncio
import argparse
import platform
import logging

from difflib import SequenceMatcher
from collections import namedtuple
from textwrap import dedent


import discord
from discord.ext import commands

__version__ = '0.0.1'
SIMILARITY_THRESHOLD = 0.2


bot = commands.Bot(
    description='',
    command_prefix=commands.when_mentioned,
    pm_help=True,
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
    message = ctx.message

    print(f'Command called: ', message.content)

    similarity_scores = [Recommendation(emoji, emoji.name, similar(arg, emoji.name)) for emoji in bot.emojis]
    similarity_scores.sort(key=lambda x: x.score, reverse=True)

    search_results = [f'{printable_emoji(res.emoji)} *{res.name}*' for res in similarity_scores if res.score >= SIMILARITY_THRESHOLD]
    best_match, other_results = search_results[0], search_results[1:]
    other_results = '\n'.join(other_results)
    print(search_results)
    embed = discord.Embed(title="Search results")
    embed.add_field(name='Best match', value=best_match)
    embed.add_field(name='Other results', value=other_results, inline=False)

    await message.author.send(embed=embed)

    try:
        await message.delete()
        print(f'Deleting message "{message.content}"')
        return
    except discord.errors.Forbidden as ex:
        print('Not able to delete trigger message: ', ex)


def printable_emoji(emoji):
    print(repr(emoji), emoji.animated)
    if emoji.animated:
        return f"<a:{emoji.name}:{emoji.id}>"
    return str(emoji)


@bot.command(pass_context=True, help='React to the previous message, or to a message which has the 🔖 reaction')
async def react(ctx, arg):
    message = ctx.message
    channel = message.channel

    print(f'Command called: ', message.content)

    log_messages = await channel.history(limit=25).flatten()

    # get first 3 matching emojis
    emojis = [emoji for emoji in bot.emojis if arg.strip(':') in emoji.name][:3]

    if not emojis:
        similarity_scores = [Recommendation(emoji, emoji.name, similar(arg, emoji.name)) for emoji in bot.emojis]
        similarity_scores.sort(key=lambda x: x.score, reverse=True)
        print(f'No results found for {arg}')
        rec = similarity_scores[0]
        print(f'{str(rec.emoji)} - {rec.name} ({rec.score})')

        await message.author.send(content=f'''No match found for '{arg}'.
        Were you looking for {similarity_scores[0].emoji} ({similarity_scores[0].name}) instead?''')

        return await message.delete()

    emoji_list = [str(emoji) for emoji in emojis]

    print(f'Found {len(emojis)} emoji: {emoji_list} matching {arg}')
    target = await get_target_message(log_messages, requester=message.author)
    async with ReactionContext(client=bot, message=target, reactions=emojis):

        def check(reaction, user):
            return reaction.message.id == target.id and user == message.author and reaction.emoji in emojis
        
        await bot.wait_for('reaction_add', check=check, timeout=6)

    try:
        await message.delete()
        print(f'Deleting message "{message.content}"')
        return
    except discord.errors.Forbidden as ex:
        print('Not able to delete trigger message: ', ex)


async def get_target_message(message_log, requester):
    for msg in message_log:
        for reaction in msg.reactions:
            if reaction.emoji == "🔖":
                if requester not in await reaction.users().flatten():
                    print("🔖 reaction found but not added by author")
                    continue
                print(f'Removing {reaction.emoji} - added by '
                      f'{requester.display_name} on "{msg.content}"')
                await msg.remove_reaction(reaction.emoji, requester)
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
            await self.message.add_reaction(reaction)

    async def __aexit__(self, *args):
        for reaction in self.reactions:
            await self.message.remove_reaction(reaction, self.client.user)
        return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--token', required=True, type=str)
    args = parser.parse_args()
    bot.run(args.token)
    bot.close()


if __name__ == "__main__":
    main()
