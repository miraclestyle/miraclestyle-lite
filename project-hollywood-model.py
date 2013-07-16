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
    
    reference = db.ReferenceProperty(None, collection_name='references', required=True)# mozda nam bude trebalo name polje u koje ce se kopirati name objekta ili njegov key (ako nema name), i mozda nam bude trebao reference type da bi znali o cemu se radi...
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
    
    parent_record = db.SelfReferenceProperty(collection_name='parent_records', required=True) # ovo je valjda ok
    country = db.ReferenceProperty(Country, collection_name='countries')
    name = db.StringProperty(multiline=False, required=True)
    code = db.StringProperty(multiline=False, required=True)
    category = db.CategoryProperty(required=True) # ovde bi mogao i IntegerProperty, sta je vec bolje od to dvoje


class ProductCategory(db.Model):
    
    parent_record = db.SelfReferenceProperty(collection_name='parent_records', required=True) # ovo je valjda ok
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
    display_digits = db.IntegerProperty(required=True)
    active = db.BooleanProperty(default=False, required=True)


class User(db.Model):
    
    state = db.IntegerProperty(required=True)


class UserConfig(db.Model):
    
    user = db.ReferenceProperty(User, collection_name='users', required=True)
    key_value = db.StringProperty(multiline=False, required=True)
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
    reference = db.ReferenceProperty(None, collection_name='references', required=True)
    permissions = db.StringListProperty()# mozda da ovo bude samo StringProperty i da nosi jednu vrednost?


class AgregateUserStorePermissions(db.Model):# mislim da bi se moglo ovako uraditi, ili da se jos bolje resi
    
    user = db.ReferenceProperty(User, collection_name='users', required=True)
    store = db.ReferenceProperty(Store, collection_name='stores', required=True)
    permissions = db.StringListProperty()# mozda da ovo bude samo StringProperty i da nosi jednu vrednost?


class Store(db.Model):#mozda ce trebati agregate tabela za roles tab
    
    name = db.StringProperty(multiline=False, required=True)
    logo = blobstore.BlobReferenceProperty()
    state = db.IntegerProperty(required=True)


class StoreConfig(db.Model):
    
    store = db.ReferenceProperty(Store, collection_name='stores', required=True)
    key_value = db.StringProperty(multiline=False, required=True)
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
    postal_code_from = db.StringProperty(multiline=False)
    postal_code_to = db.StringProperty(multiline=False)


class StoreTax(db.Model):
    
    store = db.ReferenceProperty(Store, collection_name='stores', required=True)
    name = db.StringProperty(multiline=False, required=True)
    sequence = db.IntegerProperty(required=True)
    tax_type = db.IntegerProperty(required=True)# ne mogu da koristim samo type posto je python keyword
    amount = db.FloatProperty(required=True) # ili StringProperty, sta je vec bolje - obratiti paznju oko decimala posto ovo moze da bude i currency i procenat.
    location_exclusion = db.BooleanProperty(default=True, required=True)
    active = db.BooleanProperty(default=True, required=True)


class StoreTaxLocation(db.Model):
    
    store_tax = db.ReferenceProperty(StoreTax, collection_name='store_taxes', required=True)
    country = db.ReferenceProperty(Country, collection_name='countries')
    region = db.ReferenceProperty(CountrySubdivision, collection_name='regions')
    city = db.ReferenceProperty(CountrySubdivision, collection_name='cities') # ne znam da li ce ovo postojati??
    postal_code_from = db.StringProperty(multiline=False)
    postal_code_to = db.StringProperty(multiline=False)


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
    postal_code_from = db.StringProperty(multiline=False)
    postal_code_to = db.StringProperty(multiline=False)


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
    country = db.ReferenceProperty(Country, collection_name='countries', required=True)
    region = db.ReferenceProperty(CountrySubdivision, collection_name='regions', required=True)
    city = db.ReferenceProperty(CountrySubdivision, collection_name='cities', required=True)
    postal_code = db.StringProperty(multiline=False, required=True)
    street_address = db.StringProperty(multiline=False, required=True)
    street_address2 = db.StringProperty(multiline=False, required=True)
    email = db.EmailProperty()
    telephone = db.PhoneNumberProperty() # ne znam kakva se korist moze imati od PostalAddressProperty 
    default_shipping = db.BooleanProperty(default=True, required=True)
    default_billing = db.BooleanProperty(default=True, required=True)


