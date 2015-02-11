(function () {
    'use strict';
    angular.module('app').directive('buyerAddressDisplay', function ($compile) {
        return {
            scope: {
                val: '=buyerAddressDisplay',
                field: '=buyerAddressDisplayField'
            },
            templateUrl: 'buyer/address_display.html',
            controller: function ($scope) {
                $scope.notEmpty = function (val) {
                    return angular.isString(val) || angular.isNumber(val);
                };
            }
        };
    });
}());