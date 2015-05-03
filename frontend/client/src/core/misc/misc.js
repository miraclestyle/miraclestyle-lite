(function () {
    'use strict';
    angular.module('app')
        .run(function (helpers, $mdConstant) {
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
                    scope.color = attrs.color || 'normal';
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
                replace: true
            };
        }).filter('labelize', function (GLOBAL_CONFIG) {
            return function (key, group) {
                if (angular.isUndefined(group)) {
                    group = 'default';
                }
                var get = GLOBAL_CONFIG.labels[group][key];
                if (angular.isDefined(get)) {
                    return get;
                }
                return key;
            };
        }).filter('propsFilter', function () {
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

                    s = cls.format(lang, '%%.%if' % digits, abs(val), grouping,
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
                            $.extend(field.ui, {
                                args: 'search.send.filters[\'' + i + '\'].value',
                                writable: true
                            });

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
                                        modals.alert('channelNotifications', {
                                            title: 'Notification from server',
                                            messages: [response.body]
                                        });
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
