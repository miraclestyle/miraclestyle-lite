angular.module('app').controller('HomePage', ['$scope', function ($scope) {
    $scope.showMenu = function ()
    {
       $scope.$emit('show_menu');
    };
}]);
