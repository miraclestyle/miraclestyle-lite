# -*- coding: utf-8 -*-
'''
Created on Jul 15, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from webapp2_extras.i18n import _
from app import form

class LoginForm(form.Form):
      password = form.PasswordField(_('Enter Password Please'), validators=[form.validators.required()])