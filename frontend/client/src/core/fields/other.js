(function () {
    'use strict';
    angular.module('app')
        .directive('validFile', function () {
            return {
                require: 'ngModel',
                link: function (scope, el, attrs, ngModel) {
                    el.bind('change', function () {
                        scope.$apply(function () {
                            ngModel.$setViewValue(el.val());
                            ngModel.$render();
                        });
                    });
                }
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
        .directive('generateUploadUrl', ng(function (endpoint, $rootScope) {
            return {
                restrict: 'A',
                require: '^form',
                link: function (scope, element, attrs, ctrl) {

                    var that = element,
                        form = that.parents('form:first'),
                        click = function (e) {
                            if (element.parents('button[disabled]:first').length) {
                                e.preventDefault();
                                return false;
                            }
                        },
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

                    element.on('change', change)
                           .on('click', click);

                    scope.$on('$destroy', function () {
                        $(element).off('change', change);
                    });

                    scope.$on('ngUploadComplete', reset);
                    scope.$on('ngUploadError', change);
                }
            };
        })).directive('submitIfFiles', ng(function ($parse, helpers) {
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
                            var promise,
                                isNative,
                                thingsHappened = helpers.form.wakeUp(ctrl, true);
                            if (thingsHappened) {
                                if (!scope.$$phase) {
                                    scope.$apply();
                                }
                            }
                            if (check && !check(scope)) {
                                return false;
                            }
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
                            }
                            promise = submit(scope, {
                                dontShowMessage: execute
                            });
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
        })).directive('submitIfValid', ng(function ($parse) {
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
        })).directive('showNumberOfSelectedFiles', function () {
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
                    scope.$on('ngUploadError', change);
                    scope.$on('$destroy', function () {
                        element.unbind('change', change);
                    });
                }
            };
        }).run(ng(function (formInputTypes, underscoreTemplate, $timeout, $parse,
            endpoint, modelsMeta, models, $q, $filter, $modal, helpers,
            errorHandling, modals, GLOBAL_CONFIG, snackbar) {

            formInputTypes.resolvable.extend(['SuperKeyProperty', 'SuperVirtualKeyProperty']);

            $.extend(formInputTypes, {
                SuperBooleanProperty: function (info) {
                    info.config.required = false;
                    if (!info.config.ui.specifics || angular.isUndefined(info.config.ui.specifics.type)) {
                        info.config.ui.specifics.type = 'checkbox';
                    }
                    return 'boolean';
                },
                SuperVirtualKeyProperty: function (info) {
                    return this.SuperKeyProperty(info);
                },
                _SuperKeyPropertyRepeated: function (info) {
                    var select = {};
                    info.config.ui.specifics.select = select;
                    return 'select_multiple';
                },
                SuperKeyProperty: function (info) {
                    if (info.config.searchable === false) {
                        helpers.fields.resolve(info.config);
                        return this.SuperStringProperty(info);
                    }
                    var config = info.config,
                        template = 'select_async',
                        defaults = {
                            cache: {
                                query: {
                                    '24': true,
                                    '12': 'all_countries',
                                    '13': function (key) {
                                        return key + '_all_regions';
                                    },
                                    '17': function (key) {
                                        return key + '_all_units';
                                    }
                                },
                                type: {
                                    '12': 'local',
                                    '17': 'local',
                                    '24': 'local',
                                    '13': 'local',
                                    'default': 'memory'
                                }
                            },
                            grouping: {},
                            view: {
                                'default': function (result) {
                                    if (!result) {
                                        return '';
                                    }
                                    return result.name;
                                }
                            },
                            finder: {},
                            init: {
                                '13': function (info) {
                                    info.scope.$watch(info.config.ui.parentArgs +
                                        '.country',
                                        function (neww, old) {
                                            if (neww !== old) {
                                                var args = info.scope.$eval(info.config.ui.parentArgs);
                                                args.region = null;
                                                info.config.ui.specifics.entities.empty();
                                                info.config.ui.specifics.initial(); // refresh results
                                            }
                                        });
                                }
                            },
                            queryFilter: {
                                '24': function (term, searchArguments) {
                                    return {
                                        search: {
                                            options: {limit: 300},
                                            orders: [{
                                                operator: 'asc',
                                                field: 'name'
                                            }],
                                            filters: [{
                                                value: ['indexable'],
                                                operator: 'ALL_IN',
                                                field: 'state'
                                            }, {
                                                value: null,
                                                operator: '==',
                                                field: 'parent_record'
                                            }]
                                        }
                                    };
                                },
                                '17': function (term, searchArguments, cacheFn) {
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

                                    if (config.code_name === 'uom') {
                                        if (cacheFn) {
                                            return cacheFn('uom');
                                        }
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

                                    if (config.code_name === 'currency') {
                                        if (cacheFn) {
                                            return cacheFn('currency');
                                        }
                                        argument.filters.push({
                                            value: 'Currency',
                                            field: 'measurement',
                                            operator: '=='
                                        });
                                    }

                                    if (cacheFn) {
                                        return cacheFn('units');
                                    }

                                    return searchDefaults;

                                },
                                '13': function (term, searchArguments, cacheFn) {
                                    var args = info.scope.$eval(info.config.ui.parentArgs);
                                    if ((args && args.country)) {
                                        if (cacheFn) {
                                            return cacheFn(args.country);
                                        }
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
                        exists = _.memoize(function (key) {
                            return _.findWhere(config.ui.specifics.entities, {key: key}) !== undefined;
                        }),
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

                    if (config.repeated) {
                        config.ui.fieldset = true;
                    }

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


                    if (angular.isUndefined(config.ui.specifics.grouping)) {
                        config.ui.specifics.grouping = defaults.grouping[config.kind];
                    }

                    finder = defaults.finder[config.kind];
                    if (override.finder) {
                        finder = override.finder;
                    }

                    config.ui.specifics.search.ready = initialPromise;
                    opts.cache = defaults.cache.query[config.kind];
                    opts.cacheType = defaults.cache.type[config.kind] || defaults.cache.type['default'];
                    if (override.cache && angular.isDefined(override.cache.query)) {
                        opts.cache = override.cache.query;
                    }
                    if (angular.isFunction(opts.cache)) {
                        opts._getCache = opts.cache;
                    }
                    if (override.cache && angular.isDefined(override.cache.type)) {
                        opts.cacheType = override.cache.type;
                    }

                    if (model && !config.ui.specifics.getEntities) {
                        if (model.actions.search) {
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
                                    if (angular.isFunction(opts._getCache)) {
                                        opts.cache = findArgs(null, actionArguments, opts._getCache);
                                    }
                                    if (finder) {
                                        config.ui.specifics.search.find = function (term) {
                                            return model.actions.search(findArgs(term, actionArguments), opts).then(function (response) {
                                                var entities = response.data.entities;
                                                angular.forEach(entities, function (ent) {
                                                    if (!exists(ent.key)) {
                                                        config.ui.specifics.entities.push(ent);
                                                    }
                                                });
                                            });
                                        };
                                    }
                                    config.ui.specifics.search.missing = function (id) {
                                        var defer,
                                            selectedIsArray = angular.isArray(id),
                                            hasAll = true;
                                        if (id === null || id === undefined || !id.length) {
                                            defer = $q.defer();
                                            defer.resolve();
                                            return defer.promise;
                                        }
                                        if (selectedIsArray) {
                                            angular.forEach(selectedIsArray, function (key) {
                                                if (exists(key)) {
                                                    hasAll = false;
                                                }
                                            });
                                        } else {
                                            hasAll = exists(id);
                                        }
                                        if (hasAll) {
                                            defer = $q.defer();
                                            defer.resolve(config.ui.specifics.entities);
                                            return defer.promise;
                                        }
                                        return model.actions.search({
                                            search: {
                                                keys: (selectedIsArray ? id : [id])
                                            }
                                        }, opts).then(function (response) {
                                            var fetchedEntities = response.data.entities;
                                            if (!selectedIsArray) {
                                                if (!exists(id)) {
                                                    config.ui.specifics.entities.unshift(response.data.entities[0]);
                                                }
                                            } else {
                                                angular.forEach(fetchedEntities, function (ent) {
                                                    if (!exists(ent.key)) {
                                                        config.ui.specifics.entities.push(ent);
                                                    }
                                                });
                                            }
                                            return config.ui.specifics.entities;
                                        });
                                    };
                                }
                                return model.actions.search(args, opts).then(response);
                            };
                            $timeout(function () {
                                config.ui.specifics.initial().then(function () {
                                    initialDefer.resolve();
                                });
                            });
                        } else {
                            config.ui.defer.resolve();
                        }
                    } else {
                        config.ui.defer.resolve();
                    }
                    info.scope.$on('$destroy', function () {
                        config.ui.specifics.entities = [];
                        exists.cache = {};
                    });
                    config.ui.specifics.async = true;
                    if (config.repeated) {
                        template = this._SuperKeyPropertyRepeated(info);
                    }
                    (function () {
                        var select = config.ui.specifics.select || config.ui.specifics.search,
                            args;
                        if (info.config.kind === '24') {
                            select.init = function (select, scope, element, attrs, ctrls) {
                                var splitout = function (entities) {
                                    angular.forEach(entities, function (ent) {
                                        ent.leafname = _.last(ent.name.split(' / '));
                                    });
                                };
                                select.afterClose = function () {
                                    select.product_categories.resetToTop();
                                };
                                select.openTemplate = 'core/select/product_categories.html';
                                select.windowClass = 'category-modal';
                                select.product_categories = {
                                    children: [],
                                    mapped: {},
                                    top: [],
                                    isLeaf: function (item) {
                                        return $.inArray('visible', item.state) !== -1;
                                    },
                                    resetToTop: function () {
                                        select.product_categories.children = [];
                                        select.product_categories.mapped = {};
                                    },
                                    next: function (item) {
                                        var newFilter = {
                                            search: {
                                                options: {limit: 300},
                                                orders: [{
                                                    operator: 'asc',
                                                    field: 'name'
                                                }],
                                                filters: [{
                                                    value: ['indexable'],
                                                    operator: 'ALL_IN',
                                                    field: 'state'
                                                }, {
                                                    value: null,
                                                    operator: '==',
                                                    field: 'parent_record'
                                                }]
                                            }
                                        };
                                        newFilter.search.filters[1].value = item.key;
                                        models['24'].actions.search(newFilter, opts).then(function (response) {
                                            var entities = response.data.entities,
                                                child = {
                                                    item: item
                                                },
                                                existing = select.product_categories.mapped[item.key];
                                            splitout(entities);
                                            if (existing) {
                                                child = existing;
                                            }
                                            child.visible = true;
                                            if (entities.length) {
                                                child.items = entities;
                                                select.product_categories.children.push(child);
                                                select.product_categories.mapped[item.key] = child;
                                            } else {
                                                select.select(item);
                                                select.product_categories.resetToTop();
                                            }
                                        });
                                    },
                                    prev: function (child) {
                                        var children = select.product_categories.children,
                                            reset = false;
                                        angular.forEach(children, function (value, index) {
                                            if (value === child) {
                                                value.visible = false;
                                                if (index === 0) {
                                                    reset = true;
                                                }
                                            }
                                        });
                                        if (reset) {
                                            // select.product_categories.resetToTop();
                                        }
                                    }
                                };
                                args = defaults.queryFilter[config.kind]();
                                args.search.options.limit = 400;
                                models[config.kind].actions.search(args, opts).then(function (response) {
                                    var entities = response.data.entities;
                                    splitout(entities);
                                    select.product_categories.top = entities;
                                });
                            };
                        }
                    }());
                    return template;
                },
                SuperJsonProperty: function (info) {
                    info.config.ui.attrs['json-only'] = '';
                    return this.SuperTextProperty(info);
                },
                SuperDateTimeProperty: function (info) {
                    info.config.ui.attrs['time-date-picker-dialog'] = '';
                    info.config.ui.attrs.readonly = 'true';
                    return 'datetime';
                }
            });

        }));
}());
