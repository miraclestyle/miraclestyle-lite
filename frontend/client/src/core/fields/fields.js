(function () {
    'use strict';
    angular.module('app')
        .run(ng(function (helpers, modals, $modal, GLOBAL_CONFIG) {
            if (!helpers.fields) {
                helpers.fields = {};
            }
            if (!helpers.form) {
                helpers.form = {};
            }
            $.extend(helpers.fields, {
                isFieldset: function (field) {
                    return (field.is_structured
                                || ((_.string.contains(field.type, 'KeyProperty')) && field.repeated)
                                || field.ui.fieldset);
                },
                sorter: function (prev, next) {
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
                applyGlobalConfig: function (config) {
                    if (angular.isUndefined(config.ui.help) && angular.isDefined(GLOBAL_CONFIG.fields.help[config._maker_])) {
                        config.ui.help = GLOBAL_CONFIG.fields.help[config._maker_][config.code_name];
                    }

                    if (angular.isUndefined(config.ui.emptyHelp) && angular.isDefined(GLOBAL_CONFIG.fields.emptyHelp[config._maker_])) {
                        config.ui.emptyHelp = GLOBAL_CONFIG.fields.emptyHelp[config._maker_][config.code_name];
                    }

                    if (angular.isUndefined(config.ui.label) && angular.isDefined(GLOBAL_CONFIG.fields.label[config._maker_])) {
                        config.ui.label = GLOBAL_CONFIG.fields.label[config._maker_][config.code_name];
                    }
                },
                utils: {
                    attrs: function (config) {
                        var defaults = this.defaultAttrs(config),
                            extra = this.extraAttrs(config),
                            attrs = [];

                        angular.extend(defaults, extra);

                        angular.forEach(defaults, function (value, key) {
                            attrs.push(key + (value ? '="' + value + '"' : ''));
                        });

                        return attrs.join(' ');
                    },
                    defaultAttrs: function (config) {
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
                        attrs.placeholder = config.ui.placeholder;

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

                        if (attrs.readonly) {
                            delete attrs['ng-disabled'];
                        }

                        return attrs;
                    },
                    extraAttrs: function (config) {
                        return config.ui.attrs;
                    },
                    label: function (config) {
                        var use = '{{config.ui.label}}';
                        if (config.ui.label === undefined) {
                            use = '{{config.ui.autoLabel|inflector:humanize}}';
                        }
                        return use;
                    }
                }
            });
            $.extend(helpers.form, {
                wakeUp: function (form, dirty) {
                    var happend = false;
                    angular.forEach(form, function (formElement) {
                        if (angular.isObject(formElement) && formElement.hasOwnProperty('$valid') && !formElement.$valid && angular.isFunction(formElement.$setViewValue)) {
                            formElement.$setViewValue(formElement.$viewValue !== undefined ? formElement.$viewValue : '');
                            formElement.$setDirty();
                            formElement.$setTouched();
                            if (dirty) {
                                form.$setDirty();
                            }

                            happend = true;
                        }
                    });

                    return happend;
                },
                setDirty: function () {
                    if (this.container && this.container.form) {
                        this.container.form.$setDirty();
                    }
                },
                setPristine: function () {
                    if (this.container && this.container.form) {
                        this.container.form.$setPristine();
                    }
                },
                validate: function () {
                    var form = this.container.form;
                    if (!form.$valid) {
                        helpers.form.wakeUp(form);
                        this.$broadcast('invalidForm');
                        return false;
                    }
                    return true;
                },
                leave: function (cb) {
                    var form = this.container.form;
                    if (form.$pristine) {
                        cb();
                    } else {
                        modals.confirm('discard', cb);
                    }
                }
            });

            $.extend(modals, {
                fields: {
                    remote: function (scope, field, config) {
                        $modal.open({
                            scope: scope,
                            templateUrl: 'core/models/manage.html',
                            controller: ng(function ($scope) {
                                var save = scope.save,
                                    complete = scope.complete,
                                    getTitle,
                                    initial = true;
                                getTitle = function () {
                                    return 'view' + helpers.toolbar.makeTitle(field.code_name);
                                };
                                field._title_.push(getTitle);
                                $scope.dialog = {
                                    templateBodyUrl: 'core/models/manage_body_default.html',
                                    toolbar: {}
                                };
                                $scope.parentContainer = $scope.container;
                                $scope.container = {};
                                $scope.close = angular.bind($scope, helpers.form.leave, function () {
                                    $scope.formSetPristine();
                                    $scope.$close();
                                });
                                $scope.formSetDirty = angular.bind($scope, helpers.form.setDirty);
                                $scope.formSetPristine = angular.bind($scope, helpers.form.setPristine);
                                $scope.formBuilder = {
                                    '0': [field]
                                };
                                $scope.layouts = {
                                    groups: [{
                                        label: false
                                    }]
                                };
                                $scope.$on('itemDelete', function () {
                                    $scope.formSetDirty();
                                });
                                $scope.$watch('parentContainer.form.$dirty', function (neww, old) {
                                    if (initial) {
                                        initial = false;
                                        return;
                                    }
                                    if (neww) {
                                        $scope.formSetDirty();
                                    } else {
                                        $scope.formSetPristine();
                                    }
                                });

                                $scope.$watch('entity.id', function () {
                                    $scope.dialog.toolbar.title = helpers.toolbar.buildTitle(field._title_);
                                });

                                $scope.save = function (dontShowMessage) {
                                    var maybePromise = save.call(scope, dontShowMessage);
                                    if (maybePromise) {
                                        maybePromise.then($scope.formSetPristine);
                                    }
                                    return maybePromise;
                                };

                                $scope.complete = function (response) {
                                    complete.call(scope, response);
                                    $scope.formSetPristine();
                                };

                                $scope.$on('$destroy', function () {
                                    if (angular.isArray(field.ui.specifics.parentArgs)) {
                                        field.ui.specifics.parentArgs.empty();
                                    }
                                    field._title_.remove(getTitle);
                                });
                            })
                        });
                    }
                }
            });
        }))
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
        .directive('repeatedText', ng(function (helpers) {
            return {
                require: 'ngModel',
                link: function (scope, element, attrs, ctrl) {

                    var worker = function (value, what) {

                            var test = false;

                            try {
                                if (what === 'list') {
                                    value = helpers.splitLines(value);
                                    value = _.uniq(value);
                                }
                                if (what === 'str') {
                                    if (angular.isArray(value)) {
                                        value = value.join('\n');
                                    }
                                }
                                test = true;

                            } catch (ignore) {}

                            ctrl.$setValidity('invalid', test);

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
        }))
        .directive('generateUploadUrl', ng(function (endpoint, $rootScope) {
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
        })).directive('formBuilder', ng(function ($compile, underscoreTemplate, modelsMeta) {
            return {
                restrict: 'A',
                require: '^form',
                templateUrl: 'core/fields/builder.html',
                scope: true,
                transclude: true,
                controller: ng(function ($scope, $element, $attrs) {
                    $scope.configurations = $scope.$eval($attrs.formBuilder);
                })
            };
        }))
        .directive('formInput', ng(function ($compile, underscoreTemplate,
            formInputTypes, helpers, GLOBAL_CONFIG) {

            var types = formInputTypes,
                utils = helpers.fields.utils;

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
                                directiveScope: function () {
                                    return scope;
                                },
                                specifics: {}, // used for property specific configurations
                                systemName: name,
                                name: name,
                                form: {
                                    root: ctrl,
                                    field: function () {
                                        return this.root[config.ui.name];
                                    },
                                    hasErrors: function () {
                                        if (!this.field()) {
                                            return false;
                                        }
                                        return Object.keys(this.field().$error).length;
                                    },
                                    messages: function () {
                                        if (!this.field()) {
                                            return false;
                                        }
                                        return ((this.field().$dirty && this.hasErrors()) ? this.field().$error : false) || config.ui;
                                    },
                                    shouldShowMessages: function () {
                                        if (config.ui.hideMessages) {
                                            return false;
                                        }
                                        return true;
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

                        helpers.fields.applyGlobalConfig(config);

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
                            /* console.warn('Field type: ' + config.type +
                                ' is not supported.'); */
                        }

                        scope.$on('$destroy', function () {
                            config.ui.directiveScope = undefined;
                            config.ui.form = undefined;
                        });

                    };

                    run();

                }

            };
        })).directive('compatibilityMaker', ng(function (modelsUtil) {
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
        }).factory('formInputTypes', ng(function (underscoreTemplate, $timeout, $parse,
            endpoint, modelsMeta, models, $q, $filter, $modal, helpers,
            errorHandling, modals, GLOBAL_CONFIG, snackbar) {

            var inflector = $filter('inflector'),
                formInputTypes = {
                    _SelectBox: function (info) {

                        if (!angular.isDefined(info.config.ui.specifics.searchEnabled)) {
                            if (info.config.choices.length < 10) {
                                info.config.ui.specifics.searchEnabled = false;
                            } else {
                                info.config.ui.specifics.searchEnabled = true;
                            }
                        }

                        if (info.config.choices.length && (info.config.ui.specifics && info.config.ui.specifics.translatedChoices !== false)) {
                            info.config.ui.specifics.translatedChoices = [];
                            angular.forEach(info.config.choices, function (value) {
                                // @todo this might cause problems when config.choices = some other list is applied trough the lifecycle
                                // the choices will not be re-parsed to translatedChoices
                                // this code will only run upon directive initilization
                                var hasit = helpers.getProperty(GLOBAL_CONFIG.fields.translateChoices, [info.config._maker_, info.config.code_name, value]);
                                if (angular.isUndefined(hasit)) {
                                    hasit = value;
                                }
                                info.config.ui.specifics.translatedChoices.push({
                                    key: value,
                                    name: hasit
                                });
                            });
                        }

                        return 'select';
                    },
                    SuperStringProperty: function (info) {
                        var config = info.config;


                        if (config.ui.attrs.type === undefined) {
                            config.ui.attrs.type = 'text';
                        }

                        if (config.choices) {
                            if (config.repeated) {
                                return this._SuperStringRepeated(info);
                            }
                            if (info.config.ui.attrs['repeated-text'] !== undefined) {
                                delete info.config.ui.attrs['repeated-text'];
                            }
                            return this._SelectBox(info);
                        }

                        if (config.repeated) {
                            config.ui.attrs['repeated-text'] = '';
                            return this.SuperTextProperty(info);
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
                            info.config.ui.specifics.type = 'checkbox';
                        }
                        return 'boolean';
                    },
                    SuperVirtualKeyProperty: function (info) {
                        return this.SuperKeyProperty(info);
                    },
                    _SuperStringRepeated: function (info) {
                        var select = {};
                        info.config.ui.specifics.select = select;
                        info.config._groupable = true;
                        return 'select_multiple';
                    },
                    _SuperKeyPropertyRepeated: function (info) {
                        var select = {};
                        info.config.ui.specifics.select = select;
                        return 'select_multiple';
                    },
                    SuperKeyProperty: function (info) {
                        if (info.config.searchable === false) {
                            return this.SuperStringProperty(info);
                        }
                        var config = info.config,
                            template = 'select_async',
                            defaults = {
                                cache: {
                                    query: {
                                        '24': true,
                                        '12': true,
                                        '13': true
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
                                grouping: {
                                    '17': function (items) {
                                        var grouped = [],
                                            current;
                                        angular.forEach(items, function (item) {
                                            if (current && current.label !== item.measurement) {
                                                current = null;
                                            }
                                            if (!current) {
                                                current = {
                                                    label: item.measurement,
                                                    items: []
                                                };
                                                grouped.push(current);
                                            }

                                            current.items.push(item);
                                        });

                                        return grouped;
                                    }
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
                                                    info.config.ui.specifics.initial(); // refresh results
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

                                        if (config.code_name === 'uom') {
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
                            repackMemory = function () {
                                config.ui.specifics._mapEntities = {};
                                angular.forEach(config.ui.specifics.entities, function (val) {
                                    config.ui.specifics._mapEntities[val.key] = 1;
                                });
                            },
                            actionArguments = (config.kind ? modelsMeta.getActionArguments(config.kind, 'search') : {}),
                            response = function (response) {
                                config.ui.specifics.entities = response.data.entities;
                                repackMemory();
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

                        repackMemory();

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
                                                        if (angular.isUndefined(config.ui.specifics._mapEntities[ent.key])) {
                                                            config.ui.specifics._mapEntities[ent.key] = 1;
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
                                                    if (angular.isUndefined(config.ui.specifics._mapEntities[id])) {
                                                        config.ui.specifics._mapEntities[id] = 1;
                                                        config.ui.specifics.entities.unshift(response.data.entities[0]);
                                                    }
                                                } else {
                                                    angular.forEach(fetchedEntities, function (ent) {
                                                        if (angular.isUndefined(config.ui.specifics._mapEntities[ent.key])) {
                                                            config.ui.specifics._mapEntities[ent.key] = 1;
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
                        info.scope.$on('$destroy', function () {
                            config.ui.specifics.entities = [];
                            config.ui.specifics._mapEntities = {};
                        });
                        config.ui.specifics.async = true;
                        if (config.repeated) {
                            template = this._SuperKeyPropertyRepeated(info);
                        }
                        (function () {
                            var select = config.ui.specifics.select || config.ui.specifics.search;
                            if (info.config.kind === '24') {
                                select.init = function (select, scope, element, attrs, ctrls) {
                                    var splitout = function (entities) {
                                        angular.forEach(entities, function (ent) {
                                            ent.leafname = _.last(ent.name.split(' / '));
                                        });
                                    };
                                    select.openTemplate = 'core/select/product_categories.html';
                                    select.windowClass = 'category-modal';
                                    select.product_categories = {
                                        children: [],
                                        mapped: {},
                                        top: [],
                                        resetToTop: function () {
                                            select.product_categories.children = [];
                                            select.product_categories.mapped = {};
                                        },
                                        next: function (item) {
                                            var newFilter = {
                                                search: {
                                                    orders: [{
                                                        operator: 'asc',
                                                        field: 'name'
                                                    }],
                                                    filters: [{
                                                        value: 'indexable',
                                                        operator: '==',
                                                        field: 'state'
                                                    }, {
                                                        value: 'None',
                                                        operator: '==',
                                                        field: 'parent_record'
                                                    }]
                                                }
                                            };
                                            newFilter.search.filters[1].value = item.key;
                                            models['24'].actions.search(newFilter).then(function (response) {
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

                                    models['24'].actions.search({
                                        search: {
                                            orders: [{
                                                operator: 'asc',
                                                field: 'name'
                                            }],
                                            filters: [{
                                                value: 'indexable',
                                                operator: '==',
                                                field: 'state'
                                            }, {
                                                value: 'None',
                                                operator: '==',
                                                field: 'parent_record'
                                            }]
                                        }
                                    }).then(function (response) {
                                        var entities = response.data.entities;
                                        splitout(entities);
                                        select.product_categories.top = entities;
                                    });
                                };
                            }
                        }());
                        return template;
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
                                perLine: 1,
                                clickable: true
                            };
                        config.ui.fieldset = true;

                        if (!config.ui.specifics.toolbar) {
                            config.ui.specifics.toolbar = {};
                        }

                        config.ui.specifics.sortMode = true;
                        defaultFields = defaultFields.sort(helpers.fields.sorter);

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
                            whatSortMeans: function () {
                                modals.alert('howToSort');
                            },
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
                                if (division < (helperWidth / 2)) {
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
                                var dirty;
                                angular.forEach(config.ui.specifics.parentArgs,
                                    function (ent, i) {
                                        if (ent._state === 'deleted' || ent._sequence !== i) {
                                            dirty = true;
                                        }
                                        i = ((config.ui.specifics.parentArgs.length - 1) - i);
                                        ent._sequence = i;
                                        ent.ui.access[ent.ui.access.length - 1] = i;
                                    });
                                if (dirty) {
                                    info.scope.formSetDirty();
                                }
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
                            var fieldIsWritable = $parse(config.ui.writableCompiled + '');
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

                        if (angular.isUndefined(config.ui.specifics.toolbar.titleAdd)) {
                            config.ui.specifics.toolbar.titleAdd = 'add' + helpers.toolbar.makeTitle(config.code_name);
                        }
                        if (angular.isUndefined(config.ui.specifics.toolbar.titleEdit)) {
                            config.ui.specifics.toolbar.titleEdit = 'edit' + helpers.toolbar.makeTitle(config.code_name);
                        }

                        if (config.ui.specifics.remote) {
                            // construct reference to root arguments
                            rootArgs = (config.ui.specifics.getRootArgs ? config.ui.specifics.getRootArgs() : config.ui.specifics.rootScope.args);
                            // assign "load more" logic
                            if (config.repeated && rootArgs.id && info.scope.args.id) {

                                config.ui.specifics.reader = models[rootArgs.action_model].reader({
                                    kind: rootArgs.action_model,
                                    key: rootArgs.key,
                                    args: rootArgs,
                                    access: config.ui.realPath,
                                    complete: function (items) {
                                        config.ui.specifics.parentArgs.extend(items);
                                    }
                                });
                                // apply direct reader settings if any
                                if (angular.isDefined(config.ui.specifics.readerSettings)) {
                                    config.ui.specifics.reader.state(config.ui.specifics.readerSettings);
                                }

                                if ((angular.isUndefined(config.ui.specifics.remoteAutoload) || config.ui.specifics.remoteAutoload)) {
                                    if (angular.isArray(config.ui.specifics.parentArgs)) {
                                        config.ui.specifics.parentArgs.empty();
                                    }
                                    $timeout(function () {
                                        config.ui.specifics.reader.load();
                                    }, 100, false);
                                }

                            }
                        }

                        if (!config.repeated && config.ui.specifics.modal !== true) {

                            config.ui.specifics.SingularCtrl = ng(function ($scope) {
                                $scope.args = config.ui.specifics.parentArgs;
                                info.scope.$watchCollection(config.ui.args, function (neww, old) {
                                    $.extend($scope.args, neww);
                                });
                                config.ui.specifics.getScope = function () {
                                    return $scope;
                                };
                                var getTitle = function () {
                                    return config.ui.specifics.toolbar.titleEdit;
                                };
                                config._title_.push(getTitle);
                                angular.forEach(config.ui.specifics.fields, function (field) {
                                    field._title_ = config._title_.concat();
                                });
                                $scope.$on('$destroy', function () {
                                    config._title_.remove(getTitle);
                                    config.ui.specifics.getScope = undefined;
                                });
                            });

                        } else {

                            config.ui.specifics.remove = function (arg) {
                                arg._state = 'deleted';
                                info.scope.$emit('itemDelete', arg);
                                info.scope.$broadcast('itemDelete', arg);
                                rootFormSetDirty();
                            };

                            // generic manage dialog that handles editing of remote and local structured properties
                            config.ui.specifics.manage = function (arg, defaultArgs, $event) {

                                buildPaths(); // force path rebuild

                                $modal.open({
                                    popFrom: (config.ui.specifics.cards && $event ? helpers.clicks.realEventTarget($event.target) : undefined),
                                    template: underscoreTemplate.get(config.ui.specifics.templateUrl ? config.ui.specifics.templateUrl : 'core/fields/manage_structured.html')({
                                        config: config
                                    }),
                                    controller: ng(function ($scope, modelsUtil) {
                                        var length = (config.ui.specifics.modal ? 0 : config.ui.specifics.parentArgs.length),
                                            formBuilder = {
                                                '0': []
                                            },
                                            groupBysIndx = [],
                                            groupBysMap = {},
                                            getTitle,
                                            getResult = function (response, access) {
                                                var accessPath = [],
                                                    value,
                                                    isNewAndRepeated = ($scope.isNew && config.repeated);
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
                                                    value = _.findWhere(value, {
                                                        _state: 'created'
                                                    });
                                                }

                                                return value;
                                            };

                                        config.ui.specifics.getScope = function () {
                                            return $scope;
                                        };

                                        $scope.isNew = false;

                                        $scope.rootFormSetDirty = rootFormSetDirty;
                                        $scope.formSetDirty = angular.bind($scope, helpers.form.setDirty);
                                        $scope.formSetPristine = angular.bind($scope, helpers.form.setPristine);

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
                                            $scope.isNew = true;
                                        } else if (!config.ui.specifics.modal && arg.ui) {
                                            length = _.last(arg.ui.access);
                                        }


                                        if (angular.isDefined(arg.ui)) {
                                            arg.ui.access = angular.copy(config.ui.realPath);
                                            if (!config.ui.specifics.modal) {
                                                arg.ui.access.push(length);
                                            }
                                        }

                                        $scope.layouts = {
                                            groups: [{
                                                label: false
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
                                        if (config.ui.specifics.remote) {
                                            $scope.close = angular.bind($scope, helpers.form.leave, function () {
                                                $scope.$close();
                                                if (config.ui.specifics.afterClose) {
                                                    config.ui.specifics.afterClose($scope);
                                                }
                                            });

                                        } else {
                                            $.extend(config.ui.specifics.toolbar, {
                                                leftIcon: 'arrow_back',
                                                hideSave: true
                                            });
                                            $scope.close = function () {
                                                var save = $scope.save();
                                                if (save) {
                                                    save.then(function () {
                                                        $scope._close_ = undefined;
                                                        $scope.$close();
                                                    });
                                                } else {
                                                    modals.confirm('discardWithFieldsRequired', $scope.$close);
                                                }
                                            };

                                            $scope._close_ = $scope.close;
                                        }

                                        $scope.validateForm = angular.bind($scope, helpers.form.validate);

                                        $scope.$on('$destroy', function () {
                                            config.ui.specifics.getScope = undefined;
                                        });
                                        angular.forEach(config.ui.specifics.formBuilder, function (field) {
                                            var gr, group, next;
                                            helpers.fields.applyGlobalConfig(field);
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
                                            if (field.ui.groupBy) {
                                                field.ui.hideMessages = true;
                                                if (!groupBysMap[field.ui.groupBy]) {
                                                    gr = {
                                                        ui: {
                                                            group: {
                                                                help: field.ui.groupHelp,
                                                                label: field.ui.groupLabel,
                                                                name: field.ui.groupBy,
                                                                fields: [],
                                                                messages: function () {
                                                                    var messages = {
                                                                        help: true
                                                                    };
                                                                    angular.forEach(gr.ui.group.fields, function (field) {
                                                                        if (field.ui.form.hasErrors() && field.ui.form.field().$dirty) {
                                                                            messages = field.ui.form.messages();
                                                                        }
                                                                    });
                                                                    return messages;
                                                                },
                                                                shouldShowMessages: function () {
                                                                    return true;
                                                                }
                                                            }
                                                        }
                                                    };
                                                    groupBysMap[field.ui.groupBy] = gr;
                                                    groupBysIndx.push(field.ui.groupBy);

                                                    formBuilder['0'].push(groupBysMap[field.ui.groupBy]);
                                                }
                                                groupBysMap[field.ui.groupBy].ui.group.fields.push(field);
                                                return;
                                            }
                                            if (helpers.fields.isFieldset(field) && formInputTypes[field.type]) {
                                                group = {
                                                    label: inflector((field.ui.label || field.code_name), 'humanize')
                                                };
                                                if (_.string.contains(field.type, 'Remote')) {
                                                    group.include = 'core/misc/action.html';
                                                    group.action = function () {
                                                        var test = true;
                                                        if (field.ui.specifics.canOpen) {
                                                            test = field.ui.specifics.canOpen();
                                                        }
                                                        if (test) {
                                                            modals.fields.remote($scope, field);
                                                        }
                                                    };
                                                }
                                                $scope.layouts.groups.push(group);

                                                next = $scope.layouts.groups.length - 1;

                                                if (!angular.isDefined(formBuilder[next])) {
                                                    formBuilder[next] = [];
                                                    formBuilder[next].push(field);
                                                }
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
                                            $scope.save = function (dontShowMessage) {
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
                                                                if (angular.isDefined(readRootArgsAsList)) {
                                                                    readRootArgsAsList.empty();
                                                                    readRootArgsAsList.push(readRootArgs);
                                                                    readRootArgsAsList = undefined;
                                                                }
                                                                if (readRootArgs.key !== null && angular.isDefined(readRootArgs.key)) {
                                                                    if (!angular.isDefined(readArgs.config.keys)) {
                                                                        readArgs.config.keys = [];
                                                                    }
                                                                    readArgs.config.keys.push(readRootArgs.key);

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
                                                    if ($scope.isNew) {
                                                        if (config.repeated) {
                                                            $scope.parentArgs.unshift($scope.args); // preappend arg if they are new
                                                        }
                                                        $scope.isNew = false;
                                                    }
                                                    $.extend(arg, $scope.args); // modify provided args, usually come from the parent's scope
                                                    // re-run prepare to ensure proper paths for complete hook
                                                    prepare();
                                                    if (angular.isDefined(config.ui.specifics.afterSave)) {
                                                        config.ui.specifics.afterSave($scope);
                                                    }
                                                    $scope.formSetPristine();
                                                    if (!dontShowMessage) {
                                                        snackbar.showK('changesSaved');
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
                                                $scope.formSetPristine();

                                                snackbar.showK('changesSaved');
                                            };

                                            $scope.noComplete = function () {
                                                // fired when the scope.complete() does not get fired i.e. when no files were sent for upload
                                                if (angular.isDefined(config.ui.specifics.noComplete)) {
                                                    config.ui.specifics.noComplete($scope);
                                                }
                                                $scope.formSetPristine();
                                            };

                                            $scope.completeError = function (response) {
                                                // fired when it failed to send http-form-data rpc
                                                if (angular.isDefined(config.ui.specifics.afterCompleteError)) {
                                                    config.ui.specifics.afterCompleteError($scope, response);
                                                }
                                                $scope.formSetPristine();
                                            };


                                        } else {


                                            $scope.save = function () {
                                                if (!$scope.validateForm()) { // check if the form is valid
                                                    return false;
                                                }
                                                if ($scope.container.form.$dirty) {
                                                    $scope.rootFormSetDirty();
                                                }
                                                var promise = null,
                                                    saveCompleteDefer = $q.defer(),
                                                    saveCompletePromise = saveCompleteDefer.promise,
                                                    complete = function () {
                                                        var completePromise = null,
                                                            total = 0;

                                                        if (config.repeated) {
                                                            if ($scope.isNew) {
                                                                $scope.parentArgs.unshift($scope.args);
                                                                $scope.isNew = false;
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
                                                                saveCompleteDefer.resolve();
                                                                if (config.closeAfterSave) {
                                                                    $scope.close();
                                                                }
                                                            });
                                                        } else {
                                                            $scope.formSetPristine();
                                                            saveCompleteDefer.resolve();
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
                                                return saveCompletePromise;

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

                                        getTitle = function () {
                                            return config.ui.specifics.toolbar['title' + ($scope.isNew ? 'Add' : 'Edit')];
                                        };

                                        config._title_.push(getTitle);

                                        $scope.$watch('isNew', function () {
                                            config.ui.specifics.toolbar.title = helpers.toolbar.buildTitle(config._title_);
                                        });

                                        angular.forEach(config.ui.specifics.fields, function (field) {
                                            field._title_ = config._title_.concat();
                                        });

                                        $scope.$on('$destroy', function () {
                                            config._title_.remove(getTitle);
                                        });

                                    })
                                });
                            };

                            if (angular.isUndefined(config.ui.specifics.create)) {
                                config.ui.specifics.create = config.ui.specifics.manage;
                            }

                            info.scope.$on('$destroy', function () {
                                config.ui.specifics.create = undefined;
                            });

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
                        if (info.config.ui.specifics.autoGrow === undefined || info.config.ui.specifics.autoGrow) {
                            info.config.ui.attrs['msd-elastic'] = '';
                        }
                        return 'text';
                    },
                    SuperJsonProperty: function (info) {
                        info.config.ui.attrs['json-only'] = '';
                        return this.SuperTextProperty(info);
                    },
                    SuperDateTimeProperty: function (info) {
                        info.config.ui.attrs['time-date-picker-dialog'] = '';
                        info.config.ui.attrs.readonly = 'true';
                        return 'string';
                    }
                };

            return formInputTypes;

        })).constant('msdElasticConfig', {
            append: ''
        }).directive('msdElastic', [
            '$timeout', '$window', 'msdElasticConfig',
            function ($timeout, $window, config) {
                return {
                    require: 'ngModel',
                    restrict: 'A, C',
                    link: function (scope, element, attrs, ngModel) {

                        // cache a reference to the DOM element
                        var ta = element[0],
                            $ta = element;

                        // ensure the element is a textarea, and browser is capable
                        if (ta.nodeName !== 'TEXTAREA' || !$window.getComputedStyle) {
                            return;
                        }

                        // set these properties before measuring dimensions
                        $ta.css({
                            'overflow': 'hidden',
                            'overflow-y': 'hidden',
                            'word-wrap': 'break-word'
                        });

                        // force text reflow
                        var text = ta.value;
                        ta.value = '';
                        ta.value = text;

                        var append = attrs.msdElastic ? attrs.msdElastic.replace(/\\n/g, '\n') : config.append,
                            $win = angular.element($window),
                            mirrorInitStyle = 'position: absolute; top: -999px; right: auto; bottom: auto;' +
                            'left: 0; overflow: hidden; -webkit-box-sizing: content-box;' +
                            '-moz-box-sizing: content-box; box-sizing: content-box;' +
                            'min-height: 0 !important; height: 0 !important; padding: 0;' +
                            'word-wrap: break-word; border: 0;',
                            $mirror = angular.element('<textarea aria-hidden="true" tabindex="-1" ' +
                                'style="' + mirrorInitStyle + '"/>').data('elastic', true),
                            mirror = $mirror[0],
                            taStyle = getComputedStyle(ta),
                            resize = taStyle.getPropertyValue('resize'),
                            borderBox = taStyle.getPropertyValue('box-sizing') === 'border-box' ||
                            taStyle.getPropertyValue('-moz-box-sizing') === 'border-box' ||
                            taStyle.getPropertyValue('-webkit-box-sizing') === 'border-box',
                            boxOuter = !borderBox ? {
                                width: 0,
                                height: 0
                            } : {
                                width: parseInt(taStyle.getPropertyValue('border-right-width'), 10) +
                                    parseInt(taStyle.getPropertyValue('padding-right'), 10) +
                                    parseInt(taStyle.getPropertyValue('padding-left'), 10) +
                                    parseInt(taStyle.getPropertyValue('border-left-width'), 10),
                                height: parseInt(taStyle.getPropertyValue('border-top-width'), 10) +
                                    parseInt(taStyle.getPropertyValue('padding-top'), 10) +
                                    parseInt(taStyle.getPropertyValue('padding-bottom'), 10) +
                                    parseInt(taStyle.getPropertyValue('border-bottom-width'), 10)
                            },
                            minHeightValue = parseInt(taStyle.getPropertyValue('min-height'), 10),
                            heightValue = parseInt(taStyle.getPropertyValue('height'), 10),
                            minHeight = Math.max(minHeightValue, heightValue) - boxOuter.height,
                            maxHeight = parseInt(taStyle.getPropertyValue('max-height'), 10),
                            mirrored,
                            active,
                            copyStyle = ['font-family',
                                'font-size',
                                'font-weight',
                                'font-style',
                                'letter-spacing',
                                'line-height',
                                'text-transform',
                                'word-spacing',
                                'text-indent'
                            ];

                        // exit if elastic already applied (or is the mirror element)
                        if ($ta.data('elastic')) {
                            return;
                        }

                        // Opera returns max-height of -1 if not set
                        maxHeight = maxHeight && maxHeight > 0 ? maxHeight : 9e4;

                        // append mirror to the DOM
                        if (mirror.parentNode !== document.body) {
                            angular.element(document.body).append(mirror);
                        }

                        // set resize and apply elastic
                        $ta.css({
                            'resize': (resize === 'none' || resize === 'vertical') ? 'none' : 'horizontal'
                        }).data('elastic', true);

                        /*
                         * methods
                         */

                        function initMirror() {
                            var mirrorStyle = mirrorInitStyle;

                            mirrored = ta;
                            // copy the essential styles from the textarea to the mirror
                            taStyle = getComputedStyle(ta);
                            angular.forEach(copyStyle, function (val) {
                                mirrorStyle += val + ':' + taStyle.getPropertyValue(val) + ';';
                            });
                            mirror.setAttribute('style', mirrorStyle);
                        }

                        function adjust() {
                            var taHeight,
                                taComputedStyleWidth,
                                mirrorHeight,
                                width,
                                overflow;

                            if (mirrored !== ta) {
                                initMirror();
                            }

                            // active flag prevents actions in function from calling adjust again
                            if (!active) {
                                active = true;

                                mirror.value = ta.value + append; // optional whitespace to improve animation
                                mirror.style.overflowY = ta.style.overflowY;

                                taHeight = ta.style.height === '' ? 'auto' : parseInt(ta.style.height, 10);

                                taComputedStyleWidth = getComputedStyle(ta).getPropertyValue('width');

                                // ensure getComputedStyle has returned a readable 'used value' pixel width
                                if (taComputedStyleWidth.substr(taComputedStyleWidth.length - 2, 2) === 'px') {
                                    // update mirror width in case the textarea width has changed
                                    width = parseInt(taComputedStyleWidth, 10) - boxOuter.width;
                                    mirror.style.width = width + 'px';
                                }

                                mirrorHeight = mirror.scrollHeight;

                                if (mirrorHeight > maxHeight) {
                                    mirrorHeight = maxHeight;
                                    overflow = 'scroll';
                                } else if (mirrorHeight < minHeight) {
                                    mirrorHeight = minHeight;
                                }
                                mirrorHeight += boxOuter.height;
                                ta.style.overflowY = overflow || 'hidden';

                                if (taHeight !== mirrorHeight) {
                                    ta.style.height = mirrorHeight + 'px';
                                    scope.$emit('elastic:resize', $ta);
                                }

                                // small delay to prevent an infinite loop
                                $timeout(function () {
                                    active = false;
                                }, 1, false);

                            }
                        }

                        function forceAdjust() {
                            active = false;
                            adjust();
                        }

                        /*
                         * initialise
                         */

                        // listen
                        if ('onpropertychange' in ta && 'oninput' in ta) {
                            // IE9
                            ta['oninput'] = ta.onkeyup = adjust;
                        } else {
                            ta['oninput'] = adjust;
                        }

                        $win.bind('resize', forceAdjust);

                        scope.$watch(function () {
                            return ngModel.$modelValue;
                        }, function (newValue) {
                            forceAdjust();
                        });

                        scope.$on('elastic:adjust', function () {
                            initMirror();
                            forceAdjust();
                        });

                        $timeout(adjust);

                        /*
                         * destroy
                         */

                        scope.$on('$destroy', function () {
                            $mirror.remove();
                            $win.unbind('resize', forceAdjust);
                        });
                    }
                };
            }
        ]).directive('fastNgChange', ng(function ($parse, $mdUtil) {
            return {
                priority: 1,
                link: function (scope, element, attrs) {
                    var fn = $parse(attrs.fastNgChange),
                        prev = element.val(),
                        change = $mdUtil.debounce(function (ev) {
                            var cval = element.val();
                            if (prev !== cval) {
                                prev = cval;
                                fn(scope, {
                                    $event: ev
                                });
                            }
                        }, 100, scope, true);
                    element.on('change keydown', change);
                    scope.$on('$destroy', function () {
                        element.off('change keydown', change);
                    });
                }
            };
        })).directive('fastNgModel', ng(function ($parse, $mdUtil) {
            return {
                priority: -1,
                link: function (scope, element, attrs) {
                    var model = $parse(attrs.fastNgModel),
                        change = $mdUtil.debounce(function (ev) {
                            model.assign(scope, element.val());
                        }, 100, scope, true);
                    element.on('keyup', change);
                    scope.$on('$destroy', function () {
                        element.off('keyup', change);
                    });
                }
            };
        }));
}());
