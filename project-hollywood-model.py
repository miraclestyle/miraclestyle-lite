#coding=UTF-8

#MASTER MODEL FILE

# NAPOMENA!!! - Sve mapirane informacije koje se koriste u aplikaciji trebaju biti hardcoded, tj. u samom aplikativnom codu a ne u settings.py
# u settings.py se cuvaju one informacije koje se ne cuvaju u datastore i koje se ne koriste u izgradnji datastore recorda...

from google.appengine.ext import blobstore
from google.appengine.ext import ndb
from decimal import *

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

datastore_key_kinds = {
    'ObjectLog':0,
    'User':1,
    'UserEmail':2,
    'UserIdentity':3,
    'UserIPAddress':4,
    'UserRole':5,
    'AggregateUserPermission':6,
    'Role':7,
    'Country':8,
    'CountrySubdivision':9,
    'Content':10,
    'SupportRequest':11,
    'FeedbackRequest':12,
    'Image':13,
    'ProductCategory':14,
    'ProductUOMCategory':15,
    'ProductUOM':16,
    'BuyerAddress':17,
    'BuyerCollection':18,
    
    
    'Notification':1,
    'NotificationRecipient':1,
    'NotificationOutlet':1,
    'Location':1,
    'Store':1,
    'StoreContent':1,
    'StoreTax':1,
    'StoreCarrier':1,
    'StoreCarrierLine':1,
    'StoreCarrierPricelist':1,
    
    'Currency':1,
    'Order':1,
    'OrderReference':1,
    'OrderAddress':1,
    'OrderLine':1,
    'OrderLineReference':1,
    'OrderLineTax':1,
    'PayPalTransaction':1,
    'BillingLog':1,
    'BillingCreditAdjustment':1,
    'OrderFeedback':1,
    'Catalog':1,
    'CatalogContent':1,
    'CatalogPricetag':1,
    'ProductTemplate':1,
    'ProductInstance':1,
    'ProductInstanceInventory':1,
    'ProductContent':1,
    'ProductVariant':1,
    'ProductTemplateVariant':1,
}


class DecimalProperty(ndb.StringProperty):
  def _validate(self, value):
    if not isinstance(value, (decimal.Decimal)):
      raise TypeError('expected an decimal, got %s' % repr(value))

  def _to_base_type(self, value):
    return str(value) # Doesn't matter if it's a decimal or string

  def _from_base_type(self, value):
    return decimal.Decimal(value)  # Always return a decimal


class ObjectLog(ndb.Expando):
    
    # ancestor Any - ancestor je objekat koji se ujedno i pickle u log property, ukljucujuci i njegovu hiejrarhiju - napr: 'User-UserLog-ObjectLog'
    # reference i type izvlacimo iz kljuca - key.parent()
    # posible composite indexes ???
    logged = ndb.DateTimeProperty('1', auto_now_add=True, required=True)
    agent = ndb.KeyProperty('2', kind=User, required=True)
    action = ndb.IntegerProperty('3', required=True)
    state = ndb.IntegerProperty('4', required=True)
    #_default_indexed = False
    #pass
    #message / m = ndb.TextProperty('5')# max size 64kb - to determine char count
    #note / n = ndb.TextProperty('6')# max size 64kb - to determine char count
    #log / l = ndb.TextProperty('7')
    
    # ovako se smanjuje storage u Datastore, i trebalo bi sprovesti to isto na sve modele
    @classmethod
    def _get_kind(cls):
      return datastore_key_kinds.ObjectLog


# ovo ce biti sistem za slanje poruka userima preko odredjenog outleta
# ostavicemo ga za kasnije posto nismo upoznati detaljno sa task queue
class Message(ndb.Model):
    
    # root
    outlet = ndb.IntegerProperty('1', required=True)
    group = ndb.IntegerProperty('2', required=True)
    state = ndb.IntegerProperty('3', required=True)


class MessageRecepient(ndb.Model):
    
    # ancestor Message
    recepient = ndb.KeyProperty('1', kind=User, required=True)
    sent = ndb.DateTimeProperty('2', auto_now_add=True, required=True)


