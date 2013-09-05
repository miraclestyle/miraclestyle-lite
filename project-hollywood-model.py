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
# CORE - 8
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
            # suspend can go from active to suspended
           'from' : ('active', ),
           'to'   : ('suspended',),
        },
    }
    
    # Ova akcija nastaje prilikom prve autentikacije kada korisnik nije jos registrovan.
    # Ukoliko se prilikom "login" akcije ustanovi da korisnik nikada nije evidentiran u bazi, nastupa akcija "register". 
    @ndb.transactional
    def register():
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

    # Ova akcija se izvrsava svaki put kada neautenticirani korisnik stupi u proces autentikacije.
    # Prvo se proverava da li je korisnik vec registrovan. Ukoliko User ne postoji onda se prelazi na akciju "register".
    # Ukoliko user postoji, onda se dalje ispituje. 
    # Proverava se da li ima nekih izmena na postojecim podacima, i ukoliko ima, onda se poziva "update" akcija.
    # Dalje se proverava da li je useru dozvoljen login (User.state == 'active'). Ako mu je dozvoljen login onda se izvrsava "login" akcija.
    @ndb.transactional
    def login():
        # ovde bi mogla da stoji provera continue if(User.state == 'active'),ili vani, videcemo.
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
        # ova akcija zahteva da agent ima globalnu dozvolu 'suspend'.
        # akcija se moze pozvati samo ako je user.state == 'active'
        user.state = 'suspended'
        user_key = user.put()
        object_log = ObjectLog(parent=user_key, agent='agent_key', action='suspend', state=user.state, message='poruka od agenta - obavezno polje!', note='privatni komentar agenta (dostupan samo privilegovanim agentima) - obavezno polje!', log=user)
        object_log.put()
        # poziva se akcija "logout";
        User.logout()

    # Ova akcija sluzi za aktiviranje suspendovanog korisnika i izvrsava je privilegovani/administrativni agent.
    # Treba obratiti paznju na to da aktivacija usera ujedno znaci i vracanje svih negativnih i neutralnih feedbackova koje je user ostavio dok je bio aktivan, a koji su bili izuzeti dok je bio suspendovan.
    # Aktivni user account je u potpunosti funkcionalan i operativan.
    @ndb.transactional
    def activate():
        # ova akcija zahteva da agent ima globalnu dozvolu 'activate'.
        # akcija se moze pozvati samo ako je user.state == 'suspended'
        user.state = 'active'
        user_key = user.put()
        object_log = ObjectLog(parent=user_key, agent='agent_key', action='activate', state=user.state, message='poruka od agenta - obavezno polje!', note='privatni komentar agenta (dostupan samo privilegovanim agentima) - obavezno polje!', log=user)
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

# done! ovde je za svaki write potreban user approval tako da je contention skoro nemoguc!
class AggregateUserPermission(ndb.Model):
    
    # ancestor User
    # not logged
    reference = ndb.KeyProperty('1',required=True)# ovo je referenca na Role u slucaju da user nasledjuje globalne dozvole, tj kada je Role entitet root
    permissions = ndb.StringProperty('2', repeated=True, indexed=False)# soft limit 1000x - permission_state_model - edit_unpublished_catalog

# done!
class Domain(ndb.Expando):
    
    # root
    # composite index: ancestor:no - state,name
    name = ndb.StringProperty('1', required=True)
    primary_contact = ndb.KeyProperty('2', kind=User, required=True, indexed=False)
    state = ndb.IntegerProperty('3', required=True)
    _default_indexed = False
    pass
    #Expando

# done!
class Role(ndb.Model):
    
    # ancestor Domain with permissions that affect Domain and it's related entities
    # or root (if it is root, key id is manually assigned string) with global permissions on mstyle
    # mozda bude trebalo jos indexa u zavistnosti od potreba u UIUX
    # composite index: ancestor:yes - name
    name = ndb.StringProperty('1', required=True)
    permissions = ndb.StringProperty('2', repeated=True, indexed=False)# soft limit 1000x - permission_state_model - edit_unpublished_catalog
    readonly = ndb.BooleanProperty('3', default=True, indexed=False)

