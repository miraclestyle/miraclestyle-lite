#coding=UTF-8

#MASTER MODEL FILE

# NAPOMENA!!! - Sve mapirane informacije koje se snimaju u datastore trebaju biti hardcoded, tj. u samom aplikativnom codu a ne u settings.py
# u settings.py se cuvaju one informacije koje se ne cuvaju u datastore i koje se ne koriste u izgradnji datastore recorda...

# glavno pitanje je da li ce nam trebati composite indexi za query-je poput:
# BuyerAddress.query(ancestor=key).order(BuyerAddress.name) ili AggregateUserPermission.query(AggregateUserPermission.reference == key, ancestor=key)
# ali je highly unlikely, zato sto se ancestor ne mora ukljucivati u slucajevima composite indexa

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

from google.appengine.ext import blobstore
from google.appengine.ext import ndb
from decimal import *



class DecimalProperty(ndb.StringProperty):
  def _validate(self, value):
    if not isinstance(value, (decimal.Decimal)):
      raise TypeError('expected an decimal, got %s' % repr(value))

  def _to_base_type(self, value):
    return str(value) # Doesn't matter if it's a decimal or string

  def _from_base_type(self, value):
    return decimal.Decimal(value)  # Always return a decimal

################################################################################
# CORE - 8
################################################################################

# done!
class ObjectLog(ndb.Expando):
    
    # ancestor Any - ancestor je objekat koji se ujedno i pickle u log property, i moze biti bilo koji objekat osim pojedinih objekata koji su independent
    # reference i type izvlacimo iz kljuca - key.parent()
    # composite index - ???
    logged = ndb.DateTimeProperty('1', auto_now_add=True, required=True)
    agent = ndb.KeyProperty('2', kind=User, required=True)
    action = ndb.IntegerProperty('3', required=True)
    state = ndb.IntegerProperty('4', required=True)
    _default_indexed = False
    pass
    # message / m = ndb.TextProperty('5')# max size 64kb - to determine char count
    # note / n = ndb.TextProperty('6')# max size 64kb - to determine char count
    # log / l = ndb.TextProperty('7')
    
    # ovako se smanjuje storage u Datastore, i trebalo bi sprovesti to isto na sve modele
    @classmethod
    def _get_kind(cls):
      return datastore_key_kinds.ObjectLog

# done!
class User(ndb.Expando):
    
    # root
    state = ndb.IntegerProperty('1', required=True)
    email = ndb.StringProperty('2', repeated=True)# soft limit 1000x
    identity = ndb.StringProperty('3', repeated=True)# soft limit 100x
    _default_indexed = False
    pass
    #Expando
    # mozda ovako napraviti radi indexiranja, moguce je da StructuredProperty indexira svaki field a nama u indexu treba samo identity prop.
    # user_identity = ndb.LocalStructuredProperty(UserIdentity, '4', repeated=True)# soft limit 100x

# done!
class UserIdentity(ndb.Model):
    
    # StructuredProperty model
    identity = ndb.StringProperty('1', required=True)# spojen je i provider name sa id-jem
    email = ndb.StringProperty('2', required=True, indexed=False)
    associated = ndb.BooleanProperty('3', default=True, indexed=False)
    primary = ndb.BooleanProperty('4', default=True, indexed=False)

# done!
class UserIPAddress(ndb.Model):
    
    # ancestor User
    # not logged
    logged = ndb.DateTimeProperty('1', auto_now_add=True, required=True)
    ip_address = ndb.StringProperty('2', required=True, indexed=False)

# done!
class AggregateUserPermission(ndb.Model):
    
    # ancestor User
    # not logged
    reference = ndb.KeyProperty('1',required=True)# ovo je referenca na Role u slucaju da user nasledjuje globalne dozvole, tj da je Role entitet root
    permissions = ndb.StringProperty('2', repeated=True, indexed=False)# permission_state_model - edit_unpublished_catalog

# done!
class Role(ndb.Model):
    
    # ancestor Store (Application, in the future) with permissions that affect store (application) and it's related entities
    # or root (if it is root, key id is manually assigned string) with global permissions on mstyle
    name = ndb.StringProperty('1', required=True, indexed=False)
    permissions = ndb.StringProperty('2', repeated=True, indexed=False)# permission_state_model - edit_unpublished_catalog
    readonly = ndb.BooleanProperty('3', default=True, indexed=False)