class BuyerCollection(db.Model):# za buyer collection tablee treba agregate tablea za filtriranje kataloga
    
    user = db.ReferenceProperty(User, collection_name='users', required=True)
    name = db.StringProperty(multiline=False, required=True)
    notifications = db.BooleanProperty(default=True, required=True)


class BuyerCollectionStore(db.Model):
    
    buyer_collection = db.ReferenceProperty(BuyerCollection, collection_name='buyer_collections', required=True)
    store = db.ReferenceProperty(Store, collection_name='stores', required=True)


class BuyerCollectionProductCategory(db.Model):
    
    buyer_collection = db.ReferenceProperty(BuyerCollection, collection_name='buyer_collections', required=True)
    product_category = db.ReferenceProperty(ProductCategory, collection_name='product_categories', required=True)


class Currency(db.Model):
    
    name = db.StringProperty(multiline=False, required=True)
    symbol = db.StringProperty(multiline=False, required=True)
    code = db.StringProperty(multiline=False, required=True)
    numeric_code = db.StringProperty(multiline=False, required=True)
    rounding = db.FloatProperty(required=True) # ili StringProperty, sta je vec bolje
    digits = db.IntegerProperty(required=True)
    active = db.BooleanProperty(default=True, required=True)
    grouping = db.StringProperty(multiline=False, required=True)
    decimal_separator = db.StringProperty(multiline=False, required=True)
    thousands_separator = db.StringProperty(multiline=False, required=True)
    positive_sign_position = db.IntegerProperty(required=True)
    negative_sign_position = db.IntegerProperty(required=True)
    positive_sign = db.StringProperty(multiline=False, required=True)
    negative_sign = db.StringProperty(multiline=False, required=True)
    positive_currency_symbol_precedes = db.BooleanProperty(default=True, required=True)
    negative_currency_symbol_precedes = db.BooleanProperty(default=True, required=True)
    positive_separate_by_space = db.BooleanProperty(default=True, required=True)
    negative_separate_by_space = db.BooleanProperty(default=True, required=True)


class Order(db.Model):
    
    reference = db.StringProperty(multiline=False, required=True)
    order_date = db.DateTimeProperty(auto_now_add=True, required=True)
    company_address = db.ReferenceProperty(OrderAddress, collection_name='company_addresses', required=True)# videcemo hocemo li ovako ili cemo iz OrderAddress samo reference uzimati
    invoice_address = db.ReferenceProperty(OrderAddress, collection_name='invoice_addresses', required=True)# videcemo hocemo li ovako ili cemo iz OrderAddress samo reference uzimati
    shipping_address = db.ReferenceProperty(OrderAddress, collection_name='shipping_addresses', required=True)# videcemo hocemo li ovako ili cemo iz OrderAddress samo reference uzimati
    currency = db.ReferenceProperty(Currency, collection_name='currencies', required=True)
    untaxed_amount = db.FloatProperty(required=True) # ili StringProperty, sta je vec bolje
    tax_amount = db.FloatProperty(required=True) # ili StringProperty, sta je vec bolje
    total_amount = db.FloatProperty(required=True) # ili StringProperty, sta je vec bolje
    comment = db.TextProperty()
    state = db.IntegerProperty(required=True)


class OrderRefenrece(db.Model):
    
    order = db.ReferenceProperty(Order, collection_name='orders', required=True)
    store_carrier = db.ReferenceProperty(StoreCarrier, collection_name='store_carriers', required=True)


