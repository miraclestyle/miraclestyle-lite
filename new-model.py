#coding=UTF-8

#MASTER MODEL FILE

# NAPOMENA!!! - Sve mapirane informacije koje se snimaju u datastore trebaju biti hardcoded, tj. u samom aplikativnom codu a ne u settings.py
# u settings.py se cuvaju one informacije koje se ne cuvaju u datastore i koje se ne koriste u izgradnji datastore recorda...

# pitanje je da li ce nam trebati composite indexi za query-je poput:
# BuyerAddress.query(ancestor=key).order(BuyerAddress.name) ili AggregateUserPermission.query(AggregateUserPermission.reference == key, ancestor=key)
# ali je highly unlikely, zato sto se ancestor ne mora ukljucivati u slucajevima composite indexa
# odgovor na gore postavljeno pitanje se mozda moze pronaci na: 
# https://developers.google.com/appengine/docs/python/datastore/indexes#Python_Index_configuration
# https://github.com/GoogleCloudPlatform/appengine-guestbook-python
# za sada smo resili osnovne query-je sa composite indexima koji podrazumevaju ancestor filtere,
# pa mozemo kasnije tokom razvoja funkcionalne logike to dalje unaprediti.

# datastore ne podrzava LIKE statement kao sto to podrzavaju struktuirane baze, umesto LIKE se moze korititi index range scan, kao napr:
# SELECT * FROM Country WHERE name >= 'B' AND name < 'C' ORDER BY name
# mnogi modeli koji ce imati opciju pretraga po osnovu user custom entry-ja ce koristiti ovaj mehanizam,
# i na njima se moraju pripremiti indexi za ove funkcije.

# treba se ispitati "_default_indexed = False" za Expando modele

# problem 1 write per sec unutar transakcija kojie se commitaju na jednu entity grupu se treba normalizovati.
# ovaj problem se odnosi na broj write operacija koje se mogu odvijati na istoj entity grupi.
# jedan primer gde ovaj problem moze postojati je u slucaju AggregateBuyerCollectionCatalog!!

# detalji oko modeliranja podataka i skaliranja su prezentirani na dole navedenim linkovima
# https://developers.google.com/appengine/articles/datastore/overview
# https://developers.google.com/appengine/articles/scaling/overview

# skontati idempotency modela koji ce ucestvovati u transakcijama (ovo je najbolje uraditi u fazi razvoja funkcionalne logike)
# idempotency se odnosi na sve modele, i treba nastojati uciniti sve transakcije idempotent-ne, u najmanju ruku, kada je to moguce!

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
# DOMAIN - 20
################################################################################

# done! - ovde ce nam trebati kontrola
class Domain(ndb.Expando):
    
    # root
    # composite index: ancestor:no - state,name
    name = ndb.StringProperty('1', required=True)
    primary_contact = ndb.KeyProperty('2', kind=User, required=True, indexed=False)
    state = ndb.IntegerProperty('3', required=True)
    _default_indexed = False
    pass
    #Expando
    
    _KIND = 0
    
    OBJECT_DEFAULT_STATE = 'active'
    
    OBJECT_STATES = {
        # tuple represents (state_code, transition_name)
        # second value represents which transition will be called for changing the state
        # Ne znam da li je predvidjeno ovde da moze biti vise tranzicija/akcija koje vode do istog state-a,
        # sto ce biti slucaj sa verovatno mnogim modelima.
        # broj 0 je rezervisan za none (Stateless Models) i ne koristi se za definiciju validnih state-ova
        'active' : (1, ),
        'suspended' : (2, ),
    }
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'suspend' : 3,
       'activate' : 4,
    }
    
    OBJECT_TRANSITIONS = {
        'activate' : {
            'from' : ('suspended',),
            'to' : ('active',),
         },
        'suspend' : {
           'from' : ('active', ),
           'to'   : ('suspended',),
        },
    }
    
    # Ova akcija kreira novu domenu.
    @ndb.transactional
    def create():
        # ovu akciju moze izvrsiti samo registrovani autenticirani agent.
        domain = Domain(name='deskriptivno ime po zelji kreatora', primary_contact=user_key, state='active')
        domain_key = domain.put()
        object_log = ObjectLog(parent=domain_key, agent=user_key, action='create', state=domain.state, log=domain)
        object_log.put()
        role = Role(namespace=domain_key, name='Domain Admins', permissions=['*',], readonly=True)
        role_key = role.put()
        role_user = RoleUser(parent=role_key, user=user_key, state='accepted')
        role_user_key = role_user.put()
        user_role = Role(namespace=domain_key, parent=role_user.user, id=str(role_key.id()), name='Domain Admins', permissions=['*',], readonly=True)
        user_role.put()
    
    # Ova akcija azurira postojecu domenu.
    @ndb.transactional
    def update():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'update-Domain'.
        # akcija se moze pozvati samo ako je domain.state == 'active'.
        domain.name = 'promenjeno ime od strane administratora domene'
        domain.primary_contact = agent_key # u ovaj prop. se moze upisati samo key user-a koji ima domain-specific dozvolu 'manage_security-Domain'. ? provericemo kako je to na google apps
        domain_key = domain.put()
        object_log = ObjectLog(parent=domain_key, agent=agent_key, action='update', state=domain.state, log=domain)
        object_log.put()
    
    # Ova akcija suspenduje aktivnu domenu. Ovde cemo dalje opisati posledice suspenzije
    @ndb.transactional
    def suspend():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'suspend-Domain'.
        # akcija se moze pozvati samo ako je domain.state == 'active'.
        domain.state = 'suspended'
        domain_key = domain.put()
        object_log = ObjectLog(parent=domain_key, agent=agent_key, action='suspend', state=domain.state, message='poruka od agenta - obavezno polje!', note='privatni komentar agenta (dostupan samo privilegovanim agentima) - obavezno polje!')
        object_log.put()
    
    # Ova akcija aktivira suspendovanu domenu. Ovde cemo dalje opisati posledice aktivacije
    @ndb.transactional
    def activate():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'activate-Domain'.
        # akcija se moze pozvati samo ako je domain.state == 'suspended'.
        domain.state = 'active'
        domain_key = domain.put()
        object_log = ObjectLog(parent=domain_key, agent=agent_key, action='activate', state=domain.state, message='poruka od agenta - obavezno polje!', note='privatni komentar agenta (dostupan samo privilegovanim agentima) - obavezno polje!')
        object_log.put()

# done! mozda napraviti DomainUser u kojem je repeated prop. Roles, i onda u Expando od User modela dodati struct prop Roles(Domain, Roles)?
class Role(ndb.Model):
    
    # root (namespace Domain)
    # ancestor User (for caching/optimization purposes) - Role(namespace=domain_key, parent=user_key, id=str(role_key.id()), ....)
    # TREBA TESTIRATI DA LI RADE QUERY: Role.query(namespace=..., ancestor=..., id=....)
    # mozda bude trebalo jos indexa u zavistnosti od potreba u UIUX
    # composite index: ancestor:yes - name
    name = ndb.StringProperty('1', required=True)
    permissions = ndb.StringProperty('2', repeated=True, indexed=False)# soft limit 1000x - action-Model - create-Store
    readonly = ndb.BooleanProperty('3', default=True, indexed=False)
    
    _KIND = 0
    
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    }
    
    # Pravi novu rolu
    @ndb.transactional
    def create():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'create-Role'. 
        # akcija se moze pozvati samo ako je domain.state == 'active'.
        role = Role(name='Store Managers', permissions=['create_store', 'update_store',], readonly=False) # readonly je uvek False za user generated Roles
        role_key = role.put()
        object_log = ObjectLog(parent=role_key, agent=agent_key, action='create', state='none', log=role)
        object_log.put()
    
    # Azurira postojecu rolu
    @ndb.transactional
    def update():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'update-Role'.
        # akcija se moze pozvati samo ako je domain.state == 'active'.
        role.name = 'New Store Managers'
        role.permissions = ['create_store',]
        role_key = role.put()
        object_log = ObjectLog(parent=role_key, agent=agent_key, action='update', state='none', log=role)
        object_log.put()
        role_users = RoleUser.query(ancestor=role_key).fetch(projection=[RoleUser.user,])
        # ovo uraditi sa taskletima u async radi optimizacije
        for role_user in role_users:
            key = ndb.Key(namespace=domain_key, parent=role_user, str(role_key.id()))
            user_role = key.get()
            user_role.name = role.name
            user_role.permissions = role.permissions
            user_role.put()
    
    # Brise postojecu rolu
    @ndb.transactional
    def delete():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'delete-Role'.
        # akcija se moze pozvati samo ako je domain.state == 'active'.
        object_log = ObjectLog(parent=role_key, agent=agent_key, action='delete', state='none')
        object_log.put()
        role_users = RoleUser.query(ancestor=role_key).fetch(projection=[RoleUser.user,])
        roles = []
        for role_user in role_users:
            key = ndb.Key(namespace=domain_key, parent=role_user, str(role_key.id()))
            roles.append(key)
        ndb.delete_multi(roles)
        ndb.delete_multi(role_users)
        role_key.delete()

# done!
class RoleUser(ndb.Model):
    
    # ancestor Role (namespace Domain) - id = str(user_key.id())
    # mozda bude trebalo jos indexa u zavistnosti od potreba u UIUX
    # composite index: ancestor:yes - user
    user = ndb.KeyProperty('1', kind=User, required=True)
    state = ndb.IntegerProperty('2', required=True)# invited/accepted
    
    _KIND = 0
    
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_STATES = {
        # tuple represents (state_code, transition_name)
        # second value represents which transition will be called for changing the state
        # Ne znam da li je predvidjeno ovde da moze biti vise tranzicija/akcija koje vode do istog state-a,
        # sto ce biti slucaj sa verovatno mnogim modelima.
        # broj 0 je rezervisan za none (Stateless Models) i ne koristi se za definiciju validnih state-ova
        'invited' : (1, ),
        'accepted' : (2, ),
    }
    
    OBJECT_ACTIONS = {
       'invite' : 1,
       'remove' : 2,
       'accept' : 3,
    }
    
    OBJECT_TRANSITIONS = {
        'accept' : {
            'from' : ('invited',),
            'to' : ('accepted',),
        },
    }
    
    # Poziva novog usera u rolu
    @ndb.transactional
    def invite():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'invite-RoleUser'.
        # akcija se moze pozvati samo ako je domain.state == 'active'.
        role_user = RoleUser(parent=role_key, id='123673472829', user='123673472829', state='invited')
        role_user_key = role_user.put()
        object_log = ObjectLog(parent=role_user_key, agent=agent_key, action='invite', state=role_user.state, log=role_user)
        object_log.put()
        # salje se notifikacija korisniku da je dobio poziv za dodavanje u Rolu.
    
    # Uklanja postojeceg usera iz role
    @ndb.transactional
    def remove():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'remove-RoleUser', ili agent koji je referenciran u entitetu (role_user.user == agent).
        # agent koji je referenciran u domain.primary_contact prop. ne moze izgubiti dozvole za upravljanje domenom.
        # akcija se moze pozvati samo ako je domain.state == 'active'.
        object_log = ObjectLog(parent=role_user_key, agent=agent_key, action='remove', state=role_user.state)
        object_log.put()
        role_user_key.delete()
        key = ndb.Key(namespace=domain_key, parent=role_user.user, str(role_key.id()))
        # ovaj delete nece uspeti ukoliko entitet ne postoji, napr: ako je role_user.state == 'invited'
        key.delete()
    
    # Prihvata poziv novog usera u rolu
    @ndb.transactional
    def accept():
        # ovu akciju moze izvrsiti samo agent koji je referenciran u entitetu (role_user.user == agent).
        # akcija se moze pozvati samo ako je domain.state == 'active'.
        role_user.state = 'accepted'
        role_user_key = role_user.put()
        object_log = ObjectLog(parent=role_user_key, agent=agent_key, action='accept', state=role_user.state)
        object_log.put()
        user_role = Role(parent=role_user.user, id=str(role_key.id()), name='~', permissions=['~',], readonly='True/False')
        user_role.put()