class FeedbackRequest(ndb.Model):
    
    # ancestor User
    reference = ndb.StringProperty('1', required=True, indexed=False)
    state = ndb.IntegerProperty('2', required=True)
    updated = ndb.DateTimeProperty('3', auto_now=True, required=True)
    created = ndb.DateTimeProperty('4', auto_now_add=True, required=True)
    
    # primer helper funkcije u slucajevima gde se ne koristi ancestor mehanizam za pristup relacijama
    @property
    def logs(self):
      return ObjectLog.query(ancestor = self.key())


class SupportRequest(ndb.Model):
    
    # ancestor User
    reference = ndb.StringProperty('1', required=True, indexed=False)
    state = ndb.IntegerProperty('2', required=True)
    updated = ndb.DateTimeProperty('3', auto_now=True, required=True)
    created = ndb.DateTimeProperty('4', auto_now_add=True, required=True)


class Content(ndb.Model):
    
    # root
    # composite index category+state+sequence
    # veliki problem je ovde u vezi query-ja, zato sto datastore ne podrzava LIKE statement, verovatno cemo koristiti GAE Search
    updated = ndb.DateTimeProperty('1', auto_now=True, required=True)
    title = ndb.StringProperty('2', required=True, indexed=False)
    category = ndb.IntegerProperty('3', required=True)# proveriti da li composite index moze raditi kada je ovo indexed=False
    body = ndb.TextProperty('4', required=True)
    sequence = ndb.IntegerProperty('5', required=True)# proveriti da li composite index moze raditi kada je ovo indexed=False
    state = ndb.IntegerProperty('6', required=True)# published/unpublished - proveriti da li composite index moze raditi kada je ovo indexed=False


class Image(ndb.Model):
    
    # ancestor Any Object
    image = blobstore.BlobKeyProperty('1', required=True, indexed=False)# blob ce se implementirati na GCS
    content_type = ndb.StringProperty('2', required=True, indexed=False)
    size = ndb.FloatProperty('3', required=True, indexed=False)
    width = ndb.IntegerProperty('4', required=True, indexed=False)
    height = ndb.IntegerProperty('5', required=True, indexed=False)
    sequence = ndb.IntegerProperty('6', required=True)


class Country(ndb.Model):
    
    # root
    # u slucaju da ostane index za code, trebace nam composit index code+name
    # veliki problem je ovde u vezi query-ja, zato sto datastore ne podrzava LIKE statement, verovatno cemo koristiti GAE Search
    code = ndb.StringProperty('1', required=True, indexed=False)
    name = ndb.StringProperty('2', required=True, indexed=False)
    state = ndb.IntegerProperty('3', required=True)# active/inactive - proveriti da li composite index moze raditi kada je ovo indexed=False


class CountrySubdivision(ndb.Model):
    
    # ancestor Country
    # koliko cemo drilldown u ovoj strukturi zavisi od kasnijih odluka u vezi povezivanja lokativnih informacija sa informacijama ovog modela..
    # u slucaju da ostane index za code, trebace nam composit index code+name
    # veliki problem je ovde u vezi query-ja, zato sto datastore ne podrzava LIKE statement, verovatno cemo koristiti GAE Search
    parent_record = ndb.KeyProperty('1', kind=CountrySubdivision, indexed=False)
    name = ndb.StringProperty('2', required=True, indexed=False)
    code = ndb.StringProperty('3', required=True, indexed=False)
    type = ndb.IntegerProperty('4', required=True, indexed=False)
    state = ndb.IntegerProperty('5', required=True)# active/inactive - proveriti da li composite index moze raditi kada je ovo indexed=False


class Location(ndb.Model):
    
    # ancestor Any Object (Store, StoreTax, StoreCarrierLine, Catalog...)
    country = ndb.KeyProperty('1', kind=Country, required=True)
    region = ndb.KeyProperty('2', kind=CountrySubdivision)
    city = ndb.KeyProperty('3', kind=CountrySubdivision)# ne znam da li ce ovo postojati??
    postal_code_from = ndb.StringProperty('4')
    postal_code_to = ndb.StringProperty('5')


