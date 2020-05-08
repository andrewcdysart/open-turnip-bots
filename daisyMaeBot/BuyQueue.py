import sys
sys.path.append( '..' )
from queueDbLib import GenericQueueDb
from collections import OrderedDict

BUY_QUEUE_DB = None

class AlreadyBeingServedException( Exception ):
   pass

class QueueClosedException( Exception ):
   pass

class QueueFullException( Exception ):
   pass

class BuyQueue():
   def __init__( self,
                 owner: str,
                 price: str,
                 dodoCode: str,
                 peopleServed: int = 0,
                 capacity: int = 0,
                 description: str = None,
                 closed: bool = False,
                 paused: bool = False,
                 id: int = None
               ):
      # TODO: Owner should use a Discord ID
      # TODO: Check that the owner isn't already hosting
      self.owner = str( owner )
      self.price = str( price )
      self.dodoCode = str( dodoCode )
      self.closed = closed
      self.paused = paused
      self.peopleServed = peopleServed
      self.capacity = capacity

      self.description = None
      if description:
         self.description = str( description )
      self.id = None
      if id:
         self.id = int( id )

      self.buyers = None
      self.fetchBuyersInQueue()
      if not self.buyers:
         self.buyers = OrderedDict()

   def put( self ):
      """
         Store the queue information in the database.
      """
      BUY_QUEUE_DB.createQueue( self )

   def fetchBuyersInQueue( self ):
      """
         Read buyers in queue from disk.
      """
      if self.id:
         self.buyers = BUY_QUEUE_DB.fetchBuyersInQueue( self.id )
      return self.buyers

   def getBuyer( self, buyerId ):
      """
         Retrieves a buyer by ID, or None if the ID is not found.
      """
      for buyer in self.buyers:
         if buyer.id == buyerId:
            return buyer
      return None

   def getBuyerCount( self ):
      """
         Retrieve a count of how many buyers are in the queue.
      """
      BUY_QUEUE_DB.bot.log.info( 'getBuyerCount' )
      return len( self.buyers )

   def addBuyerToQueue( self, buyer ):
      if self.closed:
         raise QueueClosedException( f'Buyer ({buyer.discordId}) failed to join Queue {self.id} because it is closed.' )
      elif self.isFull():
         raise QueueFullException( f'Buyer ({buyer.discordId}) failed to join Queue {self.id} because it is full.')
      elif buyer.discordId in self.buyers:
         raise AlreadyBeingServedException( f'Buyer ({buyer.discordId}) is already being served in this queue.' )
      elif BUY_QUEUE_DB.getBuyer( buyer.discordId ):
         raise AlreadyBeingServedException( f'Buyer ({buyer.discordId}) is already being served in another queue.')

      BUY_QUEUE_DB.bot.log.info( 'addBuyerToQueue' )
      queuePosition = len( self.buyers )
      self.buyers[buyer.discordId] = buyer
      buyer.queuePosition = queuePosition
      buyer.put()

   def isFull( self ):
      """
         Whether the queue has reached its capacity.
      """
      return ( self.capacity > 0 ) and ( self.peopleServed == self.capacity )

   def pauseQueue( self ):
      self.paused = True
      # TODO: Update in DB

   def resumeQueue( self ):
      self.paused = False
      # TODO: Update in DB

   def incrementPeopleServed( self ):
      ++self.peopleServed
      # TODO: Update in DB

   def endQueue( self ):
      BUY_QUEUE_DB.endQueue( self. id )

class Buyer():
   def __init__( self, discordId, name: str, island: str, queueId: int, queuePosition: int = None ):
      # User is made private because bot API calls cannot be made during startup.
      # Runtime access to User must occur through getUser.
      self.__user__ = None
      self.discordId = str( discordId )
      self.name = str( name )
      self.island = str( island )
      self.queueId = int( queueId )

      self.queuePosition = None
      if queuePosition:
         self.queuePosition = int( queuePosition )

   def getUser( self ):
      if not self.__user__:
         self.__user__ = BUY_QUEUE_DB.bot.get_user( self.discordId )
      return self.__user__

   def put( self ):
      BUY_QUEUE_DB.addBuyerToQueue( self )


TABLE_BUY_QUEUE = 'buyQueue'
TABLE_CURRENT_BUYERS = 'currentBuyers'

DB_SCHEMA = {
   TABLE_BUY_QUEUE: [
      'ID INTEGER PRIMARY KEY',
      'OwnerID text UNIQUE NOT NULL',
      'Price text NOT NULL',
      'DodoCode text NOT NULL',
      'PeopleServed INTEGER NOT NULL',
      'Capacity INTEGER',
      'Closed INTEGER NOT NULL',
      'Paused INTEGER NOT NULL',
      'Description text'
   ],
   TABLE_CURRENT_BUYERS: [
      'DiscordID text PRIMARY KEY',
      'QueueID int NOT NULL',
      'Name text NOT NULL',
      'Island text NOT NULL',
      'QueuePosition int NOT NULL',
      'FOREIGN KEY (QueueID) REFERENCES buyQueue(ID)'
   ]
}

