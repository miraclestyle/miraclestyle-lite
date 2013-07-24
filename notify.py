#coding=UTF-8

import webapp2
from google.appengine.api import taskqueue
from google.appengine.api import mail
from google.appengine.ext import ndb

# ovo je neki predlog osnovice, tu se treba ubaciti jos inteligencije, handlovanje gresaka, akrobacije....
class NotifyEngine(webapp2.RequestHandler):
    def post(self):
        object_log_key = self.request.get('key')
        notify_sender = self.request.get('sender')
        notify_to = self.request.get('to')
        notify_subject = self.request.get('subject')
        notify_outlet = self.request.get('outlet')
        def notify():
          object_log_future = ndb.Key(object_log_key).get_async()
          if (notify_outlet == 'email' | notify_outlet == None):
            object_log = object_log_future.get_result()
            mail.send_mail(sender=notify_sender, to=notify_to, subject=notify_subject, body=object_log.message)
        db.run_in_transaction(notify)


app = webapp2.WSGIApplication([
                              ('/notify', NotifyEngine)],
                              debug=True)