(function () {
    'use strict';

    angular.module('material.components.button', [
            'material.core'
        ])
        .directive('mdButton', MdButtonDirective);

    function MdButtonDirective($mdInkRipple, $mdAria) {

        return {
            restrict: 'E',
            replace: true,
            transclude: true,
            template: getTemplate,
            link: postLink
        };

        function isAnchor(attr) {
            return angular.isDefined(attr.href) || angular.isDefined(attr.ngHref);
        }

        function getTemplate(element, attr) {
            return isAnchor(attr) ?
                '<a class="md-button" ng-transclude></a>' :
                '<button class="md-button" ng-transclude></button>';
        }

        function postLink(scope, element, attr) {
            var node = element[0];
            $mdInkRipple.attachButtonBehavior(scope, element);

            var elementHasText = node.textContent.trim();
            if (!elementHasText) {
                $mdAria.expect(element, 'aria-label');
            }

            // For anchor elements, we have to set tabindex manually when the 
            // element is disabled
            if (isAnchor(attr) && angular.isDefined(attr.ngDisabled)) {
                scope.$watch(attr.ngDisabled, function (isDisabled) {
                    element.attr('tabindex', isDisabled ? -1 : 0);
                });
            }
        }

    }
    MdButtonDirective.$inject = ["$mdInkRipple", "$mdAria"];
})();
