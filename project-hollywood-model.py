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
from google.appengine.ext import ndb
from google.appengine.ext import webapp

# koristim drugaciju konvenciju imenovanja polja, ne znam kakve su implikacije na django, ako bude neophodno rename cemo polja da odgovaraju django konvenciji...

'''
Ovo su zabranjena imena propertija:

all
app
copy
delete
entity
entity_type
fields
from_entity
get
gql
instance_properties
is_saved
key
key_name
kind
parent
parent_key
properties
put
setdefault
to_xml
update
'''

class ObjectLog(ndb.Model):
    
    # root
    reference = ndb.KeyProperty('1',required=True)# kind izvlacimo iz kljuca pomocu key.kind() funkcije
    agent = ndb.KeyProperty('2', kind=User, required=True)
    logged = ndb.DateTimeProperty('3', auto_now_add=True, required=True)
    event = ndb.IntegerProperty('4', required=True)
    state = ndb.IntegerProperty('5', required=True)
    message = ndb.TextProperty('6', required=True)
    note = ndb.TextProperty('7', required=True)
    log = ndb.TextProperty('8', required=True)
    
    # ovako se smanjuje storage u Datastore, i trebalo bi sprovesti to isto na sve modele
    @classmethod
    def _get_kind(cls):
      return 'OL'

# mislim da je ovaj notification sistem neefikasan, moramo prostudirati ovo...
class Notification(ndb.Model):
    
    # root
    creator = ndb.KeyProperty('1', kind=User, required=True)
    created = ndb.DateTimeProperty('2', auto_now_add=True, required=True)
    message = ndb.TextProperty('3', required=True)


class NotificationRecipient(ndb.Model):
    
    # ancestor Notification
    recipient = ndb.KeyProperty('1', kind=User, required=True)
    outlets = ndb.StructuredProperty(NotificationOutlet, '2', repeated=True)


class NotificationOutlet(ndb.Model):
    
    # StructuredProperty model
    outlet = ndb.IntegerProperty('1', required=True)
    notified = ndb.BooleanProperty('2', default=False)


class FeedbackRequest(ndb.Model):
    
    # root
    reference = ndb.StringProperty('1', required=True)
    state = ndb.IntegerProperty('2', required=True)
    
    # primer helper funkcije u slucajevima gde se ne koristi ancestor mehanizam za pristup relacijama
    @property
    def logs(self):
      return ObjectLog.gql("WHERE reference = :1", self.key())


class SupportRequest(ndb.Model):
    
    # root
    reference = ndb.StringProperty('1', required=True)
    state = ndb.IntegerProperty('2', required=True)


class Content(ndb.Model):
    
    # root
    title = ndb.StringProperty('1', required=True)
    category = ndb.IntegerProperty('2', required=True)
    published = ndb.BooleanProperty('3', default=False)
    active_revision = ndb.KeyProperty('4', kind=ContentRevision, required=True)
    sequence = ndb.IntegerProperty('5', required=True)


class ContentRevision(ndb.Model):
    
    # ancestor Content
    body = ndb.TextProperty('1', required=True)
    created = ndb.DateTimeProperty('2', auto_now_add=True, required=True)


class Image(ndb.Model):
    
    # ancestor Any Object
    image = blobstore.BlobKeyProperty('1', required=True)# verovatno je i dalje ovaj property od klase blobstore
    sequence = ndb.IntegerProperty('2', required=True)

class Country(ndb.Model):
    
    # root
    code = ndb.StringProperty('1', required=True)
    name = ndb.StringProperty('2', required=True)


class CountrySubdivision(ndb.Model):
    
    # ancestor Country
    parent_record = ndb.KeyProperty('1', kind=CountrySubdivision)
    name = ndb.StringProperty('2', required=True)
    code = ndb.StringProperty('3', required=True)
    type = ndb.IntegerProperty('4', required=True)


class Location(ndb.Model):
    
    # ancestor Any Object (Store, StoreTax, StoreCarrierLine, Catalog...)
    country = ndb.KeyProperty('1', kind=Country, required=True)
    region = ndb.KeyProperty('2', kind=CountrySubdivision)
    city = ndb.KeyProperty('3', kind=CountrySubdivision)# ne znam da li ce ovo postojati??
    postal_code_from = ndb.StringProperty('4')
    postal_code_to = ndb.StringProperty('5')


