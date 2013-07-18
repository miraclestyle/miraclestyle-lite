# -*- coding: utf-8 -*-
'''
Created on Jul 15, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from webapp2_extras.i18n import _
from app import form

class LoginForm(form.Form):
      password = form.PasswordField(_('Enter Password Please'), validators=[form.validators.required()])
      
class TestForm(form.Form):
 
      mode = form.StringField(_('Model Key'))
      remove_all = form.SubmitField(_('Delete Selected Children'))
      models = form.SelectMultipleField(_('Children'), choices=[])
  
      times = form.IntegerField(_('How many times to add records'))
      cause_error = form.IntegerField(_('At what iter to cause exception'))
      transaction = form.BooleanField(_('Run query in transaction'))
      
      commit_trans = form.SubmitField(_('Run put'))