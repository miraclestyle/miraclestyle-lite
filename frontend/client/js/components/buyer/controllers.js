(function () {
    'use strict';
    angular.module('app')
        .controller('BuyerManagementCtrl', function ($scope, endpoint, currentAccount, models) {

            $scope.settings = function () {
                models['19'].settingsModal(currentAccount.key);
            };

        });
}());
