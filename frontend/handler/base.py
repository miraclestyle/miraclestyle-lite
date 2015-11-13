# -*- coding: utf-8 -*-
'''
Created on Jul 15, 2013

@author:  Edis Sehalic (edis.sehalic@gmail.com)
'''
import json
import os
import webapp2
import codecs
import re
import api
from webapp2_extras import jinja2
from google.appengine.api import urlfetch

from jinja2 import evalcontextfilter, Markup, escape

import settings
import api

KNOWN_BOT_AGENTS = [
        '007ac9 Crawler',
        '008\\/',
        '360Spider',
        'A6-Indexer',
        'ABACHOBot',
        'AbiLogicBot',
        'Aboundex',
        'Accoona-AI-Agent',
        'acoon',
        'AddSugarSpiderBot',
        'AddThis',
        'Adidxbot',
        'ADmantX',
        'AdvBot',
        'ahrefsbot',
        'aihitbot',
        'Airmail',
        'AISearchBot',
        'Anemone',
        'antibot',
        'AnyApexBot',
        'Applebot',
        'arabot',
        'Arachmo',
        'archive-com',
        'archive.org_bot',
        'B-l-i-t-z-B-O-T',
        'backlinkcrawler',
        'baiduspider',
        'BecomeBot',
        'BeslistBot',
        'bibnum\.bnf',
        'biglotron',
        'BillyBobBot',
        'Bimbot',
        'bingbot',
        'binlar',
        'blekkobot',
        'blexbot',
        'BlitzBOT',
        'bl\.uk_lddc_bot',
        'bnf\.fr_bot',
        'boitho\.com-dc',
        'boitho\.com-robot',
        'brainobot',
        'btbot',
        'BUbiNG',
        'Butterfly\/',
        'buzzbot',
        'careerbot',
        'CatchBot',
        'CC Metadata Scaper',
        'ccbot',
        'Cerberian Drtrs',
        'changedetection',
        'Charlotte',
        'CloudFlare-AlwaysOnline',
        'citeseerxbot',
        'coccoc',
        'classbot',
        'Commons-HttpClient',
        'content crawler spider',
        'Content Crawler',
        'convera',
        'ConveraCrawler',
        'CoPubbot',
        'cosmos',
        'Covario-IDS',
        'CrawlBot',
        'crawler4j',
        'CrystalSemanticsBot',
        'curl',
        'cXensebot',
        'CyberPatrol',
        'DataparkSearch',
        'dataprovider',
        'DiamondBot',
        'Digg',
        'discobot',
        'DomainAppender',
        'domaincrawler',
        'Domain Re-Animator Bot',
        'dotbot',
        'drupact',
        'DuckDuckBot',
        'EARTHCOM',
        'EasouSpider',
        'ec2linkfinder',
        'edisterbot',
        'ElectricMonk',
        'elisabot',
        'emailmarketingrobot',
        'EmeraldShield\.com WebBot',
        'envolk\[ITS\]spider',
        'EsperanzaBot',
        'europarchive\.org',
        'exabot',
        'ezooms',
        'facebookexternalhit',
        'Facebot',
        'FAST Enteprise Crawler',
        'FAST Enterprise Crawler',
        'FAST-WebCrawler',
        'FDSE robot',
        'Feedfetcher-Google',
        'FindLinks',
        'findlink',
        'findthatfile',
        'findxbot',
        'Flamingo_SearchEngine',
        'fluffy',
        'fr-crawler',
        'FRCrawler',
        'FurlBot',
        'FyberSpider',
        'g00g1e\.net',
        'GigablastOpenSource',
        'grub-client',
        'g2crawler',
        'Gaisbot',
        'GalaxyBot',
        'genieBot',
        'Genieo',
        'GermCrawler',
        'gigabot',
        'GingerCrawler',
        'Girafabot',
        'Gluten Free Crawler',
        'gnam gnam spider',
        'Googlebot-Image',
        'Googlebot-Mobile',
        'Googlebot',
        'GrapeshotCrawler',
        'gslfbot',
        'GurujiBot',
        'HappyFunBot',
        'Healthbot',
        'heritrix',
        'hl_ftien_spider',
        'Holmes',
        'htdig',
        'httpunit',
        'httrack',
        'ia_archiver',
        'iaskspider',
        'iCCrawler',
        'ichiro',
        'igdeSpyder',
        'iisbot',
        'InAGist',
        'InfoWizards Reciprocal Link System PRO',
        'Insitesbot',
        'integromedb',
        'intelium_bot',
        'InterfaxScanBot',
        'IODC',
        'IOI',
        'ip-web-crawler\.com',
        'ips-agent',
        'IRLbot',
        'IssueCrawler',
        'IstellaBot',
        'it2media-domain-crawler',
        'iZSearch',
        'Jaxified Bot',
        'JOC Web Spider',
        'jyxobot',
        'KoepaBot',
        'L\.webis',
        'LapozzBot',
        'Larbin',
        'lb-spider',
        'LDSpider',
        'LexxeBot',
        'libwww',
        'Linguee Bot',
        'Link Valet',
        'linkdex',
        'LinkExaminer',
        'LinksManager\.com_bot',
        'LinkpadBot',
        'LinksCrawler',
        'LinkWalker',
        'Lipperhey Link Explorer',
        'Lipperhey SEO Service',
        'Livelapbot',
        'lmspider',
        'lssbot',
        'lssrocketcrawler',
        'ltx71',
        'lufsbot',
        'lwp-trivial',
        'Mail\.RU_Bot',
        'MegaIndex\.ru',
        'mabontland',
        'magpie-crawler',
        'Mediapartners-Google',
        'memorybot',
        'MetaURI',
        'MJ12bot',
        'mlbot',
        'Mnogosearch',
        'mogimogi',
        'MojeekBot',
        'Moreoverbot',
        'Morning Paper',
        'Mrcgiguy',
        'MSIECrawler',
        'msnbot',
        'msrbot',
        'MVAClient',
        'mxbot',
        'NerdByNature\.Bot',
        'NerdyBot',
        'netEstate NE Crawler',
        'netresearchserver',
        'NetSeer Crawler',
        'NewsGator',
        'NextGenSearchBot',
        'NG-Search',
        'ngbot',
        'nicebot',
        'niki-bot',
        'Notifixious',
        'noxtrumbot',
        'Nusearch Spider',
        'nutch',
        'NutchCVS',
        'Nymesis',
        'obot',
        'oegp',
        'ocrawler',
        'omgilibot',
        'OmniExplorer_Bot',
        'online link validator',
        'Online Website Link Checker',
        'OOZBOT',
        'openindexspider',
        'OpenWebSpider',
        'OrangeBot',
        'Orbiter',
        'ow\.ly',
        'PaperLiBot',
        'Pingdom\.com_bot',
        'Ploetz \+ Zeller',
        'page2rss',
        'PageBitesHyperBot',
        'panscient',
        'Peew',
        'PercolateCrawler',
        'phpcrawl',
        'Pizilla',
        'Plukkie',
        'polybot',
        'Pompos',
        'PostPost',
        'postrank',
        'proximic',
        'psbot',
        'purebot',
        'PycURL',
        'python-requests',
        'Python-urllib',
        'Qseero',
        'QuerySeekerSpider',
        'Qwantify',
        'Radian6',
        'RAMPyBot',
        'REL Link Checker',
        'RetrevoPageAnalyzer',
        'Riddler',
        'Robosourcer',
        'rogerbot',
        'RufusBot',
        'SandCrawler',
        'SBIder',
        'ScoutJet',
        'Scrapy',
        'ScreenerBot',
        'scribdbot',
        'Scrubby',
        'SearchmetricsBot',
        'SearchSight',
        'seekbot',
        'semanticdiscovery',
        'SemrushBot',
        'Sensis Web Crawler',
        'SEOChat::Bot',
        'seokicks-robot',
        'SEOstats',
        'Seznam screenshot-generator',
        'seznambot',
        'Shim-Crawler',
        'ShopWiki',
        'Shoula robot',
        'ShowyouBot',
        'SimpleCrawler',
        'sistrix crawler',
        'SiteBar',
        'sitebot',
        'siteexplorer\.info',
        'SklikBot',
        'slider\.com',
        'slurp',
        'smtbot',
        'Snappy',
        'sogou spider',
        'sogou',
        'Sosospider',
        'spbot',
        'Speedy Spider',
        'speedy',
        'SpiderMan',
        'Sqworm',
        'SSL-Crawler',
        'StackRambler',
        'suggybot',
        'summify',
        'SurdotlyBot',
        'SurveyBot',
        'SynooBot',
        'tagoobot',
        'teoma',
        'TerrawizBot',
        'TheSuBot',
        'Thumbnail\.CZ robot',
        'TinEye',
        'toplistbot',
        'trendictionbot',
        'TrueBot',
        'truwoGPS',
        'turnitinbot',
        'TweetedTimes Bot',
        'TweetmemeBot',
        'twengabot',
        'Twitterbot',
        'uMBot',
        'UnisterBot',
        'UnwindFetchor',
        'updated',
        'urlappendbot',
        'Urlfilebot',
        'urlresolver',
        'UsineNouvelleCrawler',
        'Vagabondo',
        'Vivante Link Checker',
        'voilabot',
        'Vortex',
        'voyager\\/',
        'VYU2',
        'web-archive-net\.com\.bot',
        'Websquash\.com',
        'WeSEE:Ads\/PageBot',
        'wbsearchbot',
        'webcollage',
        'webcompanycrawler',
        'webcrawler',
        'webmon ',
        'WeSEE:Search',
        'wf84',
        'wget',
        'wocbot',
        'WoFindeIch Robot',
        'WomlpeFactory',
        'woriobot',
        'wotbox',
        'Xaldon_WebSpider',
        'Xenu Link Sleuth',
        'xintellibot',
        'XML Sitemaps Generator',
        'XoviBot',
        'Y!J-ASR',
        'yacy',
        'yacybot',
        'Yahoo Link Preview',
        'Yahoo! Slurp China',
        'Yahoo! Slurp',
        'YahooSeeker',
        'YahooSeeker-Testing',
        'YandexBot',
        'YandexImages',
        'YandexMetrika',
        'yandex',
        'yanga',
        'Yasaklibot',
        'yeti',
        'YioopBot',
        'YisouSpider',
        'YodaoBot',
        'yoogliFetchAgent',
        'yoozBot',
        'YoudaoBot',
        'Zao',
        'Zealbot',
        'zspider',
        'ZyBorg']