# done!
class RoleUser(ndb.Model):
    
    # ancestor Role
    user = ndb.KeyProperty('1', kind=User, required=True)
    state = ndb.IntegerProperty('1', required=True)# invited/accepted


################################################################################
# MISC - 13
################################################################################

# done!
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

# done!
class SupportRequest(ndb.Model):
    
    # ancestor User
    reference = ndb.StringProperty('1', required=True, indexed=False)
    state = ndb.IntegerProperty('2', required=True)
    updated = ndb.DateTimeProperty('3', auto_now=True, required=True)
    created = ndb.DateTimeProperty('4', auto_now_add=True, required=True)

# ?
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

# done!
class Image(ndb.Model):
    
    # base class/structured class
    image = blobstore.BlobKeyProperty('1', required=True, indexed=False)# blob ce se implementirati na GCS
    content_type = ndb.StringProperty('2', required=True, indexed=False)
    size = ndb.FloatProperty('3', required=True, indexed=False)
    width = ndb.IntegerProperty('4', required=True, indexed=False)
    height = ndb.IntegerProperty('5', required=True, indexed=False)
    sequence = ndb.IntegerProperty('6', required=True)

# ?
class Country(ndb.Model):
    
    # root
    # http://hg.tryton.org/modules/country/file/tip/country.py#l8
    # http://en.wikipedia.org/wiki/ISO_3166
    # http://hg.tryton.org/modules/country/file/tip/country.xml
    # http://downloads.tryton.org/2.8/trytond_country-2.8.0.tar.gz
    # http://bazaar.launchpad.net/~openerp/openobject-server/7.0/view/head:/openerp/addons/base/res/res_country.py#L42
    # u slucaju da ostane index za code, trebace nam composit index code+name+active
    # veliki problem je ovde u vezi query-ja, zato sto datastore ne podrzava LIKE statement, verovatno cemo koristiti GAE Search
    code = ndb.StringProperty('1', required=True, indexed=False)
    name = ndb.StringProperty('2', required=True, indexed=False)
    active = ndb.BooleanProperty('3', default=True, indexed=False)# proveriti da li composite index moze raditi kada je ovo indexed=False

# ?
class CountrySubdivision(ndb.Model):
    
    # ancestor Country
    # http://hg.tryton.org/modules/country/file/tip/country.py#l52
    # http://bazaar.launchpad.net/~openerp/openobject-server/7.0/view/head:/openerp/addons/base/res/res_country.py#L86
    # koliko cemo drilldown u ovoj strukturi zavisi od kasnijih odluka u vezi povezivanja lokativnih informacija sa informacijama ovog modela..
    # u slucaju da ostane index za code, trebace nam composit index code+name+active
    # veliki problem je ovde u vezi query-ja, zato sto datastore ne podrzava LIKE statement, verovatno cemo koristiti GAE Search
    parent_record = ndb.KeyProperty('1', kind=CountrySubdivision, indexed=False)
    name = ndb.StringProperty('2', required=True, indexed=False)
    code = ndb.StringProperty('3', required=True, indexed=False)
    type = ndb.IntegerProperty('4', required=True, indexed=False)
    active = ndb.BooleanProperty('5', default=True, indexed=False)# proveriti da li composite index moze raditi kada je ovo indexed=False

# done!
class Location(ndb.Expando):
    
    # base class/structured class
    country = ndb.KeyProperty('1', kind=Country, required=True, indexed=False)
    _default_indexed = False
    pass
    # Expando
    # region = ndb.KeyProperty('2', kind=CountrySubdivision)# ako je potreban string val onda se ovo preskace 
    # region = ndb.StringProperty('2')# ako je potreban key val onda se ovo preksace
    # postal_code_from = ndb.StringProperty('3')
    # postal_code_to = ndb.StringProperty('4')
    # city = ndb.StringProperty('5')# ako se javi potreba za ovim ??

# ?
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

# ?
class ProductUOMCategory(ndb.Model):
    
    # root
    # http://hg.tryton.org/modules/product/file/tip/uom.py#l16
    # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/product/product.py#L81
    # veliki problem je ovde u vezi query-ja, zato sto datastore ne podrzava LIKE statement, verovatno cemo koristiti GAE Search
    name = ndb.StringProperty('1', required=True, indexed=False)

