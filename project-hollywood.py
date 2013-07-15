#coding=UTF-8

import webapp2
import os
from google.appengine.ext.webapp import template
import settings
import urllib
import time
import datetime
from google.appengine.api import images
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext.webapp import util
from google.appengine.ext import db
from google.appengine.ext import webapp

# koristim drugaciju konvenciju imenovanja polja, ne znam kakve su implikacije na django, ako bude neophodno rename cemo polja da odgovaraju django konvenciji...

class ObjectLog(db.Model):
    
    reference = db.ReferenceProperty(None, collection_name='reference', required=True)
    agent = db.ReferenceProperty(User, collection_name='agents', required=True)
    logged = db.DateTimeProperty(auto_now_add=True, required=True)
    event = db.IntegerProperty(required=True)
    state = db.IntegerProperty(required=True)
    message = db.TextProperty(required=True)
    note = db.TextProperty(required=True)
    log = db.BlobProperty(required=True) # ne znam da li bi i ovde trebalo TextProperty umesto BlobProperty


class Notification(db.Model):
    
    creator = db.ReferenceProperty(User, collection_name='creators', required=True)
    created = db.DateTimeProperty(auto_now_add=True, required=True)
    message = db.TextProperty(required=True)


class NotificationRecipient(db.Model):
    
    notification = db.ReferenceProperty(Notification, collection_name='notifications', required=True)
    recipient = db.ReferenceProperty(User, collection_name='recipients', required=True)


class NotificationRecipientOutlet(db.Model):
    
    notification_recepient = db.ReferenceProperty(NotificationRecipient, collection_name='notification_recepients', required=True)
    outlet = db.IntegerProperty(required=True) # ovde bi mogao i CategoryProperty, sta je vec bolje od to dvoje
    notified = db.DateTimeProperty()


class FeedbackRequest(db.Model):
    
    reference = db.LinkProperty(required=True)
    state = db.IntegerProperty(required=True)


class SupportRequest(db.Model):
    
    reference = db.LinkProperty(required=True) # mislim da je LinkProperty bolji od  StringProperty
    state = db.IntegerProperty(required=True)


class Content(db.Model):
    
    title = db.StringProperty(multiline=False, required=True)
    category = db.CategoryProperty(required=True) # ovde bi mogao i IntegerProperty, sta je vec bolje od to dvoje
    published = db.BooleanProperty(default=False, required=True)
    active_revision = db.ReferenceProperty(ContentRevision, collection_name='active_revisions', required=True)
    sequence = db.IntegerProperty(required=True)


class ContentRevision(db.Model):
    
    content = db.ReferenceProperty(Content, collection_name='contents')
    body = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True, required=True)


class Country(db.Model):
    
    name = db.StringProperty(multiline=False, required=True)
    code = db.StringProperty(multiline=False, required=True)


class CountrySubdivision(db.Model):
    
    parent = db.SelfReferenceProperty(collection_name='parents', required=True) # ovo je valjda ok
    country = db.ReferenceProperty(Country, collection_name='countries')
    name = db.StringProperty(multiline=False, required=True)
    code = db.StringProperty(multiline=False, required=True)
    category = db.CategoryProperty(required=True) # ovde bi mogao i IntegerProperty, sta je vec bolje od to dvoje


class ProductCategory(db.Model):
    
    parent = db.SelfReferenceProperty(collection_name='parents', required=True) # ovo je valjda ok
    name = db.StringProperty(multiline=False, required=True)
    sequence = db.IntegerProperty(required=True)
    state = db.IntegerProperty(required=True)


class ProductUOMCategory(db.Model):
    
    name = db.StringProperty(multiline=False, required=True)


class ProductUOM(db.Model):
    
    name = db.StringProperty(multiline=False, required=True)
    symbol = db.StringProperty(multiline=False, required=True)
    product_uom_category = db.ReferenceProperty(ProductUOMCategory, collection_name='product_uom_categories') # ovo bi mozda moglo da bude CategoryProperty, i da se time izbaci ProductUOMCategory model??
    rate = db.FloatProperty(required=True) # ili StringProperty, sta je vec bolje
    factor = db.FloatProperty(required=True) # ili StringProperty, sta je vec bolje
    rounding = db.FloatProperty(required=True) # ili StringProperty, sta je vec bolje
    display_digits = db.FloatProperty(required=True) # ili StringProperty, sta je vec bolje
    active = db.BooleanProperty(default=False, required=True)


class User(db.Model):
    
    state = db.IntegerProperty(required=True)