# future implementation - prototype!
class Rule(ndb.Model):
    
    # root (namespace Domain)
    name = ndb.StringProperty('1', required=True)
    model_kind = ndb.StringProperty('2', required=True)
    actions = ndb.StringProperty('3', repeated=True)
    fields = ndb.LocalStructuredProperty(Field, '4', repeated=True)
    condition = ndb.TextProperty('5')
    roles = ndb.KeyProperty('6', kind=Role, repeated=True)

# future implementation - prototype!
class Field(ndb.Model):
    
    # LocalStructuredProperty model
    name = ndb.StringProperty('1', required=True, indexed=False)
    writable = ndb.BooleanProperty('2', default=True, indexed=False)
    visible = ndb.BooleanProperty('3', default=True, indexed=False)

# done!
class Store(ndb.Expando):
    
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
    
    _KIND = 0
    
    OBJECT_DEFAULT_STATE = 'active'
    
    OBJECT_STATES = {
        # tuple represents (state_code, transition_name)
        # second value represents which transition will be called for changing the state
        # Ne znam da li je predvidjeno ovde da moze biti vise tranzicija/akcija koje vode do istog state-a,
        # sto ce biti slucaj sa verovatno mnogim modelima.
        # broj 0 je rezervisan za none (Stateless Models) i ne koristi se za definiciju validnih state-ova
        'open' : (1, ),
        'closed' : (2, ),
    }
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'close' : 3,
       'open' : 4,
    }
    
    OBJECT_TRANSITIONS = {
        'open' : {
            'from' : ('closed',),
            'to' : ('open',),
         },
        'close' : {
           'from' : ('open', ),
           'to'   : ('closed',),
        },
    }
    
    # Ova akcija kreira novi store.
    @ndb.transactional
    def create():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'create-Store'.
        # akcija se moze pozvati samo ako je domain.state == 'active'.
        store = Store(name=var_name, logo=var_logo, state='open')
        store_key = store.put()
        object_log = ObjectLog(parent=store_key, agent=agent_key, action='create', state=store.state, log=store)
        object_log.put()
    
    # Ova akcija azurira postojeci store.
    @ndb.transactional
    def update():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'update-Store'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i store.state == 'open'.
        store.name = var_name
        store.logo = var_logo
        store_key = store.put()
        object_log = ObjectLog(parent=store_key, agent=agent_key, action='update', state=store.state, log=store)
        object_log.put()
    
    # Ova akcija zatvara otvoren store. Ovde cemo dalje opisati posledice zatvaranja...
    @ndb.transactional
    def close():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'close-Store'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i store.state == 'open'.
        store.state = 'closed'
        store_key = store.put()
        object_log = ObjectLog(parent=store_key, agent=agent_key, action='close', state=store.state, message='poruka od agenta - obavezno polje!', note='privatni komentar agenta (dostupan samo privilegovanim agentima) - obavezno polje!')
        object_log.put()
    
    # Ova akcija otvara zatvoreni store. Ovde cemo dalje opisati posledice otvaranja...
    @ndb.transactional
    def open():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'open-Store'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i store.state == 'closed'.
        store.state = 'open'
        store_key = store.put()
        object_log = ObjectLog(parent=store_key, agent=agent_key, action='open', state=store.state, message='poruka od agenta - obavezno polje!', note='privatni komentar agenta (dostupan samo privilegovanim agentima) - obavezno polje!')
        object_log.put()

# done!
class StoreFeedback(ndb.Model):
    
    # LocalStructuredProperty model
    # ovaj model dozvoljava da se radi feedback trending per month per year
    # mozda bi se mogla povecati granulacija per week, tako da imamo oko 52 instance per year, ali mislim da je to nepotrebno!
    # ovde treba voditi racuna u scenarijima kao sto je napr. promena feedback-a iz negative u positive state,
    # tako da se za taj record uradi negative_feedback_count - 1 i positive_feedback_count + 1
    month = ndb.IntegerProperty('1', required=True, indexed=False)
    year = ndb.IntegerProperty('2', required=True, indexed=False)
    positive_feedback_count = ndb.IntegerProperty('3', required=True, indexed=False)
    negative_feedback_count = ndb.IntegerProperty('4', required=True, indexed=False)
    neutral_feedback_count = ndb.IntegerProperty('5', required=True, indexed=False)

# done!
class StoreContent(ndb.Model):
    
    # ancestor Store (Catalog, for caching) (namespace Domain)
    # composite index: ancestor:yes - sequence
    title = ndb.StringProperty('1', required=True)
    body = ndb.TextProperty('2', required=True)
    sequence = ndb.IntegerProperty('3', required=True)
    
    _KIND = 0
    
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    }
    
    # Ova akcija kreira novi store content.
    @ndb.transactional
    def create():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'create-StoreContent'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i store.state == 'open'.
        store_content = StoreContent(parent=store_key, title=var_title, body=var_body, sequence=var_sequence)
        store_content_key = store_content.put()
        object_log = ObjectLog(parent=store_content_key, agent=agent_key, action='create', state='none', log=store_content)
        object_log.put()
    
    # Ova akcija azurira store content.
    @ndb.transactional
    def update():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'update-StoreContent'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i store.state == 'open'.
        store_content.title = var_title
        store_content.body = var_body
        store_content.sequence = var_sequence
        store_content_key = store_content.put()
        object_log = ObjectLog(parent=store_content_key, agent=agent_key, action='update', state='none', log=store_content)
        object_log.put()
    
    # Ova akcija brise store content.
    @ndb.transactional
    def delete():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'delete-StoreContent'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i store.state == 'open'.
        object_log = ObjectLog(parent=store_content_key, agent=agent_key, action='delete', state='none')
        object_log.put()
        store_content_key.delete()

# done!
class StoreShippingExclusion(Location):
    
    # ancestor Store (Catalog, for caching) (namespace Domain)
    # ovde bi se indexi mozda mogli dobro iskoristiti?
    
    _KIND = 0
    
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    }
    
    # Ova akcija kreira novi store shipping exclusion.
    @ndb.transactional
    def create():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'create-StoreShippingExclusion'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i store.state == 'open'.
        store_shipping_exclusion = StoreShippingExclusion(parent=store_key, country=var_country)
        store_shipping_exclusion_key = store_shipping_exclusion.put()
        object_log = ObjectLog(parent=store_shipping_exclusion_key, agent=agent_key, action='create', state='none', log=store_shipping_exclusion)
        object_log.put()
    
    # Ova akcija azurira store shipping exclusion.
    @ndb.transactional
    def update():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'update-StoreShippingExclusion'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i store.state == 'open'.
        store_shipping_exclusion.country = var_country
        store_shipping_exclusion_key = store_shipping_exclusion.put()
        object_log = ObjectLog(parent=store_shipping_exclusion_key, agent=agent_key, action='update', state='none', log=store_shipping_exclusion)
        object_log.put()
    
    # Ova akcija brise store shipping exclusion.
    @ndb.transactional
    def delete():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'delete-StoreShippingExclusion'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i store.state == 'open'.
        object_log = ObjectLog(parent=store_shipping_exclusion_key, agent=agent_key, action='delete', state='none')
        object_log.put()
        store_shipping_exclusion_key.delete()

# done!
class Tax(ndb.Expando):
    
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
    # carriers = ndb.KeyProperty('8', kind=Carrier, repeated=True)# soft limit 100x
    
    _KIND = 0
    
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    }
    
    # Ova akcija kreira novu taxu.
    @ndb.transactional
    def create():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'create-Tax'.
        # akcija se moze pozvati samo ako je domain.state == 'active'.
        tax = Tax(name=var_name, sequence=var_sequence, amount=var_amount, location_exclusion=var_location_exclusion, active=True)
        tax_key = tax.put()
        object_log = ObjectLog(parent=tax_key, agent=agent_key, action='create', state='none', log=tax)
        object_log.put()
    
    # Ova akcija azurira taxu.
    @ndb.transactional
    def update():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'update-Tax'.
        # akcija se moze pozvati samo ako je domain.state == 'active'.
        tax.name = var_name
        tax.sequence = var_sequence
        tax.amount = var_amount
        tax.location_exclusion = var_location_exclusion
        tax.active = var_active
        tax_key = tax.put()
        object_log = ObjectLog(parent=tax_key, agent=agent_key, action='update', state='none', log=tax)
        object_log.put()
    
    # Ova akcija brise taxu.
    @ndb.transactional
    def delete():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'delete-Tax'.
        # akcija se moze pozvati samo ako je domain.state == 'active'.
        object_log = ObjectLog(parent=tax_key, agent=agent_key, action='delete', state='none')
        object_log.put()
        tax_key.delete()

