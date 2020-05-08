from discord.ext.commands import Cog
from discord import Embed
from discord.ext import commands

import sys
sys.path.append( '..' )
import os
import json
import BuyQueue

DAISY_CONFIG_FILENAME = 'daisyConfig.json'

class QueueCommandsConfig():
   def __init__( self, filename ):
      self.filename = filename
      self.currentQueueMsgId = None
      self.announcementChannelId = None
      self.guildId = None

      self.load()

   def load( self ):
      if os.path.exists( self.filename ):
         with open( self.filename, 'r' ) as configFile:
            config = json.load( configFile )
            self.currentQueueMsgId = config['currentQueueMsgId']
            self.announcementChannelId = config['announcementChannelId']
            self.guildId = config['guildId']

   def save( self ):
      config = dict()
      config['currentQueueMsgId'] = self.currentQueueMsgId
      config['announcementChannelId'] = self.announcementChannelId
      config['guildId'] = self.guildId
      with open( self.filename, 'w' ) as configFile:
         json.dump( config, configFile )

class QueueCommands(Cog):
   def __init__( self, bot ):
      self.bot = bot
      self.queueDb = BuyQueue.BuyQueueDb( bot )
      self.config = QueueCommandsConfig( DAISY_CONFIG_FILENAME )

      self.currentQueueMessage = None

   def __del__( self ):
      if self.config:
         self.config.save()

   def getQueueEmbed( self, text ):
      embed = Embed( title = self.bot.user.name, type = "rich" )
      embed.add_field( name = "Current Turnip Queues", value = text, inline = False )
      return embed

   async def updateCurrentQueues( self ):
      # Attempt to load a previously-set queue message from config
      if not self.currentQueueMessage:
         if self.config.currentQueueMsgId and self.config.announcementChannelId and self.config.guildId:
            # guild = await self.bot.fetch_guild( self.config.guildId )
            channel = self.bot.get_channel( self.config.announcementChannelId )
            self.currentQueueMessage = await channel.fetch_message( self.config.currentQueueMsgId )

      # Update the queue message, if found.
      if self.currentQueueMessage:
         newText = self.currentQueuesText()

         currentQueueEmbed = self.getQueueEmbed( newText )
         await self.currentQueueMessage.edit( embed = currentQueueEmbed )

   def currentQueuesText( self ):
      queues = self.queueDb.getAllQueues()
      result = ''
      for queue in queues:
         # TODO: In future, queue.owner will be a Discord ID.
         # This should be used to find the owner's display name
         # (though discriminator might be nice to have too)
         result = result + f'`ID: {queue.id}` `{queue.owner}` - `{queue.price}` `{queue.getBuyerCount()} in line`\r\n'
      if not result:
         result = '- None'
      return result

   @commands.command()
   async def qchannelcurrentqueues( self, ctx ):
      """
         Mark the channel where the "current queues" message should go.
      """
      # TODO: Restrict permissions to a role
      message = ctx.message
      self.currentQueueMessage = await ctx.send( embed = self.getQueueEmbed( '- None' ) )
      await message.delete()
      self.config.currentQueueMsgId = self.currentQueueMessage.id
      self.config.announcementChannelId = self.currentQueueMessage.channel.id
      self.config.guildId = self.currentQueueMessage.guild.id
      self.config.save()
      await self.updateCurrentQueues()

   @commands.command()
   async def qchannelannouncements( self, ctx ):
      """
         Mark the channel where the queue announcements should go.
      """
      # TODO: Restrict permissions to a role
      pass

   @commands.command()
   async def qjoin( self, ctx, *, argString: str ):
      """
         Join a queue: ?qJoin <queueID> <your name without spaces> <your island without spaces>
      """
      discordUser = ctx.message.author
      arguments = argString.split( ' ' )
      queueId = int( arguments[0] )
      name = str( arguments[1] )
      islandName = str( arguments[2] )

      self.bot.log.info( f'{discordUser} ({name} from {islandName}) attempting to join queue {queueId}.' )

      if not self.queueDb:
         self.bot.log.error( 'Queue Database is None!' )
         return await ctx.send( f"{ctx.author.mention}: Could not join Queue `{queueId}` due to fatal error." )

      queue = self.queueDb.getQueue( queueId )
      if not queue:
         self.bot.log.error( f'Queue {queueId} does not exist.' )
         return await ctx.send( f"{ctx.author.mention}: Could not join Queue `{queueId}` because it does not exist." )

      buyer = BuyQueue.Buyer( discordUser.id, name, islandName, queueId )
      try:
         queue.addBuyerToQueue( buyer )
      except Exception:
         return await ctx.send( f'{ctx.author.mention}: Could not join Queue `{queueId}`. You are already being served.')

      await self.updateCurrentQueues()
      self.bot.log.info( f'{discordUser} ({name} from {islandName}) joined queue {queueId} in position {buyer.queuePosition}.' )
      return await ctx.send( f"{ctx.author.mention}: You have joined Queue `{queueId}`. You are in position {buyer.queuePosition}." )

   @commands.command()
   async def qleave( self, ctx, *, argString: str ):
      arguments = argString.split( ' ' )
      msg = ctx.message

   @commands.command()
   async def qposition( self, ctx ):
      msg = ctx.message

   @commands.command()
   async def qcreate( self, ctx, *, argString: str ):
      """
         Create a queue: ?qCreate <dodo code> <price> <optional limit>
         Specifying a limit will close the queue once the limit is reached.
      """
      discordUser = ctx.message.author
      arguments = argString.split( ' ' )
      dodoCode = str( arguments[0] )
      price = int( arguments [1] )
      limit = 0
      if len( arguments ) > 2:
         limit = int( arguments [2] )

      self.bot.log.info( f'{discordUser} attempting to create queue.' )

      # TODO: Support description
      newQueue = BuyQueue.BuyQueue( discordUser, price, dodoCode, capacity = limit )
      newQueue.put()

      self.bot.log.info( 'made the queue' )

      await self.updateCurrentQueues()
      self.bot.log.info( f'{discordUser} queue {newQueue.id} created.' )
      return await ctx.send( f'{ctx.author.mention}: `Queue {newQueue.id}` created.')

   @commands.command()
   async def qnext( self, ctx, *, argString: str ):
      """
         Send a new Dodo code to the next group: ?qNext <new dodo code>
         You can also use qnext to send a code early, e.g. when only 3 people
         are in the next group.
      """
      arguments = argString.split( ' ' )
      dodoCode = str( arguments[0] )
      msg = ctx.message

   @commands.command()
   async def qend( self, ctx ):
      """
         Close your queue: !qend
      """
      msg = ctx.message

   @commands.command()
   async def qclose( self, ctx ):
      """
         Prevent new participants from joining the queue: ?qClose
         Note: this does not end the queue. Use ?qEnd when finished
         hosting!
      """
      msg = ctx.message

   @commands.command()
   async def qopen( self, ctx ):
      """
         Allow new participants to join the queue: ?qOpen
      """
      msg = ctx.message

   @commands.command()
   async def qbreak( self, ctx ):
      """
         Take a 15 minute break: ?qBreak
      """
      msg = ctx.message

   @commands.command()
   async def qresume( self, ctx ):
      """
         Resume from your break: ?qResume
      """
      msg = ctx.message

def setup( bot ):
   bot.add_cog( QueueCommands( bot ) )