class ProductCategory(ndb.Model):
    
    # root
    # http://hg.tryton.org/modules/product/file/tip/category.py#l8
    # https://support.google.com/merchants/answer/1705911
    # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/product/product.py#L227
    # veliki problem je ovde u vezi query-ja, zato sto datastore ne podrzava LIKE statement, verovatno cemo koristiti GAE Search
    parent_record = ndb.KeyProperty('1', kind=ProductCategory, indexed=False)
    name = ndb.StringProperty('2', required=True, indexed=False)
    complete_name = ndb.TextProperty('3', required=True, indexed=False)
    state = ndb.IntegerProperty('4', required=True)


class ProductUOMCategory(ndb.Model):
    
    # root
    # http://hg.tryton.org/modules/product/file/tip/uom.py#l16
    # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/product/product.py#L81
    # veliki problem je ovde u vezi query-ja, zato sto datastore ne podrzava LIKE statement, verovatno cemo koristiti GAE Search
    name = ndb.StringProperty('1', required=True, indexed=False)


class ProductUOM(ndb.Model):
    
    # ancestor ProductUOMCategory
    # http://hg.tryton.org/modules/product/file/tip/uom.py#l28
    # http://hg.tryton.org/modules/product/file/tip/uom.xml#l63 - http://hg.tryton.org/modules/product/file/tip/uom.xml#l312
    # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/product/product.py#L89
    # veliki problem je ovde u vezi query-ja, zato sto datastore ne podrzava LIKE statement, verovatno cemo koristiti GAE Search
    name = ndb.StringProperty('1', required=True)
    symbol = ndb.StringProperty('2', required=True, indexed=False)
    rate = ndb.FloatProperty('3', required=True, indexed=False)# ovde ide custom decimal property
    factor = ndb.FloatProperty('4', required=True, indexed=False)# ovde ide custom decimal property
    rounding = ndb.FloatProperty('5', required=True, indexed=False)# ovde ide custom decimal property
    digits = ndb.IntegerProperty('6', required=True, indexed=False)
    state = ndb.IntegerProperty('7', required=True)


class User(ndb.Expando):
    
    # root
    state = ndb.IntegerProperty('1', required=True)
    #_default_indexed = False
    #pass


class UserEmail(ndb.Model):
    
    # ancestor User
    email = ndb.StringProperty('1', required=True)
    primary = ndb.BooleanProperty('2', default=True, indexed=False)


class UserIdentity(ndb.Model):
    
    # ancestor User
    user_email = ndb.KeyProperty('1', kind=UserEmail, required=True, indexed=False)
    identity = ndb.StringProperty('2', required=True)# spojen je i provider name sa id-jem
    associated = ndb.BooleanProperty('3', default=True, indexed=False)


class UserIPAddress(ndb.Model):
    
    # ancestor User
    ip_address = ndb.StringProperty('1', required=True, indexed=False)
    logged = ndb.DateTimeProperty('2', auto_now_add=True, required=True)


class UserRole(ndb.Model):
    
    # ancestor User
    role = ndb.KeyProperty('1', kind=Role, required=True)
    state = ndb.IntegerProperty('1', required=True)# invited/accepted


class AggregateUserPermission(ndb.Model):
    
    # ancestor User
    reference = ndb.KeyProperty('1',required=True)# ? ovo je referenca na Role u slucaju da user nasledjuje globalne dozvole, tj da je Role entitet root
    permissions = ndb.StringProperty('2', repeated=True, indexed=False)# permission_state_model - edit_unpublished_catalog


class Role(ndb.Model):
    
    # ancestor Store (Application, in the future) with permissions that affect store (application) and it's related entities
    # or root (if it is root, key id is manually assigned string) with global permissions on mstyle
    name = ndb.StringProperty('1', required=True, indexed=False)
    permissions = ndb.StringProperty('2', repeated=True, indexed=False)# permission_state_model - edit_unpublished_catalog
    readonly = ndb.BooleanProperty('3', default=True, indexed=False)


