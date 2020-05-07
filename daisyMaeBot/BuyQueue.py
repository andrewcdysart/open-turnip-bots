import sys
sys.path.append( '..' )
from queueDbLib import GenericQueueDb
from collections import OrderedDict

class AlreadyBeingServedException( Exception ):
   pass

class QueueClosedException( Exception ):
   pass

class BuyQueue():
   def __init__( self,
                 owner: str,
                 price: str,
                 description: str = None,
                 closed: bool = False,
                 paused: bool = False,
                 id: int = None
               ):
      self.owner = str( owner )
      self.price = str( price )
      self.closed = closed
      self.paused = paused
      self.description = None
      if description:
         self.description = str( description )
      self.id = None
      if id:
         self.id = int( id )

      self.buyers = None
      self.getBuyersInQueue()

   def put( self ):
      buyQueueDb = BuyQueueDb()
      buyQueueDb.createQueue( self )
      buyQueueDb.close()

   def getBuyersInQueue( self ):
      if self.id:
         buyQueueDb = BuyQueueDb()
         self.buyers = buyQueueDb.getBuyersInQueue( self.id )
         buyQueueDb.close()
      return self.buyers

   def addBuyerToQueue( self, buyer ):
      if self.closed:
         raise QueueClosedException( f'Buyer {buyer.discordName} failed to join Queue {self.id} because it is closed.' )
      if buyer.discordName in self.buyers:
         raise AlreadyBeingServedException( f'Buyer {buyer.discordName} is already being served.' )

      queuePosition = len( self.buyers )
      self.buyers[buyer.discordName] = buyer
      buyer.queuePosition = queuePosition
      buyer.put()

   def pauseQueue( self ):
      self.paused = True
      # TODO: Update in DB

   def resumeQueue( self ):
      self.paused = False
      # TODO: Update in DB

   def endQueue( self ):
      buyQueueDb = BuyQueueDb()
      buyQueueDb.endQueue( self. id )
      buyQueueDb.close()

class Buyer():
   def __init__( self, discordName: str, name: str, island: str, queueId: int, queuePosition: int = None ):
      self.discordName = str( discordName )
      self.name = str( name )
      self.island = str( island )
      self.queueId = int( queueId )

      self.queuePosition = None
      if queuePosition:
         self.queuePosition = int( queuePosition )

   def put( self ):
      buyQueueDb = BuyQueueDb()
      buyQueueDb.addBuyerToQueue( self )
      buyQueueDb.close()


TABLE_BUY_QUEUE = 'buyQueue'
TABLE_CURRENT_BUYERS = 'currentBuyers'

DB_SCHEMA = {
   TABLE_BUY_QUEUE: [
      'ID INTEGER PRIMARY KEY',
      'Owner text UNIQUE NOT NULL',
      'Price text NOT NULL',
      'DodoCode text NOT NULL',
      'Closed INTEGER NOT NULL',
      'Paused INTEGER NOT NULL',
      'Description text'
   ],
   TABLE_CURRENT_BUYERS: [
      'DiscordName text PRIMARY KEY',
      'QueueID int NOT NULL',
      'Name text NOT NULL',
      'Island text NOT NULL',
      'QueuePosition int NOT NULL',
      'FOREIGN KEY (QueueID) REFERENCES buyQueue(ID)'
   ]
}

class BuyQueueDb( GenericQueueDb.GenericQueueDb ):
   def __init__( self ):
      super().__init__( DB_SCHEMA )

   def createQueue( self, queue ):
      cursor = self.put(
         TABLE_BUY_QUEUE,
         ['Owner', 'Price', 'Description'],
         [queue.owner, queue.price, queue.description]
      )

      queue.id = cursor.lastrowid
      return queue

   def getQueue( self, id ):
      cursor = self.get(
         TABLE_BUY_QUEUE,
         ['Owner', 'Price', 'Description'],
         'ID = %s' % id
      )

      response = cursor.fetchone()
      queue = None
      if response:
         queue = BuyQueue( response[0], response[1], response[2], id )
      return queue

   def endQueue( self, id ):
      # Delete all the current buyers from this queue
      self.removeByColumnValue(
         TABLE_CURRENT_BUYERS,
         'QueueID',
         id
      )

      # Delete the queue itself
      self.removeByColumnValue(
         TABLE_BUY_QUEUE,
         'ID',
         id
      )

   def getAllQueues( self ):
      cursor = self.get(
         TABLE_BUY_QUEUE,
         ['Owner', 'Price', 'Description', 'ID']
      )

      queues = []
      for response in cursor.fetchall():
         queues.append( BuyQueue( response[0], response[1], response[2], response[3] ) )
      return queues

   def addBuyerToQueue( self, buyer ):
      cursor = self.put(
         TABLE_CURRENT_BUYERS,
         ['DiscordName', 'Name', 'Island', 'QueueID', 'QueuePosition'],
         [buyer.discordName, buyer.name, buyer.island, buyer.queueId, buyer.queuePosition]
      )

      return buyer

   def getBuyersInQueue( self, queueId ):
      cursor = self.get(
         TABLE_CURRENT_BUYERS,
         ['DiscordName', 'Name', 'Island', 'QueueID', 'QueuePosition'],
         condition = ( 'QueueID = %s' % queueId ),
         orderBy = 'QueuePosition ASC'
      )

      buyers = OrderedDict()
      for response in cursor.fetchall():
         buyer = Buyer( response[0], response[1], response[2], response[3], queuePosition=response[4] )
         buyers[buyer.discordName] = buyer
      return buyers

   def getBuyer( self, discordName: str ):
      cursor = self.get(
         TABLE_CURRENT_BUYERS,
         ['DiscordName', 'Name', 'Island', 'QueueID', 'QueuePosition'],
         condition = ( 'DiscordName = "%s"' % discordName )
      )

      buyer = None
      response = cursor.fetchone()
      if response:
         buyer = Buyer( response[0], response[1], response[2], response[3], queuePosition=response[4] )

      return buyer