# ?
class ProductUOM(ndb.Model):
    
    # ancestor ProductUOMCategory
    # http://hg.tryton.org/modules/product/file/tip/uom.py#l28
    # http://hg.tryton.org/modules/product/file/tip/uom.xml#l63 - http://hg.tryton.org/modules/product/file/tip/uom.xml#l312
    # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/product/product.py#L89
    # veliki problem je ovde u vezi query-ja, zato sto datastore ne podrzava LIKE statement, verovatno cemo koristiti GAE Search
    # custom index name+active
    name = ndb.StringProperty('1', required=True)
    symbol = ndb.StringProperty('2', required=True, indexed=False)
    rate = DecimalProperty('3', required=True, indexed=False)
    factor = DecimalProperty('4', required=True, indexed=False)
    rounding = DecimalProperty('5', required=True, indexed=False)
    digits = ndb.IntegerProperty('6', required=True, indexed=False)
    active = ndb.BooleanProperty('7', default=True, indexed=False)# proveriti da li composite index moze raditi kada je ovo indexed=False

# ?
class Currency(ndb.Model):
    
    # root
    # http://hg.tryton.org/modules/currency/file/tip/currency.py#l14
    # http://en.wikipedia.org/wiki/ISO_4217
    # http://hg.tryton.org/modules/currency/file/tip/currency.xml#l107
    # http://bazaar.launchpad.net/~openerp/openobject-server/7.0/view/head:/openerp/addons/base/res/res_currency.py#L32
    # custom index code+active
    # veliki problem je ovde u vezi query-ja, zato sto datastore ne podrzava LIKE statement, verovatno cemo koristiti GAE Search
    name = ndb.StringProperty('1', required=True, indexed=False)
    symbol = ndb.StringProperty('2', required=True, indexed=False)
    code = ndb.StringProperty('3', required=True)
    numeric_code = ndb.StringProperty('4', indexed=False)
    rounding = DecimalProperty('5', required=True, indexed=False)
    digits = ndb.IntegerProperty('6', required=True, indexed=False)
    active = ndb.BooleanProperty('7', default=True, indexed=False)# proveriti da li composite index moze raditi kada je ovo indexed=False
    #formating
    grouping = ndb.StringProperty('8', required=True, indexed=False)
    decimal_separator = ndb.StringProperty('9', required=True, indexed=False)
    thousands_separator = ndb.StringProperty('10', indexed=False)
    positive_sign_position = ndb.IntegerProperty('11', required=True, indexed=False)
    negative_sign_position = ndb.IntegerProperty('12', required=True, indexed=False)
    positive_sign = ndb.StringProperty('13', indexed=False)
    negative_sign = ndb.StringProperty('14', indexed=False)
    positive_currency_symbol_precedes = ndb.BooleanProperty('15', default=True, indexed=False)
    negative_currency_symbol_precedes = ndb.BooleanProperty('16', default=True, indexed=False)
    positive_separate_by_space = ndb.BooleanProperty('17', default=True, indexed=False)
    negative_separate_by_space = ndb.BooleanProperty('18', default=True, indexed=False)

# ?
# ovo ce biti sistem za slanje poruka userima preko odredjenog outleta
# ostavicemo ga za kasnije posto nismo upoznati detaljno sa task queue
class Message(ndb.Model):
    
    # root
    outlet = ndb.IntegerProperty('1', required=True)
    group = ndb.IntegerProperty('2', required=True)
    state = ndb.IntegerProperty('3', required=True)

# ?
class MessageRecepient(ndb.Model):
    
    # ancestor Message
    recepient = ndb.KeyProperty('1', kind=User, required=True)
    sent = ndb.DateTimeProperty('2', auto_now_add=True, required=True)


################################################################################
# BUYER - 4
################################################################################

# done!
class BuyerAddress(ndb.Expando):
    
    # ancestor User
    name = ndb.StringProperty('1', required=True)
    country = ndb.KeyProperty('2', kind=Country, required=True, indexed=False)
    city = ndb.StringProperty('3', required=True, indexed=False)
    postal_code = ndb.StringProperty('4', required=True, indexed=False)
    street_address = ndb.StringProperty('5', required=True, indexed=False)
    default_shipping = ndb.BooleanProperty('6', default=True, indexed=False)
    default_billing = ndb.BooleanProperty('7', default=True, indexed=False)
    _default_indexed = False
    pass
    # Expando
    # naredna dva polja su required!!!
    # region = ndb.KeyProperty('8', kind=CountrySubdivision, required=True)# ako je potreban string val onda se ovo preskace 
    # region = ndb.StringProperty('8', required=True)# ako je potreban key val onda se ovo preskace
    # street_address2 = ndb.StringProperty('9')
    # email = ndb.StringProperty('10')
    # telephone = ndb.StringProperty('11')

