#coding=UTF-8
# http://www.python.org/dev/peps/pep-0008/

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
import re

# mozda ce nam trebati mehanizam da mozemo u constructoru supply keyword arguemnte kao napr:  digits=int(2), rounding=...
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

# done! - ovde ce nam trebati kontrola - treba odluciti konvenciju imenovanja objekata!
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
        domain = Domain(name=var_name, primary_contact=user_key, state='active')
        domain_key = domain.put()
        object_log = ObjectLog(parent=domain_key, agent=user_key, action='create', state=domain.state, log=domain)
        object_log.put()
        role = DomainRole(namespace=domain_key, name='Domain Admins', permissions=['*',], readonly=True)
        role_key = role.put()
        object_log = ObjectLog(parent=role_key, agent=user_key, action='create', state='none', log=role)
        object_log.put()
        domain_user = DomainUser(namespace=domain_key, id=str(user_key.id()), name='Administrator', user=user_key, roles=[role_key,], state='accepted')
        domain_user_key = domain_user.put()
        object_log = ObjectLog(parent=domain_user_key, agent=user_key, action='accept', state=domain_user.state, log=domain_user)
        object_log.put()
        user = user_key.get()
        user.roles.append(role_key)
        user_key = user.put()
        object_log = ObjectLog(parent=user_key, agent=user_key, action='update', state=user.state, log=user)
        object_log.put()
        
    
    # Ova akcija azurira postojecu domenu.
    @ndb.transactional
    def update():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'update-Domain'.
        # akcija se moze pozvati samo ako je domain.state == 'active'.
        domain.name = var_name
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

# done!
class DomainRole(ndb.Model):
    
    # root (namespace Domain)
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
    
    # Pravi novu domain rolu
    @ndb.transactional
    def create():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'create-DomainRole'. 
        # akcija se moze pozvati samo ako je domain.state == 'active'.
        role = DomainRole(name=var_name, permissions=var_permissions, readonly=False) # readonly je uvek False za user generated Roles
        role_key = role.put()
        object_log = ObjectLog(parent=role_key, agent=agent_key, action='create', state='none', log=role)
        object_log.put()
    
    # Azurira postojecu domain rolu
    @ndb.transactional
    def update():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'update-DomainRole'.
        # akcija se moze pozvati samo ako je domain.state == 'active'.
        role.name = var_name
        role.permissions = var_permissions
        role_key = role.put()
        object_log = ObjectLog(parent=role_key, agent=agent_key, action='update', state='none', log=role)
        object_log.put()
    
    # Brise postojecu domain rolu
    @ndb.transactional
    def delete():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'delete-DomainRole'.
        # akcija se moze pozvati samo ako je domain.state == 'active'.
        object_log = ObjectLog(parent=role_key, agent=agent_key, action='delete', state='none')
        object_log.put()
        domain_users = DomainUser.query(DomainUser.roles == role_key).fetch()
        user_keys = []
        for domain_user in domain_users:
            domain_user.roles.remove(role_key)
            domain_user_key = domain_user.put()
            object_log = ObjectLog(parent=domain_user_key, agent=agent_key, action='update', state=domain_user.state, log=domain_user)
            object_log.put()
            user_keys.append(domain_user.user)
        users = ndb.get_multi(user_keys)
        for user in users:
            user.roles.remove(role_key)
            user_key = user.put()
            object_log = ObjectLog(parent=user_key, agent=agent_key, action='update', state=user.state, log=user)
            object_log.put()
        domain_role_key.delete()

# done!
class DomainUser(ndb.Expando):
    
    # root (namespace Domain) - id = str(user_key.id())
    # mozda bude trebalo jos indexa u zavistnosti od potreba u UIUX
    # composite index: ancestor:no - name
    name = ndb.StringProperty('1', required=True)# ovo je deskriptiv koji administratoru sluzi kako bi lakse spoznao usera
    user = ndb.KeyProperty('2', kind=User, required=True)
    roles = ndb.KeyProperty('3', kind=DomainRole, repeated=True)# vazno je osigurati da se u ovoj listi ne nadju duplikati rola, jer to onda predstavlja security issue!!
    state = ndb.IntegerProperty('4', required=True)# invited/accepted
    _default_indexed = False
    pass
    #Expando
    
    _KIND = 0
    
    OBJECT_DEFAULT_STATE = 'invited'
    
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
       'update' : 4,
    }
    
    OBJECT_TRANSITIONS = {
        'accept' : {
            'from' : ('invited',),
            'to' : ('accepted',),
        },
    }
    
    # Poziva novog usera u domenu
    @ndb.transactional
    def invite():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'invite-DomainUser'.
        # akcija se moze pozvati samo ako je domain.state == 'active'.
        user = var_user.get()
        if (user.state == 'active'):# da li uvoditi ovaj check jos negde, ili ga izbaciti i odavde ? 
            domain_user = DomainUser(id=str(var_user.id()), name=var_name, user=var_user, roles=var_roles, state='invited')
            domain_user_key = domain_user.put()
            object_log = ObjectLog(parent=domain_user_key, agent=agent_key, action='invite', state=domain_user.state, log=domain_user)
            object_log.put()
            # salje se notifikacija korisniku da je dobio poziv za dodavanje u Domenu.
    
    # Uklanja postojeceg usera iz domene
    @ndb.transactional
    def remove():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'remove-DomainUser', ili agent koji je referenciran u entitetu (domain_user.user == agent).
        # agent koji je referenciran u domain.primary_contact prop. ne moze biti izbacen iz domene i izgubiti dozvole za upravljanje domenom.
        # akcija se moze pozvati samo ako je domain.state == 'active'.
        user = domain_user.user.get()
        for role in domain_user.roles:
            user.roles.remove(role)
        user_key = user.put()
        object_log = ObjectLog(parent=user_key, agent=agent_key, action='update', state=user.state, log=user)
        object_log.put()
        object_log = ObjectLog(parent=domain_user_key, agent=agent_key, action='remove', state=domain_user.state)
        object_log.put()
        domain_user_key.delete()
    
    # Prihvata poziv novog usera u domenu
    @ndb.transactional
    def accept():
        # ovu akciju moze izvrsiti samo agent koji je referenciran u entitetu (domain_user.user == agent).
        # akcija se moze pozvati samo ako je domain.state == 'active'.
        domain_user.state = 'accepted'
        domain_user_key = domain_user.put()
        object_log = ObjectLog(parent=domain_user_key, agent=agent_key, action='accept', state=domain_user.state)
        object_log.put()
        user = domain_user.user.get()
        for role in domain_user.roles:
            user.roles.append(role)
        user_key = user.put()
        object_log = ObjectLog(parent=user_key, agent=agent_key, action='update', state=user.state, log=user)
        object_log.put()
    
    # Azurira postojeceg usera u domeni
    @ndb.transactional
    def update():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'update-DomainUser'.
        # akcija se moze pozvati samo ako je domain.state == 'active'.
        old_roles = domain_user.roles
        domain_user.name = var_name
        domain_user.roles = var_roles
        domain_user_key = domain_user.put()
        object_log = ObjectLog(parent=domain_user_key, agent=agent_key, action='update', state=domain_user.state, log=domain_user)
        object_log.put()
        user = domain_user.user.get()
        for role in old_roles:
            user.roles.remove(role)
        for role in domain_user.roles:
            user.roles.append(role)
        user_key = user.put()
        object_log = ObjectLog(parent=user_key, agent=agent_key, action='update', state=user.state, log=user)
        object_log.put()

# future implementation - prototype!
class DomainRule(ndb.Model):
    
    # root (namespace Domain)
    name = ndb.StringProperty('1', required=True)
    model_kind = ndb.StringProperty('2', required=True)
    actions = ndb.StringProperty('3', repeated=True)
    fields = ndb.LocalStructuredProperty(Field, '4', repeated=True)
    condition = ndb.TextProperty('5')
    roles = ndb.KeyProperty('6', kind=DomainRole, repeated=True)

# future implementation - prototype!
class DomainField(ndb.Model):
    
    # LocalStructuredProperty model
    name = ndb.StringProperty('1', required=True, indexed=False)
    writable = ndb.BooleanProperty('2', default=True, indexed=False)
    visible = ndb.BooleanProperty('3', default=True, indexed=False)

# done! mozda bude trebala kontrola i ovde
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
    # company_region = ndb.KeyProperty('6', kind=CountrySubdivision, required=True)# ako je potreban string val onda se ovo preskace / tryton ima CountrySubdivision za skoro sve zemlje
    # company_region = ndb.StringProperty('6', required=True)# ako je potreban key val onda se ovo preskace / tryton ima CountrySubdivision za skoro sve zemlje
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
    
    
    _KIND = 0
    
    OBJECT_DEFAULT_STATE = 'open'
    
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
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'create-DomainStore'.
        # akcija se moze pozvati samo ako je domain.state == 'active'.
        store = DomainStore(name=var_name, logo=var_logo, state='open')
        store_key = store.put()
        object_log = ObjectLog(parent=store_key, agent=agent_key, action='create', state=store.state, log=store)
        object_log.put()
    
    # Ova akcija azurira postojeci store.
    @ndb.transactional
    def update():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'update-DomainStore'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i store.state == 'open'.
        store.name = var_name
        store.logo = var_logo
        store_key = store.put()
        object_log = ObjectLog(parent=store_key, agent=agent_key, action='update', state=store.state, log=store)
        object_log.put()
    
    # Ova akcija zatvara otvoren store. Ovde cemo dalje opisati posledice zatvaranja...
    @ndb.transactional
    def close():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'close-DomainStore'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i store.state == 'open'.
        store.state = 'closed'
        store_key = store.put()
        object_log = ObjectLog(parent=store_key, agent=agent_key, action='close', state=store.state, message='poruka od agenta - obavezno polje!', note='privatni komentar agenta (dostupan samo privilegovanim agentima) - obavezno polje!')
        object_log.put()
    
    # Ova akcija otvara zatvoreni store. Ovde cemo dalje opisati posledice otvaranja...
    @ndb.transactional
    def open():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'open-DomainStore'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i store.state == 'closed'.
        store.state = 'open'
        store_key = store.put()
        object_log = ObjectLog(parent=store_key, agent=agent_key, action='open', state=store.state, message='poruka od agenta - obavezno polje!', note='privatni komentar agenta (dostupan samo privilegovanim agentima) - obavezno polje!')
        object_log.put()

# done!
class DomainStoreFeedback(ndb.Model):
    
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
class DomainStoreContent(ndb.Model):
    
    # ancestor DomainStore (Catalog, for caching) (namespace Domain)
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
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'create-DomainStoreContent'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i store.state == 'open'.
        store_content = DomainStoreContent(parent=store_key, title=var_title, body=var_body, sequence=var_sequence)
        store_content_key = store_content.put()
        object_log = ObjectLog(parent=store_content_key, agent=agent_key, action='create', state='none', log=store_content)
        object_log.put()
    
    # Ova akcija azurira store content.
    @ndb.transactional
    def update():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'update-DomainStoreContent'.
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
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'delete-DomainStoreContent'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i store.state == 'open'.
        object_log = ObjectLog(parent=store_content_key, agent=agent_key, action='delete', state='none')
        object_log.put()
        store_content_key.delete()

# done!
class DomainStoreShippingExclusion(Location):
    
    # ancestor DomainStore (DomainCatalog, for caching) (namespace Domain)
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
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'create-DomainStoreShippingExclusion'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i store.state == 'open'.
        store_shipping_exclusion = DomainStoreShippingExclusion(parent=store_key, country=var_country)
        store_shipping_exclusion_key = store_shipping_exclusion.put()
        object_log = ObjectLog(parent=store_shipping_exclusion_key, agent=agent_key, action='create', state='none', log=store_shipping_exclusion)
        object_log.put()
    
    # Ova akcija azurira store shipping exclusion.
    @ndb.transactional
    def update():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'update-DomainStoreShippingExclusion'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i store.state == 'open'.
        store_shipping_exclusion.country = var_country
        store_shipping_exclusion_key = store_shipping_exclusion.put()
        object_log = ObjectLog(parent=store_shipping_exclusion_key, agent=agent_key, action='update', state='none', log=store_shipping_exclusion)
        object_log.put()
    
    # Ova akcija brise store shipping exclusion.
    @ndb.transactional
    def delete():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'delete-DomainStoreShippingExclusion'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i store.state == 'open'.
        object_log = ObjectLog(parent=store_shipping_exclusion_key, agent=agent_key, action='delete', state='none')
        object_log.put()
        store_shipping_exclusion_key.delete()

# done!
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
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'create-DomainTax'.
        # akcija se moze pozvati samo ako je domain.state == 'active'.
        tax = DomainTax(name=var_name, sequence=var_sequence, amount=var_amount, location_exclusion=var_location_exclusion, active=True)
        tax_key = tax.put()
        object_log = ObjectLog(parent=tax_key, agent=agent_key, action='create', state='none', log=tax)
        object_log.put()
    
    # Ova akcija azurira taxu.
    @ndb.transactional
    def update():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'update-DomainTax'.
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
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'delete-DomainTax'.
        # akcija se moze pozvati samo ako je domain.state == 'active'.
        object_log = ObjectLog(parent=tax_key, agent=agent_key, action='delete', state='none')
        object_log.put()
        tax_key.delete()

