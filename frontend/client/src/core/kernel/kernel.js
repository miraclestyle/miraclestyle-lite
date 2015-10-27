(function () {
    'use strict';
    angular.module('app').factory('errorHandling', ng(function ($modal, snackbar, GLOBAL_CONFIG, modals) {
        var translations = GLOBAL_CONFIG.backendErrorHandling,
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
                    modals.alert(null, {
                        title: 'Error while performing an action',
                        templateUrl: 'core/misc/errors.html',
                        text: {
                            primary: 'Got it'
                        },
                        errors: (function () {
                            var formatErrors = [];
                            angular.forEach(errors, function (error, key) {
                                formatErrors.push([key, errorHandling.translate(key, error)]);
                            });
                            return formatErrors;
                        }())
                    });
                },
                snackbar: function (errors, callback) {
                    if (errors.traceback) {
                        return snackbar.showK('errorWithTraceback');
                        //return errorHandling.modal(errors);
                    }
                    var messages = (function () {
                            var formatErrors = [];
                            angular.forEach(errors, function (error, key) {
                                formatErrors.push(errorHandling.translate(key, error));
                            });
                            return formatErrors;
                        }()).join('\n'),
                        other;

                    if (callback) {
                        other = callback(errors);
                        if (other !== false) {
                            messages = other;
                        }
                    }

                    snackbar.show(messages);
                }
            };

        return errorHandling;
    })).factory('helpers', ng(function (GLOBAL_CONFIG) {

        var helpers = {
            callable: function (fn) {
                if (angular.isFunction(fn)) {
                    return fn;
                }
                return angular.noop;
            },
            endpoint: {
                isResponseError: function (response) {
                    return angular.isString(response) || (response.status !== 200 || response.data.errors);
                },
                isResponseHttpError: function (response) {
                    return angular.isString(response) || response.status !== 200;
                }
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
            forceSetProperty: function (obj, prop, value) {
                var next = obj,
                    prev,
                    last;
                if (!angular.isArray(prop)) {
                    prop = prop.split('.');
                }
                if (prop.length === 1) {
                    obj[prop.join('')] = value;
                    return;
                }
                angular.forEach(prop, function (key, i) {
                    prev = next;
                    next = next[key];
                    last = i === (prop.length - 1);
                    if (angular.isUndefined(next) && !last) {
                        next = {};
                        prev[key] = next;
                    }

                    if (last) {
                        prev[key] = value;
                    }
                });
            },
            getProperty: function (obj, prop, defaultMaybe) {
                //console.trace('helpers.getProperty', obj, prop);
                var path = prop;
                if (!angular.isArray(path)) {
                    path = prop.split('.');
                }
                angular.forEach(path, function (path) {
                    try {
                        obj = obj[path];
                    } catch (e) {
                        return defaultMaybe;
                    }
                });
                if (angular.isUndefined(obj)) {
                    return defaultMaybe;
                }
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
    })).factory('endpoint', ng(function ($http, generalLocalCache, GLOBAL_CONFIG,
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

    })).factory('generalLocalCache', ng(function (DSCacheFactory, $cacheFactory) {
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
                var yes;
                inMemory.put(key, value);
                value = prepare(key, value);
                try {
                    yes = localStorage.setItem(key, value);
                } catch (ignore) {} // in case the localStorage is full it throws error
                return yes;
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

    })).run(ng(function ($http, generalLocalCache) {

        $http.defaults.cache = generalLocalCache;

    })).config(['$httpProvider', function ($httpProvider) {

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

                    if (!rejection.config.ignoreErrors || rejection.config.ignoreErrors > 1) {

                        if (rejection.status > 200 && rejection.config.ignoreErrors === 2) {
                            errorHandling.snackbar(angular.isString(rejection.data) ? {
                                traceback: rejection.data
                            } : rejection.data.errors, rejection.config.handleError);
                            if (shouldDisable) {
                                enableUI();
                            }
                            return $q.reject(rejection);
                        }
                        if (data && data.errors && (!rejection.config.ignoreErrors || rejection.config.ignoreErrors > 2)) {
                            errorHandling.snackbar(rejection.data.errors, rejection.config.handleError);
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
            }
        ]);

    }]).factory('underscoreTemplate', ng(function ($templateCache) {

        return {
            get: function (path) {
                return _.template($templateCache.get(path));
            }
        };
    })).factory('animationGenerator', function () {
        var animationGenerator = {
            classNamePrefix: 'tmp-',
            prefix: function (thing) {
                return (/WebKit/.test(navigator.userAgent) ? '-webkit-' : '') + thing;
            },
            compile: function (props) {
                var str = '';
                angular.forEach(props, function (value, key) {
                    str += animationGenerator.prefix(key) + ': ' + value + ';' + "\n";
                });
                return str;
            },
            make: function (name, definition) {
                var str = '@' + animationGenerator.prefix('keyframes') + ' ' + name + ' {' + "\n";

                str += definition;

                str += "\n" + '} .' + animationGenerator.classNamePrefix + name + '{' + animationGenerator.prefix('animation-name') + ':' + name + ';}';
                return str;
            },
            single: function (name, codes) {
                var nextuid = _.uniqueId(),
                    id = 'temporary-animator' + nextuid,
                    style = $('#' + id);
                name = name + nextuid;
                if (!style.length) {
                    style = $('<style/>').attr('id', id);
                    style.appendTo('head');
                }
                style.text(animationGenerator.make(name, codes));
                return {
                    name: name,
                    className: animationGenerator.classNamePrefix + name,
                    destroy: function () {
                        style.remove();
                    }
                };
            }
        };
        return animationGenerator;
    });
}());