# done!
class BuyerCollection(ndb.Model):
    
    # ancestor User
    name = ndb.StringProperty('1', required=True)
    notifications = ndb.BooleanProperty('2', default=False)
    primary_email = ndb.StringProperty('3', required=True, indexed=False)

# done!
class BuyerCollectionStore(ndb.Model):
    
    # ancestor User
    store = ndb.KeyProperty('1', kind=Store, required=True)
    collections = ndb.KeyProperty('2', kind=BuyerCollection, repeated=True, indexed=False)# soft limit 500x - mozda ce trebati index zbog stores taba na collection management
    
# done!
class AggregateBuyerCollectionCatalog(ndb.Model):
    
    # ancestor User
    # not logged
    # task queue radi agregaciju prilikom nekih promena na store-u
    store = ndb.KeyProperty('1', kind=Store, required=True)
    collections = ndb.KeyProperty('2', kind=BuyerCollection, repeated=True, indexed=False)# soft limit 500x
    catalog = ndb.KeyProperty('3', kind=Catalog, required=True, indexed=False)
    catalog_cover = blobstore.BlobKeyProperty('4', required=True, indexed=False)# blob ce se implementirati na GCS
    catalog_published_date = ndb.DateTimeProperty('5', required=True)


################################################################################
# STORE - 7
################################################################################

# done!
class Store(ndb.Expando):
    
    # root (ancestor Application)
    # composite index - state+name ??
    name = ndb.StringProperty('1', required=True)
    logo = blobstore.BlobKeyProperty('2', required=True, indexed=False)# blob ce se implementirati na GCS
    primary_contact = ndb.KeyProperty('3', kind=User, required=True, indexed=False)
    state = ndb.IntegerProperty('4', required=True)# indexed=False ?
    _default_indexed = False
    pass
    #Expando
    #
    # Company
    # company_name = ndb.StringProperty('5', required=True)
    # company_country = ndb.KeyProperty('6', kind=Country, required=True)
    # company_region = ndb.KeyProperty('7', kind=CountrySubdivision, required=True)# ako je potreban string val onda se ovo preskace 
    # company_region = ndb.StringProperty('7', required=True)# ako je potreban key val onda se ovo preskace
    # company_city = ndb.StringProperty('8', required=True)
    # company_postal_code = ndb.StringProperty('9', required=True)
    # company_street_address = ndb.StringProperty('10', required=True)
    # company_street_address2 = ndb.StringProperty('11')
    # company_email = ndb.StringProperty('12')
    # company_telephone = ndb.StringProperty('13')
    #
    # Payment
    # currency = ndb.KeyProperty('14', kind=Currency, required=True)
    # tax_buyer_on ?
    # paypal_email = ndb.StringProperty('15')
    # paypal_shipping ?
    #
    # Analytics 
    # tracking_id = ndb.StringProperty('16')
    #
    # Feedback
    # positive_feedback_count = ndb.IntegerProperty('17', required=True)
    # negative_feedback_count = ndb.IntegerProperty('18', required=True)
    # neutral_feedback_count = ndb.IntegerProperty('19', required=True)

# done!
class StoreContent(ndb.Model):
    
    # ancestor Store (Catalog - for caching)
    title = ndb.StringProperty('1', required=True, indexed=False)
    body = ndb.TextProperty('2', required=True)
    sequence = ndb.IntegerProperty('3', required=True)

# done!
class StoreShippingExclusion(Location):
    
    # ancestor Store (Catalog - for caching)

# done!
class Tax(ndb.Expando):
    
    # ancestor Store (Application)
    # composite index - active+sequence
    name = ndb.StringProperty('1', required=True, indexed=False)
    sequence = ndb.IntegerProperty('2', required=True)
    amount = ndb.StringProperty('3', required=True, indexed=False)# prekompajlirane vrednosti iz UI, napr: 17.00[%] ili 10.00[c] gde je [c] = currency
    location_exclusion = ndb.BooleanProperty('4', default=False, indexed=False)# applies to all locations except/applies to all locations listed below
    active = ndb.BooleanProperty('5', default=True)# indexed=False ?
    _default_indexed = False
    pass
    # Expando
    # location = ndb.LocalStructuredProperty(Location, '6', repeated=True)
    # product_category = ndb.KeyProperty('7', kind=ProductCategory, repeated=True)
    # carrier = ndb.KeyProperty('8', kind=Carrier, repeated=True)

