#coding=UTF-8

import webapp2
from google.appengine.api import taskqueue
from google.appengine.api import mail

# ovo je neki predlog osnovice, tu se treba ubaciti jos inteligencije, handlovanje gresaka, akrobacije....
class NotifyEngine(webapp2.RequestHandler):
    def post(self):
        notify_outlet = self.request.get('outlet')# max size 500 chars
        notify_sender = self.request.get('sender')# max size 500 chars
        notify_to = self.request.get('to')# max size 500 chars
        notify_subject = self.request.get('subject')# max size 500 chars
        notify_message = self.request.get('message')# max size 64kb
        if (notify_outlet == 'email' | notify_outlet == None):
          mail.send_mail(sender=notify_sender, to=notify_to, subject=notify_subject, body=notify_message)
        else:
          pass


app = webapp2.WSGIApplication([
                              ('/notify', NotifyEngine)],
                              debug=True)