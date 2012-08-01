import requests

url = 'https://api.twitter.com/1/users/show.json'

parameters = dict(
  screen_name='talha_131',
  include_entities='true')

response = requests.get(url, params = parameters) 
for item in response.json:
    print item
