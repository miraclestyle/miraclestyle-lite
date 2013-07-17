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
    
    reference = ndb.KeyProperty('1',required=True)# collection_name is the name of the property to give to the referenced model class. The value of the property is a Query for all entities that reference the entity.
    type = ndb.IntegerProperty('2', required=True)# mozda nam bude trebalo name polje u koje ce se kopirati name objekta ili njegov key (ako nema name)
    agent = ndb.KeyProperty('3', kind=User, required=True)
    logged = ndb.DateTimeProperty('4', auto_now_add=True, required=True)
    event = ndb.IntegerProperty('5', required=True)
    state = ndb.IntegerProperty('6', required=True)
    message = ndb.TextProperty('7', required=True)
    note = ndb.TextProperty('8', required=True)
    log = ndb.TextProperty('9', required=True)


class Notification(ndb.Model):
    
    creator = ndb.KeyProperty('1', kind=User, required=True)
    created = ndb.DateTimeProperty('2', auto_now_add=True, required=True)
    message = ndb.TextProperty('3', required=True)


class NotificationRecipient(ndb.Model):
    
    notification = ndb.KeyProperty('1', kind=Notification, required=True)
    recipient = ndb.KeyProperty('2', kind=User, required=True)


class NotificationRecipientOutlet(ndb.Model):
    
    notification_recepient = ndb.KeyProperty('1', kind=NotificationRecipient, required=True)
    outlet = ndb.IntegerProperty('2', required=True)
    notified = ndb.DateTimeProperty('3')# jos ne znamo hocemo li ovde upisivati datum, ili cemo ovo pretvoriti u boolean polje, ili expandirati ovaj model...


class FeedbackRequest(ndb.Model):
    
    reference = ndb.StringProperty('1', required=True)
    state = ndb.IntegerProperty('2', required=True)


class SupportRequest(ndb.Model):
    
    reference = ndb.StringProperty('1', required=True)
    state = ndb.IntegerProperty('2', required=True)


class Content(ndb.Model):
    
    title = ndb.StringProperty('1', required=True)
    category = ndb.IntegerProperty('2', required=True)
    published = ndb.BooleanProperty('3', required=True)
    active_revision = ndb.KeyProperty('4', kind=ContentRevision, required=True)
    sequence = ndb.IntegerProperty('5', required=True)


class ContentRevision(ndb.Model):
    
    content = ndb.KeyProperty('1', kind=Content, required=True)
    body = ndb.TextProperty('2', required=True)
    created = ndb.DateTimeProperty('3', auto_now_add=True, required=True)


class Country(ndb.Model):
    
    name = ndb.StringProperty('1', required=True)
    code = ndb.StringProperty('2', required=True)


class CountrySubdivision(ndb.Model):
    
    parent_record = ndb.KeyProperty('1', kind=CountrySubdivision)# ne znam da li record moze referencirati samog sebe, ako moze onda se treba ukljuciti required=True
    country = ndb.KeyProperty('2', kind=Country, required=True)
    name = ndb.StringProperty('3', required=True)
    code = ndb.StringProperty('4', required=True)
    type = ndb.IntegerProperty('5', required=True)


class ProductCategory(ndb.Model):
    
    parent_record = ndb.KeyProperty('1', kind=ProductCategory)# ne znam da li record moze referencirati samog sebe, ako moze onda se treba ukljuciti required=True
    name = ndb.StringProperty('2', required=True)
    sequence = ndb.IntegerProperty('3', required=True)
    state = ndb.IntegerProperty('4', required=True)


class ProductUOMCategory(ndb.Model):
    
    name = ndb.StringProperty('1', required=True)


class ProductUOM(ndb.Model):
    
    name = ndb.StringProperty('1', required=True)
    symbol = ndb.StringProperty('2', required=True)
    product_uom_category = ndb.KeyProperty('3', kind=ProductUOMCategory, required=True)# ovo bi mozda moglo da bude CategoryProperty, i da se time izbaci ProductUOMCategory model??
    rate = ndb.FloatProperty('4', required=True)# ovde ide custom decimal property
    factor = ndb.FloatProperty('5', required=True)# ovde ide custom decimal property
    rounding = ndb.FloatProperty('6', required=True)# ovde ide custom decimal property
    display_digits = ndb.IntegerProperty('7', required=True)
    active = ndb.BooleanProperty('8', required=True)


