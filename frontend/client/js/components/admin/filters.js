(function () {
    'use strict';
    angular.module('app').filter('showFriendlyIndexName', function () {
        return function (input) {
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
        };
    });

}());
