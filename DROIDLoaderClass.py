import os
import sys 
import sqlite3
import hashlib
import datetime
import csv
from urlparse import urlparse
from GenerateBaselineDBClass import GenerateBaselineDB

class DROIDLoader:

   csvcolumncount = 0
   hashtype = 0

   #DROID SPECIFIC COLUMN INDEXES
   #zer0-based index
   URI_COL = 2
   PATH_COL = 3
   DATE_COL = 10
   
   #better way to handle this? 
   #avoid overflow for multiple-ids
   LAST_COL = 18
   
   def createDROIDTable(self, basedb, cursor, csvcolumnheaders):
      # turn csv headers list into a csv string, write query, create table

      self.csvcolumncount = len(csvcolumnheaders)
      columns = ""
      for header in csvcolumnheaders:
         if header == "URI":
            columns = columns + header + ", " + "URI_SCHEME, "
            self.csvcolumncount+=1
         elif header == "FILE_PATH":
            columns = columns + header + ", " + "DIR_NAME, "
            self.csvcolumncount+=1
         elif "_HASH" in header:    #regex alternative: ^([[:alnum:]]*)(_HASH)$
            basedb.sethashtype(header.split('_', 1)[0])
            columns = columns + "HASH" + ", "
         elif header == "LAST_MODIFIED":
            columns = columns + header + " TIMESTAMP" + ","
            columns = columns + "YEAR INTEGER" + ","
         else:
            #sys.stderr.write(header + "\n")
            columns = columns + header + ", "

      cursor.execute("CREATE TABLE droid (" + columns[:-2] + ")")
      return True

   def droidDBSetup(self, droidcsv):

      basedb = GenerateBaselineDB(droidcsv)
      cursor = basedb.dbsetup()

      with open(droidcsv, 'rb') as csvfile:
         droidreader = csv.reader(csvfile)
         for row in droidreader:
            if droidreader.line_num == 1:		# not zero-based index
               tablequery = self.createDROIDTable(basedb, cursor, row)
            else:
               rowstr = ""	
               for i,item in enumerate(row[0:self.csvcolumncount-1]):

                  if i != self.LAST_COL:  #avoid overrun of columns when multi-id occurs
                     
                     if item == "":
                        rowstr = rowstr + ',"no value"'
                     else:
                        rowstr = rowstr + ',"' + item + '"'
                                    
                     if i == self.URI_COL:
                        url = item
                        rowstr = rowstr + ',"' + urlparse(url).scheme + '"'

                     if i == self.PATH_COL:
                        dir = item
                        rowstr = rowstr + ',"' + os.path.dirname(item) + '"'		

                     if i == self.DATE_COL:
                        if item is not '':
                           datestring = item
                           #split at '+' if timezone is there, we're only interested in year
                           dt = datetime.datetime.strptime(datestring.split('+', 1)[0], '%Y-%m-%dT%H:%M:%S')
                           rowstr = rowstr + ',"' + str(dt.year) + '"'
                        else:
                           rowstr = rowstr + ',"' + "no value" + '"'

               cursor.execute("INSERT INTO droid VALUES (" + rowstr.lstrip(',') + ")")

      basedb.closedb(cursor)