class User(ndb.Model):
    
    state = ndb.IntegerProperty('1', required=True)


class UserConfig(ndb.Model):
    
    user = ndb.KeyProperty('1', kind=User, required=True)
    attribute = ndb.StringProperty('2', required=True)
    attribute_value = ndb.TextProperty('3', required=True)


class UserEmail(ndb.Model):
    
    user = ndb.KeyProperty('1', kind=User, required=True)
    email = ndb.StringProperty('2', required=True)
    primary = ndb.BooleanProperty('3', required=True)


class UserIdentity(ndb.Model):
    
    user = ndb.KeyProperty('1', kind=User, required=True)
    user_email = ndb.KeyProperty('2', kind=UserEmail, required=True)
    identity = ndb.StringProperty('3', required=True)
    provider = ndb.StringProperty('4', required=True)
    associated = ndb.BooleanProperty('5', required=True)


class UserIPAddress(ndb.Model):
    
    user = ndb.KeyProperty('1', kind=User, required=True)
    ip_address = ndb.StringProperty('2', required=True)
    logged = ndb.DateTimeProperty('3', auto_now_add=True, required=True)


class UserRole(ndb.Model):
    
    user = ndb.KeyProperty('1', kind=User, required=True)
    role = ndb.KeyProperty('2', kind=Role, required=True)


# ovo je pojednostavljena verzija permisija, ispod ovog modela je skalabilna verzija koja se moze prilagoditi i upotrebiti umesto ove 
class Role(ndb.Model):
    
    reference = ndb.KeyProperty('1',required=True)# ovde se za sada cuva key store-a kojem pripada ova rola
    name = ndb.StringProperty('2', required=True)
    permissions = ndb.StringProperty('3', repeated=True)
    readonly = ndb.BooleanProperty('4', required=True)


'''
Primer skalabilne verzije implementacije permission sistema
class Role(ndb.Model):
    
    app = ndb.KeyProperty('1', kind=app, required=True)# ovde se cuva key aplikacije (user space-a) kojoj pripada ova rola
    name = ndb.StringProperty('2', required=True)
    permissions = ndb.StructuredProperty(Permission, '3', repeated=True)
    readonly = ndb.BooleanProperty('4', required=True)


class Permission(ndb.Model):
    
    reference = ndb.KeyProperty('1',required=True)# ovde se cuva key objekta na kojeg se permisije odnose kojem pripada ova rola
    permissions = ndb.StringProperty('2', repeated=True)
'''

# ovo je agregaciona tabela radi optimizacije
class AggregateUserPermissions(ndb.Model):
    
    user = ndb.KeyProperty('1', kind=User, required=True)
    reference = ndb.KeyProperty('2',required=True)
    permissions = ndb.StringProperty('3', repeated=True)


class Store(ndb.Model):#mozda ce trebati agregate tabela za roles tab
    
    name = ndb.StringProperty(required=True)
    logo = blobstore.BlobKeyProperty()
    state = ndb.IntegerProperty(required=True)


class StoreConfig(ndb.Model):
    
    store = ndb.KeyProperty(Store, collection_name='stores', required=True)
    key_value = ndb.StringProperty(required=True)
    data = ndb.TextProperty(required=True) # ne znam da li bi i ovde trebalo nesto drugo umesto TextProperty


class StoreContent(ndb.Model):
    
    store = ndb.KeyProperty(Store, collection_name='stores', required=True)
    title = ndb.StringProperty(required=True)
    body = ndb.TextProperty(required=True)
    sequence = ndb.IntegerProperty(required=True)


class StoreShippingExclusion(ndb.Model):
    
    store = ndb.KeyProperty(Store, collection_name='stores', required=True)
    country = ndb.KeyProperty(Country, collection_name='countries')
    region = ndb.KeyProperty(CountrySubdivision, collection_name='regions')
    city = ndb.KeyProperty(CountrySubdivision, collection_name='cities') # ne znam da li ce ovo postojati??
    postal_code_from = ndb.StringProperty(multiline=False)
    postal_code_to = ndb.StringProperty(multiline=False)


