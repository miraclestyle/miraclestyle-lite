class DomainProductTemplate(ndb.Expando):
    
    # ancestor DomainCatalog (future - root / namespace Domain)
    # composite index: ancestor:yes - name
    product_category = ndb.KeyProperty('1', kind=ProductCategory, required=True, indexed=False)
    name = ndb.StringProperty('2', required=True)
    description = ndb.TextProperty('3', required=True)# soft limit 64kb
    product_uom = ndb.KeyProperty('4', kind=ProductUOM, required=True, indexed=False)
    unit_price = DecimalProperty('5', required=True)
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
    pass
    # Expando
    # mozda treba uvesti customer lead time??
    # variants = ndb.KeyProperty('7', kind=DomainProductVariant, repeated=True)# soft limit 100x
    # contents = ndb.KeyProperty('8', kind=DomainProductContent, repeated=True)# soft limit 100x
    # images = ndb.LocalStructuredProperty(Image, '9', repeated=True)# soft limit 100x
    # weight = ndb.StringProperty('10')# prekompajlirana vrednost, napr: 0.2[kg] - gde je [kg] jediniva mere, ili sta vec odlucimo
    # volume = ndb.StringProperty('11')# prekompajlirana vrednost, napr: 0.03[m3] - gde je [m3] jediniva mere, ili sta vec odlucimo
    # low_stock_quantity = DecimalProperty('12', default=0.00)# notify store manager when qty drops below X quantity
    # product_instance_count = ndb.IntegerProperty('13') cuvanje ovog podatka moze biti od koristi zbog prakticnog limita broja instanci na sistemu

class DomainProductInstance(ndb.Expando):
    
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
    pass
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

class OrderLine(ndb.Expando):
    
    # ancestor Order, BillingOrder
    # u slucaju Order-a, key za OrderLine ce se graditi na sledeci nacin:
    # key: parent=order_key, id=catalog_namespace-catalog_id-product_template_id-product_instance_id
    # iz id-ja se kasnije moze graditi link za referenciranje product_instance, pa je stoga nemoguce koristiti md5 za hashiranje id-a
    # u slucaju BillingOrder-a, key za OrderLine ce se graditi na sledeci nacin:
    # key: parent=billing_order_id, id=paypal_transaction_log_id ?
    # http://hg.tryton.org/modules/sale/file/tip/sale.py#l888
    # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/sale/sale.py#L649
    # composite index: ancestor:yes - sequence
    description = ndb.TextProperty('1', required=True)# soft limit 64kb
    quantity = DecimalProperty('2', required=True, indexed=False)
    product_uom = ndb.LocalStructuredProperty(OrderLineProductUOM, '3', required=True)
    unit_price = DecimalProperty('4', required=True, indexed=False)
    discount = DecimalProperty('5', default=0.00, indexed=False)
    sequence = ndb.IntegerProperty('6', required=True)
    _default_indexed = False
    pass
    # Expando
    # taxes = ndb.LocalStructuredProperty(OrderLineTax, '7', repeated=True)# soft limit 500x
    # product_category_complete_name = ndb.TextProperty('8', required=True)# soft limit 64kb
    # product_category = ndb.KeyProperty('9', kind=ProductCategory, required=True)
    # catalog_pricetag_reference = ndb.KeyProperty('10', kind=DomainCatalogPricetag, required=True)
    # tax_references = ndb.KeyProperty('12', kind=StoreTax, repeated=True)# soft limit 500x


class OrderLineTax(ndb.Model):
    
    # LocalStructuredProperty model
    # http://hg.tryton.org/modules/account/file/tip/tax.py#l545
    name = ndb.StringProperty('1', required=True, indexed=False)
    amount = ndb.StringProperty('2', required=True, indexed=False)# prekompajlirane vrednosti iz UI, napr: 17.00[%] ili 10.00[c] gde je [c] = currency

class DomainTax(ndb.Expando):
    
    # root (namespace Domain)
    # composite index: ancestor:no - active,sequence
    name = ndb.StringProperty('1', required=True)
    sequence = ndb.IntegerProperty('2', required=True)
    amount = ndb.StringProperty('3', required=True, indexed=False)# prekompajlirane vrednosti iz UI, napr: 17.00[%] ili 10.00[c] gde je [c] = currency
    location_exclusion = ndb.BooleanProperty('4', default=False, indexed=False)# applies to all locations except/applies to all locations listed below
    active = ndb.BooleanProperty('5', default=True)
    _default_indexed = False
    pass
    # Expando
    # locations = ndb.LocalStructuredProperty(Location, '6', repeated=True)# soft limit 300x
    # product_categories = ndb.KeyProperty('7', kind=ProductCategory, repeated=True)# soft limit 100x
    # carriers = ndb.KeyProperty('8', kind=DomainCarrier, repeated=True)# soft limit 100x


