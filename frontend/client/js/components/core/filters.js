(function () {
    'use strict';
    angular.module('app').filter('propsFilter', function () {
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

    }).filter('displayCurrency', ['$injector', '$locale', function ($injector, $locale) {
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
    });

}());
