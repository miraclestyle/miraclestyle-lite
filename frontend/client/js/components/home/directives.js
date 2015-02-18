(function () {
    'use strict';

    angular.module('app').directive('mainMenuItem', function ($timeout, $mdSidenav) {
        return {
            templateUrl: 'home/main_menu_item.html',
            transclude: true,
            replace: true,
            link: function (scope, element, attrs) {
                element.on('click', function () {
                    $timeout(function () {
                        $mdSidenav('left').close();
                    }, 300);
                });
            }
        };
    });

}());