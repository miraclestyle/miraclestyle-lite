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
                    return (field.is_structured || ((_.string.contains(field.type, 'KeyProperty')) && field.repeated) || field.ui.fieldset);
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
        }))
        .directive('formBuilder', ng(function ($compile, underscoreTemplate, modelsMeta) {
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
        })).factory('formInputTypes', ng(function () {

            var formInputTypes = {};

            return formInputTypes;

        })).directive('fastNgChange', ng(function ($parse, $mdUtil) {
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
