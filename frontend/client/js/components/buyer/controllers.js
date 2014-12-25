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

        }).controller('BuyOrdersCtrl', function ($scope, modals, modelsEditor, modelsMeta, models, modelsUtil, visualAid, $rootScope) {

            $rootScope.pageTitle = 'Buyer Orders';

        }).controller('BuyCartsCtrl', function ($scope, modals, modelsEditor, modelsMeta, models, modelsUtil, visualAid, $rootScope) {

            $rootScope.pageTitle = 'Buyer Carts';
        });
}());
