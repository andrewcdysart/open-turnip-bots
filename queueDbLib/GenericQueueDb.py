import sqlite3

DB_FILE = 'queue_database.db'

class GenericQueueDb:
   def __init__( self, tables ):
      self.open()
      self.__initializeTables__( tables )

   def __del__( self ):
      self.close()

   def __initializeTables__( self, tables ):
      cursor = self.connection.cursor()

      for table in tables:
         columns = tables[table]
         query = 'CREATE TABLE IF NOT EXISTS %s (' % table

         for i in range( 0, len( columns ) ):
            column = columns[i]
            query = query + column
            if i + 1 != len( columns ):
               query = query + ','
         query = query + ')'

         cursor.execute( query )

      self.commit()

   def put( self, table, valueTuples ):
      """
         Insert a set of column, value tuples into the given table.
      """
      cursor = None

      columns = []
      values = []
      for column, value in valueTuples:
         columns.append( column )
         values.append( value )

      if len( columns ) != len( values ):
         # TODO: This should probably be an exception, as it signals
         # a misuse of the interface
         print( 'Column and value count did not match!' )
      else:
         query = 'INSERT INTO %s (' % table
         query = self.__addValuesToQuery__( query, columns )
         query = query + ') VALUES ('
         query = self.__addValueSubsToQuery__( query, values )
         query = query + ')'

         cursor = self.__execute__( query, tuple( values ) )
         self.commit()
      return cursor

   def get( self, table, columns, condition=None, orderBy=None ):
      query = 'SELECT '
      query = self.__addValuesToQuery__( query, columns )
      query = query + ( ' FROM %s' % table )
      if condition:
         query = query + ' WHERE %s' % condition
      if orderBy:
         query = query + ' ORDER BY %s' % orderBy
      cursor = self.__execute__( query )
      return cursor

   def removeByColumnValue( self, table, column, id ):
      query = f'DELETE FROM {table} WHERE {column} = ?'
      self.__execute__( query, tuple( id ) )

   def __addValuesToQuery__( self, currentQuery, list ):
      for i in range( 0, len( list ) ):
         value = list[i]
         currentQuery = currentQuery + value
         if i + 1 != len( list ):
            currentQuery = currentQuery + ','
      return currentQuery

   def __addValueSubsToQuery__( self, currentQuery, list ):
      for i in range( 0, len( list ) ):
         currentQuery = currentQuery + '?'
         if i + 1 != len( list ):
            currentQuery = currentQuery + ','
      return currentQuery

   def __execute__( self, query, parameterTuple=None ):
      cursor = self.connection.cursor()
      if parameterTuple:
         cursor.execute( query, parameterTuple )
      else:
         cursor.execute( query )
      return cursor

   def commit( self ):
      self.connection.commit()

   def open( self ):
      self.connection = sqlite3.connect( DB_FILE )

   def close( self ):
      self.connection.close()
      self.connection = None