class UserConfig(db.Model):
    
    user = db.ReferenceProperty(User, collection_name='users', required=True)
    key = db.StringProperty(multiline=False, required=True)
    data = db.TextProperty(required=True) # ne znam da li bi i ovde trebalo nesto drugo umesto TextProperty


class UserEmail(db.Model):
    
    user = db.ReferenceProperty(User, collection_name='users', required=True)
    email = db.EmailProperty(required=True)
    primary = db.BooleanProperty(default=False, required=True) 


class UserIdentity(db.Model):
    
    user = db.ReferenceProperty(User, collection_name='users', required=True)
    user_email = db.ReferenceProperty(UserEmail, collection_name='user_emails', required=True)
    identity = db.StringProperty(multiline=False, required=True)
    provider = db.StringProperty(multiline=False, required=True)
    associated = db.BooleanProperty(default=True, required=True)


class UserIPAddress(db.Model):
    
    user = db.ReferenceProperty(User, collection_name='users', required=True)
    ip_address = db.StringProperty(multiline=False, required=True)
    logged = db.DateTimeProperty(auto_now_add=True, required=True)


class UserRole(db.Model):
    
    user = db.ReferenceProperty(User, collection_name='users', required=True)
    role = db.ReferenceProperty(Role, collection_name='roles', required=True)


class Role(db.Model):
    
    name = db.StringProperty(multiline=False, required=True)
    readonly = db.BooleanProperty(default=True, required=True)


class AgregateUserPermissions(db.Model):# ovo je za sada useless, osim ako odlucimo da ukinemo AgregateUserStorePermissions
    
    user = db.ReferenceProperty(User, collection_name='users', required=True)
    reference = db.ReferenceProperty(None, collection_name='reference', required=True)
    permissions = db.StringListProperty()# mozda da ovo bude samo StringProperty i da nosi jednu vrednost?


class AgregateUserStorePermissions(db.Model):# mislim da bi se moglo ovako uraditi, ili da se jos bolje resi
    
    user = db.ReferenceProperty(User, collection_name='users', required=True)
    store = db.ReferenceProperty(Store, collection_name='stores', required=True)
    permissions = db.StringListProperty()# mozda da ovo bude samo StringProperty i da nosi jednu vrednost?


class Store(db.Model):
    
    name = db.StringProperty(multiline=False, required=True)
    logo = blobstore.BlobReferenceProperty()
    state = db.IntegerProperty(required=True)


class StoreConfig(db.Model):
    
    store = db.ReferenceProperty(Store, collection_name='stores', required=True)
    key = db.StringProperty(multiline=False, required=True)
    data = db.TextProperty(required=True) # ne znam da li bi i ovde trebalo nesto drugo umesto TextProperty


class StoreContent(db.Model):
    
    store = db.ReferenceProperty(Store, collection_name='stores', required=True)
    title = db.StringProperty(multiline=False, required=True)
    body = db.TextProperty(required=True)
    sequence = db.IntegerProperty(required=True)


class StorePermission(db.Model):
    
    store = db.ReferenceProperty(Store, collection_name='stores', required=True)
    role = db.ReferenceProperty(Role, collection_name='roles', required=True)
    permission = db.StringProperty(multiline=False, required=True)


class StoreShippingExclusion(db.Model):
    
    store = db.ReferenceProperty(Store, collection_name='stores', required=True)
    country = db.ReferenceProperty(Country, collection_name='countries')
    region = db.ReferenceProperty(CountrySubdivision, collection_name='regions')
    city = db.ReferenceProperty(CountrySubdivision, collection_name='cities') # ne znam da li ce ovo postojati??
    postal_code_from = db.StringProperty(multiline=False, required=True)
    postal_code_to = db.StringProperty(multiline=False, required=True)


class StoreTax(db.Model):
    
    store = db.ReferenceProperty(Store, collection_name='stores', required=True)
    name = db.StringProperty(multiline=False, required=True)
    sequence = db.IntegerProperty(required=True)
    tax_type = db.IntegerProperty(required=True)
    amount = db.FloatProperty(required=True) # ili StringProperty, sta je vec bolje - obratiti paznju oko decimala posto ovo moze da bude i currency i procenat.
    location_exclusion = db.BooleanProperty(default=True, required=True)
    active = db.BooleanProperty(default=True, required=True)


