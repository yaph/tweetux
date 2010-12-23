#!/usr/bin/env python
# TODO see http://code.google.com/p/google-app-engine-samples/source/browse/trunk/tasks/templatefilters.py
# for a template filter example
import os
import re
import cgi
import uuid
import wsgiref.handlers
import urllib

from google.appengine.ext import webapp
from google.appengine.api import urlfetch
from google.appengine.api import memcache
from google.appengine.ext import db
import gae_utils as gae

import twitter
import lib.oauth as oauth
import lib.datamodel as datamodel
from settings import *

class BaseHandler(gae.BaseHandler):
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
    self._client = oauth.OAuthClient(self, SETTINGS_OAUTH_TWITTER)

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
    self._client = oauth.OAuthClient(self, SETTINGS_OAUTH_TWITTER, raw_access_token)
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
    
class StatusUpdateHandler(BaseHandler):
  def post(self):
    status = cgi.escape(self.request.get('status'))
    in_reply_to_status_id = cgi.escape(self.request.get('in_reply_to_status_id'))

    params = {'status': status}
    if in_reply_to_status_id is not None:
      params['in_reply_to_status_id'] = in_reply_to_status_id
    
    key_name = self.get_cookie('oauth')
    access_token = datamodel.OAuthAccessToken.get_by_key_name(key_name)
    oauth_token = oauth.OAuthToken(access_token.oauth_token, access_token.oauth_token_secret)
    client = oauth.OAuthClient(self, SETTINGS_OAUTH_TWITTER, oauth_token)

    status = client.post('/statuses/update', **params)
    self.redirect('/')

class MainPage(BaseHandler):
  def get(self, action=''):
    if action:
      topic = urllib.unquote(action)
    else:
      topic = SETTINGS_TOPICS[0]

    key_name = self.get_cookie('oauth')
    logged_in = self.is_logged_in(key_name)

    tweets = get_data(self.request, topic)

    self.set_template_value('is_user_logged_in', logged_in)
    self.set_template_value('tweets', tweets)
    self.set_template_value('topics', SETTINGS_TOPICS)
    self.set_template_value('topic', topic)

    self.generate('text/html', 'index.html')

class JsPage(BaseHandler):
  def get(self):
    key_name = self.get_cookie('oauth')
    logged_in = self.is_logged_in(key_name)

    tweets = get_data(self.request)
    
    self.set_template_value('is_user_logged_in', logged_in)
    self.set_template_value('tweets', tweets)
    
    template_file = 'tweets.html'
    if self.request.get('q').find('from:') != -1:
      template_file = 'tweets_profile.html'
      
    self.generate('text/javascript', template_file)

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
          client = oauth.OAuthClient(self, SETTINGS_OAUTH_TWITTER, oauth_token)
          params = {'screen_name': screen_name}
          profile = client.get('/users/show', **params)
          memcache.set(cache_id, profile, 86400)
        except:
          pass

    params = { 'q': 'linux', 'from': screen_name }
    tweets = twitter.search_tweets(**params)
    if not tweets:
      tweets = {}

    self.set_template_value('is_user_logged_in', logged_in)
    self.set_template_value('tweets', tweets)
    self.set_template_value('profile', profile)
    self.set_template_value('screen_name', screen_name)

    self.generate('text/html', 'profile.html')

def get_data(request, topic=''):
  page = request.get('page')
  if page is '':
    page = 1
  elif not page.isnumeric():
    return False
  
  if topic is '':
    topic = request.get('q')
    if topic is '':
      topic = SETTINGS_TOPICS[0]
    else:
      # replace chars that can occur in screen names and searches
      check = re.sub(r'[_#:\s\+\-]', '', topic)
      if not check.isalnum():
        return False

  request_params = {'page': page, 'q': topic}
  result = twitter.search_tweets(**request_params)
  return result

def main():
  application = webapp.WSGIApplication(
    [('/', MainPage),
    ('/oauth/twitter/(.*)', TwitterOAuthHandler),
    ('/status/update', StatusUpdateHandler),
    ('/profile/\w+', ProfilePage),
    ('/tweets/(.*)', MainPage),
    ('/js/tweets', JsPage)],
    debug=False
  )
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
  main()