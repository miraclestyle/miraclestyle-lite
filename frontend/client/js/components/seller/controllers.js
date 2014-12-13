(function () {
    'use strict';
    angular.module('app')
        .controller('SellerManagementCtrl', function ($scope, endpoint,
            currentAccount, models) {

            $scope.settings = function () {
                models['23'].manageModal(currentAccount.key);
            };

        });
}());