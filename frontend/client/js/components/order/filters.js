(function () {
    'use strict';
    angular.module('app').filter('displayTaxes', function () {
        return function (value) {
            var formatted = '';
            if (value) {
                formatted = $.map(value, function (item) {
                    return item.name;
                }).join(', ');
            }
            return formatted;
        };
    });

}());