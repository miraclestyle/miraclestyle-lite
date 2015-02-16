(function () {
    'use strict';
    angular.module('app').directive('buyerAddressListView', function () {
        return {
            scope: {
                val: '=buyerAddressListView'
            },
            templateUrl: 'buyer/address_list_view.html',
            controller: function ($scope) {
                $scope.notEmpty = function (val) {
                    return angular.isString(val) || angular.isNumber(val);
                };
            }
        };
    });
}());