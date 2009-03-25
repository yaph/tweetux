import wsgiref.handlers

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
import twitter

class MainPage(webapp.RequestHandler):
  def get(self):
    self.response.headers['Content-Type'] = 'text/html'
    tweets = get_data(self.request)
    if tweets:
      html = template.render('templates/index.html', dict(tweets = tweets))
    else:
      html = template.render('templates/error.html', {})
    self.response.out.write(html)

class ProfilePage(webapp.RequestHandler):
  def get(self):
    self.response.headers['Content-Type'] = 'text/html'
    screen_name = self.request.path.split('/')[-1]
    profile = twitter.get_profile(screen_name)
    tweets = twitter.user_tweets(screen_name)
    if profile and tweets:
      html = template.render('templates/profile.html', dict(profile = profile, tweets = tweets))
    else:
      html = template.render('templates/error.html', {})
    self.response.out.write(html)

class JsPage(webapp.RequestHandler):
  def get(self):
    self.response.headers['Content-Type'] = 'text/javascript'
    tweets = get_data(self.request)
    if tweets:
      html = template.render('templates/tweets.html', dict(tweets = tweets))
      self.response.out.write(html)

def get_data(request):
  page = request.get('page')
  if page is '':
    page = 1
  elif not page.isnumeric():
    return False
  
  q = request.get('q')
  if q is '':
    q = '#linux'
  else:
    check = q.strip('#')
    if not check.isalnum():
      return False

  request_params = {'page': page, 'q': q}
  result = twitter.search_tweets(**request_params)
  return result

def main():
  application = webapp.WSGIApplication([
    ('/', MainPage),
    ('/profile/\w+', ProfilePage),
    ('/tweets', JsPage)
    ],
    debug=True
  )
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
  main()