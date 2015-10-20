# -*- coding: utf-8 -*-
'''
Created on Feb 26, 2014

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import settings
import urllib

from handler import base


class AcceptableUsePolicyPage(base.SeoOrAngular):
  pass


class TosPage(base.SeoOrAngular):
  
  def respond_seo(self):
    self.render('seo/misc/tos.html', {'route_name': 'tos', 'page_title': 'Terms of service'})


class AboutPage(base.SeoOrAngular):
  
  def respond_seo(self):
    self.render('seo/misc/about.html', {'route_name': 'about', 'page_title': 'About'})


class PrivacyPage(base.SeoOrAngular):

  def respond_seo(self):
    self.render('seo/misc/privacy_policy.html', {'route_name': 'about', 'page_title': 'Privacy'})


class CopyrightPage(base.SeoOrAngular):

  def respond_seo(self):
    self.render('seo/misc/copyright_policy.html', {'route_name': 'about', 'page_title': 'Copyright'})

class AcceptableUsePolicyPage(base.SeoOrAngular):

  def respond_seo(self):
    self.render('seo/misc/acceptable_use_policy.html', {'route_name': 'about', 'page_title': 'Acceptable use policy'})

class SupportPage(base.SeoOrAngular):

  def respond_seo(self):
    pass


settings.ROUTES.extend(((r'/collections', base.AngularBlank),
                        (r'/buy/orders', base.AngularBlank),
                        (r'/buy/carts', base.AngularBlank),
                        (r'/sell/catalogs', base.AngularBlank),
                        (r'/sell/orders', base.AngularBlank),
                        (r'/sell/carts', base.AngularBlank),
                        (r'/following', base.AngularBlank),

                        # static pages
                        (r'/about', AboutPage, 'about'),
                        (r'/support', SupportPage, 'support'),
                        (r'/acceptable_use_policy', AcceptableUsePolicyPage, 'acceptable_use_policy'),
                        (r'/tos', TosPage, 'tos'),
                        (r'/privacy_policy', PrivacyPage, 'privacy'),
                        (r'/copyright_policy', CopyrightPage, 'copyright'),

                        # other
                        (r'/login/status', base.AngularBlank),
                        (r'/order/<key>', base.AngularBlank),
                        (r'/order/payment/success/<key>', base.AngularBlank),
                        (r'/order/payment/canceled/<key>', base.AngularBlank),
                        (r'/login_provider_connected/<provider>', base.AngularBlank),
                        (r'/admin/list/<kind>/<filter>', base.AngularBlank)))

# due development server bug, proxy the endpoint api to the real module
if settings.DEVELOPMENT_SERVER:

  from google.appengine.api import urlfetch

  class BackendProxy(base.RequestHandler):

    autoload_current_account = False
    autoload_model_meta = False

    def respond(self, *args, **kwargs):
      full_path = self.request.url.replace('/api/', '/api/proxy/')
      if self.request.method == 'POST':
        method = urlfetch.POST
      else:
        method = urlfetch.GET
      data = self.request.body
      if not data:
        data = self.request.params
      kwargs = {'payload': data, 'deadline': 60, 'method': method, 'url': full_path, 'headers': self.request.headers}
      result = urlfetch.fetch(**kwargs)
      self.response.write(result.content)

  settings.ROUTES.append((r'/api/<:.*>', BackendProxy))