# done!
class RoleUser(ndb.Model):
    
    # ancestor Role
    # id = string(User.key.id)
    # mozda bude trebalo jos indexa u zavistnosti od potreba u UIUX
    # composite index: ancestor:yes - user
    user = ndb.KeyProperty('1', kind=User, required=True)
    state = ndb.IntegerProperty('2', required=True)# invited/accepted


################################################################################
# MISC - 12
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
        feedback_request = FeedbackRequest(parent=user_key, reference='https://www,miraclestyle.com/...', state='new')
        feedback_request_key = feedback_request.put()
        object_log = ObjectLog(parent=feedback_request_key, agent=user_key, action='create', state=feedback_request.state, message='poruka od agenta - obavezno polje!')
        object_log.put()

    # Ova akcija sluzi za insert ObjectLog-a koji je descendant FeedbackRequest entitetu.
    # Insertom ObjectLog-a dozvoljeno je unosenje poruke (i privatnog komentara), sto je i smisao ove akcije.
    @ndb.transactional
    def update():
        # ova akcija zahteva da agent ima globalnu dozvolu 'update'. / ova akcija zahteva da je agent ili owner (feedback_request.parent == agent) ili da agent ima globalnu dozvolu 'update'.
        # Radi se update FeedbackRequest-a bez izmena na bilo koji prop. (u cilju izazivanja promene na FeedbackRequest.updated prop.)
        feedback_request_key = feedback_request.put()
        object_log = ObjectLog(parent=feedback_request_key, agent=agent_key, action='update', state=feedback_request.state, message='poruka od agenta - obavezno polje!', note='privatni komentar agenta (dostupan samo privilegovanim agentima) - obavezno polje!')
        object_log.put()

    # Ovom akcijom privilegovani/administrativni agent menja stanje FeedbackRequest entiteta u 'reviewing'.
    @ndb.transactional
    def review():
        # ova akcija zahteva da agent ima globalnu dozvolu 'review'.
        # akcija se moze pozvati samo ako je feedback_request.state == 'new'
        feedback_request.state = 'reviewing'
        feedback_request_key = feedback_request.put()
        object_log = ObjectLog(parent=feedback_request_key, agent=agent_key, action='review', state=feedback_request.state, message='poruka od agenta - obavezno polje!', note='privatni komentar agenta (dostupan samo privilegovanim agentima) - obavezno polje!')
        object_log.put()

    # Ovom akcijom privilegovani/administrativni agent menja stanje FeedbackRequest entiteta u 'duplicate', 'accepted', ili 'dismissed'.
    @ndb.transactional
    def close():
        # ova akcija zahteva da agent ima globalnu dozvolu 'close'.
        # akcija se moze pozvati samo ako je feedback_request.state == 'reviewing'
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
        # finta je sto bi user trebao da moze da pozove ovu akciju i u slucaju da je pocetno stanje 'awaiting_closure'!
        'close' : {
           'from' : ('opened', 'awaiting_closure',),
           'to'   : ('closed',),
        },
    }

    # Ova akcija krajnjem korisniku sluzi za pravljenje zahteva za pomoc (ticket-a) od miraclestyle tima.
    @ndb.transactional
    def create():
        support_request = SupportRequest(parent=user_key, reference='https://www,miraclestyle.com/...', state='new')
        support_request_key = support_request.put()
        object_log = ObjectLog(parent=support_request_key, agent=user_key, action='create', state=support_request.state, message='poruka od agenta - obavezno polje!')
        object_log.put()

    # Ova akcija sluzi za insert ObjectLog-a koji je descendant SupportRequest entitetu.
    # Insertom ObjectLog-a dozvoljeno je unosenje poruke (i privatnog komentara), sto je i smisao ove akcije.
    @ndb.transactional
    def update():
        # ova akcija zahteva da je agent ili owner (support_request.parent == agent) ili da agent ima globalnu dozvolu 'update'.
        # Radi se update SupportRequest-a bez izmena na bilo koji prop. (u cilju izazivanja promene na SupportRequest.updated prop.)
        support_request_key = support_request.put()
        object_log = ObjectLog(parent=support_request_key, agent=agent_key, action='update', state=support_request.state, message='poruka od agenta - obavezno polje!', note='privatni komentar agenta (dostupan samo privilegovanim agentima/non-owner-ima) - obavezno polje!')
        object_log.put()

    # Ovom akcijom privilegovani/administrativni agent menja stanje SupportRequest entiteta u 'opened'.
    @ndb.transactional
    def open():
        # ova akcija zahteva da agent ima globalnu dozvolu 'open'.
        # akcija se moze pozvati samo ako je support_request.state == 'new'
        support_request.state = 'opened'
        support_request_key = support_request.put()
        object_log = ObjectLog(parent=support_request_key, agent=agent_key, action='open', state=support_request.state, message='poruka od agenta - obavezno polje!', note='privatni komentar agenta (dostupan samo privilegovanim agentima/non-owner-ima) - obavezno polje!')
        object_log.put()

    # Ovom akcijom privilegovani/administrativni agent menja stanje SupportRequest entiteta u 'awaiting_closure'.
    @ndb.transactional
    def propose_close():
        # ova akcija zahteva da agent ima globalnu dozvolu 'propose_close'.
        # akcija se moze pozvati samo ako je support_request.state == 'opened'
        support_request.state = 'awaiting_closure'
        support_request_key = support_request.put()
        object_log = ObjectLog(parent=support_request_key, agent=agent_key, action='propose_close', state=support_request.state, message='poruka od agenta - obavezno polje!', note='privatni komentar agenta (dostupan samo privilegovanim agentima/non-owner-ima) - obavezno polje!')
        object_log.put()

    # Ovom akcijom agent menja stanje SupportRequest entiteta u 'closed'.
    @ndb.transactional
    def close():
        # ova akcija zahteva da je agent ili owner (support_request.parent == agent) ili da agent ima globalnu dozvolu 'close' (sto ce verovatno imati sistemski account koji ce preko cron-a izvrsiti akciju).
        # akcija se moze pozvati samo ako je support_request.state == 'opened' ili support_request.state == 'awaiting_closure'
        support_request.state = 'closed'
        support_request_key = support_request.put()
        object_log = ObjectLog(parent=support_request_key, agent=agent_key, action='close', state=support_request.state, message='poruka od agenta - obavezno polje!', note='privatni komentar agenta (dostupan samo privilegovanim agentima/non-owner-ima) - obavezno polje!')
        object_log.put()

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

