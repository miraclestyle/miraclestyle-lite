'''
account:
    account:
        read
            -owner
            -admin
        search:
            -admin

buyer:
    buyer:
        read
            -owner

catalog:
    catalog:
        search:
            -owner
            -admin
            -guest
            -non owner
        read
            -owner
            -admin
            -guest
            -non owner
    categories:
        search:
            -auth

order:
    order:
        read
            -owner
            -seller
            -admin
        search:
            -owner
            -seller
            -admin

seller:
    seller:
        read
            -owner
            -auth
            -guest

unit:
    unit:
        read
        search
            -all



'''
class BaseCache(orm.BaseModel):

    cfg = orm.SuperJsonProperty('1', indexed=False, required=True, default={})

    def run(self, context):
        Cache = context.models['Cache']
        cache_driver = self.cfg.get('cache', [])
        dcache_driver = self.cfg.get('dcache', [])
        cache_drivers = []
        user = 'account' in cache_driver
        if not context.account._is_guest:
            if user and not context.account._is_guest:
                cache_drivers.append(context.account.key_id_str)
            if 'auth' in cache_drivers and :
                cache_drivers.append('auth')
        elif 'guest' in cache_drivers:
            cache_drivers.append('guest')
        for d in dcache_driver:
            cache_drivers.append(tools.get_attr(d))
        cache_drivers = set(cache_drivers)
        key = self.cfg.get('key')
        if not key:
            key = context.cache_key
        data = None
        def do_save(data):
            queue = {}
            for driver in cache_drivers:
                queue['%s_%s' % (driver, key)] = data
            tools.mem_set_multi(queue)
        saver = {'do_save': do_save}
        if self.getter:
            for driver in cache_drivers:
                data = tools.mem_get('%s_%s' % (driver, key))
                if data:
                    break
            if data:
                context.cache = {'value': data}
                raise orm.TerminateAction()
        context.cache = saver

class GetCache(BaseCache):

    getter = True


class WriteCache(BaseCache):

    getter = False


class Account():

    ...

  orm.Action(
      id='read',
      arguments={
          'key': orm.SuperKeyProperty(kind='11', required=True),
          'read_arguments': orm.SuperJsonProperty()
      },
      _plugin_groups=[
          orm.PluginGroup(
              plugins=[
                  Context(),
                  GetCache(),
                  Read(),
                  RulePrepare(),
                  RuleExec(),
                  Set(cfg={'d': {'output.entity': '_account'}})
              ]
          )
      ]
  ),
  orm.Action(
      id='update',
      arguments={
          'key': orm.SuperKeyProperty(kind='11', required=True),
          'primary_identity': orm.SuperStringProperty(),
          'disassociate': orm.SuperStringProperty(repeated=True),
          'read_arguments': orm.SuperJsonProperty()
      },
      _plugin_groups=[
          orm.PluginGroup(
              plugins=[
                  Context(),
                  Read(),
                  AccountUpdateSet(),
                  RulePrepare(),
                  RuleExec()
              ]
          ),
          orm.PluginGroup(
              transactional=True,
              plugins=[
                  Write(),
                  WriteCache(),
                  Set(cfg={'d': {'output.entity': '_account'}}),
                  CallbackExec(cfg=[('callback',
                                     {'action_id': 'account_discontinue', 'action_model': '31'},
                                     {'account': '_account.key_urlsafe', 'account_state': '_account.state'},
                                     lambda account, account_state, **kwargs: account_state == 'suspended')])
              ]
          )
      ]
  ),