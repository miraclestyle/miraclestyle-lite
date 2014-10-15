/*global angular, window, console, jQuery, $, document*/'use strict';

angular.module('app').factory('Helpers', function() {

  var Helpers = {
    always_object : function(obj) {
      if (!angular.isObject(obj)) {
        return {};
      }
      return obj;
    },
    update : function() {

      /**
       * Overrides dict1 with dict2, dict3 etc.
       * update(dict1, dict2, dict3...)
       */
      var objects = [];
      angular.forEach(arguments, function(value) {
        objects.push(value);
      });

      var target = objects.pop();

      angular.forEach(objects, function(obj) {
        angular.forEach(target, function(new_value, key) {
          obj[key] = new_value;
        });
      });

      return objects;
    },
    resolve_defaults : function(defaults, options) {
      options = Helpers.always_object(options);

      angular.forEach(defaults, function(value, key) {
        if (!( key in options)) {
          options[key] = value;
        }
      });

      return options;
    }
  };

  return Helpers;
}).factory('Endpoint', function($http, GeneralLocalCache, GLOBAL_CONFIG, Helpers, $rootScope, $q) {

  var _compile = function(action, model, data, config) {
    config = Helpers.always_object(config);
    data = Helpers.always_object(data);

    return [angular.extend({
      action_model : model,
      action_id : action
    }, data), config];

  }, cache_prefix = 'endpoint_';

  var Endpoint = {
    invalidate_cache : function(key) {
      return GeneralLocalCache.remove(cache_prefix + key);
    },
    url : GLOBAL_CONFIG.api_endpoint_path,
    cached : function(key, action, model, data, config) {
      var cache_key = cache_prefix + key, exists = GeneralLocalCache.get(cache_key), is_promise = exists && angular.isFunction(exists.then);
      if (is_promise) {
        return is_promise;
      } else if (exists === undefined) {
        var promise = Endpoint[config.method ? config.method.toLowerCase() : 'post'](action, model, data, config);
        promise.then(function(response) {
          GeneralLocalCache.put(cache_key, response);
        }, function() {
          GeneralLocalCache.remove(cache_key);
        });
        GeneralLocalCache.put(cache_key, promise);
        return promise;
      } else {
        var deffered = $q.defer(), promise = deffered.promise;
        deffered.resolve(exists);
        return promise;
      }

    },
    post : function(action, model, data, config) {
      var compiled = _compile(action, model, data, config), defaults = {
        method : 'POST',
        url : Endpoint.url
      };
      if (compiled[1] && angular.isString(compiled[1].cache)) {
        var cache_id = compiled[1].cache;
        compiled[1].cache = false;
        // avoid recursion
        return Endpoint.cached(cache_id, action, model, data, compiled[1]);
      }
      angular.extend(defaults, compiled[1]);
      defaults['data'] = compiled[0];
      return $http(defaults);
    },
    get : function(action, model, data, config) {
      var compiled = _compile(action, model, data, config), gets = {
        params : compiled[0]
      }, defaults = {
        method : 'GET',
        url : Endpoint.url
      };
      Helpers.update(gets, compiled[1]);
      angular.extend(defaults, gets);
      if (defaults && angular.isString(defaults.cache)) {
        var cache_id = defaults.cache;
        defaults.cache = false;
        return Endpoint.cached(cache_id, action, model, data, gets);
      }
      return $http(defaults);
    },
    current_account : function() {
      return Endpoint.post('current_account', '11', {}, {
        cache : 'current_account'
      }).then(function(response) {

        angular.module('app').value('current_account', response.data.entity);

      });
    },
    model_meta : function() {
      return Endpoint.get(null, null, {}, {
        cache : 'model_meta',
        url : GLOBAL_CONFIG.api_model_meta_path
      }).then(function(response) {
        angular.module('app').value('model_info', response.data);
      });
    }
  };

  return Endpoint;

}).factory('GeneralLocalCache', function(DSCacheFactory, $cacheFactory) {
  // combination of LocalStorageCache and inMemory cache
  var inMemory = $cacheFactory('localStoragePolyfillInMemory'),
  // in memory cache for non-serizible jsons
  nothing = '___undefined___', memory_only = '___in_memory_only___';

  function prepare(key, val) {
    if (val && ((val.value && angular.isFunction(val.value.then)) || (angular.isObject(val.value) && val.value[memory_only] !== undefined))) {
      return nothing;
    }
    return angular.toJson(val);
  }

  var localStoragePolyfill = {
    getItem : function(key) {
      var out = inMemory.get(key);
      if (out && angular.isObject(out) && out[memory_only] !== undefined) {
        out = out[memory_only];
      }
      if (out === undefined) {
        // this done to prevent constant json deserializations / serializations
        out = localStorage.getItem(key);
      }
      if (out !== nothing) {
        return out;
      } else {
        return undefined;
      }
      return out;
    },
    setItem : function(key, value) {
      inMemory.put(key, value);
      value = prepare(key, value);
      return localStorage.setItem(key, value);
    },
    removeItem : function(key) {
      inMemory.remove(key);
      return localStorage.removeItem(key);
    }
  };
  var GeneralLocalCache = DSCacheFactory('generalCache', {
    storageMode : 'localStorage',
    storageImpl : localStoragePolyfill
  });

  GeneralLocalCache.in_memory = function(value) {
    var only_in_memory = {}
    only_in_memory[memory_only] = value;
    return only_in_memory;
  };

  return GeneralLocalCache;

}).run(function($http, GeneralLocalCache) {

  $http.defaults.cache = GeneralLocalCache;

}).factory('ModelMeta', function(model_info) {

  var ModelMeta = {};

  ModelMeta.friendly_action_name = function(kind, action_key) {

    var info = this.get(kind);
    if (info === undefined) {
      return undefined;
    }

    var actions = info.actions, friendly_action_name;

    angular.forEach(actions, function(action) {
      if (action.key === action_key) {
        friendly_action_name = action.id;
      }
    });

    return friendly_action_name;
  };

  ModelMeta.get = function(kind_id) {

    var kind = model_info[kind_id], fields = {}, actions = {};
    if (kind === undefined) {
      return undefined;
    }

    angular.forEach(kind, function(value, key) {
      if (key !== '_actions') {
        fields[key] = value;
      }
    });

    angular.forEach(kind._actions, function(action) {
      actions[action.id] = action;
    });

    var data = {
      'actions' : kind._actions,
      'mapped_actions' : actions,
      'fields' : fields
    };

    return data;
  };

  return ModelMeta;

}).factory('RuleEngine', function(ModelMeta) {
 
  var RuleEngine = {
    run : function(entity) {
      var actions = {}, inputs = {}, kind_info = ModelMeta.get(entity.kind);
      var rule_action_permissions = entity._action_permissions;
      if (rule_action_permissions === undefined)
      {
        return undefined; // if the permissions are not present, there is no rule engine here...
      }
      var rule_field_permissions = entity._field_permissions, rule_actions = kind_info.actions, config = {
        action : actions,
        input : inputs,
        field : rule_field_permissions
      }, action_permission_translate = function(action_name) {
        return rule_action_permissions[rule_actions[action_name]['key']];
      }, check_field = function(name, what) {
        return rule_field_permissions[name][what];
      }, executable = function(action_name) {
        var gets = action_permission_translate(action_name);
        return gets['executable'];
      };

      angular.forEach(rule_actions, function(value, key) {

        if (!config.action[value.id]) {
          config.action[value.id] = {};
        }
        config.action[value.id]['executable'] = executable(key);

        angular.forEach(value.arguments, function(argument_value, argument_key) {
          if (!config.input[value.id]) {
            config.input[value.id] = {};
          }
          config.input[value.id][argument_key] = argument_value;
        });

      });

      return config;
    }
  };

  return RuleEngine;
}).factory('Entity', function(ModelMeta, RuleEngine) {
  // Service used for entity based operations
  var Entity = {
    normalizeMultiple : function(entities) {
      angular.forEach(entities, function(entity, i) {
        entities[i] = Entity.normalize(entity);
      });
    },
    normalize : function(entity) {
      var info = ModelMeta.get(entity.kind);
      angular.forEach(info.fields, function(field, field_key) {
        var defaults = field['default'],
            value = entity[field_key];
        if (field.repeated && !angular.isArray(defaults)) {
          defaults = [];
        }
         
        if ((value === undefined || value == null)) {
          if ((defaults !== null && defaults !== undefined)) {
            entity[field_key] = defaults;
          }

        } else {
          if (field.is_structured) {
            angular.forEach((field.repeated ? value : [value]), function(subentity) {
              Entity.normalize(subentity);
            });
          }
        }
        entity.ui = {}; /// ui must be now reserved keyword in datastore
        entity.ui.rule = RuleEngine.run(entity); // rule engine must present
        // more stuff, rule engine etc
        entity.ui.toJSON = function() {
          return entity; // we must strip away uneeded properties here
        };
 

      });
    }
  };

  return Entity;
}).factory('UnderscoreTemplate', function() {

  return {
    get : function(path, typecheck) {
      if (typecheck) {
        typecheck = '[type="text/underscore-template"]';
      } else {
        typecheck = '';
      }
      var find = $('script[id="' + path + '"]' + typecheck), contents = find.text();
      if (!find.length) {
        console.error('underscore ' + typecheck + ' template not found ' + path);
      }
      return _.template(contents);
    }
  };
});
