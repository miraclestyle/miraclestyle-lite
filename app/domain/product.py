# -*- coding: utf-8 -*-
'''
Created on Oct 20, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import ndb

class Template(ndb.BaseExpando):
    
    # ancestor DomainCatalog (future - root / namespace Domain)
    # composite index: ancestor:yes - name
    product_category = ndb.KeyProperty('1', kind='core.misc.ProductCategory', required=True, indexed=False)
    name = ndb.StringProperty('2', required=True)
    description = ndb.TextProperty('3', required=True)# soft limit 64kb
    product_uom = ndb.KeyProperty('4', kind='core.misc.ProductUOM', required=True, indexed=False)
    unit_price = ndb.SuperDecimalProperty('5', required=True)
    availability = ndb.IntegerProperty('6', required=True, indexed=False)# ukljuciti index ako bude trebao za projection query
    # availability: - ovo cemo pojasniti
    # 'in stock'
    # 'available for order'
    # 'out of stock'
    # 'preorder'
    # 'auto manage inventory - available for order' (poduct is 'available for order' when inventory balance is <= 0)
    # 'auto manage inventory - out of stock' (poduct is 'out of stock' when inventory balance is <= 0)
    # https://support.google.com/merchants/answer/188494?hl=en&ref_topic=2473824
    
    _default_indexed = False
 
    # Expando
    # mozda treba uvesti customer lead time??
    # variants = ndb.KeyProperty('7', kind=DomainProductVariant, repeated=True)# soft limit 100x
    # contents = ndb.KeyProperty('8', kind=DomainProductContent, repeated=True)# soft limit 100x
    # images = ndb.LocalStructuredProperty(Image, '9', repeated=True)# soft limit 100x
    # weight = ndb.StringProperty('10')# prekompajlirana vrednost, napr: 0.2[kg] - gde je [kg] jediniva mere, ili sta vec odlucimo
    # volume = ndb.StringProperty('11')# prekompajlirana vrednost, napr: 0.03[m3] - gde je [m3] jediniva mere, ili sta vec odlucimo
    # low_stock_quantity = DecimalProperty('12', default=0.00)# notify store manager when qty drops below X quantity
    # product_instance_count = ndb.IntegerProperty('13') cuvanje ovog podatka moze biti od koristi zbog prakticnog limita broja instanci na sistemu
 
    
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
       'generate_product_instances' : 4,
    }
     

# done!
class Instance(ndb.BaseExpando):
    
    # ancestor DomainProductTemplate
    #variant_signature se gradi na osnovu ProductVariant entiteta vezanih za ProductTemplate-a (od aktuelne ProductInstance) preko ProductTemplateVariant 
    #key name ce se graditi tako sto se uradi MD5 na variant_signature
    #query ce se graditi tako sto se prvo izgradi variant_signature vrednost na osnovu odabira od strane krajnjeg korisnika a potom se ta vrednost hesira u MD5 i koristi kao key identifier
    #mana ove metode je ta sto se uvek mora izgraditi kompletan variant_signature, tj moraju se sve varijacije odabrati (svaka varianta mora biti mandatory_variant_type)
    #default vrednost code ce se graditi na osnovu sledecih informacija: ancestorkey-n, gde je n incremental integer koji se dodeljuje instanci prilikom njenog kreiranja
    #ukoliko user ne odabere multivariant opciju onda se za ProductTemplate generise samo jedna ProductInstance i njen key se gradi automatski.
    # composite index: ancestor:yes - code
    code = ndb.StringProperty('1', required=True)
    
    _default_indexed = False
 
    # Expando
    # availability = ndb.IntegerProperty('2', required=True) overide availability vrednosti sa product_template-a, inventory se uvek prati na nivou instanci, state je stavljen na template kako bi se olaksala kontrola state-ova. 
    # description = ndb.TextProperty('3', required=True)# soft limit 64kb
    # unit_price = DecimalProperty('4', required=True)
    # contents = ndb.KeyProperty('5', kind=DomainProductContent, repeated=True)# soft limit 100x
    # images = ndb.LocalStructuredProperty(Image, '6', repeated=True)# soft limit 100x
    # low_stock_quantity = DecimalProperty('7', default=0.00)# notify store manager when qty drops below X quantity
    # weight = ndb.StringProperty('8')# prekompajlirana vrednost, napr: 0.2[kg] - gde je [kg] jediniva mere, ili sta vec odlucimo
    # volume = ndb.StringProperty('9')# prekompajlirana vrednost, napr: 0.03[m3] - gde je [m3] jediniva mere, ili sta vec odlucimo
    # variant_signature = ndb.TextProperty('10', required=True)# soft limit 64kb - ova vrednost kao i vrednosti koje kupac manuelno upise kao opcije variante se prepisuju u order line description prilikom Add to Cart
 
    
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'update' : 1,
    }
  

# done! contention se moze zaobici ako write-ovi na ove entitete budu explicitno izolovani preko task queue
class InventoryLog(ndb.BaseModel):
    
    # ancestor DomainProductInstance (namespace Domain)
    # key za DomainProductInventoryLog ce se graditi na sledeci nacin:
    # key: parent=domain_product_instance.key, id=str(reference_key) ili mozda neki drugi destiled id iz key-a
    # idempotency je moguc ako se pre inserta proverava da li postoji record sa id-jem reference_key
    # not logged
    # composite index: ancestor:yes - logged:desc
    logged = ndb.DateTimeProperty('1', auto_now_add=True, required=True)
    quantity = ndb.SuperDecimalProperty('2', required=True, indexed=False)# ukljuciti index ako bude trebao za projection query
    balance = ndb.SuperDecimalProperty('3', required=True, indexed=False)# ukljuciti index ako bude trebao za projection query

# done!
class InventoryAdjustment(ndb.BaseModel):
    
    # ancestor DomainProductInstance (namespace Domain)
    # not logged ?
    adjusted = ndb.DateTimeProperty('1', auto_now_add=True, required=True, indexed=False)
    agent = ndb.KeyProperty('2', kind='core.acl.User', required=True, indexed=False)
    quantity = ndb.SuperDecimalProperty('3', required=True, indexed=False)
    comment = ndb.StringProperty('4', required=True, indexed=False)
 
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
    }
  

# done!
class Variant(ndb.BaseModel):
    
    # ancestor DomainCatalog (future - root) (namespace Domain)
    # http://v6apps.openerp.com/addon/1809
    # composite index: ancestor:yes - name
    name = ndb.StringProperty('1', required=True)
    description = ndb.TextProperty('2')# soft limit 64kb
    options = ndb.StringProperty('3', repeated=True, indexed=False)# soft limit 1000x
    allow_custom_value = ndb.BooleanProperty('4', default=False, indexed=False)# ovu vrednost buyer upisuje u definisano polje a ona se dalje prepisuje u order line description prilikom Add to Cart
  
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
    }
   

# done!
class Content(ndb.BaseModel):
    
    # ancestor DomainCatalog (future - root) (namespace Domain)
    # composite index: ancestor:yes - title
    title = ndb.StringProperty('1', required=True)
    body = ndb.TextProperty('2', required=True)
 
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
    }