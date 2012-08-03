import logging
from optparse import OptionParser
import sys
import requests
import csv
from os.path import exists
from datetime import datetime
import gviz_api

page_template = """
<html>
  <script src="https://www.google.com/jsapi" type="text/javascript"></script>
  <script>
    google.load('visualization', '1', {packages:['annotatedtimeline']});

    google.setOnLoadCallback(drawTable);
    function drawTable() {

      var json_table = new google.visualization.Table(document.getElementById('table_div_json'));
      var json_data = new google.visualization.DataTable(%(json)s, 0.6);
      json_table.draw(json_data, {showRowNumber: true});
    }
  </script>
  <body>
    <H1>Table created using ToJSon</H1>
    <div id="table_div_json"></div>
  </body>
</html>
"""

LOGGING_LEVELS = {'critical': logging.CRITICAL,
                  'error': logging.ERROR,
                  'warning': logging.WARNING,
                  'info': logging.INFO,
                  'debug': logging.DEBUG}

def main():
  parser = OptionParser()
  parser.add_option("-u", "--user", help="Twitter USER name")
  parser.add_option("-s", "--store", help="store and read data points from the specified file")
  parser.add_option("-o", "--output", help="write output to the specified file")
  parser.add_option('-l', '--logging-level', help='Logging level')
  parser.add_option('-f', '--logging-file', help='Logging file name')

  (options, args) = parser.parse_args()

  logging_level = LOGGING_LEVELS.get(options.logging_level, logging.NOTSET)
  logging.basicConfig(level=logging_level, filename=options.logging_file,
                      format='%(asctime)s %(levelname)s: %(message)s',
                      datefmt='%Y-%m-%d %H:%M:%S')

  logging.debug('User name is %r' % options.user)
  logging.debug('Store data points in %r' % options.store)

  # Create a CSV file 
  ## Create a dialect
  csv.register_dialect('twitter-followers-growth',
                      delimiter='|',
                      quoting=csv.QUOTE_NONE)
  ## Header of the CSV file
  header = ['Date', 'Count'] 
  ## CSV file has two columns separated by |

  if exists (options.store) :
    logging.debug('File %r exist' % options.store)
    ## If CSV file already exist then check does it conform to the required structure

    try:
      dialect = csv.Sniffer().sniff(open(options.store, 'rb').read(1024),delimiters=csv.get_dialect('twitter-followers-growth').delimiter )

      if dialect.delimiter == csv.get_dialect('twitter-followers-growth').delimiter and csv.Sniffer().has_header(open(options.store, 'rb').read(1024)) :
        logging.debug('File %r dialect matches' % options.store)
        inputheader = csv.reader(open(options.store, 'rb'), dialect='twitter-followers-growth').next()
        logging.debug('Header of file %r is %r' % (options.store, inputheader))

        if inputheader != header :
          logging.error('Header does not match. Either enter a new file name or give a valid CSV file that %r generated earlier.' % (__file__))
          sys.exit(1)

      else :
        logging.debug('Input file dialect delimiter is %r', dialect.delimiter)
        logging.debug('File %r dialect does not matches' % options.store)
        sys.exit(1)

    except csv.Error:
      # File appears not to be in CSV format; move along
      logging.error('File %r is not a valid CSV file. Either enter a new file name or give a valid CSV file that %s generated earlier.' % (options.store, __file__))
      sys.exit(1)

  else :
    ## If file does not exist create it
    logging.debug('File %r does not exist' % options.store)
    writer = csv.writer(open(options.store, 'wb'), dialect = 'twitter-followers-growth')
    writer.writerow(header)
    logging.debug('File %r created with header' % options.store)

  # Get twitter Response
  ## From https://dev.twitter.com/docs/api/1/get/users/show
  url = 'https://api.twitter.com/1/users/show.json'
  parameters = dict(
    screen_name=options.user,
    include_entities='true')

  response = requests.get(url, params = parameters)
  if response.status_code != 200 :
    logging.error('Communication failed. Twitter Response status code is %r.', response.status_code) 
  else :

    if response.json == 'None' :
      logging.error('JSON decoding failed.') 

    else :
      logging.debug('Followers count is %d', response.json['followers_count'])
      # Log follower count in the CSV file
      csv_file = open(options.store, 'ab')
      writer = csv.writer(csv_file, dialect='twitter-followers-growth')
      row = [datetime.now().strftime("%Y-%m-%d %H:%M:%S"), response.json['followers_count']]
      logging.debug('New row is %r' %row)
      writer.writerow(row)
      csv_file.close()

  # Render CSV into HTML
  ## Load CSV
  col1 = 'Date'
  col2 = 'Followers'
  data = []
  reader = csv.reader(open(options.store, 'rb'), dialect='twitter-followers-growth')
  ### Discard the header
  reader.next()

  for row in reader:
    record = { col1 : datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S') , col2 : int(row[1]) }
    logging.debug('Record is %r' % record)
    data.append(record)

  logging.debug('Data is %r' % data)
    
  ## Prepare table schema  
  description = {col1: ('datetime'), col2: ('number')}

  ## Load it into gviz_api.DataTable
  data_table = gviz_api.DataTable(description)
  data_table.LoadData(data)

  ## Creating a JSon string
  json = data_table.ToJSon(columns_order=(col1, col2), order_by=col1)
    
if __name__ == '__main__':
  main()
