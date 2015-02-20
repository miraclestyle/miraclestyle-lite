// Source: http://code.google.com/p/gflot/source/browse/trunk/flot/base64.js?r=153

/* Copyright (C) 1999 Masanao Izumo <iz@onicos.co.jp>
 * Version: 1.0
 * LastModified: Dec 25 1999
 * This library is free.  You can redistribute it and/or modify it.
 */

/*
 * Interfaces:
 * b64 = base64encode(data);
 * data = base64decode(b64);
 */

(function () {

    var base64EncodeChars =
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    var base64DecodeChars = new Array(-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -
        1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -
        1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 62, -1, -1, -
        1, 63,
        52, 53, 54, 55, 56, 57, 58, 59, 60, 61, -1, -1, -1, -1, -1, -1, -1, 0,
        1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14,
        15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, -1, -1, -1, -1, -1, -1, 26,
        27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40,
        41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, -1, -1, -1, -1, -1);

    function base64encode(str) {
        var out, i, len;
        var c1, c2, c3;

        len = str.length;
        i = 0;
        out = "";
        while (i < len) {
            c1 = str.charCodeAt(i++) & 0xff;
            if (i == len) {
                out += base64EncodeChars.charAt(c1 >> 2);
                out += base64EncodeChars.charAt((c1 & 0x3) << 4);
                out += "==";
                break;
            }
            c2 = str.charCodeAt(i++);
            if (i == len) {
                out += base64EncodeChars.charAt(c1 >> 2);
                out += base64EncodeChars.charAt(((c1 & 0x3) << 4) | ((c2 & 0xF0) >>
                    4));
                out += base64EncodeChars.charAt((c2 & 0xF) << 2);
                out += "=";
                break;
            }
            c3 = str.charCodeAt(i++);
            out += base64EncodeChars.charAt(c1 >> 2);
            out += base64EncodeChars.charAt(((c1 & 0x3) << 4) | ((c2 & 0xF0) >>
                4));
            out += base64EncodeChars.charAt(((c2 & 0xF) << 2) | ((c3 & 0xC0) >>
                6));
            out += base64EncodeChars.charAt(c3 & 0x3F);
        }
        return out;
    }

    function base64decode(str) {
        var c1, c2, c3, c4;
        var i, len, out;

        len = str.length;
        i = 0;
        out = "";
        while (i < len) {
            /* c1 */
            do {
                c1 = base64DecodeChars[str.charCodeAt(i++) & 0xff];
            } while (i < len && c1 == -1);
            if (c1 == -1)
                break;

            /* c2 */
            do {
                c2 = base64DecodeChars[str.charCodeAt(i++) & 0xff];
            } while (i < len && c2 == -1);
            if (c2 == -1)
                break;

            out += String.fromCharCode((c1 << 2) | ((c2 & 0x30) >> 4));

            /* c3 */
            do {
                c3 = str.charCodeAt(i++) & 0xff;
                if (c3 == 61)
                    return out;
                c3 = base64DecodeChars[c3];
            } while (i < len && c3 == -1);
            if (c3 == -1)
                break;

            out += String.fromCharCode(((c2 & 0XF) << 4) | ((c3 & 0x3C) >> 2));

            /* c4 */
            do {
                c4 = str.charCodeAt(i++) & 0xff;
                if (c4 == 61)
                    return out;
                c4 = base64DecodeChars[H4];
            } while (i < len && c4 == -1);
            if (c4 == -1)
                break;
            out += String.fromCharCode(((c3 & 0x03) << 6) | c4);
        }
        return out;
    }

    if (!window.btoa) window.btoa = base64encode;
    if (!window.atob) window.atob = base64decode;

})();

// Production steps of ECMA-262, Edition 5, 15.4.4.14
// Reference: http://es5.github.io/#x15.4.4.14
if (!Array.prototype.indexOf) {
  Array.prototype.indexOf = function(searchElement, fromIndex) {

    var k;

    // 1. Let O be the result of calling ToObject passing
    //    the this value as the argument.
    if (this == null) {
      throw new TypeError('"this" is null or not defined');
    }

    var O = Object(this);

    // 2. Let lenValue be the result of calling the Get
    //    internal method of O with the argument "length".
    // 3. Let len be ToUint32(lenValue).
    var len = O.length >>> 0;

    // 4. If len is 0, return -1.
    if (len === 0) {
      return -1;
    }

    // 5. If argument fromIndex was passed let n be
    //    ToInteger(fromIndex); else let n be 0.
    var n = +fromIndex || 0;

    if (Math.abs(n) === Infinity) {
      n = 0;
    }

    // 6. If n >= len, return -1.
    if (n >= len) {
      return -1;
    }

    // 7. If n >= 0, then Let k be n.
    // 8. Else, n<0, Let k be len - abs(n).
    //    If k is less than 0, then let k be 0.
    k = Math.max(n >= 0 ? n : len - Math.abs(n), 0);

    // 9. Repeat, while k < len
    while (k < len) {
      // a. Let Pk be ToString(k).
      //   This is implicit for LHS operands of the in operator
      // b. Let kPresent be the result of calling the
      //    HasProperty internal method of O with argument Pk.
      //   This step can be combined with c
      // c. If kPresent is true, then
      //    i.  Let elementK be the result of calling the Get
      //        internal method of O with the argument ToString(k).
      //   ii.  Let same be the result of applying the
      //        Strict Equality Comparison Algorithm to
      //        searchElement and elementK.
      //  iii.  If same is true, return k.
      if (k in O && O[k] === searchElement) {
        return k;
      }
      k++;
    }
    return -1;
  };
}
/**
 *
 * Overrides for window scope
 */
(function () {

    'use strict';

    Array.prototype.iremove = function (callback) {
        var i = this.length;
        while (i--) {
            if (callback(this[i], i)) {
                this.splice(i, 1);
            }
        }
    };

    Array.prototype.remove = function (val) {
        var index = this.indexOf(val);
        if (index !== -1) {
            this.splice(index, 1);
        }
        return this;
    };

    Array.prototype.empty = function (val) {
        this.splice(0, this.length);
        return this;
    };

    Array.prototype.contains = function (value, all) {
        if (angular.isArray(value)) {
            var matches = [];
            angular.forEach(value, function (v) {
                matches.push((this.indexOf(value) > -1));
            });
            if (all) {
                return _.all(matches);
            }
            return _.some(matches);
        }
        return this.indexOf(value) > -1;
    };

    Array.prototype.compare = function (array) {
        // if the other array is a falsy value, return
        if (!array) {
            return false;
        }
        // compare lengths - can save a lot of time
        if (this.length !== array.length) {
            return false;
        }

        var i, l = this.length;
        for (i = 0; i < l; i++) {
            // Check if we have nested arrays
            if (this[i] instanceof Array && array[i] instanceof Array) {
                // recurse into the nested arrays
                if (!this[i].compare(array[i])) {
                    return false;
                }

            } else if (this[i] !== array[i]) {
                // Warning - two different object instances will never be equal: {x:20} != {x:20}
                return false;
            }
        }
        return true;
    };

    Array.prototype.prepend = function (other_array) {
        var that = this;
        angular.forEach(other_array, function (v) {
            that.unshift(v);
        });
    };

    Array.prototype.extend = function (other_array) {
        var that = this;
        angular.forEach(other_array, function (v) {
            that.push(v);
        });
    };

}());
// bootstrap file, introduces global App or MainApp
(function () {

    'use strict';

    if (!window.console) {
        window.console = {};
    }

    angular.forEach(['log', 'error', 'trace', 'debug', 'info'], function (method) {
        if (!window.console[method]) {
            window.console[method] = angular.noop;
        }
    });

    var host = window.location.protocol + '//' + window.location.host,
        // global configuration for the application
        // this config file will expand
        GLOBAL_CONFIG = {
            debug: true, // debug mode
            host: host,
            modules: ['config', 'ngAnimate', 'ngMessages', 'ui.router', 'ui.sortable', 'ui.inflector', 'ngSanitize',
                      'ngDragDrop', 'timer', 'googlechart', 'ngMaterial'], // this will be changed accordingly
            api: {
                endpoint: {
                    path: host + '/api/endpoint'
                },
                modelsMeta: '/api/model_meta'
            },
            date: {
                format: 'yyyy-MM-dd HH:mm:ss Z'
            },
            defaultImage: 'http://placehold.it/240x100',
            defaultLogo: 'http://placehold.it/240x100',
            defaultCatalogCover: 'http://placehold.it/240x240',
            grid: {
                maxWidth: 240,
                minWidth: 180,
                maxHeight: 360
            },
            imageSizes: _.range(50, 1650, 50), // loading ranges for get serving url
            social: {
                facebook: {
                    id: '125702284258635'
                }
            },
            admin: {
                listTemplates: {},
                menu: [{name: 'Catalogs', kind: 31}, {name: 'Users', kind: 11}, {name: 'Orders', kind: '34'}], // admin paths shown in the menu
                listViewDirective: ['31', '11', '34'],
                listTitles: {
                    '31': 'Catalogs',
                    '11': 'Users',
                    '34': 'Orders'
                }
            }
        };
    angular.module('config', ['ng'])
        .constant('GLOBAL_CONFIG', GLOBAL_CONFIG)
        .config(function ($httpProvider, $locationProvider) {
            $httpProvider.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';
            $locationProvider.hashPrefix('!');
            $locationProvider.html5Mode(true);
        });
    angular.module('app', GLOBAL_CONFIG.modules)
        .config(function ($mdThemingProvider) {
            $mdThemingProvider.theme('default')
                .primaryPalette('grey')
                .accentPalette('blue-grey')
                .warnPalette('red');
        });
}());

$(function () {
    'use strict';
    var container = $('<div>').css({ height: 1, overflow: 'scroll' }).appendTo('body'),
        child = $('<div>').css({ height: 2 }).appendTo(container);
    window.SCROLLBAR_WIDTH = container.width() - child.width();
    if (Modernizr.touch) {
        window.SCROLLBAR_WIDTH = 0;
    }
    container.remove();
});
/* Bootstrap, it will try to load current account and model data and then bootstrap the application. */
(function () {
    'use strict';
    angular.element(document).ready(function () {
        var failure = function () {
                var choice = confirm('Could not start application. Reload your browser and try again?');
                if (choice) {
                    window.location.reload(true);
                }
            },
            injector = angular.injector(['config']),
            $http = injector.get('$http'),
            $q = injector.get('$q'),
            GLOBAL_CONFIG = injector.get('GLOBAL_CONFIG'),
            promises = [$http.get(GLOBAL_CONFIG.api.modelsMeta), $http.get(GLOBAL_CONFIG.api.endpoint.path + '?action_id=current_account&action_model=11')];

        $q.all(promises).then(function (response) {
            var d1 = response[0].data, d2 = response[1].data;
            window.MODELS_META = d1;
            window.CURRENT_ACCOUNT = d2.entity;
            if ((d1 && d1.errors) || (d2 && d2.errors)) {
                failure();
            } else {
                angular.bootstrap(document, ['app']);
            }
        }, failure);

    });
}());(function () {
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

                    if (normalizeEntity) {
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
/*!
 * Angular Material Design
 * https://github.com/angular/material
 * @license MIT
 * v0.7.1
 */
angular.module('ngMaterial', ["ng","ngAnimate","ngAria","material.core","material.core.theming.palette","material.core.theming","material.components.backdrop","material.components.button","material.components.card","material.components.checkbox","material.components.content","material.components.simpledialog","material.components.divider","material.components.input","material.components.progressCircular","material.components.progressLinear","material.components.radioButton","material.components.sidenav","material.components.sticky","material.components.subheader","material.components.swipe","material.components.switch","material.components.textField","material.components.toolbar","material.components.whiteframe"]);
/*!
 * Angular Material Design
 * https://github.com/angular/material
 * @license MIT
 * v0.7.1
 */
(function() {
'use strict';

/**
 * Initialization function that validates environment
 * requirements.
 */
angular
  .module('material.core', ['material.core.theming'])
  .config(MdCoreConfigure);


function MdCoreConfigure($provide, $mdThemingProvider) {
  $provide.decorator('$$rAF', ["$delegate", rAFDecorator]);

  $mdThemingProvider.theme('default')
    .primaryPalette('indigo')
    .accentPalette('pink')
    .warnPalette('red')
    .backgroundPalette('grey');
}
MdCoreConfigure.$inject = ["$provide", "$mdThemingProvider"];

function rAFDecorator( $delegate ) {
  /**
   * Use this to throttle events that come in often.
   * The throttled function will always use the *last* invocation before the
   * coming frame.
   *
   * For example, window resize events that fire many times a second:
   * If we set to use an raf-throttled callback on window resize, then
   * our callback will only be fired once per frame, with the last resize
   * event that happened before that frame.
   *
   * @param {function} callback function to debounce
   */
  $delegate.throttle = function(cb) {
    var queueArgs, alreadyQueued, queueCb, context;
    return function debounced() {
      queueArgs = arguments;
      context = this;
      queueCb = cb;
      if (!alreadyQueued) {
        alreadyQueued = true;
        $delegate(function() {
          queueCb.apply(context, queueArgs);
          alreadyQueued = false;
        });
      }
    };
  };
  return $delegate;
}

})();

/*!
 * Angular Material Design
 * https://github.com/angular/material
 * @license MIT
 * v0.7.1
 */
(function() {
'use strict';

angular.module('material.core')
.factory('$mdConstant', MdConstantFactory);

function MdConstantFactory($$rAF, $sniffer) {

  var webkit = /webkit/i.test($sniffer.vendorPrefix);
  function vendorProperty(name) {
    return webkit ?  ('webkit' + name.charAt(0).toUpperCase() + name.substring(1)) : name;
  }

  return {
    KEY_CODE: {
      ENTER: 13,
      ESCAPE: 27,
      SPACE: 32,
      LEFT_ARROW : 37,
      UP_ARROW : 38,
      RIGHT_ARROW : 39,
      DOWN_ARROW : 40
    },
    CSS: {
      /* Constants */
      TRANSITIONEND: 'transitionend' + (webkit ? ' webkitTransitionEnd' : ''),
      ANIMATIONEND: 'animationend' + (webkit ? ' webkitAnimationEnd' : ''),

      TRANSFORM: vendorProperty('transform'),
      TRANSITION: vendorProperty('transition'),
      TRANSITION_DURATION: vendorProperty('transitionDuration'),
      ANIMATION_PLAY_STATE: vendorProperty('animationPlayState'),
      ANIMATION_DURATION: vendorProperty('animationDuration'),
      ANIMATION_NAME: vendorProperty('animationName'),
      ANIMATION_TIMING: vendorProperty('animationTimingFunction'),
      ANIMATION_DIRECTION: vendorProperty('animationDirection')
    },
    MEDIA: {
      'sm': '(max-width: 600px)',
      'gt-sm': '(min-width: 600px)',
      'md': '(min-width: 600px) and (max-width: 960px)',
      'gt-md': '(min-width: 960px)',
      'lg': '(min-width: 960px) and (max-width: 1200px)',
      'gt-lg': '(min-width: 1200px)'
    }
  };
}
MdConstantFactory.$inject = ["$$rAF", "$sniffer"];

})();
/*!
 * Angular Material Design
 * https://github.com/angular/material
 * @license MIT
 * v0.7.1
 */
(function(){

  angular
    .module('material.core')
    .config( ["$provide", function($provide){
       $provide.decorator('$mdUtil', ['$delegate', function ($delegate){
           /**
            * Inject the iterator facade to easily support iteration and accessors
            * @see iterator below
            */
           $delegate.iterator = Iterator;

           return $delegate;
         }
       ]);
     }]);

  /**
   * iterator is a list facade to easily support iteration and accessors
   *
   * @param items Array list which this iterator will enumerate
   * @param reloop Boolean enables iterator to consider the list as an endless reloop
   */
  function Iterator(items, reloop) {
    var trueFn = function() { return true; };

    reloop = !!reloop;
    var _items = items || [ ];

    // Published API
    return {
      items: getItems,
      count: count,

      inRange: inRange,
      contains: contains,
      indexOf: indexOf,
      itemAt: itemAt,

      findBy: findBy,

      add: add,
      remove: remove,

      first: first,
      last: last,
      next: angular.bind(null, findSubsequentItem, false),
      previous: angular.bind(null, findSubsequentItem, true),

      hasPrevious: hasPrevious,
      hasNext: hasNext

    };

    /**
     * Publish copy of the enumerable set
     * @returns {Array|*}
     */
    function getItems() {
      return [].concat(_items);
    }

    /**
     * Determine length of the list
     * @returns {Array.length|*|number}
     */
    function count() {
      return _items.length;
    }

    /**
     * Is the index specified valid
     * @param index
     * @returns {Array.length|*|number|boolean}
     */
    function inRange(index) {
      return _items.length && ( index > -1 ) && (index < _items.length );
    }

    /**
     * Can the iterator proceed to the next item in the list; relative to
     * the specified item.
     *
     * @param item
     * @returns {Array.length|*|number|boolean}
     */
    function hasNext(item) {
      return item ? inRange(indexOf(item) + 1) : false;
    }

    /**
     * Can the iterator proceed to the previous item in the list; relative to
     * the specified item.
     *
     * @param item
     * @returns {Array.length|*|number|boolean}
     */
    function hasPrevious(item) {
      return item ? inRange(indexOf(item) - 1) : false;
    }

    /**
     * Get item at specified index/position
     * @param index
     * @returns {*}
     */
    function itemAt(index) {
      return inRange(index) ? _items[index] : null;
    }

    /**
     * Find all elements matching the key/value pair
     * otherwise return null
     *
     * @param val
     * @param key
     *
     * @return array
     */
    function findBy(key, val) {
      return _items.filter(function(item) {
        return item[key] === val;
      });
    }

    /**
     * Add item to list
     * @param item
     * @param index
     * @returns {*}
     */
    function add(item, index) {
      if ( !item ) return -1;

      if (!angular.isNumber(index)) {
        index = _items.length;
      }

      _items.splice(index, 0, item);

      return indexOf(item);
    }

    /**
     * Remove item from list...
     * @param item
     */
    function remove(item) {
      if ( contains(item) ){
        _items.splice(indexOf(item), 1);
      }
    }

    /**
     * Get the zero-based index of the target item
     * @param item
     * @returns {*}
     */
    function indexOf(item) {
      return _items.indexOf(item);
    }

    /**
     * Boolean existence check
     * @param item
     * @returns {boolean}
     */
    function contains(item) {
      return item && (indexOf(item) > -1);
    }

    /**
     * Return first item in the list
     * @returns {*}
     */
    function first() {
      return _items.length ? _items[0] : null;
    }

    /**
     * Return last item in the list...
     * @returns {*}
     */
    function last() {
      return _items.length ? _items[_items.length - 1] : null;
    }

    /**
     * Find the next item. If reloop is true and at the end of the list, it will
     * go back to the first item. If given ,the `validate` callback will be used
     * determine whether the next item is valid. If not valid, it will try to find the
     * next item again.
     * @param item
     * @param {optional} validate Validate function
     * @param {optional} limit Recursion limit
     * @returns {*}
     */
    function findSubsequentItem(backwards, item, validate, limit) {
      validate = validate || trueFn;

      var curIndex = indexOf(item);
      if (!inRange(curIndex)) {
        return null;
      }

      var nextIndex = curIndex + (backwards ? -1 : 1);
      var foundItem = null;
      if (inRange(nextIndex)) {
        foundItem = _items[nextIndex];
      } else if (reloop) {
        foundItem = backwards ? last() : first();
        nextIndex = indexOf(foundItem);
      }

      if ((foundItem === null) || (nextIndex === limit)) {
        return null;
      }

      if (angular.isUndefined(limit)) {
        limit = nextIndex;
      }

      return validate(foundItem) ? foundItem : findSubsequentItem(backwards, foundItem, validate, limit);
    }
  }

})();

/*!
 * Angular Material Design
 * https://github.com/angular/material
 * @license MIT
 * v0.7.1
 */
angular.module('material.core')
.factory('$mdMedia', mdMediaFactory);

/**
 * Exposes a function on the '$mdMedia' service which will return true or false,
 * whether the given media query matches. Re-evaluates on resize. Allows presets
 * for 'sm', 'md', 'lg'.
 *
 * @example $mdMedia('sm') == true if device-width <= sm
 * @example $mdMedia('(min-width: 1200px)') == true if device-width >= 1200px
 * @example $mdMedia('max-width: 300px') == true if device-width <= 300px (sanitizes input, adding parens)
 */
function mdMediaFactory($mdConstant, $rootScope, $window) {
  var queries = {};
  var results = {};

  return $mdMedia;

  function $mdMedia(query) {
    var validated = queries[query];
    if (angular.isUndefined(validated)) {
      validated = queries[query] = validate(query);
    }

    var result = results[validated];
    if (angular.isUndefined(result)) {
      result = add(validated);
    }

    return result;
  }

  function validate(query) {
    return $mdConstant.MEDIA[query] ||
           ((query.charAt(0) !== '(') ? ('(' + query + ')') : query);
  }

  function add(query) {
    var result = $window.matchMedia(query);
    result.addListener(onQueryChange);
    return (results[result.media] = !!result.matches);
  }

  function onQueryChange() {
    var query = this;
    $rootScope.$evalAsync(function() {
      results[query.media] = !!query.matches;
    });
  }

}
mdMediaFactory.$inject = ["$mdConstant", "$rootScope", "$window"];

/*!
 * Angular Material Design
 * https://github.com/angular/material
 * @license MIT
 * v0.7.1
 */
(function() {
'use strict';

/*
 * This var has to be outside the angular factory, otherwise when
 * there are multiple material apps on the same page, each app
 * will create its own instance of this array and the app's IDs
 * will not be unique.
 */
var nextUniqueId = ['0','0','0'];

angular.module('material.core')
.factory('$mdUtil', ["$document", "$timeout", function($document, $timeout) {
  var Util;

  return Util = {
    now: window.performance ? angular.bind(window.performance, window.performance.now) : Date.now,

    elementRect: function(element, offsetParent) {
      var node = element[0];
      offsetParent = offsetParent || node.offsetParent || document.body;
      offsetParent = offsetParent[0] || offsetParent;
      var nodeRect = node.getBoundingClientRect();
      var parentRect = offsetParent.getBoundingClientRect();
      return {
        left: nodeRect.left - parentRect.left + offsetParent.scrollLeft,
        top: nodeRect.top - parentRect.top + offsetParent.scrollTop,
        width: nodeRect.width,
        height: nodeRect.height
      };
    },

    fakeNgModel: function() {
      return {
        $fake: true,
        $setViewValue: function(value) {
          this.$viewValue = value;
          this.$render(value);
          this.$viewChangeListeners.forEach(function(cb) { cb(); });
        },
        $isEmpty: function(value) {
          return (''+value).length === 0;
        },
        $parsers: [],
        $formatters: [],
        $viewChangeListeners: [],
        $render: angular.noop
      };
    },

    // Returns a function, that, as long as it continues to be invoked, will not
    // be triggered. The function will be called after it stops being called for
    // N milliseconds.
    // @param wait Integer value of msecs to delay (since last debounce reset); default value 10 msecs
    // @param invokeApply should the $timeout trigger $digest() dirty checking
    debounce: function (func, wait, scope, invokeApply) {
      var timer;

      return function debounced() {
        var context = scope,
          args = Array.prototype.slice.call(arguments);

        $timeout.cancel(timer);
        timer = $timeout(function() {

          timer = undefined;
          func.apply(context, args);

        }, wait || 10, invokeApply );
      };
    },

    // Returns a function that can only be triggered every `delay` milliseconds.
    // In other words, the function will not be called unless it has been more
    // than `delay` milliseconds since the last call.
    throttle: function throttle(func, delay) {
      var recent;
      return function throttled() {
        var context = this;
        var args = arguments;
        var now = Util.now();

        if (!recent || (now - recent > delay)) {
          func.apply(context, args);
          recent = now;
        }
      };
    },

    /**
     * nextUid, from angular.js.
     * A consistent way of creating unique IDs in angular. The ID is a sequence of alpha numeric
     * characters such as '012ABC'. The reason why we are not using simply a number counter is that
     * the number string gets longer over time, and it can also overflow, where as the nextId
     * will grow much slower, it is a string, and it will never overflow.
     *
     * @returns an unique alpha-numeric string
     */
    nextUid: function() {
      var index = nextUniqueId.length;
      var digit;

      while(index) {
        index--;
        digit = nextUniqueId[index].charCodeAt(0);
        if (digit == 57 /*'9'*/) {
          nextUniqueId[index] = 'A';
          return nextUniqueId.join('');
        }
        if (digit == 90  /*'Z'*/) {
          nextUniqueId[index] = '0';
        } else {
          nextUniqueId[index] = String.fromCharCode(digit + 1);
          return nextUniqueId.join('');
        }
      }
      nextUniqueId.unshift('0');
      return nextUniqueId.join('');
    },

    // Stop watchers and events from firing on a scope without destroying it,
    // by disconnecting it from its parent and its siblings' linked lists.
    disconnectScope: function disconnectScope(scope) {
      if (!scope) return;

      // we can't destroy the root scope or a scope that has been already destroyed
      if (scope.$root === scope) return;
      if (scope.$$destroyed ) return;

      var parent = scope.$parent;
      scope.$$disconnected = true;

      // See Scope.$destroy
      if (parent.$$childHead === scope) parent.$$childHead = scope.$$nextSibling;
      if (parent.$$childTail === scope) parent.$$childTail = scope.$$prevSibling;
      if (scope.$$prevSibling) scope.$$prevSibling.$$nextSibling = scope.$$nextSibling;
      if (scope.$$nextSibling) scope.$$nextSibling.$$prevSibling = scope.$$prevSibling;

      scope.$$nextSibling = scope.$$prevSibling = null;

    },

    // Undo the effects of disconnectScope above.
    reconnectScope: function reconnectScope(scope) {
      if (!scope) return;

      // we can't disconnect the root node or scope already disconnected
      if (scope.$root === scope) return;
      if (!scope.$$disconnected) return;

      var child = scope;

      var parent = child.$parent;
      child.$$disconnected = false;
      // See Scope.$new for this logic...
      child.$$prevSibling = parent.$$childTail;
      if (parent.$$childHead) {
        parent.$$childTail.$$nextSibling = child;
        parent.$$childTail = child;
      } else {
        parent.$$childHead = parent.$$childTail = child;
      }
    },
  /*
   * getClosest replicates jQuery.closest() to walk up the DOM tree until it finds a matching nodeName
   *
   * @param el Element to start walking the DOM from
   * @param tagName Tag name to find closest to el, such as 'form'
   */
    getClosest: function getClosest(el, tagName) {
      tagName = tagName.toUpperCase();
      do {
        if (el.nodeName === tagName) {
          return el;
        }
      } while (el = el.parentNode);
      return null;
    }
  };

}]);

/*
 * Since removing jQuery from the demos, some code that uses `element.focus()` is broken.
 *
 * We need to add `element.focus()`, because it's testable unlike `element[0].focus`.
 *
 * TODO(ajoslin): This should be added in a better place later.
 */

angular.element.prototype.focus = angular.element.prototype.focus || function() {
  if (this.length) {
    this[0].focus();
  }
  return this;
};
angular.element.prototype.blur = angular.element.prototype.blur || function() {
  if (this.length) {
    this[0].blur();
  }
  return this;
};

})();

/*!
 * Angular Material Design
 * https://github.com/angular/material
 * @license MIT
 * v0.7.1
 */
(function() {
'use strict';

angular.module('material.core')
  .service('$mdAria', AriaService);

function AriaService($$rAF, $log, $window) {

  return {
    expect: expect,
    expectAsync: expectAsync,
    expectWithText: expectWithText
  };

  /**
   * Check if expected attribute has been specified on the target element or child
   * @param element
   * @param attrName
   * @param {optional} defaultValue What to set the attr to if no value is found
   */
  function expect(element, attrName, defaultValue) {
    var node = element[0];

    if (!node.hasAttribute(attrName) && !childHasAttribute(node, attrName)) {

      defaultValue = angular.isString(defaultValue) && defaultValue.trim() || '';
      if (defaultValue.length) {
        element.attr(attrName, defaultValue);
      } else {
        $log.warn('ARIA: Attribute "', attrName, '", required for accessibility, is missing on node:', node);
      }

    }
  }

  function expectAsync(element, attrName, defaultValueGetter) {
    // Problem: when retrieving the element's contents synchronously to find the label,
    // the text may not be defined yet in the case of a binding.
    // There is a higher chance that a binding will be defined if we wait one frame.
    $$rAF(function() {
      expect(element, attrName, defaultValueGetter());
    });
  }

  function expectWithText(element, attrName) {
    expectAsync(element, attrName, function() {
      return element.text().trim();
    });
  }

  function childHasAttribute(node, attrName) {
    var hasChildren = node.hasChildNodes(),
        hasAttr = false;

    function isHidden(el) {
      var style = el.currentStyle ? el.currentStyle : $window.getComputedStyle(el);
      return (style.display === 'none');
    }

    if(hasChildren) {
      var children = node.childNodes;
      for(var i=0; i<children.length; i++){
        var child = children[i];
        if(child.nodeType === 1 && child.hasAttribute(attrName)) {
          if(!isHidden(child)){
            hasAttr = true;
          }
        }
      }
    }
    return hasAttr;
  }
}
AriaService.$inject = ["$$rAF", "$log", "$window"];
})();

/*!
 * Angular Material Design
 * https://github.com/angular/material
 * @license MIT
 * v0.7.1
 */
(function() {
'use strict';

angular.module('material.core')
  .service('$mdCompiler', mdCompilerService);

function mdCompilerService($q, $http, $injector, $compile, $controller, $templateCache) {
  /* jshint validthis: true */

  /*
   * @ngdoc service
   * @name $mdCompiler
   * @module material.core
   * @description
   * The $mdCompiler service is an abstraction of angular's compiler, that allows the developer
   * to easily compile an element with a templateUrl, controller, and locals.
   *
   * @usage
   * <hljs lang="js">
   * $mdCompiler.compile({
   *   templateUrl: 'modal.html',
   *   controller: 'ModalCtrl',
   *   locals: {
   *     modal: myModalInstance;
   *   }
   * }).then(function(compileData) {
   *   compileData.element; // modal.html's template in an element
   *   compileData.link(myScope); //attach controller & scope to element
   * });
   * </hljs>
   */

   /*
    * @ngdoc method
    * @name $mdCompiler#compile
    * @description A helper to compile an HTML template/templateUrl with a given controller,
    * locals, and scope.
    * @param {object} options An options object, with the following properties:
    *
    *    - `controller` - `{(string=|function()=}` Controller fn that should be associated with
    *      newly created scope or the name of a registered controller if passed as a string.
    *    - `controllerAs` - `{string=}` A controller alias name. If present the controller will be
    *      published to scope under the `controllerAs` name.
    *    - `template` - `{string=}` An html template as a string.
    *    - `templateUrl` - `{string=}` A path to an html template.
    *    - `transformTemplate` - `{function(template)=}` A function which transforms the template after
    *      it is loaded. It will be given the template string as a parameter, and should
    *      return a a new string representing the transformed template.
    *    - `resolve` - `{Object.<string, function>=}` - An optional map of dependencies which should
    *      be injected into the controller. If any of these dependencies are promises, the compiler
    *      will wait for them all to be resolved, or if one is rejected before the controller is
    *      instantiated `compile()` will fail..
    *      * `key` - `{string}`: a name of a dependency to be injected into the controller.
    *      * `factory` - `{string|function}`: If `string` then it is an alias for a service.
    *        Otherwise if function, then it is injected and the return value is treated as the
    *        dependency. If the result is a promise, it is resolved before its value is 
    *        injected into the controller.
    *
    * @returns {object=} promise A promise, which will be resolved with a `compileData` object.
    * `compileData` has the following properties: 
    *
    *   - `element` - `{element}`: an uncompiled element matching the provided template.
    *   - `link` - `{function(scope)}`: A link function, which, when called, will compile
    *     the element and instantiate the provided controller (if given).
    *   - `locals` - `{object}`: The locals which will be passed into the controller once `link` is
    *     called. If `bindToController` is true, they will be coppied to the ctrl instead
    *   - `bindToController` - `bool`: bind the locals to the controller, instead of passing them in
    */
  this.compile = function(options) {
    var templateUrl = options.templateUrl;
    var template = options.template || '';
    var controller = options.controller;
    var controllerAs = options.controllerAs;
    var resolve = options.resolve || {};
    var locals = options.locals || {};
    var transformTemplate = options.transformTemplate || angular.identity;
    var bindToController = options.bindToController;

    // Take resolve values and invoke them.  
    // Resolves can either be a string (value: 'MyRegisteredAngularConst'),
    // or an invokable 'factory' of sorts: (value: function ValueGetter($dependency) {})
    angular.forEach(resolve, function(value, key) {
      if (angular.isString(value)) {
        resolve[key] = $injector.get(value);
      } else {
        resolve[key] = $injector.invoke(value);
      }
    });
    //Add the locals, which are just straight values to inject
    //eg locals: { three: 3 }, will inject three into the controller
    angular.extend(resolve, locals);

    if (templateUrl) {
      resolve.$template = $http.get(templateUrl, {cache: $templateCache})
        .then(function(response) {
          return response.data;
        });
    } else {
      resolve.$template = $q.when(template);
    }

    // Wait for all the resolves to finish if they are promises
    return $q.all(resolve).then(function(locals) {

      var template = transformTemplate(locals.$template);
      var element = angular.element('<div>').html(template.trim()).contents();
      var linkFn = $compile(element);

      //Return a linking function that can be used later when the element is ready
      return {
        locals: locals,
        element: element,
        link: function link(scope) {
          locals.$scope = scope;

          //Instantiate controller if it exists, because we have scope
          if (controller) {
            var ctrl = $controller(controller, locals);
            if (bindToController) {
              angular.extend(ctrl, locals);
            }
            //See angular-route source for this logic
            element.data('$ngControllerController', ctrl);
            element.children().data('$ngControllerController', ctrl);

            if (controllerAs) {
              scope[controllerAs] = ctrl;
            }
          }

          return linkFn(scope);
        }
      };
    });

  };
}
mdCompilerService.$inject = ["$q", "$http", "$injector", "$compile", "$controller", "$templateCache"];
})();

/*!
 * Angular Material Design
 * https://github.com/angular/material
 * @license MIT
 * v0.7.1
 */
(function() {
'use strict';

/*
 * TODO: Add support for multiple fingers on the `pointer` object (enables pinch gesture)
 */

var START_EVENTS = 'mousedown touchstart pointerdown';
var MOVE_EVENTS = 'mousemove touchmove pointermove';
var END_EVENTS = 'mouseup mouseleave touchend touchcancel pointerup pointercancel';
var HANDLERS;

document.contains || (document.contains = function(node) {
  return document.body.contains(node);
});

// TODO add windows phone to this
var userAgent = navigator.userAgent || navigator.vendor || window.opera;
var isIos = userAgent.match(/iPad/i) || userAgent.match(/iPhone/i) || userAgent.match(/iPod/i);
var isAndroid = userAgent.match(/Android/i);
var shouldHijackClicks = isIos || isAndroid;

if (shouldHijackClicks) {
  document.addEventListener('click', function(ev) {
    // Space/enter on a button, and submit events, can send clicks
    var isKeyClick = ev.clientX === 0 && ev.clientY === 0;
    if (isKeyClick || ev.$material) return;

    // Prevent clicks unless they're sent by material
    ev.preventDefault();
    ev.stopPropagation();
  }, true);
}

angular.element(document)
  .on(START_EVENTS, gestureStart)
  .on(MOVE_EVENTS, gestureMove)
  .on(END_EVENTS, gestureEnd)
  // For testing
  .on('$$mdGestureReset', function() {
    lastPointer = pointer = null;
  });

// The state of the current and previous 'pointer' (user's hand)
var pointer, lastPointer;

function runHandlers(handlerEvent, event) {
  var handler;
  for (var handlerName in HANDLERS) {
    handler = HANDLERS[handlerName];
    if (handlerEvent === 'start') {
      // Run cancel to reset any handlers' state
      handler.cancel();
    }
    handler[handlerEvent](event, pointer);
  }
}

function gestureStart(ev) {
  // If we're already touched down, abort
  if (pointer) return;

  var now = +Date.now();

  // iOS & old android bug: after a touch event, a click event is sent 350 ms later.
  // If <400ms have passed, don't allow an event of a different type than the previous event
  if (lastPointer && !typesMatch(ev, lastPointer) && (now - lastPointer.endTime < 1500)) {
    return;
  }

  pointer = makeStartPointer(ev);

  runHandlers('start', ev);
}

function gestureMove(ev) {
  if (!pointer || !typesMatch(ev, pointer)) return;

  updatePointerState(ev, pointer);
  runHandlers('move', ev);
}

function gestureEnd(ev) {
  if (!pointer || !typesMatch(ev, pointer)) return;

  updatePointerState(ev, pointer);
  pointer.endTime = +Date.now();

  runHandlers('end', ev);

  lastPointer = pointer;
  pointer = null;
}

/******** Helpers *********/
function typesMatch(ev, pointer) {
  return ev && pointer && ev.type.charAt(0) === pointer.type;
}

function getEventPoint(ev) {
  ev = ev.originalEvent || ev; // support jQuery events
  return (ev.touches && ev.touches[0]) ||
    (ev.changedTouches && ev.changedTouches[0]) ||
    ev;
}

function updatePointerState(ev, pointer) {
  var point = getEventPoint(ev);
  var x = pointer.x = point.pageX;
  var y = pointer.y = point.pageY;

  pointer.distanceX = x - pointer.startX;
  pointer.distanceY = y - pointer.startY;
  pointer.distance = Math.sqrt(
    pointer.distanceX * pointer.distanceX + pointer.distanceY * pointer.distanceY
  );

  pointer.directionX = pointer.distanceX > 0 ? 'right' : pointer.distanceX < 0 ? 'left' : '';
  pointer.directionY = pointer.distanceY > 0 ? 'up' : pointer.distanceY < 0 ? 'down' : '';

  pointer.duration = +Date.now() - pointer.startTime;
  pointer.velocityX = pointer.distanceX / pointer.duration;
  pointer.velocityY = pointer.distanceY / pointer.duration;
}


function makeStartPointer(ev) {
  var point = getEventPoint(ev);
  var startPointer = {
    startTime: +Date.now(),
    target: ev.target,
    // 'p' for pointer, 'm' for mouse, 't' for touch
    type: ev.type.charAt(0)
  };
  startPointer.startX = startPointer.x = point.pageX;
  startPointer.startY = startPointer.y = point.pageY;
  return startPointer;
}

angular.module('material.core')
.run(["$mdGesture", function($mdGesture) {}]) // make sure $mdGesture is always instantiated
.factory('$mdGesture', ["$$MdGestureHandler", "$$rAF", "$timeout", function($$MdGestureHandler, $$rAF, $timeout) {
  HANDLERS = {};

  if (shouldHijackClicks) {
    addHandler('click', {
      options: {
        maxDistance: 8
      },
      onEnd: function(ev, pointer) {
        if (ev.target) {
          var target = $(ev.target),
              isDisabled = target.prop('disabled'),
              targetParent = target.parent(),
              isButton = targetParent.is('button') || target.is('button');
          if (!isDisabled) {
            isDisabled = targetParent.prop('disabled');
          }
          if (isDisabled && isButton) {
            return;
          }
        }
        if (pointer.distance < this.state.options.maxDistance) {
          this.dispatchEvent(ev, 'click');
        }
      }
    });
  }

  addHandler('press', {
    onStart: function(ev, pointer) {
      this.dispatchEvent(ev, '$md.pressdown');
    },
    onEnd: function(ev, pointer) {
      this.dispatchEvent(ev, '$md.pressup');
    }
  });


  addHandler('hold', {
    options: {
      // If the user keeps his finger within the same <maxDistance> area for
      // <delay> ms, dispatch a hold event.
      maxDistance: 6,
      delay: 500,
    },
    onCancel: function() {
      $timeout.cancel(this.state.timeout);
    },
    onStart: function(ev, pointer) {
      // For hold, require a parent to be registered with $mdGesture.register()
      // Because we prevent scroll events, this is necessary.
      if (!this.state.registeredParent) return this.cancel();

      this.state.pos = {x: pointer.x, y: pointer.y};
      this.state.timeout = $timeout(angular.bind(this, function holdDelayFn() {
        this.dispatchEvent(ev, '$md.hold');
        this.cancel(); //we're done!
      }), this.state.options.delay, false);
    },
    onMove: function(ev, pointer) {
      // Don't scroll while waiting for hold
      ev.preventDefault();
      var dx = this.state.pos.x - pointer.x;
      var dy = this.state.pos.y - pointer.y;
      if (Math.sqrt(dx*dx + dy*dy) > this.options.maxDistance) {
        this.cancel();
      }
    },
    onEnd: function(ev, pointer) {
      this.onCancel();
    },
  });

  addHandler('drag', {
    options: {
      minDistance: 6,
      horizontal: true,
    },
    onStart: function(ev) {
      // For drag, require a parent to be registered with $mdGesture.register()
      if (!this.state.registeredParent) this.cancel();
    },
    onMove: function(ev, pointer) {
      var shouldStartDrag, shouldCancel;
      // Don't allow touch events to scroll while we're dragging or
      // deciding if this touchmove is a proper drag
      ev.preventDefault();

      if (!this.state.dragPointer) {
        if (this.state.options.horizontal) {
          shouldStartDrag = Math.abs(pointer.distanceX) > this.state.options.minDistance;
          shouldCancel = Math.abs(pointer.distanceY) > this.state.options.minDistance * 1.5;
        } else {
          shouldStartDrag = Math.abs(pointer.distanceY) > this.state.options.minDistance;
          shouldCancel = Math.abs(pointer.distanceX) > this.state.options.minDistance * 1.5;
        }

        if (shouldStartDrag) {
          // Create a new pointer, starting at this point where the drag started.
          this.state.dragPointer = makeStartPointer(ev);
          updatePointerState(ev, this.state.dragPointer);
          this.dispatchEvent(ev, '$md.dragstart', this.state.dragPointer);

        } else if (shouldCancel) {
          this.cancel();
        }
      } else {
        this.dispatchDragMove(ev);
      }
    },
    // Only dispatch these every frame; any more is unnecessray
    dispatchDragMove: $$rAF.throttle(function(ev) {
      // Make sure the drag didn't stop while waiting for the next frame
      if (this.state.isRunning) {
        updatePointerState(ev, this.state.dragPointer);
        this.dispatchEvent(ev, '$md.drag', this.state.dragPointer);
      }
    }),
    onEnd: function(ev, pointer) {
      if (this.state.dragPointer) {
        updatePointerState(ev, this.state.dragPointer);
        this.dispatchEvent(ev, '$md.dragend', this.state.dragPointer);
      }
    }
  });

  addHandler('swipe', {
    options: {
      minVelocity: 0.65,
      minDistance: 10,
    },
    onEnd: function(ev, pointer) {
      if (Math.abs(pointer.velocityX) > this.state.options.minVelocity &&
          Math.abs(pointer.distanceX) > this.state.options.minDistance) {
        var eventType = pointer.directionX == 'left' ? '$md.swipeleft' : '$md.swiperight';
        this.dispatchEvent(ev, eventType);
      }
    }
  });

  var self;
  return self = {
    handler: addHandler,
    register: register
  };

  function addHandler(name, definition) {
    var handler = new $$MdGestureHandler(name);
    angular.extend(handler, definition);
    HANDLERS[name] = handler;
    return self;
  }

  function register(element, handlerName, options) {
    var handler = HANDLERS[ handlerName.replace(/^\$md./, '') ];
    if (!handler) {
      throw new Error('Failed to register element with handler ' + handlerName + '. ' +
                      'Available handlers: ' + Object.keys(HANDLERS).join(', '));
    }
    return handler.registerElement(element, options);
  }
}])
.factory('$$MdGestureHandler', ["$$rAF", function($$rAF) {

  function GestureHandler(name) {
    this.name = name;
    this.state = {};
  }
  GestureHandler.prototype = {
    onStart: angular.noop,
    onMove: angular.noop,
    onEnd: angular.noop,
    onCancel: angular.noop,
    options: {},

    dispatchEvent: typeof window.jQuery !== 'undefined' && angular.element === window.jQuery ?
      jQueryDispatchEvent :
      nativeDispatchEvent,

    start: function(ev, pointer) {
      if (this.state.isRunning) return;
      var parentTarget = this.getNearestParent(ev.target);
      var parentTargetOptions = parentTarget && parentTarget.$mdGesture[this.name] || {};

      this.state = {
        isRunning: true,
        options: angular.extend({}, this.options, parentTargetOptions),
        registeredParent: parentTarget
      };
      this.onStart(ev, pointer);
    },
    move: function(ev, pointer) {
      if (!this.state.isRunning) return;
      this.onMove(ev, pointer);
    },
    end: function(ev, pointer) {
      if (!this.state.isRunning) return;
      this.onEnd(ev, pointer);
      this.state.isRunning = false;
    },
    cancel: function(ev, pointer) {
      this.onCancel(ev, pointer);
      this.state = {};
    },

    // Find and return the nearest parent element that has been registered via
    // $mdGesture.register(element, 'handlerName').
    getNearestParent: function(node) {
      var current = node;
      while (current) {
        if ( (current.$mdGesture || {})[this.name] ) {
          return current;
        }
        current = current.parentNode;
      }
    },

    registerElement: function(element, options) {
      var self = this;
      element[0].$mdGesture = element[0].$mdGesture || {};
      element[0].$mdGesture[this.name] = options || {};
      element.on('$destroy', onDestroy);

      return onDestroy;

      function onDestroy() {
        delete element[0].$mdGesture[self.name];
        element.off('$destroy', onDestroy);
      }
    },
  };

  function jQueryDispatchEvent(srcEvent, eventType, eventPointer) {
    eventPointer = eventPointer || pointer;
    var eventObj = new angular.element.Event(eventType)

    eventObj.$material = true;
    eventObj.pointer = eventPointer;
    eventObj.srcEvent = srcEvent;

    angular.extend(eventObj, {
      clientX: eventPointer.x,
      clientY: eventPointer.y,
      screenX: eventPointer.x,
      screenY: eventPointer.y,
      pageX: eventPointer.x,
      pageY: eventPointer.y,
      ctrlKey: srcEvent.ctrlKey,
      altKey: srcEvent.altKey,
      shiftKey: srcEvent.shiftKey,
      metaKey: srcEvent.metaKey
    });
    angular.element(eventPointer.target).trigger(eventObj);
  }

  /*
   * NOTE: nativeDispatchEvent is very performance sensitive.
   */
  function nativeDispatchEvent(srcEvent, eventType, eventPointer) {
    eventPointer = eventPointer || pointer;
    var eventObj;

    if (eventType === 'click') {
      eventObj = document.createEvent('MouseEvents');
      eventObj.initMouseEvent(
        'click', true, true, window, srcEvent.detail,
        eventPointer.x, eventPointer.y, eventPointer.x, eventPointer.y,
        srcEvent.ctrlKey, srcEvent.altKey, srcEvent.shiftKey, srcEvent.metaKey,
        srcEvent.button, srcEvent.relatedTarget || null
      );

    } else {
      eventObj = document.createEvent('CustomEvent');
      eventObj.initCustomEvent(eventType, true, true, {});
    }
    eventObj.$material = true;
    eventObj.pointer = eventPointer;
    eventObj.srcEvent = srcEvent;
    eventPointer.target.dispatchEvent(eventObj);
  }

  return GestureHandler;
}]);

})();
/*!
 * Angular Material Design
 * https://github.com/angular/material
 * @license MIT
 * v0.7.1
 */
(function() {
'use strict';

angular.module('material.core')
  .provider('$$interimElement', InterimElementProvider);

/*
 * @ngdoc service
 * @name $$interimElement
 * @module material.core
 *
 * @description
 *
 * Factory that contructs `$$interimElement.$service` services.
 * Used internally in material design for elements that appear on screen temporarily.
 * The service provides a promise-like API for interacting with the temporary
 * elements.
 *
 * ```js
 * app.service('$mdToast', function($$interimElement) {
 *   var $mdToast = $$interimElement(toastDefaultOptions);
 *   return $mdToast;
 * });
 * ```
 * @param {object=} defaultOptions Options used by default for the `show` method on the service.
 *
 * @returns {$$interimElement.$service}
 *
 */

function InterimElementProvider() {
  createInterimElementProvider.$get = InterimElementFactory;
  InterimElementFactory.$inject = ["$document", "$q", "$rootScope", "$timeout", "$rootElement", "$animate", "$interpolate", "$mdCompiler", "$mdTheming"];
  return createInterimElementProvider;

  /**
   * Returns a new provider which allows configuration of a new interimElement
   * service. Allows configuration of default options & methods for options,
   * as well as configuration of 'preset' methods (eg dialog.basic(): basic is a preset method)
   */
  function createInterimElementProvider(interimFactoryName) {
    var EXPOSED_METHODS = ['onHide', 'onShow', 'onRemove'];
    var providerConfig = {
      presets: {}
    };
    var provider = {
      setDefaults: setDefaults,
      addPreset: addPreset,
      $get: factory
    };

    /**
     * all interim elements will come with the 'build' preset
     */
    provider.addPreset('build', {
      methods: ['controller', 'controllerAs', 'resolve',
        'template', 'templateUrl', 'themable', 'transformTemplate', 'parent']
    });

    factory.$inject = ["$$interimElement", "$animate", "$injector"];
    return provider;

    /**
     * Save the configured defaults to be used when the factory is instantiated
     */
    function setDefaults(definition) {
      providerConfig.optionsFactory = definition.options;
      providerConfig.methods = (definition.methods || []).concat(EXPOSED_METHODS);
      return provider;
    }

    /**
     * Save the configured preset to be used when the factory is instantiated
     */
    function addPreset(name, definition) {
      definition = definition || {};
      definition.methods = definition.methods || [];
      definition.options = definition.options || function() { return {}; };

      if (/^cancel|hide|show$/.test(name)) {
        throw new Error("Preset '" + name + "' in " + interimFactoryName + " is reserved!");
      }
      if (definition.methods.indexOf('_options') > -1) {
        throw new Error("Method '_options' in " + interimFactoryName + " is reserved!");
      }
      providerConfig.presets[name] = {
        methods: definition.methods.concat(EXPOSED_METHODS),
        optionsFactory: definition.options,
        argOption: definition.argOption
      };
      return provider;
    }

    /**
     * Create a factory that has the given methods & defaults implementing interimElement
     */
    /* @ngInject */
    function factory($$interimElement, $animate, $injector) {
      var defaultMethods;
      var defaultOptions;
      var interimElementService = $$interimElement();

      /*
       * publicService is what the developer will be using.
       * It has methods hide(), cancel(), show(), build(), and any other
       * presets which were set during the config phase.
       */
      var publicService = {
        hide: interimElementService.hide,
        cancel: interimElementService.cancel,
        show: showInterimElement
      };

      defaultMethods = providerConfig.methods || [];
      // This must be invoked after the publicService is initialized
      defaultOptions = invokeFactory(providerConfig.optionsFactory, {});

      angular.forEach(providerConfig.presets, function(definition, name) {
        var presetDefaults = invokeFactory(definition.optionsFactory, {});
        var presetMethods = (definition.methods || []).concat(defaultMethods);

        // Every interimElement built with a preset has a field called `$type`,
        // which matches the name of the preset.
        // Eg in preset 'confirm', options.$type === 'confirm'
        angular.extend(presetDefaults, { $type: name });

        // This creates a preset class which has setter methods for every
        // method given in the `.addPreset()` function, as well as every
        // method given in the `.setDefaults()` function.
        //
        // @example
        // .setDefaults({
        //   methods: ['hasBackdrop', 'clickOutsideToClose', 'escapeToClose', 'targetEvent'],
        //   options: dialogDefaultOptions
        // })
        // .addPreset('alert', {
        //   methods: ['title', 'ok'],
        //   options: alertDialogOptions
        // })
        //
        // Set values will be passed to the options when interimElemnt.show() is called.
        function Preset(opts) {
          this._options = angular.extend({}, presetDefaults, opts);
        }
        angular.forEach(presetMethods, function(name) {
          Preset.prototype[name] = function(value) {
            this._options[name] = value;
            return this;
          };
        });

        // Create shortcut method for one-linear methods
        if (definition.argOption) {
          var methodName = 'show' + name.charAt(0).toUpperCase() + name.slice(1);
          publicService[methodName] = function(arg) {
            var config = publicService[name](arg);
            return publicService.show(config);
          };
        }

        // eg $mdDialog.alert() will return a new alert preset
        publicService[name] = function(arg) {
          // If argOption is supplied, eg `argOption: 'content'`, then we assume
          // if the argument is not an options object then it is the `argOption` option.
          //
          // @example `$mdToast.simple('hello')` // sets options.content to hello
          //                                     // because argOption === 'content'
          if (arguments.length && definition.argOption && !angular.isObject(arg) &&
              !angular.isArray(arg)) {
            return (new Preset())[definition.argOption](arg);
          } else {
            return new Preset(arg);
          }

        };
      });

      return publicService;

      function showInterimElement(opts) {
        // opts is either a preset which stores its options on an _options field,
        // or just an object made up of options
        if (opts && opts._options) opts = opts._options;
        return interimElementService.show(
          angular.extend({}, defaultOptions, opts)
        );
      }

      /**
       * Helper to call $injector.invoke with a local of the factory name for
       * this provider.
       * If an $mdDialog is providing options for a dialog and tries to inject
       * $mdDialog, a circular dependency error will happen.
       * We get around that by manually injecting $mdDialog as a local.
       */
      function invokeFactory(factory, defaultVal) {
        var locals = {};
        locals[interimFactoryName] = publicService;
        return $injector.invoke(factory || function() { return defaultVal; }, {}, locals);
      }

    }

  }

  /* @ngInject */
  function InterimElementFactory($document, $q, $rootScope, $timeout, $rootElement, $animate,
                                 $interpolate, $mdCompiler, $mdTheming ) {
    var startSymbol = $interpolate.startSymbol(),
        endSymbol = $interpolate.endSymbol(),
        usesStandardSymbols = ((startSymbol === '{{') && (endSymbol === '}}')),
        processTemplate  = usesStandardSymbols ? angular.identity : replaceInterpolationSymbols;

    return function createInterimElementService() {
      /*
       * @ngdoc service
       * @name $$interimElement.$service
       *
       * @description
       * A service used to control inserting and removing an element into the DOM.
       *
       */
      var stack = [];
      var service;
      return service = {
        show: show,
        hide: hide,
        cancel: cancel
      };

      /*
       * @ngdoc method
       * @name $$interimElement.$service#show
       * @kind function
       *
       * @description
       * Adds the `$interimElement` to the DOM and returns a promise that will be resolved or rejected
       * with hide or cancel, respectively.
       *
       * @param {*} options is hashMap of settings
       * @returns a Promise
       *
       */
      function show(options) {
        options.zIndex = 80 + stack.length;
        var interimElement = new InterimElement(options);

        stack.unshift(interimElement);
        return interimElement.show().then(function() {
          return interimElement.deferred.promise;
        });
      }

      /*
       * @ngdoc method
       * @name $$interimElement.$service#hide
       * @kind function
       *
       * @description
       * Removes the `$interimElement` from the DOM and resolves the promise returned from `show`
       *
       * @param {*} resolveParam Data to resolve the promise with
       * @returns a Promise that will be resolved after the element has been removed.
       *
       */
      function hide(response, interimElementAt) {
        var interimElement;
        if (interimElementAt !== undefined) {
          interimElement = interimElementAt;
          stack.splice(stack.indexOf(interimElementAt), 1);
        } else {
          interimElement = stack.shift();
        }
        interimElement && interimElement.remove().then(function() {
          interimElement.deferred.resolve(response);
        });

        return interimElement ? interimElement.deferred.promise : $q.when(response);
      }

      /*
       * @ngdoc method
       * @name $$interimElement.$service#cancel
       * @kind function
       *
       * @description
       * Removes the `$interimElement` from the DOM and rejects the promise returned from `show`
       *
       * @param {*} reason Data to reject the promise with
       * @returns Promise that will be rejected after the element has been removed.
       *
       */
      function cancel(reason, interimElementAt) {
        var interimElement;
        if (interimElementAt !== undefined) {
          interimElement = interimElementAt;
          stack.splice(stack.indexOf(interimElementAt), 1);
        } else {
          interimElement = stack.shift();
        }
        interimElement && interimElement.remove().then(function() {
          interimElement.deferred.reject(reason);
        });

        return interimElement ? interimElement.deferred.promise : $q.reject(reason);
      }


      /*
       * Internal Interim Element Object
       * Used internally to manage the DOM element and related data
       */
      function InterimElement(options) {
        var self;
        var hideTimeout, element;

        options = options || {};
        options = angular.extend({
          scope: options.scope || $rootScope.$new(options.isolateScope),
          onShow: function(scope, element, options) {
            return $animate.enter(element, options.parent);
          },
          onRemove: function(scope, element, options) {
            // Element could be undefined if a new element is shown before
            // the old one finishes compiling.
            return element && $animate.leave(element) || $q.when();
          }
        }, options);

        if (options.template) {
          options.template = processTemplate(options.template);
        }

        self = {
          options: options,
          deferred: $q.defer(),
          show: function() {
            return $mdCompiler.compile(options).then(function(compileData) {
              angular.extend(compileData.locals, self.options);

              // Search for parent at insertion time, if not specified
              if (angular.isString(options.parent)) {
                options.parent = angular.element($document[0].querySelector(options.parent));
              } else if (!options.parent) {
                options.parent = $rootElement.find('body');
                if (!options.parent.length) options.parent = $rootElement;
              }

              element = compileData.link(options.scope);
              element.css('z-index', options.zIndex);
              if (options.themable) $mdTheming(element);
              var ret = options.onShow(options.scope, element, options);
              return $q.when(ret)
                .then(function(){
                  // Issue onComplete callback when the `show()` finishes
                  (options.onComplete || angular.noop)(options.scope, element, options);
                  startHideTimeout();
                });

              function startHideTimeout() {
                if (options.hideDelay) {
                  hideTimeout = $timeout(service.cancel, options.hideDelay) ;
                }
              }
            });
          },
          cancelTimeout: function() {
            if (hideTimeout) {
              $timeout.cancel(hideTimeout);
              hideTimeout = undefined;
            }
          },
          remove: function() {
            self.cancelTimeout();
            var ret = options.onRemove(options.scope, element, options);
            return $q.when(ret).then(function() {
              options.scope.$destroy();
            });
          }
        };

        options.interimElement = self;
        options.stack = stack;

        return self;
      }
    };

    /*
     * Replace `{{` and `}}` in a string (usually a template) with the actual start-/endSymbols used
     * for interpolation. This allows pre-defined templates (for components such as dialog, toast etc)
     * to continue to work in apps that use custom interpolation start-/endSymbols.
     *
     * @param {string} text The text in which to replace `{{` / `}}`
     * @returns {string} The modified string using the actual interpolation start-/endSymbols
     */
    function replaceInterpolationSymbols(text) {
      if (!text || !angular.isString(text)) return text;
      return text.replace(/\{\{/g, startSymbol).replace(/}}/g, endSymbol);
    }
  }

}

})();
/*!
 * Angular Material Design
 * https://github.com/angular/material
 * @license MIT
 * v0.7.1
 */
(function() {
'use strict';

angular.module('material.core')
  .provider('$$interimStackableElement', InterimElementProvider);

/*
 * @ngdoc service
 * @name $$interimStackableElement
 * @module material.core
 *
 * @description
 *
 * Factory that contructs `$$interimStackableElement.$service` services.
 * Used internally in material design for elements that appear on screen temporarily.
 * The service provides a promise-like API for interacting with the temporary
 * elements.
 *
 * ```js
 * app.service('$mdToast', function($$interimStackableElement) {
 *   var $mdToast = $$interimStackableElement(toastDefaultOptions);
 *   return $mdToast;
 * });
 * ```
 * @param {object=} defaultOptions Options used by default for the `show` method on the service.
 *
 * @returns {$$interimStackableElement.$service}
 *
 */

function InterimElementProvider() {
  createInterimElementProvider.$get = InterimElementFactory;
  InterimElementFactory.$inject = ["$document", "$q", "$rootScope", "$timeout", "$rootElement", "$animate", "$interpolate", "$mdCompiler", "$mdTheming"];
  return createInterimElementProvider;

  /**
   * Returns a new provider which allows configuration of a new interimElement
   * service. Allows configuration of default options & methods for options,
   * as well as configuration of 'preset' methods (eg dialog.basic(): basic is a preset method)
   */
  function createInterimElementProvider(interimFactoryName) {
    var EXPOSED_METHODS = ['onHide', 'onShow', 'onRemove'];
    var providerConfig = {
      presets: {}
    };
    var provider = {
      setDefaults: setDefaults,
      addPreset: addPreset,
      $get: factory
    };

    /**
     * all interim elements will come with the 'build' preset
     */
    provider.addPreset('build', {
      methods: ['controller', 'controllerAs', 'resolve',
        'template', 'templateUrl', 'themable', 'transformTemplate', 'parent']
    });

    factory.$inject = ["$$interimStackableElement", "$animate", "$injector"];
    return provider;

    /**
     * Save the configured defaults to be used when the factory is instantiated
     */
    function setDefaults(definition) {
      providerConfig.optionsFactory = definition.options;
      providerConfig.methods = (definition.methods || []).concat(EXPOSED_METHODS);
      return provider;
    }

    /**
     * Save the configured preset to be used when the factory is instantiated
     */
    function addPreset(name, definition) {
      definition = definition || {};
      definition.methods = definition.methods || [];
      definition.options = definition.options || function() { return {}; };

      if (/^cancel|hide|show$/.test(name)) {
        throw new Error("Preset '" + name + "' in " + interimFactoryName + " is reserved!");
      }
      if (definition.methods.indexOf('_options') > -1) {
        throw new Error("Method '_options' in " + interimFactoryName + " is reserved!");
      }
      providerConfig.presets[name] = {
        methods: definition.methods.concat(EXPOSED_METHODS),
        optionsFactory: definition.options,
        argOption: definition.argOption
      };
      return provider;
    }

    /**
     * Create a factory that has the given methods & defaults implementing interimElement
     */
    /* @ngInject */
    function factory($$interimStackableElement, $animate, $injector) {
      var defaultMethods;
      var defaultOptions;
      var interimElementService = $$interimStackableElement();

      /*
       * publicService is what the developer will be using.
       * It has methods hide(), cancel(), show(), build(), and any other
       * presets which were set during the config phase.
       */
      var publicService = {
        hide: interimElementService.hide,
        cancel: interimElementService.cancel,
        show: showInterimElement
      };

      defaultMethods = providerConfig.methods || [];
      // This must be invoked after the publicService is initialized
      defaultOptions = invokeFactory(providerConfig.optionsFactory, {});

      angular.forEach(providerConfig.presets, function(definition, name) {
        var presetDefaults = invokeFactory(definition.optionsFactory, {});
        var presetMethods = (definition.methods || []).concat(defaultMethods);

        // Every interimElement built with a preset has a field called `$type`,
        // which matches the name of the preset.
        // Eg in preset 'confirm', options.$type === 'confirm'
        angular.extend(presetDefaults, { $type: name });

        // This creates a preset class which has setter methods for every
        // method given in the `.addPreset()` function, as well as every
        // method given in the `.setDefaults()` function.
        //
        // @example
        // .setDefaults({
        //   methods: ['hasBackdrop', 'clickOutsideToClose', 'escapeToClose', 'targetEvent'],
        //   options: dialogDefaultOptions
        // })
        // .addPreset('alert', {
        //   methods: ['title', 'ok'],
        //   options: alertDialogOptions
        // })
        //
        // Set values will be passed to the options when interimElemnt.show() is called.
        function Preset(opts) {
          this._options = angular.extend({}, presetDefaults, opts);
        }
        angular.forEach(presetMethods, function(name) {
          Preset.prototype[name] = function(value) {
            this._options[name] = value;
            return this;
          };
        });

        // Create shortcut method for one-linear methods
        if (definition.argOption) {
          var methodName = 'show' + name.charAt(0).toUpperCase() + name.slice(1);
          publicService[methodName] = function(arg) {
            var config = publicService[name](arg);
            return publicService.show(config);
          };
        }

        // eg $mdDialog.alert() will return a new alert preset
        publicService[name] = function(arg) {
          // If argOption is supplied, eg `argOption: 'content'`, then we assume
          // if the argument is not an options object then it is the `argOption` option.
          //
          // @example `$mdToast.simple('hello')` // sets options.content to hello
          //                                     // because argOption === 'content'
          if (arguments.length && definition.argOption && !angular.isObject(arg) &&
              !angular.isArray(arg)) {
            return (new Preset())[definition.argOption](arg);
          } else {
            return new Preset(arg);
          }

        };
      });

      return publicService;

      function showInterimElement(opts) {
        // opts is either a preset which stores its options on an _options field,
        // or just an object made up of options
        if (opts && opts._options) opts = opts._options;
        return interimElementService.show(
          angular.extend({}, defaultOptions, opts)
        );
      }

      /**
       * Helper to call $injector.invoke with a local of the factory name for
       * this provider.
       * If an $mdDialog is providing options for a dialog and tries to inject
       * $mdDialog, a circular dependency error will happen.
       * We get around that by manually injecting $mdDialog as a local.
       */
      function invokeFactory(factory, defaultVal) {
        var locals = {};
        locals[interimFactoryName] = publicService;
        return $injector.invoke(factory || function() { return defaultVal; }, {}, locals);
      }

    }

  }

  /* @ngInject */
  function InterimElementFactory($document, $q, $rootScope, $timeout, $rootElement, $animate,
                                 $interpolate, $mdCompiler, $mdTheming ) {
    var startSymbol = $interpolate.startSymbol(),
        endSymbol = $interpolate.endSymbol(),
        usesStandardSymbols = ((startSymbol === '{{') && (endSymbol === '}}')),
        processTemplate  = usesStandardSymbols ? angular.identity : replaceInterpolationSymbols;

    return function createInterimElementService() {
      /*
       * @ngdoc service
       * @name $$interimStackableElement.$service
       *
       * @description
       * A service used to control inserting and removing an element into the DOM.
       *
       */
      var stack = [];
      var service;
      return service = {
        show: show,
        hide: hide,
        cancel: cancel
      };

      /*
       * @ngdoc method
       * @name $$interimStackableElement.$service#show
       * @kind function
       *
       * @description
       * Adds the `$interimElement` to the DOM and returns a promise that will be resolved or rejected
       * with hide or cancel, respectively.
       *
       * @param {*} options is hashMap of settings
       * @returns a Promise
       *
       */
      function show(options) {
        options.zIndex = 80 + stack.length;
        var interimElement = new InterimElement(options);

        stack.unshift(interimElement);
        return interimElement.show().then(function() {
          return interimElement.deferred.promise;
        });
      }

      /*
       * @ngdoc method
       * @name $$interimStackableElement.$service#hide
       * @kind function
       *
       * @description
       * Removes the `$interimElement` from the DOM and resolves the promise returned from `show`
       *
       * @param {*} resolveParam Data to resolve the promise with
       * @returns a Promise that will be resolved after the element has been removed.
       *
       */
      function hide(response, interimElementAt) {
        var interimElement;
        if (interimElementAt !== undefined) {
          interimElement = interimElementAt;
          stack.splice(stack.indexOf(interimElementAt), 1);
        } else {
          interimElement = stack.shift();
        }
        interimElement && interimElement.remove().then(function() {
          interimElement.deferred.resolve(response);
        });

        return interimElement ? interimElement.deferred.promise : $q.when(response);
      }

      /*
       * @ngdoc method
       * @name $$interimStackableElement.$service#cancel
       * @kind function
       *
       * @description
       * Removes the `$interimElement` from the DOM and rejects the promise returned from `show`
       *
       * @param {*} reason Data to reject the promise with
       * @returns Promise that will be rejected after the element has been removed.
       *
       */
      function cancel(reason, interimElementAt) {
        var interimElement;
        if (interimElementAt !== undefined) {
          interimElement = interimElementAt;
          stack.splice(stack.indexOf(interimElementAt), 1);
        } else {
          interimElement = stack.shift();
        }
        interimElement && interimElement.remove().then(function() {
          interimElement.deferred.reject(reason);
        });

        return interimElement ? interimElement.deferred.promise : $q.reject(reason);
      }


      /*
       * Internal Interim Element Object
       * Used internally to manage the DOM element and related data
       */
      function InterimElement(options) {
        var self;
        var hideTimeout, element;

        options = options || {};
        options = angular.extend({
          scope: options.scope || $rootScope.$new(options.isolateScope),
          onShow: function(scope, element, options) {
            return $animate.enter(element, options.parent);
          },
          onRemove: function(scope, element, options) {
            // Element could be undefined if a new element is shown before
            // the old one finishes compiling.
            return element && $animate.leave(element) || $q.when();
          }
        }, options);

        if (options.template) {
          options.template = processTemplate(options.template);
        }

        self = {
          options: options,
          deferred: $q.defer(),
          show: function() {
            return $mdCompiler.compile(options).then(function(compileData) {
              angular.extend(compileData.locals, self.options);

              // Search for parent at insertion time, if not specified
              if (angular.isString(options.parent)) {
                options.parent = angular.element($document[0].querySelector(options.parent));
              } else if (!options.parent) {
                options.parent = $rootElement.find('body');
                if (!options.parent.length) options.parent = $rootElement;
              }

              element = compileData.link(options.scope);
              element.css('z-index', options.zIndex);
              if (options.themable) $mdTheming(element);
              var ret = options.onShow(options.scope, element, options);
              return $q.when(ret)
                .then(function(){
                  // Issue onComplete callback when the `show()` finishes
                  (options.onComplete || angular.noop)(options.scope, element, options);
                  startHideTimeout();
                });

              function startHideTimeout() {
                if (options.hideDelay) {
                  hideTimeout = $timeout(service.cancel, options.hideDelay) ;
                }
              }
            });
          },
          cancelTimeout: function() {
            if (hideTimeout) {
              $timeout.cancel(hideTimeout);
              hideTimeout = undefined;
            }
          },
          remove: function() {
            self.cancelTimeout();
            var ret = options.onRemove(options.scope, element, options);
            return $q.when(ret).then(function() {
              options.scope.$destroy();
            });
          }
        };

        options.interimElement = self;
        options.stack = stack;

        return self;
      }
    };

    /*
     * Replace `{{` and `}}` in a string (usually a template) with the actual start-/endSymbols used
     * for interpolation. This allows pre-defined templates (for components such as dialog, toast etc)
     * to continue to work in apps that use custom interpolation start-/endSymbols.
     *
     * @param {string} text The text in which to replace `{{` / `}}`
     * @returns {string} The modified string using the actual interpolation start-/endSymbols
     */
    function replaceInterpolationSymbols(text) {
      if (!text || !angular.isString(text)) return text;
      return text.replace(/\{\{/g, startSymbol).replace(/}}/g, endSymbol);
    }
  }

}

})();
/*!
 * Angular Material Design
 * https://github.com/angular/material
 * @license MIT
 * v0.7.1
 */
(function() {
  'use strict';

  /**
   * @ngdoc module
   * @name material.core.componentRegistry
   *
   * @description
   * A component instance registration service.
   * Note: currently this as a private service in the SideNav component.
   */
  angular.module('material.core')
    .factory('$mdComponentRegistry', ComponentRegistry);

  /*
   * @private
   * @ngdoc factory
   * @name ComponentRegistry
   * @module material.core.componentRegistry
   *
   */
  function ComponentRegistry($log, $q) {

    var self;
    var instances = [ ];
    var pendings = { };

    return self = {
      /**
       * Used to print an error when an instance for a handle isn't found.
       */
      notFoundError: function(handle) {
        $log.error('No instance found for handle', handle);
      },
      /**
       * Return all registered instances as an array.
       */
      getInstances: function() {
        return instances;
      },

      /**
       * Get a registered instance.
       * @param handle the String handle to look up for a registered instance.
       */
      get: function(handle) {
        if ( !isValidID(handle) ) return null;

        var i, j, instance;
        for(i = 0, j = instances.length; i < j; i++) {
          instance = instances[i];
          if(instance.$$mdHandle === handle) {
            return instance;
          }
        }
        return null;
      },

      /**
       * Register an instance.
       * @param instance the instance to register
       * @param handle the handle to identify the instance under.
       */
      register: function(instance, handle) {
        if ( !handle ) return angular.noop;

        instance.$$mdHandle = handle;
        instances.push(instance);
        resolveWhen();

        return deregister;

        /**
         * Remove registration for an instance
         */
        function deregister() {
          var index = instances.indexOf(instance);
          if (index !== -1) {
            instances.splice(index, 1);
          }
        }

        /**
         * Resolve any pending promises for this instance
         */
        function resolveWhen() {
          var dfd = pendings[handle];
          if ( dfd ) {
            dfd.resolve( instance );
            delete pendings[handle];
          }
        }
      },

      /**
       * Async accessor to registered component instance
       * If not available then a promise is created to notify
       * all listeners when the instance is registered.
       */
      when : function(handle) {
        if ( isValidID(handle) ) {
          var deferred = $q.defer();
          var instance = self.get(handle);

          if ( instance )  {
            deferred.resolve( instance );
          } else {
            pendings[handle] = deferred;
          }

          return deferred.promise;
        }
        return $q.reject("Invalid `md-component-id` value.");
      }

    };

    function isValidID(handle){
      return handle && (handle !== "");
    }

  }
  ComponentRegistry.$inject = ["$log", "$q"];


})();

/*!
 * Angular Material Design
 * https://github.com/angular/material
 * @license MIT
 * v0.7.1
 */
(function() {
'use strict';

angular.module('material.core')
  .factory('$mdInkRipple', InkRippleService)
  .directive('mdInkRipple', InkRippleDirective)
  .directive('mdNoInk', attrNoDirective())
  .directive('mdNoBar', attrNoDirective())
  .directive('mdNoStretch', attrNoDirective());

function InkRippleDirective($mdInkRipple, $parse) {
  return {
    controller: angular.noop,
    link: function (scope, element, attr) {
      if (attr.hasOwnProperty('mdInkRippleCheckbox')) {
        $mdInkRipple.attachCheckboxBehavior(scope, element);
      } else {
        $mdInkRipple.attachButtonBehavior(scope, element);
      }
    }
  };
}
InkRippleDirective.$inject = ["$mdInkRipple", "$parse"];

function InkRippleService($window, $timeout, $parse) {

  return {
    attachButtonBehavior: attachButtonBehavior,
    attachCheckboxBehavior: attachCheckboxBehavior,
    attachTabBehavior: attachTabBehavior,
    attach: attach
  };

  function attachButtonBehavior(scope, element, options) {
    return attach(scope, element, angular.extend({
      isFAB: element.hasClass('md-fab'),
      isMenuItem: element.hasClass('md-menu-item'),
      center: false,
      dimBackground: true
    }, options));
  }

  function attachCheckboxBehavior(scope, element, options) {
    return attach(scope, element, angular.extend({
      center: true,
      dimBackground: false,
      fitRipple: true
    }, options));
  }

  function attachTabBehavior(scope, element, options) {
    return attach(scope, element, angular.extend({
      center: false,
      dimBackground: true,
      outline: true
    }, options));
  }

  function attach(scope, element, options) {
    if (element.controller('mdNoInk')) return angular.noop;

    var ignore = element.attr('md-ink-ripple-ignore');

    ignore = (ignore ? $parse(ignore)(scope) : undefined);

    options = angular.extend({
      colorElement: element,
      mousedown: true,
      hover: true,
      focus: true,
      center: false,
      mousedownPauseTime: 150,
      dimBackground: false,
      outline: false,
      isFAB: false,
      isMenuItem: false,
      fitRipple: false
    }, options);

    var rippleSize,
        controller = element.controller('mdInkRipple') || {},
        counter = 0,
        ripples = [],
        states = [],
        isActiveExpr = element.attr('md-highlight'),
        isActive = false,
        isHeld = false,
        node = element[0],
        rippleSizeSetting = element.attr('md-ripple-size'),
        color = parseColor(element.attr('md-ink-ripple')) || parseColor($window.getComputedStyle(options.colorElement[0]).color || 'rgb(0, 0, 0)');

    switch (rippleSizeSetting) {
      case 'full':
        options.isFAB = true;
        break;
      case 'partial':
        options.isFAB = false;
        break;
    }

    // expose onInput for ripple testing
    if (options.mousedown) {
      element.on('$md.pressdown', onPressDown)
        .on('$md.pressup', onPressUp);
    }

    controller.createRipple = createRipple;

    if (isActiveExpr) {
      scope.$watch(isActiveExpr, function watchActive(newValue) {
        isActive = newValue;
        if (isActive && !ripples.length) {
          $timeout(function () { createRipple(0, 0); }, 0, false);
        }
        angular.forEach(ripples, updateElement);
      });
    }

    // Publish self-detach method if desired...
    return function detach() {
      element.off('$md.pressdown', onPressDown)
        .off('$md.pressup', onPressUp);
      getRippleContainer().remove();
    };

    /**
     * Gets the current ripple container
     * If there is no ripple container, it creates one and returns it
     *
     * @returns {angular.element} ripple container element
     */
    function getRippleContainer() {
      var container = element.data('$mdRippleContainer');
      if (container) return container;
      container = angular.element('<div class="md-ripple-container">');
      element.append(container);
      element.data('$mdRippleContainer', container);
      return container;
    }

    function parseColor(color) {
      if (!color) return;
      if (color.indexOf('rgba') === 0) return color.replace(/\d?\.?\d*\s*\)\s*$/, '0.1)');
      if (color.indexOf('rgb')  === 0) return rgbToRGBA(color);
      if (color.indexOf('#')    === 0) return hexToRGBA(color);

      /**
       * Converts a hex value to an rgba string
       *
       * @param {string} hex value (3 or 6 digits) to be converted
       *
       * @returns {string} rgba color with 0.1 alpha
       */
      function hexToRGBA(color) {
        var hex = color.charAt(0) === '#' ? color.substr(1) : color,
          dig = hex.length / 3,
          red = hex.substr(0, dig),
          grn = hex.substr(dig, dig),
          blu = hex.substr(dig * 2);
        if (dig === 1) {
          red += red;
          grn += grn;
          blu += blu;
        }
        return 'rgba(' + parseInt(red, 16) + ',' + parseInt(grn, 16) + ',' + parseInt(blu, 16) + ',0.1)';
      }

      /**
       * Converts rgb value to rgba string
       *
       * @param {string} rgb color string
       *
       * @returns {string} rgba color with 0.1 alpha
       */
      function rgbToRGBA(color) {
        return color.replace(')', ', 0.1)').replace('(', 'a(');
      }

    }

    function removeElement(elem, wait) {
      ripples.splice(ripples.indexOf(elem), 1);
      if (ripples.length === 0) {
        getRippleContainer().css({ backgroundColor: '' });
      }
      $timeout(function () { elem.remove(); }, wait, false);
    }

    function updateElement(elem) {
      var index = ripples.indexOf(elem),
          state = states[index] || {},
          elemIsActive = ripples.length > 1 ? false : isActive,
          elemIsHeld   = ripples.length > 1 ? false : isHeld;
      if (elemIsActive || state.animating || elemIsHeld) {
        elem.addClass('md-ripple-visible');
      } else if (elem) {
        elem.removeClass('md-ripple-visible');
        if (options.outline) {
          elem.css({
            width: rippleSize + 'px',
            height: rippleSize + 'px',
            marginLeft: (rippleSize * -1) + 'px',
            marginTop: (rippleSize * -1) + 'px'
          });
        }
        removeElement(elem, options.outline ? 450 : 650);
      }
    }

    /**
     * Creates a ripple at the provided coordinates
     *
     * @param {number} left cursor position
     * @param {number} top cursor position
     *
     * @returns {angular.element} the generated ripple element
     */
    function createRipple(left, top) {

      color = parseColor(element.attr('md-ink-ripple')) || parseColor($window.getComputedStyle(options.colorElement[0]).color || 'rgb(0, 0, 0)');

      var container = getRippleContainer(),
          size = getRippleSize(left, top),
          css = getRippleCss(size, left, top),
          elem = getRippleElement(css),
          index = ripples.indexOf(elem),
          state = states[index] || {};

      rippleSize = size;

      state.animating = true;

      $timeout(function () {
        if (options.dimBackground) {
          container.css({ backgroundColor: color });
        }
        elem.addClass('md-ripple-placed md-ripple-scaled');
        if (options.outline) {
          elem.css({
            borderWidth: (size * 0.5) + 'px',
            marginLeft: (size * -0.5) + 'px',
            marginTop: (size * -0.5) + 'px'
          });
        } else {
          if (options.moveToCenter === undefined || options.moveToCenter) {
            elem.css({ left: '50%', top: '50%' });
          }
        }
        updateElement(elem);
        $timeout(function () {
          state.animating = false;
          updateElement(elem);
        }, (options.outline ? 450 : 225), false);
      }, 0, false);

      return elem;

      /**
       * Creates the ripple element with the provided css
       *
       * @param {object} css properties to be applied
       *
       * @returns {angular.element} the generated ripple element
       */
      function getRippleElement(css) {
        var elem = angular.element('<div class="md-ripple" data-counter="' + counter++ + '">');
        ripples.unshift(elem);
        states.unshift({ animating: true });
        container.append(elem);
        css && elem.css(css);
        return elem;
      }

      /**
       * Calculate the ripple size
       *
       * @returns {number} calculated ripple diameter
       */
      function getRippleSize(left, top) {
        var width = container.prop('offsetWidth'),
            height = container.prop('offsetHeight'),
            multiplier, size, rect;
        if (options.isMenuItem) {
          size = Math.sqrt(Math.pow(width, 2) + Math.pow(height, 2));
        } else if (options.outline) {
          rect = node.getBoundingClientRect();
          left -= rect.left;
          top -= rect.top;
          width = Math.max(left, width - left);
          height = Math.max(top, height - top);
          size = 2 * Math.sqrt(Math.pow(width, 2) + Math.pow(height, 2));
        } else {
          multiplier = options.isFAB ? 1.1 : (angular.isDefined(options.multiplier) ?options.multiplier : 0.8);
          size = Math.sqrt(Math.pow(width, 2) + Math.pow(height, 2)) * multiplier;
          if (options.fitRipple) {
            size = Math.min(height, width, size);
          }
        }
        return size;
      }

      /**
       * Generates the ripple css
       *
       * @param {number} the diameter of the ripple
       * @param {number} the left cursor offset
       * @param {number} the top cursor offset
       *
       * @returns {{backgroundColor: *, width: string, height: string, marginLeft: string, marginTop: string}}
       */
      function getRippleCss(size, left, top) {
        var rect,
            css = {
              backgroundColor: rgbaToRGB(color),
              borderColor: rgbaToRGB(color),
              width: size + 'px',
              height: size + 'px'
            };

        if (options.outline) {
          css.width = 0;
          css.height = 0;
        } else {
          css.marginLeft = css.marginTop = (size * -0.5) + 'px';
        }

        if (options.center) {
          css.left = css.top = '50%';
        } else {
          rect = node.getBoundingClientRect();
          css.left = Math.round((left - rect.left) / container.prop('offsetWidth') * 100) + '%';
          css.top = Math.round((top - rect.top) / container.prop('offsetHeight') * 100) + '%';
        }

        return css;

        /**
         * Converts rgba string to rgb, removing the alpha value
         *
         * @param {string} rgba color
         *
         * @returns {string} rgb color
         */
        function rgbaToRGB(color) {
          return color.replace('rgba', 'rgb').replace(/,[^\)\,]+\)/, ')');
        }
      }
    }

    /**
     * Handles user input start and stop events
     *
     */
    function onPressDown(ev) {
      if (!isRippleAllowed()) return;

      if (ignore && ev.target) {
        var target = $(ev.target),
            skip = false;
        angular.forEach(ignore, function (ig) {
          if (target.is(ig) || target.parent().is(ig)) {
            skip = true;
          }
        });
        if (skip) {
          return;
        }
      }

      var ripple = createRipple(ev.pointer.x, ev.pointer.y);
      isHeld = true;
    }
    function onPressUp(ev) {
      isHeld = false;
      var ripple = ripples[ ripples.length - 1 ];
      $timeout(function () { updateElement(ripple); }, 0, false);
    }

    /**
     * Determines if the ripple is allowed
     *
     * @returns {boolean} true if the ripple is allowed, false if not
     */
    function isRippleAllowed() {
      var parent = node.parentNode;
      var grandparent = parent && parent.parentNode;
      var ancestor = grandparent && grandparent.parentNode;
      return !isDisabled(node) && !isDisabled(parent) && !isDisabled(grandparent) && !isDisabled(ancestor);
      function isDisabled (elem) {
        return elem && elem.hasAttribute && elem.hasAttribute('disabled');
      }
    }

  }
}
InkRippleService.$inject = ["$window", "$timeout", "$parse"];

/**
 * noink/nobar/nostretch directive: make any element that has one of
 * these attributes be given a controller, so that other directives can
 * `require:` these and see if there is a `no<xxx>` parent attribute.
 *
 * @usage
 * <hljs lang="html">
 * <parent md-no-ink>
 *   <child detect-no>
 *   </child>
 * </parent>
 * </hljs>
 *
 * <hljs lang="js">
 * myApp.directive('detectNo', function() {
 *   return {
 *     require: ['^?mdNoInk', ^?mdNoBar'],
 *     link: function(scope, element, attr, ctrls) {
 *       var noinkCtrl = ctrls[0];
 *       var nobarCtrl = ctrls[1];
 *       if (noInkCtrl) {
 *         alert("the md-no-ink flag has been specified on an ancestor!");
 *       }
 *       if (nobarCtrl) {
 *         alert("the md-no-bar flag has been specified on an ancestor!");
 *       }
 *     }
 *   };
 * });
 * </hljs>
 */
function attrNoDirective() {
  return function() {
    return {
      controller: angular.noop
    };
  };
}
})();

/*!
 * Angular Material Design
 * https://github.com/angular/material
 * @license MIT
 * v0.7.1
 */
(function() {
'use strict';

angular.module('material.core.theming.palette', [])
.constant('$mdColorPalette', {
  'red': {
    '50': '#ffebee',
    '100': '#ffcdd2',
    '200': '#ef9a9a',
    '300': '#e57373',
    '400': '#ef5350',
    '500': '#f44336',
    '600': '#e53935',
    '700': '#d32f2f',
    '800': '#c62828',
    '900': '#b71c1c',
    'A100': '#ff8a80',
    'A200': '#ff5252',
    'A400': '#ff1744',
    'A700': '#d50000',
    'contrastDefaultColor': 'light',
    'contrastDarkColors': '50 100 200 300 400 A100',
    'contrastStrongLightColors': '500 600 700 A200 A400 A700'
  },
  'pink': {
    '50': '#fce4ec',
    '100': '#f8bbd0',
    '200': '#f48fb1',
    '300': '#f06292',
    '400': '#ec407a',
    '500': '#e91e63',
    '600': '#d81b60',
    '700': '#c2185b',
    '800': '#ad1457',
    '900': '#880e4f',
    'A100': '#ff80ab',
    'A200': '#ff4081',
    'A400': '#f50057',
    'A700': '#c51162',
    'contrastDefaultColor': 'light',
    'contrastDarkColors': '50 100 200 300 400 A100',
    'contrastStrongLightColors': '500 600 A200 A400 A700'
  },
  'purple': {
    '50': '#f3e5f5',
    '100': '#e1bee7',
    '200': '#ce93d8',
    '300': '#ba68c8',
    '400': '#ab47bc',
    '500': '#9c27b0',
    '600': '#8e24aa',
    '700': '#7b1fa2',
    '800': '#6a1b9a',
    '900': '#4a148c',
    'A100': '#ea80fc',
    'A200': '#e040fb',
    'A400': '#d500f9',
    'A700': '#aa00ff',
    'contrastDefaultColor': 'light',
    'contrastDarkColors': '50 100 200 A100',
    'contrastStrongLightColors': '300 400 A200 A400 A700'
  },
  'deep-purple': {
    '50': '#ede7f6',
    '100': '#d1c4e9',
    '200': '#b39ddb',
    '300': '#9575cd',
    '400': '#7e57c2',
    '500': '#673ab7',
    '600': '#5e35b1',
    '700': '#512da8',
    '800': '#4527a0',
    '900': '#311b92',
    'A100': '#b388ff',
    'A200': '#7c4dff',
    'A400': '#651fff',
    'A700': '#6200ea',
    'contrastDefaultColor': 'light',
    'contrastDarkColors': '50 100 200 A100',
    'contrastStrongLightColors': '300 400 A200'
  },
  'indigo': {
    '50': '#e8eaf6',
    '100': '#c5cae9',
    '200': '#9fa8da',
    '300': '#7986cb',
    '400': '#5c6bc0',
    '500': '#3f51b5',
    '600': '#3949ab',
    '700': '#303f9f',
    '800': '#283593',
    '900': '#1a237e',
    'A100': '#8c9eff',
    'A200': '#536dfe',
    'A400': '#3d5afe',
    'A700': '#304ffe',
    'contrastDefaultColor': 'light',
    'contrastDarkColors': '50 100 200 A100',
    'contrastStrongLightColors': '300 400 A200 A400'
  },
  'blue': {
    '50': '#e3f2fd',
    '100': '#bbdefb',
    '200': '#90caf9',
    '300': '#64b5f6',
    '400': '#42a5f5',
    '500': '#2196f3',
    '600': '#1e88e5',
    '700': '#1976d2',
    '800': '#1565c0',
    '900': '#0d47a1',
    'A100': '#82b1ff',
    'A200': '#448aff',
    'A400': '#2979ff',
    'A700': '#2962ff',
    'contrastDefaultColor': 'light',
    'contrastDarkColors': '100 200 300 400 A100',
    'contrastStrongLightColors': '500 600 700 A200 A400 A700'
  },
  'light-blue': {
    '50': '#e1f5fe',
    '100': '#b3e5fc',
    '200': '#81d4fa',
    '300': '#4fc3f7',
    '400': '#29b6f6',
    '500': '#03a9f4',
    '600': '#039be5',
    '700': '#0288d1',
    '800': '#0277bd',
    '900': '#01579b',
    'A100': '#80d8ff',
    'A200': '#40c4ff',
    'A400': '#00b0ff',
    'A700': '#0091ea',
    'contrastDefaultColor': 'dark',
    'contrastLightColors': '500 600 700 800 900 A700',
    'contrastStrongLightColors': '500 600 700 800 A700'
  },
  'cyan': {
    '50': '#e0f7fa',
    '100': '#b2ebf2',
    '200': '#80deea',
    '300': '#4dd0e1',
    '400': '#26c6da',
    '500': '#00bcd4',
    '600': '#00acc1',
    '700': '#0097a7',
    '800': '#00838f',
    '900': '#006064',
    'A100': '#84ffff',
    'A200': '#18ffff',
    'A400': '#00e5ff',
    'A700': '#00b8d4',
    'contrastDefaultColor': 'dark',
    'contrastLightColors': '500 600 700 800 900',
    'contrastStrongLightColors': '500 600 700 800'
  },
  'teal': {
    '50': '#e0f2f1',
    '100': '#b2dfdb',
    '200': '#80cbc4',
    '300': '#4db6ac',
    '400': '#26a69a',
    '500': '#009688',
    '600': '#00897b',
    '700': '#00796b',
    '800': '#00695c',
    '900': '#004d40',
    'A100': '#a7ffeb',
    'A200': '#64ffda',
    'A400': '#1de9b6',
    'A700': '#00bfa5',
    'contrastDefaultColor': 'dark',
    'contrastLightColors': '500 600 700 800 900',
    'contrastStrongLightColors': '500 600 700'
  },
  'green': {
    '50': '#e8f5e9',
    '100': '#c8e6c9',
    '200': '#a5d6a7',
    '300': '#81c784',
    '400': '#66bb6a',
    '500': '#4caf50',
    '600': '#43a047',
    '700': '#388e3c',
    '800': '#2e7d32',
    '900': '#1b5e20',
    'A100': '#b9f6ca',
    'A200': '#69f0ae',
    'A400': '#00e676',
    'A700': '#00c853',
    'contrastDefaultColor': 'dark',
    'contrastLightColors': '500 600 700 800 900',
    'contrastStrongLightColors': '500 600 700'
  },
  'light-green': {
    '50': '#f1f8e9',
    '100': '#dcedc8',
    '200': '#c5e1a5',
    '300': '#aed581',
    '400': '#9ccc65',
    '500': '#8bc34a',
    '600': '#7cb342',
    '700': '#689f38',
    '800': '#558b2f',
    '900': '#33691e',
    'A100': '#ccff90',
    'A200': '#b2ff59',
    'A400': '#76ff03',
    'A700': '#64dd17',
    'contrastDefaultColor': 'dark',
    'contrastLightColors': '800 900',
    'contrastStrongLightColors': '800 900'
  },
  'lime': {
    '50': '#f9fbe7',
    '100': '#f0f4c3',
    '200': '#e6ee9c',
    '300': '#dce775',
    '400': '#d4e157',
    '500': '#cddc39',
    '600': '#c0ca33',
    '700': '#afb42b',
    '800': '#9e9d24',
    '900': '#827717',
    'A100': '#f4ff81',
    'A200': '#eeff41',
    'A400': '#c6ff00',
    'A700': '#aeea00',
    'contrastDefaultColor': 'dark',
    'contrastLightColors': '900',
    'contrastStrongLightColors': '900'
  },
  'yellow': {
    '50': '#fffde7',
    '100': '#fff9c4',
    '200': '#fff59d',
    '300': '#fff176',
    '400': '#ffee58',
    '500': '#ffeb3b',
    '600': '#fdd835',
    '700': '#fbc02d',
    '800': '#f9a825',
    '900': '#f57f17',
    'A100': '#ffff8d',
    'A200': '#ffff00',
    'A400': '#ffea00',
    'A700': '#ffd600',
    'contrastDefaultColor': 'dark'
  },
  'amber': {
    '50': '#fff8e1',
    '100': '#ffecb3',
    '200': '#ffe082',
    '300': '#ffd54f',
    '400': '#ffca28',
    '500': '#ffc107',
    '600': '#ffb300',
    '700': '#ffa000',
    '800': '#ff8f00',
    '900': '#ff6f00',
    'A100': '#ffe57f',
    'A200': '#ffd740',
    'A400': '#ffc400',
    'A700': '#ffab00',
    'contrastDefaultColor': 'dark'
  },
  'orange': {
    '50': '#fff3e0',
    '100': '#ffe0b2',
    '200': '#ffcc80',
    '300': '#ffb74d',
    '400': '#ffa726',
    '500': '#ff9800',
    '600': '#fb8c00',
    '700': '#f57c00',
    '800': '#ef6c00',
    '900': '#e65100',
    'A100': '#ffd180',
    'A200': '#ffab40',
    'A400': '#ff9100',
    'A700': '#ff6d00',
    'contrastDefaultColor': 'dark',
    'contrastLightColors': '800 900',
    'contrastStrongLightColors': '800 900'
  },
  'deep-orange': {
    '50': '#fbe9e7',
    '100': '#ffccbc',
    '200': '#ffab91',
    '300': '#ff8a65',
    '400': '#ff7043',
    '500': '#ff5722',
    '600': '#f4511e',
    '700': '#e64a19',
    '800': '#d84315',
    '900': '#bf360c',
    'A100': '#ff9e80',
    'A200': '#ff6e40',
    'A400': '#ff3d00',
    'A700': '#dd2c00',
    'contrastDefaultColor': 'light',
    'contrastDarkColors': '50 100 200 300 400 A100 A200',
    'contrastStrongLightColors': '500 600 700 800 900 A400 A700'
  },
  'brown': {
    '50': '#efebe9',
    '100': '#d7ccc8',
    '200': '#bcaaa4',
    '300': '#a1887f',
    '400': '#8d6e63',
    '500': '#795548',
    '600': '#6d4c41',
    '700': '#5d4037',
    '800': '#4e342e',
    '900': '#3e2723',
    'A100': '#d7ccc8',
    'A200': '#bcaaa4',
    'A400': '#8d6e63',
    'A700': '#5d4037',
    'contrastDefaultColor': 'light',
    'contrastDarkColors': '50 100 200',
    'contrastStrongLightColors': '300 400'
  },
  'grey': {
    '0': '#ffffff',
    '50': '#fafafa',
    '100': '#f5f5f5',
    '200': '#eeeeee',
    '300': '#e0e0e0',
    '400': '#bdbdbd',
    '500': '#9e9e9e',
    '600': '#757575',
    '700': '#616161',
    '800': '#424242',
    '900': '#212121',
    '1000': '#000000',
    'A100': '#ffffff',
    'A200': '#eeeeee',
    'A400': '#bdbdbd',
    'A700': '#616161',
    'contrastDefaultColor': 'dark',
    'contrastLightColors': '600 700 800 900'
  },
  'blue-grey': {
    '50': '#eceff1',
    '100': '#cfd8dc',
    '200': '#b0bec5',
    '300': '#90a4ae',
    '400': '#78909c',
    '500': '#607d8b',
    '600': '#546e7a',
    '700': '#455a64',
    '800': '#37474f',
    '900': '#263238',
    'A100': '#cfd8dc',
    'A200': '#b0bec5',
    'A400': '#78909c',
    'A700': '#455a64',
    'contrastDefaultColor': 'light',
    'contrastDarkColors': '50 100 200 300',
    'contrastStrongLightColors': '400 500'
  }
});
})();

/*!
 * Angular Material Design
 * https://github.com/angular/material
 * @license MIT
 * v0.7.1
 */
(function() {
'use strict';

angular.module('material.core.theming', ['material.core.theming.palette'])
  .directive('mdTheme', ThemingDirective)
  .directive('mdThemable', ThemableDirective)
  .provider('$mdTheming', ThemingProvider)
  .run(generateThemes);

/**
 * @ngdoc provider
 * @name $mdThemingProvider
 * @module material.core
 *
 * @description Provider to configure the `$mdTheming` service.
 */

/**
 * @ngdoc method
 * @name $mdThemingProvider#setDefaultTheme
 * @param {string} themeName Default theme name to be applied to elements. Default value is `default`.
 */

/**
 * @ngdoc method
 * @name $mdThemingProvider#alwaysWatchTheme
 * @param {boolean} watch Whether or not to always watch themes for changes and re-apply
 * classes when they change. Default is `false`. Enabling can reduce performance.
 */

// In memory storage of defined themes and color palettes (both loaded by CSS, and user specified)
var PALETTES;
var THEMES;
var themingProvider;
var generationIsDone;

var DARK_FOREGROUND = {
  name: 'dark',
  '1': 'rgba(0,0,0,0.87)',
  '2': 'rgba(0,0,0,0.54)',
  '3': 'rgba(0,0,0,0.26)',
  '4': 'rgba(0,0,0,0.12)'
};
var LIGHT_FOREGROUND = {
  name: 'light',
  '1': 'rgba(255,255,255,1.0)',
  '2': 'rgba(255,255,255,0.7)',
  '3': 'rgba(255,255,255,0.3)',
  '4': 'rgba(255,255,255,0.12)'
};

var DARK_SHADOW = '1px 1px 0px rgba(0,0,0,0.4), -1px -1px 0px rgba(0,0,0,0.4)';
var LIGHT_SHADOW = '';

var DARK_CONTRAST_COLOR = colorToRgbaArray('rgba(0,0,0,0.87)');
var LIGHT_CONTRAST_COLOR = colorToRgbaArray('rgba(255,255,255,0.87');
var STRONG_LIGHT_CONTRAST_COLOR = colorToRgbaArray('rgb(255,255,255)');

var THEME_COLOR_TYPES = ['primary', 'accent', 'warn', 'background'];
var DEFAULT_COLOR_TYPE = 'primary';

// A color in a theme will use these hues by default, if not specified by user.
var LIGHT_DEFAULT_HUES = {
  'accent': {
    'default': 'A200',
    'hue-1': 'A100',
    'hue-2': 'A400',
    'hue-3': 'A700'
  }
};
var DARK_DEFAULT_HUES = {
  'background': {
    'default': '500',
    'hue-1': '300',
    'hue-2': '600',
    'hue-3': '800'
  }
};
THEME_COLOR_TYPES.forEach(function(colorType) {
  // Color types with unspecified default hues will use these default hue values
  var defaultDefaultHues = {
    'default': '500',
    'hue-1': '300',
    'hue-2': '800',
    'hue-3': 'A100'
  };
  if (!LIGHT_DEFAULT_HUES[colorType]) LIGHT_DEFAULT_HUES[colorType] = defaultDefaultHues;
  if (!DARK_DEFAULT_HUES[colorType]) DARK_DEFAULT_HUES[colorType] = defaultDefaultHues;
});

var VALID_HUE_VALUES = [
  '50', '100', '200', '300', '400', '500', '600',
  '700', '800', '900', 'A100', 'A200', 'A400', 'A700'
];

function ThemingProvider($mdColorPalette) {
  PALETTES = {};
  THEMES = {};
  var defaultTheme = 'default';
  var alwaysWatchTheme = false;

  // Load JS Defined Palettes
  angular.extend(PALETTES, $mdColorPalette);

  // Default theme defined in core.js

  ThemingService.$inject = ["$rootScope", "$log"];
  return themingProvider = {
    definePalette: definePalette,
    extendPalette: extendPalette,
    theme: registerTheme,

    setDefaultTheme: function(theme) {
      defaultTheme = theme;
    },
    alwaysWatchTheme: function(alwaysWatch) {
      alwaysWatchTheme = alwaysWatch;
    },
    $get: ThemingService,
    _LIGHT_DEFAULT_HUES: LIGHT_DEFAULT_HUES,
    _DARK_DEFAULT_HUES: DARK_DEFAULT_HUES,
    _PALETTES: PALETTES,
    _THEMES: THEMES,
    _parseRules: parseRules,
    _rgba: rgba
  };

  // Example: $mdThemingProvider.definePalette('neonRed', { 50: '#f5fafa', ... });
  function definePalette(name, map) {
    map = map || {};
    PALETTES[name] = checkPaletteValid(name, map);
    return themingProvider;
  }

  // Returns an new object which is a copy of a given palette `name` with variables from
  // `map` overwritten
  // Example: var neonRedMap = $mdThemingProvider.extendPalette('red', { 50: '#f5fafafa' });
  function extendPalette(name, map) {
    return checkPaletteValid(name,  angular.extend({}, PALETTES[name] || {}, map) );
  }

  // Make sure that palette has all required hues
  function checkPaletteValid(name, map) {
    var missingColors = VALID_HUE_VALUES.filter(function(field) {
      return !map[field];
    });
    if (missingColors.length) {
      throw new Error("Missing colors %1 in palette %2!"
                      .replace('%1', missingColors.join(', '))
                      .replace('%2', name));
    }

    return map;
  }

  // Register a theme (which is a collection of color palettes to use with various states
  // ie. warn, accent, primary )
  // Optionally inherit from an existing theme
  // $mdThemingProvider.theme('custom-theme').primaryPalette('red');
  function registerTheme(name, inheritFrom) {
    inheritFrom = inheritFrom || 'default';
    if (THEMES[name]) return THEMES[name];

    var parentTheme = typeof inheritFrom === 'string' ? THEMES[inheritFrom] : inheritFrom;
    var theme = new Theme(name);

    if (parentTheme) {
      angular.forEach(parentTheme.colors, function(color, colorType) {
        theme.colors[colorType] = {
          name: color.name,
          // Make sure a COPY of the hues is given to the child color,
          // not the same reference.
          hues: angular.extend({}, color.hues)
        };
      });
    }
    THEMES[name] = theme;

    return theme;
  }

  function Theme(name) {
    var self = this;
    self.name = name;
    self.colors = {};

    self.dark = setDark;
    setDark(false);

    function setDark(isDark) {
      isDark = arguments.length === 0 ? true : !!isDark;

      // If no change, abort
      if (isDark === self.isDark) return;

      self.isDark = isDark;

      self.foregroundPalette = self.isDark ? LIGHT_FOREGROUND : DARK_FOREGROUND;
      self.foregroundShadow = self.isDark ? DARK_SHADOW : LIGHT_SHADOW;
      
      // Light and dark themes have different default hues.
      // Go through each existing color type for this theme, and for every
      // hue value that is still the default hue value from the previous light/dark setting,
      // set it to the default hue value from the new light/dark setting.
      var newDefaultHues = self.isDark ? DARK_DEFAULT_HUES : LIGHT_DEFAULT_HUES;
      var oldDefaultHues = self.isDark ? LIGHT_DEFAULT_HUES : DARK_DEFAULT_HUES;
      angular.forEach(newDefaultHues, function(newDefaults, colorType) {
        var color = self.colors[colorType];
        var oldDefaults = oldDefaultHues[colorType];
        if (color) {
          for (var hueName in color.hues) {
            if (color.hues[hueName] === oldDefaults[hueName]) {
              color.hues[hueName] = newDefaults[hueName];
            }
          }
        }
      });

      return self;
    }

    THEME_COLOR_TYPES.forEach(function(colorType) {
      var defaultHues = (self.isDark ? DARK_DEFAULT_HUES : LIGHT_DEFAULT_HUES)[colorType];
      self[colorType + 'Palette'] = function setPaletteType(paletteName, hues) {
        var color = self.colors[colorType] = {
          name: paletteName,
          hues: angular.extend({}, defaultHues, hues)
        };

        Object.keys(color.hues).forEach(function(name) {
          if (!defaultHues[name]) {
            throw new Error("Invalid hue name '%1' in theme %2's %3 color %4. Available hue names: %4"
              .replace('%1', name)
              .replace('%2', self.name)
              .replace('%3', paletteName)
              .replace('%4', Object.keys(defaultHues).join(', '))
            );
          }
        });
        Object.keys(color.hues).map(function(key) {
          return color.hues[key];
        }).forEach(function(hueValue) {
          if (VALID_HUE_VALUES.indexOf(hueValue) == -1) {
            throw new Error("Invalid hue value '%1' in theme %2's %3 color %4. Available hue values: %5"
              .replace('%1', hueValue)
              .replace('%2', self.name)
              .replace('%3', colorType)
              .replace('%4', paletteName)
              .replace('%5', VALID_HUE_VALUES.join(', '))
            );
          }
        });
        return self;
      };

      self[colorType + 'Color'] = function() {
        var args = Array.prototype.slice.call(arguments);
        console.warn('$mdThemingProviderTheme.' + colorType + 'Color() has been depricated. ' +
                     'Use $mdThemingProviderTheme.' + colorType + 'Palette() instead.');
        return self[colorType + 'Palette'].apply(self, args);
      };
    });
  }

  /**
   * @ngdoc service
   * @name $mdTheming
   *
   * @description
   *
   * Service that makes an element apply theming related classes to itself.
   *
   * ```js
   * app.directive('myFancyDirective', function($mdTheming) {
   *   return {
   *     restrict: 'e',
   *     link: function(scope, el, attrs) {
   *       $mdTheming(el);
   *     }
   *   };
   * });
   * ```
   * @param {el=} element to apply theming to
   */
  /* @ngInject */
  function ThemingService($rootScope, $log) {
    applyTheme.inherit = function(el, parent) {
      var ctrl = parent.controller('mdTheme');

      var attrThemeValue = el.attr('md-theme-watch');
      if ( (alwaysWatchTheme || angular.isDefined(attrThemeValue)) && attrThemeValue != 'false') {
        var deregisterWatch = $rootScope.$watch(function() {
          return ctrl && ctrl.$mdTheme || defaultTheme;
        }, changeTheme);
        el.on('$destroy', deregisterWatch);
      } else {
        var theme = ctrl && ctrl.$mdTheme || defaultTheme;
        changeTheme(theme);
      }

      function changeTheme(theme) {
        if (!registered(theme)) {
          $log.warn('Attempted to use unregistered theme \'' + theme + '\'. ' +
                    'Register it with $mdThemingProvider.theme().');
        }
        var oldTheme = el.data('$mdThemeName');
        if (oldTheme) el.removeClass('md-' + oldTheme +'-theme');
        el.addClass('md-' + theme + '-theme');
        el.data('$mdThemeName', theme);
      }
    };

    applyTheme.registered = registered;

    return applyTheme;

    function registered(theme) {
      if (theme === undefined || theme === '') return true;
      return THEMES[theme] !== undefined;
    }

    function applyTheme(scope, el) {
      // Allow us to be invoked via a linking function signature.
      if (el === undefined) {
        el = scope;
        scope = undefined;
      }
      if (scope === undefined) {
        scope = $rootScope;
      }
      applyTheme.inherit(el, el);
    }
  }
}
ThemingProvider.$inject = ["$mdColorPalette"];

function ThemingDirective($mdTheming, $interpolate, $log) {
  return {
    priority: 100,
    link: {
      pre: function(scope, el, attrs) {
        var ctrl = {
          $setTheme: function(theme) {
            if (!$mdTheming.registered(theme)) {
              $log.warn('attempted to use unregistered theme \'' + theme + '\'');
            }
            ctrl.$mdTheme = theme;
          }
        };
        el.data('$mdThemeController', ctrl);
        ctrl.$setTheme($interpolate(attrs.mdTheme)(scope));
        attrs.$observe('mdTheme', ctrl.$setTheme);
      }
    }
  };
}
ThemingDirective.$inject = ["$mdTheming", "$interpolate", "$log"];

function ThemableDirective($mdTheming) {
  return $mdTheming;
}
ThemableDirective.$inject = ["$mdTheming"];

function parseRules(theme, colorType, rules) {
  checkValidPalette(theme, colorType);

  rules = rules.replace(/THEME_NAME/g, theme.name);
  var generatedRules = [];
  var color = theme.colors[colorType];

  var themeNameRegex = new RegExp('.md-' + theme.name + '-theme', 'g');
  // Matches '{{ primary-color }}', etc
  var hueRegex = new RegExp('(\'|")?{{\\s*(' + colorType + ')-(color|contrast)-?(\\d\\.?\\d*)?\\s*}}(\"|\')?','g');
  var simpleVariableRegex = /'?"?\{\{\s*([a-zA-Z]+)-(A?\d+|hue\-[0-3]|shadow)-?(\d\.?\d*)?\s*\}\}'?"?/g;
  var palette = PALETTES[color.name];

  // find and replace simple variables where we use a specific hue, not angentire palette
  // eg. "{{primary-100}}"
  //\(' + THEME_COLOR_TYPES.join('\|') + '\)'
  rules = rules.replace(simpleVariableRegex, function(match, colorType, hue, opacity) {
    if (colorType === 'foreground') {
      if (hue == 'shadow') {
        return theme.foregroundShadow;
      } else {
        return theme.foregroundPalette[hue] || theme.foregroundPalette['1'];
      }
    }
    if (hue.indexOf('hue') === 0) {
      hue = theme.colors[colorType].hues[hue];
    }
    return rgba( (PALETTES[ theme.colors[colorType].name ][hue] || '').value, opacity );
  });

  // For each type, generate rules for each hue (ie. default, md-hue-1, md-hue-2, md-hue-3)
  angular.forEach(color.hues, function(hueValue, hueName) {
    var newRule = rules
      .replace(hueRegex, function(match, _, colorType, hueType, opacity) {
        return rgba(palette[hueValue][hueType === 'color' ? 'value' : 'contrast'], opacity);
      });
    if (hueName !== 'default') {
      newRule = newRule.replace(themeNameRegex, '.md-' + theme.name + '-theme.md-' + hueName);
    }
    generatedRules.push(newRule);
  });

  return generatedRules.join('');
}

// Generate our themes at run time given the state of THEMES and PALETTES
function generateThemes($injector) {
  var themeCss = $injector.has('$MD_THEME_CSS') ? $injector.get('$MD_THEME_CSS') : '';

  // MD_THEME_CSS is a string generated by the build process that includes all the themable
  // components as templates

  // Expose contrast colors for palettes to ensure that text is always readable
  angular.forEach(PALETTES, sanitizePalette);

  // Break the CSS into individual rules
  var rules = themeCss.split(/\}(?!(\}|'|"|;))/)
    .filter(function(rule) { return rule && rule.length; })
    .map(function(rule) { return rule.trim() + '}'; });

  var rulesByType = {};
  THEME_COLOR_TYPES.forEach(function(type) {
    rulesByType[type] = '';
  });
  var ruleMatchRegex = new RegExp('md-(' + THEME_COLOR_TYPES.join('|') + ')', 'g');

  // Sort the rules based on type, allowing us to do color substitution on a per-type basis
  rules.forEach(function(rule) {
    var match = rule.match(ruleMatchRegex);
    // First: test that if the rule has '.md-accent', it goes into the accent set of rules
    for (var i = 0, type; type = THEME_COLOR_TYPES[i]; i++) {
      if (rule.indexOf('.md-' + type) > -1) {
        return rulesByType[type] += rule;
      }
    }

    // If no eg 'md-accent' class is found, try to just find 'accent' in the rule and guess from
    // there
    for (i = 0; type = THEME_COLOR_TYPES[i]; i++) {
      if (rule.indexOf(type) > -1) {
        return rulesByType[type] += rule;
      }
    }

    // Default to the primary array
    return rulesByType[DEFAULT_COLOR_TYPE] += rule;
  });

  var styleString = '';

  // For each theme, use the color palettes specified for `primary`, `warn` and `accent`
  // to generate CSS rules.
  angular.forEach(THEMES, function(theme) {
    THEME_COLOR_TYPES.forEach(function(colorType) {
      styleString += parseRules(theme, colorType, rulesByType[colorType] + '');
    });
    if (theme.colors.primary.name == theme.colors.accent.name) {
      console.warn("$mdThemingProvider: Using the same palette for primary and" +
                   "accent. This violates the material design spec.");
    }
  });

  // Insert our newly minted styles into the DOM
  if (!generationIsDone) {
    var style = document.createElement('style');
    style.innerHTML = styleString;
    var head = document.getElementsByTagName('head')[0];
    head.insertBefore(style, head.firstElementChild);
    generationIsDone = true;
  }

  // The user specifies a 'default' contrast color as either light or dark,
  // then explicitly lists which hues are the opposite contrast (eg. A100 has dark, A200 has light)
  function sanitizePalette(palette) {
    var defaultContrast = palette.contrastDefaultColor;
    var lightColors = palette.contrastLightColors || [];
    var strongLightColors = palette.contrastStrongLightColors || [];
    var darkColors = palette.contrastDarkColors || [];

    // These colors are provided as space-separated lists
    if (typeof lightColors === 'string') lightColors = lightColors.split(' ');
    if (typeof strongLightColors === 'string') strongLightColors = strongLightColors.split(' ');
    if (typeof darkColors === 'string') darkColors = darkColors.split(' ');

    // Cleanup after ourselves
    delete palette.contrastDefaultColor;
    delete palette.contrastLightColors;
    delete palette.contrastStrongLightColors;
    delete palette.contrastDarkColors;

    // Change { 'A100': '#fffeee' } to { 'A100': { value: '#fffeee', contrast:DARK_CONTRAST_COLOR }
    angular.forEach(palette, function(hueValue, hueName) {
      if (angular.isObject(hueValue)) return; // Already converted
      // Map everything to rgb colors
      var rgbValue = colorToRgbaArray(hueValue);
      if (!rgbValue) {
        throw new Error("Color %1, in palette %2's hue %3, is invalid. Hex or rgb(a) color expected."
                        .replace('%1', hueValue)
                        .replace('%2', palette.name)
                        .replace('%3', hueName));
      }

      palette[hueName] = {
        value: rgbValue,
        contrast: getContrastColor()
      };
      function getContrastColor() {
        if (defaultContrast === 'light') {
          if (darkColors.indexOf(hueName) > -1) {
            return DARK_CONTRAST_COLOR;
          } else {
            return strongLightColors.indexOf(hueName) > -1 ? STRONG_LIGHT_CONTRAST_COLOR 
              : LIGHT_CONTRAST_COLOR;
          }
        } else {
          if (lightColors.indexOf(hueName) > -1) {
            return strongLightColors.indexOf(hueName) > -1 ? STRONG_LIGHT_CONTRAST_COLOR 
              : LIGHT_CONTRAST_COLOR;
          } else {
            return DARK_CONTRAST_COLOR;
          }
        }
      }
    });
  }

}
generateThemes.$inject = ["$injector"];

function checkValidPalette(theme, colorType) {
  // If theme attempts to use a palette that doesnt exist, throw error
  if (!PALETTES[ (theme.colors[colorType] || {}).name ]) {
    throw new Error(
      "You supplied an invalid color palette for theme %1's %2 palette. Available palettes: %3"
                    .replace('%1', theme.name)
                    .replace('%2', colorType)
                    .replace('%3', Object.keys(PALETTES).join(', '))
    );
  }
}

function colorToRgbaArray(clr) {
  if (angular.isArray(clr) && clr.length == 3) return clr;
  if (/^rgb/.test(clr)) {
    return clr.replace(/(^\s*rgba?\(|\)\s*$)/g, '').split(',').map(function(value, i) {
      return i == 3 ? parseFloat(value, 10) : parseInt(value, 10);
    });
  }
  if (clr.charAt(0) == '#') clr = clr.substring(1);
  if (!/^([a-fA-F0-9]{3}){1,2}$/g.test(clr)) return;

  var dig = clr.length / 3;
  var red = clr.substr(0, dig);
  var grn = clr.substr(dig, dig);
  var blu = clr.substr(dig * 2);
  if (dig === 1) {
    red += red;
    grn += grn;
    blu += blu;
  }
  return [parseInt(red, 16), parseInt(grn, 16), parseInt(blu, 16)];
}

function rgba(rgbArray, opacity) {
  if (rgbArray.length == 4) {
    rgbArray = angular.copy(rgbArray);
    opacity ? rgbArray.pop() : opacity = rgbArray.pop();
  }
  return opacity && (typeof opacity == 'number' || (typeof opacity == 'string' && opacity.length)) ?
    'rgba(' + rgbArray.join(',') + ',' + opacity + ')' :
    'rgb(' + rgbArray.join(',') + ')';
}

})();

/*!
 * Angular Material Design
 * https://github.com/angular/material
 * @license MIT
 * v0.7.1
 */
(function() {
'use strict';

/*
 * @ngdoc module
 * @name material.components.backdrop
 * @description Backdrop
 */

/**
 * @ngdoc directive
 * @name mdBackdrop
 * @module material.components.backdrop
 *
 * @restrict E
 *
 * @description
 * `<md-backdrop>` is a backdrop element used by other coponents, such as dialog and bottom sheet.
 * Apply class `opaque` to make the backdrop use the theme backdrop color.
 *
 */

angular.module('material.components.backdrop', [
  'material.core'
])
  .directive('mdBackdrop', BackdropDirective);

function BackdropDirective($mdTheming) {
  return $mdTheming;
}
BackdropDirective.$inject = ["$mdTheming"];
})();

/*!
 * Angular Material Design
 * https://github.com/angular/material
 * @license MIT
 * v0.7.1
 */
(function() {
'use strict';

/**
 * @ngdoc module
 * @name material.components.button
 * @description
 *
 * Button
 */
angular.module('material.components.button', [
  'material.core'
])
  .directive('mdButton', MdButtonDirective);

/**
 * @ngdoc directive
 * @name mdButton
 * @module material.components.button
 *
 * @restrict E
 *
 * @description
 * `<md-button>` is a button directive with optional ink ripples (default enabled).
 *
 * If you supply a `href` or `ng-href` attribute, it will become an `<a>` element. Otherwise, it will
 * become a `<button>` element.
 *
 * As per the [material design spec](http://www.google.com/design/spec/style/color.html#color-ui-color-application)
 * the FAB button is in the accent color by default. The primary color palette may be used with
 * the `md-primary` class.
 *
 * @param {boolean=} md-no-ink If present, disable ripple ink effects.
 * @param {expression=} ng-disabled En/Disable based on the expression
 * @param {string=} md-ripple-size Overrides the default ripple size logic. Options: `full`, `partial`, `auto`
 * @param {string=} aria-label Adds alternative text to button for accessibility, useful for icon buttons.
 * If no default text is found, a warning will be logged.
 *
 * @usage
 * <hljs lang="html">
 *  <md-button>
 *    Button
 *  </md-button>
 *  <md-button href="http://google.com" class="md-button-colored">
 *    I'm a link
 *  </md-button>
 *  <md-button ng-disabled="true" class="md-colored">
 *    I'm a disabled button
 *  </md-button>
 * </hljs>
 */
function MdButtonDirective($mdInkRipple, $mdTheming, $mdAria) {

  return {
    restrict: 'E',
    replace: true,
    transclude: true,
    template: getTemplate,
    link: postLink
  };

  function isAnchor(attr) {
    return angular.isDefined(attr.href) || angular.isDefined(attr.ngHref);
  }
  
  function getTemplate(element, attr) {
    return isAnchor(attr) ?
           '<a class="md-button" ng-transclude></a>' :
           '<button class="md-button" ng-transclude></button>';
  }

  function postLink(scope, element, attr) {
    var node = element[0];
    $mdTheming(element);
    $mdInkRipple.attachButtonBehavior(scope, element);

    var elementHasText = node.textContent.trim();
    if (!elementHasText) {
      $mdAria.expect(element, 'aria-label');
    }

    // For anchor elements, we have to set tabindex manually when the 
    // element is disabled
    if (isAnchor(attr) && angular.isDefined(attr.ngDisabled) ) {
      scope.$watch(attr.ngDisabled, function(isDisabled) {
        element.attr('tabindex', isDisabled ? -1 : 0);
      });
    }
  }

}
MdButtonDirective.$inject = ["$mdInkRipple", "$mdTheming", "$mdAria"];
})();

/*!
 * Angular Material Design
 * https://github.com/angular/material
 * @license MIT
 * v0.7.1
 */
(function() {
'use strict';

/**
 * @ngdoc module
 * @name material.components.card
 *
 * @description
 * Card components.
 */
angular.module('material.components.card', [
  'material.core'
])
  .directive('mdCard', mdCardDirective);



/**
 * @ngdoc directive
 * @name mdCard
 * @module material.components.card
 *
 * @restrict E
 *
 * @description
 * The `<md-card>` directive is a container element used within `<md-content>` containers.
 *
 * Cards have constant width and variable heights; where the maximum height is limited to what can
 * fit within a single view on a platform, but it can temporarily expand as needed
 *
 * @usage
 * <hljs lang="html">
 * <md-card>
 *  <img src="img/washedout.png" class="md-card-image">
 *  <h2>Paracosm</h2>
 *  <p>
 *    The titles of Washed Out's breakthrough song and the first single from Paracosm share the * two most important words in Ernest Greene's musical language: feel it. It's a simple request, as well...
 *  </p>
 * </md-card>
 * </hljs>
 *
 */
function mdCardDirective($mdTheming) {
  return {
    restrict: 'E',
    link: function($scope, $element, $attr) {
      $mdTheming($element);
    }
  };
}
mdCardDirective.$inject = ["$mdTheming"];
})();

/*!
 * Angular Material Design
 * https://github.com/angular/material
 * @license MIT
 * v0.7.1
 */
(function() {
'use strict';

/**
 * @ngdoc module
 * @name material.components.checkbox
 * @description Checkbox module!
 */
angular.module('material.components.checkbox', [
  'material.core'
])
  .directive('mdCheckbox', MdCheckboxDirective);

/**
 * @ngdoc directive
 * @name mdCheckbox
 * @module material.components.checkbox
 * @restrict E
 *
 * @description
 * The checkbox directive is used like the normal [angular checkbox](https://docs.angularjs.org/api/ng/input/input%5Bcheckbox%5D).
 *
 * As per the [material design spec](http://www.google.com/design/spec/style/color.html#color-ui-color-application)
 * the checkbox is in the accent color by default. The primary color palette may be used with
 * the `md-primary` class.
 *
 * @param {string} ng-model Assignable angular expression to data-bind to.
 * @param {string=} name Property name of the form under which the control is published.
 * @param {expression=} ng-true-value The value to which the expression should be set when selected.
 * @param {expression=} ng-false-value The value to which the expression should be set when not selected.
 * @param {string=} ng-change Angular expression to be executed when input changes due to user interaction with the input element.
 * @param {boolean=} md-no-ink Use of attribute indicates use of ripple ink effects
 * @param {string=} aria-label Adds label to checkbox for accessibility.
 * Defaults to checkbox's text. If no default text is found, a warning will be logged.
 *
 * @usage
 * <hljs lang="html">
 * <md-checkbox ng-model="isChecked" aria-label="Finished?">
 *   Finished ?
 * </md-checkbox>
 *
 * <md-checkbox md-no-ink ng-model="hasInk" aria-label="No Ink Effects">
 *   No Ink Effects
 * </md-checkbox>
 *
 * <md-checkbox ng-disabled="true" ng-model="isDisabled" aria-label="Disabled">
 *   Disabled
 * </md-checkbox>
 *
 * </hljs>
 *
 */
function MdCheckboxDirective(inputDirective, $mdInkRipple, $mdAria, $mdConstant, $mdTheming, $mdUtil) {
  inputDirective = inputDirective[0];
  var CHECKED_CSS = 'md-checked';

  return {
    restrict: 'E',
    transclude: true,
    require: '?ngModel',
    template: 
      '<div class="md-container" md-ink-ripple md-ink-ripple-checkbox>' +
        '<div class="md-icon"></div>' +
      '</div>' +
      '<div ng-transclude class="md-label"></div>',
    compile: compile
  };

  // **********************************************************
  // Private Methods
  // **********************************************************

  function compile (tElement, tAttrs) {

    tAttrs.type = 'checkbox';
    tAttrs.tabIndex = 0;
    tElement.attr('role', tAttrs.type);

    return function postLink(scope, element, attr, ngModelCtrl) {
      ngModelCtrl = ngModelCtrl || $mdUtil.fakeNgModel();
      var checked = false;
      $mdTheming(element);

      $mdAria.expectWithText(element, 'aria-label');

      // Reuse the original input[type=checkbox] directive from Angular core.
      // This is a bit hacky as we need our own event listener and own render
      // function.
      inputDirective.link.pre(scope, {
        on: angular.noop,
        0: {}
      }, attr, [ngModelCtrl]);

      element.on('click', listener)
        .on('keypress', keypressHandler);
      ngModelCtrl.$render = render;

      function keypressHandler(ev) {
        if(ev.which === $mdConstant.KEY_CODE.SPACE) {
          ev.preventDefault();
          listener(ev);
        }
      }
      function listener(ev) {
        if (element[0].hasAttribute('disabled')) return;

        scope.$apply(function() {
          checked = !checked;
          ngModelCtrl.$setViewValue(checked, ev && ev.type);
          ngModelCtrl.$render();
        });
      }

      function render() {
        checked = ngModelCtrl.$viewValue;
        if(checked) {
          element.addClass(CHECKED_CSS);
        } else {
          element.removeClass(CHECKED_CSS);
        }
      }
    };
  }
}
MdCheckboxDirective.$inject = ["inputDirective", "$mdInkRipple", "$mdAria", "$mdConstant", "$mdTheming", "$mdUtil"];

})();

/*!
 * Angular Material Design
 * https://github.com/angular/material
 * @license MIT
 * v0.7.1
 */
(function() {
'use strict';

/**
 * @ngdoc module
 * @name material.components.content
 *
 * @description
 * Scrollable content
 */
angular.module('material.components.content', [
  'material.core'
])
  .directive('mdContent', mdContentDirective);

/**
 * @ngdoc directive
 * @name mdContent
 * @module material.components.content
 *
 * @restrict E
 *
 * @description
 * The `<md-content>` directive is a container element useful for scrollable content
 *
 * ### Restrictions
 *
 * - Add the `md-padding` class to make the content padded.
 *
 * @usage
 * <hljs lang="html">
 *  <md-content class="md-padding">
 *      Lorem ipsum dolor sit amet, ne quod novum mei.
 *  </md-content>
 * </hljs>
 *
 */

function mdContentDirective($mdTheming) {
  return {
    restrict: 'E',
    controller: ['$scope', '$element', ContentController],
    link: function(scope, element, attr) {
      var node = element[0];

      $mdTheming(element);
      scope.$broadcast('$mdContentLoaded', element);

      iosScrollFix(element[0]);
    }
  };

  function ContentController($scope, $element) {
    this.$scope = $scope;
    this.$element = $element;
  }
}
mdContentDirective.$inject = ["$mdTheming"];

function iosScrollFix(node) {
  // IOS FIX:
  // If we scroll where there is no more room for the webview to scroll,
  // by default the webview itself will scroll up and down, this looks really
  // bad.  So if we are scrolling to the very top or bottom, add/subtract one
  angular.element(node).on('$md.pressdown', function(ev) {
    // Only touch events
    if (ev.pointer.type !== 't') return;
    // Don't let a child content's touchstart ruin it for us.
    if (ev.$materialScrollFixed) return;
    ev.$materialScrollFixed = true;

    if (node.scrollTop === 0) {
      node.scrollTop = 1;
    } else if (node.scrollHeight === node.scrollTop + node.offsetHeight) {
      node.scrollTop -= 1;
    }
  });
}
})();

/*!
 * Angular Material Design
 * https://github.com/angular/material
 * @license MIT
 * v0.7.1
 */
(function() {
    'use strict';

    /**
     * @ngdoc module
     * @name material.components.simpledialog
     */
    angular.module('material.components.simpledialog', ['material.core', 'material.components.backdrop'])
        .factory('mdContextualMonitor', mdContextualMonitor)
        .directive('simpleDialog', SimpleDialogDirective)
        .provider('$simpleDialog', SimpleDialogProvider);

    function mdContextualMonitor($rootElement, $mdConstant) {
        var callbacks = [],
            bound = false;
        return {
            dequeue: function (cb) {
                var index = callbacks.indexOf(cb);
                if (index !== -1) {
                    callbacks.splice(index, 1);
                }
            },
            queue: function (cb) {
                var hashPrefix = 'context-monitor-',
                    lastHash = window.location.hash;
                if (!bound) {
                    $rootElement.on('keyup', function (e) {
                        var one = false;
                        if (e.keyCode !== $mdConstant.KEY_CODE.ESCAPE) {
                            return;
                        }
                        angular.forEach(callbacks.concat().reverse(), function (cb) {
                            if (one) {
                                return;
                            }
                            if (cb && cb(e)) {
                                var index = callbacks.indexOf(cb);
                                if (index !== -1) {
                                    callbacks.splice(index, 1);
                                    one = true;
                                }
                            }
                        });
                    });
                    $(window).bind('hashchange', function () {
                        var newHash = window.location.hash;
                        // Do something
                        console.log(newHash, lastHash);
                        //At the end of the func:
                        lastHash = newHash;
                    });

                    bound = true;
                }
                window.location.hash = hashPrefix + _.uniqueId();
                callbacks.push(cb);
            }
        };
    }
    mdContextualMonitor.$inject = ["$rootElement", "$mdConstant"];


    function SimpleDialogDirective($$rAF, $mdTheming) {
        return {
            restrict: 'E',
            link: function(scope, element, attr) {
                $mdTheming(element);
                $$rAF(function() {
                    var content = element[0].querySelector('md-content');
                    if (content && content.scrollHeight > content.clientHeight) {
                        element.addClass('md-content-overflow');
                    }
                });
            }
        };
    }
    SimpleDialogDirective.$inject = ["$$rAF", "$mdTheming"];

    /**
     * @ngdoc service
     * @name $simpleDialog
     * @module material.components.simpledialog
     *
     * @description
     * `$simpleDialog` opens a dialog over the app and provides a simple promise API.
     *
     * ### Restrictions
     *
     * - The dialog is always given an isolate scope.
     * - The dialog's template must have an outer `<md-simpledialog>` element.
     *   Inside, use an `<md-content>` element for the dialog's content, and use
     *   an element with class `md-actions` for the dialog's actions.
     *
     * @usage
     * ##### HTML
     *
     * <hljs lang="html">
     * <div  ng-app="demoApp" ng-controller="EmployeeController">
     *   <md-button ng-click="showAlert()" class="md-raised md-warn">
     *     Employee Alert!
     *   </md-button>
     *   <md-button ng-click="closeAlert()" ng-disabled="!hasAlert()" class="md-raised">
     *     Close Alert
     *   </md-button>
     *   <md-button ng-click="showGreeting($event)" class="md-raised md-primary" >
     *     Greet Employee
     *   </md-button>
     * </div>
     * </hljs>
     *
     * ##### JavaScript
     *
     * <hljs lang="js">
     * (function(angular, undefined){
     *   "use strict";
     *
     *   angular
     *     .module('demoApp', ['ngMaterial'])
     *     .controller('EmployeeController', EmployeeEditor)
     *     .controller('GreetingController', GreetingController);
     *
     *   // Fictitious Employee Editor to show how to use simple and complex dialogs.
     *
     *   function EmployeeEditor($scope, $simpleDialog) {
     *     var alert;
     *
     *     $scope.showAlert = showAlert;
     *     $scope.closeAlert = closeAlert;
     *     $scope.showGreeting = showCustomGreeting;
     *
     *     $scope.hasAlert = function() { return !!alert };
     *     $scope.userName = $scope.userName || 'Bobby';
     *
     *     // Dialog #1 - Show simple alert dialog and cache
     *     // reference to dialog instance
     *
     *     function showAlert() {
     *       alert = $simpleDialog.alert()
     *         .title('Attention, ' + $scope.userName)
     *         .content('This is an example of how easy dialogs can be!')
     *         .ok('Close');
     *
     *       $simpleDialog
     *           .show( alert )
     *           .finally(function() {
     *             alert = undefined;
     *           });
     *     }
     *
     *     // Close the specified dialog instance and resolve with 'finished' flag
     *     // Normally this is not needed, just use '$simpleDialog.hide()' to close
     *     // the most recent dialog popup.
     *
     *     function closeAlert() {
     *       $simpleDialog.hide( alert, "finished" );
     *       alert = undefined;
     *     }
     *
     *     // Dialog #2 - Demonstrate more complex dialogs construction and popup.
     *
     *     function showCustomGreeting($event) {
     *         $simpleDialog.show({
     *           targetEvent: $event,
     *           template:
     *             '<md-simpledialog>' +
     *
     *             '  <md-content>Hello {{ employee }}!</md-content>' +
     *
     *             '  <div class="md-actions">' +
     *             '    <md-button ng-click="closeDialog()">' +
     *             '      Close Greeting' +
     *
     *             '    </md-button>' +
     *             '  </div>' +
     *             '</md-simpledialog>',
     *           controller: 'GreetingController',
     *           onComplete: afterShowAnimation,
     *           locals: { employee: $scope.userName }
     *         });
     *
     *         // When the 'enter' animation finishes...
     *
     *         function afterShowAnimation(scope, element, options) {
     *            // post-show code here: DOM element focus, etc.
     *         }
     *     }
     *   }
     *
     *   // Greeting controller used with the more complex 'showCustomGreeting()' custom dialog
     *
     *   function GreetingController($scope, $simpleDialog, employee) {
     *     // Assigned from construction <code>locals</code> options...
     *     $scope.employee = employee;
     *
     *     $scope.closeDialog = function() {
     *       // Easily hides most recent dialog shown...
     *       // no specific instance reference is needed.
     *       $simpleDialog.hide();
     *     };
     *   }
     *
     * })(angular);
     * </hljs>
     */

    /**
     * @ngdoc method
     * @name $simpleDialog#alert
     *
     * @description
     * Builds a preconfigured dialog with the specified message.
     *
     * @returns {obj} an `$simpleDialogPreset` with the chainable configuration methods:
     *
     * - $simpleDialogPreset#title(string) - sets title to string
     * - $simpleDialogPreset#content(string) - sets content / message to string
     * - $simpleDialogPreset#ok(string) - sets okay button text to string
     *
     */

    /**
     * @ngdoc method
     * @name $simpleDialog#confirm
     *
     * @description
     * Builds a preconfigured dialog with the specified message. You can call show and the promise returned
     * will be resolved only if the user clicks the confirm action on the dialog.
     *
     * @returns {obj} an `$simpleDialogPreset` with the chainable configuration methods:
     *
     * Additionally, it supports the following methods:
     *
     * - $simpleDialogPreset#title(string) - sets title to string
     * - $simpleDialogPreset#content(string) - sets content / message to string
     * - $simpleDialogPreset#ok(string) - sets okay button text to string
     * - $simpleDialogPreset#cancel(string) - sets cancel button text to string
     *
     */

    /**
     * @ngdoc method
     * @name $simpleDialog#show
     *
     * @description
     * Show a dialog with the specified options.
     *
     * @param {object} optionsOrPreset Either provide an `$simpleDialogPreset` returned from `alert()`,
     * `confirm()` or an options object with the following properties:
     *   - `templateUrl` - `{string=}`: The url of a template that will be used as the content
     *   of the dialog.
     *   - `template` - `{string=}`: Same as templateUrl, except this is an actual template string.
     *   - `targetEvent` - `{DOMClickEvent=}`: A click's event object. When passed in as an option,
     *     the location of the click will be used as the starting point for the opening animation
     *     of the the dialog.
     *   - `disableParentScroll` - `{boolean=}`: Whether to disable scrolling while the dialog is open.
     *     Default true.
     *   - `hasBackdrop` - `{boolean=}`: Whether there should be an opaque backdrop behind the dialog.
     *     Default true.
     *   - `clickOutsideToClose` - `{boolean=}`: Whether the user can click outside the dialog to
     *     close it. Default true.
     *   - `escapeToClose` - `{boolean=}`: Whether the user can press escape to close the dialog.
     *     Default true.
     *   - `controller` - `{string=}`: The controller to associate with the dialog. The controller
     *     will be injected with the local `$hideDialog`, which is a function used to hide the dialog.
     *   - `locals` - `{object=}`: An object containing key/value pairs. The keys will be used as names
     *     of values to inject into the controller. For example, `locals: {three: 3}` would inject
     *     `three` into the controller, with the value 3. If `bindToController` is true, they will be
     *     copied to the controller instead.
     *   - `bindToController` - `bool`: bind the locals to the controller, instead of passing them in
     *   - `resolve` - `{object=}`: Similar to locals, except it takes promises as values, and the
     *     dialog will not open until all of the promises resolve.
     *   - `controllerAs` - `{string=}`: An alias to assign the controller to on the scope.
     *   - `parent` - `{element=}`: The element to append the dialog to. Defaults to appending
     *     to the root element of the application.
     *   - `onComplete` `{function=}`: Callback function used to announce when the show() action is
     *     finished.
     *
     * @returns {promise} A promise that can be resolved with `$simpleDialog.hide()` or
     * rejected with `mdAdialog.cancel()`.
     */

    /**
     * @ngdoc method
     * @name $simpleDialog#hide
     *
     * @description
     * Hide an existing dialog and resolve the promise returned from `$simpleDialog.show()`.
     *
     * @param {*=} response An argument for the resolved promise.
     */

    /**
     * @ngdoc method
     * @name $simpleDialog#cancel
     *
     * @description
     * Hide an existing dialog and reject the promise returned from `$simpleDialog.show()`.
     *
     * @param {*=} response An argument for the rejected promise.
     */

    function SimpleDialogProvider($$interimElementProvider) {

        var alertDialogMethods = ['title', 'content', 'ariaLabel', 'ok'];

        dialogDefaultOptions.$inject = ["$timeout", "$rootElement", "$compile", "$animate", "$mdAria", "$document", "$mdUtil", "$mdConstant", "$mdTheming", "$$rAF", "$q", "$simpleDialog", "mdContextualMonitor"];
        return $$interimElementProvider('$simpleDialog')
            .setDefaults({
                methods: ['disableParentScroll', 'hasBackdrop', 'clickOutsideToClose', 'escapeToClose', 'targetEvent'],
                options: dialogDefaultOptions
            });


        /* @ngInject */
        function dialogDefaultOptions($timeout, $rootElement, $compile, $animate, $mdAria, $document,
            $mdUtil, $mdConstant, $mdTheming, $$rAF, $q, $simpleDialog, mdContextualMonitor) {
            return {
                hasBackdrop: true,
                isolateScope: true,
                onShow: onShow,
                onRemove: onRemove,
                clickOutsideToClose: true,
                escapeToClose: true,
                targetEvent: null,
                disableParentScroll: true,
                transformTemplate: function(template) {
                    return '<div class="simple-dialog-container">' + template + '</div>';
                }
            };

            function discoverDirective(options) {
                return 'simple-dialog';
            }

            function discoverContainerClass(container, options) {
            }

            // On show method for dialogs
            function onShow(scope, element, options) {
                // Incase the user provides a raw dom element, always wrap it in jqLite
                options.parent = angular.element(options.parent);

                options.popInTarget = angular.element((options.targetEvent || {}).target);
                var closeButton = findCloseButton(),
                    directive = discoverDirective(options),
                    dialogEl = element.find(directive);

                configureAria(dialogEl);
                if (options.disableParentScroll) {
                    options.oldOverflowStyle = {
                        'overflow-y': options.parent.css('overflow-y'),
                        'overflow-x': options.parent.css('overflow-x')
                    };
                    options.parent.css('overflow', 'hidden');
                }

                if (options.hasBackdrop) {
                    options.backdrop = angular.element('<md-backdrop class="simple-dialog-backdrop" style="z-index: ' + options.zIndex + '">');
                    $mdTheming.inherit(options.backdrop, options.parent);
                    $animate.enter(options.backdrop, options.parent);
                }

                dialogEl.css('z-index', options.zIndex + 1);

                return dialogPopIn(element, options)
                    .then(function () {
                        if (options.escapeToClose) {
                            options.rootElementKeyupCallback = function (e) {
                                if (options.stack.indexOf(options.interimElement) === 0) {
                                    $timeout(function () {
                                        $simpleDialog.cancel('esc', options.interimElement);
                                    });
                                }
                                return true;
                            };
                            mdContextualMonitor.queue(options.rootElementKeyupCallback);
                        }
                        if (options.clickOutsideToClose) {
                            options.dialogClickOutsideCallback = function (e) {
                                // Only close if we click the flex container outside the backdrop
                                if (e.target === options.backdrop[0]) {
                                    $timeout($simpleDialog.cancel);
                                }
                            };
                            options.backdrop.on('click', options.dialogClickOutsideCallback);
                        }
                        closeButton.focus();

                    });


                function findCloseButton() {
                    //If no element with class dialog-close, try to find the last
                    //button child in md-actions and assume it is a close button
                    var closeButton = element[0].querySelector('.dialog-close');
                    if (!closeButton) {
                        var actionButtons = element[0].querySelectorAll('.md-actions button');
                        closeButton = actionButtons[actionButtons.length - 1];
                    }
                    return angular.element(closeButton);
                }

            }

            // On remove function for all dialogs
            function onRemove(scope, element, options) {
                if (options.clickOutsideToClose && options.backdrop) {
                    options.backdrop.off('click', options.dialogClickOutsideCallback);
                }
                if (options.backdrop) {
                    $animate.leave(options.backdrop);
                }
                if (options.disableParentScroll) {
                    options.parent.css(options.oldOverflowStyle);
                    options.parent.css('overflow-wrap', options.parent.css('overflow-wrap') === 'normal' ? 'break-word' : 'normal');
                    $document[0].removeEventListener('scroll', options.captureScroll, true);
                }
                if (options.escapeToClose) {
                    mdContextualMonitor.dequeue(options.rootElementKeyupCallback);
                }
                return dialogPopOut(element, options).then(function() {
                    options.scope.$destroy();
                    element.remove();
                    options.popInTarget && options.popInTarget.focus();
                });

            }

            /**
             * Inject ARIA-specific attributes appropriate for Dialogs
             */
            function configureAria(element) {
                element.attr({
                    'role': 'dialog'
                });

                var dialogContent = element.find('md-content');
                if (dialogContent.length === 0) {
                    dialogContent = element;
                }
                $mdAria.expectAsync(element, 'aria-label', function () {
                    var words = dialogContent.text().split(/\s+/);
                    if (words.length > 3) {
                        words = words.slice(0, 3).concat('...');
                    }
                    return words.join(' ');
                });
            }

            function dialogPopIn(container, options) {
                discoverContainerClass(container, options);
                var dialogEl = container.find(discoverDirective(options)),
                    parentElement = options.parent,
                    clickElement = options.popInTarget && options.popInTarget.length && options.popInTarget,
                    defer = $q.defer();
                parentElement.append(container);
                var promise = defer.promise,
                    nextPromise;
                nextPromise = promise.then(function () {
                    var maybeDefer = $q.defer(),
                        maybePromise = maybeDefer.promise,
                        maybePromiseOnBefore;
                    if (options.onBeforeShow) {
                        maybePromiseOnBefore = options.onBeforeShow(dialogEl, options);
                        if (maybePromiseOnBefore && maybePromiseOnBefore.then) {
                            return maybePromiseOnBefore;
                        }
                    }
                    maybeDefer.resolve();
                    return maybePromise;
                });
                defer.resolve();
                return nextPromise;
            }

            function dialogPopOut(container, options) {
                discoverContainerClass(container, options);
                var dialogEl = container.find(discoverDirective(options)),
                    parentElement = options.parent,
                    type,
                    clickElement = options.popInTarget && options.popInTarget.length && options.popInTarget;
                if (options.onBeforeHide) {
                    options.onBeforeHide(dialogEl, options);
                }
                dialogEl.addClass('transition-out').removeClass('transition-in');
                var promise = dialogTransitionEnd(dialogEl);
                promise.then(function () {
                    if (options.onAfterHide) {
                        options.onAfterHide(dialogEl, options);
                    }
                });
                return promise;
            }

            function transformToClickElement(dialogEl, clickElement) {
                if (clickElement) {
                    var clickRect = clickElement[0].getBoundingClientRect();
                    var dialogRect = dialogEl[0].getBoundingClientRect();

                    var scaleX = Math.min(0.5, clickRect.width / dialogRect.width);
                    var scaleY = Math.min(0.5, clickRect.height / dialogRect.height);

                    dialogEl.css($mdConstant.CSS.TRANSFORM, 'translate3d(' +
                        (-dialogRect.left + clickRect.left + clickRect.width / 2 - dialogRect.width / 2) + 'px,' +
                        (-dialogRect.top + clickRect.top + clickRect.height / 2 - dialogRect.height / 2) + 'px,' +
                        '0) scale(' + scaleX + ',' + scaleY + ')'
                    );
                }
            }

            function dialogTransitionEnd(dialogEl) {
                var deferred = $q.defer();
                dialogEl.on($mdConstant.CSS.TRANSITIONEND, finished);

                function finished(ev) {
                    //Make sure this transitionend didn't bubble up from a child
                    if (ev.target === dialogEl[0]) {
                        dialogEl.off($mdConstant.CSS.TRANSITIONEND, finished);
                        deferred.resolve();
                    }
                }
                return deferred.promise;
            }

        }
    }
    SimpleDialogProvider.$inject = ["$$interimElementProvider"];

})();

/*!
 * Angular Material Design
 * https://github.com/angular/material
 * @license MIT
 * v0.7.1
 */
(function() {
'use strict';

/**
 * @ngdoc module
 * @name material.components.divider
 * @description Divider module!
 */
angular.module('material.components.divider', [
  'material.core'
])
  .directive('mdDivider', MdDividerDirective);

/**
 * @ngdoc directive
 * @name mdDivider
 * @module material.components.divider
 * @restrict E
 *
 * @description
 * Dividers group and separate content within lists and page layouts using strong visual and spatial distinctions. This divider is a thin rule, lightweight enough to not distract the user from content.
 *
 * @param {boolean=} md-inset Add this attribute to activate the inset divider style.
 * @usage
 * <hljs lang="html">
 * <md-divider></md-divider>
 *
 * <md-divider md-inset></md-divider>
 * </hljs>
 *
 */
function MdDividerDirective($mdTheming) {
  return {
    restrict: 'E',
    link: $mdTheming
  };
}
MdDividerDirective.$inject = ["$mdTheming"];
})();

/*!
 * Angular Material Design
 * https://github.com/angular/material
 * @license MIT
 * v0.7.1
 */
(function() {

/**
 * @ngdoc module
 * @name material.components.input
 */

angular.module('material.components.input', [
  'material.core'
])
  .directive('mdInputContainer', mdInputContainerDirective)
  .directive('label', labelDirective)
  .directive('input', inputTextareaDirective)
  .directive('textarea', inputTextareaDirective)
  .directive('mdMaxlength', mdMaxlengthDirective)
  .directive('placeholder', placeholderDirective);

/**
 * @ngdoc directive
 * @name mdInputContainer
 * @module material.components.input
 *
 * @restrict E
 *
 * @description
 * `<md-input-container>` is the parent of any input or textarea element.
 *
 * Input and textarea elements will not behave properly unless the md-input-container 
 * parent is provided.
 *
 * @param md-is-error {expression=} When the given expression evaluates to true, the input container will go into error state. Defaults to erroring if the input has been touched and is invalid.
 *
 * @usage
 * <hljs lang="html">
 *
 * <md-input-container>
 *   <label>Username</label>
 *   <input type="text" ng-model="user.name">
 * </md-input-container>
 *
 * <md-input-container>
 *   <label>Description</label>
 *   <textarea ng-model="user.description"></textarea>
 * </md-input-container>
 *
 * </hljs>
 */
function mdInputContainerDirective($mdTheming, $parse) {
  ContainerCtrl.$inject = ["$scope", "$element", "$attrs"];
  return {
    restrict: 'E',
    link: postLink,
    controller: ContainerCtrl
  };

  function postLink(scope, element, attr) {
    $mdTheming(element);
  }
  function ContainerCtrl($scope, $element, $attrs) {
    var self = this;

    self.isErrorGetter = $attrs.mdIsError && $parse($attrs.mdIsError);

    self.element = $element;
    self.setFocused = function(isFocused) {
      $element.toggleClass('md-input-focused', !!isFocused);
    };
    self.setHasValue = function(hasValue) {
      $element.toggleClass('md-input-has-value', !!hasValue);
    };
    self.setInvalid = function(isInvalid) {
      $element.toggleClass('md-input-invalid', !!isInvalid);
    };
    $scope.$watch(function() {
      return self.label && self.input;
    }, function(hasLabelAndInput) {
      if (hasLabelAndInput && !self.label.attr('for')) {
        self.label.attr('for', self.input.attr('id'));
      }
    });
  }
}
mdInputContainerDirective.$inject = ["$mdTheming", "$parse"];

function labelDirective() {
  return {
    restrict: 'E',
    require: '^?mdInputContainer',
    link: function(scope, element, attr, containerCtrl) {
      if (!containerCtrl) return;

      containerCtrl.label = element;
      scope.$on('$destroy', function() {
        containerCtrl.label = null;
      });
    }
  };
}

/**
 * @ngdoc directive
 * @name input
 * @restrict E
 * @module material.components.input
 *
 * @description
 * Must be placed as a child of an `<md-input-container>`. 
 *
 * Behaves like the [AngularJS input directive](https://docs.angularjs.org/api/ng/directive/input).
 *
 * @usage
 * <hljs lang="html">
 * <md-input-container>
 *   <label>Color</label>
 *   <input type="text" ng-model="color" required md-maxlength="10">
 * </md-input-container>
 * </hljs>
 * <h3>With Errors (uses [ngMessages](https://docs.angularjs.org/api/ngMessages))</h3>
 * <hljs lang="html">
 * <form name="userForm">
 *   <md-input-container>
 *     <label>Last Name</label>
 *     <input name="lastName" ng-model="lastName" required md-maxlength="10" minlength="4">
 *     <div ng-messages="userForm.lastName.$error" ng-show="userForm.bio.$dirty">
 *       <div ng-message="required">This is required!</div>
 *       <div ng-message="md-maxlength">That's too long!</div>
 *       <div ng-message="minlength">That's too short!</div>
 *     </div>
 *   </md-input-container>
 * </form>
 * </hljs>
 *
 * @param {number=} md-maxlength The maximum number of characters allowed in this input. If this is specified, a character counter will be shown underneath the input.
 */
/**
 * @ngdoc directive
 * @name textarea
 * @restrict E
 * @module material.components.input
 *
 * @description
 * Must be placed as a child of an `<md-input-container>`. 
 *
 * Behaves like the [AngularJS input directive](https://docs.angularjs.org/api/ng/directive/textarea).
 *
 * @usage
 * <hljs lang="html">
 * <md-input-container>
 *   <label>Description</label>
 *   <textarea ng-model="description" required minlength="15" md-maxlength="20"></textarea>
 * </md-input-container>
 * </hljs>
 * <h3>With Errors (uses [ngMessages](https://docs.angularjs.org/api/ngMessages))</h3>
 * <hljs lang="html">
 * <form name="userForm">
 *   <md-input-container>
 *     <label>Biography</label>
 *     <textarea name="bio" ng-model="biography" required md-maxlength="150"></textarea>
 *     <div ng-messages="userForm.bio.$error" ng-show="userForm.bio.$dirty">
 *       <div ng-message="required">This is required!</div>
 *       <div ng-message="md-maxlength">That's too long!</div>
 *     </div>
 *   </md-input-container>
 * </form>
 * </hljs>
 *
 * @param {number=} md-maxlength The maximum number of characters allowed in this input. If this is specified, a character counter will be shown underneath the input.
 */
function inputTextareaDirective($mdUtil, $window, $compile, $animate) {
  return {
    restrict: 'E',
    require: ['^?mdInputContainer', '?ngModel'],
    link: postLink
  };
  
  function postLink(scope, element, attr, ctrls) {

    var containerCtrl = ctrls[0];
    var ngModelCtrl = ctrls[1] || $mdUtil.fakeNgModel();
    var isReadonly = angular.isDefined(attr.readonly);

    if ( !containerCtrl ) return;
    if (containerCtrl.input) {
      throw new Error("<md-input-container> can only have *one* <input> or <textarea> child element!");
    }
    containerCtrl.input = element;

    element.addClass('md-input');
    if (!element.attr('id')) {
      element.attr('id', 'input_' + $mdUtil.nextUid());
    }

    if (element[0].tagName.toLowerCase() === 'textarea') {
      setupTextarea();
    }

    function ngModelPipelineCheckValue(arg) {
      containerCtrl.setHasValue(!ngModelCtrl.$isEmpty(arg));
      return arg;
    }
    function inputCheckValue() {
      // An input's value counts if its length > 0,
      // or if the input's validity state says it has bad input (eg string in a number input)
      containerCtrl.setHasValue(element.val().length > 0 || (element[0].validity||{}).badInput);
    }


    var isErrorGetter = containerCtrl.isErrorGetter || function() {
      return ngModelCtrl.$invalid && ngModelCtrl.$touched;
    };
    scope.$watch(isErrorGetter, containerCtrl.setInvalid);
      
    ngModelCtrl.$parsers.push(ngModelPipelineCheckValue);
    ngModelCtrl.$formatters.push(ngModelPipelineCheckValue);

    element.on('input', inputCheckValue);

    if (!isReadonly) {
      element
        .on('focus', function(ev) {
          containerCtrl.setFocused(true);
        })
        .on('blur', function(ev) {
          containerCtrl.setFocused(false);
          inputCheckValue();
        });
    }

    scope.$on('$destroy', function() {
      containerCtrl.setFocused(false);
      containerCtrl.setHasValue(false);
      containerCtrl.input = null;
    });

    function setupTextarea() {
      var node = element[0];
      var onChangeTextarea = $mdUtil.debounce(growTextarea, 1);

      function pipelineListener(value) {
        onChangeTextarea();
        return value;
      }

      if (ngModelCtrl) {
        ngModelCtrl.$formatters.push(pipelineListener);
        ngModelCtrl.$viewChangeListeners.push(pipelineListener);
      } else {
        onChangeTextarea();
      }
      element.on('keydown input', onChangeTextarea);
      element.on('scroll', onScroll);
      angular.element($window).on('resize', onChangeTextarea);

      scope.$on('$destroy', function() {
        angular.element($window).off('resize', onChangeTextarea);
      });

      function growTextarea() {
        node.style.height = "auto";
        var line = node.scrollHeight - node.offsetHeight;
        node.scrollTop = 0;
        var height = node.offsetHeight + (line > 0 ? line : 0);
        node.style.height = height + 'px';
      }

      function onScroll(e) {
        node.scrollTop = 0;
        // for smooth new line adding
        var line = node.scrollHeight - node.offsetHeight;
        var height = node.offsetHeight + line;
        node.style.height = height + 'px';
      }
    }
  }
}
inputTextareaDirective.$inject = ["$mdUtil", "$window", "$compile", "$animate"];

function mdMaxlengthDirective($animate) {
  return {
    restrict: 'A',
    require: ['ngModel', '^mdInputContainer'],
    link: postLink
  };

  function postLink(scope, element, attr, ctrls) {
    var maxlength;
    var ngModelCtrl = ctrls[0];
    var containerCtrl = ctrls[1];
    var charCountEl = angular.element('<div class="md-char-counter">');

    // Stop model from trimming. This makes it so whitespace 
    // over the maxlength still counts as invalid.
    attr.$set('ngTrim', 'false');
    containerCtrl.element.append(charCountEl);

    ngModelCtrl.$formatters.push(renderCharCount);
    ngModelCtrl.$viewChangeListeners.push(renderCharCount);
    element.on('input keydown', function() { 
      renderCharCount(); //make sure it's called with no args
    });

    scope.$watch(attr.mdMaxlength, function(value) {
      maxlength = value;
      if (angular.isNumber(value) && value > 0) {
        if (!charCountEl.parent().length) {
          $animate.enter(charCountEl, containerCtrl.element, 
                         angular.element(containerCtrl.element[0].lastElementChild));
        }
        renderCharCount();
      } else {
        $animate.leave(charCountEl);
      }
    });

    ngModelCtrl.$validators['md-maxlength'] = function(modelValue, viewValue) {
      if (!angular.isNumber(maxlength) || maxlength < 0) {
        return true;
      }
      return ( modelValue || element.val() || viewValue || '' ).length <= maxlength;
    };

    function renderCharCount(value) {
      charCountEl.text( ( element.val() || value || '' ).length + '/' + maxlength );
      return value;
    }
  }
}
mdMaxlengthDirective.$inject = ["$animate"];

function placeholderDirective() {
  return {
    restrict: 'A',
    require: '^^?mdInputContainer',
    link: postLink
  };

  function postLink(scope, element, attr, inputContainer) {
    if (!inputContainer) return;

    var placeholderText = attr.placeholder;
    element.removeAttr('placeholder');

    inputContainer.element.append('<div class="md-placeholder">' + placeholderText + '</div>');
  }
}

})();

/*!
 * Angular Material Design
 * https://github.com/angular/material
 * @license MIT
 * v0.7.1
 */
(function() {
'use strict';

/**
 * @ngdoc module
 * @name material.components.progressCircular
 * @description Circular Progress module!
 */
angular.module('material.components.progressCircular', [
  'material.core'
])
  .directive('mdProgressCircular', MdProgressCircularDirective);

/**
 * @ngdoc directive
 * @name mdProgressCircular
 * @module material.components.progressCircular
 * @restrict E
 *
* @description
 * The circular progress directive is used to make loading content in your app as delightful and painless as possible by minimizing the amount of visual change a user sees before they can view and interact with content.
 *
 * For operations where the percentage of the operation completed can be determined, use a determinate indicator. They give users a quick sense of how long an operation will take.
 *
 * For operations where the user is asked to wait a moment while something finishes up, and it’s not necessary to expose what's happening behind the scenes and how long it will take, use an indeterminate indicator.
 *
 * @param {string} md-mode Select from one of two modes: determinate and indeterminate.
 * @param {number=} value In determinate mode, this number represents the percentage of the circular progress. Default: 0
 * @param {number=} md-diameter This specifies the diamter of the circular progress. Default: 48
 *
 * @usage
 * <hljs lang="html">
 * <md-progress-circular md-mode="determinate" value="..."></md-progress-circular>
 *
 * <md-progress-circular md-mode="determinate" ng-value="..."></md-progress-circular>
 *
 * <md-progress-circular md-mode="determinate" value="..." md-diameter="100"></md-progress-circular>
 *
 * <md-progress-circular md-mode="indeterminate"></md-progress-circular>
 * </hljs>
 */
function MdProgressCircularDirective($$rAF, $mdConstant, $mdTheming) {
  var fillRotations = new Array(101),
    fixRotations = new Array(101);

  for (var i = 0; i < 101; i++) {
    var percent = i / 100;
    var rotation = Math.floor(percent * 180);

    fillRotations[i] = 'rotate(' + rotation.toString() + 'deg)';
    fixRotations[i] = 'rotate(' + (rotation * 2).toString() + 'deg)';
  }

  return {
    restrict: 'E',
    template:
        '<div class="md-spinner-wrapper">' +
          '<div class="md-inner">' +
            '<div class="md-gap"></div>' +
            '<div class="md-left">' +
              '<div class="md-half-circle"></div>' +
            '</div>' +
            '<div class="md-right">' +
              '<div class="md-half-circle"></div>' +
            '</div>' +
          '</div>' +
        '</div>',
    compile: compile
  };

  function compile(tElement, tAttrs, transclude) {
    tElement.attr('aria-valuemin', 0);
    tElement.attr('aria-valuemax', 100);
    tElement.attr('role', 'progressbar');

    return postLink;
  }

  function postLink(scope, element, attr) {
    $mdTheming(element);
    var circle = element[0],
      fill = circle.querySelectorAll('.md-fill, .md-mask.md-full'),
      fix = circle.querySelectorAll('.md-fill.md-fix'),
      i, clamped, fillRotation, fixRotation;

    var diameter = attr.mdDiameter || 48;
    var scale = diameter/48;

    circle.style[$mdConstant.CSS.TRANSFORM] = 'scale(' + scale.toString() + ')';

    attr.$observe('value', function(value) {
      clamped = clamp(value);
      fillRotation = fillRotations[clamped];
      fixRotation = fixRotations[clamped];

      element.attr('aria-valuenow', clamped);

      for (i = 0; i < fill.length; i++) {
        fill[i].style[$mdConstant.CSS.TRANSFORM] = fillRotation;
      }

      for (i = 0; i < fix.length; i++) {
        fix[i].style[$mdConstant.CSS.TRANSFORM] = fixRotation;
      }
    });
  }

  function clamp(value) {
    if (value > 100) {
      return 100;
    }

    if (value < 0) {
      return 0;
    }

    return Math.ceil(value || 0);
  }
}
MdProgressCircularDirective.$inject = ["$$rAF", "$mdConstant", "$mdTheming"];
})();

/*!
 * Angular Material Design
 * https://github.com/angular/material
 * @license MIT
 * v0.7.1
 */
(function() {
'use strict';


/**
 * @ngdoc module
 * @name material.components.progressLinear
 * @description Linear Progress module!
 */
angular.module('material.components.progressLinear', [
  'material.core'
])
  .directive('mdProgressLinear', MdProgressLinearDirective);

/**
 * @ngdoc directive
 * @name mdProgressLinear
 * @module material.components.progressLinear
 * @restrict E
 *
 * @description
 * The linear progress directive is used to make loading content in your app as delightful and painless as possible by minimizing the amount of visual change a user sees before they can view and interact with content. Each operation should only be represented by one activity indicator—for example, one refresh operation should not display both a refresh bar and an activity circle.
 *
 * For operations where the percentage of the operation completed can be determined, use a determinate indicator. They give users a quick sense of how long an operation will take.
 *
 * For operations where the user is asked to wait a moment while something finishes up, and it’s not necessary to expose what's happening behind the scenes and how long it will take, use an indeterminate indicator.
 *
 * @param {string} md-mode Select from one of four modes: determinate, indeterminate, buffer or query.
 * @param {number=} value In determinate and buffer modes, this number represents the percentage of the primary progress bar. Default: 0
 * @param {number=} md-buffer-value In the buffer mode, this number represents the precentage of the secondary progress bar. Default: 0
 *
 * @usage
 * <hljs lang="html">
 * <md-progress-linear md-mode="determinate" value="..."></md-progress-linear>
 *
 * <md-progress-linear md-mode="determinate" ng-value="..."></md-progress-linear>
 *
 * <md-progress-linear md-mode="indeterminate"></md-progress-linear>
 *
 * <md-progress-linear md-mode="buffer" value="..." md-buffer-value="..."></md-progress-linear>
 *
 * <md-progress-linear md-mode="query"></md-progress-linear>
 * </hljs>
 */
function MdProgressLinearDirective($$rAF, $mdConstant, $mdTheming) {

  return {
    restrict: 'E',
    template: '<div class="md-container">' +
      '<div class="md-dashed"></div>' +
      '<div class="md-bar md-bar1"></div>' +
      '<div class="md-bar md-bar2"></div>' +
      '</div>',
    compile: compile
  };
  
  function compile(tElement, tAttrs, transclude) {
    tElement.attr('aria-valuemin', 0);
    tElement.attr('aria-valuemax', 100);
    tElement.attr('role', 'progressbar');

    return postLink;
  }
  function postLink(scope, element, attr) {
    $mdTheming(element);
    var bar1Style = element[0].querySelector('.md-bar1').style,
      bar2Style = element[0].querySelector('.md-bar2').style,
      container = angular.element(element[0].querySelector('.md-container'));

    attr.$observe('value', function(value) {
      if (attr.mdMode == 'query') {
        return;
      }

      var clamped = clamp(value);
      element.attr('aria-valuenow', clamped);
      bar2Style[$mdConstant.CSS.TRANSFORM] = transforms[clamped];
    });

    attr.$observe('mdBufferValue', function(value) {
      bar1Style[$mdConstant.CSS.TRANSFORM] = transforms[clamp(value)];
    });

    $$rAF(function() {
      container.addClass('md-ready');
    });
  }

  function clamp(value) {
    if (value > 100) {
      return 100;
    }

    if (value < 0) {
      return 0;
    }

    return Math.ceil(value || 0);
  }
}
MdProgressLinearDirective.$inject = ["$$rAF", "$mdConstant", "$mdTheming"];


// **********************************************************
// Private Methods
// **********************************************************
var transforms = (function() {
  var values = new Array(101);
  for(var i = 0; i < 101; i++){
    values[i] = makeTransform(i);
  }

  return values;

  function makeTransform(value){
    var scale = value/100;
    var translateX = (value-100)/2;
    return 'translateX(' + translateX.toString() + '%) scale(' + scale.toString() + ', 1)';
  }
})();

})();

/*!
 * Angular Material Design
 * https://github.com/angular/material
 * @license MIT
 * v0.7.1
 */
(function() {
'use strict';


/**
 * @ngdoc module
 * @name material.components.radioButton
 * @description radioButton module!
 */
angular.module('material.components.radioButton', [
  'material.core'
])
  .directive('mdRadioGroup', mdRadioGroupDirective)
  .directive('mdRadioButton', mdRadioButtonDirective);

/**
 * @ngdoc directive
 * @module material.components.radioButton
 * @name mdRadioGroup
 *
 * @restrict E
 *
 * @description
 * The `<md-radio-group>` directive identifies a grouping
 * container for the 1..n grouped radio buttons; specified using nested
 * `<md-radio-button>` tags.
 *
 * As per the [material design spec](http://www.google.com/design/spec/style/color.html#color-ui-color-application)
 * the radio button is in the accent color by default. The primary color palette may be used with
 * the `md-primary` class.
 *
 * Note: `<md-radio-group>` and `<md-radio-button>` handle tabindex differently
 * than the native `<input type='radio'>` controls. Whereas the native controls
 * force the user to tab through all the radio buttons, `<md-radio-group>`
 * is focusable, and by default the `<md-radio-button>`s are not.
 *
 * @param {string} ng-model Assignable angular expression to data-bind to.
 * @param {boolean=} md-no-ink Use of attribute indicates flag to disable ink ripple effects.
 *
 * @usage
 * <hljs lang="html">
 * <md-radio-group ng-model="selected">
 *
 *   <md-radio-button
 *        ng-repeat="d in colorOptions"
 *        ng-value="d.value" aria-label="{{ d.label }}">
 *
 *          {{ d.label }}
 *
 *   </md-radio-button>
 *
 * </md-radio-group>
 * </hljs>
 *
 */
function mdRadioGroupDirective($mdUtil, $mdConstant, $mdTheming) {
  RadioGroupController.prototype = createRadioGroupControllerProto();

  return {
    restrict: 'E',
    controller: ['$element', RadioGroupController],
    require: ['mdRadioGroup', '?ngModel'],
    link: { pre: linkRadioGroup }
  };

  function linkRadioGroup(scope, element, attr, ctrls) {
    $mdTheming(element);
    var rgCtrl = ctrls[0];
    var ngModelCtrl = ctrls[1] || $mdUtil.fakeNgModel();

    function keydownListener(ev) {
      switch(ev.keyCode) {
        case $mdConstant.KEY_CODE.LEFT_ARROW:
        case $mdConstant.KEY_CODE.UP_ARROW:
          ev.preventDefault();
          rgCtrl.selectPrevious();
          break;

        case $mdConstant.KEY_CODE.RIGHT_ARROW:
        case $mdConstant.KEY_CODE.DOWN_ARROW:
          ev.preventDefault();
          rgCtrl.selectNext();
          break;

        case $mdConstant.KEY_CODE.ENTER:
          var form = angular.element($mdUtil.getClosest(element[0], 'form'));
          if (form.length > 0) {
            form.triggerHandler('submit');
          }
          break;
      }
    }

    rgCtrl.init(ngModelCtrl);

    element.attr({
              'role': 'radiogroup',
              'tabIndex': element.attr('tabindex') || '0'
            })
            .on('keydown', keydownListener);

  }

  function RadioGroupController($element) {
    this._radioButtonRenderFns = [];
    this.$element = $element;
  }

  function createRadioGroupControllerProto() {
    return {
      init: function(ngModelCtrl) {
        this._ngModelCtrl = ngModelCtrl;
        this._ngModelCtrl.$render = angular.bind(this, this.render);
      },
      add: function(rbRender) {
        this._radioButtonRenderFns.push(rbRender);
      },
      remove: function(rbRender) {
        var index = this._radioButtonRenderFns.indexOf(rbRender);
        if (index !== -1) {
          this._radioButtonRenderFns.splice(index, 1);
        }
      },
      render: function() {
        this._radioButtonRenderFns.forEach(function(rbRender) {
          rbRender();
        });
      },
      setViewValue: function(value, eventType) {
        this._ngModelCtrl.$setViewValue(value, eventType);
        // update the other radio buttons as well
        this.render();
      },
      getViewValue: function() {
        return this._ngModelCtrl.$viewValue;
      },
      selectNext: function() {
        return changeSelectedButton(this.$element, 1);
      },
      selectPrevious : function() {
        return changeSelectedButton(this.$element, -1);
      },
      setActiveDescendant: function (radioId) {
        this.$element.attr('aria-activedescendant', radioId);
      }
    };
  }
  /**
   * Change the radio group's selected button by a given increment.
   * If no button is selected, select the first button.
   */
  function changeSelectedButton(parent, increment) {
    // Coerce all child radio buttons into an array, then wrap then in an iterator
    var buttons = $mdUtil.iterator(
      Array.prototype.slice.call(parent[0].querySelectorAll('md-radio-button')),
      true
    );

    if (buttons.count()) {
      var validate = function (button) {
        // If disabled, then NOT valid
        return !angular.element(button).attr("disabled");
      };
      var selected = parent[0].querySelector('md-radio-button.md-checked');
      var target = buttons[increment < 0 ? 'previous' : 'next'](selected, validate) || buttons.first();
      // Activate radioButton's click listener (triggerHandler won't create a real click event)
      angular.element(target).triggerHandler('click');


    }
  }

}
mdRadioGroupDirective.$inject = ["$mdUtil", "$mdConstant", "$mdTheming"];

/**
 * @ngdoc directive
 * @module material.components.radioButton
 * @name mdRadioButton
 *
 * @restrict E
 *
 * @description
 * The `<md-radio-button>`directive is the child directive required to be used within `<md-radio-group>` elements.
 *
 * While similar to the `<input type="radio" ng-model="" value="">` directive,
 * the `<md-radio-button>` directive provides ink effects, ARIA support, and
 * supports use within named radio groups.
 *
 * @param {string} ngModel Assignable angular expression to data-bind to.
 * @param {string=} ngChange Angular expression to be executed when input changes due to user
 *    interaction with the input element.
 * @param {string} ngValue Angular expression which sets the value to which the expression should
 *    be set when selected.*
 * @param {string} value The value to which the expression should be set when selected.
 * @param {string=} name Property name of the form under which the control is published.
 * @param {string=} ariaLabel Adds label to radio button for accessibility.
 * Defaults to radio button's text. If no default text is found, a warning will be logged.
 *
 * @usage
 * <hljs lang="html">
 *
 * <md-radio-button value="1" aria-label="Label 1">
 *   Label 1
 * </md-radio-button>
 *
 * <md-radio-button ng-model="color" ng-value="specialValue" aria-label="Green">
 *   Green
 * </md-radio-button>
 *
 * </hljs>
 *
 */
function mdRadioButtonDirective($mdAria, $mdUtil, $mdTheming) {

  var CHECKED_CSS = 'md-checked';

  return {
    restrict: 'E',
    require: '^mdRadioGroup',
    transclude: true,
    template: '<div class="md-container" md-ink-ripple md-ink-ripple-checkbox>' +
                '<div class="md-off"></div>' +
                '<div class="md-on"></div>' +
              '</div>' +
              '<div ng-transclude class="md-label"></div>',
    link: link
  };

  function link(scope, element, attr, rgCtrl) {
    var lastChecked;

    $mdTheming(element);
    configureAria(element, scope);

    rgCtrl.add(render);
    attr.$observe('value', render);

    element
      .on('click', listener)
      .on('$destroy', function() {
        rgCtrl.remove(render);
      });

    function listener(ev) {
      if (element[0].hasAttribute('disabled')) return;

      scope.$apply(function() {
        rgCtrl.setViewValue(attr.value, ev && ev.type);
      });
    }

    function render() {
      var checked = (rgCtrl.getViewValue() == attr.value);
      if (checked === lastChecked) {
        return;
      }
      lastChecked = checked;
      element.attr('aria-checked', checked);
      if (checked) {
        element.addClass(CHECKED_CSS);
        rgCtrl.setActiveDescendant(element.attr('id'));
      } else {
        element.removeClass(CHECKED_CSS);
      }
    }
    /**
     * Inject ARIA-specific attributes appropriate for each radio button
     */
    function configureAria( element, scope ){
      scope.ariaId = buildAriaID();

      element.attr({
        'id' :  scope.ariaId,
        'role' : 'radio',
        'aria-checked' : 'false'
      });

      $mdAria.expectWithText(element, 'aria-label');

      /**
       * Build a unique ID for each radio button that will be used with aria-activedescendant.
       * Preserve existing ID if already specified.
       * @returns {*|string}
       */
      function buildAriaID() {
        return attr.id || ( 'radio' + "_" + $mdUtil.nextUid() );
      }
    }
  }
}
mdRadioButtonDirective.$inject = ["$mdAria", "$mdUtil", "$mdTheming"];

})();

/*!
 * Angular Material Design
 * https://github.com/angular/material
 * @license MIT
 * v0.7.1
 */
(function() {
'use strict';

/**
 * @ngdoc module
 * @name material.components.sidenav
 *
 * @description
 * A Sidenav QP component.
 */
angular.module('material.components.sidenav', [
    'material.core',
    'material.components.backdrop'
  ])
  .factory('$mdSidenav', SidenavService )
  .directive('mdSidenav', SidenavDirective)
  .controller('$mdSidenavController', SidenavController);


/**
 * @private
 * @ngdoc service
 * @name $mdSidenav
 * @module material.components.sidenav
 *
 * @description
 * `$mdSidenav` makes it easy to interact with multiple sidenavs
 * in an app.
 *
 * @usage
 * <hljs lang="js">
 * // Toggle the given sidenav
 * $mdSidenav(componentId).toggle();
 * </hljs>
 * <hljs lang="js">
 * // Open the given sidenav
 * $mdSidenav(componentId).open();
 * </hljs>
 * <hljs lang="js">
 * // Close the given sidenav
 * $mdSidenav(componentId).close();
 * </hljs>
 * <hljs lang="js">
 * // Exposes whether given sidenav is set to be open
 * $mdSidenav(componentId).isOpen();
 * </hljs>
 * <hljs lang="js">
 * // Exposes whether given sidenav is locked open
 * // If this is true, the sidenav will be open regardless of isOpen()
 * $mdSidenav(componentId).isLockedOpen();
 * </hljs>
 */
function SidenavService($mdComponentRegistry, $q) {
  return function(handle) {
    var errorMsg = "SideNav '" + handle + "' is not available!";

    // Lookup the controller instance for the specified sidNav instance
    var instance = $mdComponentRegistry.get(handle);
    if(!instance) {
      $mdComponentRegistry.notFoundError(handle);
    }

    return {
      isOpen: function() {
        return instance && instance.isOpen();
      },
      isLockedOpen: function() {
        return instance && instance.isLockedOpen();
      },
      toggle: function() {
        return instance ? instance.toggle() : $q.reject(errorMsg);
      },
      open: function() {
        return instance ? instance.open() : $q.reject(errorMsg);
      },
      close: function() {
        return instance ? instance.close() : $q.reject(errorMsg);
      }
    };
  };
}
SidenavService.$inject = ["$mdComponentRegistry", "$q"];

/**
 * @ngdoc directive
 * @name mdSidenav
 * @module material.components.sidenav
 * @restrict E
 *
 * @description
 *
 * A Sidenav component that can be opened and closed programatically.
 *
 * By default, upon opening it will slide out on top of the main content area.
 *
 * @usage
 * <hljs lang="html">
 * <div layout="row" ng-controller="MyController">
 *   <md-sidenav md-component-id="left" class="md-sidenav-left">
 *     Left Nav!
 *   </md-sidenav>
 *
 *   <md-content>
 *     Center Content
 *     <md-button ng-click="openLeftMenu()">
 *       Open Left Menu
 *     </md-button>
 *   </md-content>
 *
 *   <md-sidenav md-component-id="right"
 *     md-is-locked-open="$media('min-width: 333px')"
 *     class="md-sidenav-right">
 *     Right Nav!
 *   </md-sidenav>
 * </div>
 * </hljs>
 *
 * <hljs lang="js">
 * var app = angular.module('myApp', ['ngMaterial']);
 * app.controller('MyController', function($scope, $mdSidenav) {
 *   $scope.openLeftMenu = function() {
 *     $mdSidenav('left').toggle();
 *   };
 * });
 * </hljs>
 *
 * @param {expression=} md-is-open A model bound to whether the sidenav is opened.
 * @param {string=} md-component-id componentId to use with $mdSidenav service.
 * @param {expression=} md-is-locked-open When this expression evalutes to true,
 * the sidenav 'locks open': it falls into the content's flow instead
 * of appearing over it. This overrides the `is-open` attribute.
 *
 * A $media() function is exposed to the is-locked-open attribute, which
 * can be given a media query or one of the `sm`, `gt-sm`, `md`, `gt-md`, `lg` or `gt-lg` presets.
 * Examples:
 *
 *   - `<md-sidenav md-is-locked-open="shouldLockOpen"></md-sidenav>`
 *   - `<md-sidenav md-is-locked-open="$media('min-width: 1000px')"></md-sidenav>`
 *   - `<md-sidenav md-is-locked-open="$media('sm')"></md-sidenav>` (locks open on small screens)
 */
function SidenavDirective($timeout, $animate, $parse, $mdMedia, $mdConstant, $compile, $mdTheming, $q, $document, mdContextualMonitor) {
  return {
    restrict: 'E',
    scope: {
      isOpen: '=?mdIsOpen'
    },
    controller: '$mdSidenavController',
    compile: function(element) {
      element.addClass('md-closed');
      element.attr('tabIndex', '-1');
      return postLink;
    }
  };

  /**
   * Directive Post Link function...
   */
  function postLink(scope, element, attr, sidenavCtrl) {
    var triggeringElement = null;
    var promise = $q.when(true);

    var isLockedOpenParsed = $parse(attr.mdIsLockedOpen);
    var isLocked = function() {
      return isLockedOpenParsed(scope.$parent, {
        $media: $mdMedia
      });
    };
    var backdrop = $compile(
      '<md-backdrop class="md-sidenav-backdrop md-opaque ng-enter">'
    )(scope);

    element.on('$destroy', sidenavCtrl.destroy);
    $mdTheming.inherit(backdrop, element);

    var initialWidth = element.css('width');
    var resize = function () {
      var tolerate = $(window).width() - 56;
      if (tolerate > initialWidth) {
        element.css({
          width: '',
          'min-width': ''
        });
        return;
      }
      if (element.width() > tolerate) {
        element.css({
          width: tolerate,
          'min-width': tolerate
        });
      }
    };

    resize();

    scope.$watch(isLocked, updateIsLocked);
    scope.$watch('isOpen', updateIsOpen);
    scope.$on('$destroy', function () {
      $(window).off('resize', resize);
    });


    // Publish special accessor for the Controller instance
    sidenavCtrl.$toggleOpen = toggleOpen;

    /**
     * Toggle the DOM classes to indicate `locked`
     * @param isLocked
     */
    function updateIsLocked(isLocked, oldValue) {
      scope.isLockedOpen = isLocked;
      if (isLocked === oldValue) {
        element.toggleClass('md-locked-open', !!isLocked);
      } else {
        $animate[isLocked ? 'addClass' : 'removeClass'](element, 'md-locked-open');
      }
      backdrop.toggleClass('md-locked-open', !!isLocked);
    }

    /**
     * Toggle the SideNav view and attach/detach listeners
     * @param isOpen
     */
    function updateIsOpen(isOpen) {
      var parent = element.parent();

      backdrop[isOpen ? 'on' : 'off']('click', close);
      mdContextualMonitor[isOpen ? 'queue' : 'dequeue'](onKeyDown);

      if ( isOpen ) {
        // Capture upon opening..
        triggeringElement = $document[0].activeElement;
      }

      return promise = $q.all([
        $animate[isOpen ? 'enter' : 'leave'](backdrop, parent),
        $animate[isOpen ? 'removeClass' : 'addClass'](element, 'md-closed').then(function() {
          // If we opened, and haven't closed again before the animation finished
          if (scope.isOpen) {
            element.focus();
          }
        })
      ]);
    }

    /**
     * Toggle the sideNav view and publish a promise to be resolved when
     * the view animation finishes.
     *
     * @param isOpen
     * @returns {*}
     */
    function toggleOpen( isOpen ) {
      if (scope.isOpen == isOpen ) {

        return $q.when(true);

      } else {
        var deferred = $q.defer();

        // Toggle value to force an async `updateIsOpen()` to run
        scope.isOpen = isOpen;

        $timeout(function() {

          // When the current `updateIsOpen()` animation finishes
          promise.then(function(result){

            if ( !scope.isOpen ) {
              // reset focus to originating element (if available) upon close
              triggeringElement && triggeringElement.focus();
              triggeringElement = null;
            }

            if (isOpen) {
              resize();
            }

            deferred.resolve(result);
          });

        },0,false);

        return deferred.promise;
      }
    }

    /**
     * Auto-close sideNav when the `escape` key is pressed.
     * @param evt
     */
    function onKeyDown(ev) {
      close(ev);
      return true;
    }

    /**
     * With backdrop `clicks` or `escape` key-press, immediately
     * apply the CSS close transition... Then notify the controller
     * to close() and perform its own actions.
     */
    function close(ev) {
      ev.preventDefault();
      ev.stopPropagation();

      return sidenavCtrl.close();
    }

  }
}
SidenavDirective.$inject = ["$timeout", "$animate", "$parse", "$mdMedia", "$mdConstant", "$compile", "$mdTheming", "$q", "$document", "mdContextualMonitor"];

/*
 * @private
 * @ngdoc controller
 * @name SidenavController
 * @module material.components.sidenav
 *
 */
function SidenavController($scope, $element, $attrs, $mdComponentRegistry, $q) {

  var self = this;

  // Use Default internal method until overridden by directive postLink

  self.$toggleOpen = function() { return $q.when($scope.isOpen); };
  self.isOpen = function() { return !!$scope.isOpen; };
  self.isLockedOpen = function() { return !!$scope.isLockedOpen; };
  self.open   = function() { return self.$toggleOpen( true );  };
  self.close  = function() { return self.$toggleOpen( false ); };
  self.toggle = function() { return self.$toggleOpen( !$scope.isOpen );  };

  self.destroy = $mdComponentRegistry.register(self, $attrs.mdComponentId);
}
SidenavController.$inject = ["$scope", "$element", "$attrs", "$mdComponentRegistry", "$q"];



})();

/*!
 * Angular Material Design
 * https://github.com/angular/material
 * @license MIT
 * v0.7.1
 */
(function() {
'use strict';

/*
 * @ngdoc module
 * @name material.components.sticky
 * @description
 *
 * Sticky effects for md
 */

angular.module('material.components.sticky', [
  'material.core',
  'material.components.content'
])
  .factory('$mdSticky', MdSticky);

/*
 * @ngdoc service
 * @name $mdSticky
 * @module material.components.sticky
 *
 * @description
 * The `$mdSticky`service provides a mixin to make elements sticky.
 *
 * @returns A `$mdSticky` function that takes three arguments:
 *   - `scope`
 *   - `element`: The element that will be 'sticky'
 *   - `elementClone`: A clone of the element, that will be shown
 *     when the user starts scrolling past the original element.
 *     If not provided, it will use the result of `element.clone()`.
 */

function MdSticky($document, $mdConstant, $compile, $$rAF, $mdUtil) {

  var browserStickySupport = checkStickySupport();

  /**
   * Registers an element as sticky, used internally by directives to register themselves
   */
  return function registerStickyElement(scope, element, stickyClone) {
    var contentCtrl = element.controller('mdContent');
    if (!contentCtrl) return;

    if (browserStickySupport) {
      element.css({
        position: browserStickySupport,
        top: 0,
        'z-index': 2
      });
    } else {
      var $$sticky = contentCtrl.$element.data('$$sticky');
      if (!$$sticky) {
        $$sticky = setupSticky(contentCtrl);
        contentCtrl.$element.data('$$sticky', $$sticky);
      }

      var deregister = $$sticky.add(element, stickyClone || element.clone());
      scope.$on('$destroy', deregister);
    }
  };

  function setupSticky(contentCtrl) {
    var contentEl = contentCtrl.$element;

    // Refresh elements is very expensive, so we use the debounced
    // version when possible.
    var debouncedRefreshElements = $$rAF.throttle(refreshElements);

    // setupAugmentedScrollEvents gives us `$scrollstart` and `$scroll`,
    // more reliable than `scroll` on android.
    setupAugmentedScrollEvents(contentEl);
    contentEl.on('$scrollstart', debouncedRefreshElements);
    contentEl.on('$scroll', onScroll);

    var self;
    var stickyBaseoffset = contentEl.prop('offsetTop');
    return self = {
      prev: null,
      current: null, //the currently stickied item
      next: null,
      items: [],
      add: add,
      refreshElements: refreshElements
    };

    /***************
     * Public
     ***************/
    // Add an element and its sticky clone to this content's sticky collection
    function add(element, stickyClone) {
      stickyClone.addClass('md-sticky-clone');
      stickyClone.css('top', stickyBaseoffset + 'px');

      var item = {
        element: element,
        clone: stickyClone
      };
      self.items.push(item);

      contentEl.parent().prepend(item.clone);

      debouncedRefreshElements();

      return function remove() {
        self.items.forEach(function(item, index) {
          if (item.element[0] === element[0]) {
            self.items.splice(index, 1);
            item.clone.remove();
          }
        });
        debouncedRefreshElements();
      };
    }

    function refreshElements() {
      // Sort our collection of elements by their current position in the DOM.
      // We need to do this because our elements' order of being added may not
      // be the same as their order of display.
      self.items.forEach(refreshPosition);
      self.items = self.items.sort(function(a, b) {
        return a.top < b.top ? -1 : 1;
      });

      // Find which item in the list should be active, 
      // based upon the content's current scroll position
      var item;
      var currentScrollTop = contentEl.prop('scrollTop');
      for (var i = self.items.length - 1; i >= 0; i--) {
        if (currentScrollTop > self.items[i].top) {
          item = self.items[i];
          break;
        }
      }
      setCurrentItem(item);
    }


    /***************
     * Private
     ***************/

    // Find the `top` of an item relative to the content element,
    // and also the height.
    function refreshPosition(item) {
      // Find the top of an item by adding to the offsetHeight until we reach the 
      // content element.
      var current = item.element[0];
      item.top = 0;
      item.left = 0;
      while (current && current !== contentEl[0]) {
        item.top += current.offsetTop;
        item.left += current.offsetLeft;
        current = current.offsetParent;
      }
      item.height = item.element.prop('offsetHeight');
      item.clone.css('margin-left', item.left + 'px');
    }


    // As we scroll, push in and select the correct sticky element.
    function onScroll() {
      var scrollTop = contentEl.prop('scrollTop');
      var isScrollingDown = scrollTop > (onScroll.prevScrollTop || 0);
      onScroll.prevScrollTop = scrollTop;

      // At the top?
      if (scrollTop === 0) {
        setCurrentItem(null);

      // Going to next item?
      } else if (isScrollingDown && self.next) {
        if (self.next.top - scrollTop <= 0) {
          // Sticky the next item if we've scrolled past its position.
          setCurrentItem(self.next);
        } else if (self.current) {
          // Push the current item up when we're almost at the next item.
          if (self.next.top - scrollTop <= self.next.height) {
            translate(self.current, self.next.top - self.next.height - scrollTop);
          } else {
            translate(self.current, null);
          }
        }
        
      // Scrolling up with a current sticky item?
      } else if (!isScrollingDown && self.current) {
        if (scrollTop < self.current.top) {
          // Sticky the previous item if we've scrolled up past
          // the original position of the currently stickied item.
          setCurrentItem(self.prev);
        }
        // Scrolling up, and just bumping into the item above (just set to current)?
        // If we have a next item bumping into the current item, translate
        // the current item up from the top as it scrolls into view.
        if (self.current && self.next) {
          if (scrollTop >= self.next.top - self.current.height) {
            translate(self.current, self.next.top - scrollTop - self.current.height);
          } else {
            translate(self.current, null);
          }
        }
      }
    }
     
   function setCurrentItem(item) {
     if (self.current === item) return;
     // Deactivate currently active item
     if (self.current) {
       translate(self.current, null);
       setStickyState(self.current, null);
     }

     // Activate new item if given
     if (item) {
       setStickyState(item, 'active');
     }

     self.current = item;
     var index = self.items.indexOf(item);
     // If index === -1, index + 1 = 0. It works out.
     self.next = self.items[index + 1];
     self.prev = self.items[index - 1];
     setStickyState(self.next, 'next');
     setStickyState(self.prev, 'prev');
   }

   function setStickyState(item, state) {
     if (!item || item.state === state) return;
     if (item.state) {
       item.clone.attr('sticky-prev-state', item.state);
       item.element.attr('sticky-prev-state', item.state);
     }
     item.clone.attr('sticky-state', state);
     item.element.attr('sticky-state', state);
     item.state = state;
   }

   function translate(item, amount) {
     if (!item) return;
     if (amount === null || amount === undefined) {
       if (item.translateY) {
         item.translateY = null;
         item.clone.css($mdConstant.CSS.TRANSFORM, '');
       }
     } else {
       item.translateY = amount;
       item.clone.css(
         $mdConstant.CSS.TRANSFORM, 
         'translate3d(' + item.left + 'px,' + amount + 'px,0)'
       );
     }
   }
  }

  // Function to check for browser sticky support
  function checkStickySupport($el) {
    var stickyProp;
    var testEl = angular.element('<div>');
    $document[0].body.appendChild(testEl[0]);

    var stickyProps = ['sticky', '-webkit-sticky'];
    for (var i = 0; i < stickyProps.length; ++i) {
      testEl.css({position: stickyProps[i], top: 0, 'z-index': 2});
      if (testEl.css('position') == stickyProps[i]) {
        stickyProp = stickyProps[i];
        break;
      }
    }
    testEl.remove();
    return stickyProp;
  }

  // Android 4.4 don't accurately give scroll events.
  // To fix this problem, we setup a fake scroll event. We say:
  // > If a scroll or touchmove event has happened in the last DELAY milliseconds, 
  //   then send a `$scroll` event every animationFrame.
  // Additionally, we add $scrollstart and $scrollend events.
  function setupAugmentedScrollEvents(element) {
    var SCROLL_END_DELAY = 200;
    var isScrolling;
    var lastScrollTime;
    element.on('scroll touchmove', function() {
      if (!isScrolling) {
        isScrolling = true;
        $$rAF(loopScrollEvent);
        element.triggerHandler('$scrollstart');
      }
      element.triggerHandler('$scroll');
      lastScrollTime = +$mdUtil.now();
    });

    function loopScrollEvent() {
      if (+$mdUtil.now() - lastScrollTime > SCROLL_END_DELAY) {
        isScrolling = false;
        element.triggerHandler('$scrollend');
      } else {
        element.triggerHandler('$scroll');
        $$rAF(loopScrollEvent);
      }
    }
  }

}
MdSticky.$inject = ["$document", "$mdConstant", "$compile", "$$rAF", "$mdUtil"];
})();

/*!
 * Angular Material Design
 * https://github.com/angular/material
 * @license MIT
 * v0.7.1
 */
(function() {
'use strict';

/**
 * @ngdoc module
 * @name material.components.subheader
 * @description
 * SubHeader module
 *
 *  Subheaders are special list tiles that delineate distinct sections of a
 *  list or grid list and are typically related to the current filtering or
 *  sorting criteria. Subheader tiles are either displayed inline with tiles or
 *  can be associated with content, for example, in an adjacent column.
 *
 *  Upon scrolling, subheaders remain pinned to the top of the screen and remain
 *  pinned until pushed on or off screen by the next subheader. @see [Material
 *  Design Specifications](https://www.google.com/design/spec/components/subheaders.html)
 *
 *  > To improve the visual grouping of content, use the system color for your subheaders.
 *
 */
angular.module('material.components.subheader', [
  'material.core',
  'material.components.sticky'
])
  .directive('mdSubheader', MdSubheaderDirective);

/**
 * @ngdoc directive
 * @name mdSubheader
 * @module material.components.subheader
 *
 * @restrict E
 *
 * @description
 * The `<md-subheader>` directive is a subheader for a section
 *
 * @usage
 * <hljs lang="html">
 * <md-subheader>Online Friends</md-subheader>
 * </hljs>
 */

function MdSubheaderDirective($mdSticky, $compile, $mdTheming) {
  return {
    restrict: 'E',
    replace: true,
    transclude: true,
    template: 
      '<h2 class="md-subheader">' +
        '<span class="md-subheader-content"></span>' +
      '</h2>',
    compile: function(element, attr, transclude) {
      var outerHTML = element[0].outerHTML;
      return function postLink(scope, element, attr) {
        $mdTheming(element);
        function getContent(el) {
          return angular.element(el[0].querySelector('.md-subheader-content'));
        }

        // Transclude the user-given contents of the subheader
        // the conventional way.
        transclude(scope, function(clone) {
          getContent(element).append(clone);
        });

        // Create another clone, that uses the outer and inner contents
        // of the element, that will be 'stickied' as the user scrolls.
        transclude(scope, function(clone) {
          var stickyClone = $compile(angular.element(outerHTML))(scope);
          $mdTheming(stickyClone);
          getContent(stickyClone).append(clone);
          $mdSticky(scope, element, stickyClone);
        });
      };
    }
  };
}
MdSubheaderDirective.$inject = ["$mdSticky", "$compile", "$mdTheming"];
})();

/*!
 * Angular Material Design
 * https://github.com/angular/material
 * @license MIT
 * v0.7.1
 */
(function() {
'use strict';


/**
 * @ngdoc module
 * @name material.components.swipe
 * @description Swipe module!
 */
/**
 * @ngdoc directive
 * @module material.components.swipe
 * @name mdSwipeLeft
 *
 * @restrict A
 *
 * @description
 * The md-swipe-left directives allows you to specify custom behavior when an element is swiped
 * left.
 *
 * @usage
 * <hljs lang="html">
 * <div md-swipe-left="onSwipeLeft()">Swipe me left!</div>
 * </hljs>
 */

/**
 * @ngdoc directive
 * @module material.components.swipe
 * @name mdSwipeRight
 *
 * @restrict A
 *
 * @description
 * The md-swipe-right directives allows you to specify custom behavior when an element is swiped
 * right.
 *
 * @usage
 * <hljs lang="html">
 * <div md-swipe-right="onSwipeRight()">Swipe me right!</div>
 * </hljs>
 */

var module = angular.module('material.components.swipe',[]);

['SwipeLeft', 'SwipeRight'].forEach(function(name) {
  var directiveName = 'md' + name;
  var eventName = '$md.' + name.toLowerCase();

  module.directive(directiveName, /*@ngInject*/ ["$parse", function($parse) {
    return {
      restrict: 'A',
      link: postLink
    };

    function postLink(scope, element, attr) {
      var fn = $parse(attr[directiveName]);

      element.on(eventName, function(ev) {
        scope.$apply(function() {
          fn(scope, {
            $event: ev
          });
        });
      });

    }
  }]);
});

})();

/*!
 * Angular Material Design
 * https://github.com/angular/material
 * @license MIT
 * v0.7.1
 */
(function() {
'use strict';

/**
 * @private
 * @ngdoc module
 * @name material.components.switch
 */

angular.module('material.components.switch', [
  'material.core',
  'material.components.checkbox'
])
  .directive('mdSwitch', MdSwitch);

/**
 * @private
 * @ngdoc directive
 * @module material.components.switch
 * @name mdSwitch
 * @restrict E
 *
 * The switch directive is used very much like the normal [angular checkbox](https://docs.angularjs.org/api/ng/input/input%5Bcheckbox%5D).
 *
 * As per the [material design spec](http://www.google.com/design/spec/style/color.html#color-ui-color-application)
 * the switch is in the accent color by default. The primary color palette may be used with
 * the `md-primary` class.
 *
 * @param {string} ng-model Assignable angular expression to data-bind to.
 * @param {string=} name Property name of the form under which the control is published.
 * @param {expression=} ng-true-value The value to which the expression should be set when selected.
 * @param {expression=} ng-false-value The value to which the expression should be set when not selected.
 * @param {string=} ng-change Angular expression to be executed when input changes due to user interaction with the input element.
 * @param {boolean=} md-no-ink Use of attribute indicates use of ripple ink effects.
 * @param {string=} aria-label Publish the button label used by screen-readers for accessibility. Defaults to the switch's text.
 *
 * @usage
 * <hljs lang="html">
 * <md-switch ng-model="isActive" aria-label="Finished?">
 *   Finished ?
 * </md-switch>
 *
 * <md-switch md-no-ink ng-model="hasInk" aria-label="No Ink Effects">
 *   No Ink Effects
 * </md-switch>
 *
 * <md-switch ng-disabled="true" ng-model="isDisabled" aria-label="Disabled">
 *   Disabled
 * </md-switch>
 *
 * </hljs>
 */
function MdSwitch(mdCheckboxDirective, $mdTheming, $mdUtil, $document, $mdConstant, $parse, $$rAF, $mdGesture) {
  var checkboxDirective = mdCheckboxDirective[0];

  return {
    restrict: 'E',
    transclude: true,
    template:
      '<div class="md-container">' +
        '<div class="md-bar"></div>' +
        '<div class="md-thumb-container">' +
          '<div class="md-thumb" md-ink-ripple md-ink-ripple-checkbox></div>' +
        '</div>'+
      '</div>' +
      '<div ng-transclude class="md-label">' +
      '</div>',
    require: '?ngModel',
    compile: compile
  };

  function compile(element, attr) {
    var checkboxLink = checkboxDirective.compile(element, attr);
    // no transition on initial load
    element.addClass('md-dragging');

    return function (scope, element, attr, ngModel) {
      ngModel = ngModel || $mdUtil.fakeNgModel();
      var disabledGetter = $parse(attr.ngDisabled);
      var thumbContainer = angular.element(element[0].querySelector('.md-thumb-container'));
      var switchContainer = angular.element(element[0].querySelector('.md-container'));

      // no transition on initial load
      $$rAF(function() {
        element.removeClass('md-dragging');
      });

      checkboxLink(scope, element, attr, ngModel);

      if (angular.isDefined(attr.ngDisabled)) {
        scope.$watch(disabledGetter, function(isDisabled) {
          element.attr('tabindex', isDisabled ? -1 : 0);
        });
      }

      // These events are triggered by setup drag
      $mdGesture.register(switchContainer, 'drag');
      switchContainer
        .on('$md.dragstart', onDragStart)
        .on('$md.drag', onDrag)
        .on('$md.dragend', onDragEnd);

      var drag;
      function onDragStart(ev) {
        // Don't go if ng-disabled===true
        if (disabledGetter(scope)) return;
        ev.stopPropagation();

        element.addClass('md-dragging');
        drag = {
          width: thumbContainer.prop('offsetWidth')
        };
        element.removeClass('transition');
      }

      function onDrag(ev) {
        if (!drag) return;
        ev.stopPropagation();
        ev.srcEvent && ev.srcEvent.preventDefault();

        var percent = ev.pointer.distanceX / drag.width;

        //if checked, start from right. else, start from left
        var translate = ngModel.$viewValue ?  1 + percent : percent;
        // Make sure the switch stays inside its bounds, 0-1%
        translate = Math.max(0, Math.min(1, translate));

        thumbContainer.css($mdConstant.CSS.TRANSFORM, 'translate3d(' + (100*translate) + '%,0,0)');
        drag.translate = translate;
      }

      function onDragEnd(ev) {
        if (!drag) return;
        ev.stopPropagation();

        element.removeClass('md-dragging');
        thumbContainer.css($mdConstant.CSS.TRANSFORM, '');

        // We changed if there is no distance (this is a click a click),
        // or if the drag distance is >50% of the total.
        var isChanged = ngModel.$viewValue ? drag.translate < 0.5 : drag.translate > 0.5;
        if (isChanged) {
          applyModelValue(!ngModel.$viewValue);
        }
        drag = null;
      }

      function applyModelValue(newValue) {
        scope.$apply(function() {
          ngModel.$setViewValue(newValue);
          ngModel.$render();
        });
      }

    };
  }


}
MdSwitch.$inject = ["mdCheckboxDirective", "$mdTheming", "$mdUtil", "$document", "$mdConstant", "$parse", "$$rAF", "$mdGesture"];

})();

/*!
 * Angular Material Design
 * https://github.com/angular/material
 * @license MIT
 * v0.7.1
 */
(function() {
'use strict';

/**
 * @ngdoc module
 * @name material.components.textField
 * @description
 * Form
 */
angular.module('material.components.textField', [
  'material.core'
])
  .directive('mdInputGroup', mdInputGroupDirective)
  .directive('mdInput', mdInputDirective)
  .directive('mdTextFloat', mdTextFloatDirective);


function mdTextFloatDirective($mdTheming, $mdUtil, $parse, $log) {
  return {
    restrict: 'E',
    replace: true,
    scope : {
      fid : '@?mdFid',
      label : '@?',
      value : '=ngModel'
    },
    compile : function(element, attr) {

      $log.warn('<md-text-float> is deprecated. Please use `<md-input-container>` and `<input>`.' + 
                'More information at http://material.angularjs.org/#/api/material.components.input/directive/mdInputContainer');

      if ( angular.isUndefined(attr.mdFid) ) {
        attr.mdFid = $mdUtil.nextUid();
      }

      return {
        pre : function(scope, element, attrs) {
          var disabledParsed = $parse(attrs.ngDisabled);
          scope.isDisabled = function() {
            return disabledParsed(scope.$parent);
          };

          scope.inputType = attrs.type || "text";
        },
        post: $mdTheming
      };
    },
    template:
    '<md-input-group tabindex="-1">' +
    ' <label for="{{fid}}" >{{label}}</label>' +
    ' <md-input id="{{fid}}" ng-disabled="isDisabled()" ng-model="value" type="{{inputType}}"></md-input>' +
    '</md-input-group>'
  };
}
mdTextFloatDirective.$inject = ["$mdTheming", "$mdUtil", "$parse", "$log"];

function mdInputGroupDirective($log) {
  return {
    restrict: 'CE',
    controller: ['$element', function($element) {

      $log.warn('<md-input-group> is deprecated. Please use `<md-input-container>` and `<input>`.' + 
                'More information at http://material.angularjs.org/#/api/material.components.input/directive/mdInputContainer');
      this.setFocused = function(isFocused) {
        $element.toggleClass('md-input-focused', !!isFocused);
      };
      this.setHasValue = function(hasValue) {
        $element.toggleClass('md-input-has-value', hasValue );
      };
    }]
  };

}
mdInputGroupDirective.$inject = ["$log"];

function mdInputDirective($mdUtil, $log) {
  return {
    restrict: 'E',
    replace: true,
    template: '<input >',
    require: ['^?mdInputGroup', '?ngModel'],
    link: function(scope, element, attr, ctrls) {
      if ( !ctrls[0] ) return;

      $log.warn('<md-input> is deprecated. Please use `<md-input-container>` and `<input>`.' + 
                'More information at http://material.angularjs.org/#/api/material.components.input/directive/mdInputContainer');

      var inputGroupCtrl = ctrls[0];
      var ngModelCtrl = ctrls[1];

      scope.$watch(scope.isDisabled, function(isDisabled) {
        element.attr('aria-disabled', !!isDisabled);
        element.attr('tabindex', !!isDisabled);
      });
      element.attr('type', attr.type || element.parent().attr('type') || "text");

      // When the input value changes, check if it "has" a value, and
      // set the appropriate class on the input group
      if (ngModelCtrl) {
        //Add a $formatter so we don't use up the render function
        ngModelCtrl.$formatters.push(function(value) {
          inputGroupCtrl.setHasValue( isNotEmpty(value) );
          return value;
        });
      }

      element
        .on('input', function() {
          inputGroupCtrl.setHasValue( isNotEmpty() );
        })
        .on('focus', function(e) {
          // When the input focuses, add the focused class to the group
          inputGroupCtrl.setFocused(true);
        })
        .on('blur', function(e) {
          // When the input blurs, remove the focused class from the group
          inputGroupCtrl.setFocused(false);
          inputGroupCtrl.setHasValue( isNotEmpty() );
        });

      scope.$on('$destroy', function() {
        inputGroupCtrl.setFocused(false);
        inputGroupCtrl.setHasValue(false);
      });


      function isNotEmpty(value) {
        value = angular.isUndefined(value) ? element.val() : value;
        return (angular.isDefined(value) && (value!==null) &&
               (value.toString().trim() !== ""));
      }
    }
  };
}
mdInputDirective.$inject = ["$mdUtil", "$log"];

})();

/*!
 * Angular Material Design
 * https://github.com/angular/material
 * @license MIT
 * v0.7.1
 */
(function() {
'use strict';

/**
 * @ngdoc module
 * @name material.components.toolbar
 */
angular.module('material.components.toolbar', [
  'material.core',
  'material.components.content'
])
  .directive('mdToolbar', mdToolbarDirective);

/**
 * @ngdoc directive
 * @name mdToolbar
 * @module material.components.toolbar
 * @restrict E
 * @description
 * `md-toolbar` is used to place a toolbar in your app.
 *
 * Toolbars are usually used above a content area to display the title of the
 * current page, and show relevant action buttons for that page.
 *
 * You can change the height of the toolbar by adding either the
 * `md-medium-tall` or `md-tall` class to the toolbar.
 *
 * @usage
 * <hljs lang="html">
 * <div layout="column" layout-fill>
 *   <md-toolbar>
 *
 *     <div class="md-toolbar-tools">
 *       <span>My App's Title</span>
 *
 *       <!-- fill up the space between left and right area -->
 *       <span flex></span>
 *
 *       <md-button>
 *         Right Bar Button
 *       </md-button>
 *     </div>
 *
 *   </md-toolbar>
 *   <md-content>
 *     Hello!
 *   </md-content>
 * </div>
 * </hljs>
 *
 * @param {boolean=} md-scroll-shrink Whether the header should shrink away as
 * the user scrolls down, and reveal itself as the user scrolls up.
 * Note: for scrollShrink to work, the toolbar must be a sibling of a
 * `md-content` element, placed before it. See the scroll shrink demo.
 *
 *
 * @param {number=} md-shrink-speed-factor How much to change the speed of the toolbar's
 * shrinking by. For example, if 0.25 is given then the toolbar will shrink
 * at one fourth the rate at which the user scrolls down. Default 0.5.
 */
function mdToolbarDirective($$rAF, $mdConstant, $mdUtil, $mdTheming) {

  return {
    restrict: 'E',
    controller: angular.noop,
    link: function(scope, element, attr) {
      $mdTheming(element);

      if (angular.isDefined(attr.mdScrollShrink)) {
        setupScrollShrink();
      }

      function setupScrollShrink() {
        // Current "y" position of scroll
        var y = 0;
        // Store the last scroll top position
        var prevScrollTop = 0;

        var shrinkSpeedFactor = attr.mdShrinkSpeedFactor || 0.5;

        var toolbarHeight;
        var contentElement;

        var debouncedContentScroll = $$rAF.throttle(onContentScroll);
        var debouncedUpdateHeight = $mdUtil.debounce(updateToolbarHeight, 5 * 1000);

        // Wait for $mdContentLoaded event from mdContent directive.
        // If the mdContent element is a sibling of our toolbar, hook it up
        // to scroll events.
        scope.$on('$mdContentLoaded', onMdContentLoad);

        function onMdContentLoad($event, newContentEl) {
          // Toolbar and content must be siblings
          if (element.parent()[0] === newContentEl.parent()[0]) {
            // unhook old content event listener if exists
            if (contentElement) {
              contentElement.off('scroll', debouncedContentScroll);
            }

            newContentEl.on('scroll', debouncedContentScroll);
            newContentEl.attr('scroll-shrink', 'true');

            contentElement = newContentEl;
            $$rAF(updateToolbarHeight);
          }
        }

        function updateToolbarHeight() {
          toolbarHeight = element.prop('offsetHeight');
          // Add a negative margin-top the size of the toolbar to the content el.
          // The content will start transformed down the toolbarHeight amount,
          // so everything looks normal.
          //
          // As the user scrolls down, the content will be transformed up slowly
          // to put the content underneath where the toolbar was.
          contentElement.css(
            'margin-top',
            (-toolbarHeight * shrinkSpeedFactor) + 'px'
          );
          onContentScroll();
        }

        function onContentScroll(e) {
          var scrollTop = e ? e.target.scrollTop : prevScrollTop;

          debouncedUpdateHeight();

          y = Math.min(
            toolbarHeight / shrinkSpeedFactor,
            Math.max(0, y + scrollTop - prevScrollTop)
          );

          element.css(
            $mdConstant.CSS.TRANSFORM,
            'translate3d(0,' + (-y * shrinkSpeedFactor) + 'px,0)'
          );
          contentElement.css(
            $mdConstant.CSS.TRANSFORM,
            'translate3d(0,' + ((toolbarHeight - y) * shrinkSpeedFactor) + 'px,0)'
          );

          prevScrollTop = scrollTop;
        }

      }

    }
  };

}
mdToolbarDirective.$inject = ["$$rAF", "$mdConstant", "$mdUtil", "$mdTheming"];
})();

/*!
 * Angular Material Design
 * https://github.com/angular/material
 * @license MIT
 * v0.7.1
 */
(function() {
'use strict';

/**
 * @ngdoc module
 * @name material.components.whiteframe
 */
angular.module('material.components.whiteframe', []);
})();

angular.module("material.core").constant("$MD_THEME_CSS", "md-backdrop.md-opaque.md-THEME_NAME-theme {  background-color: '{{foreground-4-0.5}}'; }md-toolbar .md-button.md-THEME_NAME-theme.md-fab {  background-color: white; }.md-button.md-THEME_NAME-theme {  border-radius: 3px; }  .md-button.md-THEME_NAME-theme:not([disabled]):hover, .md-button.md-THEME_NAME-theme:not([disabled]):focus {    background-color: '{{background-500-0.2}}'; }  .md-button.md-THEME_NAME-theme.md-primary {    color: '{{primary-color}}'; }    .md-button.md-THEME_NAME-theme.md-primary.md-raised, .md-button.md-THEME_NAME-theme.md-primary.md-fab {      color: '{{primary-contrast}}';      background-color: '{{primary-color}}'; }      .md-button.md-THEME_NAME-theme.md-primary.md-raised:not([disabled]):hover, .md-button.md-THEME_NAME-theme.md-primary.md-raised:not([disabled]):focus, .md-button.md-THEME_NAME-theme.md-primary.md-fab:not([disabled]):hover, .md-button.md-THEME_NAME-theme.md-primary.md-fab:not([disabled]):focus {        background-color: '{{primary-600}}'; }  .md-button.md-THEME_NAME-theme.md-fab {    border-radius: 50%;    background-color: '{{accent-color}}';    color: '{{accent-contrast}}'; }    .md-button.md-THEME_NAME-theme.md-fab:not([disabled]):hover, .md-button.md-THEME_NAME-theme.md-fab:not([disabled]):focus {      background-color: '{{accent-A700}}'; }  .md-button.md-THEME_NAME-theme.md-raised {    color: '{{background-contrast}}';    background-color: '{{background-50}}'; }    .md-button.md-THEME_NAME-theme.md-raised:not([disabled]):hover, .md-button.md-THEME_NAME-theme.md-raised:not([disabled]):focus {      background-color: '{{background-200}}'; }  .md-button.md-THEME_NAME-theme.md-warn {    color: '{{warn-color}}'; }    .md-button.md-THEME_NAME-theme.md-warn.md-raised, .md-button.md-THEME_NAME-theme.md-warn.md-fab {      color: '{{warn-contrast}}';      background-color: '{{warn-color}}'; }      .md-button.md-THEME_NAME-theme.md-warn.md-raised:not([disabled]):hover, .md-button.md-THEME_NAME-theme.md-warn.md-raised:not([disabled]):focus, .md-button.md-THEME_NAME-theme.md-warn.md-fab:not([disabled]):hover, .md-button.md-THEME_NAME-theme.md-warn.md-fab:not([disabled]):focus {        background-color: '{{warn-700}}'; }  .md-button.md-THEME_NAME-theme.md-accent {    color: '{{accent-color}}'; }    .md-button.md-THEME_NAME-theme.md-accent.md-raised, .md-button.md-THEME_NAME-theme.md-accent.md-fab {      color: '{{accent-contrast}}';      background-color: '{{accent-color}}'; }      .md-button.md-THEME_NAME-theme.md-accent.md-raised:not([disabled]):hover, .md-button.md-THEME_NAME-theme.md-accent.md-raised:not([disabled]):focus, .md-button.md-THEME_NAME-theme.md-accent.md-fab:not([disabled]):hover, .md-button.md-THEME_NAME-theme.md-accent.md-fab:not([disabled]):focus {        background-color: '{{accent-700}}'; }  .md-button.md-THEME_NAME-theme[disabled], .md-button.md-THEME_NAME-theme.md-raised[disabled], .md-button.md-THEME_NAME-theme.md-fab[disabled] {    color: '{{foreground-3}}';    background-color: transparent;    cursor: not-allowed; }md-card.md-THEME_NAME-theme {  border-radius: 2px; }  md-card.md-THEME_NAME-theme .md-card-image {    border-radius: 2px 2px 0 0; }md-checkbox.md-THEME_NAME-theme .md-ripple {  color: '{{accent-600}}'; }md-checkbox.md-THEME_NAME-theme.md-checked .md-ripple {  color: '{{background-600}}'; }md-checkbox.md-THEME_NAME-theme .md-icon {  border-color: '{{foreground-2}}'; }md-checkbox.md-THEME_NAME-theme.md-checked .md-icon {  background-color: '{{accent-color-0.87}}'; }md-checkbox.md-THEME_NAME-theme.md-checked .md-icon:after {  border-color: '{{background-200}}'; }md-checkbox.md-THEME_NAME-theme:not([disabled]).md-primary .md-ripple {  color: '{{primary-600}}'; }md-checkbox.md-THEME_NAME-theme:not([disabled]).md-primary.md-checked .md-ripple {  color: '{{background-600}}'; }md-checkbox.md-THEME_NAME-theme:not([disabled]).md-primary .md-icon {  border-color: '{{foreground-2}}'; }md-checkbox.md-THEME_NAME-theme:not([disabled]).md-primary.md-checked .md-icon {  background-color: '{{primary-color-0.87}}'; }md-checkbox.md-THEME_NAME-theme:not([disabled]).md-primary.md-checked .md-icon:after {  border-color: '{{background-200}}'; }md-checkbox.md-THEME_NAME-theme:not([disabled]).md-warn .md-ripple {  color: '{{warn-600}}'; }md-checkbox.md-THEME_NAME-theme:not([disabled]).md-warn .md-icon {  border-color: '{{foreground-2}}'; }md-checkbox.md-THEME_NAME-theme:not([disabled]).md-warn.md-checked .md-icon {  background-color: '{{warn-color-0.87}}'; }md-checkbox.md-THEME_NAME-theme:not([disabled]).md-warn.md-checked .md-icon:after {  border-color: '{{background-200}}'; }md-checkbox.md-THEME_NAME-theme[disabled] .md-icon {  border-color: '{{foreground-3}}'; }md-checkbox.md-THEME_NAME-theme[disabled].md-checked .md-icon {  background-color: '{{foreground-3}}'; }md-content.md-THEME_NAME-theme {  background-color: '{{background-hue-3}}'; }md-divider.md-THEME_NAME-theme {  border-top-color: '{{foreground-4}}'; }md-input-container.md-THEME_NAME-theme .md-input, md-input-container.md-THEME_NAME-theme .as-md-input {  color: '{{foreground-1}}';  border-color: '{{foreground-4}}';  text-shadow: '{{foreground-shadow}}'; }  md-input-container.md-THEME_NAME-theme .md-input::-webkit-input-placeholder, md-input-container.md-THEME_NAME-theme .md-input::-moz-placeholder, md-input-container.md-THEME_NAME-theme .md-input:-moz-placeholder, md-input-container.md-THEME_NAME-theme .md-input:-ms-input-placeholder, md-input-container.md-THEME_NAME-theme .as-md-input::-webkit-input-placeholder, md-input-container.md-THEME_NAME-theme .as-md-input::-moz-placeholder, md-input-container.md-THEME_NAME-theme .as-md-input:-moz-placeholder, md-input-container.md-THEME_NAME-theme .as-md-input:-ms-input-placeholder {    color: '{{foreground-3}}'; }md-input-container.md-THEME_NAME-theme label, md-input-container.md-THEME_NAME-theme .md-placeholder {  text-shadow: '{{foreground-shadow}}';  color: '{{foreground-3}}'; }md-input-container.md-THEME_NAME-theme:not(.md-input-invalid).md-input-has-value label {  color: '{{foreground-2}}'; }md-input-container.md-THEME_NAME-theme:not(.md-input-invalid).md-input-focused .md-input {  border-color: '{{primary-500}}'; }md-input-container.md-THEME_NAME-theme:not(.md-input-invalid).md-input-focused label {  color: '{{primary-500}}'; }md-input-container.md-THEME_NAME-theme:not(.md-input-invalid).md-input-focused.md-accent .md-input {  border-color: '{{accent-500}}'; }md-input-container.md-THEME_NAME-theme:not(.md-input-invalid).md-input-focused.md-accent label {  color: '{{accent-500}}'; }md-input-container.md-THEME_NAME-theme:not(.md-input-invalid).md-input-focused.md-warn .md-input {  border-color: '{{warn-500}}'; }md-input-container.md-THEME_NAME-theme:not(.md-input-invalid).md-input-focused.md-warn label {  color: '{{warn-500}}'; }md-input-container.md-THEME_NAME-theme.md-input-invalid .md-input, md-input-container.md-THEME_NAME-theme.md-input-invalid .as-md-input {  border-color: '{{warn-500}}'; }md-input-container.md-THEME_NAME-theme.md-input-invalid label {  color: '{{warn-500}}'; }md-input-container.md-THEME_NAME-theme.md-input-invalid ng-message, md-input-container.md-THEME_NAME-theme.md-input-invalid data-ng-message, md-input-container.md-THEME_NAME-theme.md-input-invalid x-ng-message, md-input-container.md-THEME_NAME-theme.md-input-invalid [ng-message], md-input-container.md-THEME_NAME-theme.md-input-invalid [data-ng-message], md-input-container.md-THEME_NAME-theme.md-input-invalid [x-ng-message], md-input-container.md-THEME_NAME-theme.md-input-invalid .md-char-counter {  color: '{{warn-500}}'; }md-input-container.md-THEME_NAME-theme .md-input[disabled], md-input-container.md-THEME_NAME-theme .as-md-input[disabled] {  border-bottom-color: transparent;  color: '{{foreground-3}}';  background-image: linear-gradient(to right, '{{foreground-4}}' 0%, '{{foreground-4}}' 33%, transparent 0%); }.list-subheader {  color: '{{foreground-2}}'; }.list-divider {  background-color: '{{foreground-4}}'; }.list-content-tile span.second {  color: '{{foreground-2}}'; }.list-row--has-separator:after {  border-color: '{{foreground-4}}'; }md-progress-circular.md-THEME_NAME-theme {  background-color: transparent; }  md-progress-circular.md-THEME_NAME-theme .md-inner .md-gap {    border-top-color: '{{primary-color}}';    border-bottom-color: '{{primary-color}}'; }  md-progress-circular.md-THEME_NAME-theme .md-inner .md-left .md-half-circle, md-progress-circular.md-THEME_NAME-theme .md-inner .md-right .md-half-circle {    border-top-color: '{{primary-color}}'; }  md-progress-circular.md-THEME_NAME-theme .md-inner .md-right .md-half-circle {    border-right-color: '{{primary-color}}'; }  md-progress-circular.md-THEME_NAME-theme .md-inner .md-left .md-half-circle {    border-left-color: '{{primary-color}}'; }  md-progress-circular.md-THEME_NAME-theme.md-warn .md-inner .md-gap {    border-top-color: '{{warn-color}}';    border-bottom-color: '{{warn-color}}'; }  md-progress-circular.md-THEME_NAME-theme.md-warn .md-inner .md-left .md-half-circle, md-progress-circular.md-THEME_NAME-theme.md-warn .md-inner .md-right .md-half-circle {    border-top-color: '{{warn-color}}'; }  md-progress-circular.md-THEME_NAME-theme.md-warn .md-inner .md-right .md-half-circle {    border-right-color: '{{warn-color}}'; }  md-progress-circular.md-THEME_NAME-theme.md-warn .md-inner .md-left .md-half-circle {    border-left-color: '{{warn-color}}'; }  md-progress-circular.md-THEME_NAME-theme.md-accent .md-inner .md-gap {    border-top-color: '{{accent-color}}';    border-bottom-color: '{{accent-color}}'; }  md-progress-circular.md-THEME_NAME-theme.md-accent .md-inner .md-left .md-half-circle, md-progress-circular.md-THEME_NAME-theme.md-accent .md-inner .md-right .md-half-circle {    border-top-color: '{{accent-color}}'; }  md-progress-circular.md-THEME_NAME-theme.md-accent .md-inner .md-right .md-half-circle {    border-right-color: '{{accent-color}}'; }  md-progress-circular.md-THEME_NAME-theme.md-accent .md-inner .md-left .md-half-circle {    border-left-color: '{{accent-color}}'; }md-progress-linear.md-THEME_NAME-theme .md-container {  background-color: '{{primary-100}}'; }md-progress-linear.md-THEME_NAME-theme .md-bar {  background-color: '{{primary-color}}'; }md-progress-linear.md-THEME_NAME-theme.md-warn .md-container {  background-color: '{{warn-100}}'; }md-progress-linear.md-THEME_NAME-theme.md-warn .md-bar {  background-color: '{{warn-color}}'; }md-progress-linear.md-THEME_NAME-theme.md-accent .md-container {  background-color: '{{accent-100}}'; }md-progress-linear.md-THEME_NAME-theme.md-accent .md-bar {  background-color: '{{accent-color}}'; }md-progress-linear.md-THEME_NAME-theme[md-mode=buffer].md-warn .md-bar1 {  background-color: '{{warn-100}}'; }md-progress-linear.md-THEME_NAME-theme[md-mode=buffer].md-warn .md-dashed:before {  background: radial-gradient('{{warn-100}}' 0%, '{{warn-100}}' 16%, transparent 42%); }md-progress-linear.md-THEME_NAME-theme[md-mode=buffer].md-accent .md-bar1 {  background-color: '{{accent-100}}'; }md-progress-linear.md-THEME_NAME-theme[md-mode=buffer].md-accent .md-dashed:before {  background: radial-gradient('{{accent-100}}' 0%, '{{accent-100}}' 16%, transparent 42%); }md-radio-button.md-THEME_NAME-theme .md-off {  border-color: '{{foreground-2}}'; }md-radio-button.md-THEME_NAME-theme .md-on {  background-color: '{{accent-color-0.87}}'; }md-radio-button.md-THEME_NAME-theme.md-checked .md-off {  border-color: '{{accent-color-0.87}}'; }md-radio-button.md-THEME_NAME-theme.md-checked .md-ink-ripple {  color: '{{accent-color-0.87}}'; }md-radio-button.md-THEME_NAME-theme .md-container .md-ripple {  color: '{{accent-600}}'; }md-radio-button.md-THEME_NAME-theme:not([disabled]).md-primary .md-on {  background-color: '{{primary-color-0.87}}'; }md-radio-button.md-THEME_NAME-theme:not([disabled]).md-primary.md-checked .md-off {  border-color: '{{primary-color-0.87}}'; }md-radio-button.md-THEME_NAME-theme:not([disabled]).md-primary.md-checked .md-ink-ripple {  color: '{{primary-color-0.87}}'; }md-radio-button.md-THEME_NAME-theme:not([disabled]).md-primary .md-container .md-ripple {  color: '{{primary-600}}'; }md-radio-button.md-THEME_NAME-theme:not([disabled]).md-warn .md-on {  background-color: '{{warn-color-0.87}}'; }md-radio-button.md-THEME_NAME-theme:not([disabled]).md-warn.md-checked .md-off {  border-color: '{{warn-color-0.87}}'; }md-radio-button.md-THEME_NAME-theme:not([disabled]).md-warn.md-checked .md-ink-ripple {  color: '{{warn-color-0.87}}'; }md-radio-button.md-THEME_NAME-theme:not([disabled]).md-warn .md-container .md-ripple {  color: '{{warn-600}}'; }md-radio-button.md-THEME_NAME-theme[disabled] .md-container .md-off {  border-color: '{{foreground-3}}'; }md-radio-button.md-THEME_NAME-theme[disabled] .md-container .md-on {  border-color: '{{foreground-3}}'; }md-radio-group.md-THEME_NAME-theme:focus:not(:empty) {  border-color: '{{foreground-1}}'; }md-sidenav.md-THEME_NAME-theme {  background-color: '{{background-hue-3}}'; }.md-subheader.md-THEME_NAME-theme {  color: '{{ foreground-2-0.23 }}';  background-color: '{{background-hue-3}}'; }  .md-subheader.md-THEME_NAME-theme.md-primary {    color: '{{primary-color}}'; }  .md-subheader.md-THEME_NAME-theme.md-accent {    color: '{{accent-color}}'; }  .md-subheader.md-THEME_NAME-theme.md-warn {    color: '{{warn-color}}'; }md-switch.md-THEME_NAME-theme .md-thumb {  background-color: '{{background-50}}'; }md-switch.md-THEME_NAME-theme .md-bar {  background-color: '{{background-500}}'; }md-switch.md-THEME_NAME-theme.md-checked .md-thumb {  background-color: '{{accent-color}}'; }md-switch.md-THEME_NAME-theme.md-checked .md-bar {  background-color: '{{accent-color-0.5}}'; }md-switch.md-THEME_NAME-theme.md-checked.md-primary .md-thumb {  background-color: '{{primary-color}}'; }md-switch.md-THEME_NAME-theme.md-checked.md-primary .md-bar {  background-color: '{{primary-color-0.5}}'; }md-switch.md-THEME_NAME-theme.md-checked.md-warn .md-thumb {  background-color: '{{warn-color}}'; }md-switch.md-THEME_NAME-theme.md-checked.md-warn .md-bar {  background-color: '{{warn-color-0.5}}'; }md-switch.md-THEME_NAME-theme[disabled] .md-thumb {  background-color: '{{background-400}}'; }md-switch.md-THEME_NAME-theme[disabled] .md-bar {  background-color: '{{foreground-4}}'; }md-switch.md-THEME_NAME-theme:focus .md-label:not(:empty) {  border-color: '{{foreground-1}}';  border-style: dotted; }md-input-group.md-THEME_NAME-theme input, md-input-group.md-THEME_NAME-theme textarea {  text-shadow: '{{foreground-shadow}}'; }  md-input-group.md-THEME_NAME-theme input::-webkit-input-placeholder, md-input-group.md-THEME_NAME-theme input::-moz-placeholder, md-input-group.md-THEME_NAME-theme input:-moz-placeholder, md-input-group.md-THEME_NAME-theme input:-ms-input-placeholder, md-input-group.md-THEME_NAME-theme textarea::-webkit-input-placeholder, md-input-group.md-THEME_NAME-theme textarea::-moz-placeholder, md-input-group.md-THEME_NAME-theme textarea:-moz-placeholder, md-input-group.md-THEME_NAME-theme textarea:-ms-input-placeholder {    color: '{{foreground-3}}'; }md-input-group.md-THEME_NAME-theme label {  text-shadow: '{{foreground-shadow}}';  color: '{{foreground-3}}'; }md-input-group.md-THEME_NAME-theme input, md-input-group.md-THEME_NAME-theme textarea {  color: '{{foreground-1}}';  border-color: '{{foreground-4}}'; }md-input-group.md-THEME_NAME-theme.md-input-focused input, md-input-group.md-THEME_NAME-theme.md-input-focused textarea {  border-color: '{{primary-500}}'; }md-input-group.md-THEME_NAME-theme.md-input-focused label {  color: '{{primary-500}}'; }md-input-group.md-THEME_NAME-theme.md-input-focused.md-accent input, md-input-group.md-THEME_NAME-theme.md-input-focused.md-accent textarea {  border-color: '{{accent-500}}'; }md-input-group.md-THEME_NAME-theme.md-input-focused.md-accent label {  color: '{{accent-500}}'; }md-input-group.md-THEME_NAME-theme.md-input-has-value:not(.md-input-focused) label {  color: '{{foreground-2}}'; }md-input-group.md-THEME_NAME-theme .md-input[disabled] {  border-bottom-color: '{{foreground-4}}';  color: '{{foreground-3}}'; }md-toolbar.md-THEME_NAME-theme {  background-color: white; }");(function () {
    'use strict';
    angular.module('app')
        .factory('$transition', ['$q', '$timeout', '$rootScope', function ($q, $timeout, $rootScope) {

            var $transition = function (element, trigger, options) {
                options = options || {};
                var deferred = $q.defer();
                var endEventName = $transition[options.animation ? 'animationEndEventName' : 'transitionEndEventName'];

                var transitionEndHandler = function (event) {
                    $rootScope.$apply(function () {
                        element.unbind(endEventName, transitionEndHandler);
                        deferred.resolve(element);
                    });
                };

                if (endEventName) {
                    element.bind(endEventName, transitionEndHandler);
                }

                // Wrap in a timeout to allow the browser time to update the DOM before the transition is to occur
                $timeout(function () {
                    if (angular.isString(trigger)) {
                        element.addClass(trigger);
                    } else if (angular.isFunction(trigger)) {
                        trigger(element);
                    } else if (angular.isObject(trigger)) {
                        element.css(trigger);
                    }
                    //If browser does not support transitions, instantly resolve
                    if (!endEventName) {
                        deferred.resolve(element);
                    }
                });

                // Add our custom cancel function to the promise that is returned
                // We can call this if we are about to run a new transition, which we know will prevent this transition from ending,
                // i.e. it will therefore never raise a transitionEnd event for that transition
                deferred.promise.cancel = function () {
                    if (endEventName) {
                        element.unbind(endEventName, transitionEndHandler);
                    }
                    deferred.reject('Transition cancelled');
                };

                return deferred.promise;
            };

            // Work out the name of the transitionEnd event
            var transElement = document.createElement('trans');
            var transitionEndEventNames = {
                'WebkitTransition': 'webkitTransitionEnd',
                'MozTransition': 'transitionend',
                'OTransition': 'oTransitionEnd',
                'transition': 'transitionend'
            };
            var animationEndEventNames = {
                'WebkitTransition': 'webkitAnimationEnd',
                'MozTransition': 'animationend',
                'OTransition': 'oAnimationEnd',
                'transition': 'animationend'
            };

            function findEndEventName(endEventNames) {
                for (var name in endEventNames) {
                    if (transElement.style[name] !== undefined) {
                        return endEventNames[name];
                    }
                }
            }
            $transition.transitionEndEventName = findEndEventName(transitionEndEventNames);
            $transition.animationEndEventName = findEndEventName(animationEndEventNames);
            return $transition;
        }]).directive('collapse', ['$transition', function ($transition) {

            return {
                link: function (scope, element, attrs) {

                    var initialAnimSkip = true;
                    var currentTransition;

                    function doTransition(change) {
                        var newTransition = $transition(element, change);
                        if (currentTransition) {
                            currentTransition.cancel();
                        }
                        currentTransition = newTransition;
                        newTransition.then(newTransitionDone, newTransitionDone);
                        return newTransition;

                        function newTransitionDone() {
                            // Make sure it's this transition, otherwise, leave it alone.
                            if (currentTransition === newTransition) {
                                currentTransition = undefined;
                            }
                        }
                    }

                    function expand() {
                        if (initialAnimSkip) {
                            initialAnimSkip = false;
                            expandDone();
                        } else {
                            element.removeClass('collapse').addClass('collapsing');
                            doTransition({
                                height: element[0].scrollHeight + 'px'
                            }).then(expandDone);
                        }
                    }

                    function expandDone() {
                        element.removeClass('collapsing');
                        element.addClass('collapse in');
                        element.css({
                            height: 'auto'
                        });
                    }

                    function collapse() {
                        if (initialAnimSkip) {
                            initialAnimSkip = false;
                            collapseDone();
                            element.css({
                                height: 0
                            });
                        } else {
                            // CSS transitions don't work with height: auto, so we have to manually change the height to a specific value
                            element.css({
                                height: element[0].scrollHeight + 'px'
                            });
                            //trigger reflow so a browser realizes that height was updated from auto to a specific value
                            var x = element[0].offsetWidth;

                            element.removeClass('collapse in').addClass('collapsing');

                            doTransition({
                                height: 0
                            }).then(collapseDone);
                        }
                    }

                    function collapseDone() {
                        element.removeClass('collapsing');
                        element.addClass('collapse');
                    }

                    scope.$watch(attrs.collapse, function (shouldCollapse) {
                        if (shouldCollapse) {
                            collapse();
                        } else {
                            expand();
                        }
                    });
                }
            };
        }]).constant('accordionConfig', {
            closeOthers: true
        })

    .controller('AccordionController', ['$scope', '$attrs', 'accordionConfig', function ($scope, $attrs, accordionConfig) {

        // This array keeps track of the accordion groups
        this.groups = [];

        // Ensure that all the groups in this accordion are closed, unless close-others explicitly says not to
        this.closeOthers = function (openGroup) {
            var closeOthers = angular.isDefined($attrs.closeOthers) ? $scope.$eval($attrs.closeOthers) : accordionConfig.closeOthers;
            if (closeOthers) {
                angular.forEach(this.groups, function (group) {
                    if (group !== openGroup) {
                        group.isOpen = false;
                    }
                });
            }
        };

        // This is called from the accordion-group directive to add itself to the accordion
        this.addGroup = function (groupScope) {
            var that = this;
            this.groups.push(groupScope);

            groupScope.$on('$destroy', function (event) {
                that.removeGroup(groupScope);
            });
        };

        // This is called from the accordion-group directive when to remove itself
        this.removeGroup = function (group) {
            var index = this.groups.indexOf(group);
            if (index !== -1) {
                this.groups.splice(index, 1);
            }
        };

    }])

    // The accordion directive simply sets up the directive controller
    // and adds an accordion CSS class to itself element.
    .directive('accordion', function () {
        return {
            restrict: 'EA',
            controller: 'AccordionController',
            transclude: true,
            replace: false,
            templateUrl: 'core/accordion/accordion.html'
        };
    })

    // The accordion-group directive indicates a block of html that will expand and collapse in an accordion
    .directive('accordionGroup', function () {
        return {
            require: '^accordion', // We need this directive to be inside an accordion
            restrict: 'EA',
            transclude: true, // It transcludes the contents of the directive into the template
            replace: true, // The element containing the directive will be replaced with the template
            templateUrl: 'core/accordion/accordion_group.html',
            scope: {
                heading: '@', // Interpolate the heading attribute onto this scope
                isOpen: '=?',
                isDisabled: '=?'
            },
            controller: function () {
                this.setHeading = function (element) {
                    this.heading = element;
                };
            },
            link: function (scope, element, attrs, accordionCtrl) {
                accordionCtrl.addGroup(scope);

                scope.$watch('isOpen', function (value) {
                    if (value) {
                        accordionCtrl.closeOthers(scope);
                    }
                });

                scope.toggleOpen = function () {
                    if (!scope.isDisabled) {
                        scope.isOpen = !scope.isOpen;
                    }
                };
            }
        };
    })

    // Use accordion-heading below an accordion-group to provide a heading containing HTML
    // <accordion-group>
    //   <accordion-heading>Heading containing HTML - <img src="..."></accordion-heading>
    // </accordion-group>
    .directive('accordionHeading', function () {
        return {
            restrict: 'EA',
            transclude: true, // Grab the contents to be used as the heading
            template: '', // In effect remove this element!
            replace: true,
            require: '^accordionGroup',
            link: function (scope, element, attr, accordionGroupCtrl, transclude) {
                // Pass the heading to the accordion-group controller
                // so that it can be transcluded into the right place in the template
                // [The second parameter to transclude causes the elements to be cloned so that they work in ng-repeat]
                accordionGroupCtrl.setHeading(transclude(scope, function () {}));
            }
        };
    })

    // Use in the accordion-group template to indicate where you want the heading to be transcluded
    // You must provide the property on the accordion-group controller that will hold the transcluded element
    // <div class="accordion-group">
    //   <div class="accordion-heading" ><a ... accordion-transclude="heading">...</a></div>
    //   ...
    // </div>
    .directive('accordionTransclude', function () {
        return {
            require: '^accordionGroup',
            link: function (scope, element, attr, controller) {
                scope.$watch(function () {
                    return controller[attr.accordionTransclude];
                }, function (heading) {
                    if (heading) {
                        element.html('');
                        element.append(heading);
                    }
                });
            }
        };
    }).directive('bindHtmlUnsafe', function () {
        return function (scope, element, attr) {
            element.addClass('ng-binding').data('$binding', attr.bindHtmlUnsafe);
            scope.$watch(attr.bindHtmlUnsafe, function bindHtmlUnsafeWatchAction(value) {
                element.html(value || '');
            });
        };
    }).directive('accordionOnOpen', function ($timeout, helpers) {
        return {

            link: function (scope, element, attrs) {

                var accordions = scope.$eval(attrs.accordionOnOpen);

                if (accordions) {

                    angular.forEach(accordions.groups, function (accordion, i) {
                        scope.$watch(attrs.accordionOnOpen + '.groups[' + i + '].open', function (neww, old) {
                            var which = accordions.groups[i];
                            if (neww) {
                                scope.$broadcast('accordionOpened', which, i);
                            } else {
                                scope.$broadcast('accordionClosed', which, i);
                            }
                        });

                    });

                }

            }
        };
    }).directive('monitorAccordionFormState', function () {
            return {
                priority: -10000,
                restrict: 'A',
                require: ['^form'],
                link: function (scope, element, attrs, ctrls) {
                    var form = ctrls[0],
                        accordion = scope.$eval(attrs.monitorAccordionFormState),
                        check = function () {
                            element.find('[name]').each(function () {
                                var name = $(this).attr('name'),
                                    formElement = form[name];
                                if (angular.isDefined(formElement)) {
                                    if (!formElement.$valid) {
                                        accordion.open = true;
                                        form.$setDirty();
                                        formElement.$setViewValue(formElement.$viewValue !== undefined ? formElement.$viewValue : '');
                                        formElement.$setDirty();
                                        if (!scope.$$phase) {
                                            scope.$apply();
                                        }
                                    }
                                }
                            });
                        };
                    scope.$on('invalidForm', check);
                }
            };
        });

}());
(function () {
    'use strict';
    angular.module('app').directive('actionDropdownList', function () {
        return {
            templateUrl: 'core/action/dropdown_list.html',
            transclude: true,
            replace: true
        };
    }).directive('actionDropdown', function ($simpleDialog, $mdTheming,
        $mdInkRipple, $$rAF, $mdConstant, underscoreTemplate, $timeout, $parse, helpers) {
        return {
            replace: true,
            transclude: true,
            templateUrl: 'core/action/dropdown.html',
            scope: true,
            link: function (scope, element, attrs) {
                var dropdown = {},
                    template = scope.$eval(attrs.template);
                if (!template) {
                    return;
                }
                dropdown.open = function ($event) {
                    $simpleDialog.show({
                        templateUrl: template,
                        targetEvent: $event,
                        parent: element.parents(attrs.parent),
                        onBeforeHide: function (dialogEl, options) {
                            $(window).off('resize', options.resize);
                        },
                        onBeforeShow: function (dialogEl, options) {
                            var animateSelect = function () {
                                var target = element;
                                options.resize = function () {
                                    var targetOffset = target.offset(),
                                        parent = options.parent,
                                        paddingTop = parseInt(parent.css('padding-top'), 10) || 16,
                                        paddingBottom = parseInt(parent.css('padding-bottom'), 10) || 16,
                                        newTop = targetOffset.top,
                                        newLeft = (targetOffset.left - (dialogEl.width() - target.outerWidth())) - 12,
                                        height = parent.height() - (paddingBottom + paddingTop);
                                    newTop = targetOffset.top;
                                    if (newTop < 16) {
                                        newTop = 16;
                                    }
                                    if (newLeft < 16) {
                                        newLeft = 16;
                                    }
                                    dialogEl.css({
                                        top: newTop,
                                        left: newLeft
                                    });
                                    if (dialogEl.height() > height) {
                                        dialogEl.height(height);
                                    }
                                };
                                options.resize();
                                $(window).on('resize', options.resize);

                                dialogEl.css($mdConstant.CSS.TRANSFORM, 'scale(' +
                                        Math.min(target.width() / dialogEl.width(), 1.0) + ',' +
                                        Math.min(target.height() / dialogEl.height(), 1.0) + ')')
                                    .on($mdConstant.CSS.TRANSITIONEND, function (ev) {
                                        if (ev.target === dialogEl[0]) {
                                            dropdown.opened = true;
                                        }
                                    });
                                $$rAF(function () {
                                    dialogEl.addClass('transition-in');
                                    dialogEl.css($mdConstant.CSS.TRANSFORM, '');
                                });

                            };

                            $$rAF(animateSelect);

                            dialogEl.on('click', dropdown.close);
                        },
                        controller: function ($scope) {
                            $scope.parent = scope;
                        }
                    });
                };
                dropdown.close = function () {
                    $simpleDialog.hide().then(function () {
                        dropdown.opened = false;
                    });
                };
                scope.dropdown = dropdown;
            }
        };
    }).directive('actionToolbar', function ($mdInkRipple) {
        return {
            transclude: true,
            replace: true,
            scope: true,
            templateUrl: 'core/action/toolbar.html',
            link: function (scope, element, attrs) {
                scope.spec = scope.$eval(attrs.spec);
            }
        };
    });
}());
/**
 * @author Jason Dobry <jason.dobry@gmail.com>
 * @file angular-cache.js
 * @version 3.1.1 - Homepage <https://github.com/jmdobry/angular-cache>
 * @copyright (c) 2013-2014 Jason Dobry <http://www.pseudobry.com>
 * @license MIT <https://github.com/jmdobry/angular-cache/blob/master/LICENSE>
 *
 * @overview angular-cache is a very useful replacement for Angular's $cacheFactory.
 */
(function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);throw new Error("Cannot find module '"+o+"'")}var f=n[o]={exports:{}};t[o][0].call(f.exports,function(e){var n=t[o][1][e];return s(n?n:e)},f,f.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({1:[function(require,module,exports){
/**
 * @method bubbleUp
 * @param {array} heap The heap.
 * @param {function} weightFunc The weight function.
 * @param {number} n The index of the element to bubble up.
 */
function bubbleUp(heap, weightFunc, n) {
  var element = heap[n],
    weight = weightFunc(element);
  // When at 0, an element can not go up any further.
  while (n > 0) {
    // Compute the parent element's index, and fetch it.
    var parentN = Math.floor((n + 1) / 2) - 1,
      parent = heap[parentN];
    // If the parent has a lesser weight, things are in order and we
    // are done.
    if (weight >= weightFunc(parent)) {
      break;
    } else {
      heap[parentN] = element;
      heap[n] = parent;
      n = parentN;
    }
  }
}

/**
 * @method bubbleDown
 * @param {array} heap The heap.
 * @param {function} weightFunc The weight function.
 * @param {number} n The index of the element to sink down.
 */
function bubbleDown(heap, weightFunc, n) {
  var length = heap.length,
    node = heap[n],
    nodeWeight = weightFunc(node);

  while (true) {
    var child2N = (n + 1) * 2,
      child1N = child2N - 1;
    var swap = null;
    if (child1N < length) {
      var child1 = heap[child1N],
        child1Weight = weightFunc(child1);
      // If the score is less than our node's, we need to swap.
      if (child1Weight < nodeWeight) {
        swap = child1N;
      }
    }
    // Do the same checks for the other child.
    if (child2N < length) {
      var child2 = heap[child2N],
        child2Weight = weightFunc(child2);
      if (child2Weight < (swap === null ? nodeWeight : weightFunc(heap[child1N]))) {
        swap = child2N;
      }
    }

    if (swap === null) {
      break;
    } else {
      heap[n] = heap[swap];
      heap[swap] = node;
      n = swap;
    }
  }
}

/**
 * @class DSBinaryHeap
 * @desc DSBinaryHeap implementation of a priority queue.
 * @param {function} weightFunc Function that returns the value that should be used for node value comparison.
 * @example
 * angular.module('app').controller(function (DSBinaryHeap) {
             *      var bHeap = new DSBinaryHeap(function (x) {
             *          return x.value;
             *      });
             * );
             */
function DSBinaryHeap(weightFunc) {
  if (weightFunc && !angular.isFunction(weightFunc)) {
    throw new Error('DSBinaryHeap(weightFunc): weightFunc: must be a function!');
  }
  weightFunc = weightFunc || function (x) {
    return x;
  };
  this.weightFunc = weightFunc;
  this.heap = [];
}

/**
 * @method DSBinaryHeap.push
 * @desc Push an element into the binary heap.
 * @param {*} node The element to push into the binary heap.
 */
DSBinaryHeap.prototype.push = function (node) {
  this.heap.push(node);
  bubbleUp(this.heap, this.weightFunc, this.heap.length - 1);
};

/**
 * @method DSBinaryHeap.peek
 * @desc Return, but do not remove, the minimum element in the binary heap.
 * @returns {*}
 */
DSBinaryHeap.prototype.peek = function () {
  return this.heap[0];
};

/**
 * @method DSBinaryHeap.pop
 * @desc Remove and return the minimum element in the binary heap.
 * @returns {*}
 */
DSBinaryHeap.prototype.pop = function () {
  var front = this.heap[0],
    end = this.heap.pop();
  if (this.heap.length > 0) {
    this.heap[0] = end;
    bubbleDown(this.heap, this.weightFunc, 0);
  }
  return front;
};

/**
 * @method DSBinaryHeap.remove
 * @desc Remove the first node in the priority queue that satisfies angular.equals comparison with
 * the given node.
 * @param {*} node The node to remove.
 * @returns {*} The removed node.
 */
DSBinaryHeap.prototype.remove = function (node) {
  var length = this.heap.length;
  for (var i = 0; i < length; i++) {
    if (angular.equals(this.heap[i], node)) {
      var removed = this.heap[i],
        end = this.heap.pop();
      if (i !== length - 1) {
        this.heap[i] = end;
        bubbleUp(this.heap, this.weightFunc, i);
        bubbleDown(this.heap, this.weightFunc, i);
      }
      return removed;
    }
  }
  return null;
};

/**
 * @method DSBinaryHeap.removeAll
 * @desc Remove all nodes from this DSBinaryHeap.
 */
DSBinaryHeap.prototype.removeAll = function () {
  this.heap = [];
};

/**
 * @method DSBinaryHeap.size
 * @desc Return the size of the priority queue.
 * @returns {number} The size of the priority queue.
 */
DSBinaryHeap.prototype.size = function () {
  return this.heap.length;
};

/**
 * @desc Provider for the DSBinaryHeap.
 */
function DSBinaryHeapProvider() {
  this.$get = function () {
    return DSBinaryHeap;
  };
}

module.exports = {
  DSBinaryHeapProvider: DSBinaryHeapProvider,
  DSBinaryHeap: DSBinaryHeap
};

},{}],2:[function(require,module,exports){
/**
 * @doc method
 * @id DSCache.methods:destroy
 * @name destroy
 * @description
 * Destroy this cache and all of its data.
 *
 * ## Signature:
 * ```js
 * DSCache#destroy()
 * ```
 *
 * ## Example:
 * ```js
 * var someCache = DSCacheFactory.get('someCache');
 *
 * someCache.destroy();
 *
 * DSCacheFactory.get('someCache'); // undefined
 * someCache.put('1', 'apple'); // Error
 * ```
 */
module.exports = function destroy() {
  clearInterval(this.$$cacheFlushIntervalId);
  clearInterval(this.$$recycleFreqId);
  this.removeAll();
  if (this.$$storage) {
    this.$$storage.removeItem(this.$$prefix + '.keys');
    this.$$storage.removeItem(this.$$prefix);
  }
  this.$$storage = null;
  this.$$data = null;
  this.$$lruHeap = null;
  this.$$expiresHeap = null;
  this.$$prefix = null;
};

},{}],3:[function(require,module,exports){
var utils = require('../utils');

/**
 * @doc method
 * @id DSCache.methods:get
 * @name get
 * @description
 * Retrieve the item with the given key.
 *
 * ## Signature:
 * ```js
 * DSCache#get(key)
 * ```
 *
 * ## Examples:
 * ```js
 * var cache = DSCacheFactory('cache');
 *
 * cache.put('1', 'apple');
 *
 * cache.get('1'); // "apple"
 * cache.get('2'); // undefined
 * ```
 *
 * ```js
 *  var options = {
 *          deleteOnExpire: 'passive',
 *          maxAge: 1000
 *      },
 *      cache = DSCacheFactory('cache', options);
 *
 *  cache.put('1', 'apple');
 *
 *  cache.get('1'); // "apple"
 *
 *  setTimeout(function () {
 *      cache.get('1'); // undefined
 *  }, 1500);
 * ```
 *
 * ```js
 *  var options = {
 *          deleteOnExpire: 'passive',
 *          maxAge: 1000
 *      },
 *      cache = DSCacheFactory('cache', options);
 *
 *  cache.put('1', 'apple');
 *
 *  cache.get('1', {
 *      onExpire: function (key, value) {
 *          console.log(key, value);
 *      }
 *  }); // "apple"
 *
 *  setTimeout(function () {
 *      cache.get('1'); // undefined
 *                      // "1" "apple" (printed to console)
 *  }, 1500);
 * ```
 *
 * ```js
 *  var options = {
 *          deleteOnExpire: 'passive',
 *          maxAge: 1000,
 *          onExpire: function (key, value, done) {
 *              console.log('global hit');
 *              if (done) {
 *                  done(key, value);
 *              }
 *          }
 *      },
 *      cache = DSCacheFactory('cache', options);
 *
 *  cache.put('1', 'apple');
 *
 *  cache.get('1', {
 *      onExpire: function (key, value) {
 *          console.log(key, value);
 *      }
 *  }); // "apple"
 *
 *  setTimeout(function () {
 *      cache.get('1'); // undefined
 *                      // "global hit" (printed to console)
 *                      // "1" "apple" (printed to console)
 *  }, 1500);
 * ```
 *
 * @param {string} key The key of the item to retrieve.
 * @param {object=} options Optional configuration. Properties:
 *
 * - `{function=}` - `onExpire` - Callback to be used if in passive `deleteOnExpire` mode and the requested item has
 * expired. If a global `onExpire` callback exists for this cache, then it will be called with three arguments: `key`,
 * `value`, and `done`, where `done` is the `onExpire` callback passed into the call to `DSCache#get(key[, options])`.
 * (See the last example above.)
 *
 * @returns {*} The item with the given key.
 */
module.exports = function get(key, options) {
  var _this = this;

  if (angular.isArray(key)) {
    var keys = key,
      values = [];

    angular.forEach(keys, function (key) {
      var value = _this.get(key, options);
      if (value !== null && value !== undefined) {
        values.push(value);
      }
    });

    return values;
  } else {
    key = utils.stringifyNumber(key);

    if (this.$$disabled) {
      return;
    }
  }

  options = options || {};
  if (!angular.isString(key)) {
    throw angular.$$minErr('ng')('areq', 'Expected key to be a string! Found: {0}.', typeof key);
  } else if (options && !angular.isObject(options)) {
    throw angular.$$minErr('ng')('areq', 'Expected options to be an object! Found: {0}.', typeof options);
  } else if (options.onExpire && !angular.isFunction(options.onExpire)) {
    throw angular.$$minErr('ng')('areq', 'Expected options.onExpire to be a function! Found: {0}.', typeof options.onExpire);
  }

  var item;

  if (this.$$storage) {
    var itemJson = this.$$storage.getItem(this.$$prefix + '.data.' + key);

    if (itemJson) {
      item = angular.fromJson(itemJson);
    } else {
      return;
    }
  } else {
    if (!(key in this.$$data)) {
      return;
    }

    item = this.$$data[key];
  }

  var value = item.value,
    now = new Date().getTime();

  if (this.$$storage) {
    this.$$lruHeap.remove({
      key: key,
      accessed: item.accessed
    });
    item.accessed = now;
    this.$$lruHeap.push({
      key: key,
      accessed: now
    });
  } else {
    this.$$lruHeap.remove(item);
    item.accessed = now;
    this.$$lruHeap.push(item);
  }

  if (this.$$deleteOnExpire === 'passive' && 'expires' in item && item.expires < now) {
    this.remove(key);

    if (this.$$onExpire) {
      this.$$onExpire(key, item.value, options.onExpire);
    } else if (options.onExpire) {
      options.onExpire(key, item.value);
    }
    value = undefined;
  } else if (this.$$storage) {
    this.$$storage.setItem(this.$$prefix + '.data.' + key, (item));
  }

  return value;
};

},{"../utils":21}],4:[function(require,module,exports){
var defaults = require('../defaults'),
  DSBinaryHeap = require('../DSBinaryHeap').DSBinaryHeap;

/*!
 * Configure the cache to use webStorage.
 */
function _setStorageMode(storageMode, storageImpl) {
  if (!angular.isString(storageMode)) {
    throw angular.$$minErr('ng')('areq', 'Expected storageMode to be a string! Found: {0}.', typeof storageMode);
  } else if (storageMode !== 'memory' && storageMode !== 'localStorage' && storageMode !== 'sessionStorage') {
    throw angular.$$minErr('ng')('areq', 'Expected storageMode to be "memory", "localStorage" or "sessionStorage"! Found: {0}.', storageMode);
  }

  this.$$storageMode = storageMode;

  if (storageImpl) {
    if (!angular.isObject(storageImpl)) {
      throw angular.$$minErr('ng')('areq', 'Expected storageImpl to be an object! Found: {0}.', typeof storageImpl);
    } else if (!('setItem' in storageImpl) || typeof storageImpl.setItem !== 'function') {
      throw angular.$$minErr('ng')('areq', 'Expected storageImpl to implement "setItem(key, value)"! Found: {0}.', typeof storageImpl.setItem);
    } else if (!('getItem' in storageImpl) || typeof storageImpl.getItem !== 'function') {
      throw angular.$$minErr('ng')('areq', 'Expected storageImpl to implement "getItem(key)"! Found: {0}.', typeof storageImpl.getItem);
    } else if (!('removeItem' in storageImpl) || typeof storageImpl.removeItem !== 'function') {
      throw angular.$$minErr('ng')('areq', 'Expected storageImpl to implement "removeItem(key)"! Found: {0}.', typeof storageImpl.removeItem);
    }
    this.$$storage = storageImpl;
  } else if (this.$$storageMode === 'localStorage') {
    try {
      localStorage.setItem('angular-cache', 'angular-cache');
      localStorage.removeItem('angular-cache');
      this.$$storage = localStorage;
    } catch (e) {
      delete this.$$storage;
      this.$$storageMode = 'memory';
    }
  } else if (this.$$storageMode === 'sessionStorage') {
    try {
      sessionStorage.setItem('angular-cache', 'angular-cache');
      sessionStorage.removeItem('angular-cache');
      this.$$storage = sessionStorage;
    } catch (e) {
      delete this.$$storage;
      this.$$storageMode = 'memory';
    }
  }
}

/**
 * @doc method
 * @id DSCache.methods:setOptions
 * @name setOptions
 * @description
 * Configure this cache with the given options. With this method you can configure all of this cache's settings at once.
 *
 * ## Signature:
 * ```js
 * DSCache#setOptions(cacheOptions[, strict])
 * ```
 *
 * ## Example:
 * ```js
 *  cache.setOptions({
 *      maxAge: 60000,
 *      deleteOnExpire: 'aggressive',
 *      disabled: false
 *  });
 * ```
 *
 * @param {object} cacheOptions New configuration options for the cache. Properties:
 *
 * - `{number=}` - `capacity` - Default: `Number.MAX_VALUE`
 * - `{number=}` - `maxAge` - Default: `null`
 * - `{number=}` - `deleteOnExpire` - Default: `none`
 * - `{function=}` - `onExpire` - Default: `null`
 * - `{number=}` - `cacheFlushInterval` - Default: `null`
 * - `{number=}` - `recycleFreq` - Default: `1000`
 * - `{boolean=}` - `disabled` - Default: `false`
 *
 * @param {boolean=} strict If true then any existing configuration will be reset to the defaults before
 * applying the new options, otherwise only the options specified in the options hash will be altered.
 */
function _setOptions(cacheOptions, strict) {
  cacheOptions = cacheOptions || {};
  strict = !!strict;
  if (!angular.isObject(cacheOptions)) {
    throw angular.$$minErr('ng')('areq', 'Expected cacheOptions to be an object! Found: {0}.', typeof cacheOptions);
  }

  if ('disabled' in cacheOptions) {
    this.$$disabled = !!cacheOptions.disabled;
  } else if (strict) {
    delete this.$$disabled;
  }

  if ('capacity' in cacheOptions) {
    this.setCapacity(cacheOptions.capacity);
  } else if (strict) {
    this.setCapacity(null);
  }

  if ('deleteOnExpire' in cacheOptions) {
    this.setDeleteOnExpire(cacheOptions.deleteOnExpire);
  } else if (strict) {
    this.setDeleteOnExpire(null);
  }

  if ('maxAge' in cacheOptions) {
    this.setMaxAge(cacheOptions.maxAge);
  } else if (strict) {
    this.setMaxAge(null);
  }

  if ('recycleFreq' in cacheOptions) {
    this.setRecycleFreq(cacheOptions.recycleFreq);
  } else if (strict) {
    this.setRecycleFreq(null);
  }

  if ('cacheFlushInterval' in cacheOptions) {
    this.setCacheFlushInterval(cacheOptions.cacheFlushInterval);
  } else if (strict) {
    this.setCacheFlushInterval(null);
  }

  if ('onExpire' in cacheOptions) {
    this.setOnExpire(cacheOptions.onExpire);
  } else if (strict) {
    this.setOnExpire(null);
  }
}

/**
 * @doc function
 * @id DSCache
 * @name DSCache
 * @description
 * Instantiated via `DSCacheFactory(cacheId[, options])`.
 *
 * @param {string} cacheId The id of the new cache.
 * @param {object=} options Configuration options.
 */
function DSCache(cacheId, options) {

  this.$$data = {};
  this.$$id = cacheId;
  this.$$storage = null;

  this.$$expiresHeap = new DSBinaryHeap(function (x) {
    return x.expires;
  });

  this.$$lruHeap = new DSBinaryHeap(function (x) {
    return x.accessed;
  });

  options = options || {};

  if ('storageMode' in options) {
    _setStorageMode.apply(this, [options.storageMode, options.storageImpl]);
  }
  if ('storagePrefix' in options) {
    this.$$storagePrefix = options.storagePrefix;
  }

  this.$$prefix = this.$$storagePrefix + cacheId;

  // Initialize this cache with the default and given options
  _setOptions.apply(this, [options, true]);
}

for (var key in defaults.defaults) {
  DSCache.prototype['$$' + key] = defaults.defaults[key];
}

/**
 * @doc method
 * @id DSCache.methods:setOptions
 * @name setOptions
 * @methodOf DSCache
 * @description
 * See [DSCache.setOptions](/documentation/api/angular-cache/DSCache.methods:create).
 */
DSCache.prototype.setOptions = _setOptions;

/**
 * @doc method
 * @id DSCache.methods:setCapacity
 * @name setCapacity
 * @methodOf DSCache
 * @description
 * See [DSCache.setCapacity](/documentation/api/angular-cache/DSCache.methods:create).
 */
DSCache.prototype.setCapacity = require('./setCapacity');

/**
 * @doc method
 * @id DSCache.methods:setDeleteOnExpire
 * @name setDeleteOnExpire
 * @methodOf DSCache
 * @description
 * See [DSCache.setDeleteOnExpire](/documentation/api/angular-cache/DSCache.methods:create).
 */
DSCache.prototype.setDeleteOnExpire = require('./setDeleteOnExpire');

/**
 * @doc method
 * @id DSCache.methods:setMaxAge
 * @name setMaxAge
 * @methodOf DSCache
 * @description
 * See [DSCache.setMaxAge](/documentation/api/angular-cache/DSCache.methods:create).
 */
DSCache.prototype.setMaxAge = require('./setMaxAge');

/**
 * @doc method
 * @id DSCache.methods:setRecycleFreq
 * @name setRecycleFreq
 * @methodOf DSCache
 * @description
 * See [DSCache.setRecycleFreq](/documentation/api/angular-cache/DSCache.methods:create).
 */
DSCache.prototype.setRecycleFreq = require('./setRecycleFreq');

/**
 * @doc method
 * @id DSCache.methods:setCacheFlushInterval
 * @name setCacheFlushInterval
 * @methodOf DSCache
 * @description
 * See [DSCache.setCacheFlushInterval](/documentation/api/angular-cache/DSCache.methods:create).
 */
DSCache.prototype.setCacheFlushInterval = require('./setCacheFlushInterval');

/**
 * @doc method
 * @id DSCache.methods:setOnExpire
 * @name setOnExpire
 * @methodOf DSCache
 * @description
 * See [DSCache.setOnExpire](/documentation/api/angular-cache/DSCache.methods:create).
 */
DSCache.prototype.setOnExpire = require('./setOnExpire');

/**
 * @doc method
 * @id DSCache.methods:put
 * @name put
 * @methodOf DSCache
 * @description
 * See [DSCache.put](/documentation/api/angular-cache/DSCache.methods:create).
 */
DSCache.prototype.put = require('./put');

/**
 * @doc method
 * @id DSCache.methods:get
 * @name get
 * @methodOf DSCache
 * @description
 * See [DSCache.get](/documentation/api/angular-cache/DSCache.methods:create).
 */
DSCache.prototype.get = require('./get');

/**
 * @doc method
 * @id DSCache.methods:remove
 * @name remove
 * @methodOf DSCache
 * @description
 * See [DSCache.remove](/documentation/api/angular-cache/DSCache.methods:create).
 */
DSCache.prototype.remove = require('./remove');

/**
 * @doc method
 * @id DSCache.methods:removeAll
 * @name removeAll
 * @methodOf DSCache
 * @description
 * See [DSCache.removeAll](/documentation/api/angular-cache/DSCache.methods:create).
 */
DSCache.prototype.removeAll = require('./removeAll');

/**
 * @doc method
 * @id DSCache.methods:removeExpired
 * @name removeExpired
 * @methodOf DSCache
 * @description
 * See [DSCache.removeExpired](/documentation/api/angular-cache/DSCache.methods:create).
 */
DSCache.prototype.removeExpired = require('./removeExpired');

/**
 * @doc method
 * @id DSCache.methods:destroy
 * @name destroy
 * @methodOf DSCache
 * @description
 * See [DSCache.destroy](/documentation/api/angular-cache/DSCache.methods:create).
 */
DSCache.prototype.destroy = require('./destroy');

/**
 * @doc method
 * @id DSCache.methods:info
 * @name info
 * @methodOf DSCache
 * @description
 * See [DSCache.info](/documentation/api/angular-cache/DSCache.methods:create).
 */
DSCache.prototype.info = require('./info');

/**
 * @doc method
 * @id DSCache.methods:keySet
 * @name keySet
 * @methodOf DSCache
 * @description
 * See [DSCache.keySet](/documentation/api/angular-cache/DSCache.methods:create).
 */
DSCache.prototype.keySet = require('./keySet');

/**
 * @doc method
 * @id DSCache.methods:keys
 * @name keys
 * @methodOf DSCache
 * @description
 * See [DSCache.keys](/documentation/api/angular-cache/DSCache.methods:create).
 */
DSCache.prototype.keys = require('./keys');

/**
 * @doc method
 * @id DSCache.methods:disable
 * @name disable
 * @description
 * Disable this cache. Disabling a cache does not remove any data, it just turns DSCache#get and DSCache#put into noops.
 *
 * ## Signature:
 * ```js
 * DSCache#disable()
 * ```
 *
 * ## Example:
 * ```js
 *  var cache = DSCacheFactory.get('cache');
 *
 *  cache.put('1', 'apple');
 *  cache.get('1'); // "apple"
 *  cache.info().size; // 1
 *
 *  cache.disable();
 *  cache.info().size; // 1
 *
 *  cache.get('1'); // undefined
 *  cache.put('2', 'banana'); // undefined
 *  cache.get('2'); // undefined
 *  cache.info().size; // 1
 * ```
 */
DSCache.prototype.disable = function () {
  this.$$disabled = true;
};

/**
 * @doc method
 * @id DSCache.methods:enable
 * @name enable
 * @description
 * Enable this cache.
 *
 * ## Signature:
 * ```js
 * DSCache#enable()
 * ```
 *
 * ## Example:
 * ```js
 *  var options = {
 *      disabled: true
 *  };
 *  var cache = DSCacheFactory.get('cache', options);
 *
 *  cache.put('1', 'apple');
 *  cache.get('1'); // undefined
 *
 *  cache.enable();
 *
 *  cache.put('1', 'apple');
 *  cache.get('1'); // "apple"
 * ```
 */
DSCache.prototype.enable = function () {
  delete this.$$disabled;
};

/**
 * @doc method
 * @id DSCache.methods:touch
 * @name touch
 * @description
 * Reset the expiry of a single item or all items in the cache.
 *
 * ## Signature:
 * ```js
 * DSCache#touch(key)
 * ```
 *
 * ## Example:
 * ```js
 *  cache.touch('1'); // touch one item
 *
 *  cache.touch(); // touch all items
 * ```
 *
 * @param {string=} key The key of the item to touch.
 */
DSCache.prototype.touch = function (key) {
  if (key) {
    var _this = this;
    var val = this.get(key, {
      onExpire: function (k, v) {
        _this.put(k, v);
      }
    });
    if (val) {
      this.put(key, val);
    }
  } else {
    var keys = this.keys();
    for (var i = 0; i < keys.length; i++) {
      this.touch(keys[i]);
    }
  }
};

module.exports = DSCache;

},{"../DSBinaryHeap":1,"../defaults":19,"./destroy":2,"./get":3,"./info":5,"./keySet":6,"./keys":7,"./put":8,"./remove":9,"./removeAll":10,"./removeExpired":11,"./setCacheFlushInterval":12,"./setCapacity":13,"./setDeleteOnExpire":14,"./setMaxAge":15,"./setOnExpire":16,"./setRecycleFreq":17}],5:[function(require,module,exports){
/**
 * @doc method
 * @id DSCache.methods:info
 * @name info
 * @description
 * Return the status of this cache, or if `key` is provided return the status of the item with that key.
 *
 * ## Signature:
 * ```js
 * DSCache#info([key])
 * ```
 *
 * ## Example:
 * ```js
 * var cache = DSCacheFactory('cache');
 *
 * cache.put('1', 'apple');
 * cache.put('2', 'banana');
 *
 * cache.info();    //  {
 *                  //      id: 'cache',
 *                  //      capacity: Number.MAX_VALUE,
 *                  //      maxAge: Number.MAX_VALUE,
 *                  //      deleteOnExpire: 'none',
 *                  //      onExpire: null,
 *                  //      cacheFlushInterval: null,
 *                  //      recycleFreq: 1000,
 *                  //      storageMode: 'memory',
 *                  //      storageImpl: null,
 *                  //      disabled: false,
 *                  //      size: 2
 *                  //  }
 *
 * cache.info('1'); //  {
 *                  //      created: 1234567890,
 *                  //      accessed: 1234567890,
 *                  //      expires: Number.MAX_VALUE,
 *                  //      isExpired: false
 *                  //  }
 *
 * cache.info('3'); // undefined
 * ```
 *
 * @param {string=} key The key of the item whose status is to be retrieved.
 * @returns {object} The status of this cache or of the item with the given key.
 */
module.exports = function info(key) {
  if (key) {
    var item;
    if (this.$$storage) {
      var itemJson = this.$$storage.getItem(this.$$prefix + '.data.' + key);

      if (itemJson) {
        item = angular.fromJson(itemJson);
        return {
          created: item.created,
          accessed: item.accessed,
          expires: item.expires,
          isExpired: (new Date().getTime() - item.created) > this.$$maxAge
        };
      } else {
        return undefined;
      }
    } else {
      if (key in this.$$data) {
        item = this.$$data[key];

        return {
          created: item.created,
          accessed: item.accessed,
          expires: item.expires,
          isExpired: (new Date().getTime() - item.created) > this.$$maxAge
        };
      } else {
        return undefined;
      }
    }
  } else {
    return {
      id: this.$$id,
      capacity: this.$$capacity,
      maxAge: this.$$maxAge,
      deleteOnExpire: this.$$deleteOnExpire,
      onExpire: this.$$onExpire,
      cacheFlushInterval: this.$$cacheFlushInterval,
      recycleFreq: this.$$recycleFreq,
      storageMode: this.$$storageMode,
      storageImpl: this.$$storage,
      disabled: this.$$disabled,
      size: this.$$lruHeap && this.$$lruHeap.size() || 0
    };
  }
};

},{}],6:[function(require,module,exports){
var utils = require('../utils');

/**
 * @doc method
 * @id DSCache.methods:keySet
 * @name keySet
 * @description
 * Return an object of the keys in this cache.
 *
 * ## Signature:
 * ```js
 * DSCache#keySet()
 * ```
 *
 * ## Example:
 * ```js
 * var cache = DSCacheFactory('cache');
 *
 * cache.put('1', 'apple');
 * cache.put('2', 'banana');
 *
 * cache.keys(); // { "1": "1", "2": "2" }
 * ```
 *
 * @returns {object} An object of the keys in this cache.
 */
module.exports = function keySet() {
  if (this.$$storage) {
    var keysJson = this.$$storage.getItem(this.$$prefix + '.keys'),
      kSet = {};

    if (keysJson) {
      var keys = angular.fromJson(keysJson);

      for (var i = 0; i < keys.length; i++) {
        kSet[keys[i]] = keys[i];
      }
    }
    return kSet;
  } else {
    return utils.keySet(this.$$data);
  }
};

},{"../utils":21}],7:[function(require,module,exports){
var utils = require('../utils');

/**
 * @doc method
 * @id DSCache.methods:keys
 * @name keys
 * @description
 * Return an array of the keys in this cache.
 *
 * ## Signature:
 * ```js
 * DSCache#keys()
 * ```
 *
 * ## Example:
 * ```js
 * var cache = DSCacheFactory('cache');
 *
 * cache.put('1', 'apple');
 * cache.put('2', 'banana');
 *
 * cache.keys(); // [ "1", "2" ]
 * ```
 *
 * @returns {Array} An array of the keys in this cache.
 */
module.exports = function keys() {
  if (this.$$storage) {
    var keysJson = this.$$storage.getItem(this.$$prefix + '.keys');

    if (keysJson) {
      return angular.fromJson(keysJson);
    } else {
      return [];
    }
  } else {
    return utils.keys(this.$$data);
  }
};

},{"../utils":21}],8:[function(require,module,exports){
var utils = require('../utils');

/**
 * @doc method
 * @id DSCache.methods:put
 * @name put
 * @description
 * Insert a value into the cache under the given key.
 *
 * ## Signature:
 * ```js
 * DSCache#put(key, value)
 * ```
 *
 * ## Example:
 * ```js
 * var cache = DSCacheFactory('cache');
 *
 * cache.put('1', 'apple');
 * cache.put('2', 3);
 * cache.put('3', { stuff: 'more stuff' });
 *
 * cache.get('1'); // "apple"
 * cache.get('2'); // 3
 * cache.get('3'); // { stuff: 'more stuff' }
 * cache.get('4'); // undefined
 * ```
 *
 * ## Throws:
 * - `Error` - `key` must be a string.
 *
 * @param {string} key The key under which to store the given value.
 * @param {*} value The value to store.
 * @returns {*} The newly stored item.
 */
module.exports = function put(key, value) {
  var _this = this;
  if (this.$$disabled || value === null || value === undefined) {
    return;
  }
  if (value && value.then && false) {
    value.then(function (v) {
      if (angular.isObject(v) && 'status' in v && 'data' in v) {
        _this.put(key, [v.status, v.data, v.headers(), v.statusText]);
      } else {
        _this.put(key, v);
      }
    });
    return;
  }
  key = utils.stringifyNumber(key);

  if (!angular.isString(key)) {
    throw angular.$$minErr('ng')('areq', 'Expected key to be a string! Found: {0}.', typeof key);
  }

  var now = new Date().getTime(),
    item = {
      key: key,
      value: value,
      created: now,
      accessed: now
    };

  item.expires = item.created + this.$$maxAge;

  if (this.$$storage) {
    var keysJson = this.$$storage.getItem(this.$$prefix + '.keys'),
      keys = keysJson ? angular.fromJson(keysJson) : [],
      itemJson = this.$$storage.getItem(this.$$prefix + '.data.' + key);

    // Remove existing
    if (itemJson) {
      this.remove(key);
    }
    // Add to expires heap
    this.$$expiresHeap.push({
      key: key,
      expires: item.expires
    });
    // Add to lru heap
    this.$$lruHeap.push({
      key: key,
      accessed: item.accessed
    });
    // Set item
    this.$$storage.setItem(this.$$prefix + '.data.' + key, (item));
    var exists = false;
    for (var i = 0; i < keys.length; i++) {
      if (keys[i] === key) {
        exists = true;
        break;
      }
    }
    if (!exists) {
      keys.push(key);
    }
    this.$$storage.setItem(this.$$prefix + '.keys', (keys));
  } else {
    // Remove existing
    if (this.$$data[key]) {
      this.remove(key);
    }
    // Add to expires heap
    this.$$expiresHeap.push(item);
    // Add to lru heap
    this.$$lruHeap.push(item);
    // Set item
    this.$$data[key] = item;
  }

  // Handle exceeded capacity
  if (this.$$lruHeap.size() > this.$$capacity) {
    this.remove(this.$$lruHeap.peek().key);
  }

  return value;
};

},{"../utils":21}],9:[function(require,module,exports){
/**
 * @doc method
 * @id DSCache.methods:remove
 * @name remove
 * @description
 * Remove the item with the given key.
 *
 * ## Signature:
 * ```js
 * DSCache#remove(key)
 * ```
 *
 * ## Example:
 * ```js
 * var cache = DSCacheFactory('cache');
 *
 * cache.put('1', 'apple');
 *
 * cache.get('1'); // "apple"
 *
 * cache.remove('1'); // "apple"
 *
 * cache.get('1'); // undefined
 * ```
 *
 * @param {string} key The key of the item to remove.
 * @returns {*} The removed item if an item was removed.
 */
module.exports = function remove(key) {
  if (this.$$storage) {
    var itemJson = this.$$storage.getItem(this.$$prefix + '.data.' + key);

    if (itemJson) {
      var item = angular.fromJson(itemJson);
      this.$$lruHeap.remove({
        key: key,
        accessed: item.accessed
      });
      this.$$expiresHeap.remove({
        key: key,
        expires: item.expires
      });
      this.$$storage.removeItem(this.$$prefix + '.data.' + key);
      var keysJson = this.$$storage.getItem(this.$$prefix + '.keys'),
        keys = keysJson ? angular.fromJson(keysJson) : [],
        index = keys.indexOf(key);

      if (index >= 0) {
        keys.splice(index, 1);
      }
      this.$$storage.setItem(this.$$prefix + '.keys', (keys));
      return item.value;
    }
  } else {
    var value = this.$$data[key] ? this.$$data[key].value : undefined;
    this.$$lruHeap.remove(this.$$data[key]);
    this.$$expiresHeap.remove(this.$$data[key]);
    this.$$data[key] = null;
    delete this.$$data[key];
    return value;
  }
};

},{}],10:[function(require,module,exports){
/**
 * @doc method
 * @id DSCache.methods:removeAll
 * @name removeAll
 * @description
 * Remove all items from this cache.
 *
 * ## Signature:
 * ```js
 * DSCache#removeAll()
 * ```
 *
 * ## Example:
 * ```js
 * var cache = DSCacheFactory('cache');
 *
 * cache.put('1', 'apple');
 * cache.put('2', 'banana');
 * cache.info().size; // 2
 *
 * cache.get('1'); // "apple"
 * cache.get('2'); // "banana"
 *
 * cache.removeAll();
 * cache.info().size; // 0
 *
 * cache.get('1'); // undefined
 * cache.get('2'); // undefined
 * ```
 */
module.exports = function removeAll() {
  if (this.$$storage) {
    this.$$lruHeap.removeAll();
    this.$$expiresHeap.removeAll();
    var keysJson = this.$$storage.getItem(this.$$prefix + '.keys');

    if (keysJson) {
      var keys = angular.fromJson(keysJson);

      for (var i = 0; i < keys.length; i++) {
        this.remove(keys[i]);
      }
    }
    this.$$storage.setItem(this.$$prefix + '.keys', ([]));
  } else {
    this.$$lruHeap.removeAll();
    this.$$expiresHeap.removeAll();
    for (var key in this.$$data) {
      this.$$data[key] = null;
    }
    this.$$data = {};
  }
};

},{}],11:[function(require,module,exports){
/**
 * @doc method
 * @id DSCache.methods:removeExpired
 * @name removeExpired
 * @description
 * Remove and return all expired items from the cache.
 *
 * ## Signature:
 * ```js
 * DSCache#removeExpired()
 * ```
 *
 * ## Example:
 * ```js
 *  var options = {
 *          maxAge: 1000
 *      },
 *      // deleteOnExpire defaults to "none"
 *      cache = DSCacheFactory('cache', options);
 *
 *  cache.put('1', 'apple');
 *  cache.put('2', 'banana');
 *
 *  setTimeout(function () {
 *      cache.put('3', 'orange');
 *
 *      cache.info().size; // 3
 *      cache.info('1').isExpired; // true
 *      cache.info('2').isExpired; // true
 *      cache.info('3').isExpired; // false
 *
 *      cache.removeExpired(); // { "1": "apple", "2": "banana" }
 *
 *      cache.info().size; // 1
 *      cache.get('1'); // undefined
 *      cache.get('2'); // undefined
 *      cache.info('3').isExpired; // false
 *  }, 1500);
 * ```
 *
 * @returns {object} The removed items, if any.
 */
module.exports = function removeExpired() {
  var now = new Date().getTime(),
    expired = {},
    key,
    expiredItem;

  while ((expiredItem = this.$$expiresHeap.peek()) && expiredItem.expires < now) {
    expired[expiredItem.key] = expiredItem.value ? expiredItem.value : null;
    this.$$expiresHeap.pop();
  }

  if (this.$$storage) {
    for (key in expired) {
      var itemJson = this.$$storage.getItem(this.$$prefix + '.data.' + key);
      if (itemJson) {
        expired[key] = angular.fromJson(itemJson).value;
        this.remove(key);
      }
    }
  } else {
    for (key in expired) {
      this.remove(key);
    }
  }

  if (this.$$onExpire) {
    for (key in expired) {
      this.$$onExpire(key, expired[key]);
    }
  }

  return expired;
};

},{}],12:[function(require,module,exports){
/**
 * @doc method
 * @id DSCache.methods:setCacheFlushInterval
 * @name setCacheFlushInterval
 * @description
 * Set the `cacheFlushInterval` setting for this cache. If set, this setting will cause this cache to periodically
 * clear itself.
 *
 * ## Signature:
 * ```js
 * DSCache#setCacheFlushInterval(cacheFlushInterval)
 * ```
 *
 * ## Example:
 * ```js
 *  var cache = DSCacheFactory('cache');
 *
 *  cache.put('1', 'apple');
 *  cache.put('2', 'banana');
 *
 *  cache.info().size; // 2
 *  cache.setCacheFlushInterval(60000);
 *
 *  setTimeout(function () {
 *      cache.info().size; // 0
 *  }, 90000);
 * ```
 *
 * ## Throws:
 * - `Error` - `cacheFlushInterval` must be `null` or a number greater than zero.
 *
 * @param {number|null} cacheFlushInterval The new cacheFlushInterval for this cache in milliseconds. If
 * `cacheFlushInterval` is `null` then `cacheFlushInterval` for this cache will be reset to the default (`null`).
 */
module.exports = function setCacheFlushInterval(cacheFlushInterval) {
  if (cacheFlushInterval === null) {
    delete this.$$cacheFlushInterval;
  } else if (!angular.isNumber(cacheFlushInterval)) {
    throw angular.$$minErr('ng')('areq', 'Expected cacheFlushInterval to be a number! Found: {0}.', typeof cacheFlushInterval);
  } else if (cacheFlushInterval < 0) {
    throw angular.$$minErr('ng')('areq', 'Expected cacheFlushInterval to be greater than zero! Found: {0}.', cacheFlushInterval);
  } else if (cacheFlushInterval !== this.$$cacheFlushInterval) {
    this.$$cacheFlushInterval = cacheFlushInterval;
    clearInterval(this.$$cacheFlushIntervalId);
    (function (_this) {
      _this.$$cacheFlushIntervalId = setInterval(function () {
        _this.removeAll();
      }, _this.$$cacheFlushInterval);
    })(this);
  }
};

},{}],13:[function(require,module,exports){
/**
 * @doc method
 * @id DSCache.methods:setCapacity
 * @name setCapacity
 * @description
 * Set the capacity for this cache.
 *
 * ## Signature:
 * ```js
 * DSCache#setCapacity(capacity)
 * ```
 *
 * ## Example:
 * ```js
 * var smallCache = DSCacheFactory('smallCache', { capacity: 2 });
 *
 * smallCache.info().size; // 0
 *
 * smallCache.put('1', 'apple');
 * smallCache.put('2', 'banana');
 *
 * smallCache.info().size; // 2
 *
 * // Least-recently used items are removed
 * // when the cache's new capacity exceeds
 * // its size
 * smallCache.setCapacity(1);
 *
 * smallCache.get('1'); // undefined
 * smallCache.info().size; // 1
 * ```
 *
 * ## Throws:
 * - `Error` - `capacity` must be `null` or a number greater than zero.
 *
 * @param {number|null} capacity The new capacity for this cache. If `capacity` is `null` then the capacity for this cache
 * will be reset to the default (`Number.MAX_VALUE`).
 * @returns {object} Key-value pairs of any items removed because this cache's size exceeds the new capacity.
 */
module.exports = function setCapacity(capacity) {
  if (capacity === null) {
    delete this.$$capacity;
  } else if (!angular.isNumber(capacity)) {
    throw angular.$$minErr('ng')('areq', 'Expected capacity to be a number! Found: {0}.', typeof capacity);
  } else if (capacity < 0) {
    throw angular.$$minErr('ng')('areq', 'Expected capacity to be greater than zero! Found: {0}.', capacity);
  } else {
    this.$$capacity = capacity;
  }
  var removed = {};
  while (this.$$lruHeap.size() > this.$$capacity) {
    removed[this.$$lruHeap.peek().key] = this.remove(this.$$lruHeap.peek().key);
  }
  return removed;
};

},{}],14:[function(require,module,exports){
/**
 * @doc method
 * @id DSCache.methods:setDeleteOnExpire
 * @name setDeleteOnExpire
 * @description
 * Set the behavior for this cache for when items expire. This setting determines what this cache will do when one of
 * its items expires.
 *
 * ## Possible Values:
 * - `"none"` - Do nothing when items expire.
 * - `"passive"` - Do nothing when items expire, but if an expired item is requested, remove it from the cache and return `undefined`.
 * - `"aggressive"` - Scan for expired items on the interval specified by the `recycleFreq` setting for this cache (defaults
 * to `1000ms`) and actively remove any expired items.
 *
 * ## Signature:
 * ```js
 * DSCache#setDeleteOnExpire(deleteOnExpire)
 * ```
 *
 * ## Example:
 * ```js
 * var cache = DSCacheFactory('cache');
 *
 * cache.put('1', 'apple');
 *
 * // Wait a few seconds
 *
 * cache.get('1'); // "apple"
 *
 * cache.setDeleteOnExpire('aggressive');
 *
 * // Wait a few seconds
 *
 * cache.get('1'); // undefined
 * ```
 *
 * ## Throws:
 * - `Error` - `deleteOnExpire` must be `null`, `"none"`, `"passive"` or `"aggressive"`.
 *
 * @param {string|null} deleteOnExpire The new deleteOnExpire for this cache. If `deleteOnExpire` is `null` then
 * `deleteOnExpire` for this cache will be reset to the default (`"none"`).
 */
module.exports = function setDeleteOnExpire(deleteOnExpire) {
  if (deleteOnExpire === null) {
    delete this.$$deleteOnExpire;
  } else if (!angular.isString(deleteOnExpire)) {
    throw angular.$$minErr('ng')('areq', 'Expected deleteOnExpire to be a string! Found: {0}.', typeof deleteOnExpire);
  } else if (deleteOnExpire !== 'none' && deleteOnExpire !== 'passive' && deleteOnExpire !== 'aggressive') {
    throw angular.$$minErr('ng')('areq', 'Expected deleteOnExpire to be "none", "passive" or "aggressive"! Found: {0}.', deleteOnExpire);
  } else {
    this.$$deleteOnExpire = deleteOnExpire;
  }
  this.setRecycleFreq(this.$$recycleFreq);
};

},{}],15:[function(require,module,exports){
var utils = require('../utils');

/**
 * @doc method
 * @id DSCache.methods:setMaxAge
 * @name setMaxAge
 * @description
 * Set the `maxAge` setting for this cache. This setting specifies how long items can be in the cache before they expire.
 *
 * ## Signature:
 * ```js
 * DSCache#setMaxAge(maxAge)
 * ```
 *
 * ## Example:
 * ```js
 *  var cache = DSCacheFactory('cache', { deleteOnExpire: 'aggressive' });
 *
 *  // This won't expire for a long time
 *  cache.put('1', 'apple');
 *
 *  setTimeout(function () {
 *      // 'apple' will be removed because it
 *      // has already been in the cache longer
 *      // than the new maxAge
 *      var removed = cache.setMaxAge(1000);
 *
 *      removed; // {
 *               //     '1': 'apple'
 *               // }
 *  }, 1500);
 * ```
 *
 * ## Throws:
 * - `Error` - `maxAge must be `null` or a number greater than zero.
 *
 * @param {number} maxAge The new maxAge for this cache in milliseconds. If `maxAge` is `null` then `maxAge` for this
 * cache will be reset to the default (`Number.MAX_VALUE`);
 * @returns {object} Key-value pairs of any items aggressively removed because they are expired according to the new
 * `maxAge`. Items are only removed if the `deleteOnExpire` setting for this cache is set to `"aggressive"`.
 */
module.exports = function setMaxAge(maxAge) {
  if (maxAge === null) {
    delete this.$$maxAge;
  } else if (!angular.isNumber(maxAge)) {
    throw angular.$$minErr('ng')('areq', 'Expected maxAge to be a number! Found: {0}.', typeof maxAge);
  } else if (maxAge < 0) {
    throw angular.$$minErr('ng')('areq', 'Expected maxAge to be greater than zero! Found: {0}.', maxAge);
  } else {
    this.$$maxAge = maxAge;
  }
  var i, keys, key;

  this.$$expiresHeap.removeAll();

  if (this.$$storage) {
    var keysJson = this.$$storage.getItem(this.$$prefix + '.keys');

    keys = keysJson ? angular.fromJson(keysJson) : [];

    for (i = 0; i < keys.length; i++) {
      key = keys[i];
      var itemJson = this.$$storage.getItem(this.$$prefix + '.data.' + key);

      if (itemJson) {
        var item = angular.fromJson(itemJson);
        if (this.$$maxAge === Number.MAX_VALUE) {
          item.expires = Number.MAX_VALUE;
        } else {
          item.expires = item.created + this.$$maxAge;
        }
        this.$$expiresHeap.push({
          key: key,
          expires: item.expires
        });
      }
    }
  } else {
    keys = utils.keys(this.$$data);

    for (i = 0; i < keys.length; i++) {
      key = keys[i];
      if (this.$$maxAge === Number.MAX_VALUE) {
        this.$$data[key].expires = Number.MAX_VALUE;
      } else {
        this.$$data[key].expires = this.$$data[key].created + this.$$maxAge;
      }
      this.$$expiresHeap.push(this.$$data[key]);
    }
  }
  if (this.$$deleteOnExpire === 'aggressive') {
    return this.removeExpired();
  } else {
    return {};
  }
};

},{"../utils":21}],16:[function(require,module,exports){
/**
 * @doc method
 * @id DSCache.methods:setOnExpire
 * @name setOnExpire
 * @description
 * Set the global `onExpire` callback for this cache.
 *
 * ## Signature:
 * ```js
 * DSCache#setOnExpire(onExpire)
 * ```
 *
 * ## Examples:
 * ```js
 *  var options = {
 *      onExpire: function (key, value) {
 *          window.lastExpiredItem = key;
 *      },
 *      maxAge: 1000,
 *      deleteOnExpire: 'aggressive'
 *  };
 *  var cache = DSCacheFactory('cache', options);
 *
 *  cache.put('1', 'apple');
 *
 *  setTimeout(function () {
 *      window.lastExpiredItem; // '1'
 *  }, 1500);
 * ```
 *
 * ## Throws:
 * - `Error` - `cacheFlushInterval` must be `null` or a number greater than zero.
 *
 * @param {function|null} onExpire The new onExpire callback for this cache. If `onExpire` is `null` then the onExpire
 * callback for this cache will be removed.
 */
module.exports = function setOnExpire(onExpire) {
  if (onExpire === null) {
    delete this.$$onExpire;
  } else if (!angular.isFunction(onExpire)) {
    throw angular.$$minErr('ng')('areq', 'Expected onExpire to be a function! Found: {0}.', typeof onExpire);
  } else {
    this.$$onExpire = onExpire;
  }
};

},{}],17:[function(require,module,exports){
/**
 * @doc method
 * @id DSCache.methods:setRecycleFreq
 * @name setRecycleFreq
 * @description
 * Set the `recycleFreq` setting for this cache. This setting determines how often this cache will scan for expired
 * items. The cache will only scan for expired items if the `deleteOnExpire` setting for this cache is set to
 * `"aggressive"`.
 *
 * ## Signature:
 * ```js
 * DSCache#setRecycleFreq(recycleFreq)
 * ```
 *
 * ## Example:
 * ```js
 *  var options = {
 *      deleteOnExpire: 'aggressive',
 *      maxAge: 1000
 *  };
 *  var cache = DSCacheFactory('cache', options);
 *
 *  cache.put('1', 'apple');
 *
 *  setTimeout(function () {
 *
 *      cache.get('1'); // undefined
 *      cache.setRecycleFreq(60000);
 *
 *      // This expires after 1 second, but the cache
 *      // only checks every 60 seconds now
 *      cache.put('1', 'apple');
 *
 *      setTimeout(function () {
 *          // expired, but won't be removed
 *          // until the next check
 *          cache.get('1'); // "apple"
 *          cache.info('1').isExpired; // true
 *      }, 1500);
 *  }, 1500);
 * ```
 *
 * ## Throws:
 * - `Error` - `recycleFreq` must be `null` or a number greater than zero.
 *
 * @param {number} recycleFreq The new recycleFreq for this cache in milliseconds. If `recycleFreq` is `null` then
 * `recycleFreq` for this cache will be reset to the default (`1000` milliseconds).
 */
module.exports = function setRecycleFreq(recycleFreq) {
  if (recycleFreq === null) {
    delete this.$$recycleFreq;
  } else if (!angular.isNumber(recycleFreq)) {
    throw angular.$$minErr('ng')('areq', 'Expected recycleFreq to be a number! Found: {0}.', typeof recycleFreq);
  } else if (recycleFreq < 0) {
    throw angular.$$minErr('ng')('areq', 'Expected recycleFreq to be greater than zero! Found: {0}.', recycleFreq);
  } else {
    this.$$recycleFreq = recycleFreq;
  }
  clearInterval(this.$$recycleFreqId);
  if (this.$$deleteOnExpire === 'aggressive') {
    (function (_this) {
      _this.$$recycleFreqId = setInterval(function () {
        _this.removeExpired();
      }, _this.$$recycleFreq);
    })(this);
  } else {
    delete this.$$recycleFreqId;
  }
};

},{}],18:[function(require,module,exports){
var defaults = require('../defaults'),
  DSCache = require('../DSCache'),
  version = '3.1.1';

/**
 * @doc function
 * @id DSCacheFactoryProvider
 * @name DSCacheFactoryProvider
 */
function DSCacheFactoryProvider() {

  var config = new defaults.Config();

  this.version = version;

  /**
   * @doc method
   * @id DSCacheFactoryProvider.methods:setCacheDefaults
   * @name setCacheDefaults
   * @desc Set the default configuration for all caches created by $angularCacheFactory.
   * @param {object} options Default configuration options for each new cache.
   */
  this.setCacheDefaults = function (options) {
    options = options || {};

    if (!angular.isObject(options)) {
      throw angular.$$minErr('ng')('areq', 'Expected options to be an object! Found: {0}.', typeof options);
    }

    for (var key in defaults.defaults) {
      if (key in options) {
        config[key] = options[key];
      }
    }
    if ('disabled' in options) {
      config.$$disabled = !!options.disabled;
    }
  };

  this.$get = function () {
    var caches = {};

    /*!
     * @method _keys
     * @desc Returns an array of the keys of the given collection.
     * @param {object} collection The collection from which to get the keys.
     * @returns {array} An array of the keys of the given collection.
     */
    function _keys(collection) {
      var keys = [], key;
      for (key in collection) {
        if (collection.hasOwnProperty(key)) {
          keys.push(key);
        }
      }
      return keys;
    }

    function createCache(cacheId, options) {
      if (cacheId in caches) {
        throw angular.$$minErr('$cacheFactory')('iid', "CacheId '{0}' is already taken!", cacheId);
      } else if (!angular.isString(cacheId)) {
        throw angular.$$minErr('ng')('areq', 'Expected cacheId to be a string! Found: {0}.', typeof cacheId);
      }

      caches[cacheId] = new DSCache(cacheId, angular.extend({}, config, options));
      caches[cacheId].destroy = function () {
        this.constructor.prototype.destroy.call(this);
        delete caches[this.$$id];
      };
      return caches[cacheId];
    }

    /**
     * @doc function
     * @id DSCacheFactory
     * @name DSCacheFactory
     * @description
     * Factory function that produces instances of `DSCache`.
     *
     * @param {string} cacheId The id of the new cache.
     * @param {object} options Configuration options. Properties:
     *
     * - `{number=}` - `capacity` - Default: `Number.MAX_VALUE`
     * - `{number=}` - `maxAge` - Default: `null`
     * - `{number=}` - `deleteOnExpire` - Default: `none`
     * - `{function=}` - `onExpire` - Default: `null`
     * - `{number=}` - `cacheFlushInterval` - Default: `null`
     * - `{number=}` - `recycleFreq` - Default: `1000`
     * - `{number=}` - `deleteOnExpire` - Default: `null`
     * - `{string=}` - `storageMode` - Default: `'none`
     * - `{object=}` - `storageImpl` - Default: `null`
     * - `{boolean=}` - `disabled` - Default: `false`
     * - `{string=}` - `storagePrefix` - Default: `"angular-cache.caches."`
     *
     * @returns {DSCache} New instance of DSCache.
     */
    function DSCacheFactory(cacheId, options) {
      return createCache(cacheId, options);
    }

    /**
     * @doc method
     * @id DSCacheFactory.methods:createCache
     * @name createCache
     * @description
     * Factory function that produces instances of `DSCache`.
     *
     * @param {string} cacheId The id of the new cache.
     * @param {object} options Configuration options. Properties:
     *
     * - `{number=}` - `capacity` - Default: `Number.MAX_VALUE`
     * - `{number=}` - `maxAge` - Default: `null`
     * - `{number=}` - `deleteOnExpire` - Default: `none`
     * - `{function=}` - `onExpire` - Default: `null`
     * - `{number=}` - `cacheFlushInterval` - Default: `null`
     * - `{number=}` - `recycleFreq` - Default: `1000`
     * - `{number=}` - `deleteOnExpire` - Default: `null`
     * - `{string=}` - `storageMode` - Default: `'none`
     * - `{object=}` - `storageImpl` - Default: `null`
     * - `{boolean=}` - `disabled` - Default: `false`
     * - `{string=}` - `storagePrefix` - Default: `"angular-cache.caches."`
     *
     * @returns {DSCache} New instance of DSCache.
     */
    DSCacheFactory.createCache = createCache;

    DSCacheFactory.version = version;

    /**
     * @doc method
     * @id DSCacheFactory.methods:info
     * @name info
     * @description
     * Return the status of `DSCacheFactory`.
     * @returns {object} The status of `DSCacheFactory`.
     */
    DSCacheFactory.info = function () {
      var keys = _keys(caches);
      var info = {
        size: keys.length,
        caches: {}
      };
      for (var i = 0; i < keys.length; i++) {
        var key = keys[i];
        info.caches[key] = caches[key].info();
      }
      var c = info.cacheDefaults = angular.extend({}, config);
      for (var option in defaults.defaults) {
        if (!(option in c)) {
          c[option] = config['$$' + option];
        }
      }
      return info;
    };

    /**
     * @doc method
     * @id DSCacheFactory.methods:get
     * @name get
     * @description
     * Return the cache with the given `cacheId`.
     * @param {string} cacheId The id of the desired cache.
     * @returns {DSCache} The cache with the specified `cacheId`.
     */
    DSCacheFactory.get = function (cacheId) {
      if (!angular.isString(cacheId)) {
        throw angular.$$minErr('ng')('areq', 'Expected cacheId to be a string! Found: {0}.', typeof cacheId);
      }
      return caches[cacheId];
    };

    /**
     * @doc method
     * @id DSCacheFactory.methods:keySet
     * @name keySet
     * @description
     * Return an object containing the `cacheId` of each cache.
     * @returns {object} An object containing the `cacheId` of each cache.
     */
    DSCacheFactory.keySet = function () {
      var cacheIds = {}, cacheId;
      for (cacheId in caches) {
        if (caches.hasOwnProperty(cacheId)) {
          cacheIds[cacheId] = cacheId;
        }
      }
      return cacheIds;
    };

    /**
     * @doc method
     * @id DSCacheFactory.methods:keys
     * @name keys
     * @description
     * Return an array containing the `cacheId` of each cache.
     * @returns {array} An array containing the `cacheId` of each cache.
     */
    DSCacheFactory.keys = function () {
      return _keys(caches);
    };

    /**
     * @doc method
     * @id DSCacheFactory.methods:destroyAll
     * @name destroyAll
     * @description
     * Destroy all caches.
     *
     * ## Signature:
     * ```js
     * DSCacheFactory.destroyAll()
     * ```
     *
     * ## Example:
     * ```js
     * var newCache = DSCacheFactory('newCache');
     * var otherCache = DSCacheFactory('otherCache');
     *
     * newCache.info().size; // 0
     * otherCache.info().size; // 0
     *
     * newCache.put('1', 'apple');
     * newCache.put('2', 'banana');
     * otherCache.put('abcd', 'horse');
     *
     * newCache.info().size; // 2
     * otherCache.info().size; // 1
     *
     * DSCacheFactory.destroyAll();
     *
     * newCache.info().size; // Error thrown
     * otherCache.info().size; // Error thrown
     *
     * DSCacheFactory.get('newCache'); // undefined
     * DSCacheFactory.get('otherCache'); // undefined
     * ```
     */
    DSCacheFactory.destroyAll = function () {
      for (var cacheId in caches) {
        caches[cacheId].destroy();
      }
      caches = {};
    };

    /**
     * @doc method
     * @id DSCacheFactory.methods:clearAll
     * @name clearAll
     * @description
     * Clear the contents of all caches.
     *
     * ## Signature:
     * ```js
     * DSCacheFactory.clearAll()
     * ```
     *
     * ## Example:
     * ```js
     * var newCache = DSCacheFactory('newCache');
     * var otherCache = DSCacheFactory('otherCache');
     *
     * newCache.info().size; // 0
     * otherCache.info().size; // 0
     *
     * newCache.put('1', 'apple');
     * newCache.put('2', 'banana');
     * otherCache.put('abcd', 'horse');
     *
     * newCache.info().size; // 2
     * otherCache.info().size; // 1
     *
     * DSCacheFactory.clearAll();
     *
     * newCache.info().size; // 0
     * otherCache.info().size; // 0
     * ```
     */
    DSCacheFactory.clearAll = function () {
      for (var cacheId in caches) {
        caches[cacheId].removeAll();
      }
    };

    /**
     * @doc method
     * @id DSCacheFactory.methods:enableAll
     * @name enableAll
     * @description
     * Enable any disabled caches.
     *
     * ## Signature:
     * ```js
     * DSCacheFactory.enableAll()
     * ```
     *
     * ## Example:
     * ```js
     * var newCache = DSCacheFactory('newCache', { disabled: true });
     * var otherCache = DSCacheFactory('otherCache', { disabled: true });
     *
     * newCache.info().disabled; // true
     * otherCache.info().disabled; // true
     *
     * DSCacheFactory.enableAll();
     *
     * newCache.info().disabled; // false
     * otherCache.info().disabled; // false
     * ```
     */
    DSCacheFactory.enableAll = function () {
      for (var cacheId in caches) {
        caches[cacheId].$$disabled = false;
      }
    };

    /**
     * @doc method
     * @id DSCacheFactory.methods:disableAll
     * @name disableAll
     * @description
     * Disable all caches.
     *
     * ## Signature:
     * ```js
     * DSCacheFactory.disableAll()
     * ```
     *
     * ## Example:
     * ```js
     * var newCache = DSCacheFactory('newCache');
     * var otherCache = DSCacheFactory('otherCache');
     *
     * newCache.info().disabled; // false
     * otherCache.info().disabled; // false
     *
     * DSCacheFactory.disableAll();
     *
     * newCache.info().disabled; // true
     * otherCache.info().disabled; // true
     * ```
     */
    DSCacheFactory.disableAll = function () {
      for (var cacheId in caches) {
        caches[cacheId].$$disabled = true;
      }
    };

    return DSCacheFactory;
  };
}

module.exports = DSCacheFactoryProvider;

},{"../DSCache":4,"../defaults":19}],19:[function(require,module,exports){
var defaults = {
  /**
   * @doc overview
   * @id capacity
   * @name capacity
   * @description
   * __Default:__ `Number.MAX_VALUE`
   *
   * This option limits the capacity of a cache. With a maximum capacity set, a cache operates as an LRU cache,
   * deleting the least-recently-used item when the cache exceeds capacity.
   *
   * This option is dynamically configurable. Must be a number (milliseconds) greater than zero.
   *
   * ### Where can it be used?
   * - `DSCacheFactoryProvider.setCacheDefaults(options)`
   * - `DSCacheFactory(cacheId[, options])`
   * - `DSCache.setCapacity(capacity)`
   * - `DSCache.setOptions(options[, strict])`
   */
  capacity: Number.MAX_VALUE,

  /**
   * @doc overview
   * @id maxAge
   * @name maxAge
   * @description
   * __Default:__ `Number.MAX_VALUE`
   *
   * This option determines how long an item is in a cache before the item expires.. With `maxAge` set, items are
   * marked as expired when their time in a cache exceeds `maxAge`. A cache's behavior when an item expires is
   * determined by the [deleteOnExpire](/documentation/api/angular-cache/deleteOnExpire) option.
   *
   * This option is dynamically configurable. Must be a number (milliseconds) greater than zero.
   *
   * ### Where can it be used?
   * - `DSCacheFactoryProvider.setCacheDefaults(options)`
   * - `DSCacheFactory(cacheId[, options])`
   * - `DSCache.setMaxAge(maxAge)`
   * - `DSCache.setOptions(options[, strict])`
   */
  maxAge: Number.MAX_VALUE,

  /**
   * @doc overview
   * @id deleteOnExpire
   * @name deleteOnExpire
   * @description
   * __Default:__ `"none"`
   *
   * This option determines how long an item is in a cache before the item expires.. With `maxAge` set, items are
   * marked as expired when their time in a cache exceeds `maxAge`. A cache's behavior when an item expires is
   * determined by the [deleteOnExpire](/documentation/api/angular-cache/deleteOnExpire) option.
   *
   * This option is dynamically configurable. Must be `"none"`, `"passive"` or `"aggressive"`.
   *
   * #### "none"
   * A cache will do nothing when its items expire.
   *
   * #### "passive"
   * A cache will do nothing when its items expire. If an expired item is request it is removed from the cache and
   * `undefined` is returned.
   *
   * #### "aggressive"
   * A cache will periodically scan for expired items and actively remove them from the cache if any are found. The
   * frequency of the scan is determined by the [recycleFreq](/documentation/api/angular-cache/recycleFreq) option.
   *
   * ### Where can it be used?
   * - `DSCacheFactoryProvider.setCacheDefaults(options)`
   * - `DSCacheFactory(cacheId[, options])`
   * - `DSCache.setRecycleFreq(recycleFreq)`
   * - `DSCache.setOptions(options[, strict])`
   */
  deleteOnExpire: 'none',

  /**
   * @doc overview
   * @id onExpire
   * @name onExpire
   * @description
   * __Default:__ `"none"`
   *
   * This option is a callback function which will be executed whenever an expired item is removed from a cache by
   * either requesting an expired item while the cache is in `"passive"` `deleteOnExpire` mode, or when an expired
   * item is actively removed when the cache is in `"aggressive"` `deleteOnExpire` mode.
   *
   * This option is dynamically configurable. Must be a function. Will be passed the `key` and `value` of the expired
   * item. Will be passed a third `done` argument (if in `"passive"` `deleteOnExpire` mode) which is the `onExpire`
   * argument passed to [DSCache#get(key[, options])](/documentation/api/angular-cache/DSCache.methods:get).
   *
   * ### Where can it be used?
   * - `DSCacheFactoryProvider.setCacheDefaults(options)`
   * - `DSCacheFactory(cacheId[, options])`
   * - `DSCache.setOnExpire(onExpire)`
   * - `DSCache.setOptions(options[, strict])`
   */
  onExpire: null,

  /**
   * @doc overview
   * @id cacheFlushInterval
   * @name cacheFlushInterval
   * @description
   * __Default:__ `null`
   *
   * This option, if set, will cause a cache to periodically clear itself of all data.
   *
   * This option is dynamically configurable. Must be a number (milliseconds) greater than zero.
   *
   * ### Where can it be used?
   * - `DSCacheFactoryProvider.setCacheDefaults(options)`
   * - `DSCacheFactory(cacheId[, options])`
   * - `DSCache.setCacheFlushInterval(cacheFlushInterval)`
   * - `DSCache.setOptions(options[, strict])`
   */
  cacheFlushInterval: null,

  /**
   * @doc overview
   * @id recycleFreq
   * @name recycleFreq
   * @description
   * __Default:__ `1000`
   *
   * This option determines how often a cache will scan for expired items when in `"aggressive"` `deleteOnExpire`
   * mode.
   *
   * This option is dynamically configurable. Must be a number (milliseconds) greater than zero.
   *
   * ### Where can it be used?
   * - `DSCacheFactoryProvider.setCacheDefaults(options)`
   * - `DSCacheFactory(cacheId[, options])`
   * - `DSCache.setRecycleFreq(recycleFreq)`
   * - `DSCache.setOptions(options[, strict])`
   */
  recycleFreq: 1000,

  /**
   * @doc overview
   * @id storageMode
   * @name storageMode
   * @description
   * __Default:__ `"memory"`
   *
   * This option determines the storage mode for a cache.
   *
   * #### "memory"
   * All data will be held in memory.
   *
   * #### "localStorage"
   * Data will be held in `localStorage`, if available (or
   * [storageImpl](/documentation/api/angular-cache/storageImpl) is provided).
   *
   * #### "sessionStorage"
   * Data will be held in `sessionStorage`, if available (or
   * [storageImpl](/documentation/api/angular-cache/storageImpl) is provided).
   *
   * This option is NOT dynamically configurable. Must be `"memory"`, `"localStorage"` or `"sessionStorage"`.
   *
   * ### Where can it be used?
   * - `DSCacheFactoryProvider.setCacheDefaults(options)`
   * - `DSCacheFactory(cacheId[, options])`
   */
  storageMode: 'memory',

  /**
   * @doc overview
   * @id storageImpl
   * @name storageImpl
   * @description
   * __Default:__ `null`
   *
   * This option is available if you want to provide a custom `localStorage` or `sessionStorage` implementation.
   *
   * This option is NOT dynamically configurable. Must be an object that implements `setItem(key, value)`,
   * `getItem(key)` and `removeItem(key)`.
   *
   * ### Where can it be used?
   * - `DSCacheFactoryProvider.setCacheDefaults(options)`
   * - `DSCacheFactory(cacheId[, options])`
   */
  storageImpl: null,

  /**
   * @doc overview
   * @id disabled
   * @name disabled
   * @description
   * __Default:__ `false`
   *
   * This option disables or enables cache.
   *
   * This option is dynamically configurable. Must be `true` or `false`.
   *
   * ### Where can it be used?
   * - `DSCacheFactoryProvider.setCacheDefaults(options)`
   * - `DSCacheFactory(cacheId[, options])`
   * - `DSCache.setOptions(options[, strict])`
   *
   * or just use [DSCache#disable()](/documentation/api/angular-cache/DSCache.methods:disable) or
   * [DSCache#enable()](/documentation/api/angular-cache/DSCache.methods:enable).
   */
  disabled: false,

  /**
   * @doc overview
   * @id storagePrefix
   * @name storagePrefix
   * @description
   * __Default:__ `"angular-cache.caches."`
   *
   * This option determines the namespace for a cache when `storageMode` is `"localStorage"` or `"sessionStorage"`.
   * Setting this value to something like `"ac."` will save space when using WebStorage.
   *
   * This option is NOT dynamically configurable. Must be a string.
   *
   * ### Where can it be used?
   * - `DSCacheFactoryProvider.setCacheDefaults(options)`
   * - `DSCacheFactory(cacheId[, options])`
   */
  storagePrefix: 'angular-cache.caches.'
};

function Config() {
}

for (var option in defaults) {
  Config.prototype['$$' + option] = defaults[option];
}

module.exports = {
  Config: Config,
  defaults: defaults
};

},{}],20:[function(require,module,exports){
(function (window, angular, undefined) {
  'use strict';

  angular.$$minErr = angular.$$minErr || function minErr(module) {
    return function () {
      var code = arguments[0],
        prefix = '[' + (module ? module + ':' : '') + code + '] ',
        template = arguments[1],
        templateArgs = arguments,
        stringify = function (obj) {
          if (typeof obj === 'function') {
            return obj.toString().replace(/ \{[\s\S]*$/, '');
          } else if (typeof obj === 'undefined') {
            return 'undefined';
          } else if (typeof obj !== 'string') {
            return JSON.stringify(obj);
          }
          return obj;
        },
        message, i;

      message = prefix + template.replace(/\{\d+\}/g, function (match) {
        var index = +match.slice(1, -1), arg;

        if (index + 2 < templateArgs.length) {
          arg = templateArgs[index + 2];
          if (typeof arg === 'function') {
            return arg.toString().replace(/ ?\{[\s\S]*$/, '');
          } else if (typeof arg === 'undefined') {
            return 'undefined';
          } else if (typeof arg !== 'string') {
            return angular.toJson(arg);
          }
          return arg;
        }
        return match;
      });

      message = message + '\nhttp://errors.angularjs.org/' + angular.version.full + '/' +
        (module ? module + '/' : '') + code;
      for (i = 2; i < arguments.length; i++) {
        message = message + (i == 2 ? '?' : '&') + 'p' + (i - 2) + '=' +
          encodeURIComponent(stringify(arguments[i]));
      }

      return new Error(message);
    };
  };


  angular.module('app')
    .provider('DSBinaryHeap', require('./DSBinaryHeap').DSBinaryHeapProvider);

  /**
   * @doc overview
   * @id angular-cache
   * @name Overview
   * @description
   * __Version:__ 3.1.1
   *
   * ## Install
   *
   * #### Bower
   * ```text
   * bower install angular-cache
   * ```
   *
   * Load `dist/angular-cache.js` or `dist/angular-cache.min.js` onto your web page after Angular.js.
   *
   * #### Npm
   * ```text
   * npm install angular-cache
   * ```
   *
   * Load `dist/angular-cache.js` or `dist/angular-cache.min.js` onto your web page after Angular.js. Angular-cache is
   * also consumable by Browserify and you should be able to `require('angular-cache')`. The `main` file is `src/index.js`.
   *
   * #### Manual download
   * Download angular-cache.3.1.1.js from the [Releases](https://github.com/jmdobry/angular-cache/releases)
   * section of the angular-cache GitHub project.
   *
   * ## Load into Angular
   * Your Angular app must depend on the module `"angular-data.DSCacheFactory"` in order to use angular-cache. Loading
   * angular-cache into your app allows you to inject the following:
   *
   * - `DSCacheFactory`
   * - `DSBinaryHeap`
   *
   * [DSCacheFactory](/documentation/api/api/DSCacheFactory) is a factory function that produces instances of
   * [DSCache](/documentation/api/api/DSCache), which is API compatible with caches produced by Angular's
   * [$cacheFactory](http://docs.angularjs.org/api/ng/service/$cacheFactory).
   *
   * [DSBinaryHeap](/documentation/api/api/DSBinaryHeap) is a priority queue implemented as a Binary Heap.
   *
   * Angular-cache is a dependency of [angular-data](/documentation/api/api/angular-data) and must be loaded before
   * angular-data if you are using angular-data.
   */
  angular.module('app')
    .provider('DSCacheFactory', require('./DSCacheFactory'));

})(window, window.angular);

},{"./DSBinaryHeap":1,"./DSCacheFactory":18}],21:[function(require,module,exports){
module.exports = {
  /*!
   * Stringify a number.
   */
  stringifyNumber: function (number) {
    if (number && angular.isNumber(number)) {
      return number.toString();
    }
    return number;
  },

  /*!
   * Return a hash of the keys in the given collection.
   */
  keySet: function (collection) {
    var keySet = {}, key;
    for (key in collection) {
      if (collection.hasOwnProperty(key)) {
        keySet[key] = key;
      }
    }
    return keySet;
  },

  /*!
   * Return an array of the keys in the given collection
   */
  keys: function (collection) {
    var keys = [], key;
    for (key in collection) {
      if (collection.hasOwnProperty(key)) {
        keys.push(key);
      }
    }
    return keys;
  }
};

},{}]},{},[20]);
(function () {
    'use strict';

    angular.module('app')
        .service('dateParser', ['$locale', 'orderByFilter', function ($locale, orderByFilter) {

            this.parsers = {};

            var formatCodeToRegex = {
                'yyyy': {
                    regex: '\\d{4}',
                    apply: function (value) {
                        this.year = +value;
                    }
                },
                'yy': {
                    regex: '\\d{2}',
                    apply: function (value) {
                        this.year = +value + 2000;
                    }
                },
                'y': {
                    regex: '\\d{1,4}',
                    apply: function (value) {
                        this.year = +value;
                    }
                },
                'MMMM': {
                    regex: $locale.DATETIME_FORMATS.MONTH.join('|'),
                    apply: function (value) {
                        this.month = $locale.DATETIME_FORMATS.MONTH.indexOf(value);
                    }
                },
                'MMM': {
                    regex: $locale.DATETIME_FORMATS.SHORTMONTH.join('|'),
                    apply: function (value) {
                        this.month = $locale.DATETIME_FORMATS.SHORTMONTH.indexOf(value);
                    }
                },
                'MM': {
                    regex: '0[1-9]|1[0-2]',
                    apply: function (value) {
                        this.month = value - 1;
                    }
                },
                'M': {
                    regex: '[1-9]|1[0-2]',
                    apply: function (value) {
                        this.month = value - 1;
                    }
                },
                'dd': {
                    regex: '[0-2][0-9]{1}|3[0-1]{1}',
                    apply: function (value) {
                        this.date = +value;
                    }
                },
                'd': {
                    regex: '[1-2]?[0-9]{1}|3[0-1]{1}',
                    apply: function (value) {
                        this.date = +value;
                    }
                },
                'EEEE': {
                    regex: $locale.DATETIME_FORMATS.DAY.join('|')
                },
                'EEE': {
                    regex: $locale.DATETIME_FORMATS.SHORTDAY.join('|')
                }
            };

            function createParser(format) {
                var map = [],
                    regex = format.split('');

                angular.forEach(formatCodeToRegex, function (data, code) {
                    var index = format.indexOf(code);

                    if (index > -1) {
                        format = format.split('');

                        regex[index] = '(' + data.regex + ')';
                        format[index] = '$'; // Custom symbol to define consumed part of format
                        for (var i = index + 1, n = index + code.length; i < n; i++) {
                            regex[i] = '';
                            format[i] = '$';
                        }
                        format = format.join('');

                        map.push({
                            index: index,
                            apply: data.apply
                        });
                    }
                });

                return {
                    regex: new RegExp('^' + regex.join('') + '$'),
                    map: orderByFilter(map, 'index')
                };
            }

            this.parse = function (input, format) {
                if (!angular.isString(input) || !format) {
                    return input;
                }

                format = $locale.DATETIME_FORMATS[format] || format;

                if (!this.parsers[format]) {
                    this.parsers[format] = createParser(format);
                }

                var parser = this.parsers[format],
                    regex = parser.regex,
                    map = parser.map,
                    results = input.match(regex);

                if (results && results.length) {
                    var fields = {
                            year: 1900,
                            month: 0,
                            date: 1,
                            hours: 0
                        },
                        dt;

                    for (var i = 1, n = results.length; i < n; i++) {
                        var mapper = map[i - 1];
                        if (mapper.apply) {
                            mapper.apply.call(fields, results[i]);
                        }
                    }

                    if (isValid(fields.year, fields.month, fields.date)) {
                        dt = new Date(fields.year, fields.month, fields.date, fields.hours);
                    }

                    return dt;
                }
            };

            // Check if date is valid for specific month (and year for February).
            // Month: 0 = Jan, 1 = Feb, etc
            function isValid(year, month, date) {
                if (month === 1 && date > 28) {
                    return date === 29 && ((year % 4 === 0 && year % 100 !== 0) || year % 400 === 0);
                }

                if (month === 3 || month === 5 || month === 8 || month === 10) {
                    return date < 31;
                }

                return true;
            }
        }])
        .directive('timeDatePicker', [
            '$filter', '$sce', '$rootScope', '$parse',
            function ($filter, $sce, $rootScope, $parse) {
                var _dateFilter;
                _dateFilter = $filter('date');
                return {
                    restrict: 'AE',
                    replace: true,
                    scope: {
                        _modelValue: '=ngModel'
                    },
                    require: 'ngModel',
                    templateUrl: 'core/datetime/input.html',
                    link: function (scope, element, attrs, ngModel) {
                        var cancelFn, saveFn;
                        attrs.$observe('defaultMode', function (val) {
                            return scope._mode = val != null ? val : 'date';
                        });
                        attrs.$observe('displayMode', function (val) {
                            return scope._displayMode = val;
                        });
                        attrs.$observe('orientation', function (val) {
                            return scope._verticalMode = val === 'true';
                        });
                        attrs.$observe('displayTwentyfour', function (val) {
                            return scope._hours24 = (val != null) && val;
                        });
                        attrs.$observe('mindate', function (val) {
                            if ((val != null) && angular.isDate(val)) {
                                return scope.restrictions.mindate = val;
                            }
                        });
                        attrs.$observe('maxdate', function (val) {
                            if ((val != null) && angular.isDate(val)) {
                                return scope.restrictions.maxdate = val;
                            }
                        });
                        ngModel.$render = function () {
                            return scope.setDate(ngModel.$modelValue);
                        };
                        saveFn = $parse(attrs.onSave);
                        cancelFn = $parse(attrs.onCancel);
                        scope.save = function () {
                            scope._modelValue = scope.date;
                            ngModel.$setDirty();
                            return saveFn(scope.$parent, {
                                $value: scope.date
                            });
                        };
                        return scope.cancel = function () {
                            cancelFn(scope.$parent, {});
                            return ngModel.$render();
                        };
                    },
                    controller: [
                        '$scope',
                        function (scope) {
                            var i;
                            scope.restrictions = {
                                mindate: void 0,
                                maxdate: void 0
                            };
                            scope.setDate = function (newVal) {
                                scope.date = newVal != null ? new Date(newVal) : new Date();
                                scope.calendar._year = scope.date.getFullYear();
                                scope.calendar._month = scope.date.getMonth();
                                scope.clock._minutes = scope.date.getMinutes();
                                scope.clock._hours = scope._hours24 ? scope.date.getHours() : scope.date.getHours() % 12;
                                if (!scope._hours24 && scope.clock._hours === 0) {
                                    return scope.clock._hours = 12;
                                }
                            };
                            scope.display = {
                                fullTitle: function () {
                                    return _dateFilter(scope.date, 'EEEE d MMMM yyyy, h:mm a');
                                },
                                title: function () {
                                    if (scope._mode === 'date') {
                                        return _dateFilter(scope.date, (scope._displayMode === 'date' ? 'EEEE' : 'EEEE h:mm a'));
                                    } else {
                                        return _dateFilter(scope.date, 'MMMM d yyyy');
                                    }
                                },
                                "super": function () {
                                    if (scope._mode === 'date') {
                                        return _dateFilter(scope.date, 'MMM');
                                    } else {
                                        return '';
                                    }
                                },
                                main: function () {
                                    return $sce.trustAsHtml(scope._mode === 'date' ? _dateFilter(scope.date, 'd') : "" + (_dateFilter(scope.date, 'h:mm')) + "<small>" + (_dateFilter(scope.date, 'a')) + "</small>");
                                },
                                sub: function () {
                                    if (scope._mode === 'date') {
                                        return _dateFilter(scope.date, 'yyyy');
                                    } else {
                                        return _dateFilter(scope.date, 'HH:mm');
                                    }
                                }
                            };
                            scope.calendar = {
                                _month: 0,
                                _year: 0,
                                _months: (function () {
                                    var _i, _results;
                                    _results = [];
                                    for (i = _i = 0; _i <= 11; i = ++_i) {
                                        _results.push(_dateFilter(new Date(0, i), 'MMMM'));
                                    }
                                    return _results;
                                })(),
                                offsetMargin: function () {
                                    return new Date(this._year, this._month).getDay();
                                },
                                isVisible: function (d) {
                                    return new Date(this._year, this._month, d).getMonth() === this._month;
                                },
                                "class": function (d) {
                                    if ((scope.date != null) && new Date(this._year, this._month, d).getTime() === new Date(scope.date.getTime()).setHours(0, 0, 0, 0)) {
                                        return "selected";
                                    } else if (new Date(this._year, this._month, d).getTime() === new Date().setHours(0, 0, 0, 0)) {
                                        return "today";
                                    } else {
                                        return "";
                                    }
                                },
                                select: function (d) {
                                    var sets = scope.date.setFullYear(this._year, this._month, d);
                                    scope.save();
                                    return sets;
                                },
                                monthChange: function () {
                                    if ((this._year == null) || isNaN(this._year)) {
                                        this._year = new Date().getFullYear();
                                    }
                                    scope.date.setFullYear(this._year, this._month);
                                    if (scope.date.getMonth() !== this._month) {
                                        return scope.date.setDate(0);
                                    }
                                },
                                _incMonth: function (months) {
                                    this._month += months;
                                    while (this._month < 0 || this._month > 11) {
                                        if (this._month < 0) {
                                            this._month += 12;
                                            this._year--;
                                        } else {
                                            this._month -= 12;
                                            this._year++;
                                        }
                                    }
                                    return this.monthChange();
                                }
                            };
                            scope.clock = {
                                _minutes: 0,
                                _hours: 0,
                                _incHours: function (inc) {
                                    this._hours = scope._hours24 ? Math.max(0, Math.min(23, this._hours + inc)) : Math.max(1, Math.min(12, this._hours + inc));
                                    if (isNaN(this._hours)) {
                                        return this._hours = 0;
                                    }
                                },
                                _incMinutes: function (inc) {
                                    this._minutes = Math.max(0, Math.min(59, this._minutes + inc));
                                    if (isNaN(this._minutes)) {
                                        return this._minutes = 0;
                                    }
                                },
                                setAM: function (b) {
                                    if (b == null) {
                                        b = !this.isAM();
                                    }
                                    if (b && !this.isAM()) {
                                        return scope.date.setHours(scope.date.getHours() - 12);
                                    } else if (!b && this.isAM()) {
                                        return scope.date.setHours(scope.date.getHours() + 12);
                                    }
                                },
                                isAM: function () {
                                    return scope.date.getHours() < 12;
                                }
                            };
                            scope.$watch('clock._minutes', function (val, oldVal) {
                                if ((val != null) && val !== scope.date.getMinutes() && !isNaN(val) && (0 <= val && val <= 59)) {
                                    var sets = scope.date.setMinutes(val);
                                    sets = scope.date.setSeconds(0);
                                    scope.save();
                                    return sets;
                                }
                            });
                            scope.$watch('clock._hours', function (val) {
                                if ((val != null) && !isNaN(val)) {
                                    if (!scope._hours24) {
                                        if (val === 24) {
                                            val = 12;
                                        } else if (val === 12) {
                                            val = 0;
                                        } else if (!scope.clock.isAM()) {
                                            val += 12;
                                        }
                                    }
                                    if (val !== scope.date.getHours()) {
                                        var sets = scope.date.setHours(val);
                                        scope.save();
                                        return sets;
                                    }
                                }
                            });
                            scope.setNow = function () {
                                return scope.setDate();
                            };
                            scope._mode = 'date';
                            scope.modeClass = function () {
                                if (scope._displayMode != null) {
                                    scope._mode = scope._displayMode;
                                }
                                return "" + ((scope._verticalMode != null) && scope._verticalMode ? 'vertical ' : '') + (scope._displayMode === 'full' ? 'full-mode' : scope._displayMode === 'time' ? 'time-only' : scope._displayMode === 'date' ? 'date-only' : scope._mode === 'date' ? 'date-mode' : 'time-mode');
                            };
                            scope.modeSwitch = function () {
                                var _ref;
                                return scope._mode = (_ref = scope._displayMode) != null ? _ref : scope._mode === 'date' ? 'time' : 'date';
                            };
                            return scope.modeSwitchText = function () {
                                if (scope._mode === 'date') {
                                    return 'Clock';
                                } else {
                                    return 'Calendar';
                                }
                            };
                        }
                    ]
                };
            }
        ]).directive('timeDatePickerDialog', function ($modal, dateFilter, dateParser, GLOBAL_CONFIG) {
            return {
                require: ['ngModel', '^form'],
                link: function (scope, element, attrs, ctrls) {
                    var ngModel = ctrls[0],
                        form = ctrls[1];
                    ngModel.$render = function () {
                        element.val(dateFilter(ngModel.$modelValue, GLOBAL_CONFIG.date.format));
                    };

                    element.on('click', function (event) {
                        $modal.open({
                            windowClass: 'modal-medium',
                            targetEvent: event,
                            templateUrl: 'core/datetime/popup.html',
                            fullScreen: false,
                            controller: function ($scope) {
                                $scope.date = ngModel.$modelValue;
                                $scope.select = function () {
                                    ngModel.$setViewValue($scope.date);
                                    ngModel.$render();
                                    $scope.$close();
                                };
                            }
                        });

                        event.preventDefault();
                    });

                    ngModel.$parsers.unshift(function parseDate(viewValue) {
                        if (!viewValue) {
                            ngModel.$setValidity('date', true);
                            return null;
                        } else if (angular.isDate(viewValue) && !isNaN(viewValue)) {
                            ngModel.$setValidity('date', true);
                            return viewValue;
                        } else if (angular.isString(viewValue)) {
                            var date = dateParser.parse(viewValue, dateFormat) || new Date(viewValue);
                            if (isNaN(date)) {
                                ngModel.$setValidity('date', false);
                                return undefined;
                            } else {
                                ngModel.$setValidity('date', true);
                                return date;
                            }
                        } else {
                            ngModel.$setValidity('date', false);
                            return undefined;
                        }
                    });
                }

            };
        });
}());
(function () {
    'use strict';
    angular.module('app')
        .run(function (helpers) {
            helpers.fieldSorter = function (prev, next) {
                var p1 = parseInt(prev.name, 10),
                    p2 = parseInt(next.name, 10);
                if (isNaN(p1)) {
                    p1 = 999999;
                }
                if (isNaN(p2)) {
                    p2 = 999999;
                }
                return p1 - p2;
            };
        })
        .directive('jsonOnly', function () {
            return {
                require: 'ngModel',
                link: function (scope, element, attrs, ctrl) {
                    var worker = function (value, what) {

                            var test = false;

                            try {
                                value = angular[what](value);
                                test = true;

                            } catch (ignore) {}

                            ctrl.$setValidity('jsonOnly', test);

                            return value;
                        },
                        parser = function (value) {
                            return worker(value, 'fromJson');
                        },
                        formatter = function (value) {
                            return worker(value, 'toJson');
                        };

                    ctrl.$parsers.push(parser);
                    ctrl.$formatters.push(formatter);
                }
            };
        })
        .directive('repeatedText', function (helpers) {
            return {
                require: 'ngModel',
                link: function (scope, element, attrs, ctrl) {

                    var worker = function (value, what) {

                            var test = false;

                            try {
                                if (what === 'list') {
                                    value = helpers.splitLines(value);
                                }
                                if (what === 'str') {
                                    if (angular.isArray(value)) {
                                        value = value.join('\n');
                                    }
                                }
                                test = true;

                            } catch (ignore) {}

                            ctrl.$setValidity('repeatedText', test);

                            return value;
                        },
                        parser = function (value) {
                            return worker(value, 'list');
                        },
                        formatter = function (value) {
                            return worker(value, 'str');
                        };

                    ctrl.$parsers.push(parser);
                    ctrl.$formatters.push(formatter);
                }
            };
        })
        .directive('generateUploadUrl', function (endpoint, $rootScope) {
            return {
                restrict: 'A',
                require: '^form',
                link: function (scope, element, attrs, ctrl) {

                    var that = element,
                        form = that.parents('form:first'),
                        change = function () {

                            if (!that.val()) {
                                return false;
                            }

                            endpoint.post('blob_upload_url', '11', {
                                upload_url: endpoint.url
                            }).then(function (response) {
                                form.attr('action', response.data.upload_url);
                                ctrl.$setDirty();
                            });
                        },
                        reset = function ($event, content) {
                            form.attr('action', endpoint.url);
                            that.val('');
                        };

                    if (!form.length) {
                        console.error('Directive generateUploadUrl demands explicit <form> tag');
                        return false;
                    }

                    $(element).on('change', change);

                    scope.$on('$destroy', function () {
                        $(element).off('change', change);
                    });

                    scope.$on('ngUploadComplete', reset);
                    scope.$on('ngUploadCompleteError', change);
                }
            };
        }).directive('formBuilder', function ($compile, underscoreTemplate, modelsMeta) {
            /**
             * Main builder. It will construct a form based on a list of configuration params:
             * [
             * {
             *    ... field data
             *
             *    ui : {... user defined dictionary }
             * }
             * ]
             *
             */

            return {
                restrict: 'A',
                require: '^form',
                templateUrl: 'core/fields/builder.html',
                controller: function ($scope, $element, $attrs) {
                    $scope.configurations = $scope.$eval($attrs.formBuilder);
                }
            };
        })
        .directive('formInput', function ($compile, underscoreTemplate,
            formInputTypes, helpers) {

            var types = formInputTypes,
                utils = {
                    attrs: function (config) {
                        var defaults = this.default_attrs(config),
                            extra = this.extra_attrs(config),
                            attrs = [];

                        angular.extend(defaults, extra);

                        angular.forEach(defaults, function (value, key) {
                            attrs.push(key + (value ? '="' + value + '"' : ''));
                        });

                        return attrs.join(' ');
                    },
                    default_attrs: function (config) {
                        var attrs = {},
                            writableCompiled;
                        if (config.max_size) {
                            attrs['ng-maxlength'] = 'config.max_size';
                        }

                        if (config.ui.pattern !== undefined) {
                            attrs['ng-pattern'] = config.pattern;
                        }

                        if (angular.isString(config.required)) {
                            attrs['ng-required'] = config.required;
                        } else {
                            attrs['ng-required'] = 'config.required';
                        }
                        attrs['ng-model'] = config.ui.args;
                        attrs.placeholder = '{{config.ui.placeholder}}';

                        if (!angular.isArray(config.ui.writable)) {
                            attrs['ng-disabled'] = '!' + config.ui.writable;
                            config.ui.writableCompiled = config.ui.writable;
                        } else {
                            writableCompiled = config.ui.model + '.ui.rule.field' + $.map(config.ui.writable,
                                function (item) {
                                    return "['" + helpers.addslashes(item) + "']";
                                }).join('') + '.writable';

                            attrs['ng-disabled'] = '!' + writableCompiled;

                            config.ui.writableCompiled = writableCompiled;
                        }

                        return attrs;
                    },
                    extra_attrs: function (config) {
                        return config.ui.attrs;
                    },
                    label: function (config) {
                        var use = '{{config.ui.label}}';
                        if (config.ui.label === undefined) {
                            use = '{{config.ui.autoLabel|inflector:humanize}}';
                        }
                        return use;
                    }
                };

            return {
                restrict: 'A',
                require: '^form',
                scope: true,
                transclude: true,
                link: function (scope, element, attrs, ctrl) {

                    var run = function () {

                        var supplied_config = scope.$eval(attrs.formInput),
                            name,
                            label = null,
                            config,
                            tpl,
                            template,
                            info,
                            constructor;

                        if (!angular.isObject(supplied_config)) {
                            console.warn('Config provided is not object for element: ', element);
                            return;
                        }

                        name = supplied_config.code_name;

                        // use backend defined label if was provided, otherwise the label will be humanized
                        if (supplied_config.verbose_name !== null && supplied_config.verbose_name !== undefined) {
                            label = supplied_config.verbose_name;
                        } else {
                            label = name;
                        }

                        if (!name) {
                            console.error('Your field config', supplied_config, 'has no name defined defined. element: ', element);
                            return;
                        }

                        config = {
                            ui: { // root config for entire config, upper structure is ndb property definition
                                args: 'args.' + name,
                                parentArgs: 'args',
                                rootScope: 'rootScope', // pointer to rootScope that should be considered
                                model: 'entity',
                                autoLabel: label,
                                specifics: {}, // used for property specific configurations
                                systemName: name,
                                name: name,
                                form: {
                                    root: ctrl,
                                    field: function () {
                                        return this.root[config.ui.name];
                                    },
                                    hasErrors: function () {
                                        return Object.keys(this.field().$error).length;
                                    },
                                    messages: function () {
                                        return ((this.field().$dirty && this.hasErrors()) ? this.field().$error : false) || config.ui;
                                    },
                                    shouldShowMessages: function () {
                                        if (!this.field()) {
                                            return false;
                                        }
                                        return this.field().$dirty || config.ui.help;
                                    }
                                },
                                writable: [name],
                                path: undefined,
                                realPath: undefined,
                                attrs: {}
                            }
                        };

                        helpers.mergeDeep(supplied_config, config);
                        config = supplied_config;

                        if (angular.isFunction(config.ui.init)) {
                            constructor = config.ui.init;
                            config.ui.init = undefined;
                        }

                        if (!config.ui.init) {
                            config.ui.init = {
                                callbacks: [],
                                add: function (name, callback) {
                                    var theObj = null;
                                    angular.forEach(this.callbacks, function (obj, i) {
                                        if (angular.isDefined(obj[name])) {
                                            theObj = obj;
                                        }
                                    });
                                    if (theObj !== null) {
                                        theObj[name] = callback;
                                    } else {
                                        theObj = {};
                                        theObj[name] = callback;
                                        this.callbacks.push(theObj);
                                    }
                                }
                            };
                        }

                        if (constructor) {
                            config.ui.init.add('init', constructor);
                        }

                        if (!angular.isDefined(config.ui.path)) {
                            config.ui.path = [name];
                        }

                        if (angular.isArray(config.ui.writable)) {
                            config.ui.writable = angular.copy(config.ui.path);
                        }

                        if (!angular.isDefined(config.ui.realPath)) {
                            config.ui.realPath = [name];
                        }

                        if (types[config.type] !== undefined) {
                            // reference main locals to type builder
                            info = {
                                config: config,
                                element: element,
                                scope: scope,
                                attrs: attrs
                            };
                            tpl = types[config.type](info);

                            // compiled variables for the template
                            config.ui.compiled = {
                                attrs: utils.attrs(config),
                                label: utils.label(config)
                            };
                            angular.forEach(config.ui.init.callbacks, function (obj) {
                                angular.forEach(obj, function (callback) {
                                    callback(info);
                                });
                            });

                            if (config.ui.render === false) {
                                return;
                            }

                            template = underscoreTemplate.get(angular.isDefined(config.ui.template) ? config.ui.template : 'core/fields/' + tpl + '.html')({
                                config: config
                            });

                            scope.config = config;
                            element.html(template);
                            $compile(element.contents())(scope);

                        } else {
                            console.warn('Field type: ' + config.type +
                                ' is not supported.');
                        }

                    };

                    run();

                }

            };
        }).directive('compatibilityMaker', function (modelsUtil) {
            return {
                restrict: 'A',
                link: function (scope, element, attrs, ctrl) {
                    var fn = function () {
                        var newval = scope.$eval(attrs.compatibilityMaker),
                            stringified = modelsUtil.argumentsToJson(newval);
                        element.val(stringified);
                    };
                    scope.$watch(attrs.compatibilityMaker, fn);
                    scope.$on('ngUploadSubmit', fn);

                }
            };
        }).directive('submitIfFiles', function ($parse) {
            return {
                require: '^form',
                link: function (scope, element, attrs, ctrl) {
                    var form = element.parents('form:first'),
                        files,
                        submit = $parse(attrs.submitIfFiles),
                        complete = $parse(attrs.submitIfFilesNoComplete),
                        check = $parse(attrs.submitIf),
                        nativeSubmit = $parse(attrs.submitNative),
                        execute,
                        click = function () {
                            if (check && !check(scope)) {
                                return false;
                            }
                            var promise,
                                isNative = nativeSubmit(scope);
                            files = form.find('input[type="file"]');
                            execute = false;
                            if (files.length) {
                                files.each(function () {
                                    if ($(this).val()) {
                                        execute = true;
                                        return false;
                                    }
                                });
                            }
                            if (isNative) {
                                if (execute) {
                                    form.trigger('submit');
                                    return false;
                                }
                                promise = submit(scope);
                            } else {
                                promise = submit(scope);
                            }
                            if (promise && angular.isObject(promise) && promise.then) {
                                promise.then(function () {
                                    if (execute) {
                                        form.trigger('submit');
                                        return false;
                                    }
                                    complete(scope);
                                });
                            }

                            scope.$apply();
                        };

                    element.on('click', click);
                    scope.$on('$destroy', function () {
                        element.off('click', click);
                    });

                }
            };
        }).directive('submitIfValid', function ($parse) {
            return {
                require: '^form',
                link: function (scope, element, attrs, ctrl) {
                    var form = element.parents('form:first'),
                        check = $parse(attrs.submitIfValid),
                        click = function (e) {
                            if (check(scope)) {
                                form.submit();
                            }
                            return e.preventDefault();
                        };

                    element.on('click', click);
                    scope.$on('$destroy', function () {
                        element.off('click', click);
                    });

                }
            };
        }).directive('showNumberOfSelectedFiles', function () {
            return {
                restrict: 'A',
                link: function (scope, element, attrs) {
                    var root = element.parents('.fake-button:first'),
                        target = root.find(attrs.showNumberOfSelectedFiles),
                        totalText = target.text(),
                        change = function () {
                            setTimeout(function () {
                                var files = element.prop('files');
                                if (files && files.length) {
                                    target.css('display', 'inline');
                                    target.text(totalText.replace(':total', files.length));
                                } else {
                                    target.hide();
                                }
                            }, 200);

                        };
                    element.bind('change', change);
                    change();
                    scope.$on('ngUploadComplete', change);
                    scope.$on('ngUploadCompleteError', change);
                    scope.$on('$destroy', function () {
                        element.unbind('change', change);
                    });
                }
            };
        }).directive('checkNumeric', function () {
            return {
                require: ['ngModel', '^form'],
                link: function (scope, element, attrs, ctrls) {
                    var checkNumeric = function (value) {
                            var valid = !isNaN(parseInt(value, 10));
                            if (!valid) {
                                valid = !isNaN(parseFloat(value, 10));
                            }
                            return valid;
                        },
                        required = element.attr('required') === 'required';
                    ctrls[0].$parsers.unshift(function (value) {
                        var valid = checkNumeric(value),
                            out;
                        if (!required && (!valid || angular.isUndefined(value) || !value.length || !value.replace(/[^0-9+.]/g, ''))) {
                            valid = true;
                        }
                        ctrls[0].$setValidity('checkNumeric', valid);
                        // if it's valid, return the value to the model, 
                        // otherwise return undefined.
                        if (angular.isDefined(value)) {
                            out = value.replace(/[^0-9+.]/g, '');
                            if (out !== value) {
                                ctrls[0].$setViewValue(out);
                                ctrls[0].$render();
                            }
                            return out;
                        }

                        return valid ? value : undefined;
                    });
                }
            };
        }).factory('formInputTypes', function (underscoreTemplate, $timeout, $parse,
            endpoint, modelsMeta, models, $q, $filter, $modal, helpers,
            errorHandling, modals) {

            var inflector = $filter('inflector'),
                formInputTypes = {
                    _SelectBox: function (info) {

                        if (!angular.isDefined(info.config.ui.specifics.repeatAs)) {
                            info.config.ui.specifics.repeatAs = '';
                        }

                        if (!angular.isDefined(info.config.ui.specifics.searchEnabled)) {
                            if (info.config.choices.length < 10) {
                                info.config.ui.specifics.searchEnabled = false;
                            } else {
                                info.config.ui.specifics.searchEnabled = true;
                            }
                        }

                        return 'select';
                    },
                    SuperStringProperty: function (info) {
                        var config = info.config;
                        if (config.ui.attrs.type === undefined) {
                            config.ui.attrs.type = 'text';
                        }

                        if (config.choices) {
                            return this._SelectBox(info);
                        }

                        if (info.config.repeated) {
                            info.config.ui.attrs['repeated-text'] = '';
                            return 'text';
                        }

                        return 'string';
                    },
                    SuperFloatProperty: function (info) {
                        var config = info.config;

                        if (config.choices) {
                            return this._SelectBox(info);
                        }
                        config.ui.attrs['check-numeric'] = '';
                        return this.SuperStringProperty(info);
                    },
                    SuperIntegerProperty: function (info) {
                        var config = info.config;

                        if (config.choices) {
                            return this._SelectBox(info);
                        }

                        config.ui.attrs['check-numeric'] = '';

                        return this.SuperFloatProperty(info);
                    },
                    SuperDecimalProperty: function (info) {
                        var config = info.config;
                        if (config.choices) {
                            return this._SelectBox(info);
                        }
                        config.ui.attrs['check-numeric'] = '';
                        return this.SuperFloatProperty(info);
                    },
                    SuperBooleanProperty: function (info) {
                        info.config.required = false;
                        if (!info.config.ui.specifics || angular.isUndefined(info.config.ui.specifics.type)) {
                            info.config.ui.specifics.type = 'switch';
                        }
                        return 'boolean';
                    },
                    SuperVirtualKeyProperty: function (info) {
                        return this.SuperKeyProperty(info);
                    },
                    SuperKeyProperty: function (info) {
                        if (info.config.searchable === false) {
                            return this.SuperStringProperty(info);
                        }
                        var config = info.config,
                            defaults = {
                                cache: {
                                    query: {
                                        '24': true,
                                        '12': true,
                                        '13': true,
                                        '17': true
                                    },
                                    type: {
                                        '12': 'local',
                                        '17': 'local',
                                        'default': 'memory'
                                    }
                                },
                                finder: {
                                    '24': true
                                },
                                view: {
                                    'default': function (result) {
                                        if (!result) {
                                            return '';
                                        }
                                        return result.name;
                                    }
                                },
                                init: {
                                    '13': function (info) {
                                        info.scope.$watch(info.config.ui.parentArgs +
                                            '.country',
                                            function (neww, old) {
                                                if (neww !== old) {
                                                    var args = info.scope.$eval(info.config.ui.parentArgs);
                                                    args.region = null;
                                                    config.ui.specifics.initial(); // refresh results
                                                }
                                            });
                                    }
                                },
                                queryFilter: {
                                    '24': function (term, searchArguments) {
                                        var searchDefaults = angular.copy(searchArguments.search['default']),
                                            args = {
                                                search: searchDefaults
                                            };
                                        if (term) {
                                            args.search.filters.push({
                                                field: 'name',
                                                operator: '==',
                                                value: term
                                            });
                                        }
                                        return args;
                                    },
                                    '17': function (term, searchArguments) {
                                        var searchDefaults = {
                                                search: {
                                                    filters: [{
                                                        value: true,
                                                        field: 'active',
                                                        operator: '=='
                                                    }],
                                                    orders: [{
                                                        field: 'name',
                                                        operator: 'asc'
                                                    }],
                                                }
                                            },
                                            argument = searchDefaults.search;

                                        if (config.code_name === 'weight_uom') {
                                            argument.filters.push({
                                                value: 'Weight',
                                                field: 'measurement',
                                                operator: '=='
                                            });
                                        }

                                        if (config.code_name === 'volume_uom') {
                                            argument.filters.push({
                                                value: 'Volume',
                                                field: 'measurement',
                                                operator: '=='
                                            });
                                        }

                                        if (config.code_name === 'product_uom') {
                                            argument.filters.unshift({
                                                value: 'Currency',
                                                field: 'measurement',
                                                operator: '!='
                                            });

                                            argument.orders = [{
                                                field: 'measurement',
                                                operator: 'asc'
                                            }, {
                                                field: 'key',
                                                operator: 'asc'
                                            }];
                                        }

                                        return searchDefaults;

                                    },
                                    '13': function (term, searchArguments) {
                                        var args = info.scope.$eval(info.config.ui.parentArgs);
                                        if ((args && args.country)) {
                                            return {
                                                search: {
                                                    ancestor: args.country,
                                                    filters: [{
                                                        value: true,
                                                        field: 'active',
                                                        operator: '=='
                                                    }],
                                                    orders: [{
                                                        field: 'name',
                                                        operator: 'asc'
                                                    }],
                                                }
                                            };
                                        }
                                        return false;
                                    }
                                }
                            },
                            init,
                            model = models[config.kind],
                            search = {},
                            args,
                            opts = {},
                            override = config.ui.specifics.override || {},
                            actionArguments = (config.kind ? modelsMeta.getActionArguments(config.kind, 'search') : {}),
                            response = function (response) {
                                config.ui.specifics.entities = response.data.entities;
                                return config.ui.specifics.entities;
                            },
                            findArgs,
                            finder,
                            initialDefer = $q.defer(),
                            initialPromise = initialDefer.promise;
                        config.ui.specifics.view = function (result) {
                            var fn = defaults.view[config.kind];
                            if (!fn) {
                                fn = defaults.view['default'];
                            }
                            if (override.view) {
                                fn = override.view;
                            }
                            return fn(result);
                        };
                        init = defaults.init[config.kind];
                        if (override.init) {
                            init = override.init;
                        }
                        if (angular.isDefined(init)) {
                            init(info);
                        }
                        $.extend(search, config.ui.specifics.search);
                        config.ui.specifics.search = search;

                        if (angular.isFunction(config.ui.specifics.entities)) {
                            config.ui.specifics.getEntities = config.ui.specifics.entities;
                            config.ui.specifics.entities = config.ui.specifics.entities();
                        }

                        if (angular.isUndefined(config.ui.specifics.entities)) {
                            config.ui.specifics.entities = [];
                        }

                        finder = defaults.finder[config.kind];
                        if (override.finder) {
                            finder = override.finder;
                        }

                        config.ui.specifics.search.ready = initialPromise;

                        if (model && !config.ui.specifics.getEntities) {
                            if (model.actions.search) {
                                opts.cache = defaults.cache.query[config.kind];
                                opts.cacheType = defaults.cache.type[config.kind] || defaults.cache.type['default'];
                                if (override.cache && angular.isDefined(override.cache.query)) {
                                    opts.cache = override.cache.query;
                                }
                                if (override.cache && angular.isDefined(override.cache.type)) {
                                    opts.cacheType = override.cache.type;
                                }
                                config.ui.specifics.initial = function () {
                                    args = defaults.queryFilter[config.kind];
                                    if (override.queryFilter) {
                                        args = override.queryFilter;
                                    }
                                    if (!args) {
                                        args = actionArguments.search['default'];
                                    } else {
                                        findArgs = args;
                                        args = findArgs(null, actionArguments);
                                        if (finder) {
                                            config.ui.specifics.search.find = function (term) {
                                                return model.actions.search(findArgs(term, actionArguments), opts).then(function (response) {
                                                    var entities = response.data.entities;
                                                    angular.forEach(entities, function (ent) {
                                                        if (!_.findWhere(config.ui.specifics.entities, {
                                                                key: ent.key
                                                            })) { // this is pretty slow. however can be sped up with key-value monitoring
                                                            config.ui.specifics.entities.push(ent);
                                                        }
                                                    });
                                                });
                                            };
                                        }
                                        config.ui.specifics.search.missing = function (id) {
                                            if (id === null || id === undefined || !id.length) {
                                                return;
                                            }
                                            var selectedIsArray = angular.isArray(id);
                                            model.actions.search({
                                                search: {
                                                    keys: (selectedIsArray ? id : [id])
                                                }
                                            }, {
                                                cache: true
                                            }).then(function (response) {
                                                var fetchedEntities = response.data.entities;
                                                if (!selectedIsArray) {
                                                    if (!_.findWhere(config.ui.specifics.entities, {
                                                            key: id
                                                        })) { // slow
                                                        config.ui.specifics.entities.unshift(response.data.entities[0]);
                                                    }
                                                } else {
                                                    angular.forEach(fetchedEntities, function (ent) {
                                                        if (!_.findWhere(config.ui.specifics.entities, {
                                                                key: ent.key
                                                            })) { // slow
                                                            config.ui.specifics.entities.push(ent);
                                                        }
                                                    });
                                                }
                                            });
                                        };
                                    }
                                    return model.actions.search(args, opts).then(response);
                                };
                                config.ui.specifics.initial().then(function () {
                                    initialDefer.resolve();
                                });
                            }
                        }
                        return 'select_async';
                    },
                    SuperLocalStructuredProperty: function (info) {
                        var config = info.config,
                            fields = [],
                            newFields = [],
                            modelFields = config.modelclass,
                            defaultFields = _.toArray(modelFields),
                            noSpecifics = !angular.isDefined(config.ui.specifics),
                            newSort = [],
                            defaults,
                            defaultSortable,
                            buildPaths,
                            rootArgs,
                            rootFormSetDirty = helpers.callable(info.scope.formSetDirty),
                            list = {
                                secondary: true,
                                perLine: 2,
                                clickable: true
                            };

                        config.ui.specifics.sortMode = true;

                        defaultFields = defaultFields.sort(helpers.fieldSorter);

                        if (noSpecifics || !config.ui.specifics.fields) {
                            config.ui.specifics.fields = defaultFields;
                            if (config.ui.specifics.sortFields) {
                                angular.forEach(config.ui.specifics.sortFields, function (key) {
                                    newSort.push(_.findWhere(config.ui.specifics.fields, {
                                        code_name: key
                                    }));
                                });

                                config.ui.specifics.fields = newSort;
                            }
                        }

                        if (!noSpecifics && config.ui.specifics.excludeFields) {
                            angular.forEach(config.ui.specifics.fields, function (field, i) {
                                if ($.inArray(field.code_name, config.ui.specifics.excludeFields) === -1) {
                                    newFields.push(field);
                                }
                            });
                            config.ui.specifics.fields = newFields;
                        }

                        defaults = {
                            fields: fields,
                            addNewText: 'Add',
                            addText: '{{config.ui.specifics.addNewText}}'
                        };

                        if (config.ui.specifics.listConfig) {
                            $.extend(list, config.ui.specifics.listConfig);
                        }

                        config.ui.specifics.listConfig = list;

                        // merge defaults into the
                        angular.forEach(defaults, function (value, key) {
                            if (config.ui.specifics[key] === undefined) {
                                config.ui.specifics[key] = value;
                            }
                        });

                        config.ui.specifics.parentArgs = info.scope.$eval(config.ui.args);
                        config.ui.specifics.entity = info.scope.$eval(config.ui.model);
                        config.ui.specifics.rootScope = info.scope.$eval(config.ui.rootScope);

                        if (!config.ui.specifics.sortableOptions) {
                            config.ui.specifics.sortableOptions = {};
                        }

                        defaultSortable = {
                            disabled: false,
                            start: function (e, ui) {
                                info.scope.$broadcast('itemOrderStarted');
                            },
                            axis: false,
                            containment: false,
                            whatSortMeans: modals.howToSort,
                            handle: '.sort-handle',
                            tolerance: 'pointer',
                            helper: 'clone',
                            sort: function (e, ui) {
                                var deleteMode,
                                    division,
                                    helperWidth = ui.helper.width(),
                                    itemScope = ui.item.scope(),
                                    item = itemScope.$eval(ui.item.attr('current-item'));
                                division = ui.offset.left + helperWidth;
                                if (division < (helperWidth / 1.5)) {
                                    deleteMode = true;
                                }
                                if (item) {
                                    if (deleteMode) {
                                        ui.helper.addClass('about-to-delete');
                                        item._state = 'deleted';
                                    } else {
                                        ui.helper.removeClass('about-to-delete');
                                        item._state = null;
                                    }
                                }
                                info.scope.$broadcast('itemOrderSorting');
                            },
                            stop: function (e, ui) {
                                angular.forEach(config.ui.specifics.parentArgs,
                                    function (ent, i) {
                                        i = ((config.ui.specifics.parentArgs.length - 1) - i);
                                        ent._sequence = i;
                                        ent.ui.access[ent.ui.access.length - 1] = i;
                                    });
                                rootFormSetDirty();
                                info.scope.$broadcast('itemOrderChanged');
                                info.scope.$apply();
                            }
                        };
                        // add default sorting config
                        $.extend(defaultSortable, config.ui.specifics.sortableOptions);
                        config.ui.specifics.sortableOptions = defaultSortable;
                        // disables sorting if the field is not writable
                        // writableCompiled is as-is specification
                        config.ui.init.add('checkDisabledStateForSortable', function () {
                            var fieldIsWritable = $parse(config.ui.writableCompiled);
                            config.ui.specifics.sortableOptions.disabled = !fieldIsWritable(info.scope);
                        });
                        // watches list of arguments args != new
                        info.scope.$watch(config.ui.args, function (neww, old) {
                            if (neww !== old) {
                                config.ui.specifics.parentArgs = neww;
                            }
                        });

                        buildPaths = function () {
                            // builds form fields
                            // it appends needed paths depending on hierarchy depth
                            config.ui.specifics.formBuilder = [];
                            angular.forEach(config.ui.specifics.fields, function (field) {
                                var copyWritable = angular.copy(config.ui.writable);

                                if (angular.isArray(copyWritable)) {
                                    copyWritable.push((field.ui.writableName ? field.ui.writableName : field.code_name));
                                }

                                field.ui.path = [];
                                field.ui.path.extend(config.ui.path);
                                field.ui.path.push(field.code_name);
                                field.ui.realPath = [];
                                field.ui.realPath.extend(config.ui.realPath);
                                field.ui.realPath.push(field.code_name);
                                if (!angular.isDefined(field.ui.name)) {
                                    field.ui.name = config.ui.name + '.' + field.code_name;
                                }
                                field.ui.writable = copyWritable;
                                config.ui.specifics.formBuilder.push(field);
                            });
                        };

                        buildPaths();

                        if (config.ui.specifics.remote) {
                            // construct reference to root arguments
                            rootArgs = (config.ui.specifics.getRootArgs ? config.ui.specifics.getRootArgs() : config.ui.specifics.rootScope.args);
                            // assign "load more" logic
                            config.ui.specifics.reader = models[rootArgs.action_model].reader({
                                kind: rootArgs.action_model,
                                key: rootArgs.key,
                                next: rootArgs._next_read_arguments,
                                access: config.ui.realPath,
                                complete: function (items) {
                                    config.ui.specifics.parentArgs.extend(items);
                                }
                            });
                            // apply direct reader settings if any
                            if (angular.isDefined(config.ui.specifics.readerSettings)) {
                                config.ui.specifics.reader.state(config.ui.specifics.readerSettings);
                            }
                        }

                        if (!config.repeated && config.ui.specifics.modal !== true) {

                            config.ui.specifics.SingularCtrl = function ($scope) {
                                $scope.args = config.ui.specifics.parentArgs;
                                info.scope.$watchCollection(config.ui.args, function (neww, old) {
                                    $.extend($scope.args, neww);
                                });
                                config.ui.specifics.getScope = function () {
                                    return $scope;
                                };
                                $scope.$on('$destroy', function () {
                                    config.ui.specifics.getScope = undefined;
                                });
                            };

                        } else {

                            config.ui.specifics.remove = function (arg) {
                                arg._state = 'deleted';
                                info.scope.$emit('itemDelete', arg); // @todo handle this
                                info.scope.$broadcast('itemDelete', arg); // @todo handle this
                                rootFormSetDirty();
                            };

                            // generic manage dialog that handles editing of remote and local structured properties
                            config.ui.specifics.manage = function (arg, defaultArgs) {

                                buildPaths(); // force path rebuild

                                $modal.open({
                                    template: underscoreTemplate.get(config.ui.specifics.templateUrl ? config.ui.specifics.templateUrl : 'core/fields/manage_structured.html')({
                                        config: config
                                    }),
                                    controller: function ($scope, modelsUtil) {
                                        var isNew = false,
                                            length = (config.ui.specifics.modal ? 0 : config.ui.specifics.parentArgs.length),
                                            formBuilder = {
                                                '0': []
                                            },
                                            getResult = function (response, access) {
                                                var accessPath = [],
                                                    value,
                                                    isNewAndRepeated = (isNew && config.repeated);
                                                angular.forEach(access, function (path, i) {
                                                    var parse = parseInt(path, 10);
                                                    if (!isNaN(parse)) {
                                                        path = 0;
                                                    }
                                                    accessPath.push(path);
                                                });
                                                if (isNewAndRepeated) {
                                                    accessPath.pop();
                                                }
                                                value = helpers.getProperty(response.data.entity, accessPath);
                                                if (isNewAndRepeated && value.length) {
                                                    value = _.findWhere({
                                                        _state: 'created'
                                                    });
                                                }

                                                return value;
                                            };

                                        config.ui.specifics.getScope = function () {
                                            return $scope;
                                        };

                                        $scope.rootFormSetDirty = rootFormSetDirty;
                                        $scope.formSetDirty = function () {
                                            if ($scope.container && $scope.container.form) {
                                                return $scope.container.form.$setDirty();
                                            }
                                        };
                                        $scope.formSetPristine = function () {
                                            if ($scope.container && $scope.container.form) {
                                                return $scope.container.form.$setPristine();
                                            }
                                        };

                                        $scope.response = null;
                                        $scope.config = config;
                                        if (!arg) {
                                            arg = {
                                                kind: config.modelclass_kind,
                                                _sequence: length
                                            };
                                            modelsUtil.normalize(arg, config.modelclass,
                                                config.ui.specifics.entity, config.code_name,
                                                length);
                                            if (angular.isDefined(defaultArgs)) {
                                                $.extend(arg, defaultArgs);
                                            }
                                            isNew = true;
                                        } else if (!config.ui.specifics.modal && arg.ui) {
                                            length = _.last(arg.ui.access);
                                        }

                                        if (angular.isDefined(arg.ui)) {
                                            arg.ui.access = angular.copy(config.ui.realPath);
                                            if (!config.ui.specifics.modal) {
                                                arg.ui.access.push(length);
                                            }
                                        }

                                        $scope.accordions = {
                                            closeOthers: true,
                                            groups: [{
                                                label: 'General',
                                                disabled: true,
                                                open: true
                                            }]
                                        };

                                        $scope.formBuilder = formBuilder;
                                        $scope.container = {
                                            action: endpoint.url
                                        };
                                        $scope.args = angular.copy(arg);
                                        $scope.parentArgs = config.ui.specifics.parentArgs;
                                        $scope.rootScope = config.ui.specifics.rootScope;
                                        $scope.entity = config.ui.specifics.entity;
                                        $scope.close = function () {
                                            $scope.$close();
                                            if (config.ui.specifics.afterClose) {
                                                config.ui.specifics.afterClose($scope);
                                            }
                                        };
                                        $scope.validateForm = function () {
                                            if (!$scope.container.form.$valid) {
                                                $scope.$broadcast('invalidForm');
                                                return false;
                                            }

                                            return true;
                                        };

                                        $scope.$on('$destroy', function () {
                                            config.ui.specifics.getScope = undefined;
                                        });
                                        angular.forEach(config.ui.specifics.formBuilder, function (field) {
                                            //field = angular.copy(field); // why copy?
                                            // @todo if we do not copy the field, then the field specific options will not be included in
                                            // config tree
                                            // this problem is presented in buyer settings when trying to select country and region combo
                                            // the callbacks from previous dialog get referenced into the fields
                                            if (!field.ui.initialRealPath) {
                                                field.ui.initialRealPath = angular.copy(field.ui.realPath);
                                            } else {
                                                field.ui.realPath = angular.copy(field.ui.initialRealPath);
                                            }
                                            field.ui.realPath.pop();
                                            if (!config.ui.specifics.modal) {
                                                field.ui.realPath.push(length);
                                            }
                                            field.ui.realPath.push(field.code_name);
                                            if (field.is_structured && formInputTypes[field.type]) {
                                                $scope.accordions.groups.push({
                                                    label: inflector((field.ui.label || field.code_name), 'humanize'),
                                                    disabled: false,
                                                    key: field.code_name,
                                                    open: false
                                                });

                                                field.ui.label = false;

                                                var next = $scope.accordions.groups.length - 1;

                                                if (!angular.isDefined(formBuilder[next])) {
                                                    formBuilder[next] = [];
                                                    formBuilder[next].push(field);
                                                }
                                                $scope.accordions.groups[0].disabled = false;
                                            } else {
                                                formBuilder['0'].push(field);
                                            }
                                        });

                                        if (config.ui.specifics.remote) {

                                            // reference to args that get sent
                                            $scope.rootArgs = rootArgs;
                                            $scope.setAction = function (action) {
                                                // internal helper to set the action to be executed
                                                $scope.sendRootArgs.action_id = action;
                                            };
                                            // copy of root args used for packing the customized arguments
                                            $scope.sendRootArgs = {};
                                            $scope.save = function () {
                                                if (!$scope.validateForm()) { // check if the form is valid
                                                    return false;
                                                }
                                                $scope.rootFormSetDirty();
                                                var promise,
                                                    prepare = function () {
                                                        var readArgs = {},
                                                            readRootArgs = $scope.rootArgs,
                                                            readRootArgsAsList,
                                                            parentArgsPath = $scope.args.ui.access,
                                                            fieldList,
                                                            traceDeep;
                                                        // set this args as single item in array
                                                        // delete all remote structured property from rpc data
                                                        readRootArgs = angular.copy(readRootArgs);
                                                        helpers.setProperty(readRootArgs, parentArgsPath, $scope.args);
                                                        $scope.sendRootArgs = readRootArgs;
                                                        angular.forEach($scope.rootScope.config.fields, function (field) {
                                                            if (_.string.contains(field.type, 'RemoteStructured') && field.code_name !== $scope.args.ui.access[0]) {
                                                                delete readRootArgs[field.code_name];
                                                            }
                                                        });
                                                        readRootArgs.read_arguments = readArgs;
                                                        angular.forEach(parentArgsPath, function (part, i) {
                                                            // parseInt can produce inconsistent stuff like 10_foo makes 10, so we must avoid names of
                                                            // properties in datastore that begin with an number, which we do not
                                                            if (!angular.isDefined(readArgs[part]) && isNaN(parseInt(part, 10))) {
                                                                readArgs[part] = {
                                                                    config: {}
                                                                };
                                                                readArgs = readArgs[part];
                                                            }
                                                            // produce read path for the rpc
                                                            readRootArgs = readRootArgs[part];
                                                            if (angular.isArray(readRootArgs)) {
                                                                readRootArgsAsList = readRootArgs;
                                                            } else {
                                                                if (readRootArgs.key !== null && angular.isDefined(readRootArgs.key)) {
                                                                    if (!angular.isDefined(readArgs.config.keys)) {
                                                                        readArgs.config.keys = [];
                                                                    }
                                                                    readArgs.config.keys.push(readRootArgs.key);
                                                                    if (angular.isDefined(readRootArgsAsList)) {
                                                                        readRootArgsAsList.splice(0, readRootArgsAsList.length); // empty the list
                                                                        readRootArgsAsList.push(readRootArgs);
                                                                        readRootArgsAsList = undefined;
                                                                    }
                                                                }
                                                            }
                                                        });

                                                        traceDeep = function (readRootArgs, readArgs) {
                                                            if (readRootArgs && readRootArgs.key) {
                                                                fieldList = modelsMeta.getFields(readRootArgs.kind);
                                                                angular.forEach(fieldList, function (field) {
                                                                    if (field.is_structured && _.string.contains(field.type, 'RemoteStructured')) {
                                                                        var keys = [],
                                                                            newReadArgs = {
                                                                                config: {
                                                                                    keys: keys
                                                                                }
                                                                            };
                                                                        if (field.repeated) {
                                                                            angular.forEach(readRootArgs[field.code_name], function (ent) {
                                                                                if (ent.key) {
                                                                                    keys.push(ent.key);
                                                                                    traceDeep(ent, newReadArgs);
                                                                                }
                                                                            });
                                                                        }
                                                                        readArgs[field.code_name] = newReadArgs;
                                                                    }
                                                                });
                                                            } else if (angular.isArray(readRootArgs)) {
                                                                angular.forEach(readRootArgs, function (readRootArg) {
                                                                    traceDeep(readRootArg, readArgs);
                                                                });
                                                            }
                                                        };

                                                        traceDeep(readRootArgs, readArgs);
                                                    };

                                                prepare();
                                                if (config.ui.specifics.beforeSave) {
                                                    config.ui.specifics.beforeSave($scope);
                                                }
                                                // create rpc from root args's action model and action id
                                                promise = models[$scope.sendRootArgs.action_model].actions[$scope.sendRootArgs.action_id]($scope.sendRootArgs);
                                                promise.then(function (response) {
                                                    $scope.response = response;
                                                    var keepAccess = angular.copy($scope.args.ui.access),
                                                        // set zero-in access path, example _images.0.pricetags.0._products.0._instances.0
                                                        value = getResult(response, keepAccess);
                                                    $.extend($scope.args, value); // modify current args
                                                    $scope.args.ui.access = keepAccess; // reference back original access path
                                                    if (isNew) {
                                                        if (config.repeated) {
                                                            $scope.parentArgs.unshift($scope.args); // preappend arg if they are new
                                                        }
                                                        isNew = false;
                                                    }
                                                    $.extend(arg, $scope.args); // modify provided args, usually come from the parent's scope
                                                    // re-run prepare to ensure proper paths for complete hook
                                                    prepare();
                                                    if (angular.isDefined(config.ui.specifics.afterSave)) {
                                                        config.ui.specifics.afterSave($scope);
                                                    }
                                                    $scope.formSetPristine();

                                                }, function (response) {
                                                    // here handle error...
                                                    if (angular.isDefined(config.ui.specifics.afterSaveError)) {
                                                        config.ui.specifics.afterSaveError($scope, response);
                                                    }
                                                });

                                                return promise;
                                            };

                                            $scope.complete = function (response) {
                                                $scope.response = response;
                                                var keepAccess = angular.copy($scope.args.ui.access),
                                                    value = getResult(response, keepAccess);
                                                $.extend($scope.args, value);
                                                $scope.args.ui.access = keepAccess;
                                                if (angular.isDefined(config.ui.specifics.afterComplete)) {
                                                    config.ui.specifics.afterComplete($scope);
                                                }
                                                $scope.rootFormSetDirty();
                                                $scope.formSetPristine();
                                            };

                                            $scope.noComplete = function () {
                                                // fired when the scope.complete() does not get fired i.e. when no files were sent for upload
                                                if (angular.isDefined(config.ui.specifics.noComplete)) {
                                                    config.ui.specifics.noComplete($scope);
                                                }
                                                $scope.rootFormSetDirty();
                                                $scope.formSetPristine();
                                            };

                                            $scope.completeError = function (response) {
                                                // fired when it failed to send http-form-data rpc
                                                if (angular.isDefined(config.ui.specifics.afterCompleteError)) {
                                                    config.ui.specifics.afterCompleteError($scope, response);
                                                }
                                                $scope.rootFormSetDirty();
                                                $scope.formSetPristine();
                                            };


                                        } else {


                                            $scope.save = function () {
                                                if (!$scope.validateForm()) { // check if the form is valid
                                                    return false;
                                                }
                                                $scope.rootFormSetDirty();
                                                var promise = null,
                                                    complete = function () {
                                                        var completePromise = null,
                                                            total = 0;

                                                        if (config.repeated) {
                                                            if (isNew) {
                                                                $scope.parentArgs.unshift($scope.args);
                                                                isNew = false;
                                                                total = $scope.parentArgs.length - 1;
                                                                angular.forEach($scope.parentArgs, function (item, i) {
                                                                    i = total - i;
                                                                    item._sequence = i;
                                                                    item.sequence = i;
                                                                });
                                                            } else {
                                                                $.extend(arg, $scope.args);
                                                            }
                                                        }

                                                        if (angular.isFunction(config.ui.specifics.afterSave)) {
                                                            completePromise = config.ui.specifics.afterSave($scope, info);
                                                        }

                                                        if (completePromise && completePromise.then) {
                                                            completePromise.then(function () {
                                                                $scope.formSetPristine();
                                                                if (config.closeAfterSave) {
                                                                    $scope.close();
                                                                }
                                                            });
                                                        } else {
                                                            $scope.formSetPristine();
                                                            if (config.closeAfterSave) {
                                                                $scope.close();
                                                            }
                                                        }

                                                    };

                                                if (angular.isFunction(config.ui.specifics.beforeSave)) {
                                                    promise = config.ui.specifics.beforeSave($scope, info);
                                                }

                                                if (promise && promise.then) {
                                                    promise.then(complete);

                                                } else {
                                                    complete();
                                                }

                                            };
                                        }

                                        // construct direct scope
                                        if (config.ui.specifics.scope) {
                                            $.extend($scope, config.ui.specifics.scope);
                                        }

                                        // call constructor
                                        if (angular.isFunction(config.ui.specifics.init)) {
                                            config.ui.specifics.init($scope);
                                        }

                                    }
                                });
                            };

                            config.ui.specifics.create = config.ui.specifics.manage;

                        }

                        return 'structured_' + (config.repeated ? 'repeated' : 'single');
                    },
                    _RemoteStructuredPropery: function (info) {
                        var config = info.config;
                        config.ui.specifics.remote = true;
                    },
                    SuperStructuredProperty: function (info) {
                        return this.SuperLocalStructuredProperty(info);
                    },
                    SuperRemoteStructuredProperty: function (info) {
                        this._RemoteStructuredPropery(info);
                        var ret = this.SuperLocalStructuredProperty(info);
                        return ret;
                    },
                    SuperImageLocalStructuredProperty: function (info) {
                        this.SuperLocalStructuredProperty(info);
                        if (!info.config.ui.specifics.displayImageConfig) {
                            info.config.ui.specifics.displayImageConfig = {
                                size: 360
                            };
                        }
                        if (!info.config.ui.specifics.sortableOptions) {
                            info.config.ui.specifics.sortableOptions = {};
                        }
                        $.extend(info.config.ui.specifics.sortableOptions, {
                            axis: false,
                            containment: false
                        });
                        return 'image';
                    },
                    SuperImageStructuredProperty: function (info) {
                        if (!info.config.ui.specifics.sortableOptions) {
                            info.config.ui.specifics.sortableOptions = {};
                        }
                        $.extend(info.config.ui.specifics.sortableOptions, {
                            axis: false,
                            containment: false
                        });
                        return this.SuperImageLocalStructuredProperty(info);
                    },
                    SuperImageRemoteStructuredProperty: function (info) {
                        this._RemoteStructuredPropery(info);
                        var ret = this.SuperImageLocalStructuredProperty(info);
                        return ret;
                    },
                    SuperTextProperty: function (info) {
                        if (info.config.repeated) {
                            info.config.ui.attrs['repeated-text'] = '';
                        }
                        return 'text';
                    },
                    SuperJsonProperty: function (info) {
                        info.config.ui.attrs['json-only'] = '';
                        return this.SuperTextProperty(info);
                    },
                    SuperDateTimeProperty: function (info) {
                        info.config.ui.attrs['time-date-picker-dialog'] = '';
                        return 'string';
                    }
                };

            return formInputTypes;

        });
}());
(function () {
    'use strict';
    angular.module('app').run(function (helpers) {
        helpers.grid = {
            calculate: function (canvas_width, max_width, min_width, margin) {
                /*
                velicina covera je uvek izmedju 240x360px i 180x270px
                padding sa svih strana covera je 1px
                preferirani broj covera u horizontali je 4 ili vise
                ako je ostatak ekrana izmedju 240px i 360px onda se opet preferira najveci cover
                sto se tice GAE blobstore-a najbolje je da se uvek radi fetch covera dimenzija 240x360 pa da se ostalo radi na client side.
                */
                var loop = max_width - min_width,
                    values = [],
                    i,
                    cover_width,
                    cover_count_raw,
                    cover_count,
                    cover_width_rounded,
                    sides;
                for (i = 0; i < loop; i++) {
                    cover_width = max_width - i;
                    cover_count_raw = canvas_width / cover_width;
                    cover_count = Math.floor(cover_count_raw);
                    cover_width = canvas_width / cover_count;
                    if (cover_width > max_width) {
                        cover_count = cover_count + 1;
                        cover_width = canvas_width / cover_count;
                        if (cover_width < min_width) {
                            cover_count = cover_count - 1;
                            cover_width = max_width;
                        }
                    }
                    cover_width_rounded = Math.floor(cover_width);
                    sides = Math.floor((canvas_width % (cover_width_rounded * cover_count)) / 2);
                    cover_width_rounded = cover_width_rounded - (margin * 2);
                    values = [cover_width_rounded, cover_count, sides, cover_width_rounded];
                    if (cover_count_raw > 4 || cover_count === 1) {
                        break;
                    }
                }
                return values;
            }
        };
        helpers.fancyGrid = {
            getHeight: function (images, width, margin) {
                margin = (margin * 2);
                width -= images.length * margin;
                var h = 0;
                angular.forEach(images, function (image) {
                    h += image.proportion;
                });
                return Math.floor(width / h);
            },
            setHeight: function (images, height) {

                angular.forEach(images, function (image) {
                    image.width = (height * image.proportion);
                    image.height = (height);
                });

            },
            resize: function (images, width) {
                this.setHeight(images, this.getHeight(images, width));
            },
            calculate: function (size, images, max_height, margin) {
                var n = 0,
                    providedImages = images,
                    i,
                    slice,
                    h; // reference entire array
                w: while (images.length > 0) {
                    for (i = 1; i < images.length + 1; ++i) {
                        slice = images.slice(0, i);
                        h = this.getHeight(slice, size, margin);
                        if (h < max_height) {
                            this.setHeight(slice, h);
                            n++;
                            images = images.slice(i);
                            continue w;
                        }
                    }
                    this.setHeight(slice, Math.min(max_height, h));
                    n++;
                    break;
                }
                return providedImages;
            }

        };
    }).directive('fancyGridGenerator', function (helpers, $timeout) {

        return {
            link: function (scope, element, attrs) {
                var resize = function () {
                    var originalCanvas = 0,
                        run = function (check) {
                            var canvas = element.outerWidth(true),
                                images = [],
                                margin = 1;
                            if (!canvas || (check && originalCanvas === canvas)) {
                                return; // do not measure if canvas is falsy or if the original canvas is the same as the current one
                            }
                            angular.forEach(scope.$eval(attrs.fancyGridGenerator), function (image) {
                                if (image._state !== 'deleted') {
                                    images.push(angular.copy(image));
                                }
                            });
                            helpers.fancyGrid.calculate(canvas, images, 240, margin);
                            element.find('.grid-item').filter(function () {
                                return $(this).css('display') !== 'none';
                            }).each(function (i) {
                                if (!angular.isDefined(images[i])) {
                                    return;
                                }
                                $(this).css({
                                    width: images[i].width,
                                    height: images[i].height
                                });
                                $(this).find('img').css({
                                    height: images[i].height
                                });
                            });
                        };
                    run();
                    setTimeout(function () {
                        run(true);
                    }, 50);
                };

                scope.$on('modalResize', resize);
                scope.$on('itemOrderChanged', resize);
                scope.$on('itemOrderSorting', resize);
                scope.$on('ngRepeatEnd', resize);
                scope.$on('accordionOpened', function () {
                    setTimeout(resize, 110);
                });
                scope.$on('itemDelete', function () {
                    $timeout(resize);
                });
                scope.$on(attrs.fancyGridGenerator + '.length', function () {
                    $timeout(resize);
                });

            }
        };
    }).directive('gridGenerator', function (GLOBAL_CONFIG, helpers, $timeout) {
        return {
            link: function (scope, element, attrs) {

                var config = scope.$eval(attrs.gridGenerator) || {},
                    margin = config.margin || 0,
                    maxWidth = config.maxWidth || GLOBAL_CONFIG.grid.maxWidth,
                    minWidth = config.minWidth || GLOBAL_CONFIG.grid.minWidth,
                    maxHeight = config.maxHeight || GLOBAL_CONFIG.grid.maxHeight,
                    fixedHeight = config.fixedHeight,
                    square = (angular.isDefined(config.square) ? config.square : true),
                    resize = function () {
                        element = $(element);
                        if (!element.length) {
                            return;
                        }
                        var wrapper = element,
                            canvasWidth = wrapper.outerWidth(true),
                            values;
                        if (canvasWidth) {
                            values = helpers.grid.calculate(canvasWidth,
                                maxWidth, minWidth, margin);

                            if (wrapper.css('paddingLeft') !== values[2] || wrapper.css('paddingRight') !== values[2]) {
                                wrapper.css({
                                    paddingRight: values[2],
                                    paddingLeft: values[2]
                                });
                            }

                            wrapper.find('.grid-item').filter(function () {
                                return $(this).css('display') !== 'none';
                            }).each(function () {
                                var box, newHeight = fixedHeight ? fixedHeight : helpers.newHeightByWidth(maxWidth, maxHeight, values[0]);
                                if (values[0] !== $(this).width() || $(this).height() !== newHeight) {
                                    box = $(this).width(values[0]);
                                    if (square) {
                                        box.height(values[0]);
                                    } else {
                                        $(this).height(newHeight);
                                    }
                                }

                            });

                        }
                    };

                $(window).bind('resize modal.close mainMenu.hide', resize);
                scope.$on('ngRepeatEnd', resize);
                scope.$on('accordionOpened', function () {
                    setTimeout(resize, 110);
                });
                scope.$on('itemDelete', resize);
                scope.$watch(attrs.gridGeneratorItems + '.length', resize);
                scope.$on('$destroy', function () {
                    $(window).off('resize modal.close mainMenu.hide', resize);
                });

            }
        };
    });
}());
(function () {
    'use strict';
    angular.module('app')
        .run(function (helpers) {
            $.extend(helpers, {
                closestLargestNumber: function (arr, closestTo) {

                    var closest = Math.max.apply(null, arr),
                        i = 0; //Get the highest number in arr in case it match nothing.

                    for (i = 0; i < arr.length; i++) { //Loop the array
                        if (arr[i] > closestTo && arr[i] < closest) {
                            closest = arr[i];
                        } //Check if it's higher than your number, but lower than your closest value
                    }
                    return closest; // return the value
                },
                newWidthByHeight: function (original_width, original_height, new_height) {
                    var ratio;
                    original_width = parseInt(original_width, 10);
                    original_height = parseInt(original_height, 10);
                    new_height = parseInt(new_height, 10);
                    ratio = new_height / original_height;
                    return (original_width * ratio);
                },
                newHeightByWidth: function (original_width, original_height, new_width) {
                    var ratio;
                    original_width = parseInt(original_width, 10);
                    original_height = parseInt(original_height, 10);
                    new_width = parseInt(new_width, 10);
                    ratio = new_width / original_width; // get ratio for scaling image
                    return (original_height * ratio);
                },
                url: {
                    abs: function (part) {
                        return window.location.protocol + '//' + window.location.host + '/' + part;
                    }
                }
            });
        })
        .directive('displayImage', function (GLOBAL_CONFIG) {
            return {
                scope: {
                    image: '=displayImage',
                    config: '=displayImageConfig'
                },
                link: function (scope, element, attrs) {

                    if (!scope.config) {
                        scope.config = {};
                    }

                    if (!angular.isDefined(scope.config.size)) {
                        scope.config.size = 240;
                    }

                    var fn = function (nv, ov) {
                        if (nv !== ov) {
                            var error = function () {
                                    var defaultImage = scope.config.defaultImage;
                                    if (!defaultImage) {
                                        defaultImage = 'defaultImage';
                                    }
                                    $(this).attr('src', GLOBAL_CONFIG[defaultImage]);

                                },
                                img = element;

                            if (scope.image && scope.image.serving_url) {
                                img.on('error', error)
                                    .attr('src', scope.image.serving_url + '=s' + scope.config.size);
                            } else {
                                error.call(img);
                            }
                        }
                    };

                    scope.$watch('image.serving_url', fn);

                    fn(true, false);

                }
            };
        }).directive('loading', function ($parse) {
            return {
                link: function (scope, element, attrs) {

                    if (angular.isDefined(attrs.loading)) {
                        scope.$watch(attrs.loading, function ngBooleanAttrWatchAction(value) {
                            if (value) {
                                element.attr('disabled', 'disabled');
                            } else {
                                element.removeAttr('disabled');
                            }
                        });
                    }

                    var disable = function (e) {
                            e.stopImmediatePropagation();
                            e.preventDefault();
                            return false;
                        },
                        disabledInitially = angular.isDefined(attrs.loading) ? $parse(attrs.loading) : function () {
                            return false;
                        };

                    scope.$on('disableUI', function ($event, neww) {

                        if (disabledInitially(scope)) {
                            return;
                        }
                        if (neww === true) {
                            element.attr('disabled', 'disabled');
                            element.on('click', disable);
                        } else {
                            element.removeAttr('disabled');
                            element.off('click', disable);
                        }

                    });
                }
            };
        }).directive('onNgRepeatEnd', function ($timeout) {
            return {
                restrict: 'A',
                link: function (scope, element, attr) {
                    if (scope.$last === true) {
                        scope.$evalAsync(function () {
                            scope.$emit('ngRepeatEnd');
                        });
                    }
                }
            };
        }).directive('defaultFieldDisplay', function ($compile) {
            return {
                scope: {
                    val: '=defaultFieldDisplay'
                },
                templateUrl: 'buyer/address_display.html',
                controller: function ($scope) {
                    $scope.notEmpty = function (val) {
                        return angular.isString(val) || angular.isNumber(val);
                    };

                }
            };
        }).directive('draggableClick', function ($parse, helpers) {
            return {
                restrict: 'A',
                link: function (scope, element, attrs) {
                    var callback = $parse(attrs.draggableClick),
                        click = function (event, tap) {
                            if (element.hasClass('dragged') && !tap) {
                                element.removeClass('dragged');
                                return;
                            }
                            scope.$apply(function () {
                                callback(scope, {
                                    $event: event
                                });
                            });
                        };
                    element.on('click', click);
                    scope.$on('$destroy', function () {
                        element.off('click', click);
                    });
                }
            };
        }).directive('loadMoreButton', function () {
            return {
                restrict: 'A',
                templateUrl: 'core/misc/load_more_button.html',
                scope: {
                    config: '=loadMoreButton'
                }
            };
        }).directive('autoloadOnVerticalScrollEnd', function () {
            return {
                restrict: 'A',
                link: function (scope, element, attrs) {
                    if (!attrs.autoloadOnVerticalScrollEnd) {
                        return;
                    }
                    var config = scope.$eval(attrs.autoloadOnVerticalScrollEnd),
                        listen = config.listen || window,
                        loadMore = function (values, done) {
                            var promise = config.loader.load();
                            if (!promise) {
                                done();
                                return false;
                            }
                            promise.then(function () {
                                done();
                            });
                        },
                        steady,
                        steadyOpts = {
                            conditions: {
                                "max-bottom": config.bottom || 40
                            },
                            scrollElement: $(listen).get(0),
                            throttle: 100,
                            handler: loadMore
                        };
                    steady = new Steady(steadyOpts);
                    scope.$on('$destroy', function () {
                        steady.stop();
                        steady = undefined;
                    });

                }
            };
        }).directive('onVerticalScrollEndEvent', function () {
            return {
                restrict: 'A',
                link: function (scope, element, attrs) {
                    if (!attrs.onVerticalScrollEndEvent) {
                        return;
                    }
                    var config = scope.$eval(attrs.onVerticalScrollEndEvent),
                        scroll = config.listen === 'window' ? window : (config.listen ? config.listen : element),
                        steady,
                        triggerEvent = function (values, done) {
                            scope.$broadcast('onVerticalScrollEnd', values, done);
                        },
                        steadyOpts = {
                            conditions: {
                                "max-bottom": config.bottom || 40
                            },
                            scrollElement: $(scroll).get(0),
                            throttle: 100,
                            handler: triggerEvent
                        };
                    steady = new Steady(steadyOpts);
                    scope.$on('$destroy', function () {
                        steady.stop();
                        steady = undefined;
                    });

                }
            };
        }).directive('resizeChart', function (helpers) {
            return {
                priority: 100,
                link: function (scope, element, attrs) {

                    var resize = function () {
                        var width = $(element).width(),
                            newHeight = helpers.newHeightByWidth(640, 260, width);
                        $(element).height(newHeight);
                    };

                    resize();

                    scope.$on('modalResize', resize);
                }
            };
        }).directive('listButton', function () {
            return {
                templateUrl: 'core/misc/list_button.html',
                transclude: true,
                replace: true
            };
        }).directive('mdInkRippleList', function ($mdInkRipple) {
            return {
                link: function (scope, element, attrs) {
                    $mdInkRipple.attach(scope, element, {
                        dimBackground: true,
                        multiplier: 0.1,
                        moveToCenter: false
                    });
                }
            };
        }).directive('mdInkRippleAction', function ($mdInkRipple) {
            return {
                link: function (scope, element, attrs) {
                    $mdInkRipple.attachButtonBehavior(scope, element, {
                        dimBackground: false
                    });
                }
            };
        }).directive('mdInkRippleFit', function ($mdInkRipple) {
            return {
                link: function (scope, element, attrs) {
                    $mdInkRipple.attachButtonBehavior(scope, element, {
                        dimBackground: false,
                        fitRipple: true,
                        moveToCenter: false
                    });
                }
            };
        }).directive('icon', function ($mdInkRipple) {
            return {
                templateUrl: 'core/misc/icon.html',
                replace: true,
                transclude: true,
                scope: true,
                link: function (scope, element, attrs) {
                    var types = attrs.type.split('.');
                    scope.type = types[0];
                    scope.icon = types[1];
                }
            };
        }).directive('contentListView', function () {
            return {
                scope: {
                    val: '=contentListView'
                },
                templateUrl: 'core/misc/content_list_view.html'
            };
        }).directive('sidenavItem', function ($timeout, $mdSidenav) {
            return {
                templateUrl: 'core/misc/sidenav_item.html',
                transclude: true,
                replace: true,
                link: function (scope, element, attrs) {}
            };
        }).filter('propsFilter', function () {
            return function (items, props) {
                var out = [];

                if (angular.isArray(items)) {
                    items.forEach(function (item) {
                        var itemMatches = false,
                            keys = Object.keys(props),
                            i, prop, text;
                        for (i = 0; i < keys.length; i++) {
                            prop = keys[i];
                            text = props[prop].toLowerCase();
                            if (item[prop].toString().toLowerCase().indexOf(text) !== -1) {
                                itemMatches = true;
                                break;
                            }
                        }

                        if (itemMatches) {
                            out.push(item);
                        }
                    });
                } else {
                    // Let the output be the input untouched
                    out = items;
                }

                return out;
            };
        }).filter('output', function (modelsMeta, outputTypes, $cacheFactory) {

            var types = outputTypes,
                cacheFields = $cacheFactory('cacheFields'),
                getFields = function (kind) {
                    if (!cacheFields.get(kind)) {
                        cacheFields.put(kind, modelsMeta.getFields(kind));
                    }
                    return cacheFields.get(kind);
                };

            return function (obj, key, args) {

                var input = obj[key],
                    fields, field, format;

                if (obj.kind) {
                    fields = getFields(obj.kind);
                    field = fields[key];

                    if (angular.isDefined(field)) {
                        format = types[field.type];
                        if (angular.isDefined(format)) {
                            return format(input, field);
                        }
                        // this is more generic approach to structured objects
                        if (input && typeof input === 'object' && input.hasOwnProperty('name')) {
                            return input.name;
                        }
                    }

                }

                return input;

            };

        }).filter('autobr', function (helpers) {

            return function (str) {
                return helpers.splitLines(str).join("<br />");
            };

        }).filter('formatCurrency', ['$injector', '$locale', function ($injector, $locale) {
            var $filter = $injector.get('$filter'),
                numberFilter = $filter('number'),
                formats = $locale.NUMBER_FORMATS;
            formats.DEFAULT_PRECISION = angular.isUndefined(formats.DEFAULT_PRECISION) ? 2 : formats.DEFAULT_PRECISION;
            return function (amount, currency) {
                amount = parseFloat(amount, 10);
                if (!angular.isNumber(amount) || isNaN(amount)) {
                    return '';
                }
                var isNegative = amount < 0,
                    parts = [],
                    number;

                // @todo this code is incomplete

                /*
                {
                  "name": "US Dollar",
                  "code": "USD",
                  "id": "usd",
                  "_state": null,
                  "negative_separate_by_space": false,
                  "measurement": "Currency",
                  "thousands_separator": ",",
                  "positive_sign": "None",
                  "numeric_code": "840",
                  "positive_sign_position": 1,
                  "rate": null,
                  "digits": 2,
                  "key": "ahdkZXZ-dW5pdmVyc2FsLXRyYWlsLTYwOHILCxICMTciA3VzZAw",
                  "parent": {},
                  "kind": "17",
                  "_next_read_arguments": {},
                  "active": true,
                  "rounding": "0.01",
                  "symbol": "$",
                  "negative_currency_symbol_precedes": true,
                  "grouping": [
                    3,
                    3,
                    0
                  ],
                  "decimal_separator": ".",
                  "positive_separate_by_space": false,
                  "namespace": "",
                  "negative_sign": "-",
                  "factor": null,
                  "_sequence": null,
                  "positive_currency_symbol_precedes": true,
                  "negative_sign_position": 1
                }
                 */

                amount = Math.abs(amount);
                number = numberFilter(amount, currency.digits);

                if (currency.negative_sign_position && isNegative) {
                    if (currency.negative_currency_symbol_precedes) {
                        parts.push(currency.symbol);
                    }

                    if (currency.negative_sign !== 'None' && currency.negative_sign) {
                        parts.push(currency.negative_sign);
                    }
                } else {
                    if (!isNegative && currency.positive_sign_position) {
                        if (currency.negative_currency_symbol_precedes) {
                            parts.push(currency.symbol);
                        }
                        if (currency.positive_sign !== 'None' && currency.positive_sign) {
                            parts.push(currency.positive_sign);
                        }
                    }
                }
                parts.push(number);

                if (!currency.negative_sign_position && isNegative) {
                    if (currency.negative_currency_symbol_precedes) {
                        parts.push(currency.symbol);
                    }
                    parts.push(currency.negative_sign);
                } else {
                    if (!isNegative && !currency.positive_currency_symbol_precedes) {
                        if (currency.negative_currency_symbol_precedes) {
                            parts.push(currency.symbol);
                        }
                        if (currency.positive_sign !== 'None' && currency.positive_sign) {
                            parts.push(currency.positive_sign);
                        }
                    }
                }

                return parts.join('').replace(/\u00A4/g, '');
            };
        }]).filter('substr', function () {
            return function (str) {
                if (angular.isString(str)) {
                    return String.prototype.substr.apply(str, Array.prototype.slice.call(arguments, 1));
                }
                return str;
            };

        }).filter('nl2br', function () {
            return function (input) {
                if (input !== void 0) {
                    return input.replace(/\n/g, '<br />');
                }
            };
        }).filter('highlight', function () {
            function escapeRegexp(queryToEscape) {
                return queryToEscape.replace(/([.?*+^$[\]\\(){}|-])/g, '\\$1');
            }

            return function (matchItem, query) {
                return query && matchItem ? matchItem.replace(new RegExp(escapeRegexp(query), 'gi'), '<span class="ui-select-highlight">$&</span>') : matchItem;
            };
        }).factory('outputTypes', function (dateFilter, GLOBAL_CONFIG, modelsMeta) {
            var outputTypes = {
                SuperDateTimeProperty: function (input, field) {
                    var date = new Date(input);
                    return dateFilter(date, GLOBAL_CONFIG.date.format);
                }
            };
            return outputTypes;
        }).factory('searchBuilder', function (modelsMeta) {
            var create = function () {
                var make = {
                    kind: null,
                    hide: false,
                    filters: {},
                    indexes: [],
                    indexID: null,
                    fields: {
                        indexID: {
                            type: 'SuperStringProperty',
                            choices: [],
                            code_name: 'indexID',
                            required: true,
                            ui: {
                                args: 'search.indexID',
                                label: 'Search Options',
                                writable: true,
                                attrs: {
                                    'ng-change': 'search.makeFilters()'
                                }
                            }
                        },
                        ancestor: {
                            type: 'SuperStringProperty',
                            code_name: 'ancestor',
                            required: 'search.indexes[search.indexID].ancestor',
                            ui: {
                                args: 'search.send.ancestor',
                                label: 'Ancestor',
                                writable: true
                            }
                        },
                        filters: [],
                        orders: []
                    },
                    mapIndexes: function (obj) {
                        angular.forEach(obj, function (o, i) {
                            o._index = i;
                        });
                    },
                    formatSearchFilter: function (input) {
                        var filters, out = '';
                        if (!input || !angular.isObject(input)) {
                            return input;
                        }
                        if (input.ancestor && !input.filters) {
                            out += 'Ancestor and ';
                        }

                        if (input.filters) {
                            out += 'Filter by ';
                            if (input.ancestor) {
                                out += 'ancestor and ';
                            }
                            filters = $.map(input.filters, function (filter) {
                                return filter[0];
                            });

                            out += filters.join(" and ");

                            if (input.orders) {
                                out += ' and ';
                            }
                        }

                        if (input.orders) {
                            out += ' order by ' + $.map(input.orders, function (value) {
                                return value[0];
                            }).join(', ');
                        }

                        return out;
                    },
                    resetFilters: function () {
                        this.send.filters = [];
                        this.send.orders = [];
                        delete this.send.ancestor;
                    },
                    changeKindUI: function () {
                        this.changeKind();
                        this.setSearch(this.kind, undefined);
                        this.makeFilters();
                    },
                    changeKind: function () {

                        var searchActionArguments = modelsMeta.getActionArguments(this.kind, 'search'),
                            searchField,
                            cfg,
                            that = this;

                        if (searchActionArguments) {
                            try {
                                searchField = searchActionArguments.search;
                                this.default_send = searchField['default'];
                            } catch (ignore) {}

                            if (!searchField) {
                                this.hide = true;
                                searchField = {};
                            } else {
                                this.hide = false;
                            }

                            cfg = searchField.cfg;
                            this.cfg = cfg;
                            this.send.kind = this.kind;
                            this.filters = cfg.filters || {};
                            this.indexes = cfg.indexes || [];
                            this.indexID = null;
                            this.mapIndexes(cfg.indexes);
                            that.fields.indexID.choices = [];
                            angular.forEach(cfg.indexes, function (index) {
                                var choice = {
                                    key: index._index,
                                    name: that.formatSearchFilter(index)
                                };
                                that.fields.indexID.choices.push(choice);
                            });

                        }

                    },
                    changeOrderBy: function (e) {
                        e.field = this.indexes[this.indexID].orders[e._index][0];
                    },
                    makeFilters: function (reset) {
                        var that = this,
                            indx,
                            field,
                            operator;
                        if (!angular.isDefined(reset)) {
                            reset = true;
                        }

                        if (reset) {
                            this.resetFilters();
                        }
                        that.fields.filters = [];
                        that.fields.orders = [];

                        indx = that.indexes[that.indexID];


                        angular.forEach(indx.filters, function (filter, i) {
                            field = that.filters[filter[0]];
                            field.required = 'search.indexID != null && search.send.filters.length';
                            field.code_name = 'filter_' + filter[0];
                            field.ui = {
                                args: 'search.send.filters[\'' + i + '\'].value',
                                writable: true
                            };

                            if (reset) {
                                that.send.filters.push({
                                    field: filter[0],
                                    operator: filter[1][0],
                                    value: (field['default'] ? field['default'] : ''),
                                    _index: i
                                });
                            }

                            operator = {
                                type: 'SuperStringProperty',
                                choices: filter[1],
                                code_name: 'op_' + i,
                                required: field.required,
                                ui: {
                                    label: 'Operator',
                                    writable: true,
                                    args: 'search.send.filters[\'' + i + '\'].operator'
                                }
                            };
                            that.fields.filters.push([operator, field]);
                        });

                        angular.forEach(indx.orders, function (order, i) {

                            if (reset) {
                                that.send.orders.push({
                                    field: order[0],
                                    operator: order[1][0],
                                    _index: i,
                                });
                            }

                            field = {
                                type: 'SuperStringProperty',
                                choices: order[1],
                                code_name: 'order_by_' + order[0],
                                required: 'search.indexID != null && search.send.filters.length',
                                ui: {
                                    writable: true,
                                    args: 'search.send.orders[\'' + i + '\'].operator'
                                }
                            };

                            that.fields.orders.push(field);
                        });

                        if (!indx.orders) {
                            that.send.orders = [];
                        }

                    },
                    discoverIndexID: function () {
                        var that = this,
                            filters = this.send.filters,
                            ancestor = this.send.ancestor,
                            orders = this.send.orders;

                        angular.forEach(this.indexes, function (index, indexID) {

                            if ((ancestor && !index.ancestor) || (!ancestor && index.ancestor)) {
                                return;
                            }

                            var got_filters = true,
                                matchCount = 0,
                                orderMatchCount = 0;

                            if (index.filters) {
                                got_filters = false;
                                if (filters && filters.length) {
                                    angular.forEach(index.filters, function (filter) {
                                        var gets = _.findWhere(filters, {
                                            field: filter[0]
                                        });
                                        if (gets && $.inArray(gets.operator, filter[1]) !== -1) {
                                            matchCount += 1;
                                        }
                                    });

                                    if (filters.length === matchCount && index.filters.length === filters.length) {
                                        got_filters = true;
                                        that.indexID = indexID;
                                    }
                                }

                            }


                            angular.forEach(index.orders, function (order, oi) {

                                var gets = _.findWhere(orders, {
                                    field: order[0]
                                });

                                if (got_filters && gets && $.inArray(gets.operator, order[1]) !== -1) {
                                    orderMatchCount += 1;
                                    gets._index = oi;
                                }
                            });

                            if (got_filters && index.orders && orderMatchCount === orders.length && index.orders.length === orders.length) {
                                that.indexID = indexID;
                            }

                        });

                    },
                    setSearch: function (kind, search) {

                        if (kind === undefined || kind === null) {
                            this.hide = true;
                            return;
                        }

                        if (this.kind !== kind) {
                            this.kind = kind;
                            this.changeKind();
                            this.resetFilters();
                        }

                        var searchActionArguments = modelsMeta.getActionArguments(this.kind, 'search'),
                            searchArgument = null;
                        if (searchActionArguments) {
                            try {
                                searchArgument = searchActionArguments.search;
                            } catch (ignore) {}

                            if (searchArgument) {
                                if (search === undefined && searchArgument['default']) {
                                    this.send = searchArgument['default'];
                                } else if (search) {
                                    this.send = search;
                                }

                                this.discoverIndexID();
                                this.makeFilters(false);
                            }

                        } else {
                            this.hide = true;
                        }

                    },
                    doSearch: function () {
                        throw new Error('Not implemented');
                    },
                    submitSearch: function () {
                        this.doSearch();
                    },
                    send: {
                        filters: [],
                        orders: [],
                    }
                };
                return make;
            };
            return {
                create: create
            };
        }).factory('channelApi', function (GLOBAL_CONFIG) {
            // low level channel api
            var channelApi = {
                instances: {},
                create: function (token) {
                    if (!channelApi.instances[token]) {
                        var instance;
                        instance = {
                            callbacks: {},
                            events: {},
                            signals: [],
                            socket: null,
                            afterOnclose: [],
                            onclose: function (cb) {
                                this.afterOnclose.unshift(cb);
                            },
                            channel: new goog.appengine.Channel(token),
                            open: function (config) {
                                var that = this;
                                angular.forEach(config, function (callback, type) {
                                    that[type](callback);
                                });
                                if (that.socket !== null) {
                                    return that;
                                }
                                that.socket = that.channel.open(that.events);
                                that.socket.onclose = function () {
                                    angular.forEach(that.afterOnclose, function (cb) {
                                        cb();
                                    });
                                };
                                return that;
                            },
                            destroy: function () {
                                delete channelApi.instances[token];
                            },
                            queue: function (type, cb) {
                                var id = this.signals.length;
                                this.signals.push(id);
                                this.callbacks[type].push([cb, id]);
                            },
                            dispatch: function (type, args) {
                                var that = this,
                                    terminate = [];
                                angular.forEach(this.callbacks[type], function (data) {
                                    if ($.inArray(data[1], that.signals) === -1) {
                                        terminate.push(data);
                                        return;
                                    }
                                    args = _.toArray(args);
                                    args.push(function () {
                                        that.signals.remove(data[1]);
                                    });
                                    data[0].apply(that.socket, args);
                                });

                                if (terminate) {
                                    angular.forEach(terminate, function (data) {
                                        that.callbacks[type].remove(data);
                                    });
                                    terminate = [];
                                }
                                if (!that.signals.length) {
                                    that.socket.close();
                                }
                            }
                        };
                        angular.forEach(['onopen', 'onmessage', 'onerror'], function (type) {
                            instance.callbacks[type] = [];
                            instance[type] = function (cb) {
                                this.queue(type, cb);
                            };
                            instance.events[type] = function () {
                                instance.dispatch(type, arguments);
                            };
                        });

                        instance.afterOnclose.push(function () {
                            instance.destroy();
                        });
                        channelApi.instances[token] = instance;
                    }
                    return channelApi.instances[token];
                }
            };

            if (GLOBAL_CONFIG.debug) {
                window._channelApi = channelApi;
            }
            return channelApi;
        }).factory('channelNotifications', function (channelApi, modals) {
            var channelNotifications = {
                instances: {},
                create: function (token) {
                    var out;
                    if (!channelNotifications.instances[token]) {
                        out = channelApi.create(token);
                        channelNotifications.instances[token] = out;
                        out.open({
                            onclose: function () {
                                delete channelNotifications.instances[token];
                            },
                            onmessage: function (message, destroy) {
                                destroy();
                                if (angular.isObject(message) && message.data) {
                                    try {
                                        var response = angular.fromJson(message.data);
                                        modals.alert(response.body);
                                    } catch (ignore) {}
                                }
                            }
                        });
                    } else {
                        out = channelNotifications.instances[token];
                    }
                    return out;
                }
            };
            return channelNotifications;
        });
}());
(function () {
    'use strict';
    angular.module('app').factory('$$stackedMap', function () {
        return {
            createNew: function () {
                var stack = [];

                return {
                    add: function (key, value) {
                        stack.push({
                            key: key,
                            value: value
                        });
                    },
                    get: function (key) {
                        for (var i = 0; i < stack.length; i++) {
                            if (key == stack[i].key) {
                                return stack[i];
                            }
                        }
                    },
                    keys: function () {
                        var keys = [];
                        for (var i = 0; i < stack.length; i++) {
                            keys.push(stack[i].key);
                        }
                        return keys;
                    },
                    top: function () {
                        return stack[stack.length - 1];
                    },
                    remove: function (key) {
                        var idx = -1;
                        for (var i = 0; i < stack.length; i++) {
                            if (key == stack[i].key) {
                                idx = i;
                                break;
                            }
                        }
                        return stack.splice(idx, 1)[0];
                    },
                    removeTop: function () {
                        return stack.splice(stack.length - 1, 1)[0];
                    },
                    length: function () {
                        return stack.length;
                    }
                };
            }
        };
    })

    /**
     * A helper directive for the $modal service. It creates a backdrop element.
     */
    .directive('modalBackdrop', ['$timeout', function ($timeout) {
        return {
            restrict: 'EA',
            replace: true,
            templateUrl: 'core/modal/backdrop.html',
            link: function (scope, element, attrs) {
                scope.backdropClass = attrs.backdropClass || '';

                scope.animate = false;

                //trigger CSS transitions
                $timeout(function () {
                    scope.animate = true;
                });
            }
        };
    }])

    .directive('modalWindow', ['$modalStack', '$timeout', '$$rAF', '$mdConstant', '$q',
        function ($modalStack, $timeout, $$rAF, $mdConstant, $q) {
            return {
                restrict: 'EA',
                scope: {
                    index: '@',
                    animate: '=',
                    modalOptions: '='
                },
                replace: true,
                transclude: true,
                templateUrl: function (tElement, tAttrs) {
                    return tAttrs.templateUrl || 'core/modal/window.html';
                },
                link: function (scope, element, attrs) {
                    var clickElement = scope.modalOptions.targetEvent && scope.modalOptions.targetEvent.target;
                    element.addClass(!scope.modalOptions.fullScreen ? 'modal-medium' : ''); // attrs.windowClass
                    scope.size = attrs.size;
                    $timeout(function () {
                        // trigger CSS transitions
                        if (!scope.modalOptions.fullScreen) {
                            var modal = $(element).find('.modal-dialog'),
                                iwidth = modal.width(),
                                iheight = modal.height();
                            scope.modalOptions.resize = function () {
                                var wwidth = $(window).width(),
                                    wheight = $(window).height(),
                                    maxHeight,
                                    maxWidth,
                                    minWidth = '',
                                    minHeight = '';
                                if (iheight >= wheight) {
                                    maxHeight = wheight - 16 * 2;
                                } else {
                                    maxHeight = '';
                                    minHeight = iheight;
                                }
                                if (iwidth >= wwidth) {
                                    maxWidth = wwidth - 16 * 2;
                                } else {
                                    maxWidth = '';
                                    minWidth = iwidth;
                                }
                                modal.css('max-height', maxHeight);
                                modal.css('max-width', maxWidth);
                                modal.css('min-height', minHeight);
                                modal.css('min-width', minWidth);
                            };
                            scope.modalOptions.resize();
                            $(window).on('resize', scope.modalOptions.resize);
                        }
                        if (clickElement) {
                            var clickRect = clickElement.getBoundingClientRect();
                            var modalRect = element[0].getBoundingClientRect();
                            var scaleX = Math.min(0.5, clickRect.width / modalRect.width);
                            var scaleY = Math.min(0.5, clickRect.height / modalRect.height);

                            element.css($mdConstant.CSS.TRANSFORM, 'translate3d(' +
                                (-modalRect.left + clickRect.left + clickRect.width / 2 - modalRect.width / 2) + 'px,' +
                                (-modalRect.top + clickRect.top + clickRect.height / 2 - modalRect.height / 2) + 'px,' +
                                '0) scale(' + scaleX + ',' + scaleY + ')'
                            );
                        } else {
                            if (scope.modalOptions.inDirection) {
                                element.css($mdConstant.CSS.TRANSFORM, 'translate3d(' + (scope.modalOptions.inDirection === 'right' ? '' : '-') + '100%, 0px, 0px)');
                            }
                        }

                        if (scope.modalOptions.inDirection) {
                            element.addClass('visible');
                        }

                        if (scope.modalOptions.inDirection && !clickElement) {
                            var cb = function () {
                                element.addClass('transition-in-' + scope.modalOptions.inDirection)
                                    .css($mdConstant.CSS.TRANSFORM, '');
                            };
                        } else {
                            var cb = function () {
                                element.addClass('visible');
                                element.addClass('transition-in')
                                    .css($mdConstant.CSS.TRANSFORM, '');
                            };
                        }
                        var deferred = $q.defer();
                        deferred.promise.then(function () {
                            if (!element[0].querySelectorAll('[autofocus]').length) {
                                element[0].focus();
                            }
                            $(window).triggerHandler('modal.visible');
                        });

                        element.on($mdConstant.CSS.TRANSITIONEND, function finished(ev) {
                            if (ev.target === element[0]) {
                                element.off($mdConstant.CSS.TRANSITIONEND, finished);
                                deferred.resolve();
                            }
                        });

                        setTimeout(function () {
                            $$rAF(cb);
                        }, 100);

                        $(window).triggerHandler('modal.open');

                    });

                    scope.close = function (evt) {
                        var modal = $modalStack.getTop();
                        if (modal && modal.value.backdrop && modal.value.backdrop != 'static' && (evt.target === evt.currentTarget)) {
                            evt.preventDefault();
                            evt.stopPropagation();
                            $modalStack.dismiss(modal.key, 'backdrop click');
                        }
                    };
                }
            };
        }
    ])

    .directive('modalTransclude', function () {
        return {
            link: function ($scope, $element, $attrs, controller, $transclude) {
                $transclude($scope.$parent, function (clone) {
                    $element.empty();
                    $element.append(clone);
                });
            }
        };
    })

    .factory('$modalStack', ['$transition', '$timeout', '$document', '$compile', '$rootScope', '$$stackedMap', 'mdContextualMonitor',
        '$mdConstant',
        function ($transition, $timeout, $document, $compile, $rootScope, $$stackedMap, mdContextualMonitor, $mdConstant) {

            var OPENED_MODAL_CLASS = 'modal-open';
            var backdropDomEl, backdropScope;
            var openedWindows = $$stackedMap.createNew();
            var $modalStack = {};

            function backdropIndex() {
                var topBackdropIndex = -1;
                var opened = openedWindows.keys();
                for (var i = 0; i < opened.length; i++) {
                    if (openedWindows.get(opened[i]).value.backdrop) {
                        topBackdropIndex = i;
                    }
                }
                return topBackdropIndex;
            }

            $rootScope.$watch(backdropIndex, function (newBackdropIndex) {
                if (backdropScope) {
                    backdropScope.index = newBackdropIndex;
                }
            });

            function removeModalWindow(modalInstance) {

                var body = $document.find('body').eq(0);
                var modalWindow = openedWindows.get(modalInstance).value;

                //clean up the stack
                openedWindows.remove(modalInstance);

                //remove window DOM element
                backdropDomEl.removeClass('opaque');
                removeAfterAnimate(modalWindow.modalDomEl, modalWindow.modalScope, 300, function () {
                    modalWindow.modalScope.$destroy();
                    body.toggleClass(OPENED_MODAL_CLASS, openedWindows.length() > 0);
                    checkRemoveBackdrop();
                    $(window).triggerHandler('modal.close');
                });
            }

            function checkRemoveBackdrop() {
                //remove backdrop if no longer needed
                if (backdropDomEl && backdropIndex() == -1) {
                    var backdropScopeRef = backdropScope;
                    removeAfterAnimateOld(backdropDomEl, backdropScope, 150, function () {
                        backdropScopeRef.$destroy();
                        backdropScopeRef = null;
                    });

                    backdropDomEl = undefined;
                    backdropScope = undefined;
                }
            }

            function removeAfterAnimateOld(domEl, scope, emulateTime, done) {
                // Closing animation
                scope.animate = false;

                var transitionEndEventName = $transition.transitionEndEventName;
                if (transitionEndEventName) {
                    // transition out
                    var timeout = $timeout(afterAnimating, emulateTime);

                    domEl.bind(transitionEndEventName, function () {
                        $timeout.cancel(timeout);
                        afterAnimating();
                        scope.$apply();
                    });
                } else {
                    // Ensure this call is async
                    $timeout(afterAnimating);
                }

                function afterAnimating() {
                    if (afterAnimating.done) {
                        return;
                    }
                    afterAnimating.done = true;

                    domEl.remove();
                    if (done) {
                        done();
                    }
                }
            }

            function removeAfterAnimate(domEl, scope, emulateTime, done) {
                // Closing animation
                var modalEl = domEl,
                    clickElement = scope.modalOptions.targetEvent && scope.modalOptions.targetEvent.target;

                if (!clickElement && scope.modalOptions.inDirection) {
                    modalEl.addClass('transition-out-' + scope.modalOptions.outDirection).removeClass('transition-in-' + scope.modalOptions.inDirection)
                        .css($mdConstant.CSS.TRANSFORM, 'translate3d(' + (scope.modalOptions.outDirection === 'right' ? '' : '-') + '100%, 0px, 0px)');
                } else {
                    modalEl.addClass('transition-out').removeClass('transition-in');
                    if (clickElement) {
                        var clickRect = clickElement.getBoundingClientRect();
                        var modalRect = modalEl[0].getBoundingClientRect();
                        var scaleX = Math.min(0.5, clickRect.width / modalRect.width);
                        var scaleY = Math.min(0.5, clickRect.height / modalRect.height);

                        modalEl.css($mdConstant.CSS.TRANSFORM, 'translate3d(' +
                            (-modalRect.left + clickRect.left + clickRect.width / 2 - modalRect.width / 2) + 'px,' +
                            (-modalRect.top + clickRect.top + clickRect.height / 2 - modalRect.height / 2) + 'px,' +
                            '0) scale(' + scaleX + ',' + scaleY + ')'
                        );
                    }
                }

                modalEl.on($mdConstant.CSS.TRANSITIONEND, function afterAnimating(ev) {
                    if (ev.target !== modalEl[0]) {
                        return;
                    }
                    domEl.remove();
                    if (done) {
                        done();
                    }
                });
            }

            $modalStack.open = function (modalInstance, modal) {

                openedWindows.add(modalInstance, {
                    deferred: modal.deferred,
                    modalScope: modal.scope,
                    backdrop: modal.backdrop,
                    keyboard: modal.keyboard
                });

                modal.scope.modalOptions = {
                    inDirection: modal.inDirection,
                    outDirection: modal.outDirection,
                    targetEvent: modal.targetEvent,
                    fullScreen: modal.fullScreen
                };

                var body = $document.find('body').eq(0),
                    currBackdropIndex = backdropIndex();

                if (currBackdropIndex >= 0 && !backdropDomEl) {
                    backdropScope = $rootScope.$new(true);
                    backdropScope.index = currBackdropIndex;
                    var angularBackgroundDomEl = angular.element('<div modal-backdrop></div>');
                    angularBackgroundDomEl.attr('backdrop-class', modal.backdropClass);
                    backdropDomEl = $compile(angularBackgroundDomEl)(backdropScope);
                    body.append(backdropDomEl);
                }

                if (!modal.fullScreen) {
                    backdropDomEl.addClass('opaque');
                }

                var angularDomEl = angular.element('<div modal-window></div>');

                angularDomEl.attr({
                    'template-url': modal.windowTemplateUrl,
                    'window-class': modal.windowClass,
                    'size': modal.size,
                    'index': openedWindows.length() - 1,
                    'modal-options': 'modalOptions',
                    'animate': 'animate',
                    'exiting': 'exiting'
                }).html(modal.content);

                var modalDomEl = $compile(angularDomEl)(modal.scope);
                openedWindows.top().value.modalDomEl = modalDomEl;
                body.append(modalDomEl);
                body.addClass(OPENED_MODAL_CLASS);

                if (modal.keyboard) {
                    var esc = function (e) {
                        e.preventDefault();
                        $rootScope.$apply(function () {
                            modalInstance.withEscape = true;
                            $modalStack.dismiss(modalInstance, 'escape key press');
                        });
                        return true;
                    };
                    modalInstance.esc = esc;
                    mdContextualMonitor.queue(esc);
                }

            };

            $modalStack.close = function (modalInstance, result) {
                var modalWindow = openedWindows.get(modalInstance);
                if (modalWindow) {
                    modalWindow.value.deferred.resolve(result);
                    removeModalWindow(modalInstance);
                }
            };

            $modalStack.dismiss = function (modalInstance, reason) {
                var modalWindow = openedWindows.get(modalInstance);
                if (!modalInstance.withEscape) {
                    mdContextualMonitor.dequeue(modalInstance.esc);
                    if (modalWindow.value.modalScope.modalOptions.resize) {
                        $(window).off('resize', modalWindow.value.modalScope.modalOptions.resize);
                    }
                }
                if (modalWindow) {
                    modalWindow.value.deferred.reject(reason);
                    removeModalWindow(modalInstance);
                }
            };

            $modalStack.dismissAll = function (reason) {
                var topModal = this.getTop();
                while (topModal) {
                    this.dismiss(topModal.key, reason);
                    topModal = this.getTop();
                }
            };

            $modalStack.getTop = function () {
                return openedWindows.top();
            };

            return $modalStack;
        }
    ])

    .provider('$modal', function () {

        var $modalProvider = {
            options: {
                backdrop: true, //can be also false or 'static'
                keyboard: true,
                inDirection: 'right',
                outDirection: 'right',
                fullScreen: true
            },
            $get: ['$injector', '$rootScope', '$q', '$http', '$templateCache', '$controller', '$modalStack',
                function ($injector, $rootScope, $q, $http, $templateCache, $controller, $modalStack) {

                    var $modal = {};

                    function getTemplatePromise(options) {
                        return options.template ? $q.when(options.template) :
                            $http.get(angular.isFunction(options.templateUrl) ? (options.templateUrl)() : options.templateUrl, {
                                cache: $templateCache
                            }).then(function (result) {
                                return result.data;
                            });
                    }

                    function getResolvePromises(resolves) {
                        var promisesArr = [];
                        angular.forEach(resolves, function (value) {
                            if (angular.isFunction(value) || angular.isArray(value)) {
                                promisesArr.push($q.when($injector.invoke(value)));
                            }
                        });
                        return promisesArr;
                    }

                    $modal.open = function (modalOptions) {

                        var modalResultDeferred = $q.defer();
                        var modalOpenedDeferred = $q.defer();

                        //prepare an instance of a modal to be injected into controllers and returned to a caller
                        var modalInstance = {
                            result: modalResultDeferred.promise,
                            opened: modalOpenedDeferred.promise,
                            close: function (result) {
                                $modalStack.close(modalInstance, result);
                            },
                            dismiss: function (reason) {
                                $modalStack.dismiss(modalInstance, reason);
                            }
                        };

                        //merge and clean up options
                        modalOptions = angular.extend({}, $modalProvider.options, modalOptions);
                        modalOptions.resolve = modalOptions.resolve || {};

                        //verify options
                        if (!modalOptions.template && !modalOptions.templateUrl) {
                            throw new Error('One of template or templateUrl options is required.');
                        }

                        var templateAndResolvePromise =
                            $q.all([getTemplatePromise(modalOptions)].concat(getResolvePromises(modalOptions.resolve)));


                        templateAndResolvePromise.then(function resolveSuccess(tplAndVars) {

                            var modalScope = (modalOptions.scope || $rootScope).$new();
                            modalScope.$close = modalInstance.close;
                            modalScope.$dismiss = modalInstance.dismiss;

                            var ctrlInstance, ctrlLocals = {};
                            var resolveIter = 1;

                            //controllers
                            if (modalOptions.controller) {
                                ctrlLocals.$scope = modalScope;
                                ctrlLocals.$modalInstance = modalInstance;
                                angular.forEach(modalOptions.resolve, function (value, key) {
                                    ctrlLocals[key] = tplAndVars[resolveIter++];
                                });

                                ctrlInstance = $controller(modalOptions.controller, ctrlLocals);
                                if (modalOptions.controllerAs) {
                                    modalScope[modalOptions.controllerAs] = ctrlInstance;
                                }
                            }

                            $modalStack.open(modalInstance, {
                                scope: modalScope,
                                deferred: modalResultDeferred,
                                content: tplAndVars[0],
                                backdrop: modalOptions.backdrop,
                                keyboard: modalOptions.keyboard,
                                backdropClass: modalOptions.backdropClass,
                                windowClass: modalOptions.windowClass,
                                windowTemplateUrl: modalOptions.windowTemplateUrl,
                                size: modalOptions.size,
                                inDirection: modalOptions.inDirection,
                                outDirection: modalOptions.outDirection,
                                fullScreen: modalOptions.fullScreen,
                                targetEvent: modalOptions.targetEvent
                            });

                        }, function resolveError(reason) {
                            modalResultDeferred.reject(reason);
                        });

                        templateAndResolvePromise.then(function () {
                            modalOpenedDeferred.resolve(true);
                        }, function () {
                            modalOpenedDeferred.reject(false);
                        });

                        return modalInstance;
                    };

                    return $modal;
                }
            ]
        };

        return $modalProvider;
    }).directive('fitInModal', function () {
        return {
            link: function (scope, element, attrs) {
                var time,
                    fn = function () {
                        if (time) {
                            clearTimeout(time);
                        }
                        time = setTimeout(function () {
                            var modal = $(element).parents('.modal:first'),
                                modalDialog = modal.find('.modal-dialog:first'),
                                height = (modal.hasClass('modal-medium') ? modalDialog.height() : $(window).height());
                            modalDialog.find('.fixed-height, .min-height, .max-height').each(function () {
                                var newHeight = height,
                                    footer = modalDialog.find('.md-actions'),
                                    toolbar = modalDialog.find('md-toolbar'),
                                    css = 'height';
                                if (footer.length) {
                                    newHeight -= footer.outerHeight();
                                }
                                if (toolbar.length) {
                                    newHeight -= toolbar.outerHeight();
                                }
                                if ($(this).hasClass('min-height')) {
                                    css = 'min-height';
                                }
                                if ($(this).hasClass('max-height')) {
                                    css = 'max-height';
                                }
                                $(this).css(css, newHeight);
                            });
                            scope.$broadcast('modalResize');
                        }, 50);
                    };

                $(window).bind('resize modal.open', fn);
                scope.$on('$destroy', function () {
                    $(window).unbind('resize modal.open', fn);
                });
            }
        };
    }).factory('modals', function ($modal, $q, helpers) {

        var modals = {
            howToSort: function ($event) {
                return modals.alert('Grab the button to start sorting.', {
                    targetEvent: $event
                });
            },
            alert: function (message, extraConfig) {
                if (angular.isFunction(extraConfig)) {
                    extraConfig = {
                        ok: extraConfig
                    };
                }
                return this.create($.extend({
                    message: message,
                    type: 'alert'
                }, extraConfig));
            },
            confirm: function (messageOrConfig, callbackOrConfig) {
                var theConfig = {
                    message: 'Are you sure you want to do this?',
                    type: 'confirm'
                }, config;

                if (angular.isFunction(callbackOrConfig)) {
                    config = {
                        confirm: callbackOrConfig
                    };
                } else if (angular.isObject(callbackOrConfig)) {
                    config = callbackOrConfig;
                }
                if (angular.isDefined(messageOrConfig)) {
                    if (!angular.isObject(messageOrConfig)) {
                        config.message = messageOrConfig;
                    } else {
                        config = messageOrConfig;
                    }
                }
                config = helpers.alwaysObject(config);
                helpers.extendDeep(theConfig, config);
                theConfig.confirm = function () {
                    if (angular.isFunction(config.confirm)) {
                        config.confirm.call(this);
                    }

                    this.dismiss();
                };
                return this.create(theConfig, {
                    inDirection: false,
                    outDirection: false
                });
            },
            create: function (extraConfig, modalConfig) {
                var config = {
                    message: '',
                    type: 'notice'
                }, defaultModalConfig;
                helpers.extendDeep(config, extraConfig);
                defaultModalConfig = {
                    fullScreen: false,
                    targetEvent: extraConfig && extraConfig.targetEvent,
                    templateUrl: 'core/misc/' + config.type + '.html',
                    controller: function ($scope) {
                        var callback = (angular.isFunction(extraConfig) ? extraConfig : (extraConfig.ok ? extraConfig.ok : null));
                        config.dismiss = function () {
                            if (callback) {
                                callback.call(this);
                            }
                            $scope.$close();
                        };

                        if (!angular.isObject(extraConfig)) {
                            extraConfig = {};
                        }
                        $scope.config = config;
                    }
                };
                $.extend(defaultModalConfig, modalConfig);
                return $modal.open(defaultModalConfig);
            }
        };
        return modals;
    });

}());
(function () {
    'use strict';
    angular.module('app')
        .value('modelsInfo', {})
        .value('currentAccount', {}).factory('modelsMeta', function ($injector, GLOBAL_CONFIG) {

            var modelsMeta = {},
                standardize = function (fields) {
                    angular.forEach(fields, function (field, field_key) {
                        if (field.ui === undefined) {
                            field.ui = {};
                        }
                        if (field.code_name === null) {
                            field.code_name = field_key;
                        }
                        if (field.modelclass !== undefined) {
                            standardize(field.modelclass);
                        }
                    });

                };

            modelsMeta.friendlyActionName = function (kind, action_key) {

                var info = this.get(kind),
                    actions,
                    friendlyName;
                if (info === undefined) {
                    return undefined;
                }

                actions = info.actions;

                angular.forEach(actions, function (action) {
                    if (action.key === action_key) {
                        friendlyName = action.id;
                    }
                });

                return friendlyName;
            };

            modelsMeta.getFields = function (kind_id) {
                if (!angular.isDefined(kind_id)) {
                    console.error('provided kind id is not acceptable, got: ' +
                        kind_id);
                    return undefined;
                }
                var info = this.get(kind_id),
                    fields;
                if (!angular.isDefined(info)) {
                    console.error('could not find meta info for kind ' + kind_id);
                    return undefined;
                }

                fields = angular.copy(info.fields);

                standardize(fields);

                return fields;
            };

            modelsMeta.getDefaultActionArguments = function (kind, action) {
                var getAction = this.getActionArguments(kind, action),
                    defaultArgs = {};

                angular.forEach(getAction['arguments'], function (arg) {
                    if (arg['default'] !== null) {
                        defaultArgs[arg.code_name] = arg['default'];
                    }

                });

                return defaultArgs;
            };

            modelsMeta.getActionArguments = function (kind_id, action) {
                var info = this.get(kind_id),
                    getAction,
                    actionArguments = {},
                    fields;
                if (!angular.isDefined(info)) {
                    return undefined;
                }
                if (angular.isDefined(action)) {
                    getAction = info.mapped_actions[action];
                    if (!angular.isDefined(getAction)) {
                        console.error('action ' + action + ' not found for kind ' + kind_id);
                        return undefined;
                    }
                    fields = angular.copy(getAction['arguments']);

                    standardize(fields);
                    return fields;
                }

                angular.forEach(info.mapped_actions, function (action) {
                    fields = angular.copy(action['arguments']);
                    standardize(fields);
                    actionArguments[action.id] = fields;
                });

                return actionArguments;

            };

            modelsMeta.getActions = function (kind_id) {
                var info = this.get(kind_id),
                    actions;
                if (!angular.isDefined(info)) {
                    return undefined;
                }
                actions = info.mapped_actions;
                angular.forEach(actions, function (action) {
                    standardize(action['arguments']);
                });

                return actions;
            };

            modelsMeta.getName = function (kind_id) {
                var info = this.get(kind_id);
                if (!angular.isDefined(info)) {
                    console.error('model name not found for kind ' + kind_id);
                    return undefined;
                }
                return info.name;
            };

            modelsMeta.get = function (kind_id) {

                var modelsInfo = $injector.get('modelsInfo'),
                    kind = modelsInfo[kind_id],
                    fields = {},
                    actions = {},
                    data;

                if (kind === undefined) {
                    console.error('no info for kind ' + kind_id);
                    return undefined;
                }

                angular.forEach(kind, function (value, key) {
                    if (key !== '_actions' && key !== '__name__') {
                        fields[key] = value;
                    }
                });

                angular.forEach(kind._actions, function (action) {
                    actions[action.id] = action;
                });

                data = {
                    actions: kind._actions,
                    mapped_actions: actions,
                    fields: fields,
                    name: kind.__name__
                };

                return data;
            };

            // expose this to global intentionally, this is used mostly for console debugging @todo remove in production
            if (GLOBAL_CONFIG.debug) {
                window._modelsMeta = modelsMeta;
            }

            return modelsMeta;

        }).factory('ruleEngine', function (modelsMeta) {

            var ruleEngine = {
                run: function (entity) {
                    var actions = {},
                        inputs = {},
                        kindInfo = modelsMeta.get(entity.kind),
                        actionPermissions = entity._action_permissions,
                        fieldPermissions = entity._field_permissions,
                        ruleActions = kindInfo.actions,
                        config = {
                            action: actions,
                            input: inputs,
                            field: fieldPermissions
                        },
                        actionTranslate = function (actionName) {
                            return actionPermissions[ruleActions[actionName].key];
                        },
                        executable = function (actionName) {
                            var gets = actionTranslate(actionName);
                            return gets.executable;
                        };
                    if (actionPermissions === undefined) {
                        return undefined;
                        // if the permissions are not present, there is no rule engine here...
                    }
                    angular.forEach(ruleActions, function (value, key) {

                        if (!config.action[value.id]) {
                            config.action[value.id] = {};
                        }
                        config.action[value.id].executable = executable(key);

                        angular.forEach(value.arguments, function (argumentValue) {
                            var argument_key = argumentValue.code_name;
                            if (!config.input[value.id]) {
                                config.input[value.id] = {};
                            }
                            config.input[value.id][argument_key] = argumentValue;
                        });

                    });

                    return config;
                }
            };

            return ruleEngine;
        }).factory('modelsUtil', function (modelsMeta, ruleEngine, GLOBAL_CONFIG) {
            // Service used for normalizing entity data that gets retrieved from datastore
            var modelsUtil = {
                normalizeMultiple: function (entities) {
                    angular.forEach(entities, function (entity) {
                        modelsUtil.normalize(entity);
                    });
                },
                argumentsToJson: function (entity, pretty) {
                    var ignore = ['_field_permissions', '_next_read_arguments', '_read_arguments', '_action_permissions', 'ui'];
                    return JSON.stringify(entity,
                        function (key, value) {
                            var val = value,
                                newval;

                            if (angular.isObject(value) && value.ui) {
                                newval = {};
                                angular.forEach(value, function (v, k) {
                                    if ($.inArray(k, ignore) === -1) {
                                        newval[k] = v;
                                    }
                                });
                                val = newval;
                            }

                            if (typeof key === 'string' && key.charAt(0) === '$') {
                                val = undefined;
                            } else if (value && value.document && value.location && value.alert && value.setInterval) {
                                val = '$WINDOW';
                            } else if (value && document === value) {
                                val = '$DOCUMENT';
                            } else if (value && value.$evalAsync && value.$watch) {
                                val = '$SCOPE';
                            }

                            return val;
                        }, pretty ? '  ' : null);
                },
                normalize: function (entity, fields, parent, subentity_field_key, subentity_position, noui) {
                    if (entity.ui && entity.ui.normalized) {
                        return;
                    }

                    if (fields === undefined) {
                        fields = modelsMeta.getFields(entity.kind);
                    }

                    if (noui === undefined) {

                        entity.ui = {};
                        entity.ui.normalized = true;
                        entity.ui.access = [];
                        if (subentity_field_key) {
                            entity.ui.access.extend(parent.ui.access);
                            entity.ui.access.push(subentity_field_key);
                            if (subentity_position !== undefined) {
                                entity.ui.access.push(subentity_position);
                            }

                        }
                        /// ui must be now reserved keyword in datastore and we use it for making ui related functions
                        if (parent === undefined) {
                            entity.ui.rule = ruleEngine.run(entity);
                        }

                    }

                    angular.forEach(fields, function (field) {
                        var defaults = field['default'],
                            value = entity[field.code_name];
                        if (field.type === 'SuperDateTimeProperty' && !defaults) {
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

                        if (field.type === 'SuperDateTimeProperty' && angular.isString(value)) {
                            entity[field.code_name] = new Date(value);
                        }

                        if (field.is_structured) {
                            if (field.repeated) {
                                angular.forEach(value, function (subentity, i) {
                                    modelsUtil.normalize(subentity, field.modelclass,
                                        entity, field.code_name, i);
                                });
                            } else {

                                if ((value === undefined || value === null)) {
                                    if (field.required) {
                                        value = {
                                            kind: field.modelclass_kind
                                        };
                                        entity[field.code_name] = value;
                                    }
                                }

                                if (!(value === undefined || value === null)) {
                                    modelsUtil.normalize(value, field.modelclass, entity,
                                        field.code_name, undefined, noui);
                                }

                            }
                        }

                    });

                }
            };

            if (GLOBAL_CONFIG.debug) {
                window._modelsUtil = modelsUtil;
            }
            return modelsUtil;
        }).factory('modelsEditor', function ($modal, endpoint, $q, helpers,
            modelsUtil, errorHandling, models, modelsMeta, $timeout, $filter, formInputTypes, recordAccordion) {

            var modelsEditor = {
                create: function (new_config) {

                    var config = {
                            showClose: true,
                            closeAfterSave: false,
                            action: 'update',
                            templateBodyUrl: 'core/models/manage_body_default.html',
                            scope: {},
                            fields: [],
                            init: angular.noop,
                            getScope: null,
                            defaultInit: angular.noop,
                            defaultArgumentLoader: function ($scope) {
                                var entityCopy = angular.copy($scope.entity),
                                    actionArguments = modelsMeta.getActionArguments($scope.config.kind, $scope.config.action),
                                    args = {};

                                angular.forEach(actionArguments, function (arg) {
                                    var val = entityCopy[arg.code_name];
                                    // default is only acceptable if its not null or undefined
                                    if (val === undefined && (arg['default'] !== null &&
                                            arg['default'] !== undefined)) {
                                        val = arg['default'];
                                    }
                                    if (val !== undefined) {
                                        // arg can never be "undefined"
                                        args[arg.code_name] = val;
                                    }

                                });

                                if ($scope.entity.key) {
                                    args.key = entityCopy.key;
                                }

                                args.ui = entityCopy.ui;

                                // every entity has _read_arguments when retrieved from database
                                // argument loader will attach that to its next rpc
                                // to ensure that entity that has been fetched from database
                                // gets the same read arguments for next rpc
                                if (entityCopy._read_arguments) {
                                    args.read_arguments = entityCopy._read_arguments;
                                }

                                // attaches next read arguments to args too, needed for paging
                                if (entityCopy._next_read_arguments) {
                                    args._next_read_arguments = entityCopy._next_read_arguments;
                                }

                                // attach extra data to args
                                $.extend(args, $scope.withArgs);

                                // attach which action and model should be used in rpc from the config
                                args.action_id = $scope.config.action;
                                args.action_model = $scope.config.kind;
                                return args;
                            },
                            argumentLoader: function ($scope) {
                                return this.defaultArgumentLoader($scope);
                            },
                            defaultPrepareReadArguments: function ($scope) {
                                // it will scan entire args and populate read arguments
                                if (!angular.isObject($scope.args.read_arguments)) {
                                    $scope.args.read_arguments = {};
                                }
                                var readArgs = $scope.args.read_arguments,
                                    parser = function (arg, key, readArgs) {
                                        if (angular.isArray(arg)) {
                                            var path = readArgs[key];
                                            if (!path) {
                                                path = {
                                                    config: {}
                                                };
                                            }

                                            if (!path.config) {
                                                path.config = {};
                                            }

                                            if (arg && angular.isObject(arg[0])) {
                                                path.config.keys = $.map(arg, function (ent) {
                                                    return ent.key;
                                                });
                                            }

                                            readArgs[key] = path;
                                        }
                                    };
                                angular.forEach($scope.args, function (arg, key) {
                                    parser(arg, key, readArgs);
                                });
                            },
                            prepareReadArguments: function ($scope) {
                                this.defaultPrepareReadArguments($scope);
                            }
                        },
                        actionArguments, modelsEditorInstance;

                    // recurse the config adding only what is supplied by the `new_config`
                    helpers.extendDeep(config, new_config);

                    // load all field specs from the arguments that are going to be used based on action and model provided
                    if (!angular.isDefined(config.fields) && angular.isDefined(config.kind) && angular.isDefined(config.action)) {
                        config.fields = [];
                        actionArguments = modelsMeta.getActionArguments(config.kind, config.action);
                        angular.forEach(actionArguments, function (field) {
                            if (angular.isDefined(config.excludeFields) && $.inArray(field.code_name, config.excludeFields) !== -1) {
                                return;
                            }
                            config.fields.push(field);
                        });

                    }
                    // map out the fields to key-value dict
                    config.keyedFields = {};
                    angular.forEach(config.fields, function (field) {
                        config.keyedFields[field.code_name] = field;
                    });

                    console.log('modelsEditor.config', config);

                    modelsEditorInstance = {
                        read: function (entity, args) {
                            if (args === undefined) {
                                args = {
                                    key: entity.key
                                };
                            }
                            var that = this;
                            models[config.kind].actions.read(args).then(function (response) {
                                $.extend(entity, response.data.entity);
                                that.open(entity, args);
                            });
                        },
                        prepare: function (entity, args) {
                            var that = this;
                            models[config.kind].actions.prepare(args).then(function (response) {
                                $.extend(entity, response.data.entity);
                                that.open(entity, args);
                            });
                        },
                        open: function (entity, args) {
                            var opener = $modal,
                                fn = 'open',
                                ctrl;
                            ctrl = function ($scope) {
                                var inflector = $filter('inflector'),
                                    field,
                                    done = {},
                                    found = false,
                                    realTotal = 0,
                                    madeHistory = false,
                                    makeHistory = function () {
                                        if (madeHistory || !$scope.entity.id) {
                                            return false;
                                        }
                                        if (!angular.isDefined($scope.historyConfig)) {
                                            $scope.historyConfig = false;
                                        }
                                        if ($scope.historyConfig === true) {
                                            $scope.historyConfig = {
                                                kind: config.kind,
                                                key: $scope.entity.key
                                            };
                                        } else {
                                            if ($scope.historyConfig === false) {
                                                return false;
                                            }
                                        }
                                        madeHistory = true;
                                        var rule = $scope.args.ui.rule.field._records;
                                        $scope.historyConfig.key = $scope.entity.key;
                                        if (rule && rule.visible) {
                                            recordAccordion.attach($scope.accordions);
                                        }
                                    };
                                config.getScope = function () {
                                    return $scope;
                                };
                                modelsUtil.normalize(entity);

                                $scope.container = {
                                    action: endpoint.url
                                };
                                $scope.withArgs = args;
                                $scope.config = config;
                                $scope.dialog = {
                                    toolbar: config.toolbar,
                                    templateBodyUrl: config.templateBodyUrl
                                };
                                $scope.entity = entity;
                                $scope.args = config.argumentLoader($scope);
                                $scope.rootScope = $scope;

                                $scope.formSetPristine = function () {
                                    if ($scope.container && $scope.container.form) {
                                        $scope.container.form.$setPristine();
                                    }
                                };

                                $scope.formSetDirty = function () {
                                    if ($scope.container && $scope.container.form) {
                                        $scope.container.form.$setDirty();
                                    }
                                };

                                $scope.setAction = function (action) {
                                    $scope.args.action_id = action;
                                    config.action = action;
                                };

                                $scope.validateForm = function () {
                                    if (!$scope.container.form.$valid) {
                                        $scope.$broadcast('invalidForm');
                                        return false;
                                    }
                                    return true;
                                };

                                $scope.save = function () {
                                    if (!$scope.validateForm()) {
                                        return false;
                                    }
                                    config.prepareReadArguments($scope);
                                    var promise = models[config.kind].actions[$scope.args.action_id]($scope.args);

                                    promise.then(function (response) {
                                        $.extend($scope.entity, response.data.entity);
                                        var new_args = config.argumentLoader($scope);
                                        $.extend($scope.args, new_args);
                                        makeHistory();
                                        if (angular.isDefined(config.afterSave)) {
                                            config.afterSave($scope);
                                        }
                                        $scope.formSetPristine();
                                    }, function (response) {
                                        // here handle error...
                                        if (angular.isDefined(config.afterSaveError)) {
                                            config.afterSaveError($scope, response);
                                        }

                                    });

                                    return promise;
                                };

                                $scope.complete = function (response) {

                                    $.extend($scope.entity, response.data.entity);
                                    var newArgs = config.argumentLoader($scope);
                                    $.extend($scope.args, newArgs);
                                    makeHistory();
                                    if (angular.isDefined(config.afterComplete)) {
                                        config.afterComplete($scope);
                                    }
                                    if (config.closeAfterSave) {
                                        $timeout(function () {
                                            $scope.close();
                                        });
                                    }
                                    $scope.formSetPristine();
                                    console.log('modelsEditor.complete', $scope);

                                };

                                $scope.noComplete = function () {
                                    if (angular.isDefined(config.noComplete)) {
                                        config.noComplete($scope);
                                    }
                                };

                                $scope.completeError = function (response) {
                                    if (angular.isDefined(config.afterCompleteError)) {
                                        config.afterCompleteError($scope, response);
                                    }
                                };

                                $scope.close = function () {
                                    $scope.$close();
                                    if (config.afterClose) {
                                        config.afterClose($scope);
                                    }
                                };

                                if (angular.isDefined(config.scope)) {
                                    $.extend($scope, config.scope);
                                }

                                $scope.formBuilder = {
                                    '0': []
                                };

                                // if no accordions are defined, use the auto accordion builder
                                if (!angular.isDefined($scope.accordions)) {
                                    $scope.accordions = {
                                        closeOthers: true,
                                        groups: [{
                                            label: 'General',
                                            disabled: true,
                                            open: true
                                        }]
                                    };

                                    angular.forEach(config.fields, function (field) {
                                        if (field.is_structured && formInputTypes[field.type]) {

                                            if (!field.ui.initialLabel) {
                                                field.ui.initialLabel = field.ui.label;
                                            }
                                            $scope.accordions.groups.push({
                                                label: inflector((field.ui.initialLabel || field.code_name), 'humanize'),
                                                disabled: false,
                                                open: false
                                            });

                                            field.ui.label = false;

                                            var next = $scope.accordions.groups.length - 1;

                                            if (!angular.isDefined($scope.formBuilder[next])) {
                                                $scope.formBuilder[next] = [];
                                                $scope.formBuilder[next].push(field);
                                            }

                                            $scope.accordions.groups[0].disabled = false;
                                        } else {
                                            $scope.formBuilder['0'].push(field);
                                        }
                                    });

                                    angular.forEach($scope.accordions.groups, function (group, i) {
                                        if ($scope.formBuilder[i].length) {
                                            realTotal += 1;
                                        }
                                        if (found !== false) {
                                            return;
                                        }
                                        if ($scope.formBuilder[i].length) {
                                            group.open = true;
                                            found = group;
                                        } else {
                                            group.open = false;
                                        }
                                    });

                                    if (realTotal === 1) {
                                        found.disabled = true;
                                    }

                                } else {
                                    angular.forEach($scope.accordions.groups, function (group, i) {
                                        $scope.formBuilder[i] = [];
                                        if (!angular.isDefined(group.fields)) {
                                            var wait = false;
                                            angular.forEach(config.fields, function (field) {
                                                if (wait) {
                                                    return;
                                                }
                                                if (!done[field.code_name]) {
                                                    done[field.code_name] = 1;
                                                    if (field.is_structured) {
                                                        wait = true;
                                                    }

                                                    $scope.formBuilder[i].push(field);
                                                }
                                            });
                                        } else {
                                            angular.forEach(group.fields, function (field_key) {
                                                if (!done[field_key]) {
                                                    field = config.keyedFields[field_key];
                                                    $scope.formBuilder[i].push(field);
                                                    done[field_key] = 1;
                                                }
                                            });
                                        }
                                    });
                                }

                                // call config constructor, needed for posible after variable setup configurations
                                config.defaultInit($scope);
                                config.init($scope);
                                console.log('modelsEditor.scope', $scope);
                                makeHistory();

                                $scope.$on('$destroy', function () {
                                    config.getScope = undefined;
                                });

                            };

                            ctrl.$inject = ['$scope'];

                            opener[fn]({
                                templateUrl: 'core/models/manage.html',
                                controller: ctrl
                            });

                            return this;
                        }
                    };

                    return modelsEditorInstance;

                }
            };

            return modelsEditor;

        }).factory('modelsConfig', function () {
            // depency config loader
            var callbacks = [];
            return function (callback) {
                if (callback === true) {
                    return callbacks;
                }
                callbacks.push(callback);
            };
        }).factory('models', function (endpoint, modelsMeta, $injector, modelsConfig, helpers, $q, GLOBAL_CONFIG) {
            // models depency should never be included directly or indirectly, because its depency on modelsMeta
            var models = {}, // all model instances
                modelCreate = function (kind) {
                    // creates a new service based on kind
                    // it will map every action into function which can be called in this way: models['12'].actions.search() etc.
                    var config = {},
                        service = {
                            kind: kind,
                            actions: {},
                            getCacheKey: function (key) {
                                return this.kind + '_' + key;
                            },
                            removeCache: function (key) {
                                return endpoint.removeCache(this.getCacheKey(key));
                            },
                            getCache: function (key) {
                                return endpoint.getCache(this.getCacheKey(key));
                            },
                            get: function (key) {
                                if (angular.isDefined(this.actions.search)) {
                                    return this.actions.search({
                                        search: {
                                            keys: [key]
                                        }
                                    });
                                }

                                console.error('get() relies on actions.search action. use actions.read() instead.');
                            },
                            paginate: function (config) {
                                var that = this,
                                    theConfig = {
                                        args: {
                                            search: {}
                                        },
                                        config: {}
                                    },
                                    searchAction = modelsMeta.getActionArguments(config.kind, 'search'),
                                    paginate = {
                                        loading: false,
                                        more: null,
                                        cursor: null,
                                        args: theConfig.args,
                                        load: function () {
                                            var promise;
                                            if (this.loading || this.more === false) {
                                                return false;
                                            }
                                            if (!theConfig.args.search.options) {
                                                theConfig.args.search.options = {};
                                            }
                                            theConfig.args.search.options.start_cursor = this.cursor;
                                            this.loading = true;
                                            promise = that.actions[theConfig.action ? theConfig.action : 'search'](theConfig.args, theConfig.config);
                                            promise.then(function (response) {
                                                paginate.more = response.data.more;
                                                paginate.cursor = response.data.cursor;
                                                if (angular.isFunction(config.complete)) {
                                                    config.complete.call(this, response);
                                                }
                                            })['finally'](function () {
                                                paginate.loading = false;
                                            });
                                            return promise;
                                        }
                                    };
                                theConfig.args.search = searchAction.search['default'];
                                if (angular.isDefined(config.args)) {
                                    helpers.merge(config.args, theConfig.args);
                                    $.extend(theConfig, config);
                                }
                                return paginate;
                            },
                            reader: function (config) {
                                // reader instance that internally tracks the reader next read arguments.
                                // params provided are config, access, and callback
                                // and path to the structure that the reader will inject/read data
                                if (!angular.isArray(config.access)) {
                                    console.error('path must be array, ' + typeof config.access + ' given');
                                    return;
                                }
                                var fields,
                                    canLoadMore = function (nextReadArguments) {
                                        return helpers.getProperty(nextReadArguments, fields.join('.') + '.config.more');
                                    },
                                    init = function (access) {
                                        fields = [];
                                        angular.forEach(access, function (path) {
                                            if (isNaN(parseInt(path, 10))) {
                                                fields.push(path);
                                            }
                                        });
                                    },
                                    reader;

                                // fields are now _images, pricetags, _product, _instances
                                init(config.access);

                                reader = {
                                    next: null,
                                    loading: false,
                                    access: config.access,
                                    more: canLoadMore(config.next),
                                    config: config,
                                    state: function (config) {
                                        this.next = config.next;
                                        if (angular.isDefined(config.access)) {
                                            this.access = config.access;
                                            init(this.access);
                                        }
                                        if (angular.isDefined(config.more)) {
                                            this.more = config.more;
                                        } else {
                                            this.more = canLoadMore(this.next);
                                        }
                                    },
                                    setNextReadArguments: function (nextReadArguments) {
                                        this.next = nextReadArguments;
                                        this.more = canLoadMore(this.next);
                                    },
                                    setAccess: function (access) {
                                        this.access = access;
                                        init(access);
                                        this.more = canLoadMore(this.next);
                                    },
                                    load: function () {
                                        if (!this.more || this.loading) {
                                            return false;
                                        }
                                        var that = this,
                                            next = that.next,
                                            promise;

                                        if (!next) {
                                            next = angular.copy(config.next);
                                        }

                                        this.loading = true;

                                        promise = (config.read ? config.read(next) : models[config.kind].actions.read({
                                            key: config.key,
                                            read_arguments: next
                                        }));

                                        promise.then(function (response) {
                                            var getAccess = [],
                                                items,
                                                loadedNext;
                                            angular.forEach(that.access, function (part) {
                                                if (!isNaN(parseInt(part, 10))) {
                                                    part = 0;
                                                }
                                                getAccess.push(part);
                                            });
                                            items = helpers.getProperty(response.data.entity, getAccess);

                                            if (angular.isFunction(config.complete)) {
                                                config.complete(items);
                                            }

                                            loadedNext = response.data.entity._next_read_arguments;
                                            that.more = canLoadMore(loadedNext);

                                            if (that.more) {
                                                that.next = response.data.entity._next_read_arguments;
                                            }
                                        })['finally'](function () {
                                            reader.loading = false;
                                        });

                                        return promise;
                                    }
                                };

                                return reader;

                            }
                        };

                    service.config = config;
                    angular.forEach(modelsMeta.getActions(kind), function (action, action_key) {
                        service.actions[action_key] = function (args, overrideConfig) {
                            var defaultArgs = modelsMeta.getDefaultActionArguments(kind, action_key),
                                defaults = angular.copy(config),
                                cache_key;

                            $.extend(defaultArgs, args);
                            if (angular.isDefined(overrideConfig)) {
                                if (overrideConfig.merge) {
                                    $.extend(defaults, overrideConfig);
                                } else {
                                    defaults = overrideConfig;
                                }
                            }

                            cache_key = config.cache;
                            if (angular.isDefined(defaults) && defaults.cache) {
                                cache_key = defaults.cache;
                            }
                            if (cache_key === true) {
                                // btoa is base64encode built-in, if cache key is true then the cache key will be autogenerated
                                cache_key = kind + '_' + action_key + '_' + window.btoa(angular.toJson(defaultArgs));
                            }
                            if (!angular.isDefined(cache_key) || cache_key === false) {
                                return endpoint.post(action_key, kind, defaultArgs, defaults);
                            }
                            delete defaults.cache;
                            return endpoint.cached(cache_key, action_key, kind, defaultArgs, defaults);

                        };
                    });
                    return service;
                };

            models.initialized = false;
            models.init = function () {
                if (models.initialized === true) {
                    return;
                }

                var modelsInfo = $injector.get('modelsInfo'),
                    callbacks;

                if (!angular.isDefined(modelsInfo['0'])) {
                    return;
                }

                angular.forEach(modelsInfo, function (meta, kind) {
                    models[kind] = modelCreate(kind);
                });

                callbacks = modelsConfig(true);
                angular.forEach(callbacks, function (callback) {
                    callback(models);
                });

                models.initialized = true;
            };

            // expose models to window for debugging @todo remove when in production
            if (GLOBAL_CONFIG.debug) {
                window._models = models;
            }

            return models;

        });
}());
(function () {
    'use strict';
    angular.module('app')
        .controller('RecordListingCtrl', function ($scope, models, $modal) {

            var config = $scope.historyConfig,
                loaded = false,
                defaultReaderOpts = {
                    access: ['_records'],
                    key: config.key,
                    next: {
                        _records: {
                            config: {
                                more: true,
                                search: {
                                    orders: [{
                                        field: 'logged',
                                        operator: 'desc'
                                    }]
                                }
                            }
                        }
                    },
                    kind: config.kind,
                    complete: function (records) {
                        $scope.history.records.extend(records);
                    }
                };

            $.extend(defaultReaderOpts, config.reader);

            $scope.history = {
                records: [],
                reader: models[config.kind].reader(defaultReaderOpts),
                view: function (record) {
                    $modal.open({
                        templateUrl: 'core/models/manage.html',
                        controller: function ($scope) {
                            $scope.record = record;
                            $scope.dialog = {};
                            $scope.dialog.templateBodyUrl = 'core/record/view_body.html';
                            $scope.dialog.toolbar = {
                                hideSave: true,
                                title: 'Log for date  ' + record.logged
                            };
                            $scope.close = function () {
                                $scope.$close();
                            };
                        }
                    });
                }
            };

            $scope.$watch('accordion.open', function (opened, oldState) {
                if (opened && !loaded && $scope.history.reader.config.key) {
                    $scope.history.reader.load();
                    loaded = true;
                }
            });

            $scope.$watch('entity.key', function (old, neww) {
                if (old !== neww) {
                    $scope.history.reader.config.key = neww;
                }
            });

        }).factory('recordAccordion', function () {
            return {
                attach: function (accordions) {
                    accordions.groups.push({
                        label: 'History',
                        key: 'history',
                        open: false,
                        include: 'core/record/list.html'
                    });
                }
            };
        });
}());(function () {
    'use strict';
    angular.module('app').run(function (helpers) {
        helpers.responsive = {
            isTouch: function () {
                return Modernizr.touch;
            },
            isMobile: function () {
                return $('#is-mobile').css('visibility') === 'visible';
            },
            isTablet: function () {
                return $('#is-tablet').css('visibility') === 'visible';
            },
            isDesktop: function () {
                return !this.isMobile();
            },
            isLandscape: function () {
                return $('#is-landscape').css('visibility') === 'visible';
            },
            isPortrait: function () {
                return !this.isLandscape();
            }
        };
    });
}());
(function () {
    'use strict';
    angular.module('app')
        .directive('selectInput', function ($simpleDialog, $mdTheming,
            $mdInkRipple, $$rAF, $mdConstant, underscoreTemplate, $timeout, $parse, helpers, $q) {
            return {
                replace: true,
                transclude: true,
                require: ['ngModel', '^?mdInputContainer'],
                templateUrl: 'core/select/input.html',
                scope: true,
                link: function (scope, element, attrs, ctrls) {
                    var ngModel = ctrls[0],
                        containerCtrl = ctrls[1],
                        items = scope.$eval(attrs.items),
                        view = scope.$eval(attrs.view),
                        search = scope.$eval(attrs.search),
                        multiple = scope.$eval(attrs.multiple),
                        placeholder = attrs.placeholder,
                        select = {},
                        timeout,
                        ngModelPipelineCheckValue,
                        isErrorGetter;
                    containerCtrl.input = element;
                    $mdTheming(element);
                    ngModelPipelineCheckValue = function (arg) {
                        containerCtrl.setHasValue(!ngModel.$isEmpty(arg));
                        return arg;
                    };
                    isErrorGetter = containerCtrl.isErrorGetter || function () {
                        return ngModel.$invalid && ngModel.$touched;
                    };
                    scope.$watch(isErrorGetter, containerCtrl.setInvalid);

                    ngModel.$parsers.push(ngModelPipelineCheckValue);
                    ngModel.$formatters.push(ngModelPipelineCheckValue);

                    element.on('click', function (ev) {
                        containerCtrl.setFocused(true);
                    });
                    scope.$on('$destroy', function () {
                        containerCtrl.setFocused(false);
                        containerCtrl.setHasValue(false);
                        containerCtrl.input = null;
                    });
                    select.getHash = function (item) {
                        return (angular.isObject(item) ? item.key : item);
                    };
                    select.placeholder = placeholder;
                    select.loading = false;
                    select.multiple = multiple;
                    select.items = [];
                    select.find = function (value) {
                        if (value === null) {
                            return undefined;
                        }
                        var active,
                            missing,
                            get = function (val) {
                                var i,
                                    found;
                                if (!angular.isObject(select.items[0])) {
                                    i = select.items.indexOf(val);
                                    if (i !== -1) {
                                        found = select.items[i];
                                    }
                                } else {
                                    found = _.findWhere(select.items, {key: val});
                                }
                                return found;
                            };
                        if (select.multiple) {
                            missing = [];
                            active = [];
                            if (value && value.length) {
                                angular.forEach(value, function (val) {
                                    var gets = get(val);
                                    if (angular.isUndefined(gets)) {
                                        missing.push(val);
                                    } else {
                                        active.push(gets);
                                    }
                                });
                            }
                        } else {
                            active = get(value);
                            if (angular.isUndefined(active)) {
                                missing = value;
                            }
                        }
                        if (angular.isDefined(missing) && missing.length && select.search && select.search.ready) {
                            select.search.ready.then(function () {
                                if (select.search.missing) {
                                    select.search.missing(missing);
                                }
                            });
                        }
                        return active;
                    };
                    select.getActive = function () {
                        select.item = select.find(ngModel.$modelValue);
                        return select.item;
                    };
                    select.setItems = function (items) {
                        select.items = items;
                        select.collectActive();
                    };
                    select.isSelected = function (item) {
                        var hash = select.getHash(item);
                        if (select.multiple) {
                            return $.inArray(hash, ngModel.$modelValue) !== -1;
                        }
                        return ngModel.$modelValue === hash;
                    };
                    select.anyChecks = function () {
                        return _.some(select.multipleSelection);
                    };
                    select.multipleSelection = {};
                    select.multipleSelect = function (item) {
                        var hash = select.getHash(item),
                            hasIt = select.multipleSelection[hash],
                            already = ngModel.$modelValue || [],
                            selected = $.inArray(hash, ngModel.$modelValue) !== -1;
                        if (!angular.isArray(select.item)) {
                            select.item = [];
                        }
                        if (hasIt) {
                            if (!selected) {
                                already.push(hash);
                                select.item.push(item);
                            }
                        } else {
                            if (selected) {
                                already.remove(hash);
                                select.item.remove(item);
                            }
                        }
                        ngModel.$setViewValue(already);
                    };

                    select.collectActive = function () {
                        angular.forEach(select.items, function (item) {
                            var hash = select.getHash(item);
                            if (angular.isUndefined(select.multipleSelection[hash])
                                    && $.inArray(hash, ngModel.$modelValue) !== -1) {
                                select.multipleSelection[hash] = true;
                            }
                        });
                    };

                    select.isChecked = function (item) {
                        return select.multipleSelection[select.getHash(item)];
                    };
                    select.select = function (item) {
                        var val = select.getHash(item);
                        ngModel.$setViewValue(val);
                        select.item = item;
                        select.close();
                    };
                    select.close = angular.noop;
                    select.opened = false;
                    select.open = function ($event) {
                        if (element.attr('disabled')) {
                            return;
                        }
                        if (select.search) {
                            select.search.query = {};
                        }
                        select.multipleSelection = {};
                        select.collectActive();

                        var attachTo = element.parents('md-content:first');

                        if (!attachTo.length) {
                            attachTo = element.parents('.fixed-height:first');
                        }

                        $simpleDialog.show({
                            template: underscoreTemplate.get('core/select/choices.html')({select: select}),
                            targetEvent: $event,
                            parent: attachTo,
                            onBeforeHide: function (dialogEl, options) {
                                $(window).off('resize', options.resize);
                            },
                            onBeforeShow: function (dialogEl, options) {
                                options.parent.css('overflow-wrap', options.parent.css('overflow-wrap') === 'normal' ? 'break-word' : 'normal');
                                var nextDefer = $q.defer(),
                                    nextPromise = nextDefer.promise,
                                    animateSelect = function () {
                                        var target = element.parents('md-input-container:first');
                                        options.resize = function () {
                                            var targetPosition = target.position(),
                                                targetPaddingLeft = parseInt(target.css('paddingLeft'), 10),
                                                parent = options.parent,
                                                parentHeight = options.parent.height(),
                                                parentPosition = parent.position(),
                                                paddingTop = parseInt(parent.css('padding-top'), 10) || 16,
                                                paddingBottom = parseInt(parent.css('padding-bottom'), 10) || 16,
                                                scrollElement = dialogEl.find('md-content'),
                                                maxTop = paddingTop,
                                                active = dialogEl.find('.list-row--is-active'),
                                                newTop,
                                                totalHeight;
                                            targetPosition.left += targetPaddingLeft;
                                            dialogEl.width(target.width());
                                            if ((dialogEl.height() > parentHeight)
                                                    || (scrollElement.prop('scrollHeight') > parentHeight)) {
                                                dialogEl.css({
                                                    top: maxTop,
                                                    left: targetPosition.left
                                                }).height(options.parent.height() - (paddingBottom + paddingTop));
                                            } else {
                                                dialogEl.css(targetPosition);
                                                if (active.length) {
                                                    // position the selection at center of active item
                                                    newTop = targetPosition.top - (active.position().top - element.height() / 3);
                                                } else {
                                                    // position the div at the center if no item is selected
                                                    newTop = targetPosition.top - (dialogEl.height() / 2);
                                                }
                                                if (newTop > maxTop) { // if newTop is larger then maxTop, attempt to check if that calculated top is possible
                                                    totalHeight = newTop + dialogEl.height(); // if the top + dialogEl exceedes parentHeight
                                                    if (totalHeight > parentHeight) {
                                                        newTop = newTop - (totalHeight - parentHeight); // new top is calculated by substracting the extra space from the entire space
                                                        if (newTop < maxTop) {
                                                            newTop = maxTop;
                                                        }
                                                    }
                                                    dialogEl.css('top', newTop);
                                                } else {
                                                    dialogEl.css('top', maxTop);
                                                }
                                            }
                                            if (active.length && !select.multiple) {
                                                scrollElement.scrollTop(scrollElement.scrollTop() - scrollElement.offset().top + active.offset().top);
                                            }
                                        };
                                        options.resize();
                                        $(window).on('resize', function () {
                                            setTimeout(options.resize, 100);
                                        });

                                        dialogEl.css($mdConstant.CSS.TRANSFORM, 'scale(' +
                                            Math.min(target.width() / dialogEl.width(), 1.0) + ',' +
                                            Math.min(target.height() / dialogEl.height(), 1.0) + ')')
                                            .on($mdConstant.CSS.TRANSITIONEND, function (ev) {
                                                if (ev.target === dialogEl[0]) {
                                                    select.opened = true;
                                                    nextDefer.resolve();
                                                    if (select.search) {
                                                        dialogEl.find('input[type="search"]').focus();
                                                    }
                                                }
                                            });
                                        $$rAF(function () {
                                            dialogEl.addClass('transition-in');
                                            dialogEl.css($mdConstant.CSS.TRANSFORM, '');
                                        });

                                    };

                                $$rAF(animateSelect);

                                return nextPromise;
                            },
                            controller: function ($scope) {
                                select.close = function () {
                                    $simpleDialog.hide();
                                };
                                $scope.select = select;
                                $scope.$on('$destroy', function () {
                                    select.opened = false;
                                    containerCtrl.setFocused(false);
                                });
                            }
                        });
                    };
                    select.view = view;
                    if (!view) {
                        select.view = function (item) {
                            return angular.isObject(item) ? item.name : item;
                        };
                    }
                    ngModel.$formatters.push(function (value) {
                        select.item = select.find(value);
                        return value;
                    });

                    select.getFindTerm = function () {
                        return $parse(select.search.filterProp)(select.search.query);
                    };

                    if (search) {
                        select.search = {
                            query: {},
                            delay: 200,
                            doFind: function () {
                                var term = select.getFindTerm();
                                if (timeout) {
                                    clearTimeout(timeout);
                                }
                                if (select.search.find) {
                                    timeout = setTimeout(function () {
                                        select.search.find(term);
                                    }, select.search.delay);
                                }

                                $timeout(function () {
                                    $(window).triggerHandler('resize');
                                });
                            }
                        };
                        $.extend(select.search, search);
                        select.search.filterProp = (select.search.filterProp ? select.search.filterProp : 'name');
                        if (!select.search.model) {
                            select.search.model = 'select.search.query' + ('.' + select.search.filterProp);
                        }
                        if (!select.search.filter) {
                            select.search.filter = '| filter:select.search.query' + ((items && angular.isString(items[0])) ? ('.' + select.search.filterProp) : '');
                        }
                    }
                    select.setItems(items);
                    scope.$watchGroup([attrs.items + '.length', attrs.items], function (neww, old) {
                        if (neww[0] !== old[0] || neww[1] !== old[1]) {
                            select.setItems(scope.$eval(attrs.items));
                            select.getActive();
                            if (select.opened) {
                                $timeout(function () {
                                    $(window).triggerHandler('resize');
                                });
                            }
                        }
                    });

                    scope.select = select;
                }
            };
        });
}());(function () {
    'use strict';
    angular.module('app').directive('imageSlider', function ($timeout, $parse) {
        return {
            restrict: 'A',
            link: function (scope, element, attrs) {
                var callback = $parse(attrs.imageSliderLoadMore),
                    parent = element.parent('.image-slider-outer:first'),
                    steadyScroll,
                    anyMore = true,
                    tryToLoadSteady = function (values, done) {
                        if (!anyMore) {
                            return false;
                        }
                        anyMore = false;
                        callback(scope, {
                            callback: function (response, state) {
                                done();
                                anyMore = state;
                            }
                        });
                    },
                    measure = function () {
                        var tw = 0;
                        element.find('.image-slider-item').filter(function () {
                            return $(this).css('display') !== 'none';
                        }).each(function () {
                            tw += $(this).width();
                        });

                        element.width(Math.ceil(tw));
                    },
                    resize = function () {
                        var height = parent.parents('.fixed-height:first').height(),
                            bar = parent.parents('.modal:first').find('.new-pricetag-bar');
                        if (bar.length) {
                            height -= bar.outerHeight();
                        }
                        if (height) {
                            parent.height(height);
                            scope.$broadcast('imageSliderResized', height);
                        }
                    };

                resize();
                scope.$on('modalResize', resize);
                scope.$on('reMeasureImageSlider', function () {
                    resize();
                    measure();
                });

                scope.$on('readyImageSlider', function () {
                    resize();
                    measure();
                    //parent.scroll(tryToLoad);
                    steadyScroll = new Steady({
                        throttle: 100,
                        scrollElement: parent.get(0),
                        handler: tryToLoadSteady
                    });

                    steadyScroll.addTracker('checkLeft', function () {
                        if (!callback) {
                            return;
                        }
                        var p = parent.get(0),
                            maxscroll,
                            sense = maxscroll - parent.scrollLeft();
                        if (!p) {
                            steadyScroll.stop();
                            return;
                        }
                        maxscroll = p.scrollWidth - p.clientWidth;
                        if (sense < 300) {
                            return true;
                        }
                        return false;
                    });

                    steadyScroll.addCondition('checkLeft', true);
                    parent.data('steady', steadyScroll);
                });

                scope.$on('$destroy', function () {
                    if (steadyScroll) {
                        steadyScroll.stop();
                        parent.data('steady', undefined);
                    }
                });
            }
        };
    }).directive('sliderImage', function ($timeout, helpers, GLOBAL_CONFIG) {
        return {
            restrict: 'A',
            link: function (scope, element, attrs) {
                var image = scope.$eval(attrs.sliderImage),
                    run = function () {
                        var bar = element.parents('.modal:first').find('.new-pricetag-bar'),
                            newHeight = element.parents('.fixed-height:first').innerHeight() - window.SCROLLBAR_WIDTH - (bar.length ? bar.outerHeight() : 0),
                            newWidth = Math.ceil(newHeight * image.proportion),
                            imageSize = helpers.closestLargestNumber(GLOBAL_CONFIG.imageSizes, newHeight),
                            originalNewHeight = newHeight;
                        newWidth = helpers.newWidthByHeight(newWidth, originalNewHeight, newHeight);
                        element.attr('src', image.serving_url + '=s' + imageSize)
                            .width(newWidth)
                            .height(newHeight);

                        element.parents('.image-slider-item:first')
                            .width(newWidth)
                            .height(newHeight);
                    },
                    resize = function () {
                        run();
                        scope.$emit('reMeasureImageSlider');
                    };

                $timeout(function () {
                    run();
                    if (scope.$last) {
                        scope.$emit('readyImageSlider');
                    }
                });
                scope.$on('modalResize', resize);
                scope.$on('itemDelete', function () {
                    $timeout(resize);
                });

            }
        };
    });
}());
﻿/**
 * AngularJS directives for social sharing buttons - Facebook Like, Google+, Twitter and Pinterest
 * @author Jason Watmore <jason@pointblankdevelopment.com.au> (http://jasonwatmore.com)
 * @version 1.0.0
 * Refactored code
 */
(function () {
    'use strict';
    angular.module('app').directive('fbLike', ['$window', '$rootScope', 'GLOBAL_CONFIG',
        function ($window, $rootScope, GLOBAL_CONFIG) {
            return {
                restrict: 'A',
                scope: {
                    fbLike: '=?'
                },
                link: function (scope, element, attrs) {
                    var watchAdded = false,
                        renderLikeButton = function () {
                            if (!!attrs.fbLike && !scope.fbLike && !watchAdded) {
                                // wait for data if it hasn't loaded yet
                                watchAdded = true;
                                var unbindWatch = scope.$watch('fbLike', function (newValue, oldValue) {
                                    if (newValue) {
                                        renderLikeButton();
                                        // only need to run once
                                        unbindWatch();
                                    }

                                });
                            } else {
                                element.html('<div class="fb-like"' + (!!scope.fbLike ? ' data-href="' + scope.fbLike + '"' : '') + ' data-layout="button_count" data-action="like" data-show-faces="true" data-share="true"></div>');
                                $window.FB.XFBML.parse(element.parent()[0]);
                            }
                        };
                    if (!$window.FB) {
                        // Load Facebook SDK if not already loaded
                        $.getScript('//connect.facebook.net/en_US/sdk.js', function () {
                            $window.FB.init({
                                appId: GLOBAL_CONFIG.social.facebook.id,
                                xfbml: true,
                                version: 'v2.0'
                            });
                            renderLikeButton();
                        });
                    } else {
                        renderLikeButton();
                    }
                }
            };
        }]).directive('gplus', ['$window', function ($window) {
        return {
            restrict: 'A',
            link: function (scope, element, attrs) {
                var renderPlusButton = function () {
                    element.html('<div class="g-plusone" data-size="medium"></div>');
                    element.find('.g-plusone').attr('data-href', attrs.gplus);
                    $window.gapi.plusone.go(element.parent()[0]);
                };
                if (!$window.gapi) {
                    // Load Google SDK if not already loaded
                    $.getScript('//apis.google.com/js/platform.js', function () {
                        renderPlusButton();
                    });
                } else {
                    renderPlusButton();
                }
            }
        };
    }]).directive('tweet', ['$window', function ($window) {
        return {
            restrict: 'A',
            scope: {
                tweet: '=',
                tweetUrl: '='
            },
            link: function (scope, element, attrs) {
                var watchAdded = false,
                    renderTweetButton = function () {
                        if (!scope.tweet && !watchAdded) {
                            // wait for data if it hasn't loaded yet
                            watchAdded = true;
                            var unbindWatch = scope.$watch('tweet', function (newValue, oldValue) {
                                if (newValue) {
                                    renderTweetButton();

                                    // only need to run once
                                    unbindWatch();
                                }
                            });
                        } else {
                            element.html('<a href="https://twitter.com/share" class="twitter-share-button">Tweet</a>');
                            element.find('a').first().attr({
                                'data-url': scope.tweetUrl,
                                'data-text': scope.tweet
                            });
                            $window.twttr.widgets.load(element.parent()[0]);
                        }
                    };
                if (!$window.twttr) {
                    // Load Twitter SDK if not already loaded
                    $.getScript('//platform.twitter.com/widgets.js', function () {
                        renderTweetButton();
                    });
                } else {
                    renderTweetButton();
                }
            }
        };
    }]).directive('pinIt', ['$window', '$location', function ($window, $location) {
        return {
            restrict: 'A',
            scope: {
                pinIt: '=',
                pinItUrl: '=',
                pinItImage: '='
            },
            link: function (scope, element, attrs) {
                var watchAdded = false,
                    renderPinItButton = function () {
                        if (!scope.pinIt && !watchAdded) {
                            // wait for data if it hasn't loaded yet
                            watchAdded = true;
                            var unbindWatch = scope.$watch('pinIt', function (newValue, oldValue) {
                                if (newValue) {
                                    renderPinItButton();

                                    // only need to run once
                                    unbindWatch();
                                }
                            });
                        } else {
                            scope.pinItUrl = scope.pinItUrl || $location.absUrl();
                            element.html('<a href="//www.pinterest.com/pin/create/button/?url=' + encodeURIComponent(scope.pinItUrl) + '&media=' + scope.pinItImage + '&description=' + encodeURIComponent(scope.pinIt) + '" data-pin-do="buttonPin" data-pin-config="beside"><img src="//assets.pinterest.com/images/pidgets/pinit_fg_en_rect_gray_20.png" /></a>');
                            window.parsePins(element.parent()[0]);
                        }
                    };
                if (!$window.parsePins) {
                    // Load Pinterest SDK if not already loaded
                    (function (d) {
                        var f = d.getElementsByTagName('SCRIPT')[0],
                            p = d.createElement('SCRIPT');
                        p.type = 'text/javascript';
                        p.async = true;
                        p.src = '//assets.pinterest.com/js/pinit.js';
                        p['data-pin-build'] = 'parsePins';
                        p.onload = function () {
                            if (!!$window.parsePins) {
                                renderPinItButton();
                            } else {
                                setTimeout(p.onload, 100);
                            }
                        };
                        f.parentNode.insertBefore(p, f);
                    }($window.document));
                } else {
                    renderPinItButton();
                }
            }
        };
    }]);

}());
// Version (see package.json)
// AngularJS simple file upload directive
// this directive uses an iframe as a target
// to enable the uploading of files without
// losing focus in the ng-app.
//
// <div ng-app="app">
//   <div ng-controller="mainCtrl">
//    <form ng-attr-action="/uploads"
//      ng-upload="completed(content)">
//      ng-upload-loading="loading()"
//      <input type="file" name="avatar"></input>
//      <input type="submit" value="Upload"
//         ng-disabled="$isUploading"></input>
//    </form>
//  </div>
// </div>
//
//  angular.module('app', ['ngUpload'])
//    .controller('mainCtrl', function($scope) {
//      $scope.loading = function() {
//        console.log('loading...');
//      }
//      $scope.completed = function(content) {
//        console.log(content);
//      };
//  });
//
angular.module('app')
    .directive('uploadSubmit', ["$parse", function ($parse) {
        // Utility function to get the closest parent element with a given tag
        function getParentNodeByTagName(element, tagName) {
            element = angular.element(element);
            var parent = element.parent();
            tagName = tagName.toLowerCase();

            if (parent && parent[0].tagName.toLowerCase() === tagName) {
                return parent;
            } else {
                return !parent ? null : getParentNodeByTagName(parent, tagName);
            }
        }
        return {
            restrict: 'AC',
            link: function (scope, element, attrs) {
                element.bind('click', function ($event) {
                    // prevent default behavior of click
                    if ($event) {
                        $event.preventDefault();
                        $event.stopPropagation();
                    }

                    if (element.attr('disabled')) {
                        return;
                    }
                    var form = getParentNodeByTagName(element, 'form');
                    form.triggerHandler('submit');
                    form[0].submit();
                });
            }
        };
    }])
    .directive('ngUpload', ["$log", "$parse", "$document", "$rootScope", "errorHandling", "modelsUtil",
        function ($log, $parse, $document, $rootScope, errorHandling, modelsUtil) {
            var iframeID = 1;
            // Utility function to get meta tag with a given name attribute
            function getMetaTagWithName(name) {
                var head = $document.find('head');
                var match;

                angular.forEach(head.find('meta'), function (element) {
                    if (element.getAttribute('name') === name) {
                        match = element;
                    }
                });

                return angular.element(match);
            }

            return {
                require: 'form',
                restrict: 'AC',
                link: function (scope, element, attrs, ctrl) {
                    // Give each directive instance a new id
                    iframeID++;

                    var formController = ctrl;

                    function setLoadingState(state) {
                        scope.$isUploading = state;
                    }

                    var options = {};
                    // Options (just 1 for now)
                    // Each option should be prefixed with 'upload-options-' or 'uploadOptions'
                    // {
                    //    // add the Rails CSRF hidden input to form
                    //    enableRailsCsrf: bool
                    // }
                    var fn = attrs.ngUpload ? $parse(attrs.ngUpload) : angular.noop;
                    var errorFn = attrs.ngUploadError ? $parse(attrs.ngUploadError) : angular.noop;
                    var loading = attrs.ngUploadLoading ? $parse(attrs.ngUploadLoading) : null;
                    var opts = scope.$eval(attrs.ngUploadOptions) || {};
                    var normalize = (angular.isDefined(opts.normalize) ? opts.normalize : true);

                    if (attrs.hasOwnProperty("uploadOptionsConvertHidden")) {
                        // Allow blank or true
                        options.convertHidden = attrs.uploadOptionsConvertHidden != "false";
                    }

                    if (attrs.hasOwnProperty("uploadOptionsEnableRailsCsrf")) {
                        // allow for blank or true
                        options.enableRailsCsrf = attrs.uploadOptionsEnableRailsCsrf != "false";
                    }

                    if (attrs.hasOwnProperty("uploadOptionsBeforeSubmit")) {
                        options.beforeSubmit = $parse(attrs.uploadOptionsBeforeSubmit);
                    }

                    element.attr({
                        'target': 'upload-iframe-' + iframeID,
                        'method': 'post',
                        'enctype': 'multipart/form-data',
                        'encoding': 'multipart/form-data'
                    });

                    var config = {
                        url: element.attr('action')
                    };

                    var iframe = angular.element(
                        '<iframe name="upload-iframe-' + iframeID + '" ' +
                        'border="0" width="0" height="0" ' +
                        'style="width:0px;height:0px;border:none;display:none">'
                    );

                    // If enabled, add csrf hidden input to form
                    if (options.enableRailsCsrf) {
                        var input = angular.element("<input />");
                        input.attr("class", "upload-csrf-token");
                        input.attr("type", "hidden");
                        input.attr("name", getMetaTagWithName('csrf-param').attr('content'));
                        input.val(getMetaTagWithName('csrf-token').attr('content'));

                        element.append(input);
                    }
                    element.after(iframe);

                    setLoadingState(false);
                    // Start upload
                    element.bind('submit', function uploadStart() {
                        // if form is invalid don't submit (e.g. keypress 13)
                        if (formController && formController.$invalid) return false;
                        // perform check before submit file
                        if (options.beforeSubmit && options.beforeSubmit(scope, {}) == false) return false;

                        // bind load after submit to prevent initial load triggering uploadEnd
                        iframe.bind('load', uploadEnd);

                        // If convertHidden option is enabled, set the value of hidden fields to the eval of the ng-model
                        if (options.convertHidden) {
                            angular.forEach(element.find('input'), function (el) {
                                var _el = angular.element(el);
                                if (_el.attr('ng-model') &&
                                    _el.attr('type') &&
                                    _el.attr('type') == 'hidden') {
                                    _el.attr('value', scope.$eval(_el.attr('ng-model')));
                                }
                            });
                        }

                        if (!scope.$$phase) {
                            scope.$apply(function () {
                                if (loading) loading(scope);
                                setLoadingState(true);
                            });
                        } else {
                            if (loading) loading(scope);
                            setLoadingState(true);
                        }

                        scope.$broadcast('ngUploadSubmit');
                        $rootScope.$broadcast('disableUI', true);

                    });

                    // Finish upload
                    function uploadEnd() {
                        // unbind load after uploadEnd to prevent another load triggering uploadEnd
                        iframe.unbind('load');
                        if (!scope.$$phase) {
                            scope.$apply(function () {
                                setLoadingState(false);
                            });
                        } else {
                            setLoadingState(false);
                        }
                        // Get iframe body contents
                        var bodyContent = (iframe[0].contentDocument ||
                            iframe[0].contentWindow.document).body;
                        var content;
                        try {
                            content = angular.fromJson(bodyContent.innerText || bodyContent.textContent);
                        } catch (e) {
                            // Fall back to html if json parse failed
                            content = bodyContent.innerHTML;
                            $log.warn('Response is not valid JSON');
                        }

                        var response = {
                                content: {
                                    data: content
                                }
                            },
                            noErrors = (content && angular.isObject(content) && !content.errors);
                        // if outside a digest cycle, execute the upload response function in the active scope
                        // else execute the upload response function in the current digest
                        if (normalize && noErrors) {
                            if (angular.isDefined(content.entities)) {
                                modelsUtil.normalizeMultiple(content.entities);
                            } else if (angular.isDefined(content.entity)) {
                                modelsUtil.normalize(content.entity);
                            }
                        }
                        if (noErrors) {
                            if (!scope.$$phase) {
                                scope.$apply(function () {
                                    fn(scope, response);
                                });
                            } else {
                                fn(scope, response);
                            }
                        } else {
                            if (!scope.$$phase) {
                                scope.$apply(function () {
                                    errorFn(scope, response);
                                });
                            } else {
                                errorFn(scope, response);
                            }
                        }



                        $rootScope.$broadcast('disableUI', false);

                        if (noErrors) {
                            scope.$broadcast('ngUploadComplete', content);
                        } else {
                            errorHandling.modal(content.errors);
                            scope.$broadcast('ngUploadCompleteError', content);
                        }


                    }
                }
            };
        }
    ]);
(function () {
    'use strict';
    // code for account
    angular.module('app').constant('LOGIN_PROVIDERS', {
        '1': 'Google',
        '2': 'Facebook'
    }).controller('AccountLoginStatusCtrl', function ($scope, $location, $state, modals) {
        var data = $location.search(),
            errors;
        if (data.success) {
            $state.go('home');
        } else {
            if (data.errors) {
                errors = JSON.parse(data.errors);
                if (errors) {
                    if (errors.action_denied) {
                        modals.alert('Action you tried to perform is forbidden for this account.', function () {
                            $state.go('home');
                        });
                    }
                }
            }
        }
    }).controller('LoginLinksCtrl', function ($scope, endpoint, currentAccount, models) {

        $scope.authorization_urls = {};
        if (currentAccount._is_guest === undefined || currentAccount._is_guest) {
            models['11'].actions.login({
                login_method: 'google'
            }).then(function (response) {
                $scope.authorization_urls = response.data.authorization_urls;
            });
        }

        $scope.login = function (type) {
            endpoint.removeCache('currentAccount');
            window.location.href = $scope.authorization_urls[type];
        };

    }).controller('AccountManagementCtrl', function ($scope, currentAccount, models, modelsUtil) {

        $scope.settings = function () {
            models['11'].manageModal(currentAccount);
        };
        $scope.logout = function () {
            models['11'].logout(currentAccount.key);
        };
    }).filter('formatLoginProivider', function (LOGIN_PROVIDERS) {
        return function (value) {
            var splits = value.split('-'),
                out = '';
            if (splits && splits[1]) {
                out = LOGIN_PROVIDERS[splits[1]];
            }
            return out;
        };
    }).run(function (modelsConfig, channelApi, channelNotifications, endpoint, $window, modelsEditor, modelsMeta, modelsUtil, $modal, helpers, modals, $q) {

        modelsConfig(function (models) {

            $.extend(models['11'], {
                channel: function () {
                    var promise = this.actions.create_channel(undefined, {cache: 'accountChannel', cacheType: 'memory'});
                    return promise.then(function (response) {
                        var token = response.data.token;
                        return {token: token, channel: channelApi.create(token)};
                    });
                },
                channelNotifications: function (config) {
                    var promise = this.channel();
                    return promise.then(function (response) {
                        var token = response.token;
                        return {token: token, channel: channelNotifications.create(token)};
                    });
                },
                adminManageModal: function (account) {
                    return this.manageModal(account);
                },
                manageModal: function (account) {
                    var that = this,
                        config = {
                            kind: this.kind,
                            templateBodyUrl: 'account/manage_body.html',
                            toolbar: {
                                templateActionsUrl: 'account/manage_actions.html'
                            },
                            argumentLoader: function ($scope) {
                                var disassociate = [],
                                    entity = $scope.entity,
                                    identity = _.findWhere(entity.identities, {primary: true}),
                                    obj = $scope.config.defaultArgumentLoader($scope);
                                angular.forEach(entity.identities,
                                    function (value) {
                                        if (!value.associated) {
                                            disassociate.push(value.identity);
                                        }
                                    });
                                $.extend(obj, {
                                    action_id: $scope.config.action,
                                    action_model: $scope.config.kind,
                                    primary_identity: identity.identity,
                                    disassociate: disassociate,
                                    key: entity.key
                                });

                                return obj;
                            },
                            init: function ($scope) {
                                var entity = $scope.entity,
                                    updateFields = ['state', 'ui.rule', 'created', 'updated'],
                                    updateState = function (newArgs) {
                                        angular.forEach(['args', 'entity'], function (p) {
                                            helpers.update($scope[p], newArgs, updateFields);
                                        });
                                    };
                                $scope.actions.sudo = function () {
                                    $modal.open({
                                        templateUrl: 'core/models/manage.html',
                                        controller: function ($scope) {
                                            var sudoFields = modelsMeta.getActionArguments(that.kind, 'sudo');
                                            $scope.dialog = {
                                                templateBodyUrl: 'account/administer.html'
                                            };
                                            $scope.args = {key: entity.key, state: entity.state};

                                            /*
                                            sudoFields.state.ui.placeholder = 'Set state';
                                            sudoFields.message.ui.placeholder = 'Message for the user';
                                            sudoFields.note.ui.placeholder = 'Note for administrators';
                                            */

                                            $scope.fields = [sudoFields.state, sudoFields.message, sudoFields.note];
                                            angular.forEach($scope.fields, function (field) {
                                                field.ui.writable = true;
                                            });

                                            $scope.container = {};
                                            $scope.save = function () {
                                                var promise;
                                                if (!$scope.container.form.$valid) {
                                                    return false;
                                                }
                                                promise = models[that.kind].actions.sudo($scope.args);
                                                promise.then(function (response) {
                                                    updateState(response.data.entity);
                                                });
                                                return promise;
                                            };
                                            $scope.close = function () {
                                                $scope.$close();
                                            };
                                        }
                                    });
                                };
                            },
                            scope: {
                                historyConfig: true,
                                isAssociated: function (ident) {
                                    return $.inArray(ident.identity, this.args.disassociate) === -1;
                                },
                                setPrimary: function (ident) {
                                    this.container.form.$setDirty();
                                    this.args.primary_identity = ident.identity;
                                },
                                disassociate: function (ident) {
                                    this.container.form.$setDirty();
                                    if (this.isAssociated(ident)) {
                                        this.args.disassociate.push(ident.identity);
                                    } else {
                                        this.args.disassociate.remove(ident.identity);
                                    }
                                },
                                actions: {},
                                accordions: {
                                    closeOthers: true,
                                    groups: [{
                                        label: 'General',
                                        disabled: false,
                                        open: true
                                    }, {
                                        label: 'Login Methods',
                                        disabled: false,
                                        open: false
                                    }]
                                }
                            }
                        };

                    modelsEditor.create(config).read(account, {
                        key: account.key
                    });

                },
                logout: function (accountKey) {
                    var that = this;
                    modals.confirm('Are you sure you want to logout?', function () {
                        that.actions.logout({
                            key: accountKey
                        }).then(function (response) {
                            endpoint.removeCache();
                            $window.location.reload(false);
                        });
                    });

                }
            });

        });

    });

}());
(function () {
    'use strict';
    angular.module('app')
        .controller('BuyerManagementCtrl', function ($scope, endpoint, currentAccount, models) {

            $scope.settings = function () {
                models['19'].manageModal(currentAccount.key);
            };

            $scope.manageCollection = function () {
                models['18'].manageModal(currentAccount.key);
            };

        }).controller('BuyOrdersCtrl', function ($scope, modals, modelsEditor, modelsMeta, models, modelsUtil, $rootScope, $state) {

            var carts = $state.current.name === 'buy-carts';

            $rootScope.pageTitle = 'Buyer ' + (carts ? 'Carts' : 'Orders');

            $scope.search = {
                results: [],
                pagination: {}
            };

            $scope.scrollEnd = {loader: false};

            $scope.view = function (order) {
                models['19'].current().then(function (response) {
                    return response.data.entity;
                }).then(function (buyer) {
                    models['34'].manageModal(order, order._seller, buyer, {
                        cartMode: carts
                    });
                });
            };

            models['19'].current().then(function (response) {
                var buyerEntity = response.data.entity;
                $scope.search.pagination = models['34'].paginate({
                    kind: '34',
                    args: {
                        search: {
                            ancestor: buyerEntity.key,
                            filters: [{field: 'state', operator: 'IN', value: (carts ? ['cart', 'checkout'] : ['completed', 'canceled'])}],
                            orders: [{field: 'updated', operator: 'desc'}, {field: 'key', operator: 'asc'}]
                        }
                    },
                    config: {
                        ignoreErrors: true
                    },
                    complete: function (response) {
                        var errors = response.data.errors;
                        if (errors) {
                            if (errors['not_found_' + buyerEntity.key]) {
                                modals.alert('You do not have any buyer information yet.');
                            }
                        } else {
                            $scope.search.results.extend(response.data.entities);
                        }
                    }
                });
                $scope.scrollEnd.loader = $scope.search.pagination;
                $scope.search.pagination.load();
            });
        }).directive('buyerAddressListView', function () {
            return {
                scope: {
                    val: '=buyerAddressListView'
                },
                templateUrl: 'buyer/address_list_view.html',
                controller: function ($scope) {
                    $scope.notEmpty = function (val) {
                        return angular.isString(val) || angular.isNumber(val);
                    };
                }
            };
        }).run(function ($window, modelsEditor, modelsMeta, $q, modelsConfig, currentAccount, endpoint) {

            modelsConfig(function (models) {

                $.extend(models['19'], {
                    current: function (args) {
                        if (!args) {
                            args = {};
                        }
                        args.account = currentAccount.key;
                        return this.actions.read(args, {
                            cache: this.getCacheKey('current'),
                            cacheType: 'memory'
                        });
                    },
                    manageModal: function (accountKey) {
                        var fields = modelsMeta.getActionArguments(this.kind, 'update'),
                            addressFields = fields.addresses.modelclass,
                            that = this,
                            config;
                        fields.addresses.ui = {
                            label: false,
                            specifics: {
                                listView: 'buyer-address-list-view',
                                sortFields: ['country', 'region', 'city', 'postal_code',
                                    'street', 'name', 'email', 'telephone'],
                                afterSave: function () {
                                    endpoint.removeCache(that.getCacheKey('current'));
                                },
                                beforeSave: function ($scope, info) {
                                    var promises = [],
                                        updatedAddress = $scope.args,
                                        promise;
                                    if (updatedAddress.region && (!updatedAddress._region || (updatedAddress.region !== updatedAddress._region.key))) {
                                        promise = models['13'].get(updatedAddress.region);
                                        promise.then(function (response) {
                                            if (response.data.entities.length) {
                                                updatedAddress._region = response.data.entities[0];
                                            }
                                        });
                                        promises.push(promise);
                                    }

                                    if (updatedAddress.country && (!updatedAddress._country || (updatedAddress.country !== updatedAddress._country.key))) {
                                        promise = models['12'].actions.search(undefined, {
                                            cache: true
                                        });
                                        promise.then(function (response) {
                                            if (response.data.entities.length) {
                                                var country = _.findWhere(response.data.entities, {
                                                    key: updatedAddress.country
                                                });
                                                if (angular.isDefined(country)) {
                                                    updatedAddress._country = country;
                                                }

                                            }

                                        });

                                        promises.push(promise);
                                    }
                                    if (promises.length) {
                                        return $q.all(promises);
                                    }

                                    return false;

                                }

                            }
                        };
                        /*
                        addressFields.country.ui.placeholder = 'Select address country (e.g., USA). This value is Required!';
                        addressFields.region.ui.placeholder = 'Select address region (e.g., California). This value is Optional!';
                        addressFields.city.ui.placeholder = 'Type in address city name (e.g., Beverly Hills). This value is Required!';
                        addressFields.postal_code.ui.placeholder = 'Type in address postal code (e.g., 90210). This value is Required!';
                        addressFields.street.ui.placeholder = 'Type in address street (e.g., Rodeo Drive). This value is Required!';
                        addressFields.name.ui.placeholder = 'Type in contact name (e.g., John Doe). This value is Required!'; // example
                        addressFields.email.ui.placeholder = 'Type in contact email (e.g., johndoe@example.com). This value is Optional.';
                        addressFields.telephone.ui.placeholder = 'Type in contact telephone number. Prefix phone with plus (+) sign, and all calling codes, starting with country code (e.g., ). This value is Optional.';
                        */
                        config = {
                            fields: [fields.addresses],
                            kind: this.kind,
                            action: 'update',
                            excludeFields: ['account', 'read_arguments'],
                            argumentLoader: function ($scope) {
                                var args = this.defaultArgumentLoader($scope);
                                args.account = accountKey;
                                return args;
                            }
                        };

                        modelsEditor.create(config).read({}, {
                            account: accountKey
                        });
                    }
                });

            });

        });
}());(function () {
    'use strict';
    angular.module('app').directive('catalogNewPricetag', function ($parse) {
        return {
            restrict: 'A',
            link: function (scope, element, attrs) {
                var callback = $parse(attrs.catalogNewPricetag);
                element.on('click', function (event) {
                    var offset = element.offset(),
                        x = event.pageX - offset.left,
                        y = event.pageY - offset.top,
                        parent = element.parents('.image-slider-item:first'),
                        width = parent.width(),
                        height = parent.height();

                    scope.$apply(function () {
                        callback(scope, {config: {
                            position_left: x,
                            position_top: y,
                            image_width: width,
                            image_height: height
                        }});
                    });
                });
            }
        };
    }).directive('catalogPricetagPosition', function ($timeout, models) { // directives that are not used anywhere else other than this context are defined in their own context
        return {
            link: function (scope, element, attr) {

                var pricetag = scope.$eval(attr.catalogPricetagPosition), resize = function () {
                    var pa = $(element).parents('.image-slider-item:first'),
                        sizes;

                    sizes = models['31'].calculatePricetagPosition(
                        pricetag.position_top,
                        pricetag.position_left,
                        pricetag.image_width,
                        pricetag.image_height,
                        pa.width(),
                        pa.height()
                    );

                    pricetag._position_top = sizes[0];
                    pricetag._position_left = sizes[1];

                    $(element).css({
                        top: pricetag._position_top,
                        left: pricetag._position_left,
                        visibility: 'visible'
                    });
                };
                $timeout(resize);
                scope.$on('modalResize', resize);
                scope.$watch(attr.catalogPricetagPosition + '._state', resize);
            }
        };
    }).directive('productInstanceListView', function ($compile) {
        return {
            scope: {
                val: '=productInstanceListView'
            },
            templateUrl: 'catalog/product/product_instance_list_view.html'
        };
    }).run(function (modelsEditor, modelsMeta, modelsConfig, $modal, modals, helpers, $q, $mdSidenav, $timeout) {

        modelsConfig(function (models) {
            var toggleMenu = function ($scope, id) {
                $scope.sidenavMenuID = id;
                $scope.notRipplable = ['.catalog-close-button', '.catalog-pricetag-link'];
                $scope.toggleMenu = function ($event) {
                    var it = $mdSidenav($scope.sidenavMenuID),
                        check = false,
                        target;
                    if ($event.target) {
                        target = $($event.target);
                        angular.forEach($scope.notRipplable, function (skip) {
                            if (target.is(skip) || target.parent().is(skip)) {
                                check = true;
                            }
                        });
                        if (check) {
                            return;
                        }
                    }
                    if (it.isOpen()) {
                        $scope.closeMenu();
                    } else {
                        $scope.openMenu();
                    }
                };
                $scope.closeMenu = function () {
                    $timeout(function () {
                        $mdSidenav($scope.sidenavMenuID).close();
                    });
                };
                $scope.openMenu = function () {
                    $timeout(function () {
                        $mdSidenav($scope.sidenavMenuID).open();
                    });
                };
            };
            $.extend(models['31'], {
                formatPublicSearchResults: function (results) {
                    angular.forEach(results, function (result) {
                        result._cover = {
                            serving_url: result.cover,
                            proportion: result.cover_proportion
                        };
                        result._seller_logo = {
                            serving_url: result.seller_logo,
                            proportion: 2.4
                        };
                    });
                },
                calculatePricetagPosition: function (ihp, ivp, iiw, iih, ciw, cih) {
                    /*  
                    ihp - Initial Horizontal Price Tag Position 
                    ivp - Initial Vertical Price Tag Position 
                    iiw - Initial Image Width  
                    iih - Initial Image Height  

                    ciw - Current Image Width  
                    cih - Current Image Height  
                    chp - Current Horizontal Price Tag Position  
                    cvp - Current Vertical Price Tag Position  
                    */
                    var chp = (ihp / iiw) * ciw,
                        cvp = (ivp / iih) * cih;
                    return [chp, cvp];
                },
                previewModal: function (key, config) {
                    config = helpers.alwaysObject(config);
                    config.hideAddToCart = true;
                    return this.viewModal(key, config);
                },
                viewProductModal: function (catalogKey, imageKey, pricetagKey, variantSignatureAsDicts, config) {
                    var readArguments = {
                            _seller: {},
                            _images: {
                                config: {
                                    keys: [imageKey]
                                },
                                pricetags: {
                                    config: {
                                        keys: [pricetagKey]
                                    },
                                    _product: {
                                        _category: {}
                                    }
                                }
                            }
                        };
                    config = helpers.alwaysObject(config);
                    this.actions.read({
                        key: catalogKey,
                        read_arguments: readArguments
                    }).then(function (response) {
                        var catalog = response.data.entity,
                            makeFakeScope = function () {
                                var $scope = {};
                                $scope.product = catalog._images[0].pricetags[0]._product;
                                $scope.originalProduct = angular.copy($scope.product);
                                $scope.catalog = catalog;
                                $scope.variants = [];
                                $scope.variantSelection = [];
                                $scope.hideAddToCart = false;
                                $scope.currentVariation = [];
                                angular.forEach($scope.product.variants, function (v, i) {

                                    $scope.variants.push({
                                        name: v.name,
                                        options: v.options,
                                        option: (variantSignatureAsDicts ? variantSignatureAsDicts[i][v.name] : v.options[0]),
                                    });

                                    $scope.variantSelection.push({
                                        type: 'SuperStringProperty',
                                        choices: (v.allow_custom_value ? null : v.options),
                                        code_name: 'option_' + i,
                                        ui: {
                                            label: v.name,
                                            writable: true,
                                            attrs: {
                                                'ng-change': 'changeVariation()'
                                            },
                                            args: 'variants[' + i + '].option'
                                        }
                                    });

                                });

                                $scope.changeVariationPromise = function () {
                                    var buildVariantSignature = [],
                                        skip = false,
                                        promise;

                                    $scope.currentVariation.splice(0, $scope.currentVariation.length);

                                    angular.forEach($scope.variants, function (v) {
                                        var d = {};
                                        if (v.option === null) {
                                            skip = true;
                                        }
                                        if (!v.allow_custom_value) {
                                            buildVariantSignature.push(v.name + ': ' + v.option);
                                            d[v.name] = v.option;
                                            $scope.currentVariation.push(d);
                                        }
                                    });

                                    if (skip) {
                                        promise = $q.defer().promise;
                                        promise.resolve();
                                        return promise;
                                    }
                                    // rpc to check the instance
                                    return models['31'].actions.read({
                                        key: this.catalog.key,
                                        // 4 rpcs
                                        read_arguments: {
                                            _images: {
                                                config: {keys: [imageKey]},
                                                pricetags: {
                                                    config: {
                                                        keys: [pricetagKey]
                                                    },
                                                    _product: {
                                                        _instances: {
                                                            config: {
                                                                search: {
                                                                    filters: [{field: 'variant_options', operator: 'ALL_IN', value: buildVariantSignature}]
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    });
                                };

                                return $scope;
                            },
                            fakeScope = makeFakeScope();
                        $modal.open({
                            resolve: {productInstanceResponse: function () {
                                return fakeScope.changeVariationPromise().then(function (response) {
                                    return response;
                                });
                            }},
                            templateUrl: 'catalog/product/view.html',
                            windowClass: 'no-overflow',
                            controller: function ($scope, productInstanceResponse) {
                                var loadProductInstance, sellerKey;
                                $.extend($scope, fakeScope);
                                toggleMenu($scope, 'right_product_sidenav');
                                $scope.resetVariation = function () {
                                    this.resetVariantProduct();
                                    $scope.variationApplied = false;
                                    angular.forEach($scope.variants, function (v) {
                                        v.option = null;
                                    });
                                };
                                $scope.resetVariantProduct = function () {
                                    $.extend(this.product, this.originalProduct);
                                    $scope.productInstance = null;
                                };
                                $scope.variationApplied = false;
                                $scope.viewContent = function (content) {
                                    $modal.open({
                                        templateUrl: 'core/models/manage.html',
                                        controller: function ($scope) {
                                            $scope.dialog = {
                                                templateBodyUrl: 'core/misc/content_view_body.html',
                                                toolbar: {
                                                    hideSave: true
                                                }
                                            };
                                            $scope.content = content;
                                            $scope.close = function () {
                                                $scope.$close();
                                            };
                                        }
                                    });
                                };
                                $scope.canAddToCart = true;
                                $scope.hasThisProduct = false;
                                $scope.disableUpdateCart = false;
                                $scope.productQuantity = 0;

                                sellerKey = $scope.catalog._seller.key;
                                $scope.cartProductQuantity = function () {
                                    $scope.productQuantity = 0;
                                    $scope.hasThisProduct = false;
                                    $scope.disableUpdateCart = false;
                                    models['34'].current(sellerKey).then(function (response) {
                                        var order = response.data.entity;
                                        if (order.id) {
                                            angular.forEach(order._lines, function (line) {
                                                if (line.product._reference.parent.id === $scope.product.parent.id
                                                        && line.product._reference.id === $scope.product.id
                                                        && JSON.stringify($scope.currentVariation) === JSON.stringify(line.product.variant_signature)) {
                                                    $scope.productQuantity = parseInt(line.product.quantity, 10);
                                                    if ($scope.productQuantity > 0) {
                                                        $scope.hasThisProduct = true;
                                                        $scope.disableUpdateCart = true;
                                                    }
                                                }
                                            });
                                            $scope.canAddToCart = order.ui.rule.action.update_line.executable;
                                        } else {
                                            $scope.canAddToCart = true;
                                        }

                                    });
                                };

                                loadProductInstance = function (response) {
                                    var product,
                                        productInstance,
                                        toUpdate = ['images', 'code', 'unit_price', 'weight', 'weight_uom', 'volume', 'volume_uom',
                                                         'description', 'contents', 'availability'];
                                    try {
                                        product = response.data.entity._images[0].pricetags[0]._product;
                                    } catch (ignore) { }

                                    if (product) {
                                        productInstance = product._instances[0];
                                    }
                                    if (productInstance) {
                                        $scope.productInstance = productInstance;
                                        angular.forEach(toUpdate, function (field) {
                                            var next = productInstance[field];
                                            if (next !== null && next.length) {
                                                $scope.product[field] = next;
                                            }
                                        });
                                    } else {
                                        $scope.resetVariantProduct();
                                    }

                                    $scope.variationApplied = true;
                                };

                                $scope.changeVariation = function () {
                                    // rpc to check the instance
                                    this.changeVariationPromise()
                                        .then(loadProductInstance)
                                        .then($scope.cartProductQuantity);
                                };

                                loadProductInstance(productInstanceResponse);

                                $scope.cartProductQuantity();

                                $scope.increaseQuantity = function () {
                                    $scope.disableUpdateCart = false;
                                    $scope.productQuantity = parseInt($scope.productQuantity, 10) +  1;
                                };

                                $scope.decreaseQuantity = function () {
                                    if (parseInt($scope.productQuantity, 10) === 0) {
                                        return;
                                    }
                                    $scope.disableUpdateCart = false;
                                    $scope.productQuantity = parseInt($scope.productQuantity, 10) -  1;
                                };

                                $scope.addToCart = function () {
                                    if (!$scope.hasThisProduct && $scope.productQuantity < 1) {
                                        $scope.container.form.$setDirty();
                                        var productQuantityField = $scope.container.form.productQuantity;
                                        productQuantityField.$setViewValue(productQuantityField.$viewValue !== undefined ? productQuantityField.$viewValue : '');
                                        productQuantityField.$setDirty();
                                        productQuantityField.$setValidity('required', false);
                                        return;
                                    }
                                    models['19'].current().then(function (response) {
                                        return models['34'].actions.update_line({
                                            buyer: response.data.entity.key,
                                            product: $scope.product.key,
                                            image: imageKey,
                                            quantity: $scope.productQuantity,
                                            variant_signature: $scope.currentVariation
                                        });
                                    }).then(function (response) {
                                        if (config.events && config.events.addToCart) {
                                            config.events.addToCart.call(this, response);
                                        }
                                        if (models['34'].getCache('current' + sellerKey)) {
                                            models['34'].current(sellerKey).then(function (cached) {
                                                $.extend(cached.data.entity, response.data.entity);
                                            });
                                        }

                                        if ($scope.productQuantity < 1) {
                                            $scope.hasThisProduct = false;
                                        } else {
                                            $scope.hasThisProduct = true;
                                            $scope.disableUpdateCart = true;
                                        }
                                    });
                                };

                                $scope.close = function () {
                                    $scope.$close();
                                };
                            }
                        });
                    });
                },
                viewModal: function (key, config) {
                    var that = this;
                    that.actions.read({
                        key: key,
                        // 5 rpcs
                        read_arguments: {
                            _seller: {
                                _content: {},
                                _feedback: {}
                            },
                            _images: {
                                pricetags: {}
                            }
                        }
                    }).then(function (response) {
                        var entity = response.data.entity;
                        if (!entity._images.length) {
                            modals.alert('Catalog has no images, add some in order to view it');
                            return;
                        }
                        $modal.open({
                            templateUrl: 'catalog/view.html',
                            windowClass: 'no-overflow',
                            controller: function ($scope) {
                                toggleMenu($scope, 'right_catalog_sidenav');
                                $scope.catalog = entity;
                                $scope.catalog.action_model = '31';
                                $scope.logoImageConfig = {};
                                var imagesReader,
                                    accessImages,
                                    catalogUrl = helpers.url.abs('catalog/' + $scope.catalog.key);
                                accessImages = angular.copy($scope.catalog.ui.access);
                                accessImages.push('_images');

                                imagesReader = models['31'].reader({
                                    kind: $scope.catalog.kind,
                                    key: $scope.catalog.key,
                                    next: {_images: $scope.catalog._next_read_arguments._images},
                                    access: accessImages,
                                    complete: function (items) {
                                        $scope.catalog._images.extend(items);
                                    }
                                });
                                $scope.social = {
                                    fb: {
                                        url: catalogUrl
                                    },
                                    twitter: {
                                        url: catalogUrl,
                                        text: 'Check out this catalog!'
                                    },
                                    pinterest: {
                                        url: catalogUrl,
                                        image: $scope.catalog._images[0].serving_url + '=s600',
                                        text: 'Share on pinterest'
                                    },
                                    gplus: {
                                        url: catalogUrl
                                    }
                                };

                                $scope.loadMoreImages = function (callback) {
                                    var promise = imagesReader.load();
                                    if (promise) {
                                        promise.then(function () {
                                            callback.call(this, response, imagesReader.more);
                                        });
                                    } else {
                                        callback.call(this, undefined, imagesReader.more);
                                    }
                                };

                                $scope.displayCart = function () {
                                    models['19'].current().then(function (response) {
                                        models['34'].manageModal(undefined, $scope.catalog._seller, response.data.entity, {
                                            cartMode: true
                                        });
                                    });
                                };

                                // cache current user's cart
                                models['34'].current($scope.catalog._seller.key);

                                $scope.viewProduct = function (image, pricetag) {
                                    that.viewProductModal($scope.catalog.key, image.key, pricetag.key);
                                };

                                $scope.sellerDetails = function () {
                                    models['23'].viewModal($scope.catalog._seller);
                                };

                                $scope.close = function () {
                                    $scope.$close();
                                };
                            }
                        });
                    });
                },
                adminManageModal: function (catalog) {
                    return this.manageModal(catalog);
                },
                manageModal: function (catalog, callback) { // modal dialog for managing the catalog

                    var fields = modelsMeta.getActionArguments('31', 'update'),
                        isNew = !angular.isDefined(catalog),
                        afterSave = function ($scope) {
                            $scope.setAction('catalog_upload_images');
                            $scope.dialog.toolbar.templateActionsUrl = 'catalog/manage_actions.html';
                            callback($scope.entity);
                        },
                        afterComplete = function ($scope) {
                            $scope.setAction('update');
                        },
                        noComplete = function ($scope) {
                            afterComplete($scope);
                        },
                        config = {
                            kind: this.kind,
                            action: (isNew ? 'create' : 'update'),
                            fields: _.toArray(fields),
                            toolbar: {
                                templateActionsUrl: (isNew ? false : 'catalog/manage_actions.html')
                            },
                            afterSave: afterSave,
                            afterSaveError: afterSave,
                            afterComplete: afterComplete,
                            afterCompleteError: afterComplete,
                            init: function ($scope) {

                                $.extend(fields._images, {
                                    ui: {
                                        label: false,
                                        specifics: {
                                            addNewText: 'Select Images',
                                            mainActionsLayout: {
                                                before: 'catalog/images_manage_button.html'
                                            },
                                            sortableOptions: {
                                                stop: function () {
                                                    if (fields._images.ui.specifics.parentArgs.length) {
                                                        var total = fields._images.ui.specifics.parentArgs[0].sequence;
                                                        angular.forEach(fields._images.ui.specifics.parentArgs,
                                                            function (ent, i) {
                                                                i = ((total + 1) - i);
                                                                ent.sequence = i;
                                                                ent.ui.access[ent.ui.access.length - 1] = i;
                                                            });

                                                        $scope.formSetDirty();
                                                        $scope.$broadcast('itemOrderChanged');
                                                    }
                                                }
                                            }
                                        }
                                    }
                                });

                                var updateFields = ['state', 'ui.rule', 'created', 'updated'],
                                    updateState = function (newArgs) {
                                        angular.forEach(['args', 'entity'], function (p) {
                                            helpers.update($scope[p], newArgs, updateFields);
                                        });
                                    };

                                $scope.actions = {
                                    publish: function () {
                                        modals.confirm('Publish this catalog will make it not editable and visible to the public.' +
                                                       ' Are you sure you want to do this?',
                                            function () {
                                                models['31'].actions.publish({
                                                    key: $scope.entity.key
                                                }).then(function (response) {
                                                    modals.alert('Catalog published. It will be public in few minutes.');
                                                    updateState(response.data.entity);
                                                });
                                            });
                                    },
                                    discontinue: function () {
                                        modals.confirm('By discontinuing this catalog you will remove it from public, and it will be delted after 40 days.' +
                                                       ' Are you sure you want to do this?',
                                            function () {
                                                models['31'].actions.discontinue({
                                                    key: $scope.entity.key
                                                }).then(function (response) {
                                                    modals.alert('Catalog discontinued successfully.');
                                                    updateState(response.data.entity);
                                                });
                                            });
                                    },
                                    duplicate: function () {
                                        modals.confirm('Are you sure you want to duplicate this catalog?',
                                            function () {
                                                models['11'].channelNotifications().then(function (response) {
                                                    models['31'].actions.catalog_duplicate({
                                                        key: $scope.entity.key,
                                                        channel: response.token
                                                    }).then(function (response) {
                                                        modals.alert('You will be notified when the duplication is done.');
                                                    });
                                                });
                                            });
                                    },
                                    sudo: function () {
                                        $modal.open({
                                            templateUrl: 'core/models/manage.html',
                                            controller: function ($scope) {
                                                $scope.dialog = {
                                                    templateBodyUrl: 'catalog/administer.html'
                                                };
                                                var sudoFields = modelsMeta.getActionArguments('31', 'sudo');
                                                $scope.args = {key: catalog.key, state: catalog.state};

                                                /*
                                                sudoFields.state.ui.placeholder = 'Set state';
                                                sudoFields.index_state.ui.placeholder = 'Index action';
                                                sudoFields.message.ui.placeholder = 'Message for the user';
                                                sudoFields.note.ui.placeholder = 'Note for administrators';
                                                */

                                                $scope.fields = [sudoFields.state, sudoFields.index_state, sudoFields.message, sudoFields.note];
                                                angular.forEach($scope.fields, function (field) {
                                                    field.ui.writable = true;
                                                });

                                                $scope.container = {};
                                                $scope.save = function () {
                                                    var promise;
                                                    if (!$scope.container.form.$valid) {
                                                        return false;
                                                    }
                                                    promise = models['31'].actions.sudo($scope.args);
                                                    promise.then(function (response) {
                                                        updateState(response.data.entity);
                                                    });
                                                    return promise;
                                                };
                                                $scope.close = function () {
                                                    $scope.$close();
                                                };
                                            }
                                        });
                                    }
                                };
                            },
                            noComplete: noComplete,
                            scope: { // scope for this modal dialog
                                historyConfig: true,
                                addProducts: function () {
                                    // this function is completely custom, meaning that the entire workflow defined here is for
                                    // pricetag positioning and product editing...
                                    var parentScope = this;
                                    if (!parentScope.args._images || !parentScope.args._images.length) {
                                        modals.alert('Add some images first!');
                                        return false;
                                    }
                                    $modal.open({
                                        templateUrl: 'core/models/manage.html',
                                        windowClass: 'no-overflow',
                                        controller: function ($scope, $timeout) {
                                            var accessImages = angular.copy(parentScope.args.ui.access),
                                                imagesReader,
                                                setupCurrentPricetag;
                                            accessImages.push(fields._images.code_name);
                                            $scope.rootScope = parentScope.rootScope; // pass the rootScope
                                            $scope.config = parentScope.rootScope.config;
                                            $scope.entity = parentScope.entity;
                                            $scope.args = angular.copy(parentScope.args);
                                            $scope.dialog = {
                                                templateBodyUrl: 'catalog/manage_products.html',
                                                toolbar: {}
                                            };
                                            $scope.container = {};
                                            $scope.formSetPristine = function () {
                                                if ($scope.container && $scope.container.form) {
                                                    $scope.container.form.$setPristine();
                                                }
                                            };
                                            $scope.formSetDirty = function () {
                                                if ($scope.container && $scope.container.form) {
                                                    $scope.container.form.$setDirty();
                                                }
                                            };
                                            $scope.validateForm = function () {
                                                if (!$scope.container.form.$valid) {
                                                    $scope.$broadcast('invalidForm');
                                                    return false;
                                                }
                                                return true;
                                            };

                                            imagesReader = models['31'].reader({
                                                kind: '31',
                                                key: $scope.args.key,
                                                next: $scope.args._next_read_arguments,
                                                access: accessImages,
                                                complete: function (items) {
                                                    $scope.args._images.extend(items);
                                                }
                                            });
                                            // set next arguments from initially loaded data from root scope
                                            imagesReader.state(parentScope.config.ui.specifics.reader);

                                            $scope.onStart = function (event, ui, image, pricetag) {
                                                $(ui.helper).addClass('dragged');
                                                $(ui.helper).find('a').addClass('dragged');
                                            };

                                            $scope.onDrag = function (event, ui, image, pricetag) {
                                                var fn = function () {
                                                    var helper = $(ui.helper),
                                                        parent = helper.parents('.image-slider-item:first'),
                                                        helperW = helper.outerWidth(),
                                                        parentW = parent.width(),
                                                        nextParent = parent.next(),
                                                        prevParent = parent.prev(),
                                                        newParent,
                                                        newPositionLeft,
                                                        currentTop = parseInt(helper.css('top'), 10),
                                                        newImage,
                                                        currentLeft = parseInt(helper.css('left'), 10),
                                                        left,
                                                        moveLeft = true,
                                                        index = $scope.args._images.indexOf(image),
                                                        pass = false,
                                                        exists = false,
                                                        newPricetag;

                                                    if (!parent.length || !helperW) {
                                                        return; // jquery ui callback fallthrough
                                                    }

                                                    if (currentLeft === 0) {
                                                        left = 0;
                                                    } else {
                                                        left = (parentW - (currentLeft + helperW));
                                                        moveLeft = false;
                                                    }
                                                    if (left === 0 && moveLeft) {
                                                        // go to left
                                                        index -= 1;
                                                        pass = true;
                                                        newParent = prevParent;
                                                        newPositionLeft = (prevParent.width() - helperW) - 5;

                                                    } else if (left === 0 && !moveLeft) {
                                                        // go to right
                                                        index += 1;
                                                        pass = true;
                                                        newParent = nextParent;
                                                        newPositionLeft = 5;
                                                    }

                                                    if (index !== -1 && pass) {
                                                        newImage = $scope.args._images[index];
                                                        if (angular.isDefined(newImage)) {
                                                            pricetag._state = 'deleted';
                                                            exists = _.findWhere(newImage.pricetags, {key: pricetag.key});
                                                            if (exists) {
                                                                pricetag = exists;
                                                            }
                                                            pricetag.image_width = newParent.width();
                                                            pricetag.image_height = newParent.height();
                                                            pricetag.position_left = newPositionLeft;
                                                            pricetag.position_top = currentTop;
                                                            pricetag._position_left = newPositionLeft;
                                                            pricetag._position_top = currentTop;
                                                            pricetag._state = null;
                                                            if (!exists) {
                                                                newPricetag = angular.copy(pricetag);
                                                                newPricetag._image = image;
                                                                newImage.pricetags.push(newPricetag);
                                                                pricetag._state = 'deleted';
                                                            }

                                                            if (!$scope.$$phase) {
                                                                $scope.$digest();
                                                            }

                                                        }
                                                    }
                                                };
                                                fn();

                                            };

                                            $scope.onStop = function (event, ui, image, pricetag) {
                                                if (pricetag._state === 'deleted') {
                                                    return;
                                                }

                                                var target = $(event.target).parents('.image-slider-item:first');

                                                pricetag.position_top = ui.position.top;
                                                pricetag.position_left = ui.position.left;
                                                pricetag.image_width = target.width();
                                                pricetag.image_height = target.height();

                                                pricetag._position_top = pricetag.position_top;
                                                pricetag._position_left = pricetag.position_left;

                                                $scope.formSetDirty();

                                                if (!$scope.$$phase) {
                                                    $scope.$digest();
                                                }

                                            };

                                            $scope.onDrop = function (event, ui, image) {
                                                var target_drop = $(event.target),
                                                    posi = target_drop.offset(),
                                                    posi2 = ui.offset,
                                                    newPricetagConfig = {
                                                        position_top: posi2.top - posi.top,
                                                        position_left: posi2.left - posi.left,
                                                        image_width: target_drop.width(),
                                                        image_height: target_drop.height()
                                                    };
                                                $scope.createProduct(image, newPricetagConfig);
                                            };

                                            $scope.loadMoreImages = function (callback) {
                                                var promise = imagesReader.load();
                                                if (promise) {
                                                    promise.then(function (response) {
                                                        callback.call(this, response, imagesReader.more);
                                                    });
                                                } else {
                                                    callback.call(this, undefined, imagesReader.more);
                                                }
                                            };

                                            setupCurrentPricetag = function (image, pricetag) {
                                                $scope.image = image;
                                                $scope.pricetag = pricetag;
                                            };

                                            $scope.loadingManageProduct = false;

                                            $scope.manageProduct = function (image, pricetag) {
                                                if (pricetag._image) {
                                                    image = pricetag._image;
                                                }
                                                if ($scope.loadingManageProduct) {
                                                    return;
                                                }
                                                $scope.loadingManageProduct = true;
                                                setupCurrentPricetag(image, pricetag);
                                                // perform read catalog.images.0.pricetags.0._product
                                                models['31'].actions.read({
                                                    key: $scope.entity.key,
                                                    read_arguments: {
                                                        _images: {
                                                            config: {
                                                                keys: [image.key]
                                                            },
                                                            pricetags: {
                                                                config: {
                                                                    keys: [pricetag.key],
                                                                },
                                                                _product: {
                                                                    _instances: {
                                                                        config: {}
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }).then(function (response) {
                                                    var responseEntity = response.data.entity,
                                                        ii = $scope.args._images.indexOf(image),
                                                        product = responseEntity._images[0].pricetags[0]._product,
                                                        realPath = ['_images', ii, 'pricetags', image.pricetags.indexOf(pricetag), '_product'];
                                                    product.ui.access = realPath; // override normalizeEntity auto generated path
                                                    $scope.fieldProduct.ui.realPath = realPath; // set same path
                                                    $scope.fieldProduct.ui.specifics.toolbar = {
                                                        title: 'Manage Product',
                                                        templateActionsUrl: 'catalog/product/manage_actions.html'
                                                    };
                                                    pricetag._product = product;
                                                    $scope.fieldProduct.modelclass._instances.ui.specifics.readerSettings = {
                                                        next: response.data.entity._next_read_arguments
                                                    };
                                                    $scope.fieldProduct.ui.specifics.manage(product); // fire up modal dialog

                                                })['finally'](function () {
                                                    $scope.loadingManageProduct = false;
                                                });
                                            };

                                            $scope.createProduct = function (image, config) {

                                                var ii = $scope.args._images.indexOf(image),
                                                    newPricetag = {
                                                        _sequence: image.pricetags.length,
                                                        image_height: config.image_height,
                                                        image_width: config.image_width,
                                                        position_left: config.position_left,
                                                        position_top: config.position_top,
                                                        _position_left: config.position_left,
                                                        _position_top: config.position_top,
                                                        value: {},
                                                        _product: {},
                                                        ui: {
                                                            access: ['_images', ii, 'pricetags', image.pricetags.length]
                                                        }
                                                    },
                                                    realPath = ['_images', ii, 'pricetags', image.pricetags.length, '_product'];

                                                image.pricetags.push(newPricetag); // append new pricetag to image
                                                setupCurrentPricetag(image, newPricetag); // set current
                                                $scope.fieldProduct.ui.realPath = realPath; // set correct pathing for the new product
                                                $scope.fieldProduct.ui.specifics.create();
                                            };

                                            $scope.fieldProduct = fields._images.modelclass.pricetags.modelclass._product;
                                            $.extend($scope.fieldProduct, {
                                                ui: {
                                                    init: function (field) {
                                                        field.config.ui.specifics.remove = function (product, close) {
                                                            // removing the actual product removes the pricetag actually
                                                            $scope.pricetag._state = 'deleted';
                                                            $scope.formSetDirty();
                                                            close();
                                                        };
                                                    },
                                                    args: 'pricetag._product',
                                                    parentArgs: 'pricetag',
                                                    path: ['_images', 'pricetags', '_product'],
                                                    render: false,
                                                    label: false,
                                                    specifics: {
                                                        modal: true,
                                                        beforeSave: function (fieldScope) {
                                                            fieldScope.setAction('update');
                                                            // before saving entity, set the name and unit price for the pricetag.
                                                            var findPricetag = _.last(fieldScope.sendRootArgs._images[0].pricetags);
                                                            findPricetag.value = {
                                                                name: fieldScope.args.name,
                                                                price: fieldScope.args.unit_price
                                                            };
                                                        },
                                                        templateFooterUrl: 'catalog/product/manage_footer.html',
                                                        getRootArgs: function () {
                                                            // root args is data that gets sent with rpc
                                                            return $scope.args;
                                                        },
                                                        afterClose: function (fieldProductScope) {
                                                            // after close hook
                                                            $scope.pricetag._product = null;
                                                            if (!fieldProductScope.args.key) {
                                                                $scope.image.pricetags.remove($scope.pricetag); // remove the pricetag if we did not commit the product
                                                            }
                                                        },
                                                        afterSave: function (fieldScope) {
                                                            // after save hook
                                                            fieldScope.setAction('product_upload_images');
                                                            var updatedPricetag = fieldScope.response.data.entity._images[0].pricetags[0];
                                                            $.extend($scope.pricetag, updatedPricetag); // after save, always update the live pricetag, because there is no way that field scope can access this scope
                                                        },
                                                        afterComplete: function (fieldScope) {
                                                            // after complete hook
                                                            fieldScope.setAction('update');
                                                        },
                                                        noComplete: function (fieldScope) {
                                                            // hook for no complete event - complete event only fires if there are images to be uploaded
                                                            fieldScope.setAction('update');
                                                        },
                                                        duplicate: function () {
                                                            modals.confirm('Are you sure you want to duplicate this pricetag?',
                                                                function () {
                                                                    models['11'].channelNotifications().then(function (response) {
                                                                        models['31'].actions.catalog_pricetag_duplicate({
                                                                            key: $scope.entity.key,
                                                                            channel: response.token,
                                                                            read_arguments: {
                                                                                _images: {
                                                                                    config: {
                                                                                        keys: [$scope.image.key]
                                                                                    },
                                                                                    pricetags: {
                                                                                        config: {
                                                                                            keys: [$scope.pricetag.key]
                                                                                        }
                                                                                    }
                                                                                }
                                                                            }
                                                                        }).then(function (response) {
                                                                            modals.alert('You will be notified when the duplication is done.');
                                                                        });
                                                                    });
                                                                });
                                                        }
                                                    }
                                                }
                                            });

                                            $scope.fieldProduct.modelclass.images.ui = {
                                                name: 'images'
                                            };

                                            $scope.fieldProduct.modelclass._instances.modelclass.images.ui = {
                                                name: 'images'
                                            };

                                            $.extend($scope.fieldProduct.modelclass._instances, {
                                                ui: {
                                                    label: 'Product Instances',
                                                    path: ['_images', 'pricetags'],
                                                    specifics: {
                                                        listView: 'product-instance-list-view',
                                                        getRootArgs: function () {
                                                            return $scope.args;
                                                        },
                                                        beforeSave: function (fieldScope) {
                                                            fieldScope.setAction('update');
                                                        },
                                                        afterSave: function (fieldScope) {
                                                            fieldScope.setAction('product_instance_upload_images');
                                                        },
                                                        afterComplete: function (fieldScope) {
                                                            fieldScope.setAction('update');
                                                        },
                                                        noComplete: function (fieldScope) {
                                                            fieldScope.setAction('update');
                                                        },
                                                        sortableOptions: {
                                                            stop: function () {
                                                                var field = $scope.fieldProduct.modelclass._instances, total,
                                                                    currentFieldScope = $scope.fieldProduct.ui.specifics.getScope();
                                                                if (field.ui.specifics.parentArgs.length) {
                                                                    total = field.ui.specifics.parentArgs[0].sequence;
                                                                    angular.forEach(field.ui.specifics.parentArgs,
                                                                        function (ent, i) {
                                                                            i = ((total + 1) - i);
                                                                            ent.sequence = i;
                                                                            ent.ui.access[ent.ui.access.length - 1] = i;
                                                                        });

                                                                    currentFieldScope.formSetDirty();
                                                                    currentFieldScope.$broadcast('itemOrderChanged');
                                                                }
                                                            }
                                                        },
                                                        create: function () {
                                                            var currentFieldScope = $scope.fieldProduct.ui.specifics.getScope(),
                                                                currentArgs = currentFieldScope.args;
                                                            if (!currentArgs.variants.length) {
                                                                modals.alert('Please create some variants first.');
                                                                return false;
                                                            }
                                                            this.manage.apply(this, arguments);
                                                        },
                                                        init: function () {
                                                            var currentFieldScope = $scope.fieldProduct.ui.specifics.getScope(),
                                                                currentArgs = currentFieldScope.args,
                                                                choices = [],
                                                                variantOptions = $scope.fieldProduct.modelclass._instances.modelclass.variant_options;
                                                            if (!currentArgs.variants.length) {
                                                                modals.alert('Please create some variants first.');
                                                                return false;
                                                            }

                                                            angular.forEach(currentArgs.variants, function (variant) {
                                                                if (variant.allow_custom_value) {
                                                                    return;
                                                                }
                                                                angular.forEach(variant.options, function (variantOpt) {
                                                                    choices.push(variant.name + ': ' + variantOpt);
                                                                });
                                                            });

                                                            variantOptions.choices = choices;
                                                        },
                                                        excludeFields: ['created', 'sequence']
                                                    }
                                                }
                                            });

                                            $.extend($scope.fieldProduct.modelclass.contents, {
                                                ui: {
                                                    specifics: {}
                                                }
                                            });

                                            $.extend($scope.fieldProduct.modelclass.images, {
                                                ui: {
                                                    name: 'images',
                                                    specifics: {}
                                                }
                                            });

                                            $.extend($scope.fieldProduct.modelclass.variants, {
                                                ui: {
                                                    specifics: {}
                                                }
                                            });

                                            $scope.save = function () {
                                                var promise;
                                                promise = models['31'].actions[$scope.args.action_id]($scope.args);
                                                promise.then(function (response) {
                                                    $.extend($scope.entity, response.data.entity);
                                                    var newArgs = $scope.rootScope.config.argumentLoader($scope);
                                                    parentScope.args = angular.copy(newArgs);
                                                    $scope.args = angular.copy(newArgs);
                                                    parentScope.config.ui.specifics.reader.state(imagesReader);
                                                    $scope.formSetPristine();
                                                });
                                                return promise;
                                            };

                                            $scope.close = function () {
                                                $scope.$close();
                                            };
                                        }
                                    });

                                },
                                accordions: {
                                    closeOthers: true,
                                    groups: [{
                                        label: 'General',
                                        open: true,
                                        fields: ['name', 'discontinue_date'],
                                    }, {
                                        label: 'Products',
                                        open: false,
                                        fields: ['_images']
                                    }]
                                }
                            }
                        };

                    if (isNew) {
                        // get current seller
                        models['23'].current().then(function (response) {
                            modelsEditor.create(config).prepare({}, {
                                seller: response.data.entity.key,
                                read_arguments: {
                                    _images: {}
                                }
                            });
                        });

                    } else {
                        modelsEditor.create(config).read(catalog, {
                            key: catalog.key,
                            read_arguments: {
                                _images: {}
                            }
                        });

                    }

                }
            });

        });


    });
}());(function () {
    'use strict';
    angular.module('app').run(function (modelsConfig, endpoint, currentAccount, modelsMeta, modelsEditor) {
        modelsConfig(function (models) {
            var read_arguments = {
                _sellers: {
                    _content: {},
                    _feedback: {}
                }
            };

            $.extend(models['18'], {
                current: function (args) {
                    if (!args) {
                        args = {};
                    }
                    args.account = currentAccount.key;
                    return this.actions.read(args, {
                        cache: this.getCacheKey('current'),
                        cacheType: 'memory'
                    });
                },
                manageModal: function (accountKey) {
                    var fields = modelsMeta.getActionArguments(this.kind, 'update'),
                        config,
                        that = this;
                    config = {
                        kind: this.kind,
                        action: 'update',
                        fields: _.toArray(fields),
                        templateBodyUrl: 'collection/manage_body.html',
                        excludeFields: ['account', 'read_arguments'],
                        afterComplete: function ($scope) {
                            $scope.entity._sellers.iremove(function (seller) {
                                return $.inArray(seller.key, $scope.entity.sellers) === -1;
                            });
                            if (that.getCache('current')) {
                                that.current().then(function (response) {
                                    $.extend(response.data.entity, $scope.entity);
                                });
                            }
                        },
                        scope: {
                            remove: function (seller) {
                                this.args.sellers.remove(seller.key);
                                this.entity._sellers.remove(seller);
                            },
                            view: function (seller) {
                                var thisScope = this;
                                models['23'].actions.read({
                                    account: seller.parent.key,
                                    // 3 rpcs
                                    read_arguments: {
                                        _content: {},
                                        _feedback: {}
                                    }
                                }).then(function (response) {
                                    models['23'].viewModal(response.data.entity, function (updatedCollection) {
                                        thisScope.entity._sellers.iremove(function (seller) {
                                            return $.inArray(seller.key, updatedCollection.sellers) === -1;
                                        });
                                        var rmkey = function (sellerKey) {
                                            return $.inArray(sellerKey, updatedCollection.sellers) === -1;
                                        };
                                        thisScope.entity.sellers.iremove(rmkey);
                                        thisScope.args.sellers.iremove(rmkey);
                                    });
                                });
                            },
                            accordions: {
                                closeOthers: true,
                                groups: [{
                                    label: 'General',
                                    open: true,
                                    key: 'general'
                                }, {
                                    label: 'Sellers'
                                }]
                            }
                        }
                    };

                    modelsEditor.create(config).read({}, {
                        account: accountKey,
                        read_arguments: read_arguments
                    });

                }
            });

        });
    });
}());(function () {
    'use strict';
    angular.module('app')
        .controller('MainMenuCtrl', function ($scope, currentAccount, GLOBAL_CONFIG, $mdSidenav, $timeout) {
            $scope.currentAccount = currentAccount;
            $scope.GLOBAL_CONFIG = GLOBAL_CONFIG;
            $scope.JSON = JSON;
            $scope.closeMenu = function () {
                $timeout(function () {
                    $mdSidenav('left').close();
                });
            };
            $scope.openMenu = function () {
                $timeout(function () {
                    $mdSidenav('left').open();
                });
            };
        })
        .controller('HomePageCtrl', function ($scope, models, modals, $state, $stateParams, $q, modelsMeta) {
            var args = {search: {}},
                defer = $q.defer(),
                promise = defer.promise;
            $scope.sellerDetail = false;
            $scope.view = function (key) {
                models['31'].viewModal(key);
            };

            if ($stateParams.key) {
                args.search.filters = [{field: 'seller_account_key', operator: 'IN', value: $stateParams.key}];
                $scope.sellerDetail = {};
                models['23'].actions.read({
                    account: $stateParams.key,
                    read_arguments: {
                        _feedback: {},
                        _content: {}
                    }
                }).then(function (response) {
                    $.extend($scope.sellerDetail, response.data.entity);
                });

                $scope.viewSeller = function () {
                    models['23'].viewModal($scope.sellerDetail);
                };
            }
            if ($state.current.name === 'collections') {
                promise = models['18'].current();
                promise.then(function (response) {
                    $scope.search.pagination.args.search.filters = [{field: 'ancestor', operator: 'IN', value: response.data.entity.sellers}];
                });
            } else {
                defer.resolve();
            }
            $scope.search = {
                results: [],
                pagination: models['31'].paginate({
                    kind: '31',
                    args: args,
                    config: {
                        normalizeEntity: false
                    },
                    action: 'public_search',
                    complete: function (response) {
                        var results = response.data.entities;
                        models['31'].formatPublicSearchResults(results);
                        $scope.search.results.extend(results);
                    }
                })
            };
            $scope.scrollEnd = {loader: false};
            $scope.scrollEnd.loader = $scope.search.pagination;
            promise.then(function () {
                $scope.search.pagination.load();
            });

            $scope.datetime = new Date();


        });

}());(function () {
    'use strict';
    angular.module('app').run(function (modelsConfig, modelsMeta) {
        modelsConfig(function (models) {
            models['12'].config.cache = true;
            models['12'].getSubdivisions = function (countryKey, overrideConfig) {
                var subdivisionModel = models['13'],
                    defaultArgs = modelsMeta.getDefaultActionArguments(subdivisionModel.kind, 'search');
                defaultArgs.ancestor = countryKey;
                return subdivisionModel.search(defaultArgs, overrideConfig);
            };

        });

    });
}());(function () {
    'use strict';
    angular.module('app').directive('sendMessage', function ($parse) {
        return {
            restrict: 'A',
            link: function (scope, element, attrs) {
                var callback = $parse(attrs.sendMessage),
                    root = element.parents('.modal-dialog:first'),
                    textarea,
                    pane,
                    click = function (e) {
                        textarea = root.find('textarea');
                        pane = root.find('.overflow-y');
                        if (textarea.length && textarea.val()) {
                            callback(scope);
                        } else {
                            pane.stop().scrollTo(textarea, 100, function () {
                                textarea.focus();
                            });
                        }
                        e.preventDefault();
                    };

                element.on('click', click);

                scope.$on('$destroy', function () {
                    element.off('click', click);
                });

            }
        };
    }).filter('displayTaxes', function () {
        return function (value) {
            var formatted = '';
            if (value) {
                formatted = $.map(value, function (item) {
                    return item.name;
                }).join(', ');
            }
            return formatted;
        };
    }).run(function (modelsMeta, modelsConfig, $modal, modals, helpers, endpoint, $q, $filter, currentAccount) {
        modelsConfig(function (models) {
            $.extend(models['34'], {
                current: function (sellerKey) {
                    var that = this;
                    return models['19'].current().then(function (response) {
                        var buyer = response.data.entity;
                        return that.actions.view_order({
                            buyer: buyer.key,
                            seller: sellerKey
                        }, {
                            cache: that.getCacheKey('current' + sellerKey),
                            cacheType: 'memory'
                        });
                    });
                },
                adminManageModal: function (order) {
                    return this.manageModal(order, order._seller, undefined, {
                        sellerMode: true
                    });
                },
                manageModal: function (order, seller, buyer, config) {
                    config = helpers.alwaysObject(config);
                    var args, that = this, cartMode = config.cartMode, sellerMode = config.sellerMode, rpc = {};

                    if (!cartMode) {
                        args = {
                            key: order.key,
                            read_arguments: {
                                _lines: {config: {
                                    options: {
                                        limit: 0
                                    }
                                }},
                                _messages: {
                                    _agent: {}
                                }
                            }
                        };
                    } else {
                        args  = {
                            buyer: buyer.key,
                            seller: seller.key,
                            read_arguments: {
                                _messages: {
                                    _agent: {}
                                }
                            }
                        };
                    }

                    models['34'].actions[cartMode ? 'view_order' : 'read'](args, rpc).then(function (response) {

                        if (!response.data.entity.id) {
                            modals.alert('No cart available, please add some products to your cart before you can view it');
                            return;
                        }

                        $modal.open({
                            templateUrl: 'order/view.html',
                            controller: function ($scope) {
                                var billing_addresses, shipping_addresses, reactOnStateChange, reactOnUpdate, updateLiveEntity,
                                    orderActionsFields = modelsMeta.getActionArguments('34'), prepareMessageFields,
                                    displayAddress = function (address) {
                                        var addr = [];
                                        angular.forEach(['name', 'street', 'city', '_region.name', 'postal_code', '_country.name', 'email', 'telephone'], function (field) {
                                            var v = helpers.getProperty(address, field);
                                            if (v !== null && v !== undefined) {
                                                addr.push(v);
                                            }
                                        });
                                        return addr.join(', ');
                                    },
                                    carriers,
                                    messageSenderActions = ['log_message', 'leave_feedback', 'review_feedback', 'sudo_feedback'],
                                    getMessageField = function () {
                                        var action;
                                        angular.forEach(messageSenderActions, function (act) {
                                            if ($scope.order.ui.rule.action[act].executable) {
                                                action = act;
                                            }
                                        });
                                        if (!action) {
                                            return false;
                                        }
                                        return orderActionsFields[action].message;
                                    },
                                    getFeedbackField = function () {
                                        var action = false;
                                        if ($scope.order.ui.rule.action.sudo_feedback.executable) {
                                            action = 'sudo_feedback';
                                        }
                                        if ($scope.order.ui.rule.action.leave_feedback.executable) {
                                            action = 'leave_feedback';
                                        }
                                        if (!action) {
                                            return false;
                                        }
                                        return orderActionsFields[action].feedback;
                                    },
                                    messageField, feedbackField;

                                $scope.canShowMessageBox = function () {
                                    var truth = false;
                                    angular.forEach(messageSenderActions, function (act) {
                                        if ($scope.order.ui.rule.action[act].executable) {
                                            truth = true;
                                        }
                                    });
                                    return truth;
                                };
                                $scope.container = {};
                                $scope.selection = {};
                                $scope.cartMode = cartMode;
                                $scope.sellerMode = sellerMode;
                                $scope.order = response.data.entity;
                                $scope.seller = seller;
                                $scope.currentAccount = currentAccount;
                                $scope.newMessage = {
                                    message: null,
                                    key: $scope.order.key
                                };
                                carriers = response.data.carriers || ($scope.order.carrier ? [{
                                    name: $scope.order.carrier.description,
                                    price: $scope.order.carrier.unit_price,
                                    key: $scope.order.carrier.reference
                                }] : []);
                                carriers = $.map(carriers, function (item) {
                                    if (!item) {
                                        return '';
                                    }
                                    if (!angular.isDefined(item.original_name)) {
                                        item.original_name = item.name;
                                    }
                                    item.name = item.original_name + ' (' + $filter('formatCurrency')(item.price, $scope.order.currency) + ')';
                                    return item;
                                });

                                if (cartMode) {
                                    billing_addresses = response.data.billing_addresses;
                                    shipping_addresses = response.data.shipping_addresses;
                                    $scope.selection.billing_address = $scope.order.billing_address.reference;
                                    $scope.selection.shipping_address = $scope.order.shipping_address.reference;
                                } else {
                                    angular.forEach(['country', 'region'], function (field) {
                                        $scope.order.billing_address['_' + field] = {
                                            name: $scope.order.billing_address[field]
                                        };
                                        $scope.order.shipping_address['_' + field] = {
                                            name: $scope.order.billing_address[field]
                                        };
                                    });
                                    billing_addresses = [$scope.order.billing_address, $scope.order.shipping_address];
                                    shipping_addresses = billing_addresses;
                                    $scope.selection.billing_address = $scope.order.billing_address.key;
                                    $scope.selection.shipping_address = $scope.order.shipping_address.key;
                                }
                                $scope.selection.payment_method = $scope.order.payment_method;
                                $scope.selection.carrier = $scope.order.carrier ? $scope.order.carrier.reference : null;
                                $scope.fields = {
                                    billingAddress: {
                                        kind: orderActionsFields.update.billing_address_reference.kind,
                                        type: 'SuperKeyProperty',
                                        code_name: 'selection_billing_address',
                                        required: orderActionsFields.update.billing_address_reference.required,
                                        ui: {
                                            args: 'selection.billing_address',
                                            label: 'Billing Address',
                                            init: function (info) {
                                                info.config.ui.specifics.view = displayAddress;
                                            },
                                            writable: 'order.ui.rule.field.billing_address.reference.writable',
                                            specifics: {
                                                entities: function () {
                                                    return billing_addresses;
                                                }
                                            }
                                        }
                                    },
                                    shippingAddress: {
                                        kind: orderActionsFields.update.shipping_address_reference.kind,
                                        type: 'SuperKeyProperty',
                                        code_name: 'selection_shipping_address',
                                        required: orderActionsFields.update.shipping_address_reference.required,
                                        ui: {
                                            args: 'selection.shipping_address',
                                            label: 'Shipping Address',
                                            writable: 'order.ui.rule.field.shipping_address.reference.writable',
                                            init: function (info) {
                                                info.config.ui.specifics.view = displayAddress;
                                            },
                                            specifics: {
                                                entities: function () {
                                                    return shipping_addresses;
                                                }
                                            }
                                        }
                                    },
                                    carrier: {
                                        kind: orderActionsFields.update.carrier.kind,
                                        type: 'SuperKeyProperty',
                                        code_name: 'selection_carrier',
                                        required: orderActionsFields.update.carrier.required,
                                        ui: {
                                            args: 'selection.carrier',
                                            label: 'Delivery Method',
                                            writable: 'order.ui.rule.field.carrier.writable',
                                            specifics: {
                                                entities: function () {
                                                    return carriers;
                                                }
                                            }
                                        }
                                    }
                                };

                                prepareMessageFields = function () {
                                    messageField = getMessageField();
                                    feedbackField = getFeedbackField();

                                    // this must refresh based on state change
                                    if (messageField) {
                                        $.extend(messageField.ui, {
                                            args: 'newMessage.message',
                                            parentArgs: 'newMessage',
                                            writable: true
                                        });
                                        messageField.required = false;
                                    }
                                    if (feedbackField) {
                                        $.extend(feedbackField.ui, {
                                            args: 'newMessage.feedback',
                                            parentArgs: 'newMessage',
                                            writable: true
                                        });
                                        feedbackField.required = false;
                                    }
                                    $scope.fields.feedback = feedbackField;
                                    $scope.fields.message = messageField;
                                };

                                reactOnStateChange = function (response) {
                                    helpers.update($scope.order, response.data.entity, ['state', 'ui']);
                                    reactOnUpdate();
                                    prepareMessageFields();
                                };
                                reactOnUpdate = function () {
                                    if (order) {
                                        $.extend(order, $scope.order);
                                    }
                                    if (that.getCache('current' + seller.key)) {
                                        that.current(seller.key).then(function (response) {
                                            $.extend(response.data.entity, $scope.order);
                                        });
                                    }
                                };
                                updateLiveEntity = function (response) {
                                    var messages = $scope.order._messages;
                                    $.extend($scope.order, response.data.entity);
                                    $scope.order._messages = messages;
                                };
                                $scope.update = function () {
                                    models['34'].actions.update({
                                        key: $scope.order.key,
                                        payment_method: $scope.selection.payment_method,
                                        carrier: $scope.selection.carrier,
                                        billing_address_reference: ((cartMode && !sellerMode) ? $scope.selection.billing_address : $scope.order.billing_address.reference),
                                        shipping_address_reference: ((cartMode && !sellerMode) ? $scope.selection.shipping_address : $scope.order.shipping_address.reference),
                                        _lines: $scope.order._lines
                                    }).then(function (response) {
                                        updateLiveEntity(response);
                                        reactOnUpdate();
                                    });
                                };

                                $scope.checkout = function () {
                                    if ($scope.order.state !== 'checkout') {
                                        modals.confirm('Are you sure you want to go to checkout? You will be in able to send messages to seller or cancel this order.', function () {
                                            models['34'].actions.checkout({
                                                key: $scope.order.key
                                            }).then(function (response) {
                                                reactOnStateChange(response);
                                            });
                                        });
                                    }
                                };

                                $scope.formSetPaypalFormPristine = function () {
                                    if ($scope.container && $scope.container.paypalForm) {
                                        $scope.container.paypalForm.$setPristine();
                                    }
                                };
                                $scope.formSetPaypalFormDirty = function () {
                                    if ($scope.container && $scope.container.paypalForm) {
                                        $scope.container.paypalForm.$setDirty();
                                    }
                                };


                                $scope.removeLine = function (line) {
                                    line.product.quantity = 0;
                                    $scope.formSetPaypalFormDirty();
                                };

                                $scope.messaging = {
                                    send: function (action) {
                                        models['34'].actions[action]($scope.newMessage).then(function (response) {
                                            $scope.newMessage.message = '';
                                            $scope.order._messages.unshift(response.data.entity._messages[0]);
                                            reactOnStateChange(response);
                                        });
                                    },
                                    logMessage: function () {
                                        return this.send('log_message');
                                    },
                                    reviewFeedback: function () {
                                        return this.send('review_feedback');
                                    },
                                    sudoFeedback: function () {
                                        return this.send('sudo_feedback');
                                    },
                                    leaveFeedback: function () {
                                        return this.send('leave_feedback');
                                    },
                                    reportFeedback: function () {
                                        return this.send('report_feedback');
                                    }
                                };

                                $scope.canShowMessageBox = function () {
                                    var truth = false;
                                    angular.forEach(messageSenderActions, function (act) {
                                        if ($scope.order.ui.rule.action[act].executable) {
                                            truth = act;
                                        }
                                    });
                                    return truth;
                                };

                                $scope.cancel = function () {
                                    if ($scope.order.state === 'checkout') {
                                        modals.confirm('Are you sure you want to cancel this order?', function () {
                                            models['34'].actions.cancel({
                                                key: $scope.order.key
                                            }).then(function (response) {
                                                models['34'].removeCache('current' + seller.key);
                                                $scope.close();
                                            });
                                        });
                                    }
                                };

                                $scope.close = function () {
                                    $scope.$close();
                                };

                                $scope.viewProduct = function (line) {
                                    var path = line.product._reference;
                                    models['31'].viewProductModal(path.parent.parent.parent.key,
                                                                  path.parent.parent.key, path.pricetag.key,
                                                                  line.product.variant_signature, {events: {addToCart: updateLiveEntity}});
                                };

                                $scope.notifyUrl = helpers.url.abs('api/order/complete/paypal');
                                $scope.completePath = helpers.url.abs('payment/completed/' + $scope.order.key);
                                $scope.cancelPath = helpers.url.abs('payment/canceled/' + $scope.order.key);
                                $scope.messagesReader = models['34'].reader({
                                    kind: '34',
                                    key: $scope.order.key,
                                    next: $scope.order._next_read_arguments,
                                    access: ['_messages'],
                                    complete: function (items) {
                                        $scope.order._messages.extend(items);
                                    }
                                });

                                prepareMessageFields();

                            }
                        });


                    });

                }
            });

        });


    });
}());
(function () {
    'use strict';
    var notEmpty = function (val) {
        return angular.isString(val) || angular.isNumber(val);
    };
    angular.module('app').directive('addressRuleLocationListView', function () {
        return {
            scope: {
                val: '=addressRuleLocationListView'
            },
            templateUrl: 'seller/address_rule_location_list_view.html',
            controller: function ($scope) {
                $scope.notEmpty = notEmpty;
                $scope.postalCodes = function (postalCodes) {
                    return postalCodes.join(', ');
                };

            }
        };
    }).directive('defaultLineListView', function () {
        return {
            scope: {
                val: '=defaultLineListView'
            },
            templateUrl: 'seller/default_line_list_view.html'
        };
    }).directive('carrierLineRuleListView', function () {
        return {
            scope: {
                val: '=carrierLineRuleListView'
            },
            templateUrl: 'seller/carrier_line_rule_list_view.html',
            controller: function ($scope) {
                $scope.notEmpty = notEmpty;

            }
        };
    }).directive('pluginListView', function (modelsMeta) {
        return {
            scope: {
                val: '=pluginListView'
            },
            templateUrl: 'seller/plugin_list_view.html',
            controller: function ($scope) {
                $scope.pluginName = function (kind) {
                    return modelsMeta.getName(kind);
                };
            }
        };
    }).controller('SellerManagementCtrl', function ($scope, endpoint,
        currentAccount, models) {

        $scope.settings = function () {
            models['23'].manageModal(currentAccount.key);
        };

    }).controller('SellCatalogsCtrl', function ($scope, modals, modelsEditor, modelsMeta, models, modelsUtil, $rootScope) {

        $rootScope.pageTitle = 'Sell Catalogs';

        var newEntity = function (entity) {
            if (!_.findWhere($scope.search.results, {
                    key: entity.key
                })) {
                $scope.search.results.unshift(entity);
            }
        };

        $scope.create = function () {
            models['31'].manageModal(undefined, newEntity);
        };

        $scope.preview = function (key) {
            models['31'].previewModal(key);
        };

        $scope.manage = function (entity) {
            models['31'].manageModal(entity, newEntity);
        };


        $scope.search = {
            results: [],
            pagination: {}
        };

        $scope.scrollEnd = {
            loader: false
        };

        models['23'].current().then(function (response) {
            var sellerEntity = response.data.entity;
            $scope.search.pagination = models['31'].paginate({
                kind: '31',
                args: {
                    search: {
                        ancestor: sellerEntity.key
                    }
                },
                config: {
                    ignoreErrors: true
                },
                complete: function (response) {
                    var errors = response.data.errors;
                    if (errors) {
                        if (errors['not_found_' + sellerEntity.key]) {
                            modals.alert('You do not have any seller information yet.');
                        }
                    } else {
                        $scope.search.results.extend(response.data.entities);
                    }
                }
            });
            $scope.scrollEnd.loader = $scope.search.pagination;
            $scope.search.pagination.load();
        });

    }).controller('SellOrdersCtrl', function ($scope, modals, modelsEditor, modelsMeta, models, modelsUtil, $rootScope, $state) {

        var carts = $state.current.name === 'sell-carts';

        $rootScope.pageTitle = 'Seller ' + (carts ? 'Carts' : 'Orders');

        $scope.search = {
            results: [],
            pagination: {}
        };

        $scope.scrollEnd = {
            loader: false
        };

        $scope.view = function (order) {
            models['34'].manageModal(order, order._seller, undefined, {
                sellerMode: carts
            });
        };

        models['23'].current().then(function (response) {
            var sellerEntity = response.data.entity;
            $scope.search.pagination = models['34'].paginate({
                kind: '34',
                args: {
                    search: {
                        // {field: 'state', operator: 'IN', value: (carts ? ['cart', 'checkout'] : ['completed', 'canceled'])}
                        filters: [{
                            field: 'seller_reference',
                            operator: '==',
                            value: sellerEntity.key
                        }],
                        orders: [{
                            field: 'updated',
                            operator: 'desc'
                        }]
                    }
                },
                config: {
                    ignoreErrors: true
                },
                complete: function (response) {
                    var errors = response.data.errors;
                    if (errors) {
                        if (errors['not_found_' + sellerEntity.key]) {
                            modals.alert('You do not have any seller information yet.');
                        }
                    } else {
                        $scope.search.results.extend(response.data.entities);
                    }
                }
            });
            $scope.scrollEnd.loader = $scope.search.pagination;
            $scope.search.pagination.load();
        });
    }).run(function ($window, modelsConfig, modelsMeta,
        modelsEditor, formInputTypes, underscoreTemplate, $modal, modals, helpers, $q, $timeout, currentAccount, $filter, dateFilter) {

        modelsConfig(function (models) {
            formInputTypes.SuperPluginStorageProperty = function (info) {
                //info.config.repeated = true;
                //return this.SuperLocalStructuredProperty(info);
                var config = info.config,
                    kinds = $.map(config.kinds, function (kind_id) {
                        var name = modelsMeta.getName(kind_id);
                        return {
                            key: kind_id,
                            name: name
                        };
                    }),
                    rootFormSetDirty = helpers.callable(info.scope.formSetDirty),
                    lineSpec = {
                        listView: 'default-line-list-view'
                    },
                    locationSpec = {
                        listView: 'address-rule-location-list-view',
                        sortFields: ['country', 'region', 'postal_codes'],
                        beforeSave: function ($scope, info) {
                            var promises = [],
                                updatedAddress = $scope.args,
                                promise;

                            if (updatedAddress.region && (!updatedAddress._region || (updatedAddress.region !== updatedAddress._region.key))) {
                                promise = models['13'].get(updatedAddress.region);
                                promise.then(function (response) {
                                    if (response.data.entities.length) {
                                        updatedAddress._region = response.data.entities[0];
                                    }
                                });
                                promises.push(promise);
                            }

                            if (updatedAddress.country && ((!updatedAddress._country) || (updatedAddress.country !== updatedAddress._country.key))) {
                                promise = models['12'].actions.search(undefined, {
                                    cache: true
                                });
                                promise.then(function (response) {
                                    if (response.data.entities.length) {
                                        var country = _.findWhere(response.data.entities, {
                                            key: updatedAddress.country
                                        });
                                        if (angular.isDefined(country)) {
                                            updatedAddress._country = country;
                                        }

                                    }

                                });
                                promises.push(promise);
                            }

                            if (promises.length) {
                                return $q.all(promises);
                            }
                            return false;

                        }
                    },
                    defaultSpecifics = {
                        sortableOptions: {
                            disabled: false,
                            start: function (e, ui) {
                                info.scope.$broadcast('itemOrderStarted');
                            },
                            axis: false,
                            containment: false,
                            whatSortMeans: modals.howToSort,
                            handle: '.sort-handle',
                            tolerance: 'pointer',
                            helper: 'clone',
                            sort: function (e, ui) {
                                var deleteMode,
                                    division,
                                    helperWidth = ui.helper.width(),
                                    itemScope = ui.item.scope(),
                                    item = itemScope.$eval(ui.item.attr('current-item'));
                                division = ui.offset.left + helperWidth;
                                if (division < (helperWidth / 1.5)) {
                                    deleteMode = true;
                                }
                                if (item) {
                                    if (deleteMode) {
                                        ui.helper.addClass('about-to-delete');
                                        item._state = 'deleted';
                                    } else {
                                        ui.helper.removeClass('about-to-delete');
                                        item._state = null;
                                    }
                                }
                                info.scope.$broadcast('itemOrderSorting');
                            },
                            stop: function () {
                                angular.forEach(config.ui.specifics.parentArgs,
                                    function (ent, i) {
                                        i = ((config.ui.specifics.parentArgs.length - 1) - i);
                                        ent._sequence = i;
                                        if (ent.ui) {
                                            ent.ui.access[ent.ui.access.length - 1] = i;
                                        }
                                    });
                                rootFormSetDirty();
                                info.scope.$broadcast('itemOrderChanged');
                                info.scope.$apply();
                            }
                        },
                        pluginFieldOverrides: {
                            '113': {
                                lines: {
                                    ui: {
                                        specifics: lineSpec
                                    },
                                    modelclass: {
                                        rules: {
                                            ui: {
                                                specifics: {
                                                    listView: 'carrier-line-rule-list-view'
                                                }
                                            }
                                        },
                                        locations: {
                                            ui: {
                                                specifics: locationSpec
                                            }
                                        }
                                    }
                                }
                            },
                            '107': {
                                locations: {
                                    ui: {
                                        specifics: locationSpec
                                    }
                                }
                            },
                            '126': {
                                lines: {
                                    ui: {
                                        specifics: lineSpec
                                    }
                                }
                            },
                            '109': {
                                carriers: {
                                    ui: {
                                        specifics: {
                                            entities: function () {
                                                if (!config.ui.specifics.parentArgs) {
                                                    return [];
                                                }
                                                return $.map(config.ui.specifics.parentArgs,
                                                    function (item) {
                                                        if (item.active && item.kind === '113') {
                                                            return {
                                                                key: item.key,
                                                                name: item.name
                                                            };

                                                        }

                                                    });
                                            }
                                        }
                                    }
                                },
                                locations: {
                                    ui: {
                                        specifics: locationSpec
                                    }
                                }
                            }
                        },
                        showType: function (kind) {
                            return _.findWhere(kinds, {
                                key: kind
                            }).name;
                        },
                        kind: undefined,
                        selectKinds: {
                            type: 'SuperKeyProperty',
                            ui: {
                                specifics: {
                                    entities: function () {
                                        return kinds;
                                    },
                                },
                                args: 'info.kind',
                                label: 'Plugins',
                                attrs: {
                                    'ng-change': 'setNewArg()'
                                },
                                writable: true
                            },
                            code_name: 'kind'
                        },
                        remove: function (arg) {
                            arg._state = 'deleted';
                            info.scope.$emit('itemDelete', arg);
                            info.scope.$broadcast('itemDelete', arg);
                            rootFormSetDirty();
                        },
                        create: function () {
                            return this.manage();
                        },
                        manage: function (arg) {

                            if (!angular.isDefined(config.ui.specifics.templateUrl)) {
                                config.ui.specifics.templateUrl = 'core/fields/manage_structured.html';
                            }

                            $modal.open({
                                template: underscoreTemplate.get(config.ui.specifics.templateUrl)({
                                    config: config
                                }),
                                controller: function ($scope, modelsUtil) {
                                    var is_new = false,
                                        inflector = $filter('inflector'),
                                        resetFormBuilder = function () {
                                            $scope.accordions = {
                                                closeOthers: true,
                                                groups: [{
                                                    label: 'General',
                                                    disabled: false,
                                                    open: true
                                                }]
                                            };
                                            $scope.formBuilder = {
                                                '0': [config.ui.specifics.selectKinds]
                                            };
                                        },
                                        getPluginFieldOverrides = function (kind_id, field) {
                                            var gets = defaultSpecifics.pluginFieldOverrides[kind_id];
                                            if (angular.isDefined(gets) && angular.isDefined(gets[field])) {
                                                return angular.copy(gets[field]);
                                            }
                                            return {};
                                        };

                                    if (!arg) {
                                        arg = {};
                                    } else {
                                        modelsUtil.normalize(arg, undefined, config.ui.specifics.entity, config.code_name,
                                                config.ui.specifics.parentArgs.length);
                                    }
                                    $scope.info = {
                                        build: true
                                    };

                                    $scope.config = config;
                                    $scope.setNewArg = function () {
                                        if ($scope.info.kind !== 0 && $scope.args.kind !== $scope.info.kind) {
                                            arg = {
                                                kind: $scope.info.kind
                                            };
                                            modelsUtil.normalize(arg, undefined, config.ui.specifics.entity, config.code_name,
                                                config.ui.specifics.parentArgs.length, false);
                                            is_new = true;

                                            $scope.args = arg;
                                            $scope.getFormBuilder();
                                            $scope.info.build = false;

                                            $timeout(function () {
                                                $scope.info.build = true;
                                                $scope.$apply();
                                            }, 100);

                                        }
                                    };

                                    resetFormBuilder();

                                    $scope.getFormBuilder = function () {
                                        resetFormBuilder();
                                        var kind = $scope.info.kind,
                                            fields = modelsMeta.getFields(kind),
                                            realTotal = 0,
                                            found = false;
                                        fields = _.toArray(fields);
                                        fields.sort(helpers.fieldSorter);
                                        config.ui.specifics.fields = fields;
                                        angular.forEach(fields, function (field) {
                                            field.ui.name = 'plugin.' + field.code_name;
                                            field.ui.writable = true;
                                            var extra = getPluginFieldOverrides(kind, field.code_name),
                                                next;
                                            if (extra) {
                                                helpers.extendDeep(field, extra);
                                            }
                                            if (field.is_structured && formInputTypes[field.type]) {
                                                $scope.accordions.groups.push({
                                                    label: inflector((field.ui.label || field.code_name), 'humanize'),
                                                    disabled: false,
                                                    open: false
                                                });

                                                field.ui.label = false;
                                                next = $scope.accordions.groups.length - 1;

                                                if (!angular.isDefined($scope.formBuilder[next])) {
                                                    $scope.formBuilder[next] = [];
                                                    $scope.formBuilder[next].push(field);
                                                }
                                                $scope.accordions.groups[0].disabled = false;
                                            } else {
                                                $scope.formBuilder['0'].push(field);
                                            }
                                        });

                                        angular.forEach($scope.accordions.groups, function (group, i) {
                                            if ($scope.formBuilder[i].length) {
                                                realTotal += 1;
                                            }
                                            if (found !== false) {
                                                return;
                                            }
                                            if ($scope.formBuilder[i].length) {
                                                group.open = true;
                                                found = group;
                                            } else {
                                                group.open = false;
                                            }
                                        });

                                        if (realTotal === 1) {
                                            found.disabled = true;
                                        }

                                    };

                                    $scope.container = {};
                                    $scope.args = angular.copy(arg);
                                    // entity.addreses.0.address
                                    $scope.parentArgs = config.ui.specifics.parentArgs;
                                    // entity.addresses
                                    $scope.entity = config.ui.specifics.entity;
                                    $scope.rootFormSetDirty = rootFormSetDirty;
                                    $scope.formSetDirty = function () {
                                        if ($scope.container && $scope.container.form) {
                                            return $scope.container.form.$setDirty();
                                        }
                                    };
                                    $scope.formSetPristine = function () {
                                        if ($scope.container && $scope.container.form) {
                                            return $scope.container.form.$setPristine();
                                        }
                                    };

                                    if ($scope.args && $scope.args.kind) {
                                        $scope.info.kind = $scope.args.kind;
                                        $scope.getFormBuilder();

                                    }

                                    $scope.close = function () {
                                        $scope.$close();
                                    };

                                    $scope.validateForm = function () {
                                        if (!$scope.container.form.$valid) {
                                            $scope.$broadcast('invalidForm');
                                            return false;
                                        }
                                        return true;
                                    };

                                    $scope.save = function () {
                                        var promise, complete;
                                        if (!$scope.validateForm()) {
                                            return;
                                        }

                                        if (angular.isFunction(config.ui.specifics.beforeSave)) {
                                            promise = config.ui.specifics.beforeSave($scope, info);
                                        }

                                        complete = function () {
                                            var newPromise = null,
                                                total = 0;
                                            if (is_new) {
                                                $scope.parentArgs.unshift($scope.args);
                                                is_new = false;
                                                total = $scope.parentArgs.length;
                                                angular.forEach($scope.parentArgs, function (item, i) {
                                                    i = total - i;
                                                    item._sequence = i;
                                                });
                                            } else {
                                                $.extend(arg, $scope.args);
                                            }

                                            if (angular.isFunction(config.ui.specifics.afterSave)) {
                                                newPromise = config.ui.specifics.afterSave($scope, info);
                                            }

                                            if (newPromise && newPromise.then) {
                                                newPromise.then(function () {
                                                    $scope.close();
                                                });
                                            } else {
                                                $scope.close();
                                            }

                                        };

                                        rootFormSetDirty();
                                        if (promise && promise.then) {
                                            promise.then(complete);

                                        } else {
                                            complete();

                                        }

                                    };

                                }
                            });
                        }
                    };

                config.ui.specifics.parentArgs = info.scope.$eval(config.ui.args);
                config.ui.specifics.entity = info.scope.$eval(config.ui.model);

                info.scope.$watch(config.ui.args, function (neww, old) {
                    if (neww !== old) {
                        config.ui.specifics.parentArgs = neww;
                    }
                });

                angular.forEach(defaultSpecifics, function (v, k) {
                    if (config.ui.specifics[k] === undefined) {
                        config.ui.specifics[k] = v;
                    }
                });

                return 'plugins';
            };
        });


        modelsConfig(function (models) {
            var read_arguments = {
                _content: {
                    documents: {}
                },
                _plugin_group: {}
            };

            $.extend(models['23'], {
                viewModal: function (seller, removedOrAdded) {
                    $modal.open({
                        templateUrl: 'core/models/manage.html',
                        controller: function ($scope, currentAccount) {
                            var cartData;
                            $scope.seller = seller;
                            $scope.dialog = {
                                templateBodyUrl: 'seller/view_body.html',
                                toolbar: {
                                    templateActionsUrl: 'seller/view_actions.html',
                                    hideSave: true
                                }
                            };
                            $scope.accordions = {
                                closeOthers: true,
                                groups: [{
                                    label: $scope.seller.name,
                                    open: true
                                }, {
                                    label: 'Feedback'
                                }]
                            };

                            $scope.alreadyInCollection = false;
                            $scope.loadedCollection = models['18'].current().then(function (response) {
                                var collection = response.data.entity;
                                if ($.inArray($scope.seller.key, collection.sellers) !== -1) {
                                    $scope.alreadyInCollection = true;
                                }
                                return collection;
                            });

                            if ($scope.seller._feedback && $scope.seller._feedback.feedbacks) {
                                cartData = [];

                                angular.forEach($scope.seller._feedback.feedbacks, function (feedback) {
                                    feedback.positive_count = _.random(0, 100);
                                    feedback.negative_count = _.random(0, 100);
                                    feedback.neutral_count = _.random(0, 100);
                                    cartData.push({
                                        c: [{
                                            v: dateFilter(feedback.date, 'MMM')
                                        }, {
                                            v: feedback.positive_count
                                        }, {
                                            v: feedback.negative_count
                                        }, {
                                            v: feedback.neutral_count
                                        }]
                                    });

                                });

                                $scope.chartConfig = {
                                    type: "ColumnChart",
                                    data: {
                                        cols: [{
                                            id: "months",
                                            label: "Months",
                                            type: "string"
                                        }, {
                                            id: "positive",
                                            label: "Positive",
                                            type: "number"
                                        }, {
                                            id: "negative",
                                            label: "Negative",
                                            type: "number"
                                        }, {
                                            id: "neutral",
                                            label: "Neutral",
                                            type: "number"
                                        }],
                                        rows: cartData
                                    },
                                    options: {
                                        colors: ['green', 'red', 'gray'],
                                        series: {
                                            0: {
                                                axis: 'positive'
                                            },
                                            1: {
                                                axis: 'negative'
                                            },
                                            3: {
                                                axis: 'neutral'
                                            }
                                        },
                                        axes: {
                                            y: {
                                                positive: {
                                                    label: 'Positive'
                                                },
                                                negative: {
                                                    label: 'Negative',
                                                    side: 'right'
                                                },
                                                neutral: {
                                                    label: 'Neutral',
                                                    side: 'right'
                                                }
                                            }
                                        }
                                    }
                                };


                                $scope.feedbackStats = (function () {
                                    var positive_count = 0,
                                        neutral_count = 0,
                                        negative_count = 0,
                                        positive_average,
                                        negative_average,
                                        neutral_average,
                                        score,
                                        values = [];

                                    positive_average = parseFloat((positive_count / (positive_count + negative_count)) * 100).toFixed(1);
                                    negative_average = parseFloat((negative_count / (negative_count + positive_count)) * 100).toFixed(1);
                                    neutral_average = parseFloat((neutral_count / (neutral_count + negative_count + positive_count)) * 100).toFixed(1);

                                    if ((positive_count - negative_count) > 0) {
                                        score = positive_count - negative_count;
                                    } else {
                                        score = 0;
                                    }
                                    values[0] = positive_count;
                                    values[1] = neutral_count;
                                    values[2] = negative_count;
                                    values[3] = positive_average;
                                    values[4] = negative_average;
                                    values[5] = neutral_average;
                                    values[6] = score;
                                    return values;
                                }());
                            }


                            $scope.viewContent = function (content) {
                                $modal.open({
                                    templateUrl: 'core/models/manage.html',
                                    controller: function ($scope) {
                                        $scope.dialog = {
                                            templateBodyUrl: 'core/misc/content_view_body.html',
                                            toolbar: {
                                                hideSave: true
                                            }
                                        };
                                        $scope.content = content;
                                        $scope.close = function () {
                                            $scope.$close();
                                        };
                                    }
                                });
                            };

                            $scope.toggleCollection = function () {
                                $scope.loadedCollection.then(function (collection) {
                                    var loadedCollection = collection,
                                        removed = false;
                                    if ($scope.alreadyInCollection) {
                                        removed = true;
                                        loadedCollection.sellers.remove($scope.seller.key);
                                    } else {
                                        loadedCollection.sellers.unshift($scope.seller.key);
                                    }
                                    models['18'].actions.update({
                                        account: currentAccount.key,
                                        sellers: loadedCollection.sellers,
                                        notify: loadedCollection.notify
                                    }).then(function (newResponse) {
                                        var updatedCollection = newResponse.data.entity;
                                        //modals.alert('Successfully ' + (removed ? 'removed seller from your' : 'added seller to your') +  ' colleciton.');
                                        $scope.alreadyInCollection = !removed;
                                        // update cache
                                        $.extend(loadedCollection, updatedCollection);
                                        if (angular.isFunction(removedOrAdded)) {
                                            removedOrAdded(updatedCollection, $scope.alreadyInCollection);
                                        }
                                    });
                                });
                            };

                            $scope.close = function () {
                                $scope.$close();
                            };
                        },
                    });
                },
                current: function (args) {
                    if (!args) {
                        args = {};
                    }
                    args.account = currentAccount.key;
                    return this.actions.read(args, {
                        cache: 'currentSeller',
                        cacheType: 'memory'
                    });
                },
                manageModal: function (accountKey) {
                    var fields = modelsMeta.getActionArguments(this.kind, 'update'),
                        config;
                    fields._content.ui.label = false;
                    fields._content.modelclass.documents.ui = {
                        label: false,
                        specifics: {
                            listView: 'content-list-view',
                            listConfig: {
                                perLine: 1
                            }
                        }
                    };
                    fields._plugin_group.modelclass.plugins.ui = {
                        label: false,
                        specifics: {
                            listView: 'plugin-list-view'
                        }
                    };
                    fields.logo.ui.label = 'Select Logo';
                    fields.logo.ui.specifics = {
                        displayImageConfig: {
                            size: 240
                        }
                    };
                    fields._plugin_group.ui.label = false;
                    config = {
                        kind: this.kind,
                        action: 'update',
                        fields: _.toArray(fields),
                        toolbar: {
                            submitNative: true
                        },
                        excludeFields: ['account', 'read_arguments'],
                        argumentLoader: function ($scope) {
                            var args = this.defaultArgumentLoader($scope);
                            args.account = accountKey;
                            if (args._content === null) {
                                args._content = {
                                    kind: '21',
                                    documents: []
                                };
                            }
                            args.read_arguments = read_arguments;
                            return args;
                        },
                        scope: {
                            accordions: {
                                closeOthers: true,
                                groups: [{
                                    label: 'General',
                                    open: true,
                                    key: 'general',
                                    fields: ['name', 'logo'],
                                }, {
                                    label: 'Contents',
                                    fields: ['_content']
                                }, {
                                    label: 'Plugins',
                                    fields: ['_plugin_group'],
                                }]
                            }
                        }
                    };

                    modelsEditor.create(config).read({}, {
                        account: accountKey,
                        read_arguments: read_arguments
                    });

                }
            });

        });

    });

}());(function () {
    'use strict';
    angular.module('app')
        .controller('AdminListCtrl', function ($scope, models, $stateParams, GLOBAL_CONFIG, searchBuilder, $state, $rootScope) {

            var kind = $stateParams.kind,
                query = null,
                args = {};

            try {
                query = JSON.parse($stateParams.query);
                args = query;
            } catch (ignore) {}

            $scope.config = {
                titles: GLOBAL_CONFIG.admin.listTitles,
                kind: kind
            };

            $rootScope.pageTitle = 'Administer ' + $scope.config.titles[kind];

            $scope.manage = function (entity) {
                models[kind].adminManageModal(entity);
            };
            $scope.search = searchBuilder.create();
            $.extend($scope.search, {
                doSearch: function () {
                    $state.go('admin-list', {
                        kind: this.kind,
                        query: JSON.stringify({
                            search : this.send
                        })
                    });
                },
                results: [],
                pagination: models[kind].paginate({
                    args: args,
                    kind: kind,
                    complete: function (response) {
                        $scope.search.results.extend(response.data.entities);
                    }
                })
            });

            $scope.search.kind = kind;
            if (!query) {
                query = $scope.search.pagination.args;
            }
            $scope.search.changeKindUI();
            if (query) {
                $scope.search.setSearch(kind, query.search);
            }
            $scope.scrollEnd = {loader: $scope.search.pagination};
            $scope.search.pagination.load();


        }).directive('adminListViewItem', function (GLOBAL_CONFIG) {
            return {
                scope: {
                    ent: '=adminListViewItem'
                },
                restrict: 'A',
                template: '<span ng-include="template"></span>',
                link: function (scope, element, attrs) {
                    var template = 'admin/list_view/default.html';
                    if ($.inArray(attrs.adminListViewKind, GLOBAL_CONFIG.admin.listViewDirective) !== -1) {
                        template = 'admin/list_view/' + attrs.adminListViewKind + '.html';
                    }
                    scope.template = template;
                }
            };
        });
}());(function () {
    'use strict';
    angular.module('app').config(function ($stateProvider, GLOBAL_CONFIG) {

        $stateProvider
            .state('home', {
                url: '/',
                templateUrl: 'home/index.html',
                controller: 'HomePageCtrl'
            })
            .state('collections', {
                url: '/collections',
                templateUrl: 'home/index.html',
                controller: 'HomePageCtrl'
            })
            .state('seller-info', {
                url: '/seller/:key',
                controller: 'HomePageCtrl',
                templateUrl: 'home/index.html'
            })
            .state('sell-catalogs', {
                url: '/sell/catalogs',
                controller: 'SellCatalogsCtrl',
                templateUrl: 'catalog/list.html'
            })
            .state('sell-orders', {
                url: '/sell/orders',
                controller: 'SellOrdersCtrl',
                templateUrl: 'order/list.html'
            })
            .state('sell-carts', {
                url: '/sell/carts',
                controller: 'SellOrdersCtrl',
                templateUrl: 'order/list.html'
            })
            .state('buy-orders', {
                url: '/buy/orders',
                controller: 'BuyOrdersCtrl',
                templateUrl: 'order/list.html'
            })
            .state('buy-carts', {
                url: '/buy/carts',
                controller: 'BuyOrdersCtrl',
                templateUrl: 'buyer/carts.html'
            })
            .state('login-status', {
                url: '/login/status',
                template: '',
                controller: 'AccountLoginStatusCtrl'
            })
            .state('admin-list', {
                url: '/admin/list/:kind/:query',
                templateUrl: function ($stateParams) {

                    var defaults = 'admin/list.html',
                        config;

                    if ($stateParams.kind !== undefined) {
                        config = GLOBAL_CONFIG.admin.listTemplates[$stateParams.kind];
                        if (config && config.templateUrl) {
                            defaults = config.templateUrl;
                        }
                    }

                    return defaults;
                },
                controller: 'AdminListCtrl'
            });

    }).run(function (modelsInfo, endpoint, models, currentAccount, GLOBAL_CONFIG, modelsUtil) {
        $.extend(modelsInfo, window.MODELS_META);
        $.extend(currentAccount, window.CURRENT_ACCOUNT);
        modelsUtil.normalize(currentAccount);
        models.init();
        if (!GLOBAL_CONFIG.debug) {
            delete window.MODELS_META;
            delete window.CURRENT_ACCOUNT;
        }
    });
}());