# done!
class Carrier(ndb.Model):
    
    # ancestor Store (Application)
    # composite index - active+name ??
    name = ndb.StringProperty('1', required=True)
    active = ndb.BooleanProperty('2', default=True)# indexed=False ?

# done!
class CarrierLine(ndb.Expando):
    
    # ancestor Carrier
    # composite index - active+sequence
    name = ndb.StringProperty('1', required=True, indexed=False)
    sequence = ndb.IntegerProperty('2', required=True)
    location_exclusion = ndb.BooleanProperty('3', default=False, indexed=False)
    active = ndb.BooleanProperty('4', default=True)# indexed=False ?
    _default_indexed = False
    pass
    # Expando
    # location = ndb.LocalStructuredProperty(Location, '5', repeated=True)# soft limit 400x
    # rules = ndb.LocalStructuredProperty(CarrierLineRule, '6', repeated=True)# soft limit 500x

# done!
class CarrierLineRule(ndb.Model):
    
    # LocalStructuredProperty model
    # ovde se cuvaju dve vrednosti koje su obicno struktuirane kao formule, ovo je mnogo fleksibilnije nego hardcoded struktura informacija koje se cuva kao sto je bio prethodni slucaj
    condition = ndb.StringProperty('1', required=True, indexed=False)# prekompajlirane vrednosti iz UI, napr: True ili weight[kg] >= 5 ili volume[m3] = 0.002
    price = ndb.StringProperty('2', required=True, indexed=False)# prekompajlirane vrednosti iz UI, napr: amount = 35.99 ili amount = weight[kg]*0.28
    # weight - kg; volume - m3; ili sta vec odlucimo, samo je bitno da se podudara sa measurementsima na ProductTemplate/ProductInstance


################################################################################
# CATALOG - 9
################################################################################

# done!
class Catalog(ndb.Expando):
    
    # root (ancestor Application)
    # https://support.google.com/merchants/answer/188494?hl=en&hlrm=en#other
    # composite index - ???
    store = ndb.KeyProperty('1', kind=Store, required=True)
    name = ndb.StringProperty('2', required=True)
    publish = ndb.DateTimeProperty('3', required=True)# today
    discontinue = ndb.DateTimeProperty('4', required=True)# +30 days
    cover = blobstore.BlobKeyProperty('5', required=True, indexed=False)# blob ce se implementirati na GCS
    cost = DecimalProperty('6', required=True, indexed=False)
    state = ndb.IntegerProperty('7', required=True)
    _default_indexed = False
    pass
    # Expando
    # Search improvements
    # product count per product category
    # rank coefficient based on store feedback

# done!
class CatalogImage(Image):
    
    # ancestor Catalog

# done!
class CatalogPricetag(ndb.Model):
    
    # ancestor Catalog
    product_template = ndb.KeyProperty('1', kind=ProductTemplate, required=True, indexed=False)
    container_image = blobstore.BlobKeyProperty('2', required=True, indexed=False)# blob ce se implementirati na GCS
    source_width = ndb.FloatProperty('3', required=True, indexed=False)
    source_height = ndb.FloatProperty('4', required=True, indexed=False)
    source_position_top = ndb.FloatProperty('5', required=True, indexed=False)
    source_position_left = ndb.FloatProperty('6', required=True, indexed=False)
    value = ndb.StringProperty('7', required=True, indexed=False)# $ 19.99 - ovo se handla unutar transakcije kada se radi update na unit_price od ProductTemplate ili ProductInstance

