app.factory('Helpers', [
function() {

    return {

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
            options = always_object(options);

            angular.forEach(defaults, function(value, key) {
                if (!( key in options)) {
                    options[key] = value;
                }
            });

            return options;
        }
    };
}]).factory('Endpoint', ['$http', 'DSCacheFactory', '$cacheFactory', 'GLOBAL_CONFIG', 'Helpers',

function($http, DSCacheFactory, $cacheFactory, GLOBAL_CONFIG, Helpers) {

    var cache = DSCacheFactory('endpoint_local_storage', {
        storageMode : 'localStorage'
    });

    var in_memory = $cacheFactory('endpoint_in_memory');

    var _compile = function(action, model, data, config) {
        config = Helpers.always_object(config);
        data = Helpers.always_object(data);

        return [angular.extend({
            action_model : model,
            action_id : action,
        }, data), config];

    };

    return {
        invalidate_cache : function(key) {
            return cache.remove(key);
        },
        url : GLOBAL_CONFIG.api_endpoint_path,
        cached : function(key, action, model, data, success, error, config) {

            var loading_key = key + '_loading';
            var callbacks_key = loading_key + '_success_callbacks';
            var callbacks = in_memory.get(callbacks_key);
            var loading = in_memory.get(loading_key);
            var cached = cache.get(key);

            if (cached === undefined) {
                if (loading !== true) {
                    in_memory.put(loading_key, true);
                    return this.post(action, model, data, config).success(function(response) {
                        cache.put(key, response);
                        try {
                            success.call(this, response);

                        } catch(e) {
                            console.log(e);
                        }
                        in_memory.put(loading_key, undefined);
                        if (callbacks !== undefined) {
                            var that = this;
                            angular.forEach(callbacks, function(cb) {
                                cb.call(that, response);
                            });

                            in_memory.set(callbacks_key, undefined);

                        }
                    }).error(function() {
                        in_memory.put(loading_key, undefined);
                        in_memory.set(callbacks_key, undefined);
                        if (angular.isFunction(error)) {
                            error.call(this);
                        }
                    });

                } else {
                    if (callbacks === undefined) {
                        callbacks = [];
                    }

                    callbacks.push(success);

                    in_memory.set(callbacks_key, callbacks);
                }

            } else {
                success(cached);
            }

        },
        post : function(action, model, data, config) {
            var compiled = _compile(action, model, data, config);

            return $http.post(this.url, compiled[0], compiled[1]);
        },
        get : function(action, model, data, config) {
            var compiled = _compile(action, model, data, config);
            var gets = {
                params: compiled[0]
            };
            Helpers.update(gets, compiled[1]);
        
            return $http.get(this.url, gets);
        },
        current_account: function() {
            return this.get('current_account', '11', {}, {
                cache : true
            });
        },
        model_meta: function() {
            return $http.get(GLOBAL_CONFIG.api_model_meta_path, {
                cache : true
            });
        }
    };
}])
.factory('localStoragePolyfill', [function () {
    var in_memory = {}; // in memory cache for non-serizible jsons
    var nothing = '____undefined____';
    function prepare(key, val)
    {
        if (val && val.value && angular.isFunction(val.value.then))
        { 
            in_memory[key] = val;
            return nothing;
        }
        
        return angular.toJson(val);
    }
    
    return {
        getItem: function (key) {
            var out = localStorage.getItem(key);
            if (out !== nothing)
            {
                return out;
            }
            return in_memory[key];
        },
        setItem: function (key, value) {
            value = prepare(key, value);
            return localStorage.setItem(key, value);
        },
        removeItem: function (key) {
            if (key in in_memory)
            {
                delete in_memory[key];
            }
            return localStorage.removeItem(key);
        }
    };
}])
.run(['$http', 'DSCacheFactory', 'localStoragePolyfill',
function($http, DSCacheFactory, localStoragePolyfill) {
  
    $http.defaults.cache = DSCacheFactory('defaultCache', {
        storageMode: 'localStorage',
        storageImpl: localStoragePolyfill
    });

}]).factory('Kinds', ['Endpoint',
function(Endpoint) {

    var Kinds = {};

    Kinds.friendly_action_name = function(kind, action_key) {

        var info = this.get(kind);
        if (info === undefined)
            return undefined;
        var actions = info['actions'], friendly_action_name;

        angular.forEach(actions, function(action) {
            if (action['key'] == action_key) {
                friendly_action_name = action['id'];
            }
        });

        return friendly_action_name;
    };

    Kinds.get = function(kind_id) {

        var kind = this.info[kind_id];
        if (kind == undefined)
            return undefined;
        var fields = {};

        angular.forEach(kind, function(value, key) {
            if (key != '_actions') {
                fields[key] = value;
            }
        });

        var actions = {};

        angular.forEach(kind['_actions'], function(action) {
            actions[action.id] = action;
        });

        var data = {
            'actions' : kind['_actions'],
            'mapped_actions' : actions,
            'fields' : fields,
        };

        return data;
    };

    return Endpoint.model_meta().then(function(response) {
        Kinds.info = response.output;
        return Kinds;
    });

}]).run(['Endpoint', 'Kinds',
function(Endpoint, Kinds) {
 
    Endpoint.model_meta();
    Endpoint.current_account();
  
}]);