# done!
class BuyerCollection(ndb.Model):
    
    # ancestor User
    # composite index: ancestor:yes - name
    name = ndb.StringProperty('1', required=True)
    notifications = ndb.BooleanProperty('2', default=False)
    primary_email = ndb.StringProperty('3', required=True, indexed=False)

# done!
class BuyerCollectionStore(ndb.Model):
    
    # ancestor User
    store = ndb.KeyProperty('1', kind=Store, required=True)
    collections = ndb.KeyProperty('2', kind=BuyerCollection, repeated=True)# soft limit 500x
    
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
# Domain - 8
################################################################################

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
    
    # ancestor Store (Catalog - for caching)
    # composite index: ancestor:yes - sequence
    title = ndb.StringProperty('1', required=True)
    body = ndb.TextProperty('2', required=True)
    sequence = ndb.IntegerProperty('3', required=True)

# done!
class StoreShippingExclusion(Location):
    
    # ancestor Store (Catalog - for caching)
    # ovde bi se indexi mozda mogli dobro iskoristiti?

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

# done!
class Carrier(ndb.Model):
    
    # root (namespace Domain)
    # http://bazaar.launchpad.net/~openerp/openobject-addons/saas-1/view/head:/delivery/delivery.py#L27
    # http://hg.tryton.org/modules/carrier/file/tip/carrier.py#l10
    # composite index: ancestor:no - active,name
    name = ndb.StringProperty('1', required=True)
    active = ndb.BooleanProperty('2', default=True)

