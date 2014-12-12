(function () {
    'use strict';
    angular.module('app').config(function (datepickerConfig) { datepickerConfig.showWeeks = false; })
        .directive('mainMenuToggler', function ($rootScope) {
            return {
                link: function (scope, element) {
                    var activeClass = 'menu-active',
                        click = function (e, cmd) {
                            var mm = $('#main-menu'),
                                visible = mm.is(':visible');

                            if ((visible || cmd === 1) && cmd !== 2) {
                                mm.stop().animate({
                                    height: 0
                                }, 100, function () {
                                    $(this).hide();
                                    $('body').removeClass(activeClass);
                                });
                            } else if (!visible || cmd === 2) {
                                mm.height(0).show();
                                mm.stop().animate({
                                    height: ($(window).height() - $('#top-bar').height())
                                }, 100, function () {
                                    $('body').addClass(activeClass);
                                });
                            }
                        },
                        resize = function () {
                            var mm = $('#main-menu'),
                                visible = mm.is(':visible');

                            if (visible) {
                                mm.stop().animate({
                                    height: ($(window).height() - $('#top-bar').height())
                                }, 100);

                            }

                        };

                    element.on('click', click);
                    $(window).on('resize', resize);

                    scope.$on('$destroy', function () {
                        element.off('click', click);
                        $(window).off('resize', resize);
                    });

                    $rootScope.$on('hide_menu', function () {
                        click(null, 1);
                    });

                    $rootScope.$on('show_menu', function () {
                        click(null, 2);
                    });

                }
            };
        }).directive('toggle', function () {
            return {
                scope: {
                    ngModel: '='
                },
                link: function (scope, element, attrs) {

                    var toggle = attrs.toggle,
                        splits,
                        init,
                        handler;
                    if (!toggle) {
                        toggle = 'Yes/No';
                    }
                    splits = toggle.split('/');
                    init = function () {
                        if (scope.ngModel) {
                            element.text(splits[0]);
                        } else {
                            element.text(splits[1]);
                        }
                    };

                    init();

                    handler = function () {
                        scope.$apply(function () {
                            scope.ngModel = !scope.ngModel;
                            init();
                        });
                    };

                    element.bind('click', handler);

                    scope.$on('$destroy', function () {
                        element.off('click', handler);
                    });
                }
            };
        }).directive('jsonOnly', function () {
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
                templateUrl: 'form/builder.html',
                controller: function ($scope, $element, $attrs) {
                    $scope.configurations = $scope.$eval($attrs.formBuilder);
                }
            };
        })
        .directive('formElementWrapper', function () {
            return {
                restrict: 'EA',
                transclude: true,
                scope: true,
                templateUrl: 'misc/form_wrapper.html',
                link: function (scope, element, attrs) {
                    scope.label = attrs.label;
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

                        attrs['ng-required'] = 'config.required';
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
                            name = supplied_config.code_name,
                            label = null,
                            config,
                            tpl,
                            template;

                        // use backend defined label if was provided, otherwise the label will be humanized
                        if (supplied_config.verbose_name !== null && supplied_config.verbose_name !== undefined) {
                            label = supplied_config.verbose_name;
                        } else {
                            label = name;
                        }

                        if (!name) {
                            console.error('Your field config', supplied_config, 'has no name defined defined.');
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
                                name: name,
                                formName: name,
                                writable: [name],
                                path: undefined,
                                realPath: undefined,
                                attrs: {},
                                preRender: [] // holds list of callbacks to execute prior to rendering of the directive
                            }
                        };

                        helpers.mergeDeep(supplied_config, config);
                        config = supplied_config;

                        if (!angular.isDefined(config.ui.path)) {
                            config.ui.path = [name];
                        }

                        if (angular.isDefined(config.ui.writableName)) {
                            config.ui.writable = [config.ui.writableName];
                        } else {
                            if (angular.isArray(config.ui.writable)) {
                                config.ui.writable = angular.copy(config.ui.path);
                            }
                        }

                        if (!angular.isDefined(config.ui.realPath)) {
                            config.ui.realPath = [name];
                        }

                        if (types[config.type] !== undefined) {
                            // reference main locals to type builder
                            tpl = types[config.type]({
                                config: config,
                                element: element,
                                scope: scope,
                                attrs: attrs
                            });

                            // compiled variables for the template
                            config.ui.compiled = {
                                attrs: utils.attrs(config),
                                label: utils.label(config)
                            };

                            angular.forEach(config.ui.preRender, function (callback) {
                                callback.call(config);
                            });

                            if (config.ui.render === false) {
                                return;
                            }

                            template = underscoreTemplate.get(angular.isDefined(config.ui.template) ? config.ui.template : 'underscore/form/' + tpl + '.html')({
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
                                stringified = modelsUtil.toJson(newval);
                            element.val(stringified);
                        };
                    scope.$watch(attrs.compatibilityMaker, fn);
                    scope.$on('ngUploadSubmit', fn);

                }
            };
        })
        .directive('fitInDialog', function () {
            return {
                link: function (scope, element, attrs) {
                    var fn = function () {

                        return;

                        var modal_dialog = $(element).parents('.modal-dialog:first'),
                            height = $(window).height(),
                            modal_footer = modal_dialog.find('.modal-footer');

                        height -= parseInt(modal_dialog.css('margin-top'), 10) + parseInt(modal_dialog.css('margin-bottom'), 10);

                        if (modal_footer.length) {
                            height -= modal_footer.outerHeight();
                        }

                        modal_dialog.find('.modal-body.scrollable, .modal-body.unscrollable').css('min-height', height);

                    };

                    $(window).bind('resize modal.open', fn);
                    scope.$on('$destroy', function () {
                        $(window).unbind('resize modal.open', fn);
                    });
                }
            };
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
        }).directive('conditionalOutput', function (helpers, $compile) {
            return {
                scope: {
                    conditionalOutput: '=conditionalOutput',
                    conditionalOutputValue: '=conditionalOutputValue'
                },
                link: function (scope, element) {
                    var template = scope.conditionalOutput(scope.conditionalOutputValue);
                    element.html(template);
                    $compile(element.contents())(scope);
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
                        e.preventDefault();
                        return false;
                    }, disabledInitially = angular.isDefined(attrs.loading) ? $parse(attrs.loading) : function () {
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
        }).directive('submitIfFiles', function ($parse) {
            return {
                require: '^form',
                link: function (scope, element, attrs, ctrl) {
                    var form = element.parents('form:first'),
                        files,
                        submit = $parse(attrs.submitIfFiles),
                        complete = $parse(attrs.submitIfFilesNoComplete),
                        execute,
                        click = function () {
                            var promise = submit(scope);
                            if (promise) {
                                promise.then(function () {
                                    files = form.find('input[type="file"]');
                                    if (files.length) {
                                        execute = false;
                                        files.each(function () {
                                            if ($(this).val()) {
                                                execute = true;
                                                return false;
                                            }
                                        });

                                        if (execute) {
                                            form.trigger('submit');
                                            return false;
                                        }
                                    }

                                    complete(scope);

                                });
                            }
                        };

                    element.on('click', click);
                    scope.$on('$destroy', function () {
                        element.off('click', click);
                    });

                }
            };
        }).directive('accordionOnOpen', function ($timeout, helpers) {
            return {

                link: function (scope, element, attrs) {

                    var accordions = scope.$eval(attrs.accordionOnOpen);

                    if (accordions) {

                        angular.forEach(accordions.groups, function (accordion, i) {
                            scope.$watch(attrs.accordionOnOpen + '.groups.' + i + '.open', function (neww, old) {
                                if (neww) {
                                    scope.$broadcast('accordionStateChanged', accordions.groups[i], i);
                                }
                            });

                        });

                    }

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
        }).directive('fancyGridGenerator', function (helpers, $timeout) {

            return {
                link: function (scope, element, attrs) {
                    var resize = function () {
                        var canvas = element.outerWidth(true),
                            images = [],
                            margin = 1;
                        if (!canvas) {
                            return; // do not measure if canvas is falsy
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

                    $(window).on('resize', resize);
                    scope.$on('itemOrderChanged', resize);
                    scope.$on('ngRepeatEnd', resize);
                    scope.$on('accordionStateChanged', resize);
                    scope.$on('itemDelete', function () {
                        $timeout(resize);
                    });
                    scope.$on('$destroy', function () {
                        $(window).off('resize', resize);
                    });

                }
            };
        }).directive('gridGenerator', function (GLOBAL_CONFIG, helpers, $timeout) {
            return {
                link: function (scope, element, attrs) {

                    var config = scope.$eval(attrs.gridGenerator) || {},
                        margin = config.margin || 0,
                        maxWidth = config.maxWidth || GLOBAL_CONFIG.gridMaxWidth,
                        minWidth = config.minWidth || GLOBAL_CONFIG.gridMinWidth,
                        square = (angular.isDefined(config.square) ? config.square : true),
                        resize = function () {

                            element = $(element);
                            if (!element.length) {
                                return;
                            }
                            var wrapper = element.parents('.grid-wrapper:first'),
                                canvasWidth = wrapper.outerWidth(true),
                                values,
                                img,
                                image;
                            if (canvasWidth) {
                                values = helpers.calculateGrid(canvasWidth,
                                    maxWidth, minWidth, margin);
                                wrapper.css({
                                    paddingRight: values[2],
                                    paddingLeft: values[2]
                                });

                                element.each(function () {
                                    var box = $(this).width(values[0]);
                                    if (square) {
                                        box.height(values[0]);
                                        img = box.find('img');
                                        image = scope.$eval(attrs.gridGenerator);
                                        if (image) {
                                            img.removeClass('horizontal vertical');
                                            if (image.proportion > 1) {
                                                img.addClass('horizontal');
                                            } else {
                                                img.addClass('vertical');
                                            }
                                        }

                                    }

                                });


                            }
                        };

                    $(window).bind('resize', resize);

                    resize();

                    scope.$on('ngRepeatEnd', resize);
                    scope.$on('$destroy', function () {
                        $(window).off('resize', resize);
                    });

                }
            };
        }).directive('defaultFieldDisplay', function ($compile) {
            return {
                scope: {
                    val: '=defaultFieldDisplay',
                    field: '=defaultFieldDisplayField'
                },
                templateUrl: 'buyer/directive/buyer_address_display.html',
                controller: function ($scope) {
                    $scope.notEmpty = function (val) {
                        return angular.isString(val) || angular.isNumber(val);
                    };

                }
            };
        }).directive('standardClick', function ($parse) {
            return {
                restrict: 'A',
                link: function (scope, element, attrs) {
                    var callback = $parse(attrs.standardClick);
                    element.on('click', function (event) {
                        if (element.hasClass('dragged')) {
                            element.removeClass('dragged');
                            return;
                        }
                        scope.$apply(function () {
                            callback(scope, {event: event});
                        });
                    });
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
                                        formElement.$dirty = true;
                                        formElement.$pristine = false;
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