class Store(ndb.Expando):
    
    # root
    name = ndb.StringProperty('1', required=True)
    logo = blobstore.BlobKeyProperty('2', required=True)# verovatno je i dalje ovaj property od klase blobstore
    state = ndb.IntegerProperty('3', required=True)
    _default_indexed = False
    pass


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
    country = ndb.KeyProperty('2', kind=Country, required=True, indexed=False)
    region = ndb.KeyProperty('3', kind=CountrySubdivision, required=True, indexed=False)# ostaje da vidimo kako cemo ovo da handlamo, ili selection, ili text, ili i jedno i drugo po potrebi...
    city = ndb.StringProperty('4', required=True, indexed=False)
    postal_code = ndb.StringProperty('5', required=True, indexed=False)
    street_address = ndb.StringProperty('6', required=True, indexed=False)
    street_address2 = ndb.StringProperty('7', indexed=False)
    email = ndb.StringProperty('8', indexed=False)
    telephone = ndb.StringProperty('9', indexed=False)
    default_shipping = ndb.BooleanProperty('10', default=True)# indexed=False ?
    default_billing = ndb.BooleanProperty('11', default=True)# indexed=False ?

# bice potrebna verovatno i aggregate tabela neka
class BuyerCollection(ndb.Model):
    
    # ancestor User
    name = ndb.StringProperty('1', required=True)
    notifications = ndb.BooleanProperty('2', default=False, indexed=False)
    store = ndb.KeyProperty('3', kind=Store, repeated=True, indexed=False)
    product_category = ndb.KeyProperty('4', kind=ProductCategory, repeated=True, indexed=False)


class Currency(ndb.Model):
    
    # root
    # http://hg.tryton.org/modules/currency/file/tip/currency.py#l14
    # http://bazaar.launchpad.net/~openerp/openobject-server/7.0/view/head:/openerp/addons/base/res/res_currency.py#L32
    name = ndb.StringProperty('1', required=True)
    symbol = ndb.StringProperty('2', required=True)
    code = ndb.StringProperty('3', required=True)
    numeric_code = ndb.StringProperty('4')
    rounding = ndb.FloatProperty('5', required=True)# custom decimal
    digits = ndb.IntegerProperty('6', required=True)
    active = ndb.BooleanProperty('7', default=True)
    #formating
    grouping = ndb.StringProperty('8', required=True)
    decimal_separator = ndb.StringProperty('9', required=True)
    thousands_separator = ndb.StringProperty('10')
    positive_sign_position = ndb.IntegerProperty('11', required=True)
    negative_sign_position = ndb.IntegerProperty('12', required=True)
    positive_sign = ndb.StringProperty('13')
    negative_sign = ndb.StringProperty('14')
    positive_currency_symbol_precedes = ndb.BooleanProperty('15', default=True)
    negative_currency_symbol_precedes = ndb.BooleanProperty('16', default=True)
    positive_separate_by_space = ndb.BooleanProperty('17', default=True)
    negative_separate_by_space = ndb.BooleanProperty('18', default=True)


class Order(ndb.Expando):
    
    # root
    reference = ndb.StringProperty('1', required=True)
    order_date = ndb.DateTimeProperty('2', auto_now_add=True, required=True)
    currency = ndb.KeyProperty('3', kind=Currency, required=True)
    untaxed_amount = ndb.FloatProperty('4', required=True)# custom decimal
    tax_amount = ndb.FloatProperty('5', required=True)# custom decimal
    total_amount = ndb.FloatProperty('6', required=True)# custom decimal
    comment = ndb.TextProperty('7')
    state = ndb.IntegerProperty('8', required=True)
    #Expando
    company_address = ndb.StructuredProperty(OrderAddress, '9', required=True)
    billing_address = ndb.StructuredProperty(OrderAddress, '10', required=True)
    shipping_address = ndb.StructuredProperty(OrderAddress, '11', required=True)
    _default_indexed = False
    pass