class OrderAddress(db.Model):
    
    order = db.ReferenceProperty(Order, collection_name='orders', required=True)
    country = db.StringProperty(multiline=False, required=True)
    country_code = db.StringProperty(multiline=False, required=True)
    region = db.StringProperty(multiline=False, required=True)
    city = db.StringProperty(multiline=False, required=True)
    postal_code = db.StringProperty(multiline=False, required=True)
    street_address = db.StringProperty(multiline=False, required=True)
    street_address2 = db.StringProperty(multiline=False, required=True)
    name = db.StringProperty(multiline=False, required=True)
    email = db.EmailProperty()
    telephone = db.PhoneNumberProperty() # ne znam kakva se korist moze imati od PostalAddressProperty
    address_type = db.IntegerProperty(required=True)# ne mogu da koristim samo type posto je python keyword


class OrderAddressRefenrece(db.Model):
    
    order = db.ReferenceProperty(Order, collection_name='orders', required=True)
    buyer_address = db.ReferenceProperty(BuyerAddress, collection_name='buyer_addresses', required=True)
    address_type = db.IntegerProperty(required=True)# ne mogu da koristim samo type posto je python keyword


class OrderLine(db.Model):
    
    order = db.ReferenceProperty(Order, collection_name='orders', required=True)
    description = db.TextProperty(required=True)
    quantity = db.FloatProperty(required=True) # ili StringProperty, sta je vec bolje
    product_uom = db.ReferenceProperty(ProductUOM, collection_name='product_uoms', required=True)
    unit_price = db.FloatProperty(required=True) # ili StringProperty, sta je vec bolje
    discount = db.FloatProperty(required=True) # ili StringProperty, sta je vec bolje
    sequence = db.IntegerProperty(required=True)


class OrderLineTax(db.Model):
    
    order_line = db.ReferenceProperty(OrderLine, collection_name='order_lines', required=True)
    name = db.StringProperty(multiline=False, required=True)
    sequence = db.IntegerProperty(required=True)
    tax_type = db.IntegerProperty(required=True)# ne mogu da koristim samo type posto je python keyword
    amount = db.FloatProperty(required=True) # ili StringProperty, sta je vec bolje - obratiti paznju oko decimala posto ovo moze da bude i currency i procenat.


class OrderLineRefenrece(db.Model):
    
    order_line = db.ReferenceProperty(OrderLine, collection_name='order_lines', required=True)
    product_category = db.ReferenceProperty(ProductCategory, collection_name='product_categories', required=True)
    catalog_pricetag = db.ReferenceProperty(CatalogPricetag, collection_name='catalog_pricetags', required=True)
    catalog_product_instance = db.ReferenceProperty(CatalogProductInstance, collection_name='catalog_product_instances', required=True)


class OrderLineTaxRefenrece(db.Model):
    
    order_line = db.ReferenceProperty(OrderLine, collection_name='order_lines', required=True)
    store_tax = db.ReferenceProperty(StoreTax, collection_name='store_taxes', required=True)


class PayPalTransaction(db.Model):
    
    order = db.ReferenceProperty(Order, collection_name='orders', required=True)
    txn_id = db.StringProperty(multiline=False, required=True)
    ipn_message = db.TextProperty(required=True)
    logged = db.DateTimeProperty(auto_now_add=True, required=True)


class BillingLog(db.Model):
    
    store = db.ReferenceProperty(Store, collection_name='stores', required=True)
    logged = db.DateTimeProperty(auto_now_add=True, required=True)
    reference = db.ReferenceProperty(None, collection_name='references', required=True)# ne znam da li treba i uvesti reference_type?
    amount = db.FloatProperty(required=True) # ili StringProperty, sta je vec bolje
    balance = db.FloatProperty(required=True) # ili StringProperty, sta je vec bolje


class BillingCreditAdjustment(db.Model):
    
    store = db.ReferenceProperty(Store, collection_name='stores', required=True)
    agent = db.ReferenceProperty(User, collection_name='agents', required=True)
    adjusted = db.DateTimeProperty(auto_now_add=True, required=True)
    amount = db.FloatProperty(required=True) # ili StringProperty, sta je vec bolje
    message = db.TextProperty(required=True)
    note = db.TextProperty(required=True)


