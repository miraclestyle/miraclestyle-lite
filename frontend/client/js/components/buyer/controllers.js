(function () {
    'use strict';
    angular.module('app')
        .controller('BuyerManagementCtrl', function ($scope, endpoint, currentAccount, models) {

            $scope.settings = function () {
                models['19'].manageModal(currentAccount.key);
            };

            $scope.manageCollection = function () {
                models['18'].manageModal(currentAccount.key);
            };

        });
}());