class StoreTax(ndb.Model):
    
    store = ndb.KeyProperty(Store, collection_name='stores', required=True)
    name = ndb.StringProperty(required=True)
    sequence = ndb.IntegerProperty(required=True)
    type = ndb.IntegerProperty(required=True)
    amount = ndb.FloatProperty(required=True) # ili StringProperty, sta je vec bolje - obratiti paznju oko decimala posto ovo moze da bude i currency i procenat.
    location_exclusion = ndb.BooleanProperty(default=True, required=True)
    active = ndb.BooleanProperty(default=True, required=True)


class StoreTaxLocation(ndb.Model):
    
    store_tax = ndb.KeyProperty(StoreTax, collection_name='store_taxes', required=True)
    country = ndb.KeyProperty(Country, collection_name='countries')
    region = ndb.KeyProperty(CountrySubdivision, collection_name='regions')
    city = ndb.KeyProperty(CountrySubdivision, collection_name='cities') # ne znam da li ce ovo postojati??
    postal_code_from = ndb.StringProperty(multiline=False)
    postal_code_to = ndb.StringProperty(multiline=False)


class StoreTaxApplication(ndb.Model):
    
    store_tax = ndb.KeyProperty(StoreTax, collection_name='store_taxes', required=True)
    application = ndb.IntegerProperty(required=True)
    product_category = ndb.KeyProperty(ProductCategory, collection_name='product_categories')
    store_carrier = ndb.KeyProperty(StoreCarrier, collection_name='store_carriers')


class StoreCarrier(ndb.Model):
    
    store = ndb.KeyProperty(Store, collection_name='stores', required=True)
    name = ndb.StringProperty(required=True)
    active = ndb.BooleanProperty(default=True, required=True)


class StoreCarrierLine(ndb.Model):
    
    store_carrier = ndb.KeyProperty(StoreCarrier, collection_name='store_carriers', required=True)
    name = ndb.StringProperty(required=True)
    sequence = ndb.IntegerProperty(required=True)
    location_exclusion = ndb.BooleanProperty(default=True, required=True)
    active = ndb.BooleanProperty(default=True, required=True)


class StoreCarrierLineLocation(ndb.Model):
    
    store_carrier_line = ndb.KeyProperty(StoreCarrierLine, collection_name='store_carrier_lines', required=True)
    country = ndb.KeyProperty(Country, collection_name='countries')
    region = ndb.KeyProperty(CountrySubdivision, collection_name='regions')
    city = ndb.KeyProperty(CountrySubdivision, collection_name='cities') # ne znam da li ce ovo postojati??
    postal_code_from = ndb.StringProperty(multiline=False)
    postal_code_to = ndb.StringProperty(multiline=False)


class StoreCarrierLinePricelist(ndb.Model):
    
    store_carrier_line = ndb.KeyProperty(StoreCarrierLine, collection_name='store_carrier_lines', required=True)
    condition_type = ndb.IntegerProperty(required=True)
    condition_operator = ndb.IntegerProperty(required=True)
    condition_value = ndb.IntegerProperty(required=True)# verovatno da ce trebati i ovde product_uom_id kako bi prodavac mogao da ustima vrednost koju zeli... mozemo ici i na to da je uom fiksan ovde, a isto tako i fiksan u product measurements-ima...
    price_type = ndb.IntegerProperty(required=True)
    price_type_factor = ndb.IntegerProperty(required=True)
    amount = ndb.FloatProperty(required=True) # ili StringProperty, sta je vec bolje


class BuyerAddress(ndb.Model):
    
    user = ndb.KeyProperty(User, collection_name='users', required=True)
    name = ndb.StringProperty(required=True)
    country = ndb.KeyProperty(Country, collection_name='countries', required=True)
    region = ndb.KeyProperty(CountrySubdivision, collection_name='regions', required=True)
    city = ndb.KeyProperty(CountrySubdivision, collection_name='cities', required=True)
    postal_code = ndb.StringProperty(required=True)
    street_address = ndb.StringProperty(required=True)
    street_address2 = ndb.StringProperty(required=True)
    email = ndb.EmailProperty()
    telephone = ndb.PhoneNumberProperty() # ne znam kakva se korist moze imati od PostalAddressProperty 
    default_shipping = ndb.BooleanProperty(default=True, required=True)
    default_billing = ndb.BooleanProperty(default=True, required=True)


