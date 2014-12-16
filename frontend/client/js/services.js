(function () {
    'use strict';
    angular.module('app').value('modelsInfo', {}).value('currentAccount', {}).factory('errorHandling',
        function ($modal) {
            var translations = {
                    action_denied: function (reason) {
                        return 'You do not have permission to perform this action.';
                    },
                    invalid_image_type: 'You have supplied incorrect type of image format',
                    invalid_model: 'You have requested access to resource that does not exist',
                    invalid_action: 'You have requested access to the action that does not exist',
                    required: function (fields) {
                        return 'Some values are missing: ' + fields.join(', ');
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
                            templateUrl: 'misc/modal/errors.html',
                            controller: function ($scope, $modalInstance) {
                                $scope.errors = [];
                                angular.forEach(errors, function (error, key) {
                                    $scope.errors.push(errorHandling.translate(key, error));
                                });
                                $scope.ok = function () {
                                    $modalInstance.dismiss('ok');
                                };
                            }
                        });
                    }
                };

            return errorHandling;
        }).factory('helpers', function () {

        var helpers = {
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
            calculateGrid: function (canvas_width, max_width, min_width, margin) {
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
                        image.width = Math.floor(height * image.proportion);
                        image.height = Math.floor(height);
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

            }
        };

        window._helpers = helpers; // @todo remove on production

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
            // invalidates all caches that we use
            invalidateCache: function (key) {
                if (angular.isArray(key)) {
                    angular.forEach(key, function (k) {
                        endpoint.invalidateCache(k);
                    });

                    return true;
                }

                angular.forEach(cacheRegistry, function (cache) {
                    cache.remove(cache_prefix + key);
                });

            },
            url: GLOBAL_CONFIG.apiEndpointPath,
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
                    cacheType: 'memory'
                }).then(function (response) {

                    var currentAccount = $injector.get('currentAccount');
                    $.extend(currentAccount, response.data.entity);
                    window._currentAccount = currentAccount; // delete in production

                });
            },
            modelsMeta: function () {
                return endpoint.get(null, null, {}, {
                    cache: 'modelsMeta',
                    cacheType: 'memory',
                    url: GLOBAL_CONFIG.apimodelsMetaPath
                }).then(function (response) {
                    var modelsInfo = $injector.get('modelsInfo');
                    $.extend(modelsInfo, response.data);
                });
            }
        };

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

    }).factory('modelsMeta', function ($injector) {

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
                fields;
            if (!angular.isDefined(info)) {
                return undefined;
            }
            getAction = info.mapped_actions[action];
            if (!angular.isDefined(getAction)) {
                console.error('action ' + action + ' not found for kind ' + kind_id);
                return undefined;
            }
            fields = angular.copy(getAction['arguments']);

            standardize(fields);

            return fields;
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
                'actions': kind._actions,
                'mapped_actions': actions,
                'fields': fields,
                'name': kind.__name__
            };

            return data;
        };

        // expose this to global intentionally, this is used mostly for console debugging @todo remove in production
        window._modelsMeta = modelsMeta;

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
    }).factory('modelsUtil', function (modelsMeta, ruleEngine) {
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
                                    } else {
                                        /*value = {
                                            kind: field.modelclass_kind
                                        };
                                        entity[field.code_name] = value;*/
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

        window._modelsUtil = modelsUtil;
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
                            errorHandling.modal(angular.isString(rejection.data) ? {'traceback': rejection.data} : rejection.data.errors);
                            enableUI();
                            return $q.reject(rejection);
                        }
                        if (data && data.errors) {
                            errorHandling.modal(rejection.data.errors);
                            reject = (rejection.config.rejectOnErrors === undefined || rejection.config.rejectOnErrors === true);
                            if (data.errors.action_denied) {
                                reject = true;
                            }
                            if (reject) {
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
        modelsUtil, errorHandling, models, modelsMeta, $timeout, $filter, formInputTypes) {

        var modelsEditor = {
            create: function (new_config) {

                var config = {
                    showClose: true,
                    closeAfterSave: false,
                    action: 'update',
                    templateBodyUrl: 'entity/modal/editor_default_body.html',
                    templateFooterUrl: 'entity/modal/editor_default_footer.html',
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
                                        //path.config.limit = arg.length; // @todo this cannot be used because of entities that have different order by
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

                        $modal.open({
                            templateUrl: 'entity/modal/editor.html',
                            controller: function ($scope, $modalInstance) {
                                var inflector = $filter('inflector'),
                                    field,
                                    done = {},
                                    found = false,
                                    realTotal = 0;
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
                                        if (angular.isDefined(config.afterSave)) {
                                            config.afterSave($scope);
                                        }
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
                                    var new_args = config.argumentLoader($scope);
                                    $.extend($scope.args, new_args);
                                    if (angular.isDefined(config.afterComplete)) {
                                        config.afterComplete($scope);
                                    }

                                    if (config.closeAfterSave) {
                                        $timeout(function () {
                                            $scope.close();
                                        });
                                    }

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
                                    $modalInstance.dismiss('close');
                                    if (config.afterClose) {
                                        config.afterClose($scope);
                                    }
                                };

                                $scope.$on('$destroy', function () {
                                    config.getScope = undefined;
                                });

                                // load scope from config into the current scope
                                $.extend($scope, config.scope);

                                $scope.formBuilder = {
                                    '0': []
                                };

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
                                            $scope.accordions.groups.push({
                                                label: inflector((field.ui.label || field.code_name), 'humanize'),
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

                                // call config constructor, needed for posible on-spot configurations
                                config.defaultInit($scope);
                                config.init($scope);
                                console.log('modelsEditor.scope', $scope);

                            }
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
        errorHandling) {

        var inflector = $filter('inflector'),
            formInputTypes = {
                Custom: function (info) {
                    if (info.config.init !== undefined) {
                        info.config.init(info);
                    }

                    return info.config.template;
                },
                _SelectBox: function (info) {
                    if (angular.isDefined(info.config.ui.placeholder)) {
                        info.config.ui.placeholder = 'Select...';
                    }

                    if (!angular.isDefined(info.config.ui.specifics.repeatAs)) {
                        info.config.ui.specifics.repeatAs = '';
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
                    return this.SuperStringProperty(info);
                },
                SuperIntegerProperty: function (info) {
                    var config = info.config;

                    if (config.choices) {
                        return this._SelectBox(info);
                    }

                    return this.SuperFloatProperty(info);
                },
                SuperDecimalProperty: function (info) {
                    var config = info.config;
                    if (config.choices) {
                        return this._SelectBox(info);
                    }
                    return this.SuperFloatProperty(info);
                },
                SuperBooleanProperty: function (info) {
                    return 'boolean';
                },
                SuperVirtualKeyProperty: function (info) {
                    return this.SuperKeyProperty(info);
                },
                SuperKeyProperty: function (info) {
                    var config = info.config,
                        internalConfig = info.config.ui.specifics.internalConfig,
                        defaultInternalConfig = {
                            search: {
                                cacheResults: {
                                    'default': true,
                                    '13': false
                                },
                                propsFilterResults: {
                                    'default': '{name: $select.search}',
                                    '12': '{name: $select.search, code: $select.search}'
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
                                    '13': function () {
                                        info.scope.$watch(info.config.ui.parentArgs +
                                            '.country',
                                            function (neww, old) {
                                                if (neww !== old) {
                                                    var args = info.scope.$eval(info.config.ui.parentArgs);
                                                    args.region = null;
                                                    config.ui.specifics.search();
                                                }
                                            });
                                    }
                                },
                                query: {},
                                // this query filter config should be included into places where it's supposed to be
                                // but for quick access its located here
                                queryfilter: {
                                    '17': function (term, search_action) {
                                        var search = {
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
                                            argument = search.search;

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

                                        return search;

                                    },
                                    '13': function (term, search_action) {
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
                            }
                        },
                        propsFilter,
                        init,
                        defaultInternalSearch,
                        actionSearch,
                        shouldCache = false,
                        searchCommand,
                        cacheOption;

                    if (!angular.isDefined(internalConfig)) {
                        info.config.ui.specifics.internalConfig = defaultInternalConfig;
                        internalConfig = defaultInternalConfig;
                    } else {
                        helpers.extendDeep(defaultInternalConfig, internalConfig);
                        internalConfig = defaultInternalConfig;
                        info.config.ui.specifics.internalConfig = internalConfig;

                    }

                    if (config.kind) {

                        propsFilter = internalConfig.search.propsFilterResults[config.kind];
                        if (!propsFilter) {
                            propsFilter = internalConfig.search.propsFilterResults['default'];
                        }
                        config.ui.specifics.propsFilter = propsFilter;

                    }

                    if (!config.ui.specifics.view) {
                        config.ui.specifics.view = function (result) {
                            var fn = internalConfig.search.view[config.kind];
                            if (!fn) {
                                fn = internalConfig.search.view['default'];
                            }

                            return fn(result);
                        };
                    }
                    init = internalConfig.search.init[config.kind];
                    if (angular.isDefined(init)) {
                        init();
                    }

                    if (!angular.isDefined(config.ui.specifics.search) && !angular.isDefined(config.ui.specifics.entities)) {
                        defaultInternalSearch = internalConfig.search[config.kind];
                        if (defaultInternalSearch !== undefined) {
                            config.ui.specifics.search = defaultInternalSearch;

                        } else {

                            actionSearch = modelsMeta.getActionArguments(config.kind, 'search');

                            if (actionSearch !== undefined) {
                                cacheOption = internalConfig.search.cacheResults[config.kind];
                                if (cacheOption !== undefined && cacheOption !== false) {
                                    shouldCache = cacheOption;
                                } else if (cacheOption !== false) {
                                    shouldCache = internalConfig.search.cacheResults['default'];
                                }

                                searchCommand = function (term) {
                                    var params = actionSearch.search['default'],
                                        fn = internalConfig.search.queryfilter[config.kind],
                                        args = {},
                                        model;
                                    if (angular.isFunction(fn)) {
                                        args = fn(term, actionSearch);
                                    } else {
                                        args = {
                                            search: params
                                        };
                                    }
                                    if (args === false) {
                                        return false;
                                    }
                                    model = models[config.kind];
                                    if (angular.isDefined(model) && model.actions && angular.isFunction(model.actions.search)) {
                                        model.actions.search(args, {
                                            cache: shouldCache
                                        }).then(function (response) {
                                            config.ui.specifics.entities = response.data.entities;
                                        });
                                    } else {
                                        config.ui.specifics.entities = [];
                                    }

                                };

                                if (config.ui.specifics.entities === undefined && shouldCache !== false) {
                                    searchCommand();
                                }

                                if (shouldCache === false) {
                                    config.ui.specifics.search = function (term) {
                                        searchCommand(term);
                                    };
                                }

                            } else {
                                console.error('No search action found in kind: ' + config.kind);
                            }

                        }

                    }
                    if (angular.isFunction(config.ui.specifics.entities)) {
                        config.ui.specifics.entities = config.ui.specifics.entities();
                    }
                    if (!angular.isDefined(config.ui.placeholder)) {
                        config.ui.placeholder = 'Select...';
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
                        rootArgs;

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

                            info.scope.$broadcast('itemOrderChanged');
                        }
                    };

                    $.extend(defaultSortable, config.ui.specifics.sortableOptions);

                    config.ui.specifics.sortableOptions = defaultSortable;

                    config.ui.preRender.push(function () {
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
                            if (!angular.isDefined(field.ui.formName)) {
                                field.ui.formName = config.ui.formName + '_' + field.code_name;
                            }
                            field.ui.writable = copyWritable;
                            config.ui.specifics.formBuilder.push(field);
                        });
                    };

                    buildPaths();

                    if (config.ui.specifics.remote) {
                        rootArgs = (config.ui.specifics.getRootArgs ? config.ui.specifics.getRootArgs() : config.ui.specifics.rootScope.args);
                        if (!angular.isDefined(config.ui.specifics.reader)) {
                            config.ui.specifics.reader = models[rootArgs.action_model].reader({
                                kind: rootArgs.action_model,
                                key: rootArgs.key,
                                next: rootArgs._next_read_arguments,
                                access: config.ui.realPath,
                                callback: function (items) {
                                    config.ui.specifics.parentArgs.extend(items);
                                }
                            });
                        }

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

                        if (config.ui.specifics.remove === undefined) {
                            config.ui.specifics.remove = function (arg) {
                                arg._state = 'deleted';
                                info.scope.$emit('itemDelete', arg);
                                info.scope.$broadcast('itemDelete', arg);
                            };
                        }


                        if (config.ui.specifics.manage === undefined) {
                            config.ui.specifics.manage = function (arg, defaultArgs) {

                                buildPaths();

                                $modal.open({
                                    template: underscoreTemplate.get(config.ui.specifics.templateUrl ? config.ui.specifics.templateUrl : 'underscore/form/modal/structured.html')({
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
                                        } else if (!config.ui.specifics.modal) {
                                            length = _.last(arg.ui.access);
                                        }

                                        arg.ui.access = angular.copy(config.ui.realPath);
                                        if (!config.ui.specifics.modal) {
                                            arg.ui.access.push(length);
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
                                            field = angular.copy(field);
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
                                            };

                                            $scope.noComplete = function () {
                                                // fired when the scope.complete() does not get fired i.e. when no files were sent for upload
                                                if (angular.isDefined(config.ui.specifics.noComplete)) {
                                                    config.ui.specifics.noComplete($scope);
                                                }
                                            };

                                            $scope.completeError = function (response) {
                                                // fired when it failed to send http-form-data rpc
                                                if (angular.isDefined(config.ui.specifics.afterCompleteError)) {
                                                    config.ui.specifics.afterCompleteError($scope, response);
                                                }
                                            };


                                        } else {


                                            $scope.save = function () {
                                                if (!$scope.validateForm()) { // check if the form is valid
                                                    return false;
                                                }
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
                                                                $scope.close();
                                                            });
                                                        } else {
                                                            $scope.close();
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

                        }

                        if (config.ui.specifics.create === undefined) {
                            config.ui.specifics.create = config.ui.specifics.manage;
                        }
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
                    return 'datetime';
                }
            };

        return formInputTypes;

    }).factory('outputTypes', function (dateFilter, GLOBAL_CONFIG, modelsMeta) {
        var outputTypes = {
            SuperDateTimeProperty: function (input, field) {
                var date = new Date(input);
                return dateFilter(date, GLOBAL_CONFIG.dateFormat);
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
    }).factory('models', function (endpoint, modelsMeta, $injector, modelsConfig, helpers) {
        // models depency should never be included directly or indirectly, because its depency on modelsMeta
        var models = {}, // all model instances
            modelCreate = function (kind) {
                // creates a new service based on kind
                // it will map every action into function which can be called in this way: models['12'].actions.search() etc.
                var config = {},
                    service = {
                        kind: kind,
                        actions: {},
                        // shorthands
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
                                    more: false,
                                    cursor: null,
                                    args: theConfig.args,
                                    load: function () {
                                        var promise = that.actions.search(theConfig.args, theConfig.config);
                                        promise.then(function (response) {
                                            paginate.more = response.data.more;
                                            paginate.cursor = response.data.cursor;
                                            if (angular.isFunction(config.callback)) {
                                                config.callback.call(this, response);
                                            }
                                        });
                                        return promise;
                                    }
                                };
                            theConfig.args.search = searchAction.search['default'];
                            if (angular.isDefined(config.args)) {
                                helpers.extendDeep(theConfig.args, config.args);
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
                                access: config.access,
                                more: canLoadMore(config.next),
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
                                    if (!this.more) {
                                        console.debug('nothing to load, more=false');
                                        return false;
                                    }
                                    var that = this,
                                        next = that.next,
                                        promise;

                                    if (!next) {
                                        next = angular.copy(config.next);
                                    }

                                    promise = models[config.kind].actions.read({
                                        key: config.key,
                                        read_arguments: next
                                    });

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

                                        if (angular.isFunction(config.callback)) {
                                            config.callback(items);
                                        }

                                        loadedNext = response.data.entity._next_read_arguments;
                                        that.more = canLoadMore(loadedNext);

                                        if (that.more) {
                                            that.next = response.data.entity._next_read_arguments;
                                        }
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

                        if (!angular.isDefined(defaults.cache) && defaults.cache !== false) {
                            return endpoint.post(action_key, kind, defaultArgs, defaults);
                        }

                        cache_key = config.cache;
                        if (cache_key !== true) {
                            // btoa is base64encode built-in
                            cache_key = kind + '_' + action_key + '_' + window.btoa(angular.toJson(defaultArgs));
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
        window._models = models;

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
                    templateUrl: 'misc/modal/' + config.type + '.html',
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
    }).factory('visualAid', function (modals) {
        return {
            navigate: function () {
                var start = function (args, i) {
                    var arg = args[i],
                        find = $(arg);
                    if (!arg) {
                        return;
                    }
                    if (angular.isString(arg)) {
                        if (find.length) {
                            find.click();
                            setTimeout(function () {
                                i += 1;
                                start(args, i);
                            }, 150);
                        } else {
                            modals.alert('Instruction failed at ' + arg + ', element not found ' + arg);
                        }
                    }
                };
                start(arguments, 0);
            }
        };
    }).factory('searchForm', function (modelsMeta) {
        var create = function () {
            var make = {
                kind: null,
                hide: false,
                filters: {},
                indexes: [],
                index_id: null,
                fields: {
                    index_id: {
                        type: 'SuperStringProperty',
                        choices: [],
                        code_name: 'index_id',
                        required: true,
                        ui: {
                            args: 'search.index_id',
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
                },
                changeKindUI: function () {
                    this.changeKind();
                    this.setSearch(this.kind, undefined);
                    this.makeFilters();
                },
                changeKind: function () {

                    var kindinfo = modelsMeta.get(this.kind),
                        search_argument = null,
                        cfg;

                    if (kindinfo) {
                        try {
                            search_argument = kindinfo.mapped_actions.search['arguments'].search;
                            this.default_send = search_argument['default'];
                        } catch (ignore) {}

                        if (!search_argument) {
                            this.hide = true;
                            search_argument = {};
                        } else {
                            this.hide = false;
                        }

                        cfg = search_argument.cfg;
                        this.send.kind = this.kind;
                        this.filters = cfg.filters || {};
                        this.indexes = cfg.indexes || [];
                        this.index_id = null;
                        this.mapIndexes(cfg.indexes);
                        this.fields.index_id.choices = cfg.indexes;

                    }

                },
                changeOrderBy: function (e) {
                    e.field = this.indexes[this.index_id].orders[e._index][0];
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
                        that.send.filters = [];
                        that.send.orders = [];
                    }
                    that.fields.filters = [];
                    that.fields.orders = [];

                    indx = that.indexes[that.index_id];

                    angular.forEach(indx.filters, function (filter, i) {
                        field = that.filters[filter[0]];
                        field.required = 'search.index_id != null && search.send.filters.length';
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
                            required: 'search.index_id != null && search.send.filters.length',
                            ui: {
                                placeholder: 'Select direction',
                                writable: true,
                                args: 'search.send.orders[\'' + i + '\'].operator'
                            }
                        };

                        that.fields.orders.push(field);
                    });

                },
                discoverIndexID: function () {

                    var that = this,
                        filters = this.send.filters,
                        orders = this.send.orders;

                    angular.forEach(this.indexes, function (index, index_id) {

                        var got_filters = true;

                        if (index.filters) {
                            got_filters = false;
                            if (filters && filters.length) {
                                angular.forEach(index.filters, function (filter) {
                                    var gets = _.findWhere(filters, {
                                        field: filter[0]
                                    });
                                    if (gets && $.inArray(gets.operator, filter[1]) !== -1) {
                                        got_filters = true;
                                        that.index_id = index_id;
                                    }
                                });
                            }

                        }


                        angular.forEach(index.orders, function (order, oi) {

                            var gets = _.findWhere(orders, {
                                field: order[0]
                            });

                            if (got_filters && gets && $.inArray(gets.operator, order[1]) !== -1) {
                                that.index_id = index_id;
                                gets._index = oi;
                            }
                        });

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

                    var kindinfo = modelsMeta.get(this.kind),
                        search_argument = null;
                    if (kindinfo) {
                        try {
                            search_argument = kindinfo.mapped_actions.search['arguments'].search;
                        } catch (ignore) {}

                        if (search_argument) {

                            if (search === undefined && search_argument['default']) {
                                this.send = search_argument['default'];
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
                },
            };
            return make;
        };
        return {
            create: create
        };
    });
}());