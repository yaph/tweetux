from google.appengine.api import urlfetch
from google.appengine.api import memcache
from django.utils import simplejson
import sys
import urllib

def search_tweets(**request_params):
  url = u'http://search.twitter.com/search.json?%s'
  default_params = { 'q': 'linux', 'rpp': 10 }
  default_params.update(request_params)
  return api_request(url, 300, **default_params)

def user_tweets(screen_name):
  url = u'http://twitter.com/statuses/user_timeline.json?%s'
  params = {'screen_name': screen_name}
  return api_request(url, 600, **params)
  
def get_profile(screen_name):
  url = u'http://twitter.com/users/show.json?%s'
  params = {'screen_name': screen_name}
  return api_request(url, 86400, **params)

def api_request(url, cache_time, **params):
  request_url = url % urllib.urlencode(params)
  if cache_time != 0:
    # try to load from cache
    cache_id = request_url.encode('base64')
    result = memcache.get(cache_id)
    if result is not None:
      return result

  try:
    result = urlfetch.fetch(request_url)
    if result.status_code == 200:
      result = simplejson.loads(result.content)
      if cache_time != 0:
        # cache for 5 minutes
        memcache.set(cache_id, result, cache_time)
      return result
    elif result.status_code == 400:
      print 'Limit exceeded'
      sys.exit()
  except:
    return False

if __name__ == "__main__":
  get_tweets()