# done!
class DomainCarrier(ndb.Model):
    
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
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'create-DomainCarrier'.
        # akcija se moze pozvati samo ako je domain.state == 'active'.
        carrier = DomainCarrier(name=var_name, active=True)
        carrier_key = carrier.put()
        object_log = ObjectLog(parent=carrier_key, agent=agent_key, action='create', state='none', log=carrier)
        object_log.put()
    
    # Ova akcija azurira carrier.
    @ndb.transactional
    def update():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'update-DomainCarrier'.
        # akcija se moze pozvati samo ako je domain.state == 'active'.
        carrier.name = var_name
        carrier.active = var_active
        carrier_key = carrier.put()
        object_log = ObjectLog(parent=carrier_key, agent=agent_key, action='update', state='none', log=carrier)
        object_log.put()
    
    # Ova akcija brise carrier.
    @ndb.transactional
    def delete():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'delete-DomainCarrier'.
        # akcija se moze pozvati samo ako je domain.state == 'active'.
        object_log = ObjectLog(parent=carrier_key, agent=agent_key, action='delete', state='none')
        object_log.put()
        carrier_lines = DomainCarrierLine.query(ancestor=carrier_key).fetch(keys_only=True)
        # ovaj metod ne loguje brisanje pojedinacno svakog carrier_line entiteta, pa se trebati ustvari pozivati DomainCarrierLine.delete() sa listom kljuceva.
        # DomainCarrierLine.delete() nije za sada nije opisana da radi multi key delete.
        # a mozda je ta tehnika nepotrebna, posto se logovanje brisanja samog DomainCarrier entiteta podrazumvea da su svi potomci izbrisani!!
        ndb.delete_multi(carrier_lines)
        carrier_key.delete()

# done!
class DomainCarrierLine(ndb.Expando):
    
    # ancestor DomainCarrier (namespace Domain)
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
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'create-DomainCarrierLine'.
        # akcija se moze pozvati samo ako je domain.state == 'active'.
        carrier_line = DomainCarrierLine(parent=carrier_key, name=var_name, sequence=var_sequence, location_exclusion=var_location_exclusion, active=True)
        carrier_line_key = carrier_line.put()
        object_log = ObjectLog(parent=carrier_line_key, agent=agent_key, action='create', state='none', log=carrier_line)
        object_log.put()
    
    # Ova akcija azurira carrier line.
    @ndb.transactional
    def update():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'update-DomainCarrierLine'.
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
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'delete-DomainCarrierLine'.
        # akcija se moze pozvati samo ako je domain.state == 'active'.
        object_log = ObjectLog(parent=carrier_line_key, agent=agent_key, action='delete', state='none')
        object_log.put()
        carrier_line_key.delete()

# done!
class DomainCarrierLineRule(ndb.Model):
    
    # LocalStructuredProperty model
    # http://bazaar.launchpad.net/~openerp/openobject-addons/saas-1/view/head:/delivery/delivery.py#L226
    # ovde se cuvaju dve vrednosti koje su obicno struktuirane kao formule, ovo je mnogo fleksibilnije nego hardcoded struktura informacija koje se cuva kao sto je bio prethodni slucaj
    condition = ndb.StringProperty('1', required=True, indexed=False)# prekompajlirane vrednosti iz UI, napr: True ili weight[kg] >= 5 ili volume[m3] = 0.002
    price = ndb.StringProperty('2', required=True, indexed=False)# prekompajlirane vrednosti iz UI, napr: amount = 35.99 ili amount = weight[kg]*0.28
    # weight - kg; volume - m3; ili sta vec odlucimo, samo je bitno da se podudara sa measurementsima na ProductTemplate/ProductInstance

# done! - ovde ce nam trebati kontrola
class DomainCatalog(ndb.Expando):
    
    # root (namespace Domain)
    # https://support.google.com/merchants/answer/188494?hl=en&hlrm=en#other
    # composite index: ???
    store = ndb.KeyProperty('1', kind=DomainStore, required=True)
    name = ndb.StringProperty('2', required=True)
    publish = ndb.DateTimeProperty('3', required=True)# today
    discontinue = ndb.DateTimeProperty('4', required=True)# +30 days
    state = ndb.IntegerProperty('5', required=True)
    _default_indexed = False
    pass
    # Expando
    # cover = blobstore.BlobKeyProperty('6', required=True)# blob ce se implementirati na GCS
    # cost = DecimalProperty('7', required=True)
    # Search improvements
    # product count per product category
    # rank coefficient based on store feedback
    
    _KIND = 0
    
    OBJECT_DEFAULT_STATE = 'unpublished'
    
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
    
    # nedostaju akcije za dupliciranje catalog-a, za clean-up, etc...
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
    
    # Ova akcija kreira novi catalog.
    @ndb.transactional
    def create():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'create-DomainCatalog'.
        # akcija se moze pozvati samo ako je domain.state == 'active'.
        catalog = DomainCatalog(store=store_key, name=var_name, publish=var_publish, discontinue=var_discontinue, state='unpublished')
        catalog_key = catalog.put()
        object_log = ObjectLog(parent=catalog_key, agent=agent_key, action='create', state=catalog.state, log=catalog)
        object_log.put()
    
    # Ova akcija azurira postojeci catalog.
    @ndb.transactional
    def update():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'update-DomainCatalog'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i catalog.state == 'unpublished'.
        catalog.store = var_store
        catalog.name = var_name
        catalog.publish = var_publish
        catalog.discontinue = var_discontinue
        catalog.state = var_state
        catalog_key = catalog.put()
        object_log = ObjectLog(parent=catalog_key, agent=agent_key, action='update', state=catalog.state, log=catalog)
        object_log.put()
    
    # Ova akcija zakljucava unpublished catalog. Ovde cemo dalje opisati posledice zatvaranja...
    @ndb.transactional
    def lock():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'publish-DomainCatalog'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i catalog.state == 'unpublished'.
        # radimo update catalog-a sa novim cover-om - ovde cemo verovatno raditi i presnimavanje entiteta iz store-a za koji je zakacen catalog, i svega ostalog sto je neophodno.
        catalog_cover = DomainCatalogImage.query(ancestor=catalog_key).order(DomainCatalogImage.sequence).fetch(1, keys_only=True)
        catalog.cover = catalog_cover
        catalog_key = catalog.put()
        object_log = ObjectLog(parent=catalog_key, agent=agent_key, action='update', state=catalog.state, log=catalog)
        object_log.put()
        # zakljucavamo catalog
        catalog.state = 'locked'
        catalog_key = catalog.put()
        object_log = ObjectLog(parent=catalog_key, agent=agent_key, action='lock', state=catalog.state, message='poruka od agenta - obavezno polje!', note='privatni komentar agenta (dostupan samo privilegovanim agentima) - obavezno polje!')
        object_log.put()
    
    # Ova akcija objavljuje locked catalog. Ovde cemo dalje opisati posledice zatvaranja...
    @ndb.transactional
    def publish():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'publish-DomainCatalog'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i catalog.state == 'locked'.
        catalog.state = 'published'
        catalog_key = catalog.put()
        object_log = ObjectLog(parent=catalog_key, agent=agent_key, action='publish', state=catalog.state, message='poruka od agenta - obavezno polje!', note='privatni komentar agenta (dostupan samo privilegovanim agentima) - obavezno polje!')
        object_log.put()
    
    # Ova akcija prekida objavljen catalog. Ovde cemo dalje opisati posledice zatvaranja...
    @ndb.transactional
    def discontinue():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'discontinue-DomainCatalog'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i catalog.state == 'published'.
        catalog.state = 'discontinued'
        catalog_key = catalog.put()
        object_log = ObjectLog(parent=catalog_key, agent=agent_key, action='discontinue', state=catalog.state, message='poruka od agenta - obavezno polje!', note='privatni komentar agenta (dostupan samo privilegovanim agentima) - obavezno polje!')
        object_log.put()

# done!
class DomainCatalogImage(Image):
    
    # ancestor DomainCatalog (namespace Domain)
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
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'create-DomainCatalogImage'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i catalog.state == 'unpublished'.
        catalog_image = DomainCatalogImage(parent=catalog_key, image=var_image, content_type=var_content_type, size=var_size, width=var_width, height=var_height, sequence=var_sequence)
        catalog_image_key = catalog_image.put()
        object_log = ObjectLog(parent=catalog_image_key, agent=agent_key, action='create', state='none', log=catalog_image)
        object_log.put()
    
    # Ova akcija menja raspored slike u catalog-u.
    @ndb.transactional
    def update():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'update-DomainCatalogImage'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i catalog.state == 'unpublished'.
        catalog_image.sequence = var_sequence
        catalog_image_key = catalog_image.put()
        object_log = ObjectLog(parent=catalog_image_key, agent=agent_key, action='update', state='none', log=catalog_image)
        object_log.put()
    
    # Ova akcija brise sliku.
    @ndb.transactional
    def delete():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'delete-DomainCatalogImage'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i catalog.state == 'unpublished'.
        object_log = ObjectLog(parent=catalog_image_key, agent=agent_key, action='delete', state='none')
        object_log.put()
        catalog_image_key.delete()

# done!
class DomainCatalogPricetag(ndb.Model):
    
    # ancestor DomainCatalog (namespace Domain)
    product_template = ndb.KeyProperty('1', kind=DomainProductTemplate, required=True, indexed=False)
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
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'create-DomainCatalogPricetag'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i catalog.state == 'unpublished'.
        catalog_pricetag = DomainCatalogPricetag(parent=catalog_key, product_template=var_product_template, container_image=var_container_image, source_width=var_source_width, source_height=var_source_height, source_position_top=var_source_position_top, source_position_left=var_source_position_left, value=var_value)
        catalog_pricetag_key = catalog_pricetag.put()
        object_log = ObjectLog(parent=catalog_pricetag_key, agent=agent_key, action='create', state='none', log=catalog_pricetag)
        object_log.put()
    
    # Ova akcija azurira pricetag na catalog-u.
    @ndb.transactional
    def update():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'update-DomainCatalogPricetag'.
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
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'delete-DomainCatalogPricetag'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i catalog.state == 'unpublished'.
        object_log = ObjectLog(parent=catalog_pricetag_key, agent=agent_key, action='delete', state='none')
        object_log.put()
        catalog_pricetag_key.delete()

# done!
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
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'create-DomainProductTemplate'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i catalog.state == 'unpublished'.
        product_template = DomainProductTemplate(parent=catalog_key, product_category=var_product_category, name=var_name, description=var_description, product_uom=var_product_uom, unit_price=var_unit_price, availability=var_availability)
        product_template_key = product_template.put()
        object_log = ObjectLog(parent=product_template_key, agent=agent_key, action='create', state='none', log=product_template)
        object_log.put()
    
    # Ova akcija azurira product template.
    @ndb.transactional
    def update():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'update-DomainProductTemplate'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i catalog.state == 'unpublished'.
        product_template.product_category = var_product_category
        product_template.name = var_name
        product_template.description = var_description
        product_template.product_uom = var_product_uom
        product_template.unit_price = var_unit_price
        product_template.availability = var_availability
        product_template_key = product_template.put()
        object_log = ObjectLog(parent=product_template_key, agent=agent_key, action='update', state='none', log=product_template)
        object_log.put()
    
    # Ova akcija brise product template.
    @ndb.transactional
    def delete():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'delete-DomainProductTemplate'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i catalog.state == 'unpublished'.
        object_log = ObjectLog(parent=product_template_key, agent=agent_key, action='delete', state='none')
        object_log.put()
        product_instances = DomainProductInstance.query(ancestor=product_template_key).fetch(keys_only=True)
        # ovaj metod ne loguje brisanje pojedinacno svakog product_instance entiteta, pa se treba ustvari pozivati DomainProductInstance.delete() sa listom kljuceva.
        # DomainProductInstance.delete() nije za sada opisana da radi multi key delete.
        # a mozda je ta tehnika nepotrebna, posto se logovanje brisanja samog DomainProductTemplate entiteta podrazumvea da su svi children izbrisani!!
        ndb.delete_multi(product_instances)
        product_template_key.delete()
    
    # Ova akcija generise product instance.
    @ndb.transactional
    def generate_product_instances():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'generate_product_instances-DomainProductTemplate'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i catalog.state == 'unpublished'.
        # ova funkcija ce se u potpunosti oslanjati na task queue kako bi se resio problem velikog broja pravljenja/brisanja instanci.
        # brisemo postojece product instance - imamo problem sto se brisanje product instanci ne loguje
        product_instances = DomainProductInstance.query(ancestor=product_template_key).fetch(keys_only=True)
        ndb.delete_multi(product_instances)
        # brisemo postojece product inventory logove - imamo problem sto se brisanje product inventory logova ne loguje
        product_inventory_logs = DomainProductInventoryLog.query(ancestor=product_template_key).fetch(keys_only=True)
        ndb.delete_multi(product_inventory_logs)
        # brisemo postojece product inventory adjustment-e - imamo problem sto se brisanje product inventory adjustment-a ne loguje
        product_inventory_adjustments = DomainProductInventoryAdjustment.query(ancestor=product_template_key).fetch(keys_only=True)
        ndb.delete_multi(product_inventory_adjustments)
        # pripremamo listu varianti za product template
        # primer:
        # variants = [
            # {'name': 'Color', 'options': ['Red', 'Green', 'Blue'], 'position': 0, 'increment': False, 'reset': False},
            # {'name': 'Size', 'options': ['Small', 'Medium', 'Large'], 'position': 0, 'increment': False, 'reset': False},
            # {'name': 'Fabric', 'options': ['Silk', 'Cotton'], 'position': 0, 'increment': False, 'reset': False},
        # ]
        variants []
        for key in product_template.variants:
            product_template_variant = key.get()
            dic = {}
            dic['name'] = product_template_variant.name
            dic['options'] = product_template_variant.options
            dic['position'] = 0
            dic['increment'] = False
            dic['reset'] = False
            variants.append(dic)
        # generisemo sve moguce kombinacije variacija koje product instance moze imati
        # primer:
        # variant_signatures = [
            # {'Color': 'Red', 'Size': 'Small', 'Fabric': 'Silk'},
            # {'Color': 'Green', 'Size': 'Small', 'Fabric': 'Silk'},
            # {'Color': 'Blue', 'Size': 'Small', 'Fabric': 'Silk'},
            # {'Color': 'Red', 'Size': 'Medium', 'Fabric': 'Silk'},
            # {'Color': 'Green', 'Size': 'Medium', 'Fabric': 'Silk'},
            # {'Color': 'Blue', 'Size': 'Medium', 'Fabric': 'Silk'},
            # {'Color': 'Red', 'Size': 'Large', 'Fabric': 'Silk'},
            # {'Color': 'Green', 'Size': 'Large', 'Fabric': 'Silk'},
            # {'Color': 'Blue', 'Size': 'Large', 'Fabric': 'Silk'},
            # {'Color': 'Red', 'Size': 'Small', 'Fabric': 'Cotton'},
            # {'Color': 'Green', 'Size': 'Small', 'Fabric': 'Cotton'},
            # {'Color': 'Blue', 'Size': 'Small', 'Fabric': 'Cotton'},
            # {'Color': 'Red', 'Size': 'Medium', 'Fabric': 'Cotton'},
            # {'Color': 'Green', 'Size': 'Medium', 'Fabric': 'Cotton'},
            # {'Color': 'Blue', 'Size': 'Medium', 'Fabric': 'Cotton'},
            # {'Color': 'Red', 'Size': 'Large', 'Fabric': 'Cotton'},
            # {'Color': 'Green', 'Size': 'Large', 'Fabric': 'Cotton'},
            # {'Color': 'Blue', 'Size': 'Large', 'Fabric': 'Cotton'},
        # ]
        variant_signatures = []
        stay = True
        while stay:
            i = 0
            for item in variants:
                if (item['increment']):
                    variants[i]['position'] += 1
                    variants[i]['increment'] = False
                if (item['reset']):
                    variants[i]['position'] = 0
                    variants[i]['reset'] = False
                i += 1
            dic = {}
            i = 0
            for item in variants:
                dic[item['name']] = item['options'][item['position']]
                if (i == 0):
                    if (len(item['options']) == item['position'] + 1):
                        variants[i]['reset'] = True
                        variants[i + 1]['increment'] = True
                    else:
                        variants[i]['increment'] = True
                elif not (len(variants) == i + 1):
                    if (len(item['options']) == item['position'] + 1):
                        if (variants[i - 1]['reset']):
                            variants[i]['reset'] = True
                            variants[i + 1]['increment'] = True
                elif (len(variants) == i + 1):
                    if (len(item['options']) == item['position'] + 1):
                        if (variants[i - 1]['reset']):
                            stay = False
                            break
                i += 1
            variant_signatures.append(dic)
        product_template.product_instance_count = len(variant_signatures)
        product_template_key = product_template.put()
        object_log = ObjectLog(parent=product_template_key, agent=agent_key, action='generate_product_instances', state='none', log=product_template)
        object_log.put()
        # postavljamo limit na broju product instanci koje mogu biti generisane
        if (len(variant_signatures) <= 1000):
            i = 0
            for variant_signature in variant_signatures:
                var_code = product_template_key + "-" + i
                product_instance = DomainProductInstance(parent=product_template_key, code=var_code)
                product_instance_key = product_instance.put()
                object_log = ObjectLog(parent=product_instance_key, agent=agent_key, action='create', state='none', log=product_instance)
                object_log.put()
                i += 1