# done!
class Carrier(ndb.Model):
    
    # root (namespace Domain)
    # http://bazaar.launchpad.net/~openerp/openobject-addons/saas-1/view/head:/delivery/delivery.py#L27
    # http://hg.tryton.org/modules/carrier/file/tip/carrier.py#l10
    # composite index: ancestor:no - active,name
    name = ndb.StringProperty('1', required=True)
    active = ndb.BooleanProperty('2', default=True)
    
    _KIND = 0
    
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    }
    
    # Ova akcija kreira novi carrier.
    @ndb.transactional
    def create():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'create-Carrier'.
        # akcija se moze pozvati samo ako je domain.state == 'active'.
        carrier = Carrier(name=var_name, active=True)
        carrier_key = carrier.put()
        object_log = ObjectLog(parent=carrier_key, agent=agent_key, action='create', state='none', log=carrier)
        object_log.put()
    
    # Ova akcija azurira carrier.
    @ndb.transactional
    def update():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'update-Carrier'.
        # akcija se moze pozvati samo ako je domain.state == 'active'.
        carrier.name = var_name
        carrier.active = var_active
        carrier_key = carrier.put()
        object_log = ObjectLog(parent=carrier_key, agent=agent_key, action='update', state='none', log=carrier)
        object_log.put()
    
    # Ova akcija brise carrier.
    @ndb.transactional
    def delete():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'delete-Carrier'.
        # akcija se moze pozvati samo ako je domain.state == 'active'.
        object_log = ObjectLog(parent=carrier_key, agent=agent_key, action='delete', state='none')
        object_log.put()
        carrier_lines = CarrierLine.query(ancestor=carrier_key).fetch(keys_only=True)
        # ovaj metod ne loguje brisanje pojedinacno svakog carrier_line entiteta, pa se trebati ustvari pozivati CarrierLine.delete() sa listom kljuceva.
        # CarrierLine.delete() nije za sada nije opisana da radi multi key delete.
        # a mozda je ta tehnika nepotrebna, posto se logovanje brisanja samog Carrier entiteta podrazumvea da su svi potomci izbrisani!!
        ndb.delete_multi(carrier_lines)
        carrier_key.delete()

# done!
class CarrierLine(ndb.Expando):
    
    # ancestor Carrier (namespace Domain)
    # http://bazaar.launchpad.net/~openerp/openobject-addons/saas-1/view/head:/delivery/delivery.py#L170
    # composite index: ancestor:yes - sequence; ancestor:yes - active,sequence
    name = ndb.StringProperty('1', required=True)
    sequence = ndb.IntegerProperty('2', required=True)
    location_exclusion = ndb.BooleanProperty('3', default=False, indexed=False)
    active = ndb.BooleanProperty('4', default=True)
    _default_indexed = False
    pass
    # Expando
    # locations = ndb.LocalStructuredProperty(Location, '5', repeated=True)# soft limit 300x
    # rules = ndb.LocalStructuredProperty(CarrierLineRule, '6', repeated=True)# soft limit 300x
    
    _KIND = 0
    
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    }
    
    # Ova akcija kreira novi carrier line.
    @ndb.transactional
    def create():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'create-CarrierLine'.
        # akcija se moze pozvati samo ako je domain.state == 'active'.
        carrier_line = CarrierLine(parent=carrier_key, name=var_name, sequence=var_sequence, location_exclusion=var_location_exclusion, active=True)
        carrier_line_key = carrier_line.put()
        object_log = ObjectLog(parent=carrier_line_key, agent=agent_key, action='create', state='none', log=carrier_line)
        object_log.put()
    
    # Ova akcija azurira carrier line.
    @ndb.transactional
    def update():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'update-CarrierLine'.
        # akcija se moze pozvati samo ako je domain.state == 'active'.
        carrier_line.name = var_name
        carrier_line.sequence = var_sequence
        carrier_line.location_exclusion = var_location_exclusion
        carrier_line.active = var_active
        carrier_line_key = carrier_line.put()
        object_log = ObjectLog(parent=carrier_line_key, agent=agent_key, action='update', state='none', log=carrier_line)
        object_log.put()
    
    # Ova akcija brise carrier line.
    @ndb.transactional
    def delete():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'delete-CarrierLine'.
        # akcija se moze pozvati samo ako je domain.state == 'active'.
        object_log = ObjectLog(parent=carrier_line_key, agent=agent_key, action='delete', state='none')
        object_log.put()
        carrier_line_key.delete()

# done!
class CarrierLineRule(ndb.Model):
    
    # LocalStructuredProperty model
    # http://bazaar.launchpad.net/~openerp/openobject-addons/saas-1/view/head:/delivery/delivery.py#L226
    # ovde se cuvaju dve vrednosti koje su obicno struktuirane kao formule, ovo je mnogo fleksibilnije nego hardcoded struktura informacija koje se cuva kao sto je bio prethodni slucaj
    condition = ndb.StringProperty('1', required=True, indexed=False)# prekompajlirane vrednosti iz UI, napr: True ili weight[kg] >= 5 ili volume[m3] = 0.002
    price = ndb.StringProperty('2', required=True, indexed=False)# prekompajlirane vrednosti iz UI, napr: amount = 35.99 ili amount = weight[kg]*0.28
    # weight - kg; volume - m3; ili sta vec odlucimo, samo je bitno da se podudara sa measurementsima na ProductTemplate/ProductInstance

# done!
class Catalog(ndb.Expando):
    
    # root (namespace Domain)
    # https://support.google.com/merchants/answer/188494?hl=en&hlrm=en#other
    # composite index: ???
    store = ndb.KeyProperty('1', kind=Store, required=True)
    name = ndb.StringProperty('2', required=True)
    publish = ndb.DateTimeProperty('3', required=True)# today
    discontinue = ndb.DateTimeProperty('4', required=True)# +30 days
    cover = blobstore.BlobKeyProperty('5', required=True)# blob ce se implementirati na GCS
    cost = DecimalProperty('6', required=True, indexed=False)
    state = ndb.IntegerProperty('7', required=True)
    _default_indexed = False
    pass
    # Expando
    # Search improvements
    # product count per product category
    # rank coefficient based on store feedback
    
    _KIND = 0
    
    OBJECT_DEFAULT_STATE = 'active'
    
    OBJECT_STATES = {
        # tuple represents (state_code, transition_name)
        # second value represents which transition will be called for changing the state
        # Ne znam da li je predvidjeno ovde da moze biti vise tranzicija/akcija koje vode do istog state-a,
        # sto ce biti slucaj sa verovatno mnogim modelima.
        # broj 0 je rezervisan za none (Stateless Models) i ne koristi se za definiciju validnih state-ova
        'unpublished' : (1, ),
        'locked' : (2, ),
        'published' : (3, ),
        'discontinued' : (4, ),
    }
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'lock' : 3,
       'publish' : 4,
       'discontinue' : 5,
    }
    
    OBJECT_TRANSITIONS = {
        'lock' : {
            'from' : ('unpublished',),
            'to' : ('locked',),
         },
        'publish' : {
           'from' : ('locked', ),
           'to'   : ('published',),
        },
        'discontinue' : {
           'from' : ('published', ),
           'to'   : ('discontinued',),
        },
    }
    
    # Ova akcija kreira novi store.
    @ndb.transactional
    def create():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'create-Store'.
        # akcija se moze pozvati samo ako je domain.state == 'active'.
        store = Store(name=var_name, logo=var_logo, state='open')
        store_key = store.put()
        object_log = ObjectLog(parent=store_key, agent=agent_key, action='create', state=store.state, log=store)
        object_log.put()
    
    # Ova akcija azurira postojeci store.
    @ndb.transactional
    def update():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'update-Store'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i store.state == 'open'.
        store.name = var_name
        store.logo = var_logo
        store_key = store.put()
        object_log = ObjectLog(parent=store_key, agent=agent_key, action='update', state=store.state, log=store)
        object_log.put()
    
    # Ova akcija zatvara otvoren store. Ovde cemo dalje opisati posledice zatvaranja...
    @ndb.transactional
    def close():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'close-Store'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i store.state == 'open'.
        store.state = 'closed'
        store_key = store.put()
        object_log = ObjectLog(parent=store_key, agent=agent_key, action='close', state=store.state, message='poruka od agenta - obavezno polje!', note='privatni komentar agenta (dostupan samo privilegovanim agentima) - obavezno polje!')
        object_log.put()
    
    # Ova akcija otvara zatvoreni store. Ovde cemo dalje opisati posledice otvaranja...
    @ndb.transactional
    def open():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'open-Store'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i store.state == 'closed'.
        store.state = 'open'
        store_key = store.put()
        object_log = ObjectLog(parent=store_key, agent=agent_key, action='open', state=store.state, message='poruka od agenta - obavezno polje!', note='privatni komentar agenta (dostupan samo privilegovanim agentima) - obavezno polje!')
        object_log.put()

# done!
class CatalogImage(Image):
    
    # ancestor Catalog (namespace Domain)
    # composite index: ancestor:yes - sequence
    
    _KIND = 0
    
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    }
    
    # Ova akcija dodaje novu sliku u catalog.
    @ndb.transactional
    def create():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'create-CatalogImage'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i catalog.state == 'unpublished'.
        catalog_image = CatalogImage(parent=catalog_key, image=var_image, content_type=var_content_type, size=var_size, width=var_width, height=var_height, sequence=var_sequence)
        catalog_image_key = catalog_image.put()
        object_log = ObjectLog(parent=catalog_image_key, agent=agent_key, action='create', state='none', log=catalog_image)
        object_log.put()
    
    # Ova akcija menja raspored slike u catalog-u.
    @ndb.transactional
    def update():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'update-CatalogImage'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i catalog.state == 'unpublished'.
        catalog_image.sequence = var_sequence
        catalog_image_key = catalog_image.put()
        object_log = ObjectLog(parent=catalog_image_key, agent=agent_key, action='update', state='none', log=catalog_image)
        object_log.put()
    
    # Ova akcija brise sliku.
    @ndb.transactional
    def delete():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'delete-CatalogImage'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i catalog.state == 'unpublished'.
        object_log = ObjectLog(parent=catalog_image_key, agent=agent_key, action='delete', state='none')
        object_log.put()
        catalog_image_key.delete()

# done!
class CatalogPricetag(ndb.Model):
    
    # ancestor Catalog (namespace Domain)
    product_template = ndb.KeyProperty('1', kind=ProductTemplate, required=True, indexed=False)
    container_image = blobstore.BlobKeyProperty('2', required=True, indexed=False)# blob ce se implementirati na GCS
    source_width = ndb.FloatProperty('3', required=True, indexed=False)
    source_height = ndb.FloatProperty('4', required=True, indexed=False)
    source_position_top = ndb.FloatProperty('5', required=True, indexed=False)
    source_position_left = ndb.FloatProperty('6', required=True, indexed=False)
    value = ndb.StringProperty('7', required=True, indexed=False)# $ 19.99 - ovo se handla unutar transakcije kada se radi update na unit_price od ProductTemplate ili ProductInstance
    
    _KIND = 0
    
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    }
    
    # Ova akcija dodaje novi pricetag na catalog.
    @ndb.transactional
    def create():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'create-CatalogPricetag'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i catalog.state == 'unpublished'.
        catalog_pricetag = CatalogPricetag(parent=catalog_key, product_template=var_product_template, container_image=var_container_image, source_width=var_source_width, source_height=var_source_height, source_position_top=var_source_position_top, source_position_left=var_source_position_left, value=var_value)
        catalog_pricetag_key = catalog_pricetag.put()
        object_log = ObjectLog(parent=catalog_pricetag_key, agent=agent_key, action='create', state='none', log=catalog_pricetag)
        object_log.put()
    
    # Ova akcija azurira pricetag na catalog-u.
    @ndb.transactional
    def update():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'update-CatalogPricetag'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i catalog.state == 'unpublished'.
        catalog_pricetag.product_template = var_product_template
        catalog_pricetag.container_image = var_container_image
        catalog_pricetag.source_width = var_source_width
        catalog_pricetag.source_height = var_source_height
        catalog_pricetag.source_position_top = var_source_position_top
        catalog_pricetag.source_position_left = var_source_position_left
        catalog_pricetag.value = var_value
        catalog_pricetag_key = catalog_pricetag.put()
        object_log = ObjectLog(parent=catalog_pricetag_key, agent=agent_key, action='update', state='none', log=catalog_pricetag)
        object_log.put()
    
    # Ova akcija brise pricetag sa catalog-a.
    @ndb.transactional
    def delete():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'delete-CatalogPricetag'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i catalog.state == 'unpublished'.
        object_log = ObjectLog(parent=catalog_pricetag_key, agent=agent_key, action='delete', state='none')
        object_log.put()
        catalog_pricetag_key.delete()

