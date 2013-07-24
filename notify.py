#coding=UTF-8

import webapp2
from google.appengine.api import taskqueue
from google.appengine.api import mail
from google.appengine.ext import ndb

# ovo je neki predlog osnovice, tu se treba ubaciti jos inteligencije, handlovanje gresaka, akrobacije....
class NotifyEngine(webapp2.RequestHandler):
    def post(self):
        reference_key = self.request.get('reference_key')
        object_log_key = self.request.get('object_log_key')
        notify_sender = self.request.get('notify_sender')
        notify_to = self.request.get('notify_to')
        notify_subject = self.request.get('notify_subject')
        notify_outlet = self.request.get('notify_outlet')
        def notify():
          object_log_future = ObjectLog.get_by_id_async(object_log_key, parent=reference_key)
          if (notify_outlet == 'email' | notify_outlet == None):
            object_log = object_log_future.get_result()
            mail.send_mail(sender=notify_sender, to=notify_to, subject=notify_subject, body=object_log.message)
        db.run_in_transaction(notify)


app = webapp2.WSGIApplication([
                              ('/notify', NotifyEngine)],
                              debug=True)