# done!
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
    
    _KIND = 0
    
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'update' : 1,
    }
    
    # Ova akcija azurira product instance.
    @ndb.transactional
    def update():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'update-DomainProductInstance'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i catalog.state == 'unpublished'.
        # u slucaju da je catalog.state == 'published' onda je moguce editovanje samo product_instance.availability i product_instance.low_stock_quantity
        product_instance.code = var_code
        product_instance_key = product_instance.put()
        object_log = ObjectLog(parent=product_instance_key, agent=agent_key, action='update', state='none', log=product_instance)
        object_log.put()

# done! contention se moze zaobici ako write-ovi na ove entitete budu explicitno izolovani preko task queue
class DomainProductInventoryLog(ndb.Model):
    
    # ancestor DomainProductInstance
    # key za DomainProductInventoryLog ce se graditi na sledeci nacin:
    # key: parent=domain_product_instance.key, id=str(reference_key) ili mozda neki drugi destiled id iz key-a
    # idempotency je moguc ako se pre inserta proverava da li postoji record sa id-jem reference_key
    # not logged
    # composite index: ancestor:yes - logged:desc
    logged = ndb.DateTimeProperty('1', auto_now_add=True, required=True)
    quantity = DecimalProperty('3', required=True, indexed=False)# ukljuciti index ako bude trebao za projection query
    balance = DecimalProperty('4', required=True, indexed=False)# ukljuciti index ako bude trebao za projection query

# done!
class DomainProductInventoryAdjustment(ndb.Model):
    
    # ancestor DomainProductInstance (namespace Domain)
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
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'create-DomainProductInventoryAdjustment'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i catalog.state == 'published'. - mozda budemo dozvolili adjustment bez obzira na catalog.state
        product_inventory_adjustment = DomainProductInventoryAdjustment(parent=product_instance_key, agent=agent_key, quantity=var_quantity, comment=var_comment)
        product_inventory_adjustment_key = product_inventory_adjustment.put()
        object_log = ObjectLog(parent=product_inventory_adjustment_key, agent=agent_key, action='create', state='none', log=product_inventory_adjustment)
        object_log.put()
        # ovo bi trebalo ici preko task queue
        # idempotency je moguc ako se pre inserta proverava da li je record sa tim reference-om upisan
        product_inventory_log = DomainProductInventoryLog.query().order(-DomainProductInventoryLog.logged).fetch(1)
        new_product_inventory_log = DomainProductInventoryLog(parent=product_instance_key, id=str(product_inventory_adjustment_key), quantity=product_inventory_adjustment.quantity, balance=product_inventory_log.balance + product_inventory_adjustment.quantity)
        new_product_inventory_log.put()

# done!
class DomainProductVariant(ndb.Model):
    
    # ancestor DomainCatalog (future - root) (namespace Domain)
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
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'create-DomainProductVariant'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i catalog.state == 'unpublished'.
        product_variant = DomainProductVariant(parent=catalog_key, name=var_name, description=var_description, options=var_options, allow_custom_value=var_allow_custom_value)
        product_variant_key = product_variant.put()
        object_log = ObjectLog(parent=product_variant_key, agent=agent_key, action='create', state='none', log=product_variant)
        object_log.put()
    
    # Ova akcija azurira product variant.
    @ndb.transactional
    def update():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'update-DomainProductVariant'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i catalog.state == 'unpublished'.
        product_variant.name = var_name
        product_variant.description = var_description
        product_variant.options = var_options
        product_variant.allow_custom_value = var_allow_custom_value
        product_variant_key = product_variant.put()
        object_log = ObjectLog(parent=product_variant_key, agent=agent_key, action='update', state='none', log=product_variant)
        object_log.put()

# done!
class DomainProductContent(ndb.Model):
    
    # ancestor DomainCatalog (future - root) (namespace Domain)
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
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'create-DomainProductContent'.
        # akcija se moze pozvati samo ako je domain.state == 'active' i catalog.state == 'unpublished'.
        product_content = DomainProductContent(parent=catalog_key, title=var_title, body=var_body)
        product_content_key = product_content.put()
        object_log = ObjectLog(parent=product_content_key, agent=agent_key, action='create', state='none', log=product_content)
        object_log.put()
    
    # Ova akcija azurira product content.
    @ndb.transactional
    def update():
        # ovu akciju moze izvrsiti samo agent koji ima domain-specific dozvolu 'update-DomainProductContent'.
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
    identities = ndb.StructuredProperty(UserIdentity, '1', repeated=True)# soft limit 100x
    emails = ndb.StringProperty('2', repeated=True)# soft limit 100x
    state = ndb.IntegerProperty('3', required=True)
    _default_indexed = False
    pass
    #Expando
    # roles = ndb.KeyProperty('4', kind=DomainRole, repeated=True)
    
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
        var_identities = []
        var_emails = []
        var_identities.append(UserIdentity(identity=var_identity, email=var_email, associated=True, primary=True))
        var_emails.append(var_email)
        user = User(identities=var_identities, emails=var_emails, state='active')
        user_key = user.put()
        object_log = ObjectLog(parent=user_key, agent=user_key, action='register', state=user.state, log=user)
        object_log.put()
        # UserIPAddress se pravi nakon pravljenja ObjectLog-a zato sto se ne loguje.
        user_ip_address = UserIPAddress(parent=user_key, ip_address=var_ip_address)
        user_ip_address.put()
    
    # Ova akcija radi insert/update/delete na neki prop. (izuzev state) u User objektu.
    @ndb.transactional
    def update():
        user.emails = var_emails
        user.identities = var_identities
        user_key = user.put()
        object_log = ObjectLog(parent=user_key, agent=agent_key, action='update', state=user.state, log=user)
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
        object_log = ObjectLog(parent=user_key, agent=agent_key, action='suspend', state=user.state, message='poruka od agenta - obavezno polje!', note='privatni komentar agenta (dostupan samo privilegovanim agentima) - obavezno polje!')
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
    # region = ndb.KeyProperty('8', kind=CountrySubdivision, required=True)# ako je potreban string val onda se ovo preskace / tryton ima CountrySubdivision za skoro sve zemlje 
    # region = ndb.StringProperty('8', required=True)# ako je potreban key val onda se ovo preskace / tryton ima CountrySubdivision za skoro sve zemlje
    # street_address2 = ndb.StringProperty('9')
    # email = ndb.StringProperty('10')
    # telephone = ndb.StringProperty('11')
    
    _KIND = 0
    
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
        buyer_address = BuyerAddress(parent=user_key, name=var_name, country=var_country, city=var_city, postal_code=var_postal_code, street_address=var_street_address, region=var_region)
        buyer_address_key = buyer_address.put()
        object_log = ObjectLog(parent=buyer_address_key, agent=user_key, action='create', state='none', log=buyer_address)
        object_log.put()
    
    # Azurira postojecu adresu korisnika
    @ndb.transactional
    def update():
        # ovu akciju moze izvrsiti samo vlasnik entiteta (buyer_address.parent == agent).
        buyer_address.name = var_name
        buyer_address.country = var_country
        buyer_address.city = var_city
        buyer_address.postal_code = var_postal_code
        buyer_address.street_address = var_street_address
        buyer_address.region = var_region
        buyer_address_key = buyer_address.put()
        object_log = ObjectLog(parent=buyer_address_key, agent=user_key, action='update', state='none', log=buyer_address)
        object_log.put()
    
    # Brise postojecu adresu korisnika
    @ndb.transactional
    def delete():
        # ovu akciju moze izvrsiti samo vlasnik entiteta (buyer_address.parent == agent).
        object_log = ObjectLog(parent=buyer_address_key, agent=user_key, action='delete', state='none')
        object_log.put()
        buyer_address_key.delete()

# done!
class BuyerCollection(ndb.Model):
    
    # ancestor User
    # mozda bude trebao index na primary_email radi mogucnosti update-a kada user promeni primarnu email adresu na svom profilu
    # composite index: ancestor:yes - name
    name = ndb.StringProperty('1', required=True)
    notify = ndb.BooleanProperty('2', default=False)
    primary_email = ndb.StringProperty('3', required=True, indexed=False)
    
    _KIND = 0
    
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    }
    
    # Pravi novu korisnikovu kolekciju
    @ndb.transactional
    def create():
        # ovu akciju moze izvrsiti samo registrovani autenticirani agent.
        for identity in user.identities:
            if(identity.primary == True):
                var_primary_email = identity.email
                break
        buyer_collection = BuyerCollection(parent=user_key, name=var_name, notify=var_notify, primary_email=var_primary_email)
        buyer_collection_key = buyer_collection.put()
        object_log = ObjectLog(parent=buyer_collection_key, agent=user_key, action='create', state='none', log=buyer_collection)
        object_log.put()
    
    # Azurira postojecu korisnikovu kolekciju
    @ndb.transactional
    def update():
        # ovu akciju moze izvrsiti samo vlasnik entiteta (buyer_collection.parent == agent).
        buyer_collection.name = var_name
        buyer_collection.notify = var_notify
        for identity in user.identities:
            if(identity.primary == True):
                var_primary_email = identity.email
                break
        buyer_collection.primary_email = var_primary_email
        buyer_collection_key = buyer_collection.put()
        object_log = ObjectLog(parent=buyer_collection_key, agent=user_key, action='update', state='none', log=buyer_collection)
        object_log.put()
    
    # Brise postojecu korisnikovu kolekciju
    @ndb.transactional
    def delete():
        # ovu akciju moze izvrsiti samo vlasnik entiteta (buyer_collection.parent == agent).
        object_log = ObjectLog(parent=buyer_collection_key, agent=user_key, action='delete', state='none')
        object_log.put()
        buyer_collection_key.delete()