class ProductCategory(ndb.Model):
    
    # root
    parent_record = ndb.KeyProperty('1', kind=ProductCategory)
    name = ndb.StringProperty('2', required=True)
    sequence = ndb.IntegerProperty('3', required=True)
    state = ndb.IntegerProperty('4', required=True)


class ProductUOMCategory(ndb.Model):
    
    # root
    name = ndb.StringProperty('1', required=True)


class ProductUOM(ndb.Model):
    
    # ancestor ProductUOMCategory
    name = ndb.StringProperty('1', required=True)
    symbol = ndb.StringProperty('2', required=True)
    rate = ndb.FloatProperty('3', required=True)# ovde ide custom decimal property
    factor = ndb.FloatProperty('4', required=True)# ovde ide custom decimal property
    rounding = ndb.FloatProperty('5', required=True)# ovde ide custom decimal property
    digits = ndb.IntegerProperty('6', required=True)
    active = ndb.BooleanProperty('7', default=True)


class User(ndb.Model):
    
    # root
    state = ndb.IntegerProperty('1', required=True)

# da li ima potrebe ovo stavljati da je Expando?
class UserConfig(ndb.Model):
    
    # ancestor User
    #_default_indexed = False
    #pass
    attribute = ndb.StringProperty('1', required=True)
    attribute_value = ndb.TextProperty('2', required=True)


class UserEmail(ndb.Model):
    
    # ancestor User
    email = ndb.StringProperty('1', required=True)
    primary = ndb.BooleanProperty('2', default=True)


class UserIdentity(ndb.Model):
    
    # ancestor User
    user_email = ndb.KeyProperty('1', kind=UserEmail, required=True)
    identity = ndb.StringProperty('2', required=True)
    provider = ndb.StringProperty('3', required=True)
    associated = ndb.BooleanProperty('4', default=True)

# moze li ovo snimati GAE log ?
class UserIPAddress(ndb.Model):
    
    # ancestor User
    ip_address = ndb.StringProperty('1', required=True)
    logged = ndb.DateTimeProperty('2', auto_now_add=True, required=True)


class UserRole(ndb.Model):
    
    # splice
    user = ndb.KeyProperty('1', kind=User, required=True)
    role = ndb.KeyProperty('2', kind=Role, required=True)


# ovo je pojednostavljena verzija permisija, ispod ovog modela je skalabilna verzija koja se moze prilagoditi i upotrebiti umesto ove 
class Role(ndb.Model):
    
    # ancestor Store (Any?)
    name = ndb.StringProperty('1', required=True)
    permissions = ndb.StringProperty('2', indexed=False, repeated=True)
    readonly = ndb.BooleanProperty('3', default=True)


'''
Primer skalabilne verzije implementacije permission sistema
class Role(ndb.Model):
    
    # ancestor App
    name = ndb.StringProperty('1', required=True)
    permissions = ndb.StructuredProperty(Permission, '2', required=True)
    readonly = ndb.BooleanProperty('3', default=True)


class Permission(ndb.Model):
    
    # ancestor Object - Any
    permissions = ndb.StringProperty('1', indexed=False, repeated=True)
'''

# ovo je agregaciona tabela radi optimizacije
#mozda ce trebati agregate tabela za roles tab u Store
class AggregateUserPermissions(ndb.Model):
    
    # splice
    user = ndb.KeyProperty('1', kind=User, required=True)
    reference = ndb.KeyProperty('2',required=True)
    permissions = ndb.StringProperty('3', indexed=False, repeated=True)


class Store(ndb.Model):
    
    # root
    name = ndb.StringProperty('1', required=True)
    logo = blobstore.BlobKeyProperty('2', required=True)# verovatno je i dalje ovaj property od klase blobstore
    state = ndb.IntegerProperty('3', required=True)

# da li ima potrebe ovo stavljati da je Expando?
class StoreConfig(ndb.Model):
    
    # ancestor Store
    #_default_indexed = False
    #pass
    attribute = ndb.StringProperty('1', required=True)
    attribute_value = ndb.TextProperty('2', required=True)