class JSONEncoder(json.JSONEncoder):

  def iterencode(self, o, _one_shot=False):
    chunks = super(JSONEncoder, self).iterencode(o, _one_shot)
    for chunk in chunks:
      chunk = chunk.replace('&', '\\u0026')
      chunk = chunk.replace('<', '\\u003c')
      chunk = chunk.replace('>', '\\u003e')
      yield chunk


def to_json(s, **kwds):
  kwds['cls'] = JSONEncoder
  return json.dumps(s, **kwds)


def _static_dir(file_path):
  return '%s/client/%s' % (settings.get_host_url(), file_path)


def _angular_include_template(path):
  return codecs.open(os.path.join(settings.ROOT_DIR, 'templates/angular/parts', path), 'r', 'utf-8').read()

settings.JINJA_GLOBALS.update({'static_dir': _static_dir,
                               'settings': settings,
                               'len': len,
                               'angular_include_template': _angular_include_template})

settings.JINJA_FILTERS.update({'to_json': to_json, 'static_dir': _static_dir})


class RequestHandler(webapp2.RequestHandler):

  '''General-purpose handler from which all other frontend handlers must derrive from.'''

  def __init__(self, *args, **kwargs):
    super(RequestHandler, self).__init__(*args, **kwargs)
    self.data = {}
    self.template = {}

  def send_json(self, data):
    ''' sends `data` to be serialized in json format, and sets content type application/json utf8'''
    ent = 'application/json;charset=utf-8'
    if self.response.headers.get('Content-Type') != ent:
      self.response.headers['Content-Type'] = ent
    self.response.write(json.dumps(data))

  def before(self):
    '''
    This function is fired just before the handler logic is executed
    '''
    pass

  def after(self):
    '''
    This function is fired just after the handler is executed
    '''
    pass

  def get(self, *args, **kwargs):
    return self.respond(*args, **kwargs)

  def post(self, *args, **kwargs):
    return self.respond(*args, **kwargs)

  def respond(self, *args, **kwargs):
    self.abort(404)
    self.response.write('<h1>404 Not found</h1>')

  def dispatch(self):
    self.template['base_url'] = self.request.host_url
    try:
      self.before()
      super(RequestHandler, self).dispatch()
      self.after()
    finally:
      pass

  @webapp2.cached_property
  def jinja2(self):
    # Returns a Jinja2 renderer cached in the app registry.
    return jinja2.get_jinja2(app=self.app)

  def render_response(self, _template, **context):
    # Renders a template and writes the result to the response.
    rv = self.jinja2.render_template(_template, **context)
    self.response.write(rv)

  def render(self, tpl, data=None):
    if data is None:
      data = {}
    self.template.update(data)
    return self.render_response(tpl, **self.template)


