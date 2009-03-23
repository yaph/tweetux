import wsgiref.handlers

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
import tweets

class MainPage(webapp.RequestHandler):
  def get(self):
    self.response.headers['Content-Type'] = 'text/html'
    results = tweets.get_tweets()
    if results:
      html = template.render('index.html', dict(results = results))
    else:
      html = template.render('error.html', {})
    self.response.out.write(html)

def main():
  application = webapp.WSGIApplication([('/', MainPage)], debug=True)
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
  main()