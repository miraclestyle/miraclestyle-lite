(function () {
    'use strict';
    var notEmpty = function (val) {
        return angular.isString(val) || angular.isNumber(val);
    };
    angular.module('app').directive('addressRuleLocationDisplay', function () {
        return {
            scope: {
                val: '=addressRuleLocationDisplay',
                field: '=addressRuleLocationDisplayField'
            },
            templateUrl: 'seller/directive/address_rule_location_display.html',
            controller: function ($scope) {
                $scope.notEmpty = notEmpty;

            }
        };
    }).directive('defaultLineDisplay', function () {
        return {
            scope: {
                val: '=defaultLineDisplay',
                field: '=defaultLineDisplay'
            },
            templateUrl: 'seller/directive/default_line_display.html'
        };
    }).directive('carrierLineRuleDisplay', function () {
        return {
            scope: {
                val: '=carrierLineRuleDisplay',
                field: '=carrierLineRuleDisplayField'
            },
            templateUrl: 'seller/directive/carrier_line_rule_display.html',
            controller: function ($scope) {
                $scope.notEmpty = notEmpty;

            }
        };
    });

}());