class StoreContent(ndb.Model):
    
    # ancestor Store, Catalog (kesiranje)
    title = ndb.StringProperty('1', required=True)
    body = ndb.TextProperty('2', required=True)
    sequence = ndb.IntegerProperty('3', required=True)


class StoreTax(ndb.Expando):
    
    # ancestor Store
    name = ndb.StringProperty('1', required=True)
    sequence = ndb.IntegerProperty('2', required=True)
    type = ndb.IntegerProperty('3', required=True)
    amount = ndb.FloatProperty('4', required=True)# ovde ide custom decimal property - obratiti paznju oko decimala posto ovo moze da bude i currency i procenat.
    location_exclusion = ndb.BooleanProperty('5', default=False)
    active = ndb.BooleanProperty('6', default=True)
    #product_category = ndb.KeyProperty('7', kind=ProductCategory)
    #store_carrier = ndb.KeyProperty('8', kind=StoreCarrier)


class StoreCarrier(ndb.Model):
    
    # ancestor Store
    name = ndb.StringProperty('1', required=True)
    active = ndb.BooleanProperty('2', default=True)


class StoreCarrierLine(ndb.Model):
    
    # ancestor StoreCarrier
    name = ndb.StringProperty('1', required=True)
    sequence = ndb.IntegerProperty('2', required=True)
    location_exclusion = ndb.BooleanProperty('3', default=False)
    active = ndb.BooleanProperty('4', default=True)
    pricelists = ndb.StructuredProperty(StoreCarrierPricelist, '5', repeated=True)

# jos je upitno da li cemo ovo ovako zadrzati, to sve zavizi od querija i indexa...
class StoreCarrierPricelist(ndb.Model):
    
    # StructuredProperty model
    condition_type = ndb.IntegerProperty('1', required=True)
    condition_operator = ndb.IntegerProperty('2', required=True)
    condition_value = ndb.FloatProperty('3', required=True)# ovde ide custom decimal property - verovatno da ce trebati i ovde product_uom_id kako bi prodavac mogao da ustima vrednost koju zeli... mozemo ici i na to da je uom fiksan ovde, a isto tako i fiksan u product measurements-ima...
    price_type = ndb.IntegerProperty('4', required=True)
    price_type_factor = ndb.IntegerProperty('5', required=True)
    amount = ndb.FloatProperty('6', required=True)# ovde ide custom decimal property


class BuyerAddress(ndb.Model):
    
    # ancestor User
    name = ndb.StringProperty('1', required=True)
    country = ndb.KeyProperty('2', kind=Country, required=True)
    region = ndb.KeyProperty('3', kind=CountrySubdivision, required=True)
    city = ndb.KeyProperty('4', kind=CountrySubdivision, required=True)# mozda bude string ??
    postal_code = ndb.StringProperty('5', required=True)
    street_address = ndb.StringProperty('6', required=True)
    street_address2 = ndb.StringProperty('7')
    email = ndb.StringProperty('8')
    telephone = ndb.StringProperty('9')
    default_shipping = ndb.BooleanProperty('10', default=True)
    default_billing = ndb.BooleanProperty('11', default=True)

# bice potrebna verovatno i aggregate tabela neka
class BuyerCollection(ndb.Model):
    
    # ancestor User
    # kad budemo skontali querije i indexe onda mozda ovde ubacimo store i product_categories propertije
    name = ndb.StringProperty('1', required=True)
    notifications = ndb.BooleanProperty('2', default=False)


class BuyerCollectionStore(ndb.Model):
    
    # ancestor BuyerCollection
    store = ndb.KeyProperty('1', kind=Store, required=True)


class BuyerCollectionProductCategory(ndb.Model):
    
    # ancestor BuyerCollection
    product_categories = ndb.KeyProperty('1', kind=ProductCategory, required=True)