# done!
class BuyerCollectionStore(ndb.Model):
    
    # ancestor User
    store = ndb.KeyProperty('1', kind=Store, required=True)
    collections = ndb.KeyProperty('2', kind=BuyerCollection, repeated=True)# soft limit 500x
    
    _KIND = 0
    
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    }
    
    # Dodaje novi store u korisnikovoj listi i odredjuje clanstvo u korisnikovim kolekcijama
    @ndb.transactional
    def create():
        # ovu akciju moze izvrsiti samo registrovani autenticirani agent.
        buyer_collection_store = BuyerCollectionStore(parent=user_key, store=var_store, collections=var_collections)
        buyer_collection_store_key = buyer_collection_store.put()
        object_log = ObjectLog(parent=buyer_collection_store_key, agent=user_key, action='create', state='none', log=buyer_collection_store)
        object_log.put()
        # izaziva se update AggregateBuyerCollectionCatalog preko task queue
    
    # Menja clanstvo store u korisnikovim kolekcijama
    @ndb.transactional
    def update():
        # ovu akciju moze izvrsiti samo vlasnik entiteta (buyer_collection_store.parent == agent).
        buyer_collection_store.collections = var_collections
        buyer_collection_store_key = buyer_collection_store.put()
        object_log = ObjectLog(parent=buyer_collection_store_key, agent=user_key, action='update', state='none', log=buyer_collection_store)
        object_log.put()
        # izaziva se update AggregateBuyerCollectionCatalog preko task queue
    
    # Brise store iz korisnikove liste
    @ndb.transactional
    def delete():
        # ovu akciju moze izvrsiti samo vlasnik entiteta (buyer_collection_store.parent == agent).
        object_log = ObjectLog(parent=buyer_collection_store_key, agent=user_key, action='delete', state='none')
        object_log.put()
        buyer_collection_store_key.delete()
        # izaziva se update AggregateBuyerCollectionCatalog preko task queue
        # ndb.delete_multi(AggregateBuyerCollectionCatalog.query(AggregateBuyerCollectionCatalog.store == buyer_collection_store.store, ancestor=user_key).fetch(keys_only=True))

