(function () {
    'use strict';
    angular.module('app')
        .run(ng(function (helpers, $mdConstant, GLOBAL_CONFIG) {
            $.extend(helpers, {
                clicks: {
                    realEventTarget: function (target) {
                        var theTarget = $(target),
                            parentTarget = theTarget.parents('.grid-item:first'),
                            cardParent = theTarget.parents('.card:first');
                        if (!theTarget.hasClass('grid-item') && parentTarget.length) {
                            target = parentTarget.get(0);
                        }

                        if (cardParent.length) {
                            target = cardParent.get(0);
                        }

                        return target;
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
                newHeightByWidth: function (original_width, original_height, new_width) {
                    var ratio;
                    original_width = parseInt(original_width, 10);
                    original_height = parseInt(original_height, 10);
                    new_width = parseInt(new_width, 10);
                    ratio = new_width / original_width; // get ratio for scaling image
                    return (original_height * ratio);
                },
                popup: {
                    openCentered: function (url, title) {
                        var w = $(window).width() / 1.3,
                            h = $(window).height() / 1.3,
                            left = (screen.width / 2) - (w / 2),
                            top = (screen.height / 2) - (h / 2),
                            popup;
                        // toolbar=no, location=no, directories=no, status=no, menubar=no, scrollbars=1, resizable=no, copyhistory=no, 
                        popup = window.open(url, title, 'width=' + w + ', height=' + h + ', top=' + top + ', left=' + left);
                        popup.focus();
                        return popup;
                    }
                },
                url: {
                    abs: function (part) {
                        return GLOBAL_CONFIG.host + '/' + part;
                    },
                    handleProtocol: function (url) {
                        return ((document.location.protocol === 'https:' || document.location.protocol === 'chrome-extension:') ? url.replace('http://', 'https://') : url);
                    },
                    urlsafe: function (str) {
                        return window.btoa(str).replace(new RegExp('=', 'g'), '-');
                    },
                    urlunsafe: function (str) {
                        return window.atob(str.replace(new RegExp('-', 'g'), '='));
                    },
                    jsonFromUrlsafe: function (str) {
                        return angular.fromJson(helpers.url.urlunsafe(str));
                    },
                    jsonToUrlsafe: function (str) {
                        return helpers.url.urlsafe(angular.toJson(str));
                    }
                }
            });

            var animationEnd = function (which, cb) {
                return $(this).on($mdConstant.CSS.ANIMATIONEND, function kill(e) {
                    if (e.target === this) {
                        cb.call(this, e);
                        if (which === 'one') {
                            $(this).off($mdConstant.CSS.ANIMATIONEND, kill);
                        }
                    }
                });
            };

            $.fn.oneAnimationEnd = function (cb) {
                return animationEnd.call(this, 'one', cb);
            };

            $.fn.onAnimationEnd = function (cb) {
                return animationEnd.call(this, 'on', cb);
            };

        }))
        .directive('fillEmptySpace', function () {
            return {
                link: function (scope, element, attrs) {
                    var resize = function () {
                        var margintop = parseInt(element.css('marginTop'), 10);
                        element.css('min-height', $(window).height() - margintop);
                    };
                    resize();
                    $(window).resize(resize);
                    scope.$on('$destroy', function () {
                        $(window).unbind('resize', resize);
                    });
                }
            };
        })
        .directive('onEnter', ng(function ($parse, helpers, $mdConstant) {
            return {
                link: function (scope, element, attrs) {
                    var callback = $parse(attrs.onEnter);
                    element.on('keydown', function (e) {
                        if (helpers.responsive.isMobile() || helpers.responsive.isTablet()) {
                            return;
                        }
                        if (e.keyCode === $mdConstant.KEY_CODE.ENTER && !e.shiftKey) {
                            e.preventDefault();
                            callback(scope, {
                                $event: e
                            });
                            $(this).val('');
                        }
                    });
                }
            };
        }))
        .directive('helpRender', function () {
            return {
                scope: {
                    help: '=helpRender'
                },
                templateUrl: 'core/misc/help_render.html',
                link: function (scope, element, attrs) {
                    scope.isTemplate = function () {
                        return !angular.isArray(scope.help);
                    };
                }
            };
        })
        .directive('displayImage', ng(function (GLOBAL_CONFIG, helpers, $http) {
            return {
                scope: {
                    image: '=displayImage',
                    config: '=displayImageConfig'
                },
                link: function (scope, element, attrs) {

                    var path, fn;

                    if (!scope.config) {
                        scope.config = {};
                    }

                    if (!angular.isDefined(scope.config.size)) {
                        scope.config.size = 240;
                    }

                    fn = function watchServingUrl(nv, ov) {
                        if (nv !== ov) {
                            if (window.isChromeApp && path) {
                                URL.revokeObjectURL(path);
                            }
                            var img = element,
                                done = function () {
                                    img.css('visibility', 'inherit');
                                    scope.$emit('displayImageLoaded', img);
                                },
                                error = function () {
                                    var defaultImage = scope.config.defaultImage;
                                    if (!defaultImage) {
                                        defaultImage = 'defaultImage';
                                    }
                                    img.attr('src', GLOBAL_CONFIG[defaultImage]);
                                    done();
                                };

                            if (scope.image && scope.image.serving_url) {
                                path = helpers.url.handleProtocol(scope.image.serving_url) + (scope.config.size === true ? '' : '=s' + scope.config.size);
                                img.on('load', done)
                                    .on('error', error);
                                if (!window.isChromeApp) {
                                    img.attr('src', path);
                                } else {
                                    $http.get(path, {
                                        responseType: 'blob'
                                    }).success(function (response) {
                                        path = URL.createObjectURL(response.data);
                                        img.attr('src', path);
                                    }).error(error);
                                }
                            } else {
                                setTimeout(function () {
                                    error();
                                    done();
                                }, 50);
                            }
                        }
                    };

                    scope.$watch('image.serving_url', fn);

                    fn(true, false);

                }
            };
        })).directive('loading', ng(function ($parse) {
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
        })).directive('onNgRepeatEnd', ng(function ($timeout) {
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
        })).directive('defaultFieldDisplay', ng(function ($compile) {
            return {
                scope: {
                    val: '=defaultFieldDisplay'
                },
                templateUrl: 'buyer/address_display.html',
                controller: ng(function ($scope) {
                    $scope.notEmpty = function (val) {
                        return angular.isString(val) || angular.isNumber(val);
                    };

                })
            };
        })).directive('draggableClick', ng(function ($parse, helpers) {
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
        })).directive('loadMoreButton', ng(function () {
            return {
                restrict: 'A',
                templateUrl: 'core/misc/load_more_button.html',
                scope: {
                    config: '=loadMoreButton'
                },
                link: function (scope, element) {
                    scope.$watch('config.firstLoad', function (neww, old) {
                        if (neww === false || neww === true) {
                            var modal = element.parents('.modal:first'),
                                spinner = modal.find('content-spinner').find(':first');
                            if (!spinner.length) {
                                if (modal.length) {
                                    return;
                                }
                                spinner = $('body content-spinner:first').find(':first');
                            }
                            if (neww === true) {
                                spinner.removeClass('ng-hide');
                            } else if (neww === false) {
                                spinner.addClass('ng-hide');
                            }
                        }
                    });
                }
            };
        })).directive('autoloadOnVerticalScrollEnd', ng(function ($timeout) {
            return {
                restrict: 'A',
                link: function (scope, element, attrs) {
                    var config,
                        listen,
                        loadMore,
                        steady,
                        intervalid,
                        waitinterval = false,
                        loaded = false,
                        steadyOpts,
                        maybeMore,
                        startInterval,
                        timeoutid,
                        run;
                    config = scope.$eval(attrs.autoloadOnVerticalScrollEnd);

                    run = function () {
                        listen = (function () {
                            var listener = config.listen;
                            if (!listener) {
                                listener = element.parents('.ui-view-wrapper:first');
                                if (listener.length) {
                                    return listener;
                                }
                                listener = element.parents('md-content[md-scroll-y]:first');
                                if (element.hasClass('overflow-y') || element.hasClass('overflow-auto-y')) {
                                    listener = element;
                                } else {
                                    if (!listener.length) {
                                        listener = element.parents('.overflow-y:first');
                                    }
                                    if (!listener.length) {
                                        listener = element.parents('.overflow-auto-y:first');
                                    }
                                }
                            } else {
                                listener = $(config.listen || window);
                            }
                            return listener;
                        }());


                        maybeMore = function () {
                            $timeout.cancel(timeoutid);
                            timeoutid = $timeout(function () {
                                var listenNode = listen.get(0),
                                    listenScrollHeight = listenNode.scrollHeight,
                                    viewport = $(window).height() - 56,
                                    maybe,
                                    promise;
                                if (config.reverse) {
                                    maybe = (listenNode ? (listen.scrollTop() < (config.top || 40)) : false);
                                } else {
                                    console.log(viewport, viewport - listenScrollHeight);
                                    maybe = (listenNode ? ((viewport >= listenScrollHeight) || ((viewport - listenScrollHeight) > -10)) : false);
                                }
                                if (!listen.length || !listenNode) {
                                    return;
                                }
                                if (maybe) {
                                    promise = loadMore({}, angular.noop);
                                    if (promise) {
                                        promise.then(function () {
                                            if (!config.reverse) {
                                                maybeMore();
                                            }
                                        })['finally'](function () {
                                            waitinterval = false;
                                        });
                                    }
                                } else {
                                    waitinterval = false;
                                }

                            }, 1000, false);

                        };

                        startInterval = function () {
                            clearInterval(intervalid);
                            intervalid = setInterval(function () {
                                if (waitinterval) {
                                    return true;
                                }
                                waitinterval = true;
                                maybeMore();
                            }, 2000);
                        };

                        loadMore = function (values, done) {
                            if (!config.loader || !angular.isFunction(config.loader.load)) {
                                return;
                            }
                            var promise = config.loader.load();
                            if (!promise) {
                                done();
                                return false;
                            }
                            promise.then(function () {
                                done();
                            });

                            return promise;
                        };
                        steadyOpts = {
                            conditions: {
                                'max-bottom': config.bottom || 40
                            },
                            scrollElement: listen.get(0),
                            throttle: 100,
                            handler: loadMore
                        };
                        if (config.reverse) {
                            delete steadyOpts.conditions;
                        }
                        steady = new Steady(steadyOpts);
                        if (config.reverse) {
                            steady.addTracker('checkTop', function () {
                                return listen.scrollTop() < (config.top || 40);
                            });
                            steady.addCondition('checkTop', true);
                        }
                        scope.$on('$destroy', function () {
                            steady.stop();
                            steady = undefined;
                            clearInterval(intervalid);
                            $timeout.cancel(timeoutid);
                        });

                        if (config.watch) {
                            scope.$watchGroup(angular.isArray(config.watch) ? config.watch : [config.watch], function (neww, old) {
                                if (JSON.stringify(neww) !== JSON.stringify(old)) {
                                    maybeMore();
                                    startInterval();
                                }
                            });
                        } else {
                            maybeMore();
                            startInterval();
                        }
                    };

                    scope.$watch(function () {
                        return attrs.autoloadOnVerticalScrollEnd && config && config.loader;
                    }, function (neww, old) {
                        if (!neww || loaded) {
                            return;
                        }
                        $timeout(function () {
                            loaded = true;
                            run();
                        });
                    });

                }
            };
        })).directive('resizeChart', ng(function (helpers) {
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
        })).directive('listButton', function () {
            return {
                templateUrl: 'core/misc/list_button.html',
                transclude: true,
                replace: true
            };
        }).directive('mdInkRippleList', ng(function ($mdInkRipple) {
            return {
                link: function (scope, element, attrs) {
                    $mdInkRipple.attach(scope, element, {
                        dimBackground: true,
                        multiplier: 0.1,
                        moveToCenter: false
                    });
                }
            };
        })).directive('mdInkRippleAction', ng(function ($mdInkRipple) {
            return {
                link: function (scope, element, attrs) {
                    $mdInkRipple.attachButtonBehavior(scope, element, {
                        dimBackground: false
                    });
                }
            };
        })).directive('mdInkRippleFit', ng(function ($mdInkRipple) {
            return {
                link: function (scope, element, attrs) {
                    $mdInkRipple.attachButtonBehavior(scope, element, {
                        dimBackground: false,
                        fitRipple: true,
                        moveToCenter: false
                    });
                }
            };
        })).directive('icon', ng(function ($mdInkRipple) {
            return {
                templateUrl: 'core/misc/icon.html',
                replace: true,
                transclude: true,
                scope: true,
                link: function (scope, element, attrs) {
                    scope.icon = attrs.type;
                    scope.color = attrs.color || 'normal';
                }
            };
        })).directive('contentListView', function () {
            return {
                scope: {
                    val: '=contentListView'
                },
                templateUrl: 'core/misc/content_list_view.html'
            };
        }).directive('sidenavItem', ng(function ($timeout, $mdSidenav) {
            return {
                templateUrl: 'core/misc/sidenav_item.html',
                transclude: true,
                replace: true
            };
        })).filter('labelize', ng(function (GLOBAL_CONFIG, $log) {
            return function (key, group) {
                if (key === undefined || key === null) {
                    return key;
                }
                if (angular.isUndefined(group)) {
                    group = 'default';
                }
                var getGroup = GLOBAL_CONFIG.labels[group],
                    get;
                if (angular.isUndefined(getGroup)) {
                    $log.warn('Group is not defined: ' + group);
                    return key;
                }
                get = getGroup[key];
                if (angular.isDefined(get)) {
                    return get;
                }
                $log.warn('Path for label not found: ' + group + '.' + key);
                return key;
            };
        })).filter('propsFilter', function () {
            return function (items, props) {
                var out = [];

                if (angular.isArray(items)) {
                    items.forEach(function (item) {
                        var itemMatches = false,
                            keys = Object.keys(props),
                            i,
                            prop,
                            text;
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
        }).filter('capitalize', function () {
            return function (obj) {
                return _.str.capitalize(obj);
            };
        }).filter('output', ng(function (modelsMeta, outputTypes, $cacheFactory) {

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
                    fields,
                    field,
                    format;

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

        })).filter('escape', function () {
            return function (val) {
                if (!val) {
                    return val;
                }
                return _.escape(val);
            };
        }).filter('autobr', ng(function (helpers) {
            return function (data) {
                if (!data) {
                    return data;
                }
                return data.replace(/\n\r?/g, '<br />');
            };

        })).filter('formatCurrency', ['$injector', '$locale', function ($injector, $locale) {
            var $filter = $injector.get('$filter'),
                numberFilter = $filter('number'),
                formats = $locale.NUMBER_FORMATS;
            formats.DEFAULT_PRECISION = angular.isUndefined(formats.DEFAULT_PRECISION) ? 2 : formats.DEFAULT_PRECISION;
            return function (amount, currency) {
                amount = parseFloat(amount, 10);
                if (!angular.isNumber(amount) || isNaN(amount)) {
                    return '';
                }
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

                s = '<' + number + '>';
                symb = currency.symbol;
                smb = currency.symbol
                if (smb) {
                    precedes = (isNegative && currency.negative_currency_symbol_precedes || currency.positive_currency_symbol_precedes)
                    separated = (isNegative && currency.negative_separate_by_space || currency.positive_separate_by_space)

                    if (precedes) {
                        s = smb + (separated ? ' ' : '') + s
                    }
                    else {
                        s = s + (separated ? ' ' : '') + smb
                    }
                }

                sign_pos = isNegative && currency.negative_sign_position || currency.positive_sign_position;
                sign = isNegative && currency.negative_sign || currency.positive_sign;

                if (sign_pos == 0) {
                    s = '(' + s + ')'
                }
                else if (sign_pos == 1) {
                    s = sign + s
                }
                else if (sign_pos == 2) {
                    s = s + sign
                }
                else if (sign_pos == 3) {
                    s = s.replace('<', sign)
                }
                else if (sign_pos == 4) {
                    s = s.replace('>', sign)
                }
                else {
                    # the default if nothing specified;
                    # this should be the most fitting sign position
                    s = sign + s
                }

                s = s.replace('<', '').replace('>', '')


                @classmethod
                def currency(cls, lang, val, currency, symbol=True, grouping=False):
                    """
                    Formats val according to the currency settings in lang.
                    """
                    # Code from currency in locale.py
                    if not lang:
                        lang = cls(
                            decimal_point=cls.default_decimal_point(),
                            thousands_sep=cls.default_thousands_sep(),
                            grouping=cls.default_grouping(),
                            )

                    # check for illegal values
                    digits = currency.digits
                    if digits == 127:
                        raise ValueError("Currency formatting is not possible using "
                                         "the 'C' locale.")

                    s = cls.format(lang, '%.%if' % digits, abs(val), grouping,
                            monetary=currency)
                    # '<' and '>' are markers if the sign must be inserted
                    # between symbol and value
                    s = '<' + s + '>'

                    if symbol:
                        smb = currency.symbol
                        precedes = (val < 0 and currency.n_cs_precedes
                            or currency.p_cs_precedes)
                        separated = (val < 0 and currency.n_sep_by_space
                            or currency.p_sep_by_space)

                        if precedes:
                            s = smb + (separated and ' ' or '') + s
                        else:
                            s = s + (separated and ' ' or '') + smb

                    sign_pos = val < 0 and currency.n_sign_posn or currency.p_sign_posn
                    sign = val < 0 and currency.negative_sign or currency.positive_sign

                    if sign_pos == 0:
                        s = '(' + s + ')'
                    elif sign_pos == 1:
                        s = sign + s
                    elif sign_pos == 2:
                        s = s + sign
                    elif sign_pos == 3:
                        s = s.replace('<', sign)
                    elif sign_pos == 4:
                        s = s.replace('>', sign)
                    else:
                        # the default if nothing specified;
                        # this should be the most fitting sign position
                        s = sign + s

                    return s.replace('<', '').replace('>', '')


                 */
                var isNegative = amount < 0,
                    number,
                    s,
                    smb,
                    precedes,
                    separated,
                    sign_pos,
                    sign;

                amount = Math.abs(amount);
                number = numberFilter(amount, currency.digits);

                s = '<' + number + '>';
                smb = currency.symbol;
                if (smb) {
                    precedes = (isNegative && currency.negative_currency_symbol_precedes || currency.positive_currency_symbol_precedes);
                    separated = (isNegative && currency.negative_separate_by_space || currency.positive_separate_by_space);

                    if (precedes) {
                        s = smb + (separated ? ' ' : '') + s;
                    } else {
                        s = s + (separated ? ' ' : '') + smb;
                    }
                }

                sign_pos = isNegative && currency.negative_sign_position || currency.positive_sign_position;
                sign = isNegative && currency.negative_sign || currency.positive_sign;
                if (!sign) {
                    sign = '';
                }

                if (sign_pos === 0) {
                    s = '(' + s + ')';
                } else if (sign_pos === 1) {
                    s = sign + s;
                } else if (sign_pos === 2) {
                    s = s + sign;
                } else if (sign_pos === 3) {
                    s = s.replace('<', sign);
                } else if (sign_pos === 4) {
                    s = s.replace('>', sign);
                } else {
                    s = sign + s;
                }

                s = s.replace('<', '').replace('>', '');

                return s;
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
        }).factory('outputTypes', ng(function (dateFilter, GLOBAL_CONFIG, modelsMeta) {
            var outputTypes = {
                SuperDateTimeProperty: function (input, field) {
                    var date = new Date(input),
                        now = new Date(),
                        thisyear = now.getYear() === date.getYear(),
                        thismonth = false,
                        today = false,
                        tz = ' UTC+1:00',
                        format = GLOBAL_CONFIG.date.format;
                    // for reference https://docs.angularjs.org/api/ng/filter/date
                    if (!thisyear) {
                        format = 'd MMM yyyy, HH:mm';
                    }
                    if (thisyear) {
                        thismonth = date.getMonth() === now.getMonth();
                        format = 'd MMM, HH:mm';
                    }
                    if (thismonth && thisyear && date.getDate() === now.getDate()) {
                        today = true;
                        format = 'HH:mm';
                    }
                    return dateFilter(date, format);
                }
            };
            return outputTypes;
        })).factory('searchBuilder', ng(function (modelsMeta, GLOBAL_CONFIG) {
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
                                label: GLOBAL_CONFIG.fields.label.search.indexID,
                                specifics: {
                                    translatedChoices: false
                                },
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
                                label: GLOBAL_CONFIG.fields.label.search.ancestor,
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
                                    label: GLOBAL_CONFIG.fields.label.search.operator,
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
        })).factory('channelApi', ng(function (GLOBAL_CONFIG) {
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
                                console.log('socket.open', that.socket);
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
        })).factory('channelNotifications', ng(function (channelApi, snackbar) {
            var channelNotifications = {
                instances: {},
                create: function (token, callback) {
                    var out;
                    out = channelApi.create(token);
                    //channelNotifications.instances[token] = out;
                    out.open({
                        onmessage: function (message, destroy) {
                            destroy();
                            if (angular.isObject(message) && message.data) {
                                try {
                                    var response = angular.fromJson(message.data);
                                    if (callback) {
                                        callback(response);
                                    } else {
                                        snackbar.show(response.body);
                                    }
                                } catch (ignore) {
                                    console.warn('channel callback could not execute, got error', ignore, 'with data', message);
                                }
                            } else {
                                console.warn('channel returned no parsable data, got', message);
                            }
                        }
                    });
                    return out;
                }
            };
            return channelNotifications;
        })).directive('contentSpinner', function () {
            return {
                templateUrl: 'core/misc/content_spinner.html',
                link: function (scope, element) {
                    var top = function () {
                            return element.find(':first');
                        },
                        hide = function () {
                            top().addClass('ng-hide');
                        },
                        show = function () {
                            top().removeClass('ng-hide');
                        };
                    scope.contentSpinner.hide.push(hide);
                    scope.contentSpinner.show.push(show);

                    scope.$on('$destroy', function () {
                        scope.contentSpinner.hide.remove(hide);
                        scope.contentSpinner.show.remove(show);
                    });
                }
            };
        }).directive('activitySpinner', ng(function ($animate) {
            return {
                scope: true,
                templateUrl: 'core/misc/activity_spinner.html',
                link: function (scope, element) {
                    scope.raised = true;
                    scope.slide = true;
                    var top = function () {
                            return element.find(':first');
                        },
                        digest = function () {
                            if (!scope.$$phase) {
                                scope.$digest();
                            }
                        },
                        slide = function () {
                            return top().find('.slide');
                        },
                        hide = function () {
                            if (top().hasClass('ng-hide')) {
                                return;
                            }
                            var s = slide();
                            if (s.length) {
                                $animate.addClass(s, 'out').then(function () {
                                    top().addClass('ng-hide');
                                    s.removeClass('in');
                                });
                            }
                        },
                        show = function () {
                            top().removeClass('ng-hide');
                            if (slide().length) {
                                $animate.removeClass(slide(), 'out').then(function () {
                                    return $animate.addClass(slide(), 'in');
                                });
                            }
                        };
                    scope.activitySpinner.hide.push(hide);
                    scope.activitySpinner.show.push(show);

                    scope.$on('$destroy', function () {
                        scope.activitySpinner.hide.remove(hide);
                        scope.activitySpinner.show.remove(show);
                    });
                }
            };
        })).directive('collapse', ['$animate', function ($animate) {

            return {
                link: function (scope, element, attrs) {
                    function expand() {
                        element.removeClass('collapse').addClass('collapsing');
                        $animate.addClass(element, 'in', {
                            to: {
                                height: element[0].scrollHeight + 'px'
                            }
                        }).then(expandDone);
                    }

                    function expandDone() {
                        element.removeClass('collapsing');
                        element.css({
                            height: 'auto'
                        });
                    }

                    function collapse() {
                        element
                        // IMPORTANT: The height must be set before adding "collapsing" class.
                        // Otherwise, the browser attempts to animate from height 0 (in
                        // collapsing class) to the given height here.
                            .css({
                                height: element[0].scrollHeight + 'px'
                            })
                            // initially all panel collapse have the collapse class, this removal
                            // prevents the animation from jumping to collapsed state
                            .removeClass('collapse')
                            .addClass('collapsing');

                        $animate.removeClass(element, 'in', {
                            to: {
                                height: '0'
                            }
                        }).then(collapseDone);
                    }

                    function collapseDone() {
                        element.css({
                            height: '0'
                        }); // Required so that collapse works when animation is disabled
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
        }]).directive('nonBlockingNgClass', ng(function ($animate, $rootScope, $$rAF) {
            return {
                link: function (scope, element, attrs) {
                    var changed = {},
                        now = $.now();
                    scope.$watch(function () {
                        var run = false,
                            parser = scope.$eval(attrs.nonBlockingNgClass);
                        if (changed) {
                            angular.forEach(parser, function (value, key) {
                                if (changed[key] !== value && !run) {
                                    run = $.now();
                                }
                                changed[key] = value;
                            });
                        }
                        return (run || now);
                    }, function (neww, old) {
                        if (neww !== old) {
                            angular.forEach(scope.$eval(attrs.nonBlockingNgClass), function (value, key) {
                                $rootScope.$$postDigest(function () {
                                    $$rAF(function () {
                                        element[value ? 'addClass' : 'removeClass'](key);
                                    });
                                });
                            });
                        }
                    });
                }
            };
        }));
}());