class StoreTaxLocation(db.Model):
    
    store_tax = db.ReferenceProperty(StoreTax, collection_name='store_taxes', required=True)
    country = db.ReferenceProperty(Country, collection_name='countries')
    region = db.ReferenceProperty(CountrySubdivision, collection_name='regions')
    city = db.ReferenceProperty(CountrySubdivision, collection_name='cities') # ne znam da li ce ovo postojati??
    postal_code_from = db.StringProperty(multiline=False, required=True)
    postal_code_to = db.StringProperty(multiline=False, required=True)


class StoreTaxApplication(db.Model):
    
    store_tax = db.ReferenceProperty(StoreTax, collection_name='store_taxes', required=True)
    application = db.IntegerProperty(required=True)
    product_category = db.ReferenceProperty(ProductCategory, collection_name='product_categories')
    store_carrier = db.ReferenceProperty(StoreCarrier, collection_name='store_carriers')


class StoreCarrier(db.Model):
    
    store = db.ReferenceProperty(Store, collection_name='stores', required=True)
    name = db.StringProperty(multiline=False, required=True)
    active = db.BooleanProperty(default=True, required=True)


class StoreCarrierLine(db.Model):
    
    store_carrier = db.ReferenceProperty(StoreCarrier, collection_name='store_carriers', required=True)
    name = db.StringProperty(multiline=False, required=True)
    sequence = db.IntegerProperty(required=True)
    location_exclusion = db.BooleanProperty(default=True, required=True)
    active = db.BooleanProperty(default=True, required=True)


class StoreCarrierLineLocation(db.Model):
    
    store_carrier_line = db.ReferenceProperty(StoreCarrierLine, collection_name='store_carrier_lines', required=True)
    country = db.ReferenceProperty(Country, collection_name='countries')
    region = db.ReferenceProperty(CountrySubdivision, collection_name='regions')
    city = db.ReferenceProperty(CountrySubdivision, collection_name='cities') # ne znam da li ce ovo postojati??
    postal_code_from = db.StringProperty(multiline=False, required=True)
    postal_code_to = db.StringProperty(multiline=False, required=True)


class StoreCarrierLinePricelist(db.Model):
    
    store_carrier_line = db.ReferenceProperty(StoreCarrierLine, collection_name='store_carrier_lines', required=True)
    condition_type = db.IntegerProperty(required=True)
    condition_operator = db.IntegerProperty(required=True)
    condition_value = db.IntegerProperty(required=True)# verovatno da ce trebati i ovde product_uom_id kako bi prodavac mogao da ustima vrednost koju zeli... mozemo ici i na to da je uom fiksan ovde, a isto tako i fiksan u product measurements-ima...
    price_type = db.IntegerProperty(required=True)
    price_type_factor = db.IntegerProperty(required=True)
    amount = db.FloatProperty(required=True) # ili StringProperty, sta je vec bolje


class BuyerAddress(db.Model):
    
    user = db.ReferenceProperty(User, collection_name='users', required=True)
    name = db.StringProperty(multiline=False, required=True)
    country = db.ReferenceProperty(Country, collection_name='countries')
    region = db.ReferenceProperty(CountrySubdivision, collection_name='regions')
    city = db.ReferenceProperty(CountrySubdivision, collection_name='cities')
    postal_code = db.StringProperty(multiline=False, required=True)
    street_address = db.StringProperty(multiline=False, required=True)
    street_address2 = db.StringProperty(multiline=False, required=True)
    email = db.EmailProperty(required=True)
    telephone = db.PhoneNumberProperty(required=True) # ne znam kakva se korist moze imati od PostalAddressProperty 
    default_shipping = db.BooleanProperty(default=True, required=True)
    default_billing = db.BooleanProperty(default=True, required=True)


class BuyerCollection(db.Model):
    
    user = db.ReferenceProperty(User, collection_name='users', required=True)
    name = db.StringProperty(multiline=False, required=True)
    notifications = db.BooleanProperty(default=True, required=True)


class BuyerCollectionStore(db.Model):
    
    buyer_collection = db.ReferenceProperty(BuyerCollection, collection_name='buyer_collections', required=True)
    store = db.ReferenceProperty(Store, collection_name='stores', required=True)


class BuyerCollectionProductCategory(db.Model):
    
    buyer_collection = db.ReferenceProperty(BuyerCollection, collection_name='buyer_collections', required=True)
    product_category = db.ReferenceProperty(ProductCategory, collection_name='product_categories')








class MainHandler(webapp2.RequestHandler):
  def get(self):
    template_values = {
      'name': "World",
    }

    path = os.path.join(os.path.dirname(__file__), 'index.html')
    self.response.out.write(template.render(path, template_values))


app = webapp2.WSGIApplication([
  ('/.*', MainHandler),
], debug=True)