# done! contention se moze zaobici ako write-ovi na ove entitete budu explicitno izolovani preko task queue
class AggregateBuyerCollectionCatalog(ndb.Model):
    
    # ancestor User
    # not logged
    # task queue radi agregaciju prilikom nekih promena na store-u
    # mogao bi da se uvede index na collections radi filtera: AggregateBuyerCollectionCatalog.collections = 'collection', 
    # ovaj model bi se trebao ukinuti u korist MapReduce resenja, koje bi bilo superiornije od ovog
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
    
    _KIND = 0
    
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
    
    _KIND = 0
    
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
    # reference = ndb.StringProperty('9', required=True)
    # company_address = ndb.LocalStructuredProperty(OrderAddress, '10', required=True)
    # billing_address = ndb.LocalStructuredProperty(OrderAddress, '11', required=True)
    # shipping_address = ndb.LocalStructuredProperty(OrderAddress, '12', required=True)
    # company_address_reference = ndb.KeyProperty('13', kind=Store, required=True)
    # billing_address_reference = ndb.KeyProperty('14', kind=BuyerAddress, required=True)
    # shipping_address_reference = ndb.KeyProperty('15', kind=BuyerAddress, required=True)
    # carrier_reference = ndb.KeyProperty('16', kind=StoreCarrier, required=True)
    # feedback = ndb.IntegerProperty('17', required=True)
    # payment = ndb.IntegerProperty('18', required=True) # payment status parametar
    # store_name = ndb.StringProperty('19', required=True)# testirati da li ovo indexiranje radi, tj overrid-a _default_indexed = False
    # store_logo = blobstore.BlobKeyProperty('20', required=True)# testirati da li ovo indexiranje radi, tj overrid-a _default_indexed = False
    # paypal_account = ndb.StringProperty('21', required=True)
    
    _KIND = 0
    
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
    
    @ndb.transactional
    def add_to_cart():
        # ovu akciju moze izvrsiti samo registrovani autenticirani agent.
        # akcija se moze pozvati samo ako je order.state == 'cart'.
        # imamo na raspolaganju user_key, catalog_key, catalog_pricetag_key, domain_key, product_template_key, product_instance_key, variant_signature, custom_variants ?
        catalog = catalog_key.get()
        store = catalog.store.get()
        shipping_exclusions = DomainStoreShippingExclusion.query(ancestor=catalog_key).fetch()
        order = get_order(store_key=catalog.store, user_key=user_key)
        # ako order postoji onda ne pravimo novi order
        if (order):
            # proveriti da li je order u state-u 'cart'
            if (order.state != 'cart'):
                # ukoliko je order u drugom state-u od 'cart' satate-a, onda ne praviti nikakve izmene
                # zabranjeno je dodavati artikle u order koji nije shopping cart-a
                return None
            else:
                # proveriti da li je shipping dozvoljen, i nastaviti ukoliko jeste
                buyer_addresses = []
                buyer_addresses.append(order.shipping_address_reference.get())
                shipping_addresses = get_shipping_addresses(buyer_addresses=buyer_addresses, shipping_exclusions=shipping_exclusions, store=store)
                if not (shipping_addresses['shipping_addresses']):
                    # zabranjeno je dodavati artikle iz store-a koji ne dozvoljava shipping na makar jednu adresu korisnika,
                    # bez obizra da li je order prethodno napravljen ili ne.
                    # postojeci order se moze jedino cancel u tom slucaju, 
                    # ili kupac mora napraviti adresu na koju se moze shipping raditi, kako bi bio u stanju da update-a order
                    return None
                # proveriti da li postoji order line (sto podrazumeva da order postoji u state-u 'cart') sa proizvodom koji se dodaje u order
                order_line_id = str(catalog_key.namespace()) + '-' + 
                                str(catalog_key.id()) + '-' + 
                                str(product_template_key.id()) + '-' + 
                                str(product_instance_key.id())
                line_exists = False
                index = 0
                for line in order.lines:
                    # ukoliko order line postoji (sto podrazumeva da order postoji u state-u 'cart'), 
                    # update postojeceg order line sa kolicinom proizvoda (quantity), 
                    # i update postojeceg order-a sa novim vrednostima
                    if (order_line_id == str(line.key.id())):
                        # ako order line postoji u order-u, radimo update quantity tako sto ga uvecavamo za 1
                        quantity = DecTools.form(line.quantity) + DecTools.form('1', line.product_uom)
                        order_line = update_order_line(user_key=user_key, order=order, order_line=line, order_line_quantity=quantity)
                        # ovde moramo nekako ovaj update-ovani order_line uguramo u order.lines, a da stari iz njih izbacimo.
                        # ovo je mozda primer tog swapanja order line-a
                        order.lines.pop(index)
                        order.lines.insert(index, order_line)
                        line_exists = True
                        break
                    index += 1
                # ukoliko order line ne postoji (a order postoji u state-u 'cart'), 
                # napraviti novi order line sa vrednostima koje se prepisuju iz proizvoda i ostalim vrednostima (tax...), 
                # i uraditi update postojeceg order-a sa novim vrednostima
                if not (line_exists):
                    # ako order line jos uvek ne postoji u order-u, pravimo novi order
                    product_template = product_template_key.get()
                    product_instance = product_instance_key.get()
                    taxes = DomainTax.query(namespace=catalog_key.namespace).order(DomainTax.sequence).fetch()
                    # ne znam da li ce ovde ici location=order.shipping_address ili location=order.billing_address
                    valid_taxes = get_taxes(taxes=taxes, location=order.shipping_address, product_template=product_template)
                    order_line = update_order_line(
                        user_key=user_key, 
                        catalog=catalog, 
                        catalog_pricetag_key=catalog_pricetag_key, 
                        product_template=product_template, 
                        product_instance=product_instance, 
                        order=order, 
                        variant_signature=variant_signature, 
                        custom_variants=custom_variants, 
                        valid_taxes=valid_taxes)
                    # u postojeci order dodajemo novu liniju
                    order.lines.append(order_line)
                # radimo update ordera kako bi se keshirani amount-ovi update-ovali
                order = update_order(order=order, store=store)
                return order
                # preostaje da se jos u radi update carrier-a sa novim vrednostima, one se u ovoj fazi koriste samo u view, 
                # sve dok se carrier ne prenese kao novi order line..
        # ukoliko order ne postoji, napraviti novi order, i potom uraditi korak 5.
        else:
            # proveriti da li je shipping dozvoljen, i nastaviti ukoliko jeste
            buyer_addresses = BuyerAddress.query(ancestor=user_key).fetch()
            shipping_addresses = get_shipping_addresses(buyer_addresses=buyer_addresses, shipping_exclusions=shipping_exclusions, store=store)
            if not (shipping_addresses['shipping_addresses']):
                # zabranjeno je dodavati artikle iz store-a koji ne dozvoljava shipping na makar jednu adresu korisnika,
                # bez obizra da li je order prethodno napravljen ili ne.
                # postojeci order se moze jedino cancel u tom slucaju, 
                # ili kupac mora napraviti adresu na koju se moze shipping raditi, kako bi bio u stanju da update-a order
                return None
            # pripremamo shipping address
            if (shipping_addresses['default_shipping_address']):
                shipping_address = shipping_addresses['default_shipping_address']
            else:
                shipping_address = shipping_addresses['default_shipping_address'][0]
            # pripremamo billing addresse
            for buyer_address in buyer_addresses:
                if (buyer_address.default_billing):
                    billing_address = buyer_address
                    break
            # pravimo novi order
            order = update_order(user_key=user_key, store=store, billing_address=billing_address, shipping_address=shipping_address, carrier_reference=carrier_reference)
            # pravimo novi order line
            product_template = product_template_key.get()
            product_instance = product_instance_key.get()
            taxes = DomainTax.query(namespace=catalog_key.namespace).order(DomainTax.sequence).fetch()
            # ne znam da li ce ovde ici location=order.shipping_address ili location=order.billing_address
            valid_taxes = get_taxes(taxes=taxes, location=order.shipping_address, product_template=product_template)
            order_line = update_order_line(
                user_key=user_key, 
                catalog=catalog, 
                catalog_pricetag_key=catalog_pricetag_key, 
                product_template=product_template, 
                product_instance=product_instance, 
                order=order, 
                variant_signature=variant_signature, 
                custom_variants=custom_variants, 
                valid_taxes=valid_taxes)
            # u postojeci order dodajemo novu liniju
            order.lines.append(order_line)
            # radimo update ordera kako bi se keshirani amount-ovi update-ovali
            order = update_order(order=order, store=store)
            return order
            # preostaje da se jos u radi update carrier-a sa novim vrednostima, one se u ovoj fazi koriste samo u view, 
            # sve dok se carrier ne prenese kao novi order line..
    
    @ndb.transactional
    def update_cart():
        # ovu akciju moze izvrsiti samo vlasnik entiteta (order.parent == agent) ako je order.state == 'cart',
        # ili agent koji ima domain-specific dozvolu 'discount-Order', za order.store koji pripada domeni, i ako je order.state == 'checkout'.
        # akcija se moze pozvati samo ako je order.state == 'cart' ili order.state == 'checkout'
        # imamo na raspolaganju user_key, catalog_key, catalog_pricetag_key, domain_key, order_lines, shipping_address_key, billing_address_key   ?
        catalog = catalog_key.get()
        store = catalog.store.get()
        shipping_exclusions = DomainStoreShippingExclusion.query(ancestor=catalog_key).fetch()
        order = get_order(store_key=catalog.store, user_key=user_key)
        # ako order postoji onda nastavljamo dalje
        if (order):
            # proveriti da li je order u state-u 'cart'
            if (order.state == 'cart'):
                # proveriti da li je shipping dozvoljen, i nastaviti ukoliko jeste
                shipping_address = shipping_address_key.get()
                billing_address = billing_address_key.get()
                shipping_addresses = get_shipping_addresses(buyer_addresses=[shipping_address], shipping_exclusions=shipping_exclusions, store=store)
                if not (shipping_addresses['shipping_addresses']):
                    # zabranjeno je dodavati artikle iz store-a koji ne dozvoljava shipping na makar jednu adresu korisnika,
                    # bez obizra da li je order prethodno napravljen ili ne.
                    # postojeci order se moze jedino cancel u tom slucaju, 
                    # ili kupac mora napraviti adresu na koju se moze shipping raditi, kako bi bio u stanju da update-a order
                    return None
                # update postojecih order lines-a sa novim kolicinama proizvoda (quantity), 
                # i update postojeceg order-a sa novim vrednostima
                lines = order.lines
                order.lines = []
                sequence = 0
                for line in lines:
                    # order_lines je prekapovan dictionary sa values-ima za svaki order line i mapiranim originalnim kljucevima lines-a
                    ord_line = order_lines.get(line.key)
                    quantity = DecTools.form(ord_line['quantity'])
                    order_line = update_order_line(user_key=user_key, order=order, order_line=line, order_line_quantity=quantity, order_line_sequence=sequence)
                    # valjda ce ovako moci da radi sequencing.
                    # ako ovo ne bude valjalo onda treba smisliti drugaciji nacin seqenca, mozda sa clienta da se salju sequence..
                    if (order_line):
                        order.lines.append(order_line)
                        sequence += 1
                # radimo update ordera kako bi se keshirani amount-ovi update-ovali
                order = update_order(order=order, store=store, billing_address=billing_address, shipping_address=shipping_address, carrier_reference=carrier_reference)
                return order
                # preostaje da se jos u radi update carrier-a sa novim vrednostima, one se u ovoj fazi koriste samo u view, 
                # sve dok se carrier ne prenese kao novi order line..
            # proveriti da li je order u state-u 'checkout'
            elif (order.state == 'checkout'):
                # update postojecih order lines-a sa novim discount-ima, 
                # i update postojeceg order-a sa novim vrednostima
                lines = order.lines
                order.lines = []
                for line in lines:
                    # order_lines je prekapovan dictionary sa values-ima za svaki order line i mapiranim originalnim kljucevima lines-a
                    ord_line = order_lines.get(line.key)
                    discount = DecTools.form(ord_line['discount'])
                    order_line = update_order_line(user_key=user_key, order=order, order_line=line, order_line_discount=discount)
                    order.lines.append(order_line)
                # radimo update ordera kako bi se keshirani amount-ovi update-ovali
                order = update_order(order=order, store=store)
                return order
            else:
                # ukoliko je order u drugom state-u od 'cart' ili 'checkout' satate-a, onda ne praviti nikakve izmene
                # zabranjeno je update-ovati order koji nije shopping cart-a ili quotation
                return None
        # ukoliko order ne postoji vraca se poruka da je shopping cart-a prazna
        else:
            return None
    
    @ndb.transactional
    def checkout():
        # ovu akciju moze izvrsiti samo vlasnik entiteta (order.parent == agent).
        # akcija se moze pozvati samo ako je order.state == 'cart'.
        # prvo se execute update_cart funkcija i onda se radi update order objekta
        order = update_cart() # naravno, u pravilnom code-u ova funckija ce primati argumente kao i sve ostale dokumentovane metode
        order.state = 'checkout'
        order_key = order.put()
        object_log = ObjectLog(parent=order_key, agent=kwargs.get('user_key'), action='checkout', state=order.state, log=order)
        object_log.put()
        return order
    
    @ndb.transactional
    def cancel():
        # ovu akciju moze izvrsiti samo vlasnik entiteta (order.parent == agent),
        # ili agent koji ima domain-specific dozvolu 'cancel-Order', za order.store koji pripada domeni.
        # mozda budemo stavili da 'checkout' i 'cart' orderi sami expire-aju nakon nekog intervala, tako da domain-specific dozvola bude nepotrebna
        # akcija se moze pozvati samo ako je order.state == 'checkout'.
        store = catalog.store.get()
        order = get_order(store_key=catalog.store, user_key=user_key)
        order.state = 'canceled'
        order_key = order.put()
        object_log = ObjectLog(parent=order_key, agent=kwargs.get('user_key'), action='cancel', state=order.state, log=order)
        object_log.put()
        return order
    
    @ndb.transactional
    def pay():
        # ovu akciju moze izvrsiti samo vlasnik entiteta (order.parent == agent).
        # akcija se moze pozvati samo ako je order.state == 'checkout'.
        store = catalog.store.get()
        order = get_order(store_key=catalog.store, user_key=user_key)
        order.state = 'processing'
        order.paypal_account = store.paypal_email # mozda da ovo stavimo u update_order ?
        order_key = order.put()
        object_log = ObjectLog(parent=order_key, agent=kwargs.get('user_key'), action='pay', state=order.state, log=order)
        object_log.put()
        return order
    
    @ndb.transactional
    def timeout():
        # ovu akciju moze izvrsiti samo agent koji ima globalnu dozvolu 'timeout-Order'. Verovatno ce to biti System Account
        # akcija se moze pozvati samo ako je order.state == 'processing'.
        store = catalog.store.get()
        order = get_order(store_key=catalog.store, user_key=user_key)
        order.state = 'checkout'
        order_key = order.put()
        object_log = ObjectLog(parent=order_key, agent=kwargs.get('user_key'), action='timeout', state=order.state, log=order)
        object_log.put()
        return order
    
    @ndb.transactional
    def complete():
        # ovu akciju moze izvrsiti samo agent koji ima globalnu dozvolu 'complete-Order'. Verovatno ce to biti System Account
        # akcija se moze pozvati samo ako je order.state == 'processing'.
        store = catalog.store.get()
        order = get_order(store_key=catalog.store, user_key=user_key)
        order.state = 'completed'
        order_key = order.put()
        object_log = ObjectLog(parent=order_key, agent=kwargs.get('user_key'), action='complete', state=order.state, log=order)
        object_log.put()
        # azuriranje product inventory. ovaj code bi mogao eventualno da se prebaci u checkout() ?
        for line in order.lines:
            # gradimo kljuc product instance iz id-ja linije.
            line_ids = str(line.key.id()).split('-')
            product_instance_key = ndb.Key('DomainCatalog', line_ids[1], 'DomainProductTemplate', line_ids[2], 'DomainProductInstance', line_ids[3], namespace=line_ids[0])
            # proveravamo da li product instance postoji
            product_instance = product_instance_key.get()
            if (product_instance):
                # ako product_instance postoji, onda se radi inventory logging za ovaj line
                # ovo bi trebalo ici preko task queue
                # product instance ne mora postojati, napr. u slucaju kada product template ima preko 1000 varijacija
                # idempotency je moguc ako se pre inserta proverava da li je record sa tim reference-om upisan
                logged = ndb.Key('DomainProductInventoryLog', str(line.key), parent=product_instance_key).get()
                # samo se jednom radi inventory logging per order line!
                if not (logged):
                    # uzimamo zadnji status quantity-ja radi obracuna
                    product_inventory_log = DomainProductInventoryLog.query().order(-DomainProductInventoryLog.logged).fetch(1)
                    new_product_inventory_log = DomainProductInventoryLog(parent=product_instance_key, id=str(line.key), quantity=line.quantity, balance=product_inventory_log[0].balance + line.quantity)
                    new_product_inventory_log.put()
        return order
    
    @ndb.transactional
    def message():
        # ovu akciju moze izvrsiti samo vlasnik entiteta (order.parent == agent),
        # ili agent koji ima domain-specific dozvolu 'message-Order', za order.store koji pripada domeni.
        # akcija se moze pozvati samo ako je order.state == 'checkout'.
        object_log = ObjectLog(parent=order_key, agent=kwargs.get('user_key'), action='message', state=order.state, message='poruka od agenta - obavezno polje!', note='privatni komentar agenta (dostupan samo privilegovanim agentima) - obavezno polje!')
        object_log.put()
        return order
    
    # REUSABLE CODE!
    # funkcije get_order, update_order, update_order_line, get_shipping_addresses, get_taxes, calculate_taxes, get_carrires.. 
    # se nikad ne pozivaju direktno (sa client-a) vec ih pozivuaju druge funkcije..
    
    def get_order(**kwargs):
        order = Order.query(Order.store == kwargs.get('store_key'), Order.state.IN(['cart', 'checkout', 'processing']), ancestor=kwargs.get('user_key')).fetch() # trebace nam composite index za ovo
        if (order):
            order = order[0]
            # ucitavamo sve linije, ovde se moze uspostaviti kontrola da se ucitava samo kada se to zahteva, napr: if(kwargs.get('get_lines')):...
            order_lines = OrderLine.query(ancestor=order.key).order(OrderLine.sequence).fetch()
            order.lines = order_lines
        return order
    
    def update_order(**kwargs):
        # store se ucitava radi prepisivanja vrednosti u order
        store = kwargs.get('store')
        # ako order postoji onda ga update-amo
        if (kwargs.get('order')):
            # treba zavrsiti dokumentovanje i pregledati kako jos optimize ovo... 
            order = kwargs.get('order')
            if (kwargs.get('billing_address')):
                # billing address se prepisuje iz BuyerAddress koji ima default_billing=True
                billing_address = kwargs.get('billing_address')
                # billing address reference se dobija iz kwarg-a sto je zapravo key BuyerAddress sa default_billing=True
                billing_address_reference = billing_address.key
                billing_address_country = billing_address.country.get()
                if (isinstance(billing_address.region, str)):
                    billing_address_region = billing_address.region
                    billing_address_region_code = billing_address.region
                else:
                    region = billing_address.region.get()
                    billing_address_region = region.name
                    billing_address_region_code = region.code
                order_billing_address = OrderAddress(
                    name=billing_address.name, 
                    country=billing_address_country.name, 
                    country_code=billing_address_country.code, 
                    region=billing_address_region, 
                    region_code=billing_address_region_code, 
                    city=billing_address.city, 
                    postal_code=billing_address.postal_code, 
                    street_address=billing_address.street_address, 
                    street_address2=billing_address.street_address2, 
                    email=billing_address.email, 
                    telephone=billing_address.telephone)
                order.billing_address = order_billing_address
                order.billing_address_reference = billing_address_reference
            if (kwargs.get('shipping_address')):
                # shipping address se prepisuje iz BuyerAddress koji ima default_shipping=True
                shipping_address = kwargs.get('shipping_address')
                # shipping address reference se dobija iz kwarg-a sto je zapravo key BuyerAddress sa default_shipping=True
                shipping_address_reference = shipping_address.key
                shipping_address_country = shipping_address.country.get()
                if (isinstance(shipping_address.region, str)):
                    shipping_address_region = shipping_address.region
                    shipping_address_region_code = shipping_address.region
                else:
                    region = shipping_address.region.get()
                    shipping_address_region = region.name
                    shipping_address_region_code = region.code
                order_shipping_address = OrderAddress(
                    name=shipping_address.name, 
                    country=shipping_address_country.name, 
                    country_code=shipping_address_country.code, 
                    region=shipping_address_region, 
                    region_code=shipping_address_region_code, 
                    city=shipping_address.city, 
                    postal_code=shipping_address.postal_code, 
                    street_address=shipping_address.street_address, 
                    street_address2=shipping_address.street_address2, 
                    email=shipping_address.email, 
                    telephone=shipping_address.telephone)
                order.shipping_address = order_shipping_address
                order.shipping_address_reference = shipping_address_reference
            if (kwargs.get('carrier_reference') and order.carrier_reference != kwargs.get('carrier_reference')):
                order.carrier_reference = kwargs.get('carrier_reference')
            if (kwargs.get('feedback') and order.feedback != kwargs.get('feedback')):
                order.feedback = kwargs.get('feedback')
            if (order.store_name != store.name):
                order.store_name = store.name
            if (order.store_logo != store.logo):
                order.store_logo = store.logo
            # ovde pre update-a obracunavamo ukupne iznose na orderu
            untaxed_amount = DecTools.form('0', order.currency)
            tax_amount = DecTools.form('0', order.currency)
            total_amount = DecTools.form('0', order.currency)
            for line in order.lines:
                untaxed_amount += DecTools.form(line.subtotal, order.currency)
                tax_amount += DecTools.form(line.tax_subtotal, order.currency)
                total_amount += DecTools.form(line.subtotal, order.currency) + DecTools.form(line.tax_subtotal, order.currency)
            order.untaxed_amount = untaxed_amount
            order.tax_amount = tax_amount
            order.total_amount = total_amount
            order_key = order.put()
            object_log = ObjectLog(parent=order_key, agent=kwargs.get('user_key'), action='update_order', state=order.state, log=order)
            object_log.put()
            return order
        # ako order ne potoji onda pravimo novi
        else:
            # pravimo novi order sa standardnim vrednostima
            # currency za order se preuzima iz store.currency
            store_currency = store.currency.get()
            order_currency = OrderCurrency()
            order_currency.name = store_currency.name
            order_currency.symbol = store_currency.symbol
            order_currency.code = store_currency.code
            order_currency.numeric_code = store_currency.numeric_code
            order_currency.rounding = store_currency.rounding
            order_currency.digits = store_currency.digits
            order_currency.grouping = store_currency.grouping
            order_currency.decimal_separator = store_currency.decimal_separator
            order_currency.thousands_separator = store_currency.thousands_separator
            order_currency.positive_sign_position = store_currency.positive_sign_position
            order_currency.negative_sign_position = store_currency.negative_sign_position
            order_currency.positive_sign = store_currency.positive_sign
            order_currency.negative_sign = store_currency.negative_sign
            order_currency.positive_currency_symbol_precedes = store_currency.positive_currency_symbol_precedes
            order_currency.negative_currency_symbol_precedes = store_currency.negative_currency_symbol_precedes
            order_currency.positive_separate_by_space = store_currency.positive_separate_by_space
            order_currency.negative_separate_by_space = store_currency.negative_separate_by_space
            # default amount vrednosti su 0, s obzirom da order jos nema nijedan order line
            untaxed_amount = DecTools.form('0', order_currency)
            tax_amount = DecTools.form('0', order_currency)
            total_amount = DecTools.form('0', order_currency)
            # company address reference je za sada store key, posto se u store cuvaju company podaci
            company_address_reference = store.key
            # company address se prepisuje iz store, posto se u store cuvaju company podaci
            company_address_country = store.company_country.get()
            if (isinstance(store.company_region, str)):
                company_address_region = store.company_region
                company_address_region_code = store.company_region
            else:
                region = store.company_region.get()
                company_address_region = region.name
                company_address_region_code = region.code
            order_company_address = OrderAddress(
                name=store.company_name, 
                country=company_address_country.name, 
                country_code=company_address_country.code, 
                region=company_address_region, 
                region_code=company_address_region_code, 
                city=store.company_city, 
                postal_code=store.company_postal_code, 
                street_address=store.company_street_address, 
                street_address2=store.company_street_address2, 
                email=store.company_email, 
                telephone=store.company_telephone)
            # billing address se prepisuje iz BuyerAddress koji ima default_billing=True
            billing_address = kwargs.get('billing_address')
            # billing address reference se dobija iz kwarg-a sto je zapravo key BuyerAddress sa default_billing=True
            billing_address_reference = billing_address.key
            billing_address_country = billing_address.country.get()
            if (isinstance(billing_address.region, str)):
                billing_address_region = billing_address.region
                billing_address_region_code = billing_address.region
            else:
                region = billing_address.region.get()
                billing_address_region = region.name
                billing_address_region_code = region.code
            order_billing_address = OrderAddress(
                name=billing_address.name, 
                country=billing_address_country.name, 
                country_code=billing_address_country.code, 
                region=billing_address_region, 
                region_code=billing_address_region_code, 
                city=billing_address.city, 
                postal_code=billing_address.postal_code, 
                street_address=billing_address.street_address, 
                street_address2=billing_address.street_address2, 
                email=billing_address.email, 
                telephone=billing_address.telephone)
            # shipping address se prepisuje iz BuyerAddress koji ima default_shipping=True
            shipping_address = kwargs.get('shipping_address')
            # shipping address reference se dobija iz kwarg-a sto je zapravo key BuyerAddress sa default_shipping=True
            shipping_address_reference = shipping_address.key
            shipping_address_country = shipping_address.country.get()
            if (isinstance(shipping_address.region, str)):
                shipping_address_region = shipping_address.region
                shipping_address_region_code = shipping_address.region
            else:
                region = shipping_address.region.get()
                shipping_address_region = region.name
                shipping_address_region_code = region.code
            order_shipping_address = OrderAddress(
                name=shipping_address.name, 
                country=shipping_address_country.name, 
                country_code=shipping_address_country.code, 
                region=shipping_address_region, 
                region_code=shipping_address_region_code, 
                city=shipping_address.city, 
                postal_code=shipping_address.postal_code, 
                street_address=shipping_address.street_address, 
                street_address2=shipping_address.street_address2, 
                email=shipping_address.email, 
                telephone=shipping_address.telephone)
            # carrier reference se dobija iz kwarg-a
            carrier_reference = kwargs.get('carrier_reference')
            # feedback treba da ima neku default vrednost, to je ustvari OrderFeedback.state vrednost
            feedback = 1
            # store name se prepisuje iz store.name
            store_name = store.name
            # store logo se prepisuje iz store.logo
            store_logo = store.logo
            # ovde se gradi order sa vrednostima koje su prethodno stecene
            order = Order(
                parent=kwargs.get('user_key'), 
                store=store.key, 
                currency=order_currency, 
                untaxed_amount=untaxed_amount, 
                tax_amount=tax_amount, 
                total_amount=total_amount, 
                state='cart', 
                company_address=order_company_address, 
                billing_address=order_billing_address, 
                shipping_address=order_shipping_address, 
                company_address_reference=company_address_reference, 
                billing_address_reference=billing_address_reference, 
                shipping_address_reference=shipping_address_reference, 
                carrier_reference=carrier_reference, 
                feedback=feedback, 
                store_name=store_name, 
                store_logo=store_logo)
            order_key = order.put()
            object_log = ObjectLog(parent=order_key, agent=kwargs.get('user_key'), action='new_order', state=order.state, log=order)# videcemo kako cemo ovaj logging resiti
            object_log.put()
            return order
    
    def update_order_line(**kwargs):
        order = kwargs.get('order')
        # ako order_line postoji onda ga update-amo
        if (kwargs.get('order_line')):
            # treba voditi racuna oko dozvola ko sta moze ovde da uradi...
            order_line = kwargs.get('order_line')
            # ako je quantity jednak ili manji od nule onda se order line brise.
            if (kwargs.get('order_line_quantity') <= 0):
                object_log = ObjectLog(parent=order_line.key, agent=kwargs.get('user_key'), action='remove_order_line', state='none')
                object_log.put()
                order_line.key.delete()
                return None
            # ako je quantity veci od nule i ako se user input razlikuje od onoga sto je vec u order_line-u onda update-amo order_line
            if (kwargs.get('order_line_quantity') > 0):
                if (order_line.quantity != kwargs.get('order_line_quantity')):
                    order_line.quantity = DecTools.form(kwargs.get('order_line_quantity'), order_line.product_uom)
            # ako je discount provided i ako se user input razlikuje od onoga sto je vec u order_line-u onda update-amo order_line
            if (kwargs.get('order_line_discount') and (order_line.discount != kwargs.get('order_line_discount'))):
                order_line.discount = DecTools.form(kwargs.get('order_line_discount'), '.2f')
            # ako je sequence provided i ako se user input razlikuje od onoga sto je vec u order_line-u onda update-amo order_line
            if (kwargs.get('order_line_sequence') and (order_line.sequence != kwargs.get('order_line_sequence'))):
                order_line.sequence = kwargs.get('order_line_sequence')
            # ako je valid_taxes provided onda update-amo order_line
            if (kwargs.get('valid_taxes')):
                # generisemo taxes i tax_references
                taxes = []
                tax_references = []
                for tax in kwargs.get('valid_taxes'):
                    order_line_tax = OrderLineTax(name=tax.name, amount=tax.amount)
                    taxes.append(order_line_tax)
                    tax_references.append(tax.key)
                order_line.taxes = taxes
                order_line.tax_references = tax_references
            # pre snimanja nazad u bazu update-amo subtotal cache
            subtotal = DecTools.form(order_line.unit_price, order.currency) * DecTools.form(order_line.quantity, order_line.product_uom)
            discount_subtotal = DecTools.form(subtotal) - (DecTools.form(subtotal) * (DecTools.form(order_line.discount) * DecTools.form('0.01'))) # moze i "/ DecTools.form('100')"
            order_line.subtotal = DecTools.form(discount_subtotal, order.currency)
            # pre snimanja nazad u bazu update-amo tax subtotal cache
            order_line.tax_subtotal = calcualte_taxes(order=order, order_line=order_line)
            order_line_key = order_line.put()
            object_log = ObjectLog(parent=order_line_key, agent=kwargs.get('user_key'), action='update_order_line', state='none', log=order_line)
            object_log.put()
            return order_line
        # ako order line ne postoji onda pravimo novi order line sa discount 0.00 i quantity 1
        else:
            catalog = kwargs.get('catalog')
            # ucitavamo product template i product instance entitete koji nam trebaju za izgradnju order line,
            # i preuzimamo propertije iz product template i product instance, kako bi mogli da ispitamo koji su postojani
            product_template = kwargs.get('product_template')
            product_instance = kwargs.get('product_instance')
            product_template_properties = product_template._properties
            product_instance_properties = product_instance._properties
            # redosled izgradnje id-a za order line/cart line: id=catalog_namespace-catalog_id-product_template_id-product_instance_id
            order_line_id = str(catalog.key.namespace()) + '-' + 
                            str(catalog.key.id()) + '-' + 
                            str(product_template.key.id()) + '-' + 
                            str(product_instance.key.id())
            # catalog_pricetag_reference dobijamo iz inputa
            catalog_pricetag_reference = kwargs.get('catalog_pricetag_key')
            # product_category_complete_name i product_category preuzimamo iz product template
            product_category = product_template.product_category.get()
            product_category_complete_name = product_template_category.complete_name
            product_category = product_template.product_category
            # generisemo taxes i tax_references
            taxes = []
            tax_references = []
            for tax in kwargs.get('valid_taxes'):
                order_line_tax = OrderLineTax(name=tax.name, amount=tax.amount)
                taxes.append(order_line_tax)
                tax_references.append(tax.key)
            # description se inicijalno setuje na product template name
            description = product_template.name
            # preuzimamo uom iz product template-a i gradimo instancu OrderLineProductUOM koji nam treba za cart line
            uom = product_template.product_uom.get()
            uom_category = uom.key.parent().get()
            product_uom = OrderLineProductUOM(name=uom.name, symbol=uom.symbol, category=uom_category.name, rounding=uom.rounding, digits=uom.digits)
            # http://docs.python.org/2/library/decimal.html
            # http://docs.python.org/2/library/functions.html#format
            # http://docs.python.org/2/library/string.html#formatspec
            # http://stackoverflow.com/questions/15076310/format-python-decimal-object-to-a-specified-precision
            # ovo gore su primeri formatiranja, koji mozda nisu ispravni, ovaj code ovde je samo radi opisa.
            # quantity se setuje na 1 posto new line podrazumeva jednu mernu jedinicu proizvoda
            quantity = DecTools.form('1', product_uom)
            # odlucujemo odakle cemo da preuzimamo vrednosti za unit_price, product instance ima prednost (ako postoji)
            if (product_instance_properties['unit_price']):
                unit_price = DecTools.form(product_instance.unit_price, order.currency)
            else:
                unit_price = DecTools.form(product_template.unit_price, order.currency)
            # discount se postavlja na 0.00, i kasnije se moze editovati od strane prodavca, ukoliko je order u state-u koji to dozvoljava
            discount = DecTools.form('0', '.2f')
            # sequence se podesava po count-u postojecih linija - ako sequencing bude zero based onda nam ne treba len() + 1
            sequence = len(order.lines)
            # proveravamo da li su product instance uopste generisane, a bice generisane samo ako ih bude mannje od 1k per template
            if (product_template_properties['product_instance_count'] and product_template.product_instance_count > 1000):
                # ukolliko nema instanci onda se uz name proizvoda dodaje i variant signature koji se izbildao iz web forme prilikom user inputa.
                description # += '\n' + kwargs.get('variant_signature')
            else:
                # variant_signature ce se mozda upisivati u Expando prop. OrderLine-a
                # variant_signature = product_instance.variant_signature
                if (kwargs.get('custom_variants')):
                    description # += '\n' + kwargs.get('variant_signature')
            order_line = OrderLine(
                parent=order.key, 
                id=order_line_id, 
                description=description, 
                quantity=quantity, 
                product_uom=product_uom, 
                unit_price=unit_price, 
                discount=discount, 
                sequence=sequence, 
                taxes=taxes, 
                product_category_complete_name=product_category_complete_name, 
                product_category=product_category, 
                catalog_pricetag_reference=catalog_pricetag_reference, 
                tax_references=tax_references)
            subtotal = DecTools.form(order_line.unit_price, order.currency) * DecTools.form(order_line.quantity, order_line.product_uom)
            discount_subtotal = DecTools.form(subtotal) - (DecTools.form(subtotal) * (DecTools.form(order_line.discount) * DecTools.form('0.01'))) # moze i "/ DecTools.form('100')"
            order_line.subtotal = DecTools.form(discount_subtotal, order.currency)
            order_line.tax_subtotal = calcualte_taxes(order=order, order_line=order_line)
            order_line_key = order_line.put()
            object_log = ObjectLog(parent=order_line_key, agent=kwargs.get('user_key'), action='add_order_line', state='none', log=order_line)
            object_log.put()
            return order_line
    
    def get_shipping_addresses(**kwargs):
        # proveravamo da li kupac moze kupovati u datoj prodavnici/da li ima neku adresu na koju store dozvoljava shipping
        # object_key moze da bude key bilo kojeg entiteta koji u potomstvu ima DomainStoreShippingExclusion entitete
        # ovde smo trebali da koristimo keshiranu verziju DomainStoreShippingExclusion, 
        # tj. DomainStoreShippingExclusion.query(ancestor=catalog_key).fetch(),
        # medjutim to predstavlja problem da se moze dogoditi da user iz jednog kataloga moze izabrati adresu koja mu je nedostupna u drugom katalogu u istom store-u
        # to pravi nekonzistentnost i funkcionalnost nije onakva kakva se ocekuje da bude.
        buyer_addresses = kwargs.get('buyer_addresses')
        shipping_exclusions = kwargs.get('shipping_exclusions')
        store = kwargs.get('store')
        shipping_addresses = []
        default_shipping_address = None
        for buyer_address in buyer_addresses:
            shipping_allowed = False
            if not (shipping_exclusions):
                shipping_allowed = True
            else:
                # Shipping everywhere except at the following locations
                if not (store.location_exclusion):
                    shipping_allowed = True
                    for shipping_exclusion in shipping_exclusions:
                        p = shipping_exclusion._properties
                        if not (p['region'] and p['postal_code_from'] and p['postal_code_to']):
                            if (buyer_address.country == shipping_exclusion.country):
                                shipping_allowed = False
                                break
                        elif not (p['postal_code_from'] and p['postal_code_to']):
                            if (buyer_address.country == shipping_exclusion.country and buyer_address.region == shipping_exclusion.region):
                                shipping_allowed = False
                                break
                        else:
                            if (buyer_address.country == shipping_exclusion.country and buyer_address.region == shipping_exclusion.region and (buyer_address.postal_code >= shipping_exclusion.postal_code_from and buyer_address.postal_code <= shipping_exclusion.postal_code_to)):
                                shipping_allowed = False
                                break
                else:
                    # Shipping only at the following locations
                    for shipping_exclusion in shipping_exclusions:
                        p = shipping_exclusion._properties
                        if not (p['region'] and p['postal_code_from'] and p['postal_code_to']):
                            if (buyer_address.country == shipping_exclusion.country):
                                shipping_allowed = True
                                break
                        elif not (p['postal_code_from'] and p['postal_code_to']):
                            if (buyer_address.country == shipping_exclusion.country and buyer_address.region == shipping_exclusion.region):
                                shipping_allowed = True
                                break
                        else:
                            if (buyer_address.country == shipping_exclusion.country and buyer_address.region == shipping_exclusion.region and (buyer_address.postal_code >= shipping_exclusion.postal_code_from and buyer_address.postal_code <= shipping_exclusion.postal_code_to)):
                                shipping_allowed = True
                                break
            if (shipping_allowed):    
                shipping_addresses.append(buyer_address)
                    if (buyer_address.default_shipping):
                        default_shipping_address = buyer_address
        return {'shipping_addresses': shipping_addresses, 'default_shipping_address': default_shipping_address}
    
    def get_taxes(**kwargs):
        taxes = kwargs.get('taxes')
        location = kwargs.get('location')
        product_template = kwargs.get('product_template')
        product_category = product_template.product_category
        carrier = kwargs.get('carrier')
        valid_taxes = []
        for tax in taxes:
            tax_allowed = False
            tax_p = tax._properties
            # location parametar se uvek mora proslediti metodi, kako bi se uradila ispravna validacija.
            if (tax_p['locations']):
                # Tax everywhere except at the following locations
                if not (tax.location_exclusion):
                    tax_allowed = True
                    for tax_location in tax.locations:
                        p = tax_location._properties
                        if not (p['region'] and p['postal_code_from'] and p['postal_code_to']):
                            if (location.country == tax_location.country):
                                tax_allowed = False
                                break
                        elif not (p['postal_code_from'] and p['postal_code_to']):
                            if (location.country == tax_location.country and location.region == tax_location.region):
                                tax_allowed = False
                                break
                        else:
                            if (location.country == tax_location.country and location.region == tax_location.region and (location.postal_code >= tax_location.postal_code_from and location.postal_code <= tax_location.postal_code_to)):
                                tax_allowed = False
                                break
                else:
                    # Tax only at the following locations
                    for tax_location in tax.locations:
                        p = tax_location._properties
                        if not (p['region'] and p['postal_code_from'] and p['postal_code_to']):
                            if (location.country == tax_location.country):
                                tax_allowed = True
                                break
                        elif not (p['postal_code_from'] and p['postal_code_to']):
                            if (location.country == tax_location.country and location.region == tax_location.region):
                                tax_allowed = True
                                break
                        else:
                            if (location.country == tax_location.country and location.region == tax_location.region and (location.postal_code >= tax_location.postal_code_from and location.postal_code <= tax_location.postal_code_to)):
                                tax_allowed = True
                                break
            else:
                # u slucaju da taxa nema konfigurisane location exclusions-e onda se odnosi na sve lokacije/onda je to globalna taxa
                tax_allowed = True
            # ako je tax_allowed nakon location check-a onda radimo validaciju po carrier-u i product_category-ju
            if (tax_allowed):
                # ako je validator metod primio carrier id, onda se validacija odnosi na carrier.
                if (carrier):
                    tax_allowed = False
                    # samo taxe koje su eksplicitno konfigurisane za carrier-e se mogu odnositi na carrier
                    if (tax_p['carriers']) and (tax.carriers.count(carrier)):
                        tax_allowed = True
                # ako je validator metod primio product_category id, onda se validacija odnosi na product.
                elif (product_category):
                    # samo taxe koje nisu eksplicitno konfigurisane za carrier-e se mogu odnositi na prouduct
                    if (tax_p['carriers']):
                        tax_allowed = False
                    else:
                        # ukoliko taxa target-a product kategorije, onda se product_category mora naci medju njima kako bi taxa bila validna
                        if (tax_p['product_categories']):
                            if not (tax.product_categories.count(product_category)):
                                tax_allowed = False
            if (tax_allowed):
                valid_taxes.append(tax)
        return valid_taxes
    
    def calcualte_taxes(**kwargs):
        if (kwargs.get('order')):
            order = kwargs.get('order')
            if (kwargs.get('order_line')):
                order_line = kwargs.get('order_line')
                tax_subtotal = DecTools.form('0', order.currency)
                for tax in order_line.taxes:
                    if (tax.amount.find('[%]') != -1):
                        tax_amount = DecTools.form(re.sub(r'\[%\]','', tax.amount)) * DecTools.form('0.01') # moze i "/ DecTools.form('100')"
                        tax_subtotal += order_line.subtotal * tax_amount
                    elif (tax.amount.find('[c]') != -1):
                        tax_amount = DecTools.form(re.sub(r'\[c\]','', tax.amount))
                        tax_subtotal += tax_amount
                return tax_subtotal
            else:
                lines = order.lines
                order.lines = []
                for order_line in lines:
                    tax_subtotal = DecTools.form('0', order.currency)
                    for tax in order_line.taxes:
                        if (tax.amount.find('[%]') != -1):
                            tax_amount = DecTools.form(re.sub(r'\[%\]','', tax.amount)) * DecTools.form('0.01') # moze i "/ DecTools.form('100')"
                            tax_subtotal += order_line.subtotal * tax_amount
                        elif (tax.amount.find('[c]') != -1):
                            tax_amount = DecTools.form(re.sub(r'\[c\]','', tax.amount))
                            tax_subtotal += tax_amount
                    order_line.tax_subtotal = tax_subtotal
                    order.lines.append(line)
                return order
    
    def get_carriers(**kwargs):
        carriers = []
        order = None
        valid_carriers = []
        for key, value in kwargs.iteritems():
            if (key = 'carriers'):
                carriers = value
            elif (key = 'order'):
                order = value
        for carrier in carriers:
            for carrier_line in carrier.lines
                line_allowed = False
                carrier_line_p = carrier_line._properties
                # location parametar se uvek mora proslediti metodi, kako bi se uradila ispravna validacija.
                if (carrier_line_p['locations']):
                    # Everywhere except at the following locations
                    if not (carrier_line.location_exclusion):
                        line_allowed = True
                        for carrier_line_location in carrier_line.locations:
                            p = carrier_line_location._properties
                            if not (p['region'] and p['postal_code_from'] and p['postal_code_to']):
                                if (order.shipping_address.country == carrier_line_location.country):
                                    line_allowed = False
                                    break
                            elif not (p['postal_code_from'] and p['postal_code_to']):
                                if (order.shipping_address.country == carrier_line_location.country and order.shipping_address.region == carrier_line_location.region):
                                    line_allowed = False
                                    break
                            else:
                                if (order.shipping_address.country == carrier_line_location.country and order.shipping_address.region == carrier_line_location.region and (order.shipping_address.postal_code >= carrier_line_location.postal_code_from and order.shipping_address.postal_code <= carrier_line_location.postal_code_to)):
                                    line_allowed = False
                                    break
                    else:
                        # Only at the following locations
                        for carrier_line_location in carrier_line.locations:
                            p = carrier_line_location._properties
                            if not (p['region'] and p['postal_code_from'] and p['postal_code_to']):
                                if (order.shipping_address.country == carrier_line_location.country):
                                    line_allowed = True
                                    break
                            elif not (p['postal_code_from'] and p['postal_code_to']):
                                if (order.shipping_address.country == carrier_line_location.country and order.shipping_address.region == carrier_line_location.region):
                                    line_allowed = True
                                    break
                            else:
                                if (order.shipping_address.country == carrier_line_location.country and order.shipping_address.region == carrier_line_location.region and (order.shipping_address.postal_code >= carrier_line_location.postal_code_from and order.shipping_address.postal_code <= carrier_line_location.postal_code_to)):
                                    line_allowed = True
                                    break
                else:
                    # u slucaju da carrier line nema konfigurisane location exclusions-e onda se odnosi na sve lokacije/onda je to globalni carrier
                    line_allowed = True
                # ako je line_allowed nakon location check-a onda radimo validaciju po carrier line rules
                if (line_allowed):
                    for carrier_line_rule in carrier_line.rules:
                        # validacija carrier_line_rule,condition se ovde radi
                if (tax_allowed):
                    valid_carriers.append(tax)
        return valid_carriers

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
    # product_instance_reference = ndb.KeyProperty('11', kind=DomainProductInstance, required=True)
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
    
    _KIND = 0
    
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
    }
    
    # 
    @ndb.transactional
    def create():
        # ipn algoritam
        # **Preamble**
        # https://docs.google.com/document/d/1cHymrH2q6pHH19XOtOyLLsznR0tEb0-pkcU5ZGfS1hQ/edit#bookmark=id.fmp7h260u37l
        # **Duplicate Check**
        # na raspolaganju imamo kompletan ipn objekat, ili mozda skup variabla, kako se vec bude to formatiralo.
        if not (ipn.verified):
            # samo verifikovane ipn poruke dolaze u obzir
            return None
        # Kada stigne novi ipn, prvo se radi upit na tabelu i izvlace se svi recordi koji imaju istu vrednost txn_id kao i primljeni ipn.
        transactions = PayPalTransaction.query(PayPalTransaction.txn_id == ipn.txn_id).fetch()
        if (transactions):
            # Ukoliko ima rezultata, radi se provera da pristigla ipn poruka nije duplikat nekog od snimljenih recorda.
            for transaction in transactions:
                # Provera duplikata se vrsi tako sto se uporedjuje payment_status.
                # Za sve upisane transakcije sa istim txn_id, vrednosti payment_status moraju biti razlicite.
                # za sada se uzdamo u payment_status da garantuje uniqueness, ali mozda otkrijemo da to nije dobro resenje...
                if (transaction.payment_status == ipn.payment_status):
                    # Ukoliko je pristigla ipn poruka duplikat onda se tiho odbacuje i algoritam se prekida.
                    return None
        # Ukoliko nema rezultata iz upita na tabelu, ili je pristigla poruka unikatna, onda se prelazi na IPN Algoritam - Fraud Check.
        # **Fraud check**
        # Prvo ipn polje koje se proverava je custom koje bi trebalo da nosi referencu na record u order tabelama 
        # (u slucaju billing-a referencu na domenu za koju se kredit kupuje, i referencu na user account koji je inicirao kupovinu kredita).
        if (ipn.custom):
            reference = ipn.custom.get()
            if not (reference):
                # Ukoliko ovo polje nema vrednosti ili vrednost ne referencira record u order 
                # tabelama (ili store/user u slucaju billing-a), radi se dispatch na notification 
                # engine sa detaljima sta se dogodilo (kako bi se obavestilo da je pristigla 
                # validna poruka sa nevazecom referencom na order tabele), radi se logging i algoritam se prekida.
                return None
        paypal_transaction = PayPalTransaction(parent=reference.key, txn_id=ipn.txn_id, ipn_message=ipn)
        paypal_transaction_key = paypal_transaction.put()
        

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
    # composite index: ancestor:no - category,active,sequence
    updated = ndb.DateTimeProperty('1', auto_now=True, required=True)
    title = ndb.StringProperty('2', required=True)
    category = ndb.IntegerProperty('3', required=True)
    body = ndb.TextProperty('4', required=True)
    sequence = ndb.IntegerProperty('5', required=True)
    active = ndb.BooleanProperty('6', default=False)
    
    _KIND = 0
    
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    }
    
    # Ova akcija kreira novi content.
    @ndb.transactional
    def create():
        # ovu akciju moze izvrsiti samo agent koji ima globalnu dozvolu 'create-Content'.
        content = Content(title=var_title, category=var_category, body=var_body, sequence=var_sequence, active=var_active)
        content_key = content.put()
        object_log = ObjectLog(parent=content_key, agent=agent_key, action='create', state='none', log=content)
        object_log.put()
    
    # Ova akcija azurira content.
    @ndb.transactional
    def update():
        # ovu akciju moze izvrsiti samo agent koji ima globalnu dozvolu 'update-Content'.
        content.title = var_title
        content.category = var_category
        content.body = var_body
        content.sequence = var_sequence
        content.active = var_active
        content_key = content.put()
        object_log = ObjectLog(parent=content_key, agent=agent_key, action='update', state='none', log=content)
        object_log.put()
    
    # Ova akcija brise content.
    @ndb.transactional
    def delete():
        # ovu akciju moze izvrsiti samo agent koji ima globalnu dozvolu 'delete-Content'.
        object_log = ObjectLog(parent=content_key, agent=agent_key, action='delete', state='none')
        object_log.put()
        content_key.delete()

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
    
    _KIND = 0
    
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    }
    
    # Ova akcija kreira novi country.
    @ndb.transactional
    def create():
        # ovu akciju moze izvrsiti samo agent koji ima globalnu dozvolu 'create-Country'.
        country = Country(code=var_code, name=var_name, active=var_active)
        country_key = country.put()
        object_log = ObjectLog(parent=country_key, agent=agent_key, action='create', state='none', log=country)
        object_log.put()
    
    # Ova akcija azurira country.
    @ndb.transactional
    def update():
        # ovu akciju moze izvrsiti samo agent koji ima globalnu dozvolu 'update-Country'.
        country.code = var_code
        country.name = var_name
        country.active = var_active
        country_key = country.put()
        object_log = ObjectLog(parent=country_key, agent=agent_key, action='update', state='none', log=country)
        object_log.put()
    
    # Ova akcija brise country.
    @ndb.transactional
    def delete():
        # ovu akciju moze izvrsiti samo agent koji ima globalnu dozvolu 'delete-Country'.
        object_log = ObjectLog(parent=country_key, agent=agent_key, action='delete', state='none')
        object_log.put()
        country_subdivisions = CountrySubdivision.query(ancestor=country_key).fetch(keys_only=True)
        # ovaj metod ne loguje brisanje pojedinacno svakog country_subdivision entiteta, pa se trebati ustvari pozivati CountrySubdivision.delete() sa listom kljuceva.
        # CountrySubdivision.delete() nije za sada nije opisana da radi multi key delete.
        # a mozda je ta tehnika nepotrebna, posto se logovanje brisanja samog Country entiteta podrazumvea da su svi potomci izbrisani!!
        ndb.delete_multi(country_subdivisions)
        country_key.delete()

