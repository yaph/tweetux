import wsgiref.handlers

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
import twitter

class JsPage(webapp.RequestHandler):
  def get(self):
    self.response.headers['Content-Type'] = 'text/javascript'
    result = twitter.get_tweets()
    if result:
      html = template.render('templates/tweets.html', dict(result = result))
      self.response.out.write(html)

def main():
  application = webapp.WSGIApplication([('/tweets', JsPage)], debug=True)
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
  main()