# includes code from http://github.com/ryanwi/twitteroauth/tree/master
import os
import re
import cgi
import uuid
import wsgiref.handlers

from google.appengine.ext import webapp
from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.api import urlfetch
from google.appengine.ext.webapp import template
from django.template import TemplateDoesNotExist

import twitter
import lib.oauth as oauth
import lib.datamodel as datamodel
from settings import *

class BaseHandler(webapp.RequestHandler):
  """Supplies a common template generation function.

  When you call generate(), we augment the template variables supplied with
  the current user in the 'user' variable and the current webapp request
  in the 'request' variable.
  """
  def generate(self, content_type='text/html', template_name='index.html', **template_values):

    # set the content type
    content_type += '; charset=utf-8'
    self.response.headers["Content-Type"] = content_type

    values = {
      'request': self.request,
      'host': self.request.host,
      'application_name': 'tweetux',
    }

    values.update(template_values)
    directory = os.path.dirname(__file__)
    path = os.path.join(directory, os.path.join('templates', template_name))
    
    try:
      self.response.out.write(template.render(path, values))

    except TemplateDoesNotExist, e:
      self.response.set_status(404)
      self.response.out.write(template.render(os.path.join('templates', '404.html'), values))

  def error(self, status_code):
    webapp.RequestHandler.error(self, status_code)
    if status_code == 404:
      self.generate('404.html')

  def get_cookie(self, name):
    return self.request.cookies.get(name)

  def set_cookie(self, name, value, path='/', expires="Fri, 28-Dec-2666 23:59:59 GMT"):
    self.response.headers.add_header(
      'Set-Cookie', '%s=%s; path=%s; expires=%s' %
      (name, value, path, expires))

  def expire_cookie(self, name, path='/'):
    self.response.headers.add_header(
    'Set-Cookie', '%s=; path=%s; expires="Fri, 31-Dec-1999 23:59:59 GMT"' %
    (name, path))

  def create_uuid(self):
    return 'id-%s' % uuid.uuid4().hex

  def is_logged_in(self, key_name):
    logged_in = False
    if key_name is not None:
      logged_in = True
    return logged_in

class TwitterOAuthHandler(BaseHandler):
  '''Request Handler for all OAuth workflow when authenticating user'''

  def get(self, action=''):
    self._client = oauth.OAuthClient(self, OAUTH_APP_SETTINGS)

    if action == 'login':
      self.login()
    elif action == 'logout':
      self.logout()
    elif action == 'callback':
      self.callback()
    elif action == 'cleanup':
      self.cleanup()

  def login(self):
    # get a request token
    raw_request_token = self._client.get_request_token()

    # store the request token
    request_token = datamodel.OAuthRequestToken(
      oauth_token=raw_request_token.key,
      oauth_token_secret=raw_request_token.secret,
    )
    request_token.put()

    # get the authorize url and redirect to twitter
    authorize_url = self._client.get_authorize_url(raw_request_token)
    self.redirect(authorize_url)

  def logout(self):
    self.expire_cookie('oauth')
    self.redirect('/')

  def callback(self):
    # lookup request token
    raw_oauth_token = self.request.get('oauth_token')
    request_token = datamodel.OAuthRequestToken.all().filter('oauth_token =', raw_oauth_token).fetch(1)[0]

    # get an access token for the authorized user
    oauth_token = oauth.OAuthToken(request_token.oauth_token, request_token.oauth_token_secret)
    raw_access_token = self._client.get_access_token(oauth_token)

    # get the screen_name
    self._client = oauth.OAuthClient(self, OAUTH_APP_SETTINGS, raw_access_token)
    screen_name = self._client.get('/account/verify_credentials')['screen_name']

    # delete any old access tokens for this user
    old = datamodel.OAuthAccessToken.all().filter('specifier =', screen_name)
    db.delete(old)
        
    # store access token
    key_name = self.create_uuid()
    access_token = datamodel.OAuthAccessToken(
      key_name=key_name,
      specifier=screen_name,
      oauth_token=raw_access_token.key,
      oauth_token_secret=raw_access_token.secret
    )
    access_token.put()

    self.set_cookie('oauth', key_name)
    self.redirect('/')

class MainPage(BaseHandler):
  def get(self):
    key_name = self.get_cookie('oauth')
    logged_in = self.is_logged_in(key_name)

    tweets = get_data(self.request)
    values = {
      'is_user_logged_in':logged_in,
      'tweets':tweets
    }
    self.generate('text/html', 'index.html', **values)

class JsPage(BaseHandler):
  def get(self):
    key_name = self.get_cookie('oauth')
    logged_in = self.is_logged_in(key_name)

    tweets = get_data(self.request)
    values = {
      'is_user_logged_in':logged_in,
      'tweets':tweets
    }
    
    template_file = 'tweets.html'
    if self.request.get('q').find('from:') != -1:
      template_file = 'tweets_profile.html'
      
    self.generate('text/javascript', template_file, **values)

class ProfilePage(BaseHandler):
  def get(self):
    profile = {}
    screen_name = self.request.path.split('/')[-1]

    key_name = self.get_cookie('oauth')
    logged_in = self.is_logged_in(key_name)

    if logged_in:
      cache_id = screen_name.encode('base64')
      profile = memcache.get(cache_id)

      if not profile:
        try:
          access_token = datamodel.OAuthAccessToken.get_by_key_name(key_name)
          oauth_token = oauth.OAuthToken(access_token.oauth_token, access_token.oauth_token_secret)
          client = oauth.OAuthClient(self, OAUTH_APP_SETTINGS, oauth_token)
          params = {'screen_name': screen_name}
          profile = client.get('/users/show', **params)
          memcache.set(cache_id, profile, 86400)
        except:
          pass

    params = { 'q': 'linux', 'from': screen_name }
    tweets = twitter.search_tweets(**params)
    if not tweets:
      tweets = {}

    values = {
      'is_user_logged_in':logged_in,
      'profile':profile,
      'tweets':tweets,
      'screen_name':screen_name
    }

    self.generate('text/html', 'profile.html', **values)

def get_data(request):
  page = request.get('page')
  if page is '':
    page = 1
  elif not page.isnumeric():
    return False
  
  q = request.get('q')
  if q is '':
    q = 'linux'
  else:
    # replace chars that can occur in screen names and searches
    check = re.sub(r'[_#:\s\+\-]', '', q)
    if not check.isalnum():
      return False

  request_params = {'page': page, 'q': q}
  result = twitter.search_tweets(**request_params)
  return result

def main():
  application = webapp.WSGIApplication(
    [('/', MainPage),
    ('/oauth/twitter/(.*)', TwitterOAuthHandler),
    ('/profile/\w+', ProfilePage),
    ('/tweets', JsPage)],
    debug=False
  )
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
  main()