# done!
class ProductTemplate(ndb.Expando):
    
    # ancestor Catalog (future - root / namespace Domain)
    # composite index: ancestor:yes - name
    product_category = ndb.KeyProperty('1', kind=ProductCategory, required=True, indexed=False)
    name = ndb.StringProperty('2', required=True)
    description = ndb.TextProperty('3', required=True)# soft limit 64kb
    product_uom = ndb.KeyProperty('4', kind=ProductUOM, required=True, indexed=False)
    unit_price = DecimalProperty('5', required=True)
    _default_indexed = False
    pass
    # Expando
    # mozda treba uvesti customer lead time??
    # product_template_variants = ndb.KeyProperty('7', kind=ProductVariant, repeated=True)# soft limit 100x
    # product_template_contents = ndb.KeyProperty('8', kind=ProductContent, repeated=True)# soft limit 100x
    # product_template_images = ndb.LocalStructuredProperty(Image, '9', repeated=True)# soft limit 100x
    # weight = ndb.StringProperty('10')# prekompajlirana vrednost, napr: 0.2[kg] - gde je [kg] jediniva mere, ili sta vec odlucimo
    # volume = ndb.StringProperty('11')# prekompajlirana vrednost, napr: 0.03[m3] - gde je [m3] jediniva mere, ili sta vec odlucimo
    
    _KIND = 0
    
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
       'generate_product_instances' : 4,
    }
    
    # Ova akcija kreira novi product template.
    @ndb.transactional
    def create():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'create-ProductTemplate'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i catalog.state == 'unpublished'.
        product_template = ProductTemplate(parent=catalog_key, product_category=var_product_category, name=var_name, description=var_description, product_uom=var_product_uom, unit_price=var_unit_price)
        product_template_key = product_template.put()
        object_log = ObjectLog(parent=product_template_key, agent=agent_key, action='create', state='none', log=product_template)
        object_log.put()
    
    # Ova akcija azurira product template.
    @ndb.transactional
    def update():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'update-ProductTemplate'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i catalog.state == 'unpublished'.
        product_template.product_category = var_product_category
        product_template.name = var_name
        product_template.description = var_description
        product_template.product_uom = var_product_uom
        product_template.unit_price = var_unit_price
        product_template.state = var_state
        product_template_key = product_template.put()
        object_log = ObjectLog(parent=product_template_key, agent=agent_key, action='update', state='none', log=product_template)
        object_log.put()
    
    # Ova akcija brise product template.
    @ndb.transactional
    def delete():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'delete-ProductTemplate'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i catalog.state == 'unpublished'.
        object_log = ObjectLog(parent=product_template_key, agent=agent_key, action='delete', state='none')
        object_log.put()
        product_instances = ProductInstance.query(ancestor=product_template_key).fetch(keys_only=True)
        # ovaj metod ne loguje brisanje pojedinacno svakog product_instance entiteta, pa se trebati ustvari pozivati ProductInstance.delete() sa listom kljuceva.
        # ProductInstance.delete() nije za sada opisana da radi multi key delete.
        # a mozda je ta tehnika nepotrebna, posto se logovanje brisanja samog ProductTemplate entiteta podrazumvea da su svi potomci izbrisani!!
        ndb.delete_multi(product_instances)
        product_template_key.delete()
    
    # Ova akcija generise product instance.
    @ndb.transactional
    def generate_product_instances():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'generate_product_instances-ProductTemplate'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i catalog.state == 'unpublished'.
        product_instances = ProductInstance.query(ancestor=product_template_key).fetch(keys_only=True)
        ndb.delete_multi(product_instances)
        
        
        
        
        variants []
        for key in product_template_variants:
            product_template_variant = key.get()
            dic = {}
            dic['name'] = product_template_variant.name
            dic['options'] = product_template_variant.options
            dic['position'] = 0
            dic['increment'] = False
            dic['reset'] = False
            variants.append(dic)
        
variants = [
    {'name': 'Color', 'options': ['Red', 'Green', 'Blue'], 'position': 0, 'increment': False, 'reset': False},
    {'name': 'Size', 'options': ['Small', 'Medium', 'Large'], 'position': 0, 'increment': False, 'reset': False},
    {'name': 'Fabric', 'options': ['Silk', 'Cotton'], 'position': 0, 'increment': False, 'reset': False},
    {'name': 'Motif', 'options': ['Lace', 'Smooth', 'ZigZag', 'Butterfly'], 'position': 0, 'increment': False, 'reset': False},
]
        
variant_signatures = []
stay = True
while stay:
    iterator = 0
    for item in variants:
        if (item['increment']):
            variants[iterator]['position'] += 1
            variants[iterator]['increment'] = False
        if (item['reset']):
            variants[iterator]['position'] = 0
            variants[iterator]['reset'] = False
        iterator += 1
    dic = {}
    iterator = 0
    for item in variants:
        dic[item['name']] = item['options'][item['position']]
        if (iterator == 0):
            if (len(item['options']) == item['position'] + 1):
                variants[iterator]['reset'] = True
                variants[iterator + 1]['increment'] = True
            else:
                variants[iterator]['increment'] = True
        elif not (len(variants) == iterator + 1):
            if (len(item['options']) == item['position'] + 1):
                if (variants[iterator - 1]['reset']):
                    variants[iterator]['reset'] = True
                    variants[iterator + 1]['increment'] = True
        elif (len(variants) == iterator + 1):
            if (len(item['options']) == item['position'] + 1):
                if (variants[iterator - 1]['reset']):
                    stay = False
                    break
        iterator += 1
    variant_signatures.append(dic)
        
        variant_signatures = [
            {'Color': 'Red', 'Size': 'Small', 'Fabric': 'Silk'},
            {'Color': 'Green', 'Size': 'Small', 'Fabric': 'Silk'},
            {'Color': 'Blue', 'Size': 'Small', 'Fabric': 'Silk'},
            {'Color': 'Red', 'Size': 'Medium', 'Fabric': 'Silk'},
            {'Color': 'Green', 'Size': 'Medium', 'Fabric': 'Silk'},
            {'Color': 'Blue', 'Size': 'Medium', 'Fabric': 'Silk'},{'name
            {'Color': 'Red', 'Size': 'Large', 'Fabric': 'Silk'},
            {'Color': 'Green', 'Size': 'Large', 'Fabric': 'Silk'},
            {'Color': 'Blue', 'Size': 'Large', 'Fabric': 'Silk'},
            {'Color': 'Red', 'Size': 'Small', 'Fabric': 'Cotton'},
            {'Color': 'Green', 'Size': 'Small', 'Fabric': 'Cotton'},
            {'Color': 'Blue', 'Size': 'Small', 'Fabric': 'Cotton'},
            {'Color': 'Red', 'Size': 'Medium', 'Fabric': 'Cotton'},
            {'Color': 'Green', 'Size': 'Medium', 'Fabric': 'Cotton'},
            {'Color': 'Blue', 'Size': 'Medium', 'Fabric': 'Cotton'},
            {'Color': 'Red', 'Size': 'Large', 'Fabric': 'Cotton'},
            {'Color': 'Green', 'Size': 'Large', 'Fabric': 'Cotton'},
            {'Color': 'Blue', 'Size': 'Large', 'Fabric': 'Cotton'},
        ]
        
            # ako nakon ove variante ima jos varianti onda mi treba broj option-sa u varianti i prvi option iz variante, 
            # ali treba zapamtiti redni broj option-a koji je trenutno izabran
            
            # 
            # treba mi index ucatne variante i treba mi ukupan broj varianti
            # ako iza ove 
            for option in product_template_variant.options:
                
                
                
                
                
        product_instance = ProductInstance(parent=product_template_key, code=var_code, state=var_state)
        product_instance_key = product_instance.put()
        object_log = ObjectLog(parent=product_instance_key, agent=agent_key, action='create', state='none', log=product_instance)
        object_log.put()

# done!
class ProductInstance(ndb.Expando):
    
    # ancestor ProductTemplate
    #variant_signature se gradi na osnovu ProductVariant entiteta vezanih za ProductTemplate-a (od aktuelne ProductInstance) preko ProductTemplateVariant 
    #key name ce se graditi tako sto se uradi MD5 na variant_signature
    #query ce se graditi tako sto se prvo izgradi variant_signature vrednost na osnovu odabira od strane krajnjeg korisnika a potom se ta vrednost hesira u MD5 i koristi kao key identifier
    #mana ove metode je ta sto se uvek mora izgraditi kompletan variant_signature, tj moraju se sve varijacije odabrati (svaka varianta mora biti mandatory_variant_type)
    #default vrednost code ce se graditi na osnovu sledecih informacija: ancestorkey-n, gde je n incremental integer koji se dodeljuje instanci prilikom njenog kreiranja
    #ukoliko user ne odabere multivariant opciju onda se za ProductTemplate generise samo jedna ProductInstance i njen key se gradi automatski.
    # composite index: ancestor:yes - code
    code = ndb.StringProperty('1', required=True)
    state = ndb.IntegerProperty('2', required=True, indexed=False)# ukljuciti index ako bude trebao za projection query
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
    # product_instance_contents = ndb.KeyProperty('5', kind=ProductContent, repeated=True)# soft limit 100x
    # product_instance_images = ndb.LocalStructuredProperty(Image, '6', repeated=True)# soft limit 100x
    # low_stock_quantity = DecimalProperty('7', default=0.00)# notify store manager when qty drops below X quantity
    # weight = ndb.StringProperty('8')# prekompajlirana vrednost, napr: 0.2[kg] - gde je [kg] jediniva mere, ili sta vec odlucimo
    # volume = ndb.StringProperty('9')# prekompajlirana vrednost, napr: 0.03[m3] - gde je [m3] jediniva mere, ili sta vec odlucimo
    # variant_signature = ndb.TextProperty('10', required=True)# soft limit 64kb - ova vrednost kao i vrednosti koje kupac manuelno upise kao opcije variante se prepisuju u order line description prilikom Add to Cart
    
    _KIND = 0
    
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'update' : 1,
       'update_inventory' : 2,
    }
    
    # Ova akcija azurira product instance.
    @ndb.transactional
    def update():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'update-ProductInstance'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i catalog.state == 'unpublished'.
        # u slucaju da je catalog.state == 'published' onda je moguce editovanje samo product_instance.state i product_instance.low_stock_quantity
        product_instance.code = var_code
        product_instance.state = var_state
        product_instance_key = product_instance.put()
        object_log = ObjectLog(parent=product_instance_key, agent=agent_key, action='update', state=product_instance.state, log=product_instance)
        object_log.put()