# done! - tryton ima CountrySubdivision za skoro sve zemlje!
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
    
    _KIND = 0
    
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    }
    
    # Ova akcija kreira novi country subdivision.
    @ndb.transactional
    def create():
        # ovu akciju moze izvrsiti samo agent koji ima globalnu dozvolu 'create-CountrySubdivision'.
        country_subdivision = CountrySubdivision(parent=country_key, parent_record=var_parent_record, code=var_code, name=var_name, type=var_type, active=var_active)
        country_subdivision_key = country_subdivision.put()
        object_log = ObjectLog(parent=country_subdivision_key, agent=agent_key, action='create', state='none', log=country_subdivision)
        object_log.put()
    
    # Ova akcija azurira country subdivision.
    @ndb.transactional
    def update():
        # ovu akciju moze izvrsiti samo agent koji ima globalnu dozvolu 'update-CountrySubdivision'.
        country_subdivision.parent_record = var_parent_record
        country_subdivision.code = var_code
        country_subdivision.name = var_name
        country_subdivision.type = var_type
        country_subdivision.active = var_active
        country_subdivision_key = country_subdivision.put()
        object_log = ObjectLog(parent=country_subdivision_key, agent=agent_key, action='update', state='none', log=country_subdivision)
        object_log.put()
    
    # Ova akcija brise country subdivision.
    @ndb.transactional
    def delete():
        # ovu akciju moze izvrsiti samo agent koji ima globalnu dozvolu 'delete-CountrySubdivision'.
        object_log = ObjectLog(parent=country_subdivision_key, agent=agent_key, action='delete', state='none')
        object_log.put()
        country_subdivision_key.delete()

