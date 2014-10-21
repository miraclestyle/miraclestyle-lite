angular.module('app')
.controller('MainMenuCtrl', function ($scope, current_account) {
    $scope.current_account = current_account;
})
.controller('HomePageCtrl', ['$scope', function ($scope) {
    $scope.showMenu = function ()
    {
       $scope.$emit('show_menu');
    };
}]);