# done! contention se moze zaobici ako write-ovi na ove entitete budu explicitno izolovani preko task queue
class ProductInventoryLog(ndb.Model):
    
    # ancestor ProductInstance
    # not logged
    # composite index: ancestor:yes - logged:desc
    logged = ndb.DateTimeProperty('1', auto_now_add=True, required=True)
    reference = ndb.KeyProperty('2',required=True)# idempotency je moguc ako se pre inserta proverava da li je record sa tim reference-om upisan 
    quantity = DecimalProperty('3', required=True, indexed=False)# ukljuciti index ako bude trebao za projection query
    balance = DecimalProperty('4', required=True, indexed=False)# ukljuciti index ako bude trebao za projection query

# done!
class ProductInventoryAdjustment(ndb.Model):
    
    # ancestor ProductInstance (namespace Domain)
    # not logged ?
    adjusted = ndb.DateTimeProperty('1', auto_now_add=True, required=True, indexed=False)
    agent = ndb.KeyProperty('2', kind=User, required=True, indexed=False)
    quantity = DecimalProperty('3', required=True, indexed=False, indexed=False)
    comment = ndb.StringProperty('4', required=True, indexed=False)
    
    _KIND = 0
    
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
    }
    
    # Ova akcija azurira product inventory.
    @ndb.transactional
    def create():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'create-ProductInventoryAdjustment'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i catalog.state == 'published'. - mozda budemo dozvolili adjustment bez obzira na catalog.state
        product_inventory_adjustment = ProductInventoryAdjustment(parent=product_instance_key, agent=agent_key, quantity=var_quantity, comment=var_comment)
        product_inventory_adjustment_key = product_inventory_adjustment.put()
        object_log = ObjectLog(parent=product_inventory_adjustment_key, agent=agent_key, action='create', state='none', log=product_inventory_adjustment)
        object_log.put()
        # ovo bi trebalo ici preko task queue
        # idempotency je moguc ako se pre inserta proverava da li je record sa tim reference-om upisan
        product_inventory_log = ProductInventoryLog.query().order(-ProductInventoryLog.logged).fetch(1)
        new_product_inventory_log = ProductInventoryLog(parent=product_instance_key, reference=product_inventory_adjustment_key, quantity=product_inventory_adjustment.quantity, balance=product_inventory_log.balance + product_inventory_adjustment.quantity)
        new_product_inventory_log.put()

# done!
class ProductVariant(ndb.Model):
    
    # ancestor Catalog (future - root) (namespace Domain)
    # http://v6apps.openerp.com/addon/1809
    # composite index: ancestor:yes - name
    name = ndb.StringProperty('1', required=True)
    description = ndb.TextProperty('2')# soft limit 64kb
    options = ndb.StringProperty('3', repeated=True, indexed=False)# soft limit 1000x
    allow_custom_value = ndb.BooleanProperty('4', default=False, indexed=False)# ovu vrednost buyer upisuje u definisano polje a ona se dalje prepisuje u order line description prilikom Add to Cart
    
    _KIND = 0
    
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
    }
    
    # Ova akcija kreira novi product variant.
    @ndb.transactional
    def create():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'create-ProductVariant'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i catalog.state == 'unpublished'.
        product_variant = ProductVariant(parent=catalog_key, name=var_name, description=var_description, options=var_options, allow_custom_value=var_allow_custom_value)
        product_variant_key = product_variant.put()
        object_log = ObjectLog(parent=product_variant_key, agent=agent_key, action='create', state='none', log=product_variant)
        object_log.put()
    
    # Ova akcija azurira product variant.
    @ndb.transactional
    def update():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'update-ProductVariant'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i catalog.state == 'unpublished'.
        product_variant.name = var_name
        product_variant.description = var_description
        product_variant.options = var_options
        product_variant.allow_custom_value = var_allow_custom_value
        product_variant_key = product_variant.put()
        object_log = ObjectLog(parent=product_variant_key, agent=agent_key, action='update', state='none', log=product_variant)
        object_log.put()

# done!
class ProductContent(ndb.Model):
    
    # ancestor Catalog (future - root) (namespace Domain)
    # composite index: ancestor:yes - title
    title = ndb.StringProperty('1', required=True)
    body = ndb.TextProperty('2', required=True)
    
    _KIND = 0
    
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
    }
    
    # Ova akcija kreira novi product content.
    @ndb.transactional
    def create():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'create-ProductContent'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i catalog.state == 'unpublished'.
        product_content = ProductContent(parent=catalog_key, title=var_title, body=var_body)
        product_content_key = product_content.put()
        object_log = ObjectLog(parent=product_content_key, agent=agent_key, action='create', state='none', log=product_content)
        object_log.put()
    
    # Ova akcija azurira product content.
    @ndb.transactional
    def update():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'update-ProductContent'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i catalog.state == 'unpublished'.
        product_content.title = var_title
        product_content.body = var_body
        product_content_key = product_content.put()
        object_log = ObjectLog(parent=product_content_key, agent=agent_key, action='update', state='none', log=product_content)
        object_log.put()

################################################################################
# User - 3
################################################################################

# done!
class User(ndb.Expando):
    
    # root
    state = ndb.IntegerProperty('1', required=True)
    emails = ndb.StringProperty('2', repeated=True)# soft limit 100x
    identities = ndb.StructuredProperty(UserIdentity, '3', repeated=True)# soft limit 100x
    _default_indexed = False
    pass
    #Expando
    
    _KIND = 2
    
    OBJECT_DEFAULT_STATE = 'active'
    
    OBJECT_STATES = {
        # tuple represents (state_code, transition_name)
        # second value represents which transition will be called for changing the state
        # Ne znam da li je predvidjeno ovde da moze biti vise tranzicija/akcija koje vode do istog state-a,
        # sto ce biti slucaj sa verovatno mnogim modelima.
        # broj 0 je rezervisan za none (Stateless Models) i ne koristi se za definiciju validnih state-ova
        'active' : (1, ),
        'suspended' : (2, ),
    }
    
    OBJECT_ACTIONS = {
       'register' : 1,
       'update' : 2,
       'login' : 3,
       'logout' : 4,
       'suspend' : 5,
       'activate' : 6,
    }
    
    OBJECT_TRANSITIONS = {
        'activate' : {
             # from where to where this transition can be accomplished?
            'from' : ('suspended',),
            'to' : ('active',),
         },
        'suspend' : {
           'from' : ('active', ),
           'to'   : ('suspended',),
        },
    }
    
    # Ova akcija nastaje prilikom prve autentikacije kada korisnik nije jos registrovan.
    # Ukoliko se prilikom "login" akcije ustanovi da korisnik nikada nije evidentiran u bazi, nastupa akcija "register". 
    @ndb.transactional
    def register():
        # ovu akciju moze izvrsiti samo neregistrovani neautenticirani agent.
        user = User(state='active', emails=['user@email.com',], identities=[UserIdentity(identity='abc123', email='user@email.com', associated=True, primary=True),])
        user_key = user.put()
        object_log = ObjectLog(parent=user_key, agent=user_key, action='register', state=user.state, log=user)
        object_log.put()
        # UserIPAddress se pravi nakon pravljenja ObjectLog-a zato sto se ne loguje.
        user_ip_address = UserIPAddress(parent=user_key, ip_address='127.0.0.1')
        user_ip_address.put()
    
    # Ova akcija radi insert/update/delete na neki prop. (izuzev state) u User objektu.
    @ndb.transactional
    def update():
        user.emails = ['user@email.com',]
        user.identities = [UserIdentity(identity='abc123', email='user@email.com', associated=True, primary=True),]
        user_key = user.put()
        object_log = ObjectLog(parent=user_key, agent=user_key, action='update', state=user.state, log=user)
        object_log.put()
        # ukoliko se u listi user.identities promenio prop. user.identities.primary, 
        # radi se potraga za eventualnim BuyerCollection entietom usera koji je imao prethodnu email adresu, 
        # i radi se buyer_collection.primary_email prop.
    
    # Ova akcija se izvrsava svaki put kada neautenticirani korisnik stupi u proces autentikacije.
    # Prvo se proverava da li je korisnik vec registrovan. Ukoliko User ne postoji onda se prelazi na akciju "register".
    # Ukoliko user postoji, onda se dalje ispituje. 
    # Proverava se da li ima nekih izmena na postojecim podacima, i ukoliko ima, onda se poziva "update" akcija.
    # Dalje se proverava da li je useru dozvoljen login (User.state == 'active'). Ako mu je dozvoljen login onda se izvrsava "login" akcija.
    @ndb.transactional
    def login():
        # ovde bi mogla da stoji provera continue if(User.state == 'active'), ili van ove funkcije, videcemo.
        object_log = ObjectLog(parent=user_key, agent=user_key, action='login', state=user.state)
        object_log.put()
        # UserIPAddress se pravi nakon pravljenja ObjectLog-a zato sto se ne loguje.
        user_ip_address = UserIPAddress(parent=user_key, ip_address='127.0.0.1')
        user_ip_address.put()
    
    # Ova akcija se izvrsava svaki put kada autenticirani korisnik stupi u proces deautentikacije.
    @ndb.transactional
    def logout():
        object_log = ObjectLog(parent=user_key, agent='user_key/agent_key', action='logout', state=user.state)
        object_log.put()
    
    # Ova akcija sluzi za suspenziju aktivnog korisnika, i izvrsava je privilegovani/administrativni agent.
    # Treba obratiti paznju na to da suspenzija usera ujedno znaci i izuzimanje svih negativnih i neutralnih feedbackova koje je user ostavio dok je bio aktivan.
    ''' Suspenzija user account-a zabranjuje njegovom vlasniku autenticirani pristup na mstyle, 
    i deaktivira sve negativne i neutralne feedback-ove koji su sa ovog user account-a ostavljeni. 
    Ni jedan asocirani email suspendovanog korisnickog racuna se vise ne moze upotrebiti na mstyle 
    (za otvaranje novog account-a, ili neke druge operacije). 
    Account koji je suspendovan se moze opet reaktivirati od strane administratora sistema. '''
    @ndb.transactional
    def suspend():
        # ovu akciju moze izvrsiti samo agent koji ima globalnu dozvolu 'suspend-User'.
        # akcija se moze pozvati samo ako je user.state == 'active'.
        user.state = 'suspended'
        user_key = user.put()
        object_log = ObjectLog(parent=user_key, agent='agent_key', action='suspend', state=user.state, message='poruka od agenta - obavezno polje!', note='privatni komentar agenta (dostupan samo privilegovanim agentima) - obavezno polje!')
        object_log.put()
        # poziva se akcija "logout";
        User.logout()
    
    # Ova akcija sluzi za aktiviranje suspendovanog korisnika i izvrsava je privilegovani/administrativni agent.
    # Treba obratiti paznju na to da aktivacija usera ujedno znaci i vracanje svih negativnih i neutralnih feedbackova koje je user ostavio dok je bio aktivan, a koji su bili izuzeti dok je bio suspendovan.
    # Aktivni user account je u potpunosti funkcionalan i operativan.
    @ndb.transactional
    def activate():
        # ovu akciju moze izvrsiti samo agent koji ima globalnu dozvolu 'activate-User'.
        # akcija se moze pozvati samo ako je user.state == 'suspended'.
        user.state = 'active'
        user_key = user.put()
        object_log = ObjectLog(parent=user_key, agent='agent_key', action='activate', state=user.state, message='poruka od agenta - obavezno polje!', note='privatni komentar agenta (dostupan samo privilegovanim agentima) - obavezno polje!')
        object_log.put()

