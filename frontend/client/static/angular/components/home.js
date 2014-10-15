angular.module('app').controller('HomePageCtrl', ['$scope', function ($scope) {
    $scope.showMenu = function ()
    {
       $scope.$emit('show_menu');
    };
}]);
