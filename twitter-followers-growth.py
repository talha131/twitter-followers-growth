import logging
from optparse import OptionParser
import sys
import requests
import csv
from os.path import exists
from time import strftime, localtime

LOGGING_LEVELS = {'critical': logging.CRITICAL,
                  'error': logging.ERROR,
                  'warning': logging.WARNING,
                  'info': logging.INFO,
                  'debug': logging.DEBUG}

def main():
  parser = OptionParser()
  parser.add_option("-u", "--user", help="Twitter USER name")
  parser.add_option("-s", "--store", help="File name in which followers count would be stored")
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
      writer = csv.writer(open(options.store, 'ab'), dialect='twitter-followers-growth')
      row = [strftime("%Y-%m-%d %H:%M:%S", localtime()), response.json['followers_count']]
      logging.debug('New row is %r' %row)
      writer.writerow(row)

if __name__ == '__main__':
  main()
