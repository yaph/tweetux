import wsgiref.handlers

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
import twitter

class MainPage(webapp.RequestHandler):
  def get(self):
    self.response.headers['Content-Type'] = 'text/html'
    result = twitter.get_tweets()
    if result:
      html = template.render('templates/index.html', dict(result = result))
    else:
      html = template.render('templates/error.html', {})
    self.response.out.write(html)

def main():
  application = webapp.WSGIApplication([('/', MainPage)], debug=True)
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
  main()