(function () {
    'use strict';
    var notEmpty = function (val) {
        return angular.isString(val) || angular.isNumber(val);
    };
    angular.module('app').directive('addressRuleLocationListView', function () {
        return {
            scope: {
                val: '=addressRuleLocationListView'
            },
            templateUrl: 'seller/address_rule_location_list_view.html',
            controller: function ($scope) {
                $scope.notEmpty = notEmpty;
                $scope.postalCodes = function (postalCodes) {
                    return postalCodes.join(', ');
                };

            }
        };
    }).directive('defaultLineListView', function () {
        return {
            scope: {
                val: '=defaultLineListView'
            },
            templateUrl: 'seller/default_line_list_view.html'
        };
    }).directive('carrierLineRuleListView', function () {
        return {
            scope: {
                val: '=carrierLineRuleListView'
            },
            templateUrl: 'seller/carrier_line_rule_list_view.html',
            controller: function ($scope) {
                $scope.notEmpty = notEmpty;

            }
        };
    }).directive('pluginListView', function (modelsMeta) {
        return {
            scope: {
                val: '=pluginListView'
            },
            templateUrl: 'seller/plugin_list_view.html',
            controller: function ($scope) {
                $scope.pluginName = function (kind) {
                    return modelsMeta.getName(kind);
                };
            }
        };
    });

}());