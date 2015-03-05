(function () {
    'use strict';
    angular.module('app').factory('errorHandling',
        function ($modal) {
            var translations = {
                    action_denied: function (reason) {
                        return 'You do not have permission to perform this action.';
                    },
                    not_found: function (fields) {
                        return 'Requested data ' + fields.join(', ') + ' could not be found in database.';
                    },
                    invalid_image_type: 'You have supplied incorrect type of image format.',
                    invalid_model: 'You have requested access to resource that does not exist,',
                    invalid_action: 'You have requested access to the action that does not exist.',
                    required: function (fields) {
                        return 'Some values are missing: ' + fields.join(', ') + '.';
                    },
                    traceback: function (trace) {
                        var parse = $.parseHTML(trace);
                        return $(parse).filter('pre').text();
                    },
                    transaction: function (reason) {
                        if (reason === 'timeout') {
                            return 'Transaction was not completed due timeout. Please try again.';
                        }
                        if (reason === 'failed') {
                            return 'Transaction was not completed due failure. Please try again.';
                        }
                        return reason;
                    }
                },
                errorHandling = {
                    translate: function (k, v) {
                        var possible = translations[k];
                        if (angular.isString(possible)) {
                            return possible;
                        }
                        if (angular.isFunction(possible)) {
                            return possible(v);
                        }
                        return v;
                    },
                    modal: function (errors) {
                        $modal.open({
                            templateUrl: 'core/models/manage.html',
                            controller: function ($scope) {
                                $scope.dialog = {
                                    templateBodyUrl: 'core/misc/errors.html',
                                    toolbar: {
                                        title: 'Error',
                                        hideSave: true
                                    }
                                };
                                $scope.errors = [];
                                angular.forEach(errors, function (error, key) {
                                    $scope.errors.push([key, errorHandling.translate(key, error)]);
                                });
                                $scope.close = function () {
                                    $scope.$close();
                                };
                            }
                        });
                    }
                };

            return errorHandling;
        }).factory('helpers', function (GLOBAL_CONFIG) {

        var helpers = {
            callable: function (fn) {
                if (angular.isFunction(fn)) {
                    return fn;
                }
                return angular.noop;
            },
            alwaysObject: function (obj) {
                if (!angular.isObject(obj)) {
                    return {};
                }
                return obj;
            },
            splitLines: function (val) {
                return val.match(/[^\r\n]+/g);
            },
            addslashes: function (str) {
                return (str.toString()).replace(/[\\"']/g, '\\$&').replace(/\u0000/g, '\\0');
            },
            resolveDefaults: function (defaults, options) {
                options = helpers.alwaysObject(options);

                angular.forEach(defaults, function (value, key) {
                    if (!angular.isUndefined(options[key])) {
                        options[key] = value;
                    }
                });

                return options;
            },
            setProperty: function (obj, prop, value) {
                //console.trace('helpers.setProperty', obj, prop, value);
                var path = prop,
                    of,
                    last;
                if (!angular.isArray(prop)) {
                    prop = prop.split('.');
                    path = prop;
                }
                last = _.last(path);
                path = path.slice(0, path.length - 1);
                if (!path.length) {
                    obj[prop.join('')] = value;
                    return;
                }
                of = this.getProperty(obj, path);
                of[last] = value;
            },
            getProperty: function (obj, prop) {
                //console.trace('helpers.getProperty', obj, prop);
                var path = prop;
                if (!angular.isArray(path)) {
                    path = prop.split('.');
                }
                angular.forEach(path, function (path) {
                    try {
                        obj = obj[path];
                    } catch (e) {
                        return undefined;
                    }
                });
                return obj;

            },
            extendDeep: function (dst) {
                angular.forEach(arguments, function (obj) {
                    if (obj !== dst) {
                        angular.forEach(obj, function (value, key) {
                            if (dst[key] && angular.isObject(dst[key])) {
                                helpers.extendDeep(dst[key], value);
                            } else {
                                dst[key] = value;
                            }
                        });
                    }
                });
                return dst;
            },
            extend: function (dst) {
                angular.forEach(arguments, function (obj) {
                    if (obj !== dst) {
                        angular.forEach(obj, function (value, key) {
                            dst[key] = value;
                        });
                    }
                });
                return dst;
            },
            merge: function (dst) {
                angular.forEach(arguments, function (obj) {
                    if (obj !== dst) {
                        angular.forEach(obj, function (value, key) {
                            if (!angular.isDefined(dst[key])) {
                                dst[key] = value;
                            }
                        });
                    }
                });
                return dst;
            },
            mergeDeep: function (dst) {
                angular.forEach(arguments, function (obj) {
                    if (obj !== dst) {
                        angular.forEach(obj, function (value, key) {
                            if (dst[key] && angular.isObject(dst[key])) {
                                helpers.mergeDeep(dst[key], value);
                            } else if (!angular.isDefined(dst[key])) {
                                dst[key] = value;
                            }
                        });
                    }
                });
                return dst;
            },
            update: function (obj1, obj2, paths) {
                if (angular.isDefined(paths)) {
                    angular.forEach(paths, function (path) {
                        var val1 = helpers.getProperty(obj2, path);
                        helpers.setProperty(obj1, path, val1);
                    });
                } else {
                    $.extend(obj1, obj2); // shallow merge
                }
            }
        };
        if (GLOBAL_CONFIG.debug) {
            window._helpers = helpers;
        }
        return helpers;
    }).factory('endpoint', function ($http, generalLocalCache, GLOBAL_CONFIG,
        helpers, modelsUtil, $rootScope, $q, $cacheFactory, $injector) {

        var onlyInMemoryCache = $cacheFactory('endpointOnlyInMemory'),
            getCache = function (type) {
                if (type === undefined || type === 'local') {
                    return generalLocalCache;
                }
                if (type === 'memory') {
                    return onlyInMemoryCache;
                }
                console.error('Invalid type of cache provided: ' + type);
            },
            _compile = function (action, model, data, config) {
                config = helpers.alwaysObject(config);
                data = helpers.alwaysObject(data);

                return [angular.extend({
                    action_model: model,
                    action_id: action
                }, data), config];

            },
            cache_prefix = 'endpoint_',
            cacheRegistry = [],
            endpoint;

        cacheRegistry.push(onlyInMemoryCache);
        cacheRegistry.push(generalLocalCache);

        endpoint = {
            getCache: function (key) {
                var result = null;
                angular.forEach(cacheRegistry, function (cache) {
                    if (!result) {
                        result = cache.get(cache_prefix + key);
                    }
                });
                return result;
            },
            removeCache: function (key) {

                if (!angular.isDefined(key)) {
                    angular.forEach(cacheRegistry, function (cache) {
                        cache.removeAll();
                    });
                    return true;
                }
                if (angular.isArray(key)) {
                    angular.forEach(key, function (k) {
                        endpoint.removeCache(k);
                    });

                    return true;
                }

                angular.forEach(cacheRegistry, function (cache) {
                    cache.remove(cache_prefix + key);
                });

            },
            url: GLOBAL_CONFIG.api.endpoint.path,
            cached: function (key, action, model, data, config) {
                var cacheEngine = getCache(config ? config.cacheType : undefined),
                    cache_key = cache_prefix + key,
                    exists = cacheEngine.get(cache_key),
                    is_promise = (exists && angular.isFunction(exists.then)),
                    deffered,
                    promise;
                if (is_promise) {
                    return exists;
                }
                if (exists === undefined) {
                    promise = endpoint[config.method ? config.method.toLowerCase() : 'post'](action, model, data, config);
                    promise.then(function (response) {
                        cacheEngine.put(cache_key, response);
                    }, function () {
                        cacheEngine.remove(cache_key);
                    });
                    cacheEngine.put(cache_key, promise);
                    return promise;
                }

                deffered = $q.defer();
                promise = deffered.promise;
                deffered.resolve(exists);
                return promise;


            },
            post: function (action, model, data, config) {
                var compiled = _compile(action, model, data, config),
                    defaults = {
                        method: 'POST',
                        url: endpoint.url
                    },
                    cache_id;
                compiled[0] = modelsUtil.argumentsToJson(compiled[0]);
                if (compiled[1] && angular.isString(compiled[1].cache)) {
                    cache_id = compiled[1].cache;
                    compiled[1].cache = false;
                    // avoid recursion
                    return endpoint.cached(cache_id, action, model, data, compiled[1]);
                }
                angular.extend(defaults, compiled[1]);
                defaults.data = compiled[0];
                return $http(defaults);
            },
            get: function (action, model, data, config) {
                var compiled = _compile(action, model, data, config),
                    gets = {
                        params: compiled[0]
                    },
                    defaults = {
                        method: 'GET',
                        url: endpoint.url
                    },
                    cache_id;
                compiled[0] = modelsUtil.argumentsToJson(compiled[0]);
                $.extend(gets, compiled[1]);
                angular.extend(defaults, gets);
                if (defaults && angular.isString(defaults.cache)) {
                    cache_id = defaults.cache;
                    defaults.cache = false;
                    return endpoint.cached(cache_id, action, model, data, gets);
                }
                return $http(defaults);
            }
        };

        if (GLOBAL_CONFIG.debug) {
            window._endpoint = endpoint;
        }

        return endpoint;

    }).factory('generalLocalCache', function (DSCacheFactory, $cacheFactory) {
        // combination of LocalStorageCache and inMemory cache
        var inMemory = $cacheFactory('localStoragePolyfillInMemory'),
            // in memory cache for non-serizible jsons
            nothing = '___undefined___',
            memory_only = '___in_memory_only___',
            localStoragePolyfill,
            generalLocalCache;

        function prepare(key, val) {
            if (val && ((val.value && angular.isFunction(val.value.then)) || (angular.isObject(val.value) && val.value[memory_only] !== undefined))) {
                return nothing;
            }
            return angular.toJson(val);
        }

        localStoragePolyfill = {
            getItem: function (key) {
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
                }
                return undefined;
            },
            setItem: function (key, value) {
                inMemory.put(key, value);
                value = prepare(key, value);
                return localStorage.setItem(key, value);
            },
            removeItem: function (key) {
                inMemory.remove(key);
                return localStorage.removeItem(key);
            }
        };
        generalLocalCache = DSCacheFactory('generalCache', {
            storageMode: 'localStorage',
            storageImpl: localStoragePolyfill
        });

        generalLocalCache.inMemory = function (value) {
            var only_in_memory = {};
            only_in_memory[memory_only] = value;
            return only_in_memory;
        };

        return generalLocalCache;

    }).run(function ($http, generalLocalCache) {

        $http.defaults.cache = generalLocalCache;

    }).config(['$httpProvider', function ($httpProvider) {

        $httpProvider.interceptors.push(['$rootScope', '$q', '$injector',
            function ($rootScope, $q, $injector) {

                var handleResponse = function (rejection) {

                    var data = rejection.data,
                        normalizeEntity = (rejection.config.normalizeEntity === undefined || rejection.config.normalizeEntity),
                        errorHandling = $injector.get('errorHandling'),
                        modelsUtil = $injector.get('modelsUtil'),
                        enableUI = function () {
                            $rootScope.$broadcast('disableUI', false);
                        },
                        reject,
                        shouldDisable = (rejection.config.disableUI === undefined || rejection.config.disableUI === true);

                    if (!rejection.config.ignoreErrors) {

                        if (rejection.status > 200) {
                            errorHandling.modal(angular.isString(rejection.data) ? {
                                traceback: rejection.data
                            } : rejection.data.errors);
                            if (shouldDisable) {
                                enableUI();
                            }
                            return $q.reject(rejection);
                        }
                        if (data && data.errors) {
                            errorHandling.modal(rejection.data.errors);
                            reject = (rejection.config.rejectOnErrors === undefined || rejection.config.rejectOnErrors === true);
                            if (data.errors.action_denied) {
                                reject = true;
                            }
                            if (reject && shouldDisable) {
                                enableUI();
                                return $q.reject(rejection);
                            }

                        }
                    }

                    if (normalizeEntity && data) {
                        if (angular.isDefined(data.entities)) {
                            modelsUtil.normalizeMultiple(data.entities);
                        } else if (angular.isDefined(data.entity)) {
                            modelsUtil.normalize(data.entity);
                        }

                    }
                    if (shouldDisable) {
                        enableUI();
                    }
                    // otherwise, default behaviour
                    return rejection || $q.when(rejection);

                };

                return {
                    response: handleResponse,
                    responseError: handleResponse,
                    request: function (config) {
                        var shouldDisable = (config.disableUI === undefined || config.disableUI === true);
                        if (shouldDisable) {
                            $rootScope.$broadcast('disableUI', true);
                        }
                        return config || $q.when(config);
                    }
                };
            }]);

    }]).factory('underscoreTemplate', function ($templateCache) {

        return {
            get: function (path) {
                return _.template($templateCache.get(path));
            }
        };
    });
}());
