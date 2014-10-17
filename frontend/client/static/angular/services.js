/*global angular, window, console, jQuery, $, document*/'use strict';

angular.module('app')
.factory('errorHandling', function ($modal) {
  var translations = {
    'action_denied' : function (reason)
    {
      return 'You do not have permission to perform this action.';
    },
    'invalid_model' : 'You have requested access to resource that does not exist',
    'invalid_action' : 'You have requested access to the action that does not exist',
    'required' : function (fields) {
      return 'Some values are missing: ' + fields.join(', '); 
     },
    'transaction' : function (reason)
    {
 
      if (reason == 'timeout')
      {
        return 'Transaction was not completed due timeout. Please try again.';
      }
      else if (reason == 'failed')
      {
        return 'Transaction was not completed due failure. Please try again.';
      }
      
    }
  },
    errorHandling = {
    translate : function (k, v)
    {
      var possible = translations[k];
      if (angular.isString(possible))
      {
        return possible;
      }
      else
      {
        return possible(v);
      }
    },
    modal : function (errors)
    {
      $modal.open({
        templateUrl : 'misc/modal_errors.html',
        controller : function ($scope, $modalInstance)
        {
          $scope.errors = [];
          angular.forEach(errors, function (error, key) {
            $scope.errors.push(errorHandling.translate(key, error));
          });
          $scope.ok = function ()
          {
            $modalInstance.dismiss('ok');
            
          };
        }
      })
    }
  }
  
  return errorHandling;
})
.factory('helpers', function() {

  var helpers = {
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
      options = helpers.always_object(options);

      angular.forEach(defaults, function(value, key) {
        if (!( key in options)) {
          options[key] = value;
        }
      });

      return options;
    }
  };

  return helpers;
}).factory('endpoint', function($http, generalLocalCache, GLOBAL_CONFIG, helpers, $rootScope, $q) {

  var _compile = function(action, model, data, config) {
    config = helpers.always_object(config);
    data = helpers.always_object(data);

    return [angular.extend({
      action_model : model,
      action_id : action
    }, data), config];

  }, cache_prefix = 'endpoint_';

  var endpoint = {
    invalidate_cache : function(key) {
      return generalLocalCache.remove(cache_prefix + key);
    },
    url : GLOBAL_CONFIG.api_endpoint_path,
    cached : function(key, action, model, data, config) {
      var cache_key = cache_prefix + key, exists = generalLocalCache.get(cache_key), is_promise = exists && angular.isFunction(exists.then);
      if (is_promise) {
        return is_promise;
      } else if (exists === undefined) {
        var promise = endpoint[config.method ? config.method.toLowerCase() : 'post'](action, model, data, config);
        promise.then(function(response) {
          generalLocalCache.put(cache_key, response);
        }, function() {
          generalLocalCache.remove(cache_key);
        });
        generalLocalCache.put(cache_key, promise);
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
        url : endpoint.url
      };
      if (compiled[1] && angular.isString(compiled[1].cache)) {
        var cache_id = compiled[1].cache;
        compiled[1].cache = false;
        // avoid recursion
        return endpoint.cached(cache_id, action, model, data, compiled[1]);
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
        url : endpoint.url
      };
      helpers.update(gets, compiled[1]);
      angular.extend(defaults, gets);
      if (defaults && angular.isString(defaults.cache)) {
        var cache_id = defaults.cache;
        defaults.cache = false;
        return endpoint.cached(cache_id, action, model, data, gets);
      }
      return $http(defaults);
    },
    current_account : function() {
      return endpoint.post('current_account', '11', {}, {
        cache : 'current_account'
      }).then(function(response) {

        angular.module('app').value('current_account', response.data.entity);

      });
    },
    model_meta : function() {
      return endpoint.get(null, null, {}, {
        cache : 'model_meta',
        url : GLOBAL_CONFIG.api_model_meta_path
      }).then(function(response) {
        angular.module('app').value('model_info', response.data);
      });
    }
  };

  return endpoint;

}).factory('generalLocalCache', function(DSCacheFactory, $cacheFactory) {
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
  var generalLocalCache = DSCacheFactory('generalCache', {
    storageMode : 'localStorage',
    storageImpl : localStoragePolyfill
  });

  generalLocalCache.inMemory = function(value) {
    var only_in_memory = {}
    only_in_memory[memory_only] = value;
    return only_in_memory;
  };

  return generalLocalCache;

}).run(function($http, generalLocalCache) {

  $http.defaults.cache = generalLocalCache;

}).factory('modelMeta', function(model_info) {

  var modelMeta = {};

  modelMeta.friendly_action_name = function(kind, action_key) {

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

  modelMeta.get = function(kind_id) {

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

  return modelMeta;

}).factory('ruleEngine', function(modelMeta) {

  var ruleEngine = {
    run : function(entity) {
      var actions = {}, inputs = {}, kind_info = modelMeta.get(entity.kind);
      var rule_action_permissions = entity._action_permissions;
      if (rule_action_permissions === undefined) {
        return undefined;
        // if the permissions are not present, there is no rule engine here...
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

  return ruleEngine;
}).factory('entityUtil', function(modelMeta, ruleEngine) {
  // Service used for entity based operations
  var dont_send = ['_field_permissions', '_action_permissions', 'ui'], entityUtil = {
    normalizeMultiple : function(entities) {
      angular.forEach(entities, function(entity, i) {
        entities[i] = entityUtil.normalize(entity);
      });
    },
    normalize : function(entity, fields, parent, subentity_field_key, subentity_position) {
      var info = modelMeta.get(entity.kind);
      if (fields !== undefined) {
        info.fields = fields;
      }

      angular.forEach(info.fields, function(field, field_key) {
        var defaults = field['default'], value = entity[field_key];
        if (field.type == 'SuperDateTimeProperty' && !defaults) {
          defaults = new Date();

        }
        if (field.repeated && !angular.isArray(defaults)) {
          defaults = [];
        }

        if ((value === undefined || value == null)) {
          if ((defaults !== null && defaults !== undefined)) {
            entity[field_key] = defaults;
          }

        } else {
          if (field.is_structured) {
            angular.forEach((field.repeated ? value : [value]), function(subentity, i) {
              entityUtil.normalize(subentity, field.modelclass, entity, field_key, i);
            });
          }
        }
        
        });
         
        entity.toJSON = function() {
          var copy = {};
          angular.forEach(this, function(value, key) {
            if ($.inArray(key, dont_send) === -1) {
              copy[key] = value;
            }
          });
          return copy;
        };

        entity.ui = {};
        entity.ui.access = [];
        if (subentity_field_key)
        {
          entity.ui.access.extend(parent.ui.access);
          entity.ui.access.push(subentity_field_key);
          entity.ui.access.push(subentity_position);
        }
        entity.ui.parent = parent;
        entity.ui.root_access = function ()
        {
     
            return this.access.join('.');
        };
        entity.ui.root = function (collect)
        {
          var get_parent = this.parent;
          
          if (get_parent === undefined)
          {
            if (collect)
            {
              collect.push(entity);
            }
            return entity;
          }
          else
          {
            
            if (collect)
            {
                  collect.push(entity);
            }
           
            while(true)
            {
              if (collect)
              {
                  collect.push(get_parent);
              }
                
              var next_parent = get_parent.ui.parent;
              if (next_parent === undefined)
              {
                break;
              }
              else
              { 
                get_parent = next_parent;
              }
            }
            
            return get_parent;
          }
        };
        /// ui must be now reserved keyword in datastore and we use it for making ui related functions
        if (parent == undefined)
        {
          entity.ui.rule = ruleEngine.run(entity);
        }
        else if (parent.ui.rule)
        {
          entity.ui.rule = parent.ui.rule[subentity_field_key];
        }

     
    }
  };

  return entityUtil;
}).factory('underscoreTemplate', function() {

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