class StoreBuyerOrderFeedback(db.Model):
    
    store = db.ReferenceProperty(Store, collection_name='stores', required=True)
    store_name = db.StringProperty(multiline=False, required=True)
    buyer = db.ReferenceProperty(User, collection_name='buyers', required=True)
    order = db.ReferenceProperty(Order, collection_name='orders', required=True)
    state = db.IntegerProperty(required=True)


class Catalog(db.Model):
    
    store = db.ReferenceProperty(Store, collection_name='stores', required=True)
    name = db.StringProperty(multiline=False, required=True)
    publish = db.DateTimeProperty(required=True)# trebaju se definisati granice i rasponi, i postaviti neke default vrednosti
    discontinue = db.DateTimeProperty(required=True)
    cover = blobstore.BlobReferenceProperty()
    cost = db.FloatProperty(required=True) # ili StringProperty, sta je vec bolje
    state = db.IntegerProperty(required=True)


class CatalogImage(db.Model):
    
    catalog = db.ReferenceProperty(Catalog, collection_name='catalogs', required=True)
    image = blobstore.BlobReferenceProperty()
    sequence = db.IntegerProperty(required=True)


class CatalogStoreContent(db.Model):
    
    catalog = db.ReferenceProperty(Catalog, collection_name='catalogs', required=True)
    store = db.ReferenceProperty(Store, collection_name='stores', required=True)
    title = db.StringProperty(multiline=False, required=True)
    body = db.TextProperty(required=True)
    sequence = db.IntegerProperty(required=True)


class CatalogStoreShippingExclusion(db.Model):
    
    catalog = db.ReferenceProperty(Catalog, collection_name='catalogs', required=True)
    store = db.ReferenceProperty(Store, collection_name='stores', required=True)
    country = db.ReferenceProperty(Country, collection_name='countries')
    region = db.ReferenceProperty(CountrySubdivision, collection_name='regions')
    city = db.ReferenceProperty(CountrySubdivision, collection_name='cities') # ne znam da li ce ovo postojati??
    postal_code_from = db.StringProperty(multiline=False)
    postal_code_to = db.StringProperty(multiline=False)


class CatalogPricetag(db.Model):
    
    catalog = db.ReferenceProperty(Catalog, collection_name='catalogs', required=True)
    catalog_product_template = db.ReferenceProperty(CatalogProductTemplate, collection_name='catalog_product_templates', required=True)
    catalog_image = db.ReferenceProperty(CatalogImage, collection_name='catalog_images', required=True)
    source_width = db.FloatProperty(required=True)
    source_height = db.FloatProperty(required=True)
    source_position_top = db.FloatProperty(required=True)
    source_position_left = db.FloatProperty(required=True)
    pricetag_value = db.StringProperty(multiline=False)


class CatalogProductTemplate(db.Model):
    
    catalog = db.ReferenceProperty(Catalog, collection_name='catalogs', required=True)
    product_category = db.ReferenceProperty(ProductCategory, collection_name='product_categories', required=True)
    name = db.StringProperty(multiline=False, required=True)
    description = db.TextProperty(required=True)
    product_uom = db.ReferenceProperty(ProductUOM, collection_name='product_uoms', required=True)
    unit_price = db.FloatProperty(required=True) # ili StringProperty, sta je vec bolje
    active = db.BooleanProperty(default=True, required=True)


class CatalogProductVariantType(db.Model):
    
    catalog = db.ReferenceProperty(Catalog, collection_name='catalogs', required=True)
    name = db.StringProperty(multiline=False, required=True)
    description = db.TextProperty()
    allow_custom_value = db.BooleanProperty(default=False, required=True)
    mandatory_variant_type = db.BooleanProperty(default=True, required=True)