class BuyerCollection(ndb.Model):# za buyer collection tablee treba agregate tablea za filtriranje kataloga
    
    user = ndb.KeyProperty(User, collection_name='users', required=True)
    name = ndb.StringProperty(required=True)
    notifications = ndb.BooleanProperty(default=True, required=True)


class BuyerCollectionStore(ndb.Model):
    
    buyer_collection = ndb.KeyProperty(BuyerCollection, collection_name='buyer_collections', required=True)
    store = ndb.KeyProperty(Store, collection_name='stores', required=True)


class BuyerCollectionProductCategory(ndb.Model):
    
    buyer_collection = ndb.KeyProperty(BuyerCollection, collection_name='buyer_collections', required=True)
    product_category = ndb.KeyProperty(ProductCategory, collection_name='product_categories', required=True)


class Currency(ndb.Model):
    
    name = ndb.StringProperty(required=True)
    symbol = ndb.StringProperty(required=True)
    code = ndb.StringProperty(required=True)
    numeric_code = ndb.StringProperty(required=True)
    rounding = ndb.FloatProperty(required=True) # ili StringProperty, sta je vec bolje
    digits = ndb.IntegerProperty(required=True)
    active = ndb.BooleanProperty(default=True, required=True)
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
    
    store = ndb.KeyProperty(Store, collection_name='stores', required=True)
    name = ndb.StringProperty(required=True)
    publish = ndb.DateTimeProperty(required=True)# trebaju se definisati granice i rasponi, i postaviti neke default vrednosti
    discontinue = ndb.DateTimeProperty(required=True)
    cover = blobstore.BlobKeyProperty()
    cost = ndb.FloatProperty(required=True) # ili StringProperty, sta je vec bolje
    state = ndb.IntegerProperty(required=True)


class CatalogImage(ndb.Model):
    
    catalog = ndb.KeyProperty(Catalog, collection_name='catalogs', required=True)
    image = blobstore.BlobKeyProperty()
    sequence = ndb.IntegerProperty(required=True)


class CatalogStoreContent(ndb.Model):
    
    catalog = ndb.KeyProperty(Catalog, collection_name='catalogs', required=True)
    store = ndb.KeyProperty(Store, collection_name='stores', required=True)
    title = ndb.StringProperty(required=True)
    body = ndb.TextProperty(required=True)
    sequence = ndb.IntegerProperty(required=True)


class CatalogStoreShippingExclusion(ndb.Model):
    
    catalog = ndb.KeyProperty(Catalog, collection_name='catalogs', required=True)
    store = ndb.KeyProperty(Store, collection_name='stores', required=True)
    country = ndb.KeyProperty(Country, collection_name='countries')
    region = ndb.KeyProperty(CountrySubdivision, collection_name='regions')
    city = ndb.KeyProperty(CountrySubdivision, collection_name='cities') # ne znam da li ce ovo postojati??
    postal_code_from = ndb.StringProperty(multiline=False)
    postal_code_to = ndb.StringProperty(multiline=False)


class CatalogPricetag(ndb.Model):
    
    catalog = ndb.KeyProperty(Catalog, collection_name='catalogs', required=True)
    catalog_product_template = ndb.KeyProperty(CatalogProductTemplate, collection_name='catalog_product_templates', required=True)
    catalog_image = ndb.KeyProperty(CatalogImage, collection_name='catalog_images', required=True)
    source_width = ndb.FloatProperty(required=True)
    source_height = ndb.FloatProperty(required=True)
    source_position_top = ndb.FloatProperty(required=True)
    source_position_left = ndb.FloatProperty(required=True)
    pricetag_value = ndb.StringProperty(multiline=False)


class CatalogProductTemplate(ndb.Model):
    
    catalog = ndb.KeyProperty(Catalog, collection_name='catalogs', required=True)
    product_category = ndb.KeyProperty(ProductCategory, collection_name='product_categories', required=True)
    name = ndb.StringProperty(required=True)
    description = ndb.TextProperty(required=True)
    product_uom = ndb.KeyProperty(ProductUOM, collection_name='product_uoms', required=True)
    unit_price = ndb.FloatProperty(required=True) # ili StringProperty, sta je vec bolje
    active = ndb.BooleanProperty(default=True, required=True)