class OrderReference(ndb.Model):
    
    # ancestor Order
    company_address = ndb.KeyProperty('1', kind=BuyerAddress, required=True)
    billing_address = ndb.KeyProperty('2', kind=BuyerAddress, required=True)
    shipping_address = ndb.KeyProperty('3', kind=BuyerAddress, required=True)
    carrier = ndb.KeyProperty('4', kind=StoreCarrier, required=True)


class OrderAddress(ndb.Expando):
    
    # StructuredProperty model
    name = ndb.StringProperty('1', required=True)
    country = ndb.StringProperty('2', required=True)
    country_code = ndb.StringProperty('3', required=True)
    region = ndb.StringProperty('4', required=True)
    city = ndb.StringProperty('5', required=True)
    postal_code = ndb.StringProperty('6', required=True)
    street_address = ndb.StringProperty('7', required=True)
    street_address2 = ndb.StringProperty('8')
    email = ndb.StringProperty('9')
    telephone = ndb.StringProperty('10')
    type = ndb.IntegerProperty('11', required=True)# ?


class OrderLine(ndb.Expando):
    
    # ancestor Order
    description = ndb.TextProperty('1', required=True)
    quantity = ndb.FloatProperty('2', required=True)# custom decimal
    product_uom = ndb.KeyProperty('3', kind=ProductUOM, required=True)
    unit_price = ndb.FloatProperty('4', required=True)# custom decimal
    discount = ndb.FloatProperty('5', default=0.00)# custom decimal
    sequence = ndb.IntegerProperty('6', required=True)
    taxes = ndb.StructuredProperty(OrderLineTax, '7', repeated=True)
    _default_indexed = False
    pass
    #Expando
    #product_category = ndb.KeyProperty('1', kind=ProductCategory, required=True)


class OrderLineReference(ndb.Model):
    
    # ancestor OrderLine
    catalog_pricetag = ndb.KeyProperty('1', kind=CatalogPricetag, required=True)
    product_instance = ndb.KeyProperty('2', kind=ProductInstance, required=True)
    taxes = ndb.KeyProperty('3', kind=StoreTax, repeated=True)


class OrderLineTax(ndb.Model):
    
    # StructuredProperty model
    # ovde vazi isto, ovo se moze izmeniti kada budemo optimize query/index..
    # http://hg.tryton.org/modules/account/file/tip/tax.py#l545
    name = ndb.StringProperty('1', required=True)
    type = ndb.IntegerProperty('2', required=True)
    amount = ndb.FloatProperty('3', required=True) # custom decimal - obratiti paznju oko decimala posto ovo moze da bude i currency i procenat.
    #sequence = ndb.IntegerProperty('4', required=True)


class PayPalTransaction(ndb.Model):
    
    # ancestor Order
    txn_id = ndb.StringProperty('1', required=True)
    ipn_message = ndb.TextProperty('2', required=True)
    logged = ndb.DateTimeProperty('3', auto_now_add=True, required=True)


class BillingLog(ndb.Model):
    
    # ancestor Billing Object (Store)
    logged = ndb.DateTimeProperty('1', auto_now_add=True, required=True)
    reference = ndb.KeyProperty('2',required=True)
    amount = ndb.FloatProperty('3', required=True)# custom decimal
    balance = ndb.FloatProperty('4', required=True)# custom decimal


class BillingCreditAdjustment(ndb.Model):
    
    # ancestor Billing Object (Store)
    amount = ndb.FloatProperty('1', required=True)# custom decimal
    state = ndb.IntegerProperty('2', required=True)


class OrderFeedback(ndb.Model):
    
    # ancestor Order
    store = ndb.KeyProperty('1', kind=Store, required=True)
    store_name = ndb.StringProperty('2', required=True)
    buyer = ndb.KeyProperty('3', kind=User, required=True)
    state = ndb.IntegerProperty('4', required=True)
    
    order_reference = ndb.StringProperty('5', required=True)# ? mozda async 
    order_date = ndb.DateTimeProperty('6', auto_now_add=True, required=True)#? mozda async
    total_amount = ndb.FloatProperty('7', required=True)# custom decimal ? mozda async
    order_state = ndb.IntegerProperty('8', required=True)# ? mozda async