# done!
class ProductTemplate(ndb.Expando):
    
    # ancestor Catalog (Application)
    product_category = ndb.KeyProperty('1', kind=ProductCategory, required=True, indexed=False)
    name = ndb.StringProperty('2', required=True)
    description = ndb.TextProperty('3', required=True)# soft limit 64kb
    product_uom = ndb.KeyProperty('4', kind=ProductUOM, required=True, indexed=False)
    unit_price = DecimalProperty('5', required=True, indexed=False)
    state = ndb.IntegerProperty('6', required=True)
    # states: - ovo cemo pojasniti
    # 'in stock'
    # 'available for order'
    # 'out of stock'
    # 'preorder'
    # 'auto manage inventory - available for order' (poduct is 'available for order' when inventory balance is <= 0)
    # 'auto manage inventory - out of stock' (poduct is 'out of stock' when inventory balance is <= 0)
    # https://support.google.com/merchants/answer/188494?hl=en&ref_topic=2473824
    _default_indexed = False
    pass
    # Expando
    # mozda treba uvesti customer lead time??
    # product_template_variant = ndb.KeyProperty('7', kind=ProductVariant, repeated=True)# soft limit 100x
    # product_template_content = ndb.KeyProperty('8', kind=ProductContent, repeated=True)# soft limit 100x
    # product_template_image = ndb.LocalStructuredProperty(Image, '9', repeated=True)# soft limit 100x
    # weight = DecimalProperty('10')# kg - ili sta vec odlucimo
    # volume = DecimalProperty('11')# m3 - ili sta vec odlucimo

# done!
class ProductInstance(ndb.Expando):
    
    # ancestor ProductTemplate
    #variant_signature se gradi na osnovu ProductVariant entiteta vezanih za ProductTemplate-a (od aktuelne ProductInstance) preko ProductTemplateVariant 
    #key name ce se graditi tako sto se uradi MD5 na variant_signature
    #query ce se graditi tako sto se prvo izgradi variant_signature vrednost na osnovu odabira od strane krajnjeg korisnika a potom se ta vrednost hesira u MD5 i koristi kao key identifier
    #mana ove metode je ta sto se uvek mora izgraditi kompletan variant_signature, tj moraju se sve varijacije odabrati (svaka varianta mora biti mandatory_variant_type)
    #default vrednost code ce se graditi na osnovu sledecih informacija: ancestorkey-n, gde je n incremental integer koji se dodeljuje instanci prilikom njenog kreiranja
    #ukoliko user ne odabere multivariant opciju onda se za ProductTemplate generise samo jedna ProductInstance i njen key se gradi automatski.
    code = ndb.StringProperty('1', required=True)
    state = ndb.IntegerProperty('2', required=True)
    # states: - ovo cemo pojasniti
    # 'in stock'
    # 'available for order'
    # 'out of stock'
    # 'preorder'
    # 'auto manage inventory - available for order' (poduct is 'available for order' when inventory balance is <= 0)
    # 'auto manage inventory - out of stock' (poduct is 'out of stock' when inventory balance is <= 0)
    # https://support.google.com/merchants/answer/188494?hl=en&ref_topic=2473824
    _default_indexed = False
    pass
    # Expando
    # description = ndb.TextProperty('3', required=True)# soft limit 64kb
    # unit_price = DecimalProperty('4', required=True)
    # product_instance_content = ndb.KeyProperty('5', kind=ProductContent, repeated=True)# soft limit 100x
    # product_instance_image = ndb.LocalStructuredProperty(Image, '6', repeated=True)# soft limit 100x
    # low_stock_quantity = DecimalProperty('7', default=0.00)# notify store manager when qty drops below X quantity
    # weight = DecimalProperty('8')# kg - ili sta vec odlucimo
    # volume = DecimalProperty('9')# m3 - ili sta vec odlucimo
    # variant_signature = ndb.TextProperty('10', required=True)# soft limit 64kb - ova vrednost kao i vrednosti koje kupac manuelno upise kao opcije variante se prepisuju u order line description prilikom Add to Cart

# done!
class ProductInventoryLog(ndb.Model):
    
    # ancestor ProductInstance
    # not logged
    logged = ndb.DateTimeProperty('1', auto_now_add=True, required=True)
    reference = ndb.KeyProperty('2',required=True, indexed=False)
    quantity = DecimalProperty('3', required=True, indexed=False)
    balance = DecimalProperty('4', required=True, indexed=False)

# done!
class ProductInventoryAdjustment(ndb.Model):
    
    # ancestor ProductInstance
    # not logged
    adjusted = ndb.DateTimeProperty('1', auto_now_add=True, required=True, indexed=False)
    agent = ndb.KeyProperty('2', kind=User, required=True, indexed=False)
    quantity = DecimalProperty('3', required=True, indexed=False, indexed=False)
    comment = ndb.StringProperty('4', required=True, indexed=False)

