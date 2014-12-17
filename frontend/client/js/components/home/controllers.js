(function () {
    'use strict';
    angular.module('app')
        .controller('MainMenuCtrl', function ($scope, currentAccount, GLOBAL_CONFIG) {
            $scope.currentAccount = currentAccount;
            $scope.GLOBAL_CONFIG = GLOBAL_CONFIG;
            $scope.JSON = JSON;
        })
        .controller('HomePageCtrl', ['$scope', function ($scope) {
            $scope.showMenu = function () {
                $scope.$emit('show_menu');
            };
        }]);

}());