class BuyQueueDb( GenericQueueDb.GenericQueueDb ):
   def __init__( self, bot ):
      super().__init__( DB_SCHEMA )

      # Maintain an in-memory copy of queues so that we don't
      # need to read from disk unless starting up fresh.
      global BUY_QUEUE_DB
      BUY_QUEUE_DB = self
      self.bot = bot
      self.queues = None
      self.queues = self.fetchAllQueues()

   # def load( self ):
   #    """
   #       Load information from disk. Meant to be called once after init.
   #    """
   #    self.queues = self.fetchAllQueues()

   def createQueue( self, queue ):
      """
         Add a new queue to the database.
      """
      cursor = self.put(
         TABLE_BUY_QUEUE,
         [
            ( 'OwnerID', queue.owner ),
            ( 'Price', queue.price ),
            ( 'DodoCode', queue.dodoCode ),
            ( 'PeopleServed', queue.peopleServed ),
            ( 'Capacity', queue.capacity ),
            ( 'Closed', int( queue.closed ) ),
            ( 'Paused', int( queue.paused ) ),
            ( 'Description', queue.description )
         ]
      )

      queue.id = cursor.lastrowid
      self.queues.append( queue )
      return queue

   def getQueue( self, id ):
      """
         Get a queue with matching ID, or None if the ID isn't found.
      """
      for queue in self.queues:
         if queue.id == id:
            return queue
      return None

   def fetchQueue( self, id ):
      """
         Fetch a queue from disk by ID.
      """
      cursor = self.get(
         TABLE_BUY_QUEUE,
         ['OwnerID', 'Price', 'DodoCode', 'PeopleServed', 'Capacity', 'Closed', 'Paused', 'Description'],
         'ID = %s' % id
      )

      response = cursor.fetchone()
      queue = None
      if response:
         queue = BuyQueue(
            response[0],
            response[1],
            response[2],
            response[3],
            response[4],
            response[5],
            response[6],
            response[7],
            id
         )
      return queue

   def pauseQueue( self, id ):
      """
         Mark a queue as paused in-memory and in-database.
      """
      pass

   def closeQueue( self, id ):
      """
         Mark a queue as closed in-memory and in-database.
      """
      pass

   def endQueue( self, id ):
      """
         Permanently delete a queue from memory and disk.
      """
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

      # Remove the queue from memory
      self.queues.remove( self.getQueue( id ) )

   def getAllQueues( self ):
      """
         Read all queues from memory.
      """
      return self.queues

   def fetchAllQueues( self ):
      """
         Read all queues from disk.
      """
      cursor = self.get(
         TABLE_BUY_QUEUE,
         ['OwnerID', 'Price', 'DodoCode', 'PeopleServed', 'Capacity', 'Closed', 'Paused', 'Description', 'ID'],
      )

      queues = []
      for response in cursor.fetchall():
         queues.append(
            BuyQueue(
               response[0],
               response[1],
               response[2],
               response[3],
               response[4],
               response[5],
               response[6],
               response[7],
               response[8]
            )
         )
      return queues

   def addBuyerToQueue( self, buyer ):
      cursor = self.put(
         TABLE_CURRENT_BUYERS,
         [
            ( 'DiscordID', buyer.discordId ),
            ( 'Name', buyer.name ),
            ( 'Island', buyer.island ),
            ( 'QueueID', buyer.queueId ),
            ( 'QueuePosition', buyer.queuePosition )
         ]
      )

      return buyer

   def getBuyersInQueue( self, queueId ):
      """
         Read all buyers in the queue from memory.
      """
      return self.getQueue( queueId ).buyers

   def fetchBuyersInQueue( self, queueId ):
      """
         Read all buyers in the queue from disk.
      """
      cursor = self.get(
         TABLE_CURRENT_BUYERS,
         ['DiscordID', 'Name', 'Island', 'QueueID', 'QueuePosition'],
         condition = ( 'QueueID = %s' % queueId ),
         orderBy = 'QueuePosition ASC'
      )

      buyers = OrderedDict()
      for response in cursor.fetchall():
         buyer = Buyer( response[0], response[1], response[2], response[3], queuePosition=response[4] )
         buyers[buyer.discordId] = buyer
      return buyers

   def getBuyer( self, buyerId: str ):
      """
         Read a buyer from memory.
      """
      for queue in self.queues:
         buyer = queue.getBuyer( buyerId )
         if buyer:
            return buyer
      return None

   def fetchBuyer( self, discordId: str ):
      """
         Read a buyer from disk.
      """
      cursor = self.get(
         TABLE_CURRENT_BUYERS,
         ['DiscordID', 'Name', 'Island', 'QueueID', 'QueuePosition'],
         condition = ( 'DiscordID = "%s"' % discordId )
      )

      buyer = None
      response = cursor.fetchone()
      if response:
         buyer = Buyer( response[0], response[1], response[2], response[3], queuePosition=response[4] )

      return buyer

if __name__ == '__main__':
   print( 'This module is intended for use as an import, not as a standalone module.')
   exit( 1 )