# done!
class ProductVariant(ndb.Model):
    
    #ancestor Catalog (Application)
    # http://v6apps.openerp.com/addon/1809
    name = ndb.StringProperty('1', required=True)
    description = ndb.TextProperty('2')
    options = ndb.StringProperty('3', repeated=True, indexed=False)# nema potrebe za seqence - The datastore preserves the order of the list items in a repeated property, so you can assign some meaning to their ordering.
    allow_custom_value = ndb.BooleanProperty('4', default=False, indexed=False)# ovu vrednost buyer upisuje u definisano polje a ona se dalje prepisuje u order line description prilikom Add to Cart 

# done!
class ProductContent(ndb.Model):
    
    # ancestor Catalog (Application)
    title = ndb.StringProperty('1', required=True)
    body = ndb.TextProperty('2', required=True)


################################################################################
# TRADE - 9
################################################################################

# ?
class Order(ndb.Expando):
    
    # ancestor Store (Application) ? root - ali verovatno je najbolje da pripadne storovima, radi jednostavnosti
    # http://hg.tryton.org/modules/sale/file/tip/sale.py#l28
    # http://hg.tryton.org/modules/purchase/file/tip/purchase.py#l32
    # http://doc.tryton.org/2.8/modules/sale/doc/index.html
    # http://doc.tryton.org/2.8/modules/purchase/doc/index.html
    # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/sale/sale.py#L48
    # store = ndb.KeyProperty('1', kind=Store, required=True)
    # composite index - buyer+updated; buyer+order_date
    buyer = ndb.KeyProperty('2', kind=User, required=True)# indexed=False ?
    order_date = ndb.DateTimeProperty('3', auto_now_add=True, required=True)# updated on checkout
    currency = ndb.KeyProperty('4', kind=Currency, required=True, indexed=False)# ? mozda staviti iso code posto je to key na currency 
    untaxed_amount = DecimalProperty('5', required=True, indexed=False)
    tax_amount = DecimalProperty('6', required=True, indexed=False)
    total_amount = DecimalProperty('7', required=True, indexed=False)
    state = ndb.IntegerProperty('8', required=True)# indexed=False ? 
    updated = ndb.DateTimeProperty('9', auto_now=True, required=True)
    _default_indexed = False
    pass
    # Expando
    # company_address = ndb.LocalStructuredProperty(OrderAddress, '10', required=True)
    # billing_address = ndb.LocalStructuredProperty(OrderAddress, '11', required=True)
    # shipping_address = ndb.LocalStructuredProperty(OrderAddress, '12', required=True)
    # reference = ndb.StringProperty('13', required=True)
    # comment = ndb.TextProperty('14')# 64kb limit
    # company_address_reference = ndb.KeyProperty('15', kind=Store, required=True)
    # billing_address_reference = ndb.KeyProperty('16', kind=BuyerAddress, required=True)
    # shipping_address_reference = ndb.KeyProperty('17', kind=BuyerAddress, required=True)
    # carrier_reference = ndb.KeyProperty('18', kind=StoreCarrier, required=True)
    # feedback = ndb.IntegerProperty('19', required=True)
    # store_name = ndb.StringProperty('20', required=True)
    # store_logo = blobstore.BlobKeyProperty('21', required=True)# ovo bi moglo da posluzi ??

# done!
class OrderFeedback(ndb.Model):
    
    # ancestor Order
    state = ndb.IntegerProperty('1', required=True, indexed=False)

# ?
class BillingOrder(ndb.Expando):
    
    # ancestor Store (Application)
    # http://hg.tryton.org/modules/sale/file/tip/sale.py#l28
    # http://hg.tryton.org/modules/purchase/file/tip/purchase.py#l32
    # http://doc.tryton.org/2.8/modules/sale/doc/index.html
    # http://doc.tryton.org/2.8/modules/purchase/doc/index.html
    # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/sale/sale.py#L48
    order_date = ndb.DateTimeProperty('1', auto_now_add=True, required=True)# updated on checkout
    currency = ndb.KeyProperty('2', kind=Currency, required=True, indexed=False)# ? mozda staviti iso code posto je to key na currency 
    untaxed_amount = DecimalProperty('3', required=True, indexed=False)
    tax_amount = DecimalProperty('4', required=True, indexed=False)
    total_amount = DecimalProperty('5', required=True, indexed=False)
    state = ndb.IntegerProperty('6', required=True)# indexed=False ? 
    updated = ndb.DateTimeProperty('7', auto_now=True, required=True)
    _default_indexed = False
    pass
    # Expando
    # company_address = ndb.LocalStructuredProperty(OrderAddress, '8', required=True)
    # billing_address = ndb.LocalStructuredProperty(OrderAddress, '9', required=True)
    # shipping_address = ndb.LocalStructuredProperty(OrderAddress, '10', required=True)
    # reference = ndb.StringProperty('11', required=True)
    # comment = ndb.TextProperty('12')# 64kb limit