class Currency(ndb.Model):
    
    # root
    name = ndb.StringProperty(required=True)
    symbol = ndb.StringProperty(required=True)
    code = ndb.StringProperty(required=True)
    numeric_code = ndb.StringProperty(required=True)
    rounding = ndb.FloatProperty(required=True) # ili StringProperty, sta je vec bolje
    digits = ndb.IntegerProperty(required=True)
    active = ndb.BooleanProperty(default=True)
    grouping = ndb.StringProperty(required=True)
    decimal_separator = ndb.StringProperty(required=True)
    thousands_separator = ndb.StringProperty(required=True)
    positive_sign_position = ndb.IntegerProperty(required=True)
    negative_sign_position = ndb.IntegerProperty(required=True)
    positive_sign = ndb.StringProperty(required=True)
    negative_sign = ndb.StringProperty(required=True)
    positive_currency_symbol_precedes = ndb.BooleanProperty(default=True, required=True)
    negative_currency_symbol_precedes = ndb.BooleanProperty(default=True, required=True)
    positive_separate_by_space = ndb.BooleanProperty(default=True, required=True)
    negative_separate_by_space = ndb.BooleanProperty(default=True, required=True)


class Order(ndb.Model):
    
    reference = ndb.StringProperty(required=True)
    order_date = ndb.DateTimeProperty(auto_now_add=True, required=True)
    company_address = ndb.KeyProperty(OrderAddress, collection_name='company_addresses', required=True)# videcemo hocemo li ovako ili cemo iz OrderAddress samo reference uzimati
    invoice_address = ndb.KeyProperty(OrderAddress, collection_name='invoice_addresses', required=True)# videcemo hocemo li ovako ili cemo iz OrderAddress samo reference uzimati
    shipping_address = ndb.KeyProperty(OrderAddress, collection_name='shipping_addresses', required=True)# videcemo hocemo li ovako ili cemo iz OrderAddress samo reference uzimati
    currency = ndb.KeyProperty(Currency, collection_name='currencies', required=True)
    untaxed_amount = ndb.FloatProperty(required=True) # ili StringProperty, sta je vec bolje
    tax_amount = ndb.FloatProperty(required=True) # ili StringProperty, sta je vec bolje
    total_amount = ndb.FloatProperty(required=True) # ili StringProperty, sta je vec bolje
    comment = ndb.TextProperty()
    state = ndb.IntegerProperty(required=True)


class OrderRefenrece(ndb.Model):
    
    order = ndb.KeyProperty(Order, collection_name='orders', required=True)
    store_carrier = ndb.KeyProperty(StoreCarrier, collection_name='store_carriers', required=True)


class OrderAddress(ndb.Model):
    
    order = ndb.KeyProperty(Order, collection_name='orders', required=True)
    country = ndb.StringProperty(required=True)
    country_code = ndb.StringProperty(required=True)
    region = ndb.StringProperty(required=True)
    city = ndb.StringProperty(required=True)
    postal_code = ndb.StringProperty(required=True)
    street_address = ndb.StringProperty(required=True)
    street_address2 = ndb.StringProperty(required=True)
    name = ndb.StringProperty(required=True)
    email = ndb.EmailProperty()
    telephone = ndb.PhoneNumberProperty() # ne znam kakva se korist moze imati od PostalAddressProperty
    type = ndb.IntegerProperty(required=True)


class OrderAddressRefenrece(ndb.Model):
    
    order = ndb.KeyProperty(Order, collection_name='orders', required=True)
    buyer_address = ndb.KeyProperty(BuyerAddress, collection_name='buyer_addresses', required=True)
    type = ndb.IntegerProperty(required=True)


class OrderLine(ndb.Model):
    
    order = ndb.KeyProperty(Order, collection_name='orders', required=True)
    description = ndb.TextProperty(required=True)
    quantity = ndb.FloatProperty(required=True) # ili StringProperty, sta je vec bolje
    product_uom = ndb.KeyProperty(ProductUOM, collection_name='product_uoms', required=True)
    unit_price = ndb.FloatProperty(required=True) # ili StringProperty, sta je vec bolje
    discount = ndb.FloatProperty(required=True) # ili StringProperty, sta je vec bolje
    sequence = ndb.IntegerProperty(required=True)


