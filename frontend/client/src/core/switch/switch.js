(function () {
    'use strict';

    angular.module('material.components.switch', [
            'material.core',
            'material.components.checkbox'
        ])
        .directive('mdInkRippleSwitch', ng(function ($mdInkRipple) {
            return {
                link: function (scope, element, attrs) {
                    $mdInkRipple.attachButtonBehavior(scope, element, {
                        dimBackground: false
                    });
                }
            };
        }))
        .directive('mdSwitch', MdSwitch);

    function MdSwitch(mdCheckboxDirective, $mdUtil, $document, $mdConstant, $parse, $$rAF, $mdGesture) {
        var checkboxDirective = mdCheckboxDirective[0];

        return {
            restrict: 'E',
            transclude: true,
            template: '<div ng-transclude class="md-label"></div>' +
                '<div class="md-container">' +
                '<div class="md-bar"></div>' +
                '<div class="md-thumb-container">' +
                '<div class="md-thumb"></div>' +
                '</div>' +
                '</div>',
            require: '?ngModel',
            compile: compile
        };

        function compile(element, attr) {
            var checkboxLink = checkboxDirective.compile(element, attr);
            // no transition on initial load
            element.addClass('md-dragging');

            return function (scope, element, attr, ngModel) {
                ngModel = ngModel || $mdUtil.fakeNgModel();
                var disabledGetter = $parse(attr.ngDisabled);
                var thumbContainer = angular.element(element[0].querySelector('.md-thumb-container'));
                var switchContainer = angular.element(element[0].querySelector('.md-container'));

                // no transition on initial load
                $$rAF(function () {
                    element.removeClass('md-dragging');
                });

                checkboxLink(scope, element, attr, ngModel);

                if (angular.isDefined(attr.ngDisabled)) {
                    scope.$watch(disabledGetter, function (isDisabled) {
                        element.attr('tabindex', isDisabled ? -1 : 0);
                    });
                }

                // These events are triggered by setup drag
                $mdGesture.register(switchContainer, 'drag');
                switchContainer
                    .on('$md.dragstart', onDragStart)
                    .on('$md.drag', onDrag)
                    .on('$md.dragend', onDragEnd);

                var drag;

                function onDragStart(ev) {
                    // Don't go if ng-disabled===true
                    if (disabledGetter(scope)) return;
                    ev.stopPropagation();

                    element.addClass('md-dragging');
                    drag = {
                        width: thumbContainer.prop('offsetWidth')
                    };
                    element.removeClass('transition');
                }

                function onDrag(ev) {
                    if (!drag) return;
                    ev.stopPropagation();
                    ev.srcEvent && ev.srcEvent.preventDefault();

                    var percent = ev.pointer.distanceX / drag.width;

                    //if checked, start from right. else, start from left
                    var translate = ngModel.$viewValue ? 1 + percent : percent;
                    // Make sure the switch stays inside its bounds, 0-1%
                    translate = Math.max(0, Math.min(1, translate));

                    thumbContainer.css($mdConstant.CSS.TRANSFORM, 'translate3d(' + (100 * translate) + '%,0,0)');
                    drag.translate = translate;
                }

                function onDragEnd(ev) {
                    if (!drag) return;
                    ev.stopPropagation();

                    element.removeClass('md-dragging');
                    thumbContainer.css($mdConstant.CSS.TRANSFORM, '');

                    // We changed if there is no distance (this is a click a click),
                    // or if the drag distance is >50% of the total.
                    var isChanged = ngModel.$viewValue ? drag.translate < 0.5 : drag.translate > 0.5;
                    if (isChanged) {
                        applyModelValue(!ngModel.$viewValue);
                    }
                    drag = null;
                }

                function applyModelValue(newValue) {
                    scope.$apply(function () {
                        ngModel.$setViewValue(newValue);
                        ngModel.$render();
                    });
                }

            };
        }


    }
    MdSwitch.$inject = ["mdCheckboxDirective", "$mdUtil", "$document", "$mdConstant", "$parse", "$$rAF", "$mdGesture"];

})();