# done!
class Location(ndb.Expando):
    
    # base class/structured class
    country = ndb.KeyProperty('1', kind=Country, required=True, indexed=False)
    _default_indexed = False
    pass
    # Expando
    # region = ndb.KeyProperty('2', kind=CountrySubdivision)# ako je potreban string val onda se ovo preskace / tryton ima CountrySubdivision za skoro sve zemlje
    # region = ndb.StringProperty('2')# ako je potreban key val onda se ovo preksace / tryton ima CountrySubdivision za skoro sve zemlje
    # postal_code_from = ndb.StringProperty('3')
    # postal_code_to = ndb.StringProperty('4')
    # city = ndb.StringProperty('5')# ako se javi potreba za ovim ??

# done!
class ProductCategory(ndb.Model):
    
    # root
    # http://hg.tryton.org/modules/product/file/tip/category.py#l8
    # https://support.google.com/merchants/answer/1705911
    # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/product/product.py#L227
    # composite index: ancestor:no - status,name
    parent_record = ndb.KeyProperty('1', kind=ProductCategory, indexed=False)
    name = ndb.StringProperty('2', required=True)
    complete_name = ndb.TextProperty('3', required=True)# da je ovo indexable bilo bi idealno za projection query
    status = ndb.IntegerProperty('4', required=True)
    
    _KIND = 0
    
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    }
    
    # Ova akcija kreira novi product category.
    @ndb.transactional
    def create():
        # ovu akciju moze izvrsiti samo agent koji ima globalnu dozvolu 'create-ProductCategory'.
        product_category = ProductCategory(parent_record=var_parent_record, name=var_name, complete_name=var_complete_name, status=var_status)
        product_category_key = product_category.put()
        object_log = ObjectLog(parent=product_category_key, agent=agent_key, action='create', state='none', log=product_category)
        object_log.put()
    
    # Ova akcija azurira product category.
    @ndb.transactional
    def update():
        # ovu akciju moze izvrsiti samo agent koji ima globalnu dozvolu 'update-ProductCategory'.
        product_category.parent_record = var_parent_record
        product_category.name = var_name
        product_category.complete_name = var_complete_name
        product_category.status = var_status
        product_category_key = product_category.put()
        object_log = ObjectLog(parent=product_category_key, agent=agent_key, action='update', state='none', log=product_category)
        object_log.put()
    
    # Ova akcija brise product category.
    @ndb.transactional
    def delete():
        # ovu akciju moze izvrsiti samo agent koji ima globalnu dozvolu 'delete-ProductCategory'.
        object_log = ObjectLog(parent=product_category_key, agent=agent_key, action='delete', state='none')
        object_log.put()
        product_category_key.delete()

