# MIT License

# Copyright (c) 2018 Arda "Ave" Ozkal

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# Modified in 2020 by Andrew Dysart for use in Open Turnip Bots.
# Original source located here: https://gitlab.com/a/dpyBotBase
#

import os
import sys
import logging
import logging.handlers
import traceback
import json
from pathlib import Path
import aiohttp

import discord
from discord.ext import commands

script_name = os.path.basename(__file__).split('.')[0]

log_file_name = f"{script_name}.log"

# Limit of discord (non-nitro) is 8MB (not MiB)
max_file_size = 1000 * 1000 * 8
backup_count = 10
file_handler = logging.handlers.RotatingFileHandler(
    filename=log_file_name, maxBytes=max_file_size, backupCount=backup_count)
stdout_handler = logging.StreamHandler(sys.stdout)

log_format = logging.Formatter(
    '[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s')
file_handler.setFormatter(log_format)
stdout_handler.setFormatter(log_format)

log = logging.getLogger('discord')
log.setLevel(logging.INFO)
log.addHandler(file_handler)
log.addHandler(stdout_handler)

if not Path(f"config.json").is_file():
    log.warning(
        f"No config file (config.json) found, "
        f"please create one from config.json.example file.")
    exit(3)

with open("config.json") as f:
    config = json.load(f)


def get_prefix(bot, message):
    prefixes = config['base']['prefixes']

    return commands.when_mentioned_or(*prefixes)(bot, message)


initial_extensions = ['cogs.common',
                      'cogs.admin',
                      'cogs.basic']

bot = commands.Bot(command_prefix=get_prefix,
                   description=config['base']['description'],
                   case_insensitive=True)
bot.help_command = commands.DefaultHelpCommand(dm_help=None)

bot.log = log
bot.config = config
bot.script_name = script_name

if __name__ == '__main__':
    for extension in initial_extensions:
        try:
            bot.load_extension(extension)
        except:
            log.error(f'Failed to load extension {extension}.')
            log.error(traceback.print_exc())


@bot.event
async def on_ready():
    aioh = {"User-Agent": f"{script_name}/1.0'"}
    bot.aiosession = aiohttp.ClientSession(headers=aioh)
    bot.app_info = await bot.application_info()

    log.info(f'\nLogged in as: {bot.user.name} - '
             f'{bot.user.id}\ndpy version: {discord.__version__}\n')
    game_name = f"{config['base']['prefixes'][0]}help"
    await bot.change_presence(activity=discord.Game(name=game_name))


@bot.event
async def on_command(ctx):
    log_text = f"{ctx.message.author} ({ctx.message.author.id}): "\
               f"\"{ctx.message.content}\" "
    if ctx.guild:  # was too long for tertiary if
        log_text += f"on \"{ctx.channel.name}\" ({ctx.channel.id}) "\
                    f"at \"{ctx.guild.name}\" ({ctx.guild.id})"
    else:
        log_text += f"on DMs ({ctx.channel.id})"
    log.info(log_text)


@bot.event
async def on_error(event_method, *args, **kwargs):
    log.error(f"Error on {event_method}: {sys.exc_info()}")


@bot.event
async def on_command_error(ctx, error):
    log.error(f"Error with \"{ctx.message.content}\" from "
              f"\"{ctx.message.author} ({ctx.message.author.id}) "
              f"of type {type(error)}: {error}")

    if isinstance(error, commands.NoPrivateMessage):
        return await ctx.send("This command doesn't work on DMs.")
    elif isinstance(error, commands.MissingPermissions):
        roles_needed = '\n- '.join(error.missing_perms)
        return await ctx.send(f"{ctx.author.mention}: You don't have the right"
                              " permissions to run this command. You need: "
                              f"```- {roles_needed}```")
    elif isinstance(error, commands.BotMissingPermissions):
        roles_needed = '\n-'.join(error.missing_perms)
        return await ctx.send(f"{ctx.author.mention}: Bot doesn't have "
                              "the right permissions to run this command. "
                              "Please add the following roles: "
                              f"```- {roles_needed}```")
    elif isinstance(error, commands.CommandOnCooldown):
        return await ctx.send(f"{ctx.author.mention}: You're being "
                              "ratelimited. Try in "
                              f"{error.retry_after:.1f} seconds.")
    elif isinstance(error, commands.CheckFailure):
        return await ctx.send(f"{ctx.author.mention}: Check failed. "
                              "You might not have the right permissions "
                              "to run this command.")

    help_text = f"Usage of this command is: ```{ctx.prefix}{ctx.command.name} "\
                f"{ctx.command.signature}```\nPlease see `{ctx.prefix}help "\
                f"{ctx.command.name}` for more info about this command."
    if isinstance(error, commands.BadArgument):
        return await ctx.send(f"{ctx.author.mention}: You gave incorrect "
                              f"arguments. {help_text}")
    elif isinstance(error, commands.MissingRequiredArgument):
        return await ctx.send(f"{ctx.author.mention}: You gave incomplete "
                              f"arguments. {help_text}")


@bot.event
async def on_guild_join(guild):
    bot.log.info(f"Joined guild \"{guild.name}\" ({guild.id}).")
    await guild.owner.send(f"Hello and welcome to {script_name}!\n"
                           "If you don't know why you're getting this message"
                           f", it's because someone added {script_name} to your"
                           " server\nDue to Discord API ToS, I am required to "
                           "inform you that **I log command usages and "
                           "errors**.\n**I don't log *anything* else**."
                           "\n\nIf you do not agree to be logged, stop"
                           f" using {script_name} and remove it from your "
                           "server as soon as possible.")


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    ctx = await bot.get_context(message)
    await bot.invoke(ctx)

def loadExtensions( extensions ):
   for extension in extensions:
      log.info( f'Attempting to load {extension}.' )
      try:
         bot.load_extension( extension )
      except:
         log.error( f'Failed to load extension {extension}.' )
         log.error( traceback.print_exc() )
      log.info ( f'{extension} loaded.' )

def run():
   bot.run(config['base']['token'], bot=True, reconnect=True)
