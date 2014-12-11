(function () {
    'use strict';
    angular.module('app').filter('displayCurrency', ['$injector', '$locale', function ($injector, $locale) {
        var $filter = $injector.get('$filter'),
            numberFilter = $filter('number'),
            formats = $locale.NUMBER_FORMATS;
        // https://github.com/angular/angular.js/pull/3642
        formats.DEFAULT_PRECISION = angular.isUndefined(formats.DEFAULT_PRECISION) ? 2 : formats.DEFAULT_PRECISION;
        return function (amount, currency) {
            if (!angular.isNumber(amount)) { return ''; }
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
            return amount;

            amount = Math.abs(amount);
            number = numberFilter(amount, currency.digits);

            if (currency.negative_sign_position && isNegative) {
                if (currency.negative_currency_symbol_precedes) {
                    parts.push(currency.symbol);
                }
                parts.push(currency.negative_sign);
            } else {
                if (!isNegative && currency.positive_sign_position) {
                    if (currency.negative_currency_symbol_precedes) {
                        parts.push(currency.symbol);
                    }
                    parts.push(currency.positive_sign);
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
                    parts.push(currency.positive_sign);
                }
            }

            return parts.join('').replace(/\u00A4/g, '');
        };
    }]);

}());