class CatalogProductVariantType(ndb.Model):
    
    catalog = ndb.KeyProperty(Catalog, collection_name='catalogs', required=True)
    name = ndb.StringProperty(required=True)
    description = ndb.TextProperty()
    allow_custom_value = ndb.BooleanProperty(default=False, required=True)
    mandatory_variant_type = ndb.BooleanProperty(default=True, required=True)


class CatalogProductVariantOption(ndb.Model):
    
    catalog_product_varinat_type = ndb.KeyProperty(CatalogProductVariantType, collection_name='catalog_product_varinat_types', required=True)
    name = ndb.StringProperty(required=True)
    sequence = ndb.IntegerProperty(required=True)


class CatalogProductTemplateProductVariantType(ndb.Model):
    
    catalog_product_template = ndb.KeyProperty(CatalogProductTemplate, collection_name='catalog_product_templates', required=True)
    catalog_product_varinat_type = ndb.KeyProperty(CatalogProductVariantType, collection_name='catalog_product_varinat_types', required=True)
    sequence = ndb.IntegerProperty(required=True)


class CatalogProductVariantValue(ndb.Model):
    
    catalog_product_template = ndb.KeyProperty(CatalogProductTemplate, collection_name='catalog_product_templates', required=True)
    catalog_product_varinat_type = ndb.KeyProperty(CatalogProductVariantType, collection_name='catalog_product_varinat_types', required=True)
    catalog_product_varinat_option = ndb.KeyProperty(CatalogProductVariantOption, collection_name='catalog_product_varinat_options', required=True)


class CatalogProductInstanceProductVariantValue(ndb.Model):
    
    catalog_product_varinat_value = ndb.KeyProperty(CatalogProductVariantValue, collection_name='catalog_product_varinat_values', required=True)
    catalog_product_instance = ndb.KeyProperty(CatalogProductInstance, collection_name='catalog_product_instances', required=True)


class CatalogProductInstance(ndb.Model):
    
    catalog_product_template = ndb.KeyProperty(CatalogProductTemplate, collection_name='catalog_product_templates', required=True)
    code = ndb.StringProperty(required=True)
    description = ndb.TextProperty()
    unit_price = ndb.FloatProperty() # ili StringProperty, sta je vec bolje    
    active = ndb.BooleanProperty(default=True, required=True)


class CatalogProductInstanceStock(ndb.Model):
    
    catalog_product_instance = ndb.KeyProperty(CatalogProductInstance, collection_name='catalog_product_instances', required=True)
    type = ndb.IntegerProperty(required=True)
    low_stock_notify = ndb.BooleanProperty(default=True, required=True)
    low_stock_quantity = ndb.FloatProperty() # ili StringProperty, sta je vec bolje


class CatalogProductInstanceInventory(ndb.Model):
    
    catalog_product_instance = ndb.KeyProperty(CatalogProductInstance, collection_name='catalog_product_instances', required=True)
    updated = ndb.DateTimeProperty(required=True)
    reference = ndb.KeyProperty(None, collection_name='references')
    quantity = ndb.FloatProperty() # ili StringProperty, sta je vec bolje
    balance = ndb.FloatProperty() # ili StringProperty, sta je vec bolje


class CatalogProductImage(ndb.Model):
    
    reference = ndb.KeyProperty(None, collection_name='references', required=True)
    image = blobstore.BlobKeyProperty()
    sequence = ndb.IntegerProperty(required=True)


class CatalogProductContent(ndb.Model):
    
    catalog = ndb.KeyProperty(Catalog, collection_name='catalogs', required=True)
    title = ndb.StringProperty(required=True)
    body = ndb.TextProperty(required=True)


class CatalogProductProductContent(ndb.Model):
    
    reference = ndb.KeyProperty(None, collection_name='references', required=True)
    catalog_product_content = ndb.KeyProperty(CatalogProductContent, collection_name='catalog_product_contents', required=True)
    sequence = ndb.IntegerProperty(required=True)

class CatalogProductMeasurements(ndb.Model):
    
    reference = ndb.KeyProperty(None, collection_name='references', required=True)
    weight = ndb.FloatProperty() # ili StringProperty, sta je vec bolje
    weight_uom = ndb.KeyProperty(ProductUOM, collection_name='weight_uoms', required=True)
    volume = ndb.FloatProperty() # ili StringProperty, sta je vec bolje
    volume_uom = ndb.KeyProperty(ProductUOM, collection_name='volume_uoms', required=True)



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