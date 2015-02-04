(function () {
    'use strict';
    angular.module('app').value('modelsInfo', {}).value('currentAccount', {}).factory('errorHandling',
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
                            templateUrl: 'misc/dialog/errors.html',
                            controller: function ($scope, $modalInstance) {
                                $scope.errors = [];
                                angular.forEach(errors, function (error, key) {
                                    $scope.errors.push([key, errorHandling.translate(key, error)]);
                                });
                                $scope.ok = function () {
                                    $modalInstance.dismiss('ok');
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
            fieldSorter: function (prev, next) {
                var p1 = parseInt(prev.name, 10),
                    p2 = parseInt(next.name, 10);
                if (isNaN(p1)) {
                    p1 = 999999;
                }
                if (isNaN(p2)) {
                    p2 = 999999;
                }
                return p1 - p2;
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
            grid: {
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
            },
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
            newHeightByWidth:  function (original_width, original_height, new_width) {
                var ratio;
                original_width = parseInt(original_width, 10);
                original_height = parseInt(original_height, 10);
                new_width = parseInt(new_width, 10);
                ratio = new_width / original_width; // get ratio for scaling image
                return (original_height * ratio);
            },
            fancyGrid: {
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
w:                  while (images.length > 0) {
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

            },
            responsive: {
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
            },
            url: {
                abs: function (part) {
                    return window.location.protocol + '//' + window.location.host + '/' + part;
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
                if (type === undefined) {
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
            },
            currentAccount: function () {
                return endpoint.post('current_account', '11', {}, {
                    cache: 'currentAccount',
                    cacheType: 'memory',
                    ignoreErrors: true
                }).then(function (response) {
                    var currentAccount = $injector.get('currentAccount');
                    $.extend(currentAccount, response.data.entity);
                    if (GLOBAL_CONFIG.debug) {
                        window._currentAccount = currentAccount; // delete in production
                    }

                });
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

    }).factory('modelsMeta', function ($injector, GLOBAL_CONFIG) {

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
                argumentsToJson : function (entity, pretty) {
                    var ignore = ['_field_permissions', '_next_read_arguments', '_read_arguments', '_action_permissions', 'ui'];
                    return JSON.stringify(entity,
                        function (key, value) {
                            var val = value, newval;

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
                            } else if (value &&  document === value) {
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
    }).factory('underscoreTemplate', function () {

        return {
            get: function (path, typecheck) {
                if (typecheck) {
                    typecheck = '[type="text/underscore-template"]';
                } else {
                    typecheck = '';
                }
                var find = $('script[id="' + path + '"]' + typecheck),
                    contents = find.text();
                if (!find.length) {
                    console.error('underscore ' + typecheck + ' template not found ' +
                        path);
                }
                return _.template(contents);
            }
        };
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
                            errorHandling.modal(angular.isString(rejection.data) ? {traceback: rejection.data} : rejection.data.errors);
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
            }
            ]);

    }]).factory('modelsEditor', function ($modal, endpoint, $q, helpers,
        modelsUtil, errorHandling, models, modelsMeta, $timeout, $filter, formInputTypes, recordAccordion) {

        var modelsEditor = {
            create: function (new_config) {

                var config = {
                    showClose: true,
                    closeAfterSave: false,
                    action: 'update',
                    templateBodyUrl: 'entity/dialog/editor_default_body.html',
                    templateFooterUrl: 'entity/dialog/editor_default_footer.html',
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
                        if (entityCopy._read_arguments) {
                            args.read_arguments = entityCopy._read_arguments;
                        }

                        if (entityCopy._next_read_arguments) {
                            args._next_read_arguments = entityCopy._next_read_arguments;
                        }

                        $.extend(args, $scope.withArgs);

                        args.action_id = $scope.config.action;
                        args.action_model = $scope.config.kind;
                        return args;
                    },
                    argumentLoader: function ($scope) {
                        return this.defaultArgumentLoader($scope);
                    },
                    defaultPrepareReadArguments: function ($scope) {

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
                }, actionArguments, modelsEditorInstance;

                helpers.extendDeep(config, new_config);

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
                        ctrl = function ($scope, $modalInstance) {
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
                                    $scope.historyConfig.key = $scope.entity.key;
                                    if ($scope.args.ui.rule.field._records.visible) {
                                        recordAccordion.attach($scope.accordions);
                                    }
                                };
                            modelsUtil.normalize(entity);
                            $scope.container = {
                                action: endpoint.url
                            };

                            config.getScope = function () {
                                return $scope;
                            };

                            $scope.withArgs = args;
                            $scope.config = config;
                            $scope.entity = entity;
                            $scope.$modalInstance = $modalInstance;
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
                            console.log('modelsEditor.init', $scope);

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
                                if ($modalInstance.dismiss) {
                                    $modalInstance.dismiss('close');
                                } else {
                                    $modalInstance.hide();
                                }
                                if (config.afterClose) {
                                    config.afterClose($scope);
                                }
                            };

                            $scope.$on('$destroy', function () {
                                config.getScope = undefined;
                            });

                            if (angular.isDefined(config.scope)) {
                                $.extend($scope, config.scope);
                                delete config.scope;
                            }

                            $scope.formBuilder = {
                                '0': []
                            };

                            // if no accordions are defined, use the auto-builder
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

                        };

                        ctrl.$inject = ['$scope', '$modalInstance'];

                        opener[fn]({
                            templateUrl: 'entity/dialog/editor.html',
                            controller: ctrl
                        });

                        return this;
                    },
                };

                return modelsEditorInstance;

            }
        };

        return modelsEditor;

    }).factory('formInputTypes', function (underscoreTemplate, $timeout, $parse,
        endpoint, modelsMeta, models, $q, $filter, $modal, helpers,
        errorHandling, modals) {

        var inflector = $filter('inflector'),
            formInputTypes = {
                _SelectBox: function (info) {
                    if (angular.isDefined(info.config.ui.placeholder)) {
                        info.config.ui.placeholder = 'Select...';
                    }

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
                                results: {
                                    'default': true,
                                    '13': false,
                                    '24': false
                                },
                                query: {
                                    '24': true
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
                                        args.search.filters.push({field: 'name', operator: '==', value: term});
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
                        actionArguments = modelsMeta.getActionArguments(config.kind, 'search'),
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
                            if (override.cache && angular.isDefined(override.cache.query)) {
                                opts.cache = override.cache.query;
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
                                                    if (!_.findWhere(config.ui.specifics.entities, {key: ent.key})) { // this is pretty slow. however can be sped up with key-value monitoring
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
                                                if (!_.findWhere(config.ui.specifics.entities, {key: id})) { // slow
                                                    config.ui.specifics.entities.unshift(response.data.entities[0]);
                                                }
                                            } else {
                                                angular.forEach(fetchedEntities, function (ent) {
                                                    if (!_.findWhere(config.ui.specifics.entities, {key: ent.key})) { // slow
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
                        listFields = [],
                        newSort = [],
                        newListFields = [],
                        defaults,
                        defaultSortable,
                        buildPaths,
                        rootArgs,
                        rootFormSetDirty = helpers.callable(info.scope.formSetDirty);

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

                    if (noSpecifics || !config.ui.specifics.listFields) {

                        angular.forEach(defaultFields, function (field) {
                            if (!noSpecifics && (config.ui.specifics.excludeListFields &&
                                    $.inArray(field.code_name, config.ui.specifics.excludeListFields) !== -1)) {
                                return;
                            }

                            listFields.push({
                                key: field.code_name,
                                generated: true,
                                label: (field.ui && field.ui.label ? field.ui.label : inflector(field.code_name, 'humanize'))
                            });
                        });

                        if (!noSpecifics && angular.isDefined(config.ui.specifics.onlyListFields)) {
                            newListFields = [];
                            angular.forEach(config.ui.specifics.onlyListFields, function (key) {
                                var find = _.findWhere(listFields, {
                                    key: key
                                });
                                if (find) {
                                    newListFields.push(find);
                                }
                            });

                            listFields = newListFields;
                        }

                    }

                    defaults = {
                        listFields: listFields,
                        fields: fields,
                        addNewText: 'Add ' + inflector(config.code_name, 'humanize'),
                        addText: '{{config.ui.specifics.addNewText}}'
                    };

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
                        whatSortMeans: function () {
                            modals.alert('Grab the button to start sorting.');
                        },
                        handle: '.sort-handle',
                        sort: function (e, ui) {
                            var sample = ui.placeholder.next();
                            if (sample.length) {
                                ui.placeholder.width(sample.width()).height(sample.height());
                            }
                            info.scope.$broadcast('itemOrderSorting');
                        },
                        stop: function () {
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
                    $.extend(defaultSortable, config.ui.specifics.sortableOptions);
                    config.ui.specifics.sortableOptions = defaultSortable;
                    config.ui.init.add('checkDisabledStateForSortable', function () {
                        var fieldIsWritable = $parse(config.ui.writableCompiled);
                        config.ui.specifics.sortableOptions.disabled = !fieldIsWritable(info.scope);
                    });

                    info.scope.$watch(config.ui.args, function (neww, old) {
                        if (neww !== old) {
                            config.ui.specifics.parentArgs = neww;
                        }
                    });

                    buildPaths = function () {
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
                        rootArgs = (config.ui.specifics.getRootArgs ? config.ui.specifics.getRootArgs() : config.ui.specifics.rootScope.args);
                        config.ui.specifics.reader = models[rootArgs.action_model].reader({
                            kind: rootArgs.action_model,
                            key: rootArgs.key,
                            next: rootArgs._next_read_arguments,
                            access: config.ui.realPath,
                            complete: function (items) {
                                config.ui.specifics.parentArgs.extend(items);
                            }
                        });

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
                            info.scope.$emit('itemDelete', arg);
                            info.scope.$broadcast('itemDelete', arg);
                            rootFormSetDirty();
                        };

                        config.ui.specifics.manage = function (arg, defaultArgs) {

                            buildPaths();

                            $modal.open({
                                template: underscoreTemplate.get(config.ui.specifics.templateUrl ? config.ui.specifics.templateUrl : 'underscore/form/dialog/structured.html')({
                                    config: config
                                }),
                                controller: function ($scope, $modalInstance, modelsUtil) {
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
                                        $modalInstance.dismiss('cancel');
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
                                                                    var keys = [], newReadArgs = {config: {keys: keys}};
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

                                    if (config.ui.specifics.scope) {
                                        $.extend($scope, config.ui.specifics.scope);
                                    }

                                    if (angular.isFunction(config.ui.specifics.init)) {
                                        config.ui.specifics.init($scope);
                                    }

                                }
                            });
                        };

                        config.ui.specifics.create = config.ui.specifics.manage;

                    }

                    return 'structured';
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

                    return 'image';
                },
                SuperImageStructuredProperty: function (info) {
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
                    info.config.ui.specifics.options = {
                        datepickerPopup: 'yyy-MM-dd'
                    };
                    return 'datetime';
                }
            };

        return formInputTypes;

    }).factory('outputTypes', function (dateFilter, GLOBAL_CONFIG, modelsMeta) {
        var outputTypes = {
            SuperDateTimeProperty: function (input, field) {
                var date = new Date(input);
                return dateFilter(date, GLOBAL_CONFIG.date.format);
            }
        };
        return outputTypes;
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

    }).factory('modals', function ($modal, $q, helpers) {

        return {
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
                return this.create(theConfig);
            },
            create: function (extraConfig) {
                var config = {
                    message: '',
                    type: 'notice'
                };
                helpers.extendDeep(config, extraConfig);
                return $modal.open({
                    windowClass: 'modal-medium',
                    templateUrl: 'misc/dialog/' + config.type + '.html',
                    controller: function ($scope, $modalInstance) {
                        var callback = (angular.isFunction(extraConfig) ? extraConfig : (extraConfig.ok ? extraConfig.ok : null));
                        config.dismiss = function () {
                            if (callback) {
                                callback.call(this);
                            }
                            $modalInstance.dismiss('dismiss');
                        };

                        if (!angular.isObject(extraConfig)) {
                            extraConfig = {};
                        }
                        $scope.config = config;
                    }
                });
            }
        };
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
                            placeholder: 'Select index',
                            writable: true,
                            attrs: {
                                'ng-change': 'search.makeFilters()'
                            },
                            specifics: {
                                choiceFilter: 'showFriendlyIndexName',
                                repeatAs: 'choice._index as '
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
                            placeholder: 'Type the ancestor key',
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
                        cfg;

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
                        this.fields.indexID.choices = cfg.indexes;

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
                            placeholder: 'Select value...',
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
                                placeholder: 'Select operator',
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
                                placeholder: 'Select direction',
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

                        var got_filters = true, matchCount = 0, orderMatchCount = 0;

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
    }).factory('recordAccordion', function () {
        return {
            attach: function (accordions) {
                accordions.groups.push({
                    label: 'History',
                    key: 'history',
                    open: false,
                    include: 'misc/history.html'
                });
            }
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