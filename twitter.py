from google.appengine.api import urlfetch
from google.appengine.api import memcache
from django.utils import simplejson
import urllib

def search_tweets(**request_params):
  url = u'http://search.twitter.com/search.json?%s'
  default_params = { 'q': '#linux', 'rpp': 10 }
  default_params.update(request_params)
  request_url = url % urllib.urlencode(default_params)
  
  # try to load from cache
  cache_id = request_url.encode('base64')
  result = memcache.get(cache_id)
  if result is not None:
    return result
  else:
    # for debugging
    #result = simplejson.load(open('./search.json', 'rb'))
    #return result

    # try to fetch from twitter
    try:
      result = urlfetch.fetch(request_url)
      if result.status_code == 200:
        result = simplejson.loads(result.content)

        # cache for 5 minutes
        memcache.set(cache_id, result, 300)
        return result
    except:
      return False

def user_tweets(screen_name):
  url = u'http://twitter.com/statuses/user_timeline.json?%s'
  params = {'screen_name': screen_name}
  return api_request(url, **params)
  
def get_profile(screen_name):
  url = u'http://twitter.com/users/show.json?%s'
  params = {'screen_name': screen_name}
  return api_request(url, **params)

def api_request(url, **params):
  request_url = url % urllib.urlencode(params)
  try:
    result = urlfetch.fetch(request_url)
    if result.status_code == 200:
      result = simplejson.loads(result.content)
      return result
  except:
      return False

if __name__ == "__main__":
  get_tweets()