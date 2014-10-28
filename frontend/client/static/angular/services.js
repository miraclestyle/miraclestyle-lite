/*global angular, window, console, jQuery, $, document*/'use strict';

angular.module('app').factory('errorHandling', function($modal) {
  var translations = {
    action_denied : function(reason) {
      return 'You do not have permission to perform this action.';
    },
    invalid_model : 'You have requested access to resource that does not exist',
    invalid_action : 'You have requested access to the action that does not exist',
    required : function(fields) {
      return 'Some values are missing: ' + fields.join(', ');
    },
    transaction : function(reason) {

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
      } else if (angular.isFunction(possible)){
        return possible(v);
      }
      return v;
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
    alwaysObject : function(obj) {
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
    fieldSorter : function (prev, next) {
      return parseInt(prev.name) - parseInt(next.name);
    },
    resolveDefaults : function(defaults, options) {
      options = helpers.alwaysObject(options);

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
    config = helpers.alwaysObject(config);
    data = helpers.alwaysObject(data);

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
      defaults.data = compiled[0];
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

  var modelMeta = {},
      standardize = function (fields)
      {
        angular.forEach(fields, function (field, field_key) {
          if (field.ui === undefined)
          {
            field.ui = {};
          }
          if (field.code_name === null)
          {
            field.code_name = field_key;
          }
          if (field.modelclass !== undefined)
          {
            standardize(field.modelclass);
          }
        });
        
      };

  modelMeta.friendlyActionName = function(kind, action_key) {

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
  
  modelMeta.getModelFields = function (kind_id)
  {
    if (!angular.isDefined(kind_id))
    {
      console.error('provided kind id is not acceptable, got: ' + kind_id);
    }
    var info = this.get(kind_id);
    if (!angular.isDefined(info))
    {
      console.error('could not find meta info for kind ' + kind_id);
    }
    var fields = angular.copy(info.fields);
 
    standardize(fields);
       
    return fields;
  };
  
  
  modelMeta.getActionArguments = function (kind_id, action)
  {
    var info = this.get(kind_id);
    if (!angular.isDefined(info))
    {
      return undefined;
    }
    var action = info.mapped_actions[action];
    if (!angular.isDefined(action))
    {
      return undefined;
    }
    var fields = angular.copy(action['arguments']);
 
    standardize(fields);
       
    return fields;
  };
  
  modelMeta.getModelName = function (kind_id)
  {
    var info = this.get(kind_id);
    return info.name;
  };

  modelMeta.get = function(kind_id) {

    var kind = model_info[kind_id], fields = {}, actions = {};
    if (kind === undefined) {
      console.error('no info for kind ' + kind_id);
      return undefined;
    }

    angular.forEach(kind, function(value, key) {
      if (key !== '_actions' && key !== '__name__') {
        fields[key] = value;
      }
    });

    angular.forEach(kind._actions, function(action) {
      actions[action.id] = action;
    });

    var data = {
      'actions' : kind._actions,
      'mapped_actions' : actions,
      'fields' : fields,
      'name' : kind.__name__
    };

    return data;
  };

  // expose this to global intentionally, this is used mostly for console debugging @todo remove in production
  window.modelMeta = modelMeta;

  return modelMeta;

}).factory('ruleEngine', function(modelMeta) {

  var ruleEngine = {
    run : function(entity) {
      var actions = {}, inputs = {}, kind_info = modelMeta.getModelFields(entity.kind);
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

        angular.forEach(value.arguments, function(argument_value) {
          var argument_key = argument_value.code_name;
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
    normalize : function(entity, fields, parent, subentity_field_key, subentity_position, noui) {
      if (entity.ui && entity.ui.normalized) {
        return;
      }
 
      if (fields === undefined) {
        fields = modelMeta.getModelFields(entity.kind);
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
      
      if (noui === undefined)
      {
 

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
      
             
      }

      angular.forEach(fields, function(field) {
        var defaults = field['default'], value = entity[field.code_name];
        if (field.type == 'SuperDateTimeProperty' && !defaults) {
          defaults = new Date();

        }
        if (field.repeated && !angular.isArray(defaults)) {
          defaults = [];
        }

        if ((value === undefined || value === null)) {
          if ((defaults !== null && defaults !== undefined)) {
            entity[field.code_name] = defaults;
          }
        }
        if (field.is_structured) {
          if (field.repeated) {
            angular.forEach(value, function(subentity, i) {
              entityUtil.normalize(subentity, field.modelclass, entity, field.code_name, i);
            });
          } else {

            if ((value === undefined || value === null)) {
                value = {
                  kind : field.modelclass_kind
                };
                entity[field.code_name] = value;
              }
           
              entityUtil.normalize(value, field.modelclass, entity, field.code_name, undefined, noui);

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
        templateBodyUrl : 'entity/modal_editor_default_body.html',
        templateFooterUrl : 'entity/modal_editor_default_footer.html',
        scope : {},
        init : function() {
        },
        defaultInit : function($scope) {
          

        },
        actions : [],
        defaultActions : [],
        defaultArgumentLoader : function($scope) {
          // by default argument loader will attempt to extract the argument data from the current entity
          var entityCopy = angular.copy($scope.entity), actionArguments = modelMeta.getActionArguments($scope.config.kind, $scope.config.action), args = {};

          angular.forEach(actionArguments, function(arg, arg_key) {
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

      if (!angular.isDefined(config.fields) && angular.isDefined(config.kind) && angular.isDefined(config.action)) {
        config.fields = [];
        var actionArguments = modelMeta.getActionArguments(config.kind, config.action);
        
        angular.forEach(actionArguments, function (field) {
          if (angular.isDefined(config.excludeFields) && $.inArray(field.code_name, config.excludeFields) !== -1) {
            return;
          }
          config.fields.push(field);
        });

      }
      
      config.keyedFields = {};
      angular.forEach(config.fields, function(field) {
          config.keyedFields[field.code_name] = field;
      });
      
   
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
            entityUtil.normalize(response.data.entity);
            helpers.update(entity, response.data.entity);
            that.open(response.data.entity, args);
          });
        },
        prepare : function(entity, args) {
          var that = this;
          endpoint.post('prepare', entity.kind, args).then(function(response) {
            entityUtil.normalize(response.data.entity);
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
              $scope.args.action_id = config.action;
              $scope.args.action_model = config.kind;
              
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

}).factory('formInputTypes', function (underscoreTemplate, $timeout, endpoint, modelMeta, $q, $filter, $modal, helpers, $parse, errorHandling) {
  
  
  var inflector = $filter('inflector'), formInputTypes = {
    Custom : function (info)
    {
      if (info.config.init !== undefined)
      info.config.init(info);
      
      return info.config.template;
    },
    SuperStringProperty : function(info) {
      var config = info.config;
      if (config.ui.attrs.type === undefined) {
        config.ui.attrs.type = 'text';
      }
      
      if (config.choices) {
        return 'select';
      }
      
      if (info.config.repeated)
      {
        info.config.ui.attrs['repeated-text'] = '';
        return 'text';
      }
      
      return 'string';
    },
    SuperFloatProperty : function(info) {
      var config = info.config;

      if (config.choices) {
        return 'select';
      }

      if (config.ui.attrs.type === undefined) {
        //config.ui.attrs.type = 'number';
      }
      return this.SuperStringProperty(info);
    },
    SuperIntegerProperty : function(info) {
      var config = info.config;

      if (config.choices) {
        return 'select';
      }
      
      return this.SuperFloatProperty(info);
    },
    SuperDecimalProperty : function(info) {
      var config = info.config;
      if (config.choices) {
        return 'select';
      }
      return this.SuperFloatProperty(info);
    },
    SuperBooleanProperty : function(info) {
      var config = info.config;
      return 'boolean';
    },
    SuperKeyProperty : function(info) {
      var config = info.config, internalConfig = info.config.ui.specifics.internalConfig,
      defaultInternalConfig = {
            search : {
              cache_results : {
                'default' : true,
                '13' : false
              },
              propsFilter_results : {
                'default' : '{name: $select.search}',
                '12' : '{name: $select.search, code: $select.search}'
              },
              view : {
                'default' : function(result) {
                  if (result === undefined) {
                    return '';
                  }
                  return result.name;
                }
              },
              queryfilter : {
                '13' : function (term, info, search_action)
                {
                  var args = info.scope.$eval(info.config.ui.parentArgs);
                  if ((args && args.country))
                  {
                
                    return {
                      search : {
                         ancestor : args.country,
                         filters : [{
                           value : true,
                           field : 'active',
                           operator : '=='
                         }],
                         orders : [{field: 'name', operator: 'asc'}],
                      }
                    };
                  }
                  
                  return false;
                  
                }
              }
            }
          };
      
      if (!angular.isDefined(internalConfig))
      {
        info.config.ui.specifics.internalConfig = defaultInternalConfig;
        internalConfig = defaultInternalConfig;
      }
      else
      {
        $.extend(true, defaultInternalConfig, internalConfig);
        internalConfig = defaultInternalConfig;
        info.config.ui.specifics.internalConfig = internalConfig;
        
      }
      
      if (config.kind)
      {
        
        var propsFilter = internalConfig.search.propsFilter_results[config.kind];
        if (!propsFilter) {
          propsFilter = internalConfig.search.propsFilter_results['default'];
        }
        config.ui.specifics.propsFilter = propsFilter;
        
      }
       

      if (!config.ui.specifics.view) {
        config.ui.specifics.view = function(result) {
          var fn = internalConfig.search.view[config.kind];
          if (!fn) {
            fn = internalConfig.search.view['default'];
          }

          return fn(result);
        };
      }

      if (!angular.isDefined(config.ui.specifics.search) && !angular.isDefined(config.ui.specifics.entities)) {

        var action_search = modelMeta.getActionArguments(config.kind, 'search'), cache_hit, cache_key = 'search_results_' + config.kind, should_cache = false, search_command, skip_search_command = false;

        if (action_search !== undefined) {
          var cache_option = internalConfig.search.cache_results[config.kind];
          if (cache_option !== undefined && cache_option != false) {
            if (angular.isFunction(cache_option))
            {
              cache_key = cache_key + cache_option(info);
            }
            should_cache = cache_key;
          }
          else if (cache_option != false)
          {
            should_cache = internalConfig.search.cache_results['default'];
            if (should_cache === true)
            {
              should_cache = cache_key;
            }
          }
   
          search_command = function(term) {
            var params = action_search.search['default'], fn = internalConfig.search.queryfilter[config.kind], args = {};
            if (angular.isFunction(fn)) {
              args = fn(term, info, action_search);
            } else {
              args = {
                search : params
              };
            }
            if (args === false)
            {
              return false;
            }
            endpoint.post('search', config.kind, args, {
              cache : should_cache
            }).then(function(response) {
              config.ui.specifics.entities = response.data.entities;
            });
          };

          if (config.ui.specifics.entities === undefined && should_cache !== false) {
            search_command();
          }
          
            if (should_cache === false) {
            config.ui.specifics.search = function(term) {
              search_command(term);
            };
          }

        } else {
          console.error('No search action found in kind: ' + config.kind);
        }
   
      

      }
      return 'select_async';
    },

    SuperLocalStructuredProperty : function(info) {
      var config = info.config, fields = [], beforeSave, modelFields, defaultFields, noSpecifics, afterSave, listFields = [];
     
      beforeSave = config.ui.specifics.beforeSave;
      afterSave = config.ui.specifics.afterSave;
      noSpecifics = !angular.isDefined(config.ui.specifics);
      modelFields = modelMeta.getModelFields(config.modelclass_kind);
      
      defaultFields = _.toArray(modelFields);
      defaultFields = defaultFields.sort(helpers.fieldSorter);
      
      if (noSpecifics || !config.ui.specifics.fields)
      { 
        config.ui.specifics.fields = defaultFields;
      }
      
      if (noSpecifics || !config.ui.specifics.listFields)
      {
     
        angular.forEach(defaultFields, function (field) {
          if (!noSpecifics && (config.ui.specifics.excludeListFields && $.inArray(field.code_name, config.ui.specifics.excludeListFields) !== -1))
          {
            return;
          }
          
          listFields.push({
              key : field.code_name,
              generated : true,
              label : (field.ui && field.ui.label ? field.ui.label : inflector(field.code_name, 'humanize'))
            });
        });
  
        if (!noSpecifics && angular.isDefined(config.ui.specifics.onlyListFields))
        {
            var newListFields = [];
            angular.forEach(config.ui.specifics.onlyListFields, function (key) {
              var find = _.findWhere(listFields, {key : key});
              if (find)
              {
                newListFields.push(find);
              }
            });
            
            listFields = newListFields;
        }
        
      }
 
      var defaults = {
        listFields : listFields,
        fields : fields,
        addNewText : 'Add',
        addText : '{{config.ui.specifics.addNewText}}'
      };
  
      // merge defaults into the 
      angular.forEach(defaults, function(value, key) {
        if (config.ui.specifics[key] === undefined) {
          config.ui.specifics[key] = value;
        }
      });
      
      config.ui.specifics.parentArgs = info.scope.$eval(config.ui.args);
      config.ui.specifics.entity = info.scope.$eval(config.ui.model);
 
      
      config.ui.specifics.formBuilder = [];
      angular.forEach(config.ui.specifics.fields, function(field) {
        var copyWritable = angular.copy(config.ui.writable);
        
        if (angular.isArray(copyWritable))
        {
          copyWritable.push((field.ui.writableName ? field.ui.writableName : field.code_name));
        }
        
        field.ui.formName = field.ui.formName + '_' + config.ui.formName;
        field.ui.writable = copyWritable;
        config.ui.specifics.formBuilder.push(field);
      });
      
      if (!config.repeated)
      {
        config.ui.specifics.SingularCtrl = function ($scope)
        { 
          $scope.args = config.ui.specifics.parentArgs;
        };
        
      }
      else
      {
        
        if (config.ui.specifics.remove === undefined)
        {
          config.ui.specifics.remove = function(arg) {
            arg._state = 'deleted';
          };
        }
        
        if (config.ui.specifics.manage === undefined)
        {  
          config.ui.specifics.manage = function(arg) {
     
            $modal.open({
              template : underscoreTemplate.get(config.ui.specifics.templateUrl ? config.ui.specifics.templateUrl : 'underscore/form/modal/structured.html')({
                config : config
              }),
              controller : function($scope, $modalInstance, entityUtil) {
                var is_new = false;
  
                $scope.config = config;
                if (!arg) {
                  arg = {
                    kind : config.modelclass_kind
                  };
                  var length = config.ui.specifics.parentArgs.length;
                  entityUtil.normalize(arg, config.modelclass, 
                                  config.ui.specifics.entity, config.code_name,
                                   length, false);
                  is_new = true;
                }
                $scope.container = {};
                $scope.args = angular.copy(arg); // entity.addreses.0.address
                $scope.parentArgs = config.ui.specifics.parentArgs; // entity.addresses
                $scope.entity = config.ui.specifics.entity;
   
                $scope.cancel = function() {
                  $modalInstance.dismiss('cancel');
                };
  
                $scope.save = function() {
                  
                  if (!$scope.container.form.$valid)
                  {
                    errorHandling.modal({
                      required : ['field']
                    });
                    return;
                  }
                  var promise = null;
                  if (angular.isFunction(config.ui.specifics.beforeSave))
                  {
                    promise = config.ui.specifics.beforeSave($scope, info);
                  }
                  
                  var complete = function ()
                  {
                    var promise = null;
                    
                    if (config.repeated) {
                      if (is_new) {
                        $scope.parentArgs.push($scope.args);
                      } else {
                        helpers.update(arg, $scope.args);
                      }
                    }
                     
                    if (angular.isFunction(config.ui.specifics.afterSave))
                    {
                      promise = config.ui.specifics.afterSave($scope, info);
                    }
                    
                    if (promise && promise.then)
                    {
                      promise.then(function () {
                        $scope.cancel();
                      });
                    }
                    else
                    {
                      $scope.cancel();
                    }
     
                  };
                  
                  if (promise && promise.then)
                  {
                    promise.then(complete);
                  }
                  else
                  {
                    complete();
                  }
                    
                };
  
              }
            });
          };
            
        }
      }
    
      return 'structured';
    },
    SuperStructuredProperty : function(info) {
      return this.SuperLocalStructuredProperty(info);
    },
    SuperRemoteStructuredProperty : function(info) {
      // remote structured is missing here... @todo
      return this.SuperLocalStructuredProperty(info);
    },
    SuperImageLocalStructuredProperty : function(info) {
      info.scope.$on('ngUploadCompleteImageUpload', function ($event, content) {
         if (!content || content.errors)
         {
           errorHandling.modal(content.errors);
         }
         else
         {
           if (info.config.repeated)
           {
             
             var path = info.scope.entity.root_access().split('.');
             path.splice(path.length-1, 1);
             var getter = $parse(path.join('.')),
                 setter = getter.assign;
             
             var list = getter(info.scope.entity.root());
             var new_entities = getter(content.entity);
             list.push(new_entities);
             
           }
           
         }
         
      });
      return 'image';
    },
    SuperTextProperty : function(info) {
      if (info.config.repeated)
      {
        info.config.ui.attrs['repeated-text'] = '';
      }
      return 'text';
    },
    SuperJsonProperty : function(info) {
      info.config.ui.attrs['json-only'] = '';
      return this.SuperTextProperty(info);
    },
    SuperDateTimeProperty : function(info) {
      return 'datetime';
    },
    SuperPluginStorageProperty : function (info)
    {
      var config = info.config,
      kinds = $.map(config.kinds, function (kind_id) {
          var name = modelMeta.getModelName(kind_id);
          return {
            key : kind_id,
            name : name
          };
       }),
      defaultSpecifics = {
        showType : function (kind)
        {
          return _.findWhere(kinds, {key : kind}).name;
        },
        kind : undefined,
        selectKinds : {
          type : 'SuperKeyProperty',
          ui : {
            specifics : {
              entities : kinds
            },
            args : 'info.kind',
            label : 'Configuration',
            attrs : {
              'ng-change' : 'setNewArg()'
            },
            writable : true
          },
          code_name : 'kind'
        },
        remove : function(arg) {
           config.ui.specifics.parentArgs.remove(arg);
        },
        manage : function(arg) {
     
            $modal.open({
              template : underscoreTemplate.get(config.ui.specifics.templateUrl ? config.ui.specifics.templateUrl : 'underscore/form/modal/plugins.html')({
                config : config
              }),
              controller : function($scope, $modalInstance, entityUtil) {
                var is_new = false;
                
                if (!arg)
                {
                  arg = {};
                } 
                $scope.info = {
                  build : true
                };
                $scope.config = config;
                $scope.setNewArg = function ()
                { 
                  if ($scope.info.kind !== 0 && $scope.args.kind != $scope.info.kind)
                  {
                    arg = {
                      kind : $scope.info.kind
                    };
                    var length = config.ui.specifics.parentArgs.length;
                    entityUtil.normalize(arg, undefined, 
                                    config.ui.specifics.entity, config.code_name,
                                     length, false);
                    is_new = true;
                    
                    $scope.args = arg;
                    $scope.getFormBuilder();
                    $scope.info.build = false;
                    
                     $timeout(function () {
                       $scope.info.build = true;
                       $scope.$apply();
                      }, 300);
                    
                  }
                }
             
                $scope.pluginTemplate = 'seller/plugins/default.html';
                $scope.formBuilder = [];
                $scope.getFormBuilder = function ()
                {
                  $scope.formBuilder = [];
                  var kind = $scope.info.kind,
                      settingsFields = config.ui.specifics.fields, fields = modelMeta.getModelFields(kind);
                  fields = _.toArray(fields);
                  fields.sort(helpers.fieldSorter);
                  if (settingsFields)
                  {
                    if (settingsFields[kind])
                    {
                      fields = settingsFields[kind];
                    }
                  }
                  
                  angular.forEach(fields, function(field) {
                    field.ui.formName = 'plugin_' + field.code_name;
                    field.ui.writable = true;
                    $scope.formBuilder.push(field);
                  });
                };
                
                $scope.container = {};
                $scope.args = angular.copy(arg); // entity.addreses.0.address
                $scope.parentArgs = config.ui.specifics.parentArgs; // entity.addresses
                $scope.entity = config.ui.specifics.entity;
                
                if ($scope.args && $scope.args.kind)
                {
                  $scope.info.kind = $scope.args.kind;
                  $scope.getFormBuilder();
             
                }
   
                $scope.cancel = function() {
                  $modalInstance.dismiss('cancel');
                };
  
                $scope.save = function() {
                  
                  if (!$scope.container.form.$valid)
                  { 
                    return;
                  }
                  var promise = null;
                  if (angular.isFunction(config.ui.specifics.beforeSave))
                  {
                    promise = config.ui.specifics.beforeSave($scope, info);
                  }
                  
                  var complete = function ()
                  {
                     var promise = null;
             
                     if (is_new) {
                        $scope.parentArgs.push($scope.args);
                     } else {
                        helpers.update(arg, $scope.args);
                     }
             
                    if (angular.isFunction(config.ui.specifics.afterSave))
                    {
                      promise = config.ui.specifics.afterSave($scope, info);
                    }
                    
                    if (promise && promise.then)
                    {
                      promise.then(function () {
                        $scope.cancel();
                      });
                    }
                    else
                    {
                      $scope.cancel();
                    }
     
                  };
                  
                  if (promise && promise.then)
                  {
                    promise.then(complete);
                  }
                  else
                  {
                    complete();
                  }
                    
                };
  
              }
            });
          }
      };
      
      config.ui.specifics.parentArgs = info.scope.$eval(config.ui.args);
      config.ui.specifics.entity = info.scope.$eval(config.ui.model);
      
      angular.forEach(defaultSpecifics, function (v, k) {
        if (config.ui.specifics[k] == undefined)
        {
          config.ui.specifics[k] = v;
        }
      });
       
      return 'plugins';
    }
  };
  
  return formInputTypes;
  
}).factory('outputTypes', function (dateFilter, GLOBAL_CONFIG, modelMeta) {
  var outputTypes = {
    SuperDateTimeProperty : function (input, field)
    {
       var date = new Date(input);
       return dateFilter(date, GLOBAL_CONFIG.dateFormat);
    }
  };
  
  return outputTypes;
});
