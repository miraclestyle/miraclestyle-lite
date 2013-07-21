#coding=UTF-8

#MASTER MODEL FILE

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
    'ObjectLog':1,
    'Notification':1,
    'NotificationRecipient':1,
    'NotificationOutlet':1,
    'FeedbackRequest':1,
    'SupportRequest':1,
    'Content':1,
    'ContentRevision':1,
    'Image':1,
    'Country':1,
    'CountrySubdivision':1,
    'Location':1,
    'ProductCategory':1,
    'ProductUOMCategory':1,
    'ProductUOM':1,
    'User':'0',
    'UserEmail':'01',
    'UserIdentity':'02',
    'UserIPAddress':'03',
    'UserRole':'04',
    'Role':'05',
    'AggregateUserPermissions':1,
    'Store':1,
    'StoreContent':1,
    'StoreTax':1,
    'StoreCarrier':1,
    'StoreCarrierLine':1,
    'StoreCarrierPricelist':1,
    'BuyerAddress':1,
    'BuyerCollection':1,
    'BuyerCollectionStore':1,
    'BuyerCollectionProductCategory':1,
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
    return str(value) # Doesn't matter if it's an int or a long

  def _from_base_type(self, value):
    return decimal.Decimal(value)  # Always return a long


class ObjectLog(ndb.Model):
    
    # ancestor Any
    # kind izvlacimo iz kljuca pomocu key.kind() funkcije
    logged = ndb.DateTimeProperty('1', auto_now_add=True, required=True)
    agent = ndb.KeyProperty('2', kind=User, required=True)
    event = ndb.IntegerProperty('3', required=True)
    state = ndb.IntegerProperty('4', required=True)
    message = ndb.TextProperty('5', required=True)
    note = ndb.TextProperty('6', required=True)
    log = ndb.TextProperty('7', required=True)
    
    # ovako se smanjuje storage u Datastore, i trebalo bi sprovesti to isto na sve modele
    @classmethod
    def _get_kind(cls):
      return datastore_key_kinds.ObjectLog

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
    content_type = ndb.StringProperty('2', required=True)
    size = ndb.FloatProperty('3', required=True)
    width = ndb.IntegerProperty('4', required=True)
    height = ndb.IntegerProperty('5', required=True)
    sequence = ndb.IntegerProperty('6', required=True)

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


class User(ndb.Expando):
    
    # root
    state = ndb.IntegerProperty('1', required=True)
    #_default_indexed = False
    #pass


class UserEmail(ndb.Model):
    
    # ancestor User
    # key is MD5 of email + salt
    email = ndb.StringProperty('1', required=True, indexed=False)
    primary = ndb.BooleanProperty('2', default=True, indexed=False)


class UserIdentity(ndb.Model):
    
    # ancestor User
    # key is MD5 of provider + identity + salt
    user_email = ndb.KeyProperty('1', kind=UserEmail, required=True, indexed=False)
    provider = ndb.StringProperty('2', required=True, indexed=False)
    identity = ndb.StringProperty('3', required=True, indexed=False)
    associated = ndb.BooleanProperty('4', default=True, indexed=False)

# moze li ovo snimati GAE log ?
class UserIPAddress(ndb.Model):
    
    # ancestor User
    ip_address = ndb.StringProperty('1', required=True, indexed=False)
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
    #http://hg.tryton.org/modules/currency/file/tip/currency.py#l14
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
    adjusted = ndb.DateTimeProperty('1', auto_now_add=True, required=True)
    agent = ndb.KeyProperty('2', kind=User, required=True)
    amount = ndb.FloatProperty('3', required=True)# custom decimal
    message = ndb.TextProperty('4', required=True)
    note = ndb.TextProperty('5', required=True)


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