# done!
class UserIdentity(ndb.Model):
    
    # StructuredProperty model
    identity = ndb.StringProperty('1', required=True)# spojen je i provider name sa id-jem
    email = ndb.StringProperty('2', required=True)
    associated = ndb.BooleanProperty('3', default=True)
    primary = ndb.BooleanProperty('4', default=True)

# done! mozemo li ovo da stavljamo u app engine log ? - ovo sam verovatno i ranje pitao...
class UserIPAddress(ndb.Model):
    
    # ancestor User
    # not logged
    # ako budemo radili per user istragu loga onda nam treba composite index: ancestor:yes - logged:desc
    logged = ndb.DateTimeProperty('1', auto_now_add=True, required=True)
    ip_address = ndb.StringProperty('2', required=True, indexed=False)

################################################################################
# BUYER - 4
################################################################################

# done!
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
    # region = ndb.KeyProperty('8', kind=CountrySubdivision, required=True)# ako je potreban string val onda se ovo preskace 
    # region = ndb.StringProperty('8', required=True)# ako je potreban key val onda se ovo preskace
    # street_address2 = ndb.StringProperty('9')
    # email = ndb.StringProperty('10')
    # telephone = ndb.StringProperty('11')
    
    _KIND = 18
    
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    }
    
    # Pravi novu adresu korisnika
    @ndb.transactional
    def create():
        # ovu akciju moze izvrsiti samo registrovani autenticirani agent.
        buyer_address = BuyerAddress(parent=user_key, name='Home', country='82736563', city='Beverly Hills', postal_code='90210', street_address='First Street, 10', region='656776533')
        buyer_address_key = buyer_address.put()
        object_log = ObjectLog(parent=buyer_address_key, agent=user_key, action='create', state='none', log=buyer_address)
        object_log.put()
    
    # Azurira postojecu adresu korisnika
    @ndb.transactional
    def update():
        # ovu akciju moze izvrsiti samo entity owner (buyer_address.parent == agent).
        buyer_address.name = 'Home in Miami'
        buyer_address.country = '82736563'
        buyer_address.city = 'Miami'
        buyer_address.postal_code = '26547'
        buyer_address.street_address = 'Second Street, 10'
        buyer_address.region = '514133'
        buyer_address_key = buyer_address.put()
        object_log = ObjectLog(parent=buyer_address_key, agent=user_key, action='update', state='none', log=buyer_address)
        object_log.put()
    
    # Brise postojecu adresu korisnika
    @ndb.transactional
    def delete():
        # ovu akciju moze izvrsiti samo entity owner (buyer_address.parent == agent).
        object_log = ObjectLog(parent=buyer_address_key, agent=user_key, action='delete', state='none')
        object_log.put()
        buyer_address_key.delete()

# done!
class BuyerCollection(ndb.Model):
    
    # ancestor User
    # mozda bude trebao index na primary_email radi mogucnosti update-a kada user promeni primarnu email adresu na svom profilu
    # composite index: ancestor:yes - name
    name = ndb.StringProperty('1', required=True)
    notifications = ndb.BooleanProperty('2', default=False)
    primary_email = ndb.StringProperty('3', required=True, indexed=False)
    
    _KIND = 19
    
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    }
    
    # Pravi novu kolekciju za korisnika
    @ndb.transactional
    def create():
        # ovu akciju moze izvrsiti samo registrovani autenticirani agent.
        for identity in user.identities:
            if(identity.primary == True):
                user_primary_email = identity.email
                break
        buyer_collection = BuyerCollection(parent=user_key, name='Favorites', notifications=True, primary_email=user_primary_email)
        buyer_collection_key = buyer_collection.put()
        object_log = ObjectLog(parent=buyer_collection_key, agent=user_key, action='create', state='none', log=buyer_collection)
        object_log.put()
    
    # Azurira postojecu kolekciju korisnika
    @ndb.transactional
    def update():
        # ovu akciju moze izvrsiti samo entity owner (buyer_collection.parent == agent).
        buyer_collection.name = 'Shoes'
        buyer_collection.notifications = True
        for identity in user.identities:
            if(identity.primary == True):
                user_primary_email = identity.email
                break
        buyer_collection.primary_email = user_primary_email
        buyer_collection_key = buyer_collection.put()
        object_log = ObjectLog(parent=buyer_collection_key, agent=user_key, action='update', state='none', log=buyer_collection)
        object_log.put()
    
    # Brise postojecu kolekciju korisnika
    @ndb.transactional
    def delete():
        # ovu akciju moze izvrsiti samo entity owner (buyer_collection.parent == agent).
        object_log = ObjectLog(parent=buyer_collection_key, agent=user_key, action='delete', state='none')
        object_log.put()
        buyer_collection_key.delete()

# done!
class BuyerCollectionStore(ndb.Model):
    
    # ancestor User
    store = ndb.KeyProperty('1', kind=Store, required=True)
    collections = ndb.KeyProperty('2', kind=BuyerCollection, repeated=True)# soft limit 500x
    
    _KIND = 20
    
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    }
    
    # Dodaje novi store u korisnikovu listu i odredjuje clanstvo u kolekcijama korisnika
    @ndb.transactional
    def create():
        # ovu akciju moze izvrsiti samo registrovani autenticirani agent.
        buyer_collection_store = BuyerCollectionStore(parent=user_key, store='7464536', collections=['1234'])
        buyer_collection_store_key = buyer_collection_store.put()
        object_log = ObjectLog(parent=buyer_collection_store_key, agent=user_key, action='create', state='none', log=buyer_collection_store)
        object_log.put()
        # izaziva se update AggregateBuyerCollectionCatalog preko task queue
    
    # Menja clanstvo store u kolekcijama korisnika
    @ndb.transactional
    def update():
        # ovu akciju moze izvrsiti samo entity owner (buyer_collection_store.parent == agent).
        buyer_collection_store.collections = ['1234', '56433']
        buyer_collection_store_key = buyer_collection_store.put()
        object_log = ObjectLog(parent=buyer_collection_store_key, agent=user_key, action='update', state='none', log=buyer_collection_store)
        object_log.put()
        # izaziva se update AggregateBuyerCollectionCatalog preko task queue
    
    # Brise store iz korisnikove liste
    @ndb.transactional
    def delete():
        # ovu akciju moze izvrsiti samo entity owner (buyer_collection_store.parent == agent).
        object_log = ObjectLog(parent=buyer_collection_store_key, agent=user_key, action='delete', state='none')
        object_log.put()
        buyer_collection_store_key.delete()
        # izaziva se update AggregateBuyerCollectionCatalog preko task queue
        # ndb.delete_multi(AggregateBuyerCollectionCatalog.query(AggregateBuyerCollectionCatalog.store == buyer_collection_store.store, ancestor=user_key))

# done! contention se moze zaobici ako write-ovi na ove entitete budu explicitno izolovani preko task queue
class AggregateBuyerCollectionCatalog(ndb.Model):
    
    # ancestor User
    # not logged
    # task queue radi agregaciju prilikom nekih promena na store-u
    # mogao bi da se uvede index na collections radi filtera: AggregateBuyerCollectionCatalog.collections = 'collection', 
    # ovo moze biti dobra situacija za upotrebu MapReduce ??
    # composite index: ancestor:yes - catalog_published_date:desc
    store = ndb.KeyProperty('1', kind=Store, required=True)
    collections = ndb.KeyProperty('2', kind=BuyerCollection, repeated=True, indexed=False)# soft limit 500x
    catalog = ndb.KeyProperty('3', kind=Catalog, required=True, indexed=False)
    catalog_cover = blobstore.BlobKeyProperty('4', required=True, indexed=False)# blob ce se implementirati na GCS
    catalog_published_date = ndb.DateTimeProperty('5', required=True)

################################################################################
# USER REQUEST - 2
################################################################################