class Blank(RequestHandler):

  '''Blank response base class'''

  def respond(self, *args, **kwargs):
    pass


class Angular(RequestHandler):

  '''Angular subclass of base handler'''

  base_template = 'angular/index.html'

  def get(self, *args, **kwargs):
    data = self.respond(*args, **kwargs)
    if data:
      self.data = data

  def post(self, *args, **kwargs):
    data = self.respond(*args, **kwargs)
    if data:
      self.data = data

  def after(self):
    if (self.request.headers.get('X-Requested-With', '').lower() == 'xmlhttprequest'):
      if not self.data:
        self.data = {}
        if self.response.status == 200:
          self.response.status = 204
      self.send_json(self.data)
      return
    else:
      # always return the index.html rendering as init
      self.render(self.base_template)


class AngularBlank(Angular):

  '''Same as Blank, but for angular'''

  def respond(self, *args, **kwargs):
    pass


class SeoOrAngular(AngularBlank):

  out = None

  @property
  def is_seo(self):
    agent = self.request.headers.get('User-Agent')
    if agent:
      general_match = re.search('(bot|crawl|slurp|spider|facebook|twitter|pinterest|linkedin)', agent)
      manual_debug = self.request.cookies.get('seo') == '1' or self.request.get('__seo') == '1'
      return  general_match or manual_debug or agent in KNOWN_BOT_AGENTS
    return False

  def respond_angular(self, *args, **kwargs):
    return super(SeoOrAngular, self).respond(*args, **kwargs)

  def respond(self, *args, **kwargs):
    if not self.is_seo:
      return self.respond_angular(*args, **kwargs)
    else:
      return self.respond_seo(*args, **kwargs)

  def respond_seo(self, *args, **kargs):
    self.abort(404)

  def api_endpoint(self, *args, **kwargs):
    if 'headers' not in kwargs:
      kwargs['headers'] = self.request.headers
    response = api.endpoint(*args, **kwargs)
    if 'errors' in response:
      self.abort(503, response['errors'])
    return response

  def after(self):
    if not self.is_seo:
      super(SeoOrAngular, self).after()


def autohttps(s):
    if os.environ.get('HTTPS') == 'on':
        return s.replace('http://', 'https://')
    return s

settings.JINJA_GLOBALS.update({'uri_for': webapp2.uri_for, 'ROUTES': settings.ROUTES, 'settings': settings})
settings.JINJA_FILTERS.update({'json': lambda x: json.dumps(x, indent=2), 'autohttps': autohttps})

_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')


@evalcontextfilter
def nl2br(eval_ctx, value):
  result = u'\n\n'.join(u'<p>%s</p>' % p.replace('\n', '<br>\n')
                        for p in _paragraph_re.split(escape(value)))
  if eval_ctx.autoescape:
    result = Markup(result)
  return result


@evalcontextfilter
def keywords(eval_ctx, value):
  return ','.join(unicode(value).lower().split(' '))

settings.JINJA_FILTERS['nl2br'] = nl2br
settings.JINJA_FILTERS['keywords'] = keywords