class CatalogProductVariantOption(db.Model):
    
    catalog_product_varinat_type = db.ReferenceProperty(CatalogProductVariantType, collection_name='catalog_product_varinat_types', required=True)
    name = db.StringProperty(multiline=False, required=True)
    sequence = db.IntegerProperty(required=True)


class CatalogProductTemplateProductVariantType(db.Model):
    
    catalog_product_template = db.ReferenceProperty(CatalogProductTemplate, collection_name='catalog_product_templates', required=True)
    catalog_product_varinat_type = db.ReferenceProperty(CatalogProductVariantType, collection_name='catalog_product_varinat_types', required=True)
    sequence = db.IntegerProperty(required=True)


class CatalogProductVariantValue(db.Model):
    
    catalog_product_template = db.ReferenceProperty(CatalogProductTemplate, collection_name='catalog_product_templates', required=True)
    catalog_product_varinat_type = db.ReferenceProperty(CatalogProductVariantType, collection_name='catalog_product_varinat_types', required=True)
    catalog_product_varinat_option = db.ReferenceProperty(CatalogProductVariantOption, collection_name='catalog_product_varinat_options', required=True)


class CatalogProductInstanceProductVariantValue(db.Model):
    
    catalog_product_varinat_value = db.ReferenceProperty(CatalogProductVariantValue, collection_name='catalog_product_varinat_values', required=True)
    catalog_product_instance = db.ReferenceProperty(CatalogProductInstance, collection_name='catalog_product_instances', required=True)


class CatalogProductInstance(db.Model):
    
    catalog_product_template = db.ReferenceProperty(CatalogProductTemplate, collection_name='catalog_product_templates', required=True)
    code = db.StringProperty(multiline=False, required=True)
    description = db.TextProperty()
    unit_price = db.FloatProperty() # ili StringProperty, sta je vec bolje    
    active = db.BooleanProperty(default=True, required=True)


class CatalogProductInstanceStock(db.Model):
    
    catalog_product_instance = db.ReferenceProperty(CatalogProductInstance, collection_name='catalog_product_instances', required=True)
    product_instance_type = db.IntegerProperty(required=True)
    low_stock_notify = db.BooleanProperty(default=True, required=True)
    low_stock_quantity = db.FloatProperty() # ili StringProperty, sta je vec bolje


class CatalogProductInstanceInventory(db.Model):
    
    catalog_product_instance = db.ReferenceProperty(CatalogProductInstance, collection_name='catalog_product_instances', required=True)
    updated = db.DateTimeProperty(required=True)
    reference = db.ReferenceProperty(None, collection_name='references')
    quantity = db.FloatProperty() # ili StringProperty, sta je vec bolje
    balance = db.FloatProperty() # ili StringProperty, sta je vec bolje


class CatalogProductImage(db.Model):
    
    reference = db.ReferenceProperty(None, collection_name='references', required=True)
    image = blobstore.BlobReferenceProperty()
    sequence = db.IntegerProperty(required=True)


class CatalogProductContent(db.Model):
    
    catalog = db.ReferenceProperty(Catalog, collection_name='catalogs', required=True)
    title = db.StringProperty(multiline=False, required=True)
    body = db.TextProperty(required=True)


class CatalogProductProductContent(db.Model):
    
    reference = db.ReferenceProperty(None, collection_name='references', required=True)
    catalog_product_content = db.ReferenceProperty(CatalogProductContent, collection_name='catalog_product_contents', required=True)
    sequence = db.IntegerProperty(required=True)

class CatalogProductMeasurements(db.Model):
    
    reference = db.ReferenceProperty(None, collection_name='references', required=True)
    weight = db.FloatProperty() # ili StringProperty, sta je vec bolje
    weight_uom = db.ReferenceProperty(ProductUOM, collection_name='weight_uoms', required=True)
    volume = db.FloatProperty() # ili StringProperty, sta je vec bolje
    volume_uom = db.ReferenceProperty(ProductUOM, collection_name='volume_uoms', required=True)



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