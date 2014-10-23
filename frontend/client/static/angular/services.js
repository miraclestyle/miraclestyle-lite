/*global angular, window, console, jQuery, $, document*/'use strict';

angular.module('app').factory('errorHandling', function($modal) {
  var translations = {
    'action_denied' : function(reason) {
      return 'You do not have permission to perform this action.';
    },
    'invalid_model' : 'You have requested access to resource that does not exist',
    'invalid_action' : 'You have requested access to the action that does not exist',
    'required' : function(fields) {
      return 'Some values are missing: ' + fields.join(', ');
    },
    'transaction' : function(reason) {

      if (reason == 'timeout') {
        return 'Transaction was not completed due timeout. Please try again.';
      } else if (reason == 'failed') {
        return 'Transaction was not completed due failure. Please try again.';
      }

    }
  }, errorHandling = {
    translate : function(k, v) {
      var possible = translations[k];
      if (angular.isString(possible)) {
        return possible;
      } else {
        return possible(v);
      }
    },
    modal : function(errors) {
      $modal.open({
        templateUrl : 'misc/modal_errors.html',
        controller : function($scope, $modalInstance) {
          $scope.errors = [];
          angular.forEach(errors, function(error, key) {
            $scope.errors.push(errorHandling.translate(key, error));
          });
          $scope.ok = function() {
            $modalInstance.dismiss('ok');

          };
        }
      })
    }
  }

  return errorHandling;
}).factory('helpers', function() {

  var helpers = {
    always_object : function(obj) {
      if (!angular.isObject(obj)) {
        return {};
      }
      return obj;
    },
    addslashes : function(str) {
 
      return (str + '')
        .replace(/[\\"']/g, '\\$&')
        .replace(/\u0000/g, '\\0');
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
}).factory('endpoint', function($http, generalLocalCache, GLOBAL_CONFIG, helpers, $rootScope, $q, $cacheFactory) {

  var onlyInMemoryCache = $cacheFactory('endpointOnlyInMemory'), getCache = function(type) {
    if (type === undefined) {
      return generalLocalCache;
    } else if (type === 'memory') {
      return onlyInMemoryCache;
    } else {
      console.error('Invalid type of cache provided: ' + type);
    }
  }, _compile = function(action, model, data, config) {
    config = helpers.always_object(config);
    data = helpers.always_object(data);

    return [angular.extend({
      action_model : model,
      action_id : action
    }, data), config];

  }, cache_prefix = 'endpoint_', cacheRegistry = [];

  cacheRegistry.push(onlyInMemoryCache);
  cacheRegistry.push(generalLocalCache);

  var endpoint = {
    // invalidates all caches that we use
    invalidate_cache : function(key) {
      if (angular.isArray(key)) {
        angular.forEach(key, function(k) {
          endpoint.invalidate_cache(k);
        });

        return true;
      } else {
        angular.forEach(cacheRegistry, function(cache) {
          cache.remove(cache_prefix + key);
        });
      }

    },
    url : GLOBAL_CONFIG.apiEndpointPath,
    cached : function(key, action, model, data, config) {
      var cacheEngine = getCache( config ? config.cacheType : undefined), cache_key = cache_prefix + key, exists = cacheEngine.get(cache_key), is_promise = exists && angular.isFunction(exists.then);
      if (is_promise) {
        return is_promise;
      } else if (exists === undefined) {
        var promise = endpoint[config.method ? config.method.toLowerCase() : 'post'](action, model, data, config);
        promise.then(function(response) {
          cacheEngine.put(cache_key, response);
        }, function() {
          cacheEngine.remove(cache_key);
        });
        cacheEngine.put(cache_key, promise);
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
        cache : 'current_account',
        cacheType : 'memory'
      }).then(function(response) {

        angular.module('app').value('current_account', response.data.entity);

      });
    },
    model_meta : function() {
      return endpoint.get(null, null, {}, {
        cache : 'model_meta',
        url : GLOBAL_CONFIG.apiModelMetaPath
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
      angular.forEach(action.arguments, function(arg, key) {
        if (arg.code_name === null || arg.name === null) {
          // fixup codename
          arg.code_name = key;
        }
      });
    });

    var data = {
      'actions' : kind._actions,
      'mapped_actions' : actions,
      'fields' : fields
    };

    return data;
  };

  // expose this to global intentionally, this is used mostly for console debugging @todo remove in production
  window.modelMeta = modelMeta;

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
  var dont_send = ['_field_permissions', '_action_permissions'], entityUtil = {
    normalizeMultiple : function(entities) {
      angular.forEach(entities, function(entity, i) {
        entities[i] = entityUtil.normalize(entity);
      });
    },
    normalize : function(entity, fields, parent, subentity_field_key, subentity_position) {
      if (entity.ui && entity.ui.normalized) {
        return;
      }
      var info = modelMeta.get(entity.kind);
      if (fields !== undefined) {
        info.fields = fields;
      }

      entity.toJSON = function() {
        var copy = {};
        angular.forEach(this, function(value, key) {
          if ($.inArray(key, dont_send) === -1) {
            copy[key] = value;
          }
        });
        if (copy.ui && copy.ui.parent) {
          delete copy.ui.parent;
        }

        return copy;
      };

      entity.ui = {};
      entity.ui.normalized = true;
      entity.ui.access = [];
      if (subentity_field_key) {
        entity.ui.access.extend(parent.ui.access);
        entity.ui.access.push(subentity_field_key);
        if (subentity_position !== undefined)
        {
          entity.ui.access.push(subentity_position);
        }
        
      }
      entity.ui.parent = parent;
      entity.ui.root_access = function() {

        return this.access.join('.');
      };
      entity.ui.root = function(collect) {
        var get_parent = this.parent;

        if (get_parent === undefined) {
          if (collect) {
            collect.push(entity);
          }
          return entity;
        } else {

          if (collect) {
            collect.push(entity);
          }

          while (true) {
            if (collect) {
              collect.push(get_parent);
            }

            var next_parent = get_parent.ui.parent;
            if (next_parent === undefined) {
              break;
            } else {
              get_parent = next_parent;
            }
          }

          return get_parent;
        }
      };
      /// ui must be now reserved keyword in datastore and we use it for making ui related functions
      if (parent == undefined) {
        entity.ui.rule = ruleEngine.run(entity);
      } else if (parent.ui.rule) {
        entity.ui.rule = {};
        entity.ui.rule.input = parent.ui.rule.input;
        entity.ui.rule.action = parent.ui.rule.action;
        entity.ui.rule.field = parent.ui.rule.field[subentity_field_key];
      }

      angular.forEach(info.fields, function(field, field_key) {
        var defaults = field['default'], value = entity[field_key];
        if (field.type == 'SuperDateTimeProperty' && !defaults) {
          defaults = new Date();

        }
        if (field.repeated && !angular.isArray(defaults)) {
          defaults = [];
        }

        if ((value === undefined || value === null)) {
          if ((defaults !== null && defaults !== undefined)) {
            entity[field_key] = defaults;
          }
        }
        if (field.is_structured) {
          if (field.repeated) {
            angular.forEach(value, function(subentity, i) {
              entityUtil.normalize(subentity, field.modelclass, entity, field_key, i);
            });
          } else {

            if ((value === undefined || value === null)) {
                value = {
                  kind : field.modelclass_kind
                };
                entity[field_key] = value;
              }
           
              entityUtil.normalize(value, field.modelclass, entity, field_key);

            }
          }
   
      });

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
}).config(['$httpProvider',
function($httpProvider) {

  $httpProvider.interceptors.push(['$rootScope', '$q', '$injector',
  function($rootScope, $q, $injector) {

    var handle_error = function(rejection) {

      var data = rejection.data;
      var errorHandling = $injector.get('errorHandling');

      if (!rejection.config.ignoreErrors) {

        if (rejection.status > 200) {
          errorHandling.modal(rejection.data.errors);
          //return $q.reject(rejection);
        } else {
          if (data && data.errors) {
            errorHandling.modal(rejection.data.errors);
            var reject = (rejection.config.rejectOnErrors === undefined || rejection.config.rejectOnErrors === true);
            if (data.errors.action_denied) {
              reject = true;
            }
            if (reject) {
              return $q.reject(rejection);
            }

          }
        }

      }
      // otherwise, default behaviour
      return rejection || $q.when(rejection);

    };

    return {
      response : handle_error,
      responseError : handle_error
    };
  }]);

}]).factory('entityManager', function($modal, endpoint, $q, helpers, entityUtil, errorHandling, modelMeta, $timeout) {

  var entityManager = {
    create : function(new_config) {

      var config = {
        showCancel : true,
        closeAfterSave : false,
        action : 'update',
        excludeFields : [],
        templateBodyUrl : 'entity/modal_editor_default_body.html',
        templateFooterUrl : 'entity/modal_editor_default_footer.html',
        scope : {},
        init : function() {
        },
        defaultInit : function($scope) {
          var cfg = $scope.config;
          if (!cfg.fields) {
            cfg.fields = [];
            var info = modelMeta.get($scope.entity.kind);
            angular.forEach(info.fields, function(prop, prop_key) {
              cfg.fields.push(prop);
            });
          }

          cfg.keyedFields = {};
          angular.forEach(cfg.fields, function(field) {
            cfg.keyedFields[field.code_name] = field;
          });

        },
        actions : [],
        defaultActions : [],
        defaultArgumentLoader : function($scope) {
          // by default argument loader will attempt to extract the argument data from the current entity
          var entityCopy = angular.copy($scope.entity), info = modelMeta.get($scope.config.kind), args = {};

          angular.forEach(info.mapped_actions[$scope.config.action].arguments, function(arg, arg_key) {
            var val = entityCopy[arg_key];
            if (val === undefined) {
              val = arg['default'];
            }
            if (val !== undefined) {
              // arg can never be "undefined"
              args[arg_key] = val;
            }

          });
 
          return args;
        },
        argumentLoader : function($scope) {
          var cfg = $scope.config;
          return cfg.defaultArgumentLoader($scope);
        }
      };

      $.extend(true, config, new_config);

      if (config.fields === undefined && config.kind !== undefined && config.action !== undefined) {
        config.fields = [];
        var kind = config.kind, info = modelMeta.get(kind);
        angular.forEach(info.mapped_actions[config.action].arguments, function(prop, prop_key) {
          if ($.inArray(prop_key, config.excludeFields) === -1) {
            config.fields.push(prop);
          }
        });

      }

      console.log('entityManager.config', config);

      var entityManagerInstance = {
        read : function(entity, args) {
          if (args === undefined) {
            args = {
              key : entity.key
            };
          }
          var that = this;
          
          endpoint.post('read', config.kind, args).then(function(response) {
            helpers.update(entity, response.data.entity);
            that.open(response.data.entity, args);
          });
        },
        prepare : function(entity, args) {
          var that = this;
          endpoint.post('prepare', entity.kind, args).then(function(response) {
            helpers.update(entity, response.data.entity);
            that.open(response.data.entity, args);
          });
        },
        open : function(entity, args) {

          $modal.open({
            templateUrl : 'entity/modal_editor.html',
            controller : function($scope, $modalInstance) {
              entityUtil.normalize(entity);
              $scope.container = {
                action : endpoint.url
              };

              $scope.config = config;
              $scope.entity = entity;
              $scope.$modalInstance = $modalInstance;
              // load into scope from config
              helpers.update($scope, config.scope);
              // call config constructor, needed for posible on-spot configurations
              config.defaultInit($scope);
              config.init($scope);

              $scope.args = config.argumentLoader($scope);
              // argument loader to load arguments for editing
              $scope.args['action_id'] = config.action;
              $scope.args['action_model'] = config.kind;
              
              if (args !== undefined)
              {
                helpers.update($scope.args, args);
              }
 
              console.log('entityManager.init', $scope);

              $scope.complete = function(response) {
                 
                entityUtil.normalize(response.entity);
                helpers.update($scope.entity, response.entity);
                
                var new_args = config.argumentLoader($scope);
 
                helpers.update($scope.args, new_args);
         
                if (config.closeAfterSave) {
                    $timeout(function () {
                      $scope.close();
                    });
                 }
                 
                console.log('entityManager.complete', $scope);
                
              };

              $scope.close = function() {
                $modalInstance.dismiss('close');
              };

              console.log('entityManager.scope', $scope);

            }
          });

          return this;
        },
      };

      return entityManagerInstance;

    }
  };

  return entityManager;

});
