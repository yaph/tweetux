import wsgiref.handlers

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
import twitter

class MainPage(webapp.RequestHandler):
  def get(self):
    self.response.headers['Content-Type'] = 'text/html'
    result = get_data(self.request)
    if result:
      html = template.render('templates/index.html', dict(result = result))
    else:
      html = template.render('templates/error.html', {})
    self.response.out.write(html)

class JsPage(webapp.RequestHandler):
  def get(self):
    self.response.headers['Content-Type'] = 'text/javascript'
    result = get_data(self.request)
    if result:
      html = template.render('templates/tweets.html', dict(result = result))
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
  result = twitter.get_tweets(**request_params)
  return result

def main():
  application = webapp.WSGIApplication([
    ('/', MainPage),
    ('/tweets', JsPage)
    ],
    debug=True
  )
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
  main()