# done!
class FeedbackRequest(ndb.Model):
    
    # ancestor User
    # ako hocemo da dozvolimo sva sortiranja, i dodatni filter po state-u uz sortiranje, onda nam trebaju slecedi indexi
    # composite index:
    # ancestor:yes - updated:desc; ancestor:yes - created:desc;
    # ancestor:yes - state,updated:desc; ancestor:yes - state,created:desc
    reference = ndb.StringProperty('1', required=True, indexed=False)
    state = ndb.IntegerProperty('2', required=True)
    updated = ndb.DateTimeProperty('3', auto_now=True, required=True)
    created = ndb.DateTimeProperty('4', auto_now_add=True, required=True)
    
    # primer helper funkcije u slucajevima gde se ne koristi ancestor mehanizam za pristup relacijama
    @property
    def logs(self):
      return ObjectLog.query(ancestor = self.key())
    
    _KIND = 8
    
    OBJECT_DEFAULT_STATE = 'new'
    
    OBJECT_STATES = {
        # tuple represents (state_code, transition_name)
        # second value represents which transition will be called for changing the state
        # ne znam da li je predvidjeno ovde da moze biti vise tranzicija/akcija koje vode do istog state-a,
        # sto ce biti slucaj sa verovatno mnogim modelima.
        # broj 0 je rezervisan za state none (Stateless Models) i ne koristi se za definiciju validnih state-ova
        'new' : (1, ),
        'reviewing' : (2, ),
        'duplicate' : (3, ),
        'accepted' : (4, ),
        'dismissed' : (5, ),
    }
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'review' : 3,
       'close' : 4,
    }
    
    OBJECT_TRANSITIONS = {
        'review' : {
            'from' : ('new',),
            'to' : ('reviewing',),
         },
        'close' : {
           'from' : ('reviewing', ),
           'to'   : ('duplicate', 'accepted', 'dismissed',),
        },
    }
    
    # Ova akcija sluzi za slanje feedback-a miraclestyle timu od strane krajnjih korisnika.
    @ndb.transactional
    def create():
        # ovu akciju moze izvrsiti samo registrovani autenticirani agent.
        feedback_request = FeedbackRequest(parent=user_key, reference='https://www,miraclestyle.com/...', state='new')
        feedback_request_key = feedback_request.put()
        object_log = ObjectLog(parent=feedback_request_key, agent=user_key, action='create', state=feedback_request.state, message='poruka od agenta - obavezno polje!')
        object_log.put()
    
    # Ova akcija sluzi za insert ObjectLog-a koji je descendant FeedbackRequest entitetu.
    # Insertom ObjectLog-a dozvoljeno je unosenje poruke (i privatnog komentara), sto je i smisao ove akcije.
    @ndb.transactional
    def update():
        # ovu akciju moze izvrsiti samo agent koji ima globalnu dozvolu 'update-FeedbackRequest'. / ? # ovu akciju moze izvrsiti samo entity owner (feedback_request.parent == agent) ili agent koji ima globalnu dozvolu 'update-FeedbackRequest'.
        # Radi se update FeedbackRequest-a bez izmena na bilo koji prop. (u cilju izazivanja promene na FeedbackRequest.updated prop.)
        feedback_request_key = feedback_request.put()
        object_log = ObjectLog(parent=feedback_request_key, agent=agent_key, action='update', state=feedback_request.state, message='poruka od agenta - obavezno polje!', note='privatni komentar agenta (dostupan samo privilegovanim agentima) - obavezno polje!')
        object_log.put()
    
    # Ovom akcijom privilegovani/administrativni agent menja stanje FeedbackRequest entiteta u 'reviewing'.
    @ndb.transactional
    def review():
        # ovu akciju moze izvrsiti samo agent koji ima globalnu dozvolu 'review-FeedbackRequest'.
        # akcija se moze pozvati samo ako je feedback_request.state == 'new'.
        feedback_request.state = 'reviewing'
        feedback_request_key = feedback_request.put()
        object_log = ObjectLog(parent=feedback_request_key, agent=agent_key, action='review', state=feedback_request.state, message='poruka od agenta - obavezno polje!', note='privatni komentar agenta (dostupan samo privilegovanim agentima) - obavezno polje!')
        object_log.put()
    
    # Ovom akcijom privilegovani/administrativni agent menja stanje FeedbackRequest entiteta u 'duplicate', 'accepted', ili 'dismissed'.
    @ndb.transactional
    def close():
        # ovu akciju moze izvrsiti samo agent koji ima globalnu dozvolu 'close-FeedbackRequest'.
        # akcija se moze pozvati samo ako je feedback_request.state == 'reviewing'.
        feedback_request.state = 'duplicate' | 'accepted' | 'dismissed'
        feedback_request_key = feedback_request.put()
        object_log = ObjectLog(parent=feedback_request_key, agent=agent_key, action='close', state=feedback_request.state, message='poruka od agenta - obavezno polje!', note='privatni komentar agenta (dostupan samo privilegovanim agentima) - obavezno polje!')
        object_log.put()

# done!
class SupportRequest(ndb.Model):
    
    # ancestor User
    # ako uopste bude vidljivo useru onda mozemo razmatrati indexing
    # ako hocemo da dozvolimo sva sortiranja, i dodatni filter po state-u uz sortiranje, onda nam trebaju slecedi indexi
    # composite index:
    # ancestor:yes - updated:desc; ancestor:yes - created:desc;
    # ancestor:yes - state,updated:desc; ancestor:yes - state,created:desc
    reference = ndb.StringProperty('1', required=True, indexed=False)
    state = ndb.IntegerProperty('2', required=True)
    updated = ndb.DateTimeProperty('3', auto_now=True, required=True)
    created = ndb.DateTimeProperty('4', auto_now_add=True, required=True)
    
    _KIND = 9
    
    OBJECT_DEFAULT_STATE = 'new'
    
    OBJECT_STATES = {
        # tuple represents (state_code, transition_name)
        # second value represents which transition will be called for changing the state
        # ne znam da li je predvidjeno ovde da moze biti vise tranzicija/akcija koje vode do istog state-a,
        # sto ce biti slucaj sa verovatno mnogim modelima.
        # broj 0 je rezervisan za state none (Stateless Models) i ne koristi se za definiciju validnih state-ova
        'new' : (1, ),
        'opened' : (2, ),
        'awaiting_closure' : (3, ),
        'closed' : (4, ),
    }
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'open' : 3,
       'propose_close' : 4,
       'close' : 5,
    }
    
    OBJECT_TRANSITIONS = {
        'open' : {
            'from' : ('new',),
            'to' : ('opened',),
         },
        'propose_close' : {
           'from' : ('opened', ),
           'to'   : ('awaiting_closure',),
        },
        'close' : {
           'from' : ('opened', 'awaiting_closure',),
           'to'   : ('closed',),
        },
    }
    
    # Ova akcija krajnjem korisniku sluzi za pravljenje zahteva za pomoc (ticket-a) od miraclestyle tima.
    @ndb.transactional
    def create():
        # ovu akciju moze izvrsiti samo registrovani autenticirani agent.
        support_request = SupportRequest(parent=user_key, reference='https://www,miraclestyle.com/...', state='new')
        support_request_key = support_request.put()
        object_log = ObjectLog(parent=support_request_key, agent=user_key, action='create', state=support_request.state, message='poruka od agenta - obavezno polje!')
        object_log.put()
    
    # Ova akcija sluzi za insert ObjectLog-a koji je descendant SupportRequest entitetu.
    # Insertom ObjectLog-a dozvoljeno je unosenje poruke (i privatnog komentara), sto je i smisao ove akcije.
    @ndb.transactional
    def update():
        # ovu akciju moze izvrsiti samo entity owner (support_request.parent == agent) ili agent koji ima globalnu dozvolu 'update-SupportRequest'
        # Radi se update SupportRequest-a bez izmena na bilo koji prop. (u cilju izazivanja promene na SupportRequest.updated prop.)
        support_request_key = support_request.put()
        object_log = ObjectLog(parent=support_request_key, agent=agent_key, action='update', state=support_request.state, message='poruka od agenta - obavezno polje!', note='privatni komentar agenta (dostupan samo privilegovanim agentima/non-owner-ima) - obavezno polje!')
        object_log.put()
    
    # Ovom akcijom privilegovani/administrativni agent menja stanje SupportRequest entiteta u 'opened'.
    @ndb.transactional
    def open():
        # ovu akciju moze izvrsiti samo agent koji ima globalnu dozvolu 'open-SupportRequest'.
        # akcija se moze pozvati samo ako je support_request.state == 'new'.
        support_request.state = 'opened'
        support_request_key = support_request.put()
        object_log = ObjectLog(parent=support_request_key, agent=agent_key, action='open', state=support_request.state, message='poruka od agenta - obavezno polje!', note='privatni komentar agenta (dostupan samo privilegovanim agentima/non-owner-ima) - obavezno polje!')
        object_log.put()
    
    # Ovom akcijom privilegovani/administrativni agent menja stanje SupportRequest entiteta u 'awaiting_closure'.
    @ndb.transactional
    def propose_close():
        # ovu akciju moze izvrsiti samo agent koji ima globalnu dozvolu 'propose_close-SupportRequest'.
        # akcija se moze pozvati samo ako je support_request.state == 'opened'.
        support_request.state = 'awaiting_closure'
        support_request_key = support_request.put()
        object_log = ObjectLog(parent=support_request_key, agent=agent_key, action='propose_close', state=support_request.state, message='poruka od agenta - obavezno polje!', note='privatni komentar agenta (dostupan samo privilegovanim agentima/non-owner-ima) - obavezno polje!')
        object_log.put()
    
    # Ovom akcijom agent menja stanje SupportRequest entiteta u 'closed'.
    @ndb.transactional
    def close():
        # ovu akciju moze izvrsiti samo entity owner (support_request.parent == agent) ili agent koji ima globalnu dozvolu 'close-SupportRequest' (sto ce verovatno imati sistemski account koji ce preko cron-a izvrsiti akciju).
        # akcija se moze pozvati samo ako je support_request.state == 'opened' ili support_request.state == 'awaiting_closure'.
        support_request.state = 'closed'
        support_request_key = support_request.put()
        object_log = ObjectLog(parent=support_request_key, agent=agent_key, action='close', state=support_request.state, message='poruka od agenta - obavezno polje!', note='privatni komentar agenta (dostupan samo privilegovanim agentima/non-owner-ima) - obavezno polje!')
        object_log.put()

################################################################################
# TRADE - 11
################################################################################

# done!
class Order(ndb.Expando):
    
    # ancestor User (namespace Domain)
    # http://hg.tryton.org/modules/sale/file/tip/sale.py#l28
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

# done!
class OrderFeedback(ndb.Model):
    
    # ancestor Order
    state = ndb.IntegerProperty('1', required=True, indexed=False)

# done!
class BillingOrder(ndb.Expando):
    
    # root (namespace Domain)
    # http://hg.tryton.org/modules/sale/file/tip/sale.py#l28
    # http://hg.tryton.org/modules/purchase/file/tip/purchase.py#l32
    # http://doc.tryton.org/2.8/modules/sale/doc/index.html
    # http://doc.tryton.org/2.8/modules/purchase/doc/index.html
    # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/sale/sale.py#L48
    order_date = ndb.DateTimeProperty('1', auto_now_add=True, required=True, indexed=False)# updated on checkout
    currency = ndb.LocalStructuredProperty(OrderCurrency, '2', required=True)
    untaxed_amount = DecimalProperty('3', required=True, indexed=False)
    tax_amount = DecimalProperty('4', required=True, indexed=False)
    total_amount = DecimalProperty('5', required=True, indexed=False)
    state = ndb.IntegerProperty('6', required=True, indexed=False) 
    updated = ndb.DateTimeProperty('7', auto_now=True, required=True, indexed=False)
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