# done!
class ProductUOMCategory(ndb.Model):
    
    # root
    # http://hg.tryton.org/modules/product/file/tip/uom.py#l16
    # http://bazaar.launchpad.net/~openerp/openobject-addons/7.0/view/head:/product/product.py#L81
    # mozda da ovi entiteti budu non-deletable i non-editable ??
    name = ndb.StringProperty('1', required=True)
    
    _KIND = 0
    
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    }
    
    # Ova akcija kreira novi product uom category.
    @ndb.transactional
    def create():
        # ovu akciju moze izvrsiti samo agent koji ima globalnu dozvolu 'create-ProductUOMCategory'.
        product_uom_category = ProductUOMCategory(name=var_name)
        product_uom_category_key = product_uom_category.put()
        object_log = ObjectLog(parent=product_uom_category_key, agent=agent_key, action='create', state='none', log=product_uom_category)
        object_log.put()
    
    # Ova akcija azurira product uom category.
    @ndb.transactional
    def update():
        # ovu akciju moze izvrsiti samo agent koji ima globalnu dozvolu 'update-ProductUOMCategory'.
        product_uom_category.name = var_name
        product_uom_category_key = product_uom_category.put()
        object_log = ObjectLog(parent=product_uom_category_key, agent=agent_key, action='update', state='none', log=product_uom_category)
        object_log.put()
    
    # Ova akcija brise product uom category.
    @ndb.transactional
    def delete():
        # ovu akciju moze izvrsiti samo agent koji ima globalnu dozvolu 'delete-ProductUOMCategory'.
        object_log = ObjectLog(parent=product_uom_category_key, agent=agent_key, action='delete', state='none')
        object_log.put()
        product_uoms = ProductUOM.query(ancestor=product_uom_category_key).fetch(keys_only=True)
        # ovaj metod ne loguje brisanje pojedinacno svakog product_uom entiteta, pa se trebati ustvari pozivati ProductUOM.delete() sa listom kljuceva.
        # ProductUOM.delete() nije za sada nije opisana da radi multi key delete.
        # a mozda je ta tehnika nepotrebna, posto se logovanje brisanja samog ProductUOMCategory entiteta podrazumvea da su svi potomci izbrisani!!
        ndb.delete_multi(product_uoms)
        product_uom_category_key.delete()

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
    
    _KIND = 0
    
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    }
    
    # Ova akcija kreira novi product uom.
    @ndb.transactional
    def create():
        # ovu akciju moze izvrsiti samo agent koji ima globalnu dozvolu 'create-ProductUOM'.
        product_uom = ProductUOM(parent=product_uom_category_key, name=var_name, symbol=var_symbol, rate=var_rate, factor=var_factor, rounding=var_rounding, digits=var_digits, active=var_active)
        product_uom_key = product_uom.put()
        object_log = ObjectLog(parent=product_uom_key, agent=agent_key, action='create', state='none', log=product_uom)
        object_log.put()
    
    # Ova akcija azurira product uom.
    @ndb.transactional
    def update():
        # ovu akciju moze izvrsiti samo agent koji ima globalnu dozvolu 'update-ProductUOM'.
        product_uom.name = var_name
        product_uom.symbol = var_symbol
        product_uom.rate = var_rate
        product_uom.factor = var_factor
        product_uom.rounding = var_rounding
        product_uom.digits = var_digits
        product_uom.active = var_active
        product_uom_key = product_uom.put()
        object_log = ObjectLog(parent=product_uom_key, agent=agent_key, action='update', state='none', log=product_uom)
        object_log.put()
    
    # Ova akcija brise product uom.
    @ndb.transactional
    def delete():
        # ovu akciju moze izvrsiti samo agent koji ima globalnu dozvolu 'delete-ProductUOM'.
        object_log = ObjectLog(parent=product_uom_key, agent=agent_key, action='delete', state='none')
        object_log.put()
        product_uom_key.delete()

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
    
    _KIND = 0
    
    OBJECT_DEFAULT_STATE = 'none'
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'delete' : 3,
    }
    
    # Ova akcija kreira novi currency.
    @ndb.transactional
    def create():
        # ovu akciju moze izvrsiti samo agent koji ima globalnu dozvolu 'create-Currency'.
        currency = Currency()
        currency.name = var_name
        currency.symbol = var_symbol
        currency.code = var_code
        currency.numeric_code = var_numeric_code
        currency.rounding = var_rounding
        currency.digits = var_digits
        currency.active = var_active
        currency.grouping = var_grouping
        currency.decimal_separator = var_decimal_separator
        currency.thousands_separator = var_thousands_separator
        currency.positive_sign_position = var_positive_sign_position
        currency.negative_sign_position = var_negative_sign_position
        currency.positive_sign = var_positive_sign
        currency.negative_sign = var_negative_sign
        currency.positive_currency_symbol_precedes = var_positive_currency_symbol_precedes
        currency.negative_currency_symbol_precedes = var_negative_currency_symbol_precedes
        currency.positive_separate_by_space = var_positive_separate_by_space
        currency.negative_separate_by_space = var_negative_separate_by_space
        currency_key = currency.put()
        object_log = ObjectLog(parent=currency_key, agent=agent_key, action='create', state='none', log=currency)
        object_log.put()
    
    # Ova akcija azurira currency.
    @ndb.transactional
    def update():
        # ovu akciju moze izvrsiti samo agent koji ima globalnu dozvolu 'update-Currency'.
        currency.name = var_name
        currency.symbol = var_symbol
        currency.code = var_code
        currency.numeric_code = var_numeric_code
        currency.rounding = var_rounding
        currency.digits = var_digits
        currency.active = var_active
        currency.grouping = var_grouping
        currency.decimal_separator = var_decimal_separator
        currency.thousands_separator = var_thousands_separator
        currency.positive_sign_position = var_positive_sign_position
        currency.negative_sign_position = var_negative_sign_position
        currency.positive_sign = var_positive_sign
        currency.negative_sign = var_negative_sign
        currency.positive_currency_symbol_precedes = var_positive_currency_symbol_precedes
        currency.negative_currency_symbol_precedes = var_negative_currency_symbol_precedes
        currency.positive_separate_by_space = var_positive_separate_by_space
        currency.negative_separate_by_space = var_negative_separate_by_space
        currency_key = currency.put()
        object_log = ObjectLog(parent=currency_key, agent=agent_key, action='update', state='none', log=currency)
        object_log.put()
    
    # Ova akcija brise currency.
    @ndb.transactional
    def delete():
        # ovu akciju moze izvrsiti samo agent koji ima globalnu dozvolu 'delete-Currency'.
        object_log = ObjectLog(parent=currency_key, agent=agent_key, action='delete', state='none')
        object_log.put()
        currency_key.delete()

# done!
# ostaje da se ispita u preprodukciji!!
class Message(ndb.Model):
    
    # root
    outlet = ndb.IntegerProperty('1', required=True, indexed=False)
    group = ndb.IntegerProperty('2', required=True, indexed=False)
    state = ndb.IntegerProperty('3', required=True)
    
    _KIND = 0
    
    OBJECT_DEFAULT_STATE = 'composing'
    
    OBJECT_STATES = {
        # tuple represents (state_code, transition_name)
        # second value represents which transition will be called for changing the state
        # Ne znam da li je predvidjeno ovde da moze biti vise tranzicija/akcija koje vode do istog state-a,
        # sto ce biti slucaj sa verovatno mnogim modelima.
        # broj 0 je rezervisan za none (Stateless Models) i ne koristi se za definiciju validnih state-ova
        'composing' : (1, ),
        'processing' : (2, ),
        'completed' : (3, ),
        'canceled' : (4, ),
    }
    
    OBJECT_ACTIONS = {
       'create' : 1,
       'update' : 2,
       'send' : 3,
       'complete' : 4,
       'cancel' : 5,
    }
    
    OBJECT_TRANSITIONS = {
        'send' : {
            'from' : ('composing',),
            'to' : ('processing',),
         },
        'complete' : {
           'from' : ('processing',),
           'to'   : ('completed',),
        },
        'cancel' : {
           'from' : ('composing',),
           'to'   : ('canceled',),
        },
    }
    
    # Ova akcija kreira novi message.
    @ndb.transactional
    def create():
        # ovu akciju moze izvrsiti samo agent koji ima globalnu dozvolu 'create-Message'.
        message = Message(outlet=var_outlet, group=var_group, state='composing')
        message_key = message.put()
        object_log = ObjectLog(parent=message_key, agent=agent_key, action='create', state=message.state, message='poruka od agenta - obavezno polje!', note='privatni komentar agenta (dostupan samo privilegovanim agentima) - obavezno polje!')
        object_log.put()
    
    # Ova akcija azurira postojeci message.
    @ndb.transactional
    def update():
        # ovu akciju moze izvrsiti samo agent koji ima globalnu dozvolu 'update-Message'.
        # akcija se moze pozvati samo ako je message.state == 'composing'.
        object_log = ObjectLog(parent=message_key, agent=agent_key, action='update', state=message.state, message='poruka od agenta - obavezno polje!', note='privatni komentar agenta (dostupan samo privilegovanim agentima) - obavezno polje!')
        object_log.put()
    
    # Ova akcija salje poruku. Ovde cemo dalje opisati posledice slanja...
    @ndb.transactional
    def send():
        # ovu akciju moze izvrsiti samo agent koji ima globalnu dozvolu 'send-Message'.
        # akcija se moze pozvati samo ako je message.state == 'composing'.
        message.state = 'processing'
        message_key = message.put()
        object_log = ObjectLog(parent=message_key, agent=agent_key, action='send', state=message.state, note='privatni komentar agenta (dostupan samo privilegovanim agentima) - obavezno polje!')
        object_log.put()
        # ovde se dalje inicira distribucija poruke preko task queue...
    
    # Ova akcija oznacava poruku kao poslanu. Ovde cemo dalje opisati posledice oznacavanja poruke kao poslane...
    @ndb.transactional
    def complete():
        # ovu akciju moze izvrsiti samo agent koji ima globalnu dozvolu 'complete-Message'. ovu akciju poziva sistemski agent sa eventualnim izvestajem sta je uradjeno.
        # akcija se moze pozvati samo ako je message.state == 'processing'.
        message.state = 'completed'
        message_key = message.put()
        object_log = ObjectLog(parent=message_key, agent=agent_key, action='complete', state=message.state, note='privatni komentar agenta (dostupan samo privilegovanim agentima) - obavezno polje!')
        object_log.put()
    
    # Ova akcija obustavlja poruku. Ovde cemo dalje opisati posledice obustavljanja...
    @ndb.transactional
    def cancel():
        # ovu akciju moze izvrsiti samo agent koji ima globalnu dozvolu 'cancel-Message'.
        # akcija se moze pozvati samo ako je message.state == 'composing'.
        message.state = 'canceled'
        message_key = message.put()
        object_log = ObjectLog(parent=message_key, agent=agent_key, action='cancel', state=message.state, note='privatni komentar agenta (dostupan samo privilegovanim agentima) - obavezno polje!')
        object_log.put()

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

# neki primer toola za formatiranje Decimal vrednosti
class DecTools(object):
    
    @staticmethod
    def form(value, formater=None):
        if (formater):
            if (isinstance(formater, str)):
                return Decimal(format(Decimal(value), formater))
            else:
                return Decimal(format(Decimal(value), '.' + formater.digits + 'f'))
        else:
            return Decimal(value)
        
        