class OrderLineTax(ndb.Model):
    
    order_line = ndb.KeyProperty(OrderLine, collection_name='order_lines', required=True)
    name = ndb.StringProperty(required=True)
    sequence = ndb.IntegerProperty(required=True)
    type = ndb.IntegerProperty(required=True)
    amount = ndb.FloatProperty(required=True) # ili StringProperty, sta je vec bolje - obratiti paznju oko decimala posto ovo moze da bude i currency i procenat.


class OrderLineRefenrece(ndb.Model):
    
    order_line = ndb.KeyProperty(OrderLine, collection_name='order_lines', required=True)
    product_category = ndb.KeyProperty(ProductCategory, collection_name='product_categories', required=True)
    catalog_pricetag = ndb.KeyProperty(CatalogPricetag, collection_name='catalog_pricetags', required=True)
    catalog_product_instance = ndb.KeyProperty(CatalogProductInstance, collection_name='catalog_product_instances', required=True)


class OrderLineTaxRefenrece(ndb.Model):
    
    order_line = ndb.KeyProperty(OrderLine, collection_name='order_lines', required=True)
    store_tax = ndb.KeyProperty(StoreTax, collection_name='store_taxes', required=True)


class PayPalTransaction(ndb.Model):
    
    order = ndb.KeyProperty(Order, collection_name='orders', required=True)
    txn_id = ndb.StringProperty(required=True)
    ipn_message = ndb.TextProperty(required=True)
    logged = ndb.DateTimeProperty(auto_now_add=True, required=True)


class BillingLog(ndb.Model):
    
    store = ndb.KeyProperty(Store, collection_name='stores', required=True)
    logged = ndb.DateTimeProperty(auto_now_add=True, required=True)
    reference = ndb.KeyProperty(None, collection_name='references', required=True)# ne znam da li treba i uvesti reference_type?
    amount = ndb.FloatProperty(required=True) # ili StringProperty, sta je vec bolje
    balance = ndb.FloatProperty(required=True) # ili StringProperty, sta je vec bolje


class BillingCreditAdjustment(ndb.Model):
    
    store = ndb.KeyProperty(Store, collection_name='stores', required=True)
    agent = ndb.KeyProperty(User, collection_name='agents', required=True)
    adjusted = ndb.DateTimeProperty(auto_now_add=True, required=True)
    amount = ndb.FloatProperty(required=True) # ili StringProperty, sta je vec bolje
    message = ndb.TextProperty(required=True)
    note = ndb.TextProperty(required=True)


class StoreBuyerOrderFeedback(ndb.Model):
    
    store = ndb.KeyProperty(Store, collection_name='stores', required=True)
    store_name = ndb.StringProperty(required=True)
    buyer = ndb.KeyProperty(User, collection_name='buyers', required=True)
    order = ndb.KeyProperty(Order, collection_name='orders', required=True)
    state = ndb.IntegerProperty(required=True)


class Catalog(ndb.Model):
    
    # root
    store = ndb.KeyProperty('1', kind=Store, required=True)
    name = ndb.StringProperty('2', required=True)
    publish = ndb.DateTimeProperty('3', required=True)# trebaju se definisati granice i rasponi, i postaviti neke default vrednosti
    discontinue = ndb.DateTimeProperty('4', required=True)
    cover = blobstore.BlobKeyProperty('5', required=True)# verovatno je i dalje ovaj property od klase blobstore
    cost = ndb.FloatProperty('6', required=True)# ovde ide custom decimal property
    state = ndb.IntegerProperty('7', required=True)


class CatalogContent(ndb.Model):
    
    # ancestor Catalog
    title = ndb.StringProperty('1', required=True)
    body = ndb.TextProperty('2', required=True)


class CatalogPricetag(ndb.Model):
    
    # ancestor Catalog
    product_template = ndb.KeyProperty('1', kind=ProductTemplate, required=True)
    container_image = blobstore.BlobKeyProperty('2', required=True)# verovatno je i dalje ovaj property od klase blobstore
    source_width = ndb.FloatProperty('3', required=True)
    source_height = ndb.FloatProperty('4', required=True)
    source_position_top = ndb.FloatProperty('5', required=True)
    source_position_left = ndb.FloatProperty('6', required=True)
    value = ndb.StringProperty('7', required=True)


