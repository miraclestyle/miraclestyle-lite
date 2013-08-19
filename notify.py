#coding=UTF-8

import webapp2
from google.appengine.api import taskqueue
from google.appengine.api import mail
from google.appengine.ext import ndb

from app.kernel.models import User

class NotifySegments(webapp2.RequestHandler):
      def post(self):
          command = self.request.get('command')
          offset = int(self.request.get('offset', 0))
          failed = self.request.get_all('failed')
          fail = list()
          
          limit = 50 # send 50 emails per task
          if command == 'send_email_to_all_users':
             all = User.query().fetch(offset, limit)
             
             if failed:
                all += ndb.get_multi(failed)
             
             if not all:
                # if there is no more users, exit this task
                return
            
             for a in all:
                 try:
                   # mail.Send(.....) here goes the send code
                   pass
                 except Exception:
                     fail.append('user key that did not recieve mail due mail.send failure')
                     
          if len(fail):
             taskqueue.add(url='/notify_in_segments', params={'failed' : fail, 'offset' : limit + offset, 'command' : command})
             
          

# ovo je neki predlog osnovice, tu se treba ubaciti jos inteligencije, handlovanje gresaka, akrobacije....
class NotifyEngine(webapp2.RequestHandler):
    def post(self):
        notify_outlet = self.request.get('outlet')# max size 500 chars
        notify_sender = self.request.get('sender')# max size 500 chars
        notify_to = self.request.get('to')# max size 500 chars
        notify_subject = self.request.get('subject')# max size 500 chars
        notify_message = self.request.get('message')# max size 64kb
        if (notify_outlet == 'email'):
          mail.send_mail(sender=notify_sender, to=notify_to, subject=notify_subject, body=notify_message)
        elif(notify_outlet == 'all'):# ovaj validator treba da pusti poruku na sve outlete (treba jos o ovome odluciti??)
          mail.send_mail(sender=notify_sender, to=notify_to, subject=notify_subject, body=notify_message)
        else:
          pass


app = webapp2.WSGIApplication([
                              ('/notify', NotifyEngine), ('/notify_in_segments', NotifySegments)],
                              debug=True)