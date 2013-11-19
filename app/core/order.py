# -*- coding: utf-8 -*-
'''
Created on Oct 20, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
from app import ndb

class OrderCurrency(ndb.BaseModel):
    
    KIND_ID = 27
    
    # LocalStructuredProperty model
    # http://hg.tryton.org/modules/currency/file/tip/currency.py#l14
    # http://en.wikipedia.org/wiki/ISO_4217
    # http://hg.tryton.org/modules/currency/file/tip/currency.xml#l107
    # http://bazaar.launchpad.net/~openerp/openobject-server/7.0/view/head:/openerp/addons/base/res/res_currency.py#L32
    name = ndb.SuperStringProperty('1', required=True, indexed=False)
    symbol = ndb.SuperStringProperty('2', required=True, indexed=False)
    code = ndb.SuperStringProperty('3', required=True, indexed=False)
    numeric_code = ndb.SuperStringProperty('4', indexed=False)
    rounding = ndb.SuperDecimalProperty('5', required=True, indexed=False)
    digits = ndb.SuperIntegerProperty('6', required=True, indexed=False)
    #formating
    grouping = ndb.SuperStringProperty('7', required=True, indexed=False)
    decimal_separator = ndb.SuperStringProperty('8', required=True, indexed=False)
    thousands_separator = ndb.SuperStringProperty('9', indexed=False)
    positive_sign_position = ndb.SuperIntegerProperty('10', required=True, indexed=False)
    negative_sign_position = ndb.SuperIntegerProperty('11', required=True, indexed=False)
    positive_sign = ndb.SuperStringProperty('12', indexed=False)
    negative_sign = ndb.SuperStringProperty('13', indexed=False)
    positive_currency_symbol_precedes = ndb.SuperBooleanProperty('14', default=True, indexed=False)
    negative_currency_symbol_precedes = ndb.SuperBooleanProperty('15', default=True, indexed=False)
    positive_separate_by_space = ndb.SuperBooleanProperty('16', default=True, indexed=False)
    negative_separate_by_space = ndb.SuperBooleanProperty('17', default=True, indexed=False)

class Order(ndb.BaseExpando, ndb.Workflow):
    
    KIND_ID = 28
    
    # ancestor User (namespace Domain) ovaj koncept ne radi, morace da se promeni...
    # http://hg.tryton.org/modules/sale/file/tip/sale.py#l33
    # http://hg.tryton.org/modules/purchase/file/tip/purchase.py#l32
    # http://doc.tryton.org/2.8/modules/sale/doc/index.html
    # http://doc.tryton.org/2.8/modules/purchase/doc/index.html
    # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/sale/sale.py#L48
    # buyer = ndb.KeyProperty('1', kind=User, required=True)
    # composite index: 
    # ancestor:no - store,state,updated:desc; ancestor:no - store,state,order_date:desc
    # ancestor:no - state,updated:desc; ancestor:no - state,order_date:desc
    # ancestor:yes - state,updated:desc; ancestor:yes - state,order_date:desc
    company = ndb.SuperKeyProperty('1', kind='app.domain.sale.Company', required=True)
    order_date = ndb.SuperDateTimeProperty('2', auto_now_add=True)# updated on checkout / or on completed ?
    currency = ndb.SuperLocalStructuredProperty(OrderCurrency, '3', required=True)
    untaxed_amount = ndb.SuperDecimalProperty('4', required=True, indexed=False)
    tax_amount = ndb.SuperDecimalProperty('5', required=True, indexed=False)
    total_amount = ndb.SuperDecimalProperty('6', required=True)
    state = ndb.SuperIntegerProperty('7', required=True) 
    updated = ndb.SuperDateTimeProperty('8', auto_now=True)
    _default_indexed = False
 
    # Expando
    # reference = ndb.SuperStringProperty('9', required=True)
    # company_address = ndb.SuperLocalStructuredProperty(OrderAddress, '10', required=True)
    # billing_address = ndb.SuperLocalStructuredProperty(OrderAddress, '11', required=True)
    # shipping_address = ndb.SuperLocalStructuredProperty(OrderAddress, '12', required=True)
    # company_address_reference = ndb.SuperKeyProperty('13', kind=Store, required=True)
    # billing_address_reference = ndb.SuperKeyProperty('14', kind=BuyerAddress, required=True)
    # shipping_address_reference = ndb.SuperKeyProperty('15', kind=BuyerAddress, required=True)
    # carrier_reference = ndb.SuperKeyProperty('16', kind=StoreCarrier, required=True)
    # feedback = ndb.SuperIntegerProperty('17', required=True) # ako OrderFeedback jos nije napravljen onda ovo polje nije definisano, a sistem to interpretira kao 'not provided'
    # store_name = ndb.SuperStringProperty('18', required=True)# testirati da li ovo indexiranje radi, tj overrid-a _default_indexed = False
    # store_logo = blobstore.BlobKeyProperty('19', required=True)# testirati da li ovo indexiranje radi, tj overrid-a _default_indexed = False
    # paypal_email = ndb.SuperStringProperty('20', required=True)
    # paypal_payment_status = ndb.SuperStringProperty('21', required=True)
 
    
    OBJECT_DEFAULT_STATE = 'cart'
    
    OBJECT_STATES = {
        # tuple represents (state_code, transition_name)
        # second value represents which transition will be called for changing the state
        # Ne znam da li je predvidjeno ovde da moze biti vise tranzicija/akcija koje vode do istog state-a,
        # sto ce biti slucaj sa verovatno mnogim modelima.
        # broj 0 je rezervisan za none (Stateless Models) i ne koristi se za definiciju validnih state-ova
        'cart' : (1, ),# buyer can create order, add/update (quantity)/remove order lines;
        'checkout' : (2, ),# buyer can cancel/pay order, post messages;
        'processing' : (3, ),# no one can cancel/edit/delete order lines;
        'completed' : (4, ),# no one can cancel/edit/delete order lines;
        'canceled' : (5, ),# no one can cancel/edit/delete order lines;
    }
    
    OBJECT_ACTIONS = {
       'add_to_cart' : 1,
       'update_cart' : 2,
       'checkout' : 3,
       'cancel' : 4,
       'pay' : 5,
       'timeout' : 6,
       'complete' : 7,
       'message' : 8,
    }
    
    OBJECT_TRANSITIONS = {
        'checkout' : {
            'from' : ('cart',),
            'to' : ('checkout',),
         },
         'cancel' : {
           'from' : ('checkout',),
           'to'   : ('canceled',),
        },
        'pay' : {
           'from' : ('checkout',),
           'to'   : ('processing',),
        },
        'timeout' : {
           'from' : ('processing',),
           'to'   : ('checkout',),
        },
        'complete' : {
           'from' : ('processing', ),
           'to'   : ('completed',),
        },
    }

# done! - ovaj model se verovatno izbacuje
class BillingOrder(ndb.BaseExpando):
    
    KIND_ID = 29
    
    # root (namespace Domain)
    # http://hg.tryton.org/modules/sale/file/tip/sale.py#l28
    # http://hg.tryton.org/modules/purchase/file/tip/purchase.py#l32
    # http://doc.tryton.org/2.8/modules/sale/doc/index.html
    # http://doc.tryton.org/2.8/modules/purchase/doc/index.html
    # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/sale/sale.py#L48
    order_date = ndb.SuperDateTimeProperty('1', auto_now_add=True, indexed=False)# updated on checkout
    currency = ndb.SuperLocalStructuredProperty(OrderCurrency, '2', required=True)
    untaxed_amount = ndb.SuperDecimalProperty('3', required=True, indexed=False)
    tax_amount = ndb.SuperDecimalProperty('4', required=True, indexed=False)
    total_amount = ndb.SuperDecimalProperty('5', required=True, indexed=False)
    state = ndb.SuperIntegerProperty('6', required=True, indexed=False) 
    updated = ndb.SuperDateTimeProperty('7', auto_now=True, indexed=False)
    
    _default_indexed = False
 
    # Expando
    # company_address = ndb.LocalStructuredProperty(OrderAddress, '8', required=True)
    # billing_address = ndb.LocalStructuredProperty(OrderAddress, '9', required=True)
    # shipping_address = ndb.LocalStructuredProperty(OrderAddress, '10', required=True)
    # reference = ndb.StringProperty('11', required=True)
    
    # ovaj model za sada postoji dok ne budemo videli kako ce Order izgledati
    # cilj nam je da BillingOrder izbacimo
    # ako razlike budu zanemarljive u pogledu Order-a i BillingOrder-a onda cemo BillingOrder izbaciti
    # trebamo jos da utvrdimo koji je diference u funkcijama izmedju ORder-a i BillingOrder-a
    # razlika u funkcijama izmedju Order-a i Billing order-a bi trebala da je mala
    # za sada se zna da ce BillingOrder uvek imati samo jedan OrderLine,
    # i da ce OrderLine uvek imati sledece konstante:
    # OrderLine(quantity=1, product_uom=Unit, discount=0.00, sequence=1)

# done!
class OrderAddress(ndb.BaseExpando):
    
    KIND_ID = 30
    
    # LocalStructuredProperty model
    name = ndb.SuperStringProperty('1', required=True, indexed=False)
    country = ndb.SuperStringProperty('2', required=True, indexed=False)
    country_code = ndb.SuperStringProperty('3', required=True, indexed=False)
    region = ndb.SuperStringProperty('4', required=True, indexed=False)
    region_code = ndb.SuperStringProperty('5', required=True, indexed=False)
    city = ndb.SuperStringProperty('6', required=True, indexed=False)
    postal_code = ndb.SuperStringProperty('7', required=True, indexed=False)
    street_address = ndb.SuperStringProperty('8', required=True, indexed=False)
    
    _default_indexed = False
 
    # Expando
    # street_address2 = ndb.StringProperty('9') # ovo polje verovatno ne treba, s obzirom da je u street_address dozvoljeno 500 karaktera 
    # email = ndb.StringProperty('10')
    # telephone = ndb.StringProperty('11')
 

class OrderLineProductUOM(ndb.BaseModel):
    
    KIND_ID = 31
    
    # LocalStructuredProperty model
    # http://hg.tryton.org/modules/product/file/tip/uom.py#l28
    # http://hg.tryton.org/modules/product/file/tip/uom.xml#l63 - http://hg.tryton.org/modules/product/file/tip/uom.xml#l312
    # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/product/product.py#L89
    name = ndb.SuperStringProperty('1', required=True, indexed=False)
    symbol = ndb.SuperStringProperty('2', required=True, indexed=False)
    category = ndb.SuperStringProperty('3', required=True, indexed=False)# ProductUOMCategory.name
    rounding = ndb.SuperDecimalProperty('4', required=True, indexed=False)
    digits = ndb.SuperIntegerProperty('5', required=True, indexed=False)
    

# done!
class OrderLine(ndb.BaseExpando):
    
    KIND_ID = 32
    
    # ancestor Order, BillingOrder
    # u slucaju Order-a, key za OrderLine ce se graditi na sledeci nacin:
    # key: parent=order_key, id=catalog_namespace-catalog_id-product_template_id-product_instance_id
    # iz id-ja se kasnije moze graditi link za referenciranje product_instance, pa je stoga nemoguce koristiti md5 za hashiranje id-a
    # u slucaju BillingOrder-a, key za OrderLine ce se graditi na sledeci nacin:
    # key: parent=billing_order_id, id=paypal_transaction_log_id ?
    # http://hg.tryton.org/modules/sale/file/tip/sale.py#l888
    # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/sale/sale.py#L649
    # composite index: ancestor:yes - sequence
    description = ndb.SuperTextProperty('1', required=True)# soft limit 64kb
    quantity = ndb.SuperDecimalProperty('2', required=True, indexed=False)
    product_uom = ndb.SuperLocalStructuredProperty(OrderLineProductUOM, '3', required=True)
    unit_price = ndb.SuperDecimalProperty('4', required=True, indexed=False)
    discount = ndb.SuperDecimalProperty('5', default=0.00, indexed=False)
    sequence = ndb.SuperIntegerProperty('6', required=True)
    
    _default_indexed = False
 
    # Expando
    # taxes = ndb.LocalStructuredProperty(OrderLineTax, '7', repeated=True)# soft limit 500x
    # product_category_complete_name = ndb.TextProperty('8', required=True)# soft limit 64kb
    # product_category = ndb.KeyProperty('9', kind=ProductCategory, required=True)
    # catalog_pricetag_reference = ndb.KeyProperty('10', kind=DomainCatalogPricetag, required=True)
    # product_instance_reference = ndb.KeyProperty('11', kind=DomainProductInstance, required=True)
    # tax_references = ndb.KeyProperty('12', kind=StoreTax, repeated=True)# soft limit 500x

# done!
class OrderLineTax(ndb.BaseModel):
    
    KIND_ID = 33
    
    # LocalStructuredProperty model
    # http://hg.tryton.org/modules/account/file/tip/tax.py#l545
    name = ndb.SuperStringProperty('1', required=True, indexed=False)
    amount = ndb.SuperStringProperty('2', required=True, indexed=False)# prekompajlirane vrednosti iz UI, napr: 17.00[%] ili 10.00[c] gde je [c] = currency

# done! - sudo kontrolisan model
class OrderFeedback(ndb.BaseModel, ndb.Workflow):
    
    KIND_ID = 34
    
    # ancestor Order
    # key: parent=order_key, id=order_id
    # ako hocemo da dozvolimo sva sortiranja, i dodatni filter po state-u uz sortiranje, onda nam trebaju slecedi indexi
    # composite index:
    # ancestor:yes - updated:desc; ancestor:yes - created:desc;
    # ancestor:yes - state,updated:desc; ancestor:yes - state,created:desc
    state = ndb.SuperIntegerProperty('1', required=True, indexed=False)
    updated = ndb.SuperDateTimeProperty('2', auto_now=True)
    created = ndb.SuperDateTimeProperty('3', auto_now_add=True)
 
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_STATES = {
        # tuple represents (state_code, transition_name)
        # second value represents which transition will be called for changing the state
        # ne znam da li je predvidjeno ovde da moze biti vise tranzicija/akcija koje vode do istog state-a,
        # sto ce biti slucaj sa verovatno mnogim modelima.
        # broj 0 je rezervisan za state none (Stateless Models) i ne koristi se za definiciju validnih state-ova
        'positive' : (1, ),
        'neutral' : (2, ),
        'negative' : (3, ),
        'revision' : (4, ),
        'reported' : (5, ),
        'su_positive' : (6, ),
        'su_neutral' : (7, ),
        'su_negative' : (8, ),
        # mozda nam bude trebao i su_invisible state kako bi mogli da uticemo na vidljivost pojedinacnih OrderFeedback-ova
    }
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'log_message' : 2,
       'review' : 3,
       'report' : 4,
       'revision_feedback' : 5,
       'sudo' : 6,
       'invisible' : 7,
    }
    
    OBJECT_TRANSITIONS = {
        'review' : {
            'from' : ('positive', 'neutral', 'negative',),
            'to' : ('revision',),
         },
        'report' : {
           'from' : ('positive', 'neutral', 'negative', 'revision',),
           'to'   : ('reported',),
        },
        'revision_feedback' : {
           'from' : ('revision',),
           'to'   : ('positive', 'neutral', 'negative',),
        },
        'su_feedback' : {
           'from' : ('positive', 'neutral', 'negative', 'revision', 'reported', 'su_positive', 'su_neutral', 'su_negative',),
           'to'   : ('su_positive', 'su_neutral', 'su_negative',),
        },
    }