(function () {
    'use strict';
    var module = angular.module('material.components.swipe', []);

    ['SwipeLeft', 'SwipeRight'].forEach(function (name) {
        var directiveName = 'md' + name;
        var eventName = '$md.' + name.toLowerCase();

        module.directive(directiveName, /*@ngInject*/ ["$parse", function ($parse) {
            return {
                restrict: 'A',
                link: postLink
            };

            function postLink(scope, element, attr) {
                var fn = $parse(attr[directiveName]);

                element.on(eventName, function (ev) {
                    scope.$apply(function () {
                        fn(scope, {
                            $event: ev
                        });
                    });
                });

            }
        }]);
    });

})();
