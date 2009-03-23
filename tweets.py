from google.appengine.api import urlfetch
from django.utils import simplejson
import urllib

def get_tweets():
  url = u'http://search.twitter.com/search.json?%s'
  params = urllib.urlencode({
    "q": "#linux",
    "rpp": 50
  })
  request_url = url % params
  try:
    result = urlfetch.fetch(request_url)
    if result.status_code == 200:
      results = simplejson.loads(result.content)
      return results['results']
  except:
    return False

if __name__ == "__main__":
  get_tweets()