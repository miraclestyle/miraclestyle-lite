(function () {
    'use strict';
    angular.module('app')
        .controller('MainMenuCtrl', function ($scope, currentAccount) {
            $scope.currentAccount = currentAccount;
        })
        .controller('HomePageCtrl', ['$scope', function ($scope) {
            $scope.showMenu = function () {
                $scope.$emit('show_menu');
            };
        }]);

}());