# done!
class CarrierLine(ndb.Expando):
    
    # ancestor Carrier
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

# done!
class CarrierLineRule(ndb.Model):
    
    # LocalStructuredProperty model
    # http://bazaar.launchpad.net/~openerp/openobject-addons/saas-1/view/head:/delivery/delivery.py#L226
    # ovde se cuvaju dve vrednosti koje su obicno struktuirane kao formule, ovo je mnogo fleksibilnije nego hardcoded struktura informacija koje se cuva kao sto je bio prethodni slucaj
    condition = ndb.StringProperty('1', required=True, indexed=False)# prekompajlirane vrednosti iz UI, napr: True ili weight[kg] >= 5 ili volume[m3] = 0.002
    price = ndb.StringProperty('2', required=True, indexed=False)# prekompajlirane vrednosti iz UI, napr: amount = 35.99 ili amount = weight[kg]*0.28
    # weight - kg; volume - m3; ili sta vec odlucimo, samo je bitno da se podudara sa measurementsima na ProductTemplate/ProductInstance


################################################################################
# CATALOG - 9
################################################################################

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

# done!
class CatalogImage(Image):
    
    # ancestor Catalog
    # composite index: ancestor:yes - sequence

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
    
    # ancestor Catalog (future - root / namespace Domain)
    # composite index: ancestor:yes - name
    product_category = ndb.KeyProperty('1', kind=ProductCategory, required=True, indexed=False)
    name = ndb.StringProperty('2', required=True)
    description = ndb.TextProperty('3', required=True)# soft limit 64kb
    product_uom = ndb.KeyProperty('4', kind=ProductUOM, required=True, indexed=False)
    unit_price = DecimalProperty('5', required=True)
    state = ndb.IntegerProperty('6', required=True, indexed=False)
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
    # product_template_variants = ndb.KeyProperty('7', kind=ProductVariant, repeated=True)# soft limit 100x
    # product_template_contents = ndb.KeyProperty('8', kind=ProductContent, repeated=True)# soft limit 100x
    # product_template_images = ndb.LocalStructuredProperty(Image, '9', repeated=True)# soft limit 100x
    # weight = ndb.StringProperty('10')# prekompajlirana vrednost, napr: 0.2[kg] - gde je [kg] jediniva mere, ili sta vec odlucimo
    # volume = ndb.StringProperty('11')# prekompajlirana vrednost, napr: 0.03[m3] - gde je [m3] jediniva mere, ili sta vec odlucimo

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
    
    # ancestor ProductInstance
    # not logged
    adjusted = ndb.DateTimeProperty('1', auto_now_add=True, required=True, indexed=False)
    agent = ndb.KeyProperty('2', kind=User, required=True, indexed=False)
    quantity = DecimalProperty('3', required=True, indexed=False, indexed=False)
    comment = ndb.StringProperty('4', required=True, indexed=False)

# done!
class ProductVariant(ndb.Model):
    
    # ancestor Catalog (future - root / namespace Domain)
    # http://v6apps.openerp.com/addon/1809
    # composite index: ancestor:yes - name
    name = ndb.StringProperty('1', required=True)
    description = ndb.TextProperty('2')# soft limit 64kb
    options = ndb.StringProperty('3', repeated=True, indexed=False)# soft limit 1000x
    allow_custom_value = ndb.BooleanProperty('4', default=False, indexed=False)# ovu vrednost buyer upisuje u definisano polje a ona se dalje prepisuje u order line description prilikom Add to Cart 

# done!
class ProductContent(ndb.Model):
    
    # ancestor Catalog (future - root / namespace Domain)
    # composite index: ancestor:yes - title
    title = ndb.StringProperty('1', required=True)
    body = ndb.TextProperty('2', required=True)


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

