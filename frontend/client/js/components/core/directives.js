(function () {
    'use strict';
    angular.module('app')
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
                templateUrl: 'core/form/builder.html',
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
                            config.ui.init = {callbacks: [], add: function (name, callback) {
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
                            }};
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

                            template = underscoreTemplate.get(angular.isDefined(config.ui.template) ? config.ui.template : 'core/underscore/form/' + tpl + '.html')({
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
        })
        .directive('fitInModal', function () {
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
                        check = $parse(attrs.submitIf),
                        execute,
                        click = function () {
                            if (check && !check(scope)) {
                                return false;
                            }
                            var promise = submit(scope);
                            if (promise && angular.isObject(promise) && promise.then) {
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
                        var originalCanvas = 0,
                            run = function (check) {
                                var canvas = element.outerWidth(true),
                                    images = [],
                                    margin = 1;
                                if (!canvas || (check && originalCanvas === canvas)) {
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
                        run();
                        setTimeout(function () {
                            run(true);
                        }, 50);
                    };

                    scope.$on('modalResize', resize);
                    scope.$on('itemOrderChanged', resize);
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
        }).directive('tapOrClick', function ($parse, helpers) {
            return {
                restrict: 'A',
                link: function (scope, element, attrs) {
                    var callback = $parse(attrs.tapOrClick),
                        click = function (event, tap) {
                            if (element.hasClass('dragged') && !tap) {
                                element.removeClass('dragged');
                                return;
                            }
                            scope.$apply(function () {
                                callback(scope, {$event: event});
                            });
                        },
                        tap = function (e) {
                            click.call(this, e, 1);
                            return e.preventDefault();
                        },
                        touch = helpers.responsive.isTouch();
                    if (touch) {
                        $(element).hammer().bind('tap', tap);
                    } else {
                        element.on('click', click);
                    }

                    scope.$on('$destroy', function () {
                        if (touch) {
                            $(element).hammer().off('tap', tap);
                        } else {
                            element.off('click', click);
                        }
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
        }).directive('imageSlider', function ($timeout, $parse) {
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
                            callback(scope, {callback: function (response, state) {
                                done();
                                anyMore = state;
                            }});
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
                            var height = parent.parents('.fixed-height').height();
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
                            var newHeight = element.parents('.fixed-height:first').innerHeight() - window.SCROLLBAR_WIDTH,
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
                                    target.show();
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
                    }, required = element.attr('required') === 'required';
                    ctrls[0].$parsers.unshift(function (value) {
                        var valid = checkNumeric(value), out;
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
        }).directive('actionDropdownList', function () {
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
                                            targetNode = target.get(0),
                                            targetRect = targetNode.getBoundingClientRect(),
                                            parent = options.parent,
                                            parentNode = parent.get(0),
                                            parentRect = parentNode.getBoundingClientRect(),
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
        })
        .directive('selectInput', function ($simpleDialog, $mdTheming,
            $mdInkRipple, $$rAF, $mdConstant, underscoreTemplate, $timeout, $parse, helpers) {
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
                            template: underscoreTemplate.get('core/select/underscore/choices.html')({select: select}),
                            targetEvent: $event,
                            parent: attachTo,
                            onBeforeHide: function (dialogEl, options) {
                                $(window).off('resize', options.resize);
                            },
                            onBeforeShow: function (dialogEl, options) {
                                options.parent.css('overflow-wrap', options.parent.css('overflow-wrap') === 'normal' ? 'break-word' : 'normal');
                                var animateSelect = function () {
                                    var target = element.parents('md-input-container:first');
                                    options.resize = function () {
                                        var targetOffset = target.offset(),
                                            targetNode = target.get(0),
                                            targetRect = targetNode.getBoundingClientRect(),
                                            elementNode = element.get(0),
                                            elementRect = elementNode.getBoundingClientRect(),
                                            elementOffset = element.offset(),
                                            parent = options.parent,
                                            parentNode = parent.get(0),
                                            parentRect = parentNode.getBoundingClientRect(),
                                            paddingTop = parseInt(parent.css('padding-top'), 10) || 16,
                                            paddingBottom = parseInt(parent.css('padding-bottom'), 10) || 16,
                                            parentHeight = options.parent.height(),
                                            scrollElement = dialogEl.find('md-content'),
                                            scrollElementNode = scrollElement.get(0),
                                            top = parentRect.top + paddingTop,
                                            activeOffset,
                                            active = dialogEl.find('.list-row--is-active'),
                                            activeNode = active.get(0),
                                            activeRect,
                                            buffer,
                                            spaceAvailable,
                                            scrollElementTopMargin = parseInt(scrollElement.css('margin-top'), 10),
                                            newTop,
                                            totalHeight,
                                            newScrollTop;
                                        if (active.length) {
                                            activeOffset = active.offset();
                                            activeRect = activeNode.getBoundingClientRect();
                                        }
                                        dialogEl.width(target.width());
                                        if ((dialogEl.height() > parentHeight)
                                                || (scrollElement.prop('scrollHeight') > parentHeight)) {
                                            dialogEl.css({
                                                top: top,
                                                left: targetOffset.left
                                            }).height(options.parent.height() - (paddingBottom + paddingTop));
                                        } else {
                                            dialogEl.css(targetOffset);
                                            activeOffset = active.offset();
                                            if (active.length) {
                                                // position the selection at center of active item
                                                newTop = (targetOffset.top - (activeOffset.top - elementOffset.top)) - ((active.height() - element.height()) / 2);
                                            } else {
                                                // position the div at the center if no item is selected
                                                newTop = (elementOffset.top + element.height()) - (dialogEl.height() / 2) - parseInt(scrollElement.css('paddingTop'), 10) - 3;
                                            }
                                            if (newTop > top) {
                                                totalHeight = newTop + dialogEl.height();
                                                if (totalHeight > parentHeight) {
                                                    newTop = newTop - (totalHeight - parentHeight);
                                                    if (newTop < top) {
                                                        newTop = top;
                                                    }
                                                }
                                                dialogEl.css('top', newTop);
                                            } else {
                                                dialogEl.css('top', top);
                                            }
                                        }
                                        if (active.length && !select.multiple) {
                                            scrollElement.scrollTop(scrollElement.scrollTop() - scrollElement.offset().top + active.offset().top);
                                        }
                                    };
                                    options.resize();
                                    $(window).on('resize', options.resize);

                                    dialogEl.css($mdConstant.CSS.TRANSFORM, 'scale(' +
                                        Math.min(target.width() / dialogEl.width(), 1.0) + ',' +
                                        Math.min(target.height() / dialogEl.height(), 1.0) + ')')
                                        .on($mdConstant.CSS.TRANSITIONEND, function (ev) {
                                            if (ev.target === dialogEl[0]) {
                                                select.opened = true;
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
        }).directive('mainMenuItem', function () {
            return {
                templateUrl: 'home/main_menu_item.html',
                transclude: true,
                replace: true
            };
        }).directive('listButton', function () {
            return {
                templateUrl: 'core/list/button.html',
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
        }).directive('mdInkRippleAction', function ($mdInkRipple) {
            return {
                link: function (scope, element, attrs) {
                    $mdInkRipple.attachButtonBehavior(scope, element, {
                        dimBackground: false
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
        });


}());