class Order(ndb.Expando):
    
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
    store = ndb.KeyProperty('1', kind=Store, required=True)
    order_date = ndb.DateTimeProperty('2', auto_now_add=True, required=True)# updated on checkout
    currency = ndb.LocalStructuredProperty(OrderCurrency, '3', required=True)
    untaxed_amount = DecimalProperty('4', required=True, indexed=False)
    tax_amount = DecimalProperty('5', required=True, indexed=False)
    total_amount = DecimalProperty('6', required=True)
    state = ndb.IntegerProperty('7', required=True) 
    updated = ndb.DateTimeProperty('8', auto_now=True, required=True)
    _default_indexed = False
    pass
    # Expando
    # company_address = ndb.LocalStructuredProperty(OrderAddress, '9', required=True)
    # billing_address = ndb.LocalStructuredProperty(OrderAddress, '10', required=True)
    # shipping_address = ndb.LocalStructuredProperty(OrderAddress, '11', required=True)
    # reference = ndb.StringProperty('12', required=True)
    # comment = ndb.TextProperty('13')# 64kb limit
    # company_address_reference = ndb.KeyProperty('14', kind=Store, required=True)
    # billing_address_reference = ndb.KeyProperty('15', kind=BuyerAddress, required=True)
    # shipping_address_reference = ndb.KeyProperty('16', kind=BuyerAddress, required=True)
    # carrier_reference = ndb.KeyProperty('17', kind=StoreCarrier, required=True)
    # feedback = ndb.IntegerProperty('18', required=True)
    # store_name = ndb.StringProperty('19', required=True, indexed=True)# testirati da li ovo indexiranje radi, tj overrid-a _default_indexed = False
    # store_logo = blobstore.BlobKeyProperty('20', required=True, indexed=True)# testirati da li ovo indexiranje radi, tj overrid-a _default_indexed = False

class OrderAddress(ndb.Expando):
    
    # LocalStructuredProperty model
    name = ndb.StringProperty('1', required=True, indexed=False)
    country = ndb.StringProperty('2', required=True, indexed=False)
    country_code = ndb.StringProperty('3', required=True, indexed=False)
    region = ndb.StringProperty('4', required=True, indexed=False)
    region_code = ndb.StringProperty('5', required=True, indexed=False)
    city = ndb.StringProperty('6', required=True, indexed=False)
    postal_code = ndb.StringProperty('7', required=True, indexed=False)
    street_address = ndb.StringProperty('8', required=True, indexed=False)
    _default_indexed = False
    pass
    # Expando
    # street_address2 = ndb.StringProperty('9')
    # email = ndb.StringProperty('10')
    # telephone = ndb.StringProperty('11')
class DomainStore(ndb.Expando):
    
    # root (namespace Domain)
    # composite index: ancestor:no - state,name
    name = ndb.StringProperty('1', required=True)
    logo = blobstore.BlobKeyProperty('2', required=True)# blob ce se implementirati na GCS
    state = ndb.IntegerProperty('3', required=True)
    _default_indexed = False
    pass
    #Expando
    #
    # Company
    # company_name = ndb.StringProperty('4', required=True)
    # company_country = ndb.KeyProperty('5', kind=Country, required=True)
    # company_region = ndb.KeyProperty('6', kind=CountrySubdivision, required=True)# ako je potreban string val onda se ovo preskace 
    # company_region = ndb.StringProperty('6', required=True)# ako je potreban key val onda se ovo preskace
    # company_city = ndb.StringProperty('7', required=True)
    # company_postal_code = ndb.StringProperty('8', required=True)
    # company_street_address = ndb.StringProperty('9', required=True)
    # company_street_address2 = ndb.StringProperty('10')
    # company_email = ndb.StringProperty('11')
    # company_telephone = ndb.StringProperty('12')
    #
    # Payment
    # currency = ndb.KeyProperty('13', kind=Currency, required=True)
    # tax_buyer_on ?
    # paypal_email = ndb.StringProperty('14')
    # paypal_shipping ?
    #
    # Analytics 
    # tracking_id = ndb.StringProperty('15')
    #
    # Feedback
    # feedbacks = ndb.LocalStructuredProperty(StoreFeedback, '16', repeated=True)# soft limit 120x
    #
    # Shipping Exclusion Settings
    # Shipping everywhere except at the following locations: location_exclusion = False
    # Shipping only at the following locations: location_exclusion = True
    # location_exclusion = ndb.BooleanProperty('17', default=False)

class CountrySubdivision(ndb.Model):
    
    # ancestor Country
    # http://hg.tryton.org/modules/country/file/tip/country.py#l52
    # http://bazaar.launchpad.net/~openerp/openobject-server/7.0/view/head:/openerp/addons/base/res/res_country.py#L86
    # koliko cemo drilldown u ovoj strukturi zavisi od kasnijih odluka u vezi povezivanja lokativnih informacija sa informacijama ovog modela..
    # composite index: ancestor:yes - name; ancestor:yes - active,name
    parent_record = ndb.KeyProperty('1', kind=CountrySubdivision, indexed=False)
    code = ndb.StringProperty('2', required=True, indexed=False)# ukljuciti index ako bude trebao za projection query
    name = ndb.StringProperty('3', required=True)
    type = ndb.IntegerProperty('4', required=True, indexed=False)
    active = ndb.BooleanProperty('5', default=True)

class BuyerAddress(ndb.Expando):
    
    # ancestor User
    # composite index: ancestor:yes - name
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
    # region = ndb.KeyProperty('8', kind=CountrySubdivision, required=True)# ako je potreban string val onda se ovo preskace / tryton ima CountrySubdivision za skoro sve zemlje 
    # region = ndb.StringProperty('8', required=True)# ako je potreban key val onda se ovo preskace / tryton ima CountrySubdivision za skoro sve zemlje
    # street_address2 = ndb.StringProperty('9')
    # email = ndb.StringProperty('10')
    # telephone = ndb.StringProperty('11')