# done!
class OrderCurrency(ndb.Model):
    
    # LocalStructuredProperty model
    # http://hg.tryton.org/modules/currency/file/tip/currency.py#l14
    # http://en.wikipedia.org/wiki/ISO_4217
    # http://hg.tryton.org/modules/currency/file/tip/currency.xml#l107
    # http://bazaar.launchpad.net/~openerp/openobject-server/7.0/view/head:/openerp/addons/base/res/res_currency.py#L32
    name = ndb.StringProperty('1', required=True, indexed=False)
    symbol = ndb.StringProperty('2', required=True, indexed=False)
    code = ndb.StringProperty('3', required=True, indexed=False)
    numeric_code = ndb.StringProperty('4', indexed=False)
    rounding = DecimalProperty('5', required=True, indexed=False)
    digits = ndb.IntegerProperty('6', required=True, indexed=False)
    #formating
    grouping = ndb.StringProperty('7', required=True, indexed=False)
    decimal_separator = ndb.StringProperty('8', required=True, indexed=False)
    thousands_separator = ndb.StringProperty('9', indexed=False)
    positive_sign_position = ndb.IntegerProperty('10', required=True, indexed=False)
    negative_sign_position = ndb.IntegerProperty('11', required=True, indexed=False)
    positive_sign = ndb.StringProperty('12', indexed=False)
    negative_sign = ndb.StringProperty('13', indexed=False)
    positive_currency_symbol_precedes = ndb.BooleanProperty('14', default=True, indexed=False)
    negative_currency_symbol_precedes = ndb.BooleanProperty('15', default=True, indexed=False)
    positive_separate_by_space = ndb.BooleanProperty('16', default=True, indexed=False)
    negative_separate_by_space = ndb.BooleanProperty('17', default=True, indexed=False)

# done!
class OrderLine(ndb.Expando):
    
    # ancestor Order, BillingOrder
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
    # catalog_pricetag_reference = ndb.KeyProperty('10', kind=CatalogPricetag, required=True)
    # product_instance_reference = ndb.KeyProperty('11', kind=ProductInstance, required=True)
    # tax_references = ndb.KeyProperty('12', kind=StoreTax, repeated=True)# soft limit 500x

# done!
class OrderLineProductUOM(ndb.Model):
    
    # LocalStructuredProperty model
    # http://hg.tryton.org/modules/product/file/tip/uom.py#l28
    # http://hg.tryton.org/modules/product/file/tip/uom.xml#l63 - http://hg.tryton.org/modules/product/file/tip/uom.xml#l312
    # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/product/product.py#L89
    name = ndb.StringProperty('1', required=True, indexed=False)
    symbol = ndb.StringProperty('2', required=True, indexed=False)
    category = ndb.StringProperty('3', required=True, indexed=False)# ProductUOMCategory.name
    rounding = DecimalProperty('4', required=True, indexed=False)
    digits = ndb.IntegerProperty('5', required=True, indexed=False)

# done!
class OrderLineTax(ndb.Model):
    
    # LocalStructuredProperty model
    # http://hg.tryton.org/modules/account/file/tip/tax.py#l545
    name = ndb.StringProperty('1', required=True, indexed=False)
    amount = ndb.StringProperty('2', required=True, indexed=False)# prekompajlirane vrednosti iz UI, napr: 17.00[%] ili 10.00[c] gde je [c] = currency

# done!
class PayPalTransaction(ndb.Model):
    
    # ancestor Order, BillingOrder
    # not logged
    # ako budemo radili analizu sa pojedinacnih ordera onda nam treba composite index: ancestor:yes - logged:desc
    logged = ndb.DateTimeProperty('1', auto_now_add=True, required=True)
    txn_id = ndb.StringProperty('2', required=True)
    ipn_message = ndb.TextProperty('3', required=True)

# done! contention se moze zaobici ako write-ovi na ove entitete budu explicitno izolovani preko task queue
class BillingLog(ndb.Model):
    
    # root (namespace Domain)
    # not logged
    logged = ndb.DateTimeProperty('1', auto_now_add=True, required=True)
    reference = ndb.KeyProperty('2',required=True)# idempotency je moguc ako se pre inserta proverava da li je record sa tim reference-om upisan
    amount = DecimalProperty('3', required=True, indexed=False)# ukljuciti index ako bude trebao za projection query
    balance = DecimalProperty('4', required=True, indexed=False)# ukljuciti index ako bude trebao za projection query

# done!
class BillingCreditAdjustment(ndb.Model):
    
    # root (namespace Domain)
    # not logged
    adjusted = ndb.DateTimeProperty('2', auto_now_add=True, required=True, indexed=False)
    agent = ndb.KeyProperty('3', kind=User, required=True, indexed=False)
    amount = DecimalProperty('4', required=True, indexed=False)
    message = ndb.TextProperty('5')# soft limit 64kb - to determine char count
    note = ndb.TextProperty('6')# soft limit 64kb - to determine char count

################################################################################
# MISC - 10
################################################################################

# done!
class Content(ndb.Model):
    
    # root
    # composite index: ancestor:no - category,state,sequence
    updated = ndb.DateTimeProperty('1', auto_now=True, required=True)
    title = ndb.StringProperty('2', required=True)
    category = ndb.IntegerProperty('3', required=True)
    body = ndb.TextProperty('4', required=True)
    sequence = ndb.IntegerProperty('5', required=True)
    state = ndb.IntegerProperty('6', required=True)# published/unpublished

# done!
class Image(ndb.Model):
    
    # base class/structured class
    image = blobstore.BlobKeyProperty('1', required=True, indexed=False)# blob ce se implementirati na GCS
    content_type = ndb.StringProperty('2', required=True, indexed=False)
    size = ndb.FloatProperty('3', required=True, indexed=False)
    width = ndb.IntegerProperty('4', required=True, indexed=False)
    height = ndb.IntegerProperty('5', required=True, indexed=False)
    sequence = ndb.IntegerProperty('6', required=True)

# done!
class Country(ndb.Model):
    
    # root
    # http://hg.tryton.org/modules/country/file/tip/country.py#l8
    # http://en.wikipedia.org/wiki/ISO_3166
    # http://hg.tryton.org/modules/country/file/tip/country.xml
    # http://downloads.tryton.org/2.8/trytond_country-2.8.0.tar.gz
    # http://bazaar.launchpad.net/~openerp/openobject-server/7.0/view/head:/openerp/addons/base/res/res_country.py#L42
    # composite index: ancestor:no - active,name
    code = ndb.StringProperty('1', required=True, indexed=False)# ukljuciti index ako bude trebao za projection query
    name = ndb.StringProperty('2', required=True)
    active = ndb.BooleanProperty('3', default=True)

# done!
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

# done!
class ProductCategory(ndb.Model):
    
    # root
    # http://hg.tryton.org/modules/product/file/tip/category.py#l8
    # https://support.google.com/merchants/answer/1705911
    # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/product/product.py#L227
    # composite index: ancestor:no - state,name
    parent_record = ndb.KeyProperty('1', kind=ProductCategory, indexed=False)
    name = ndb.StringProperty('2', required=True)
    complete_name = ndb.TextProperty('3', required=True)# da je ovo indexable bilo bi idealno za projection query
    state = ndb.IntegerProperty('4', required=True)

# done!
class ProductUOMCategory(ndb.Model):
    
    # root
    # http://hg.tryton.org/modules/product/file/tip/uom.py#l16
    # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/product/product.py#L81
    # mozda da ovi entiteti budu non-deletable i non-editable ??
    name = ndb.StringProperty('1', required=True)

# done!
class ProductUOM(ndb.Model):
    
    # ancestor ProductUOMCategory
    # http://hg.tryton.org/modules/product/file/tip/uom.py#l28
    # http://hg.tryton.org/modules/product/file/tip/uom.xml#l63 - http://hg.tryton.org/modules/product/file/tip/uom.xml#l312
    # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/product/product.py#L89
    # mozda da ovi entiteti budu non-deletable i non-editable ??
    # composite index: ancestor:no - active,name
    name = ndb.StringProperty('1', required=True)
    symbol = ndb.StringProperty('2', required=True, indexed=False)# ukljuciti index ako bude trebao za projection query
    rate = DecimalProperty('3', required=True, indexed=False)# The coefficient for the formula: 1 (base unit) = coef (this unit) - digits=(12, 12)
    factor = DecimalProperty('4', required=True, indexed=False)# The coefficient for the formula: coef (base unit) = 1 (this unit) - digits=(12, 12)
    rounding = DecimalProperty('5', required=True, indexed=False)# Rounding Precision - digits=(12, 12)
    digits = ndb.IntegerProperty('6', required=True, indexed=False)
    active = ndb.BooleanProperty('7', default=True)

# done!
class Currency(ndb.Model):
    
    # root
    # http://hg.tryton.org/modules/currency/file/tip/currency.py#l14
    # http://en.wikipedia.org/wiki/ISO_4217
    # http://hg.tryton.org/modules/currency/file/tip/currency.xml#l107
    # http://bazaar.launchpad.net/~openerp/openobject-server/7.0/view/head:/openerp/addons/base/res/res_currency.py#L32
    # composite index: ancestor:no - active,name
    name = ndb.StringProperty('1', required=True)
    symbol = ndb.StringProperty('2', required=True, indexed=False)# ukljuciti index ako bude trebao za projection query
    code = ndb.StringProperty('3', required=True, indexed=False)# ukljuciti index ako bude trebao za projection query
    numeric_code = ndb.StringProperty('4', indexed=False)
    rounding = DecimalProperty('5', required=True, indexed=False)
    digits = ndb.IntegerProperty('6', required=True, indexed=False)
    active = ndb.BooleanProperty('7', default=True)
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

# done!
# ostaje da se ispita u preprodukciji!!
class Message(ndb.Model):
    
    # root
    outlet = ndb.IntegerProperty('1', required=True, indexed=False)
    group = ndb.IntegerProperty('2', required=True, indexed=False)
    state = ndb.IntegerProperty('3', required=True)

################################################################################
# OBJECT LOG - 1
################################################################################

# done!
class ObjectLog(ndb.Expando):
    
    # ancestor Any - ancestor je objekat koji se ujedno i pickle u log property, i moze biti bilo koji objekat osim pojedinih objekata koji su independent
    # reference i type izvlacimo iz kljuca - key.parent()
    # composite index: ???
    logged = ndb.DateTimeProperty('1', auto_now_add=True, required=True)
    agent = ndb.KeyProperty('2', kind=User, required=True)
    action = ndb.IntegerProperty('3', required=True)
    state = ndb.IntegerProperty('4', required=True)
    _default_indexed = False
    pass
    # message / m = ndb.TextProperty('5')# soft limit 64kb - to determine char count
    # note / n = ndb.TextProperty('6')# soft limit 64kb - to determine char count
    # log / l = ndb.PickleProperty('7')
    
    # ovako se smanjuje storage u Datastore, i trebalo bi sprovesti to isto na sve modele
    @classmethod
    def _get_kind(cls):
      return datastore_key_kinds.ObjectLog
