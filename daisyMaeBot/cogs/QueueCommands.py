from discord.ext.commands import Cog
from discord.ext import commands

import sys
sys.path.append( '..' )
from BuyQueue import Buyer, BuyQueue, BuyQueueDb

class QueueCommands(Cog):
   def __init__( self, bot ):
      self.bot = bot
      self.queueDb = BuyQueueDb()

# To join a queue, use:
# Command: [!/?]qJoin <queueID> <your_Name> <your_Island>
   @commands.command()
   async def qjoin( self, ctx, *, argString: str ):
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

      buyer = Buyer( discordUser, name, islandName, queueId )
      try:
         queue.addBuyerToQueue( buyer )
      except Exception:
         return await ctx.send( f'{ctx.author.mention}: Could not join Queue `{queueId}`. You are already being served.')

      self.bot.log.info( f'{discordUser} ({name} from {islandName}) joined queue {queueId} in position {buyer.queuePosition}.' )
      return await ctx.send( f"{ctx.author.mention}: You have joined Queue `{queueId}`. You are in position {buyer.queuePosition}." )

   @commands.command()
   async def qleave( self, ctx, *, argString: str ):
      arguments = argString.split( ' ' )
      msg = ctx.message

   @commands.command()
   async def qposition( self, ctx ):
      msg = ctx.message

# Example: !qCreate DG48V 364 20 - This will limit the queue to 20 people.
# The queue will automatically start when 4 people join.
   @commands.command()
   async def qcreate( self, ctx, *, argString: str ):
      discordUser = ctx.message.author
      arguments = argString.split( ' ' )
      dodoCode = str( arguments[0] )
      price = int( arguments [1] )
      limit = None
      if len( arguments ) > 2:
         limit = int( arguments [2] )

      self.bot.log.info( f'{discordUser} attempting to create queue.' )

      newQueue = BuyQueue( discordUser, price )
      newQueue.put()
      queueId = newQueue.id

      self.bot.log.info( f'{discordUser} queue {queueId} created.' )
      return await ctx.send( f'{ctx.author.mention}: `Queue {queueId}` created.')

# Step three:
# After the first group is finished, you will need to notify the bot you're ready for the next set!
# Command: !qNext <New Dodo Code>
# Example: !qNext TV26S
   @commands.command()
   async def qnext( self, ctx, *, argString: str ):
      arguments = argString.split( ' ' )
      msg = ctx.message

# Step four:
# When you're done hosting, please be sure to end your queue!
# Command: !qEnd
   @commands.command()
   async def qend( self, ctx ):
      msg = ctx.message

# Extra commands!

# Stop new participants from queuing up:
# Command: !qClose
   @commands.command()
   async def qclose( self, ctx ):
      msg = ctx.message

# Re-open the queue after closing it:
# Command: !qOpen
   @commands.command()
   async def qopen( self, ctx ):
      msg = ctx.message

# Need a break? Use this for a 15 minute break:
# Command: !qBreak
   @commands.command()
   async def qbreak( self, ctx ):
      msg = ctx.message

# Ready to resume from break?
# Command: !qResume
   @commands.command()
   async def qresume( self, ctx ):
      msg = ctx.message

def setup( bot ):
   bot.add_cog( QueueCommands( bot ) )