from google.appengine.api import urlfetch
from google.appengine.api import memcache
from django.utils import simplejson
import urllib

def get_tweets():
  url = u'http://search.twitter.com/search.json?%s'
  params = urllib.urlencode({
    "q": "#linux",
    "rpp": 50
  })
  request_url = url % params
  
  # try to load from cache
  cache_id = request_url.encode('base64')
  results = memcache.get(cache_id)
  if results is not None:
    return results
  else:
    # try to fetch from twitter
    try:
      result = urlfetch.fetch(request_url)
      if result.status_code == 200:
        results = simplejson.loads(result.content)['results']
        # try to cache for 60 seconds
        memcache.set(cache_id, results, 60)
        return results
    except:
      return False

if __name__ == "__main__":
  get_tweets()