class Catalog(ndb.Expando):
    
    # root
    store = ndb.KeyProperty('1', kind=Store, required=True)
    name = ndb.StringProperty('2', required=True)
    publish = ndb.DateTimeProperty('3', required=True)# trebaju se definisati granice i rasponi, i postaviti neke default vrednosti
    discontinue = ndb.DateTimeProperty('4', required=True)
    cover = blobstore.BlobKeyProperty('5', required=True)# verovatno je i dalje ovaj property od klase blobstore
    cost = ndb.FloatProperty('6', required=True)# custom decimal
    state = ndb.IntegerProperty('7', required=True)
    _default_indexed = False
    pass


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
    active = ndb.BooleanProperty('6', default=True)#?
    _default_indexed = False
    pass
    #Expando
    #weight = ndb.FloatProperty('7')# custom decimal
    #weight_uom = ndb.KeyProperty('8', kind=ProductUOM, required=True)# filtrirano po ProductUOMCategory Weight
    #volume = ndb.FloatProperty('9')# custom decimal
    #volume_uom = ndb.KeyProperty('10', kind=ProductUOM, required=True)# filtrirano po ProductUOMCategory Volume


class ProductInstance(ndb.Expando):
    
    # ancestor ProductTemplate
    #variant_signature se gradi na osnovu ProductVariant entiteta vezanih za ProductTemplate-a (od aktuelne ProductInstance) preko ProductTemplateVariant 
    #key name ce se graditi tako sto se uradi MD5 na variant_signature
    #query ce se graditi tako sto se prvo izgradi variant_signature vrednost na osnovu odabira od strane krajnjeg korisnika a potom se ta vrednost hesira u MD5 i koristi kao key identifier
    #mana ove metode je ta sto se uvek mora izgraditi kompletan variant_signature, tj moraju se sve varijacije odabrati (svaka varianta mora biti mandatory_variant_type)
    #default vrednost code ce se graditi na osnovu sledecih informacija: ancestorkey-n, gde je n incremental integer koji se dodeljuje instanci prilikom njenog kreiranja
    #ukoliko user ne odabere multivariant opciju onda se za ProductTemplate generise samo jedna ProductInstance i njen key se gradi automatski.
    code = ndb.StringProperty('1', required=True)
    active = ndb.BooleanProperty('2', default=True)#?
    _default_indexed = False
    pass
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
    #variant_signature = ndb.TextProperty('12', required=True)


class ProductInstanceInventory(ndb.Model):
    
    # ancestor ProductInstance
    updated = ndb.DateTimeProperty('1', auto_now_add=True, required=True)
    # ? reference = ndb.KeyProperty('2', required=True)
    quantity = ndb.FloatProperty('3', required=True)# custom decimal
    balance = ndb.FloatProperty('4', required=True)# custom decimal


class ProductContent(ndb.Model):
    
    # ancestor ProductTemplate, ProductInstance
    catalog_content = ndb.KeyProperty('1', kind=CatalogContent, required=True)
    sequence = ndb.IntegerProperty('2', required=True)


class ProductVariant(ndb.Model):
    
    #ancestor Catalog
    name = ndb.StringProperty('1', required=True)
    description = ndb.TextProperty('2')
    options = ndb.StringProperty('3', repeated=True)# nema potrebe za seqence - The datastore preserves the order of the list items in a repeated property, so you can assign some meaning to their ordering.
    allow_custom_value = ndb.BooleanProperty('4', default=False)#?
    mandatory_variant_type = ndb.BooleanProperty('5', default=True)#?


class ProductTemplateVariant(ndb.Model):
    
    # ancestor ProductTemplate
    product_variant = ndb.KeyProperty('1', kind=ProductVariant, required=True)
    sequence = ndb.IntegerProperty('2', required=True)