class ProductTemplate(ndb.Expando):
    
    # ancestor Catalog
    product_category = ndb.KeyProperty('1', kind=ProductCategory, required=True)
    name = ndb.StringProperty('2', required=True)
    description = ndb.TextProperty('3', required=True)# limit na 10000 karaktera - We recommend that you submit around 500 to 1,000 characters, but you can submit up to 10,000 characters.
    product_uom = ndb.KeyProperty('4', kind=ProductUOM, required=True)
    unit_price = ndb.FloatProperty('5', required=True) # custom decimal property
    active = ndb.BooleanProperty('6', default=True)
    #Expando
    #weight = ndb.FloatProperty('7')# custom decimal
    #weight_uom = ndb.KeyProperty('8', kind=ProductUOM, required=True)# filtrirano po ProductUOMCategory Weight
    #volume = ndb.FloatProperty('9')# custom decimal
    #volume_uom = ndb.KeyProperty('10', kind=ProductUOM, required=True)# filtrirano po ProductUOMCategory Volume


class ProductInstance(ndb.Expando):
    
    # ancestor ProductTemplate
    code = ndb.StringProperty('1', required=True)
    active = ndb.BooleanProperty('2', default=True)
    #Expando
    #description = ndb.TextProperty('3', required=True)
    #unit_price = ndb.FloatProperty('4', required=True) # custom decimal property
    #managed_stock = ndb.BooleanProperty('5', default=False)
    #low_stock_notify = ndb.BooleanProperty('6', default=True)
    #low_stock_quantity = ndb.FloatProperty('7', default=0.00)# custom decimal
    #weight = ndb.FloatProperty('8')# custom decimal
    #weight_uom = ndb.KeyProperty('9', kind=ProductUOM, required=True)# filtrirano po ProductUOMCategory Weight
    #volume = ndb.FloatProperty('10')# custom decimal
    #volume_uom = ndb.KeyProperty('11', kind=ProductUOM, required=True)# filtrirano po ProductUOMCategory Volume


class ProductInstanceInventory(ndb.Model):
    
    # ancestor ProductInstance
    updated = ndb.DateTimeProperty('1', auto_now_add=True, required=True)
    # ? reference = ndb.KeyProperty(None, collection_name='references')
    quantity = ndb.FloatProperty('3', required=True)# custom decimal
    balance = ndb.FloatProperty('4', required=True)# custom decimal


class ProductContent(ndb.Model):
    
    # ancestor ProductTemplate, ProductInstance
    catalog_content = ndb.KeyProperty('1', kind=CatalogContent, required=True)
    sequence = ndb.IntegerProperty('2', required=True)


class ProductVariant(ndb.Model):
    
    #ancestor Catalog
    name = ndb.StringProperty(required=True)
    description = ndb.TextProperty()
    options = ndb.StringProperty(repeated=True)
    allow_custom_value = ndb.BooleanProperty(default=False)
    mandatory_variant_type = ndb.BooleanProperty(default=True)


class ProductTemplateVariant(ndb.Model):
    
    # splice
    product_template = ndb.KeyProperty('1', kind=ProductTemplate, required=True)
    product_variant = ndb.KeyProperty('2', kind=ProductVariant, required=True)
    sequence = ndb.IntegerProperty('3', required=True)


class CatalogProductVariantValue(ndb.Model):
    
    catalog_product_template = ndb.KeyProperty(CatalogProductTemplate, collection_name='catalog_product_templates', required=True)
    catalog_product_varinat_type = ndb.KeyProperty(CatalogProductVariantType, collection_name='catalog_product_varinat_types', required=True)
    catalog_product_varinat_option = ndb.KeyProperty(CatalogProductVariantOption, collection_name='catalog_product_varinat_options', required=True)


class CatalogProductInstanceProductVariantValue(ndb.Model):
    
    catalog_product_varinat_value = ndb.KeyProperty(CatalogProductVariantValue, collection_name='catalog_product_varinat_values', required=True)
    catalog_product_instance = ndb.KeyProperty(CatalogProductInstance, collection_name='catalog_product_instances', required=True)


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