# done!
class OrderAddress(ndb.Expando):
    
    # LocalStructuredProperty model
    name = ndb.StringProperty('1', required=True, indexed=False)
    country = ndb.StringProperty('2', required=True, indexed=False)
    country_code = ndb.StringProperty('3', required=True, indexed=False)
    region = ndb.StringProperty('4', required=True, indexed=False)
    city = ndb.StringProperty('5', required=True, indexed=False)
    postal_code = ndb.StringProperty('6', required=True, indexed=False)
    street_address = ndb.StringProperty('7', required=True, indexed=False)
    _default_indexed = False
    pass
    # Expando
    # street_address2 = ndb.StringProperty('8')
    # email = ndb.StringProperty('9')
    # telephone = ndb.StringProperty('10')

# ?
class OrderLine(ndb.Expando):
    
    # ancestor Order, BillingOrder
    # http://hg.tryton.org/modules/sale/file/tip/sale.py#l888
    # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/sale/sale.py#L649
    description = ndb.TextProperty('1', required=True)
    quantity = DecimalProperty('2', required=True, indexed=False)
    product_uom = ndb.KeyProperty('3', kind=ProductUOM, required=True, indexed=False)#?
    unit_price = DecimalProperty('4', required=True, indexed=False)
    discount = DecimalProperty('5', default=0.00, indexed=False)
    sequence = ndb.IntegerProperty('6', required=True, indexed=False)
    _default_indexed = False
    pass
    # Expando
    # taxes = ndb.LocalStructuredProperty(OrderLineTax, '7', repeated=True)
    # product_category = ndb.KeyProperty('8', kind=ProductCategory, required=True)
    # catalog_pricetag_reference = ndb.KeyProperty('9', kind=CatalogPricetag, required=True)
    # product_instance_reference = ndb.KeyProperty('10', kind=ProductInstance, required=True)
    # taxes_reference = ndb.KeyProperty('11', kind=StoreTax, repeated=True)

# done!
class OrderLineTax(ndb.Model):
    
    # LocalStructuredProperty model
    # http://hg.tryton.org/modules/account/file/tip/tax.py#l545
    name = ndb.StringProperty('1', required=True, indexed=False)
    type = ndb.IntegerProperty('2', required=True, indexed=False)
    amount = DecimalProperty('3', required=True, indexed=False)# obratiti paznju oko decimala posto ovo moze da bude i currency i procenat.

# done!
class PayPalTransaction(ndb.Model):
    
    # ancestor Order, BillingOrder
    # not logged
    logged = ndb.DateTimeProperty('1', auto_now_add=True, required=True)# indexed=False ? ako cemo imati direktan pristup ovoj tabeli onda nam treba index
    txn_id = ndb.StringProperty('2', required=True)
    ipn_message = ndb.TextProperty('3', required=True)

# done!
class BillingLog(ndb.Model):
    
    # ancestor Store (Application)
    # not logged
    logged = ndb.DateTimeProperty('1', auto_now_add=True, required=True)
    reference = ndb.KeyProperty('2',required=True, indexed=False)
    amount = DecimalProperty('3', required=True, indexed=False)
    balance = DecimalProperty('4', required=True, indexed=False)

# done!
class BillingCreditAdjustment(ndb.Model):
    
    # ancestor Store (Application)
    # not logged
    adjusted = ndb.DateTimeProperty('1', auto_now_add=True, required=True, indexed=False)
    agent = ndb.KeyProperty('2', kind=User, required=True, indexed=False)
    amount = DecimalProperty('3', required=True, indexed=False)
    message = ndb.TextProperty('4')# max size 64kb - to determine char count
    note = ndb.TextProperty('5')# max size 64kb - to determine char count

