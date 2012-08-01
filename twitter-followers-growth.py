import requests
from optparse import OptionParser

# Parse command line options
parser = OptionParser()
parser.add_option("-u", "--user", 
                  action="store", 
                  type="string", 
                  dest="user",
                  help="Twitter USER name")

(options, args) = parser.parse_args()

print options.user

# Get twitter Response
# From https://dev.twitter.com/docs/api/1/get/users/show
url = 'https://api.twitter.com/1/users/show.json'
parameters = dict(
  screen_name=options.user,
  include_entities='true')

response = requests.get(url, params = parameters) 

print response.json["followers_count"]

