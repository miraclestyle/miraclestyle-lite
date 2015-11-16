(function () {
    'use strict';

    angular.module('material.components.checkbox', [
            'material.core'
        ])
        .directive('mdCheckbox', MdCheckboxDirective);

    function MdCheckboxDirective(inputDirective, $mdAria, $mdConstant, $mdUtil, $timeout, $animate) {
        inputDirective = inputDirective[0];
        var CHECKED_CSS = 'md-checked';

        return {
            restrict: 'E',
            transclude: true,
            require: '?ngModel',
            template: '<div class="md-container list-primary-tile">' +
                '<div class="avatar-small"><div><icon class="button-square" type="check_box"></icon>' +
                '<icon class="button-square" type="check_box_outline_blank"></icon></div>' +
                '</div></div>' +
                '<div ng-transclude class="md-label"></div>',
            compile: compile
        };

        // **********************************************************
        // Private Methods
        // **********************************************************

        function compile(tElement, tAttrs) {

            tAttrs.type = 'checkbox';
            tAttrs.tabindex = tAttrs.tabindex || '0';
            tElement.attr('role', tAttrs.type);

            // Attach a click handler in compile in order to immediately stop propagation
            // (especially for ng-click) when the checkbox is disabled.
            tElement.on('click', function (event) {
                if (this.hasAttribute('disabled')) {
                    event.stopImmediatePropagation();
                }
            });

            return function postLink(scope, element, attr, ngModelCtrl) {
                ngModelCtrl = ngModelCtrl || $mdUtil.fakeNgModel();


                if (attr.ngChecked) {
                    scope.$watch(
                        scope.$eval.bind(scope, attr.ngChecked),
                        ngModelCtrl.$setViewValue.bind(ngModelCtrl)
                    );
                }

                $$watchExpr('ngDisabled', 'tabindex', {
                    true: '-1',
                    false: attr.tabindex
                });

                // Reuse the original input[type=checkbox] directive from Angular core.
                // This is a bit hacky as we need our own event listener and own render
                // function.
                inputDirective.link.pre(scope, {
                    on: angular.noop,
                    0: {}
                }, attr, [ngModelCtrl]);

                scope.mouseActive = false;
                element.on('click', listener)
                    .on('keypress', keypressHandler)
                    .on('mousedown', function () {
                        scope.mouseActive = true;
                        $timeout(function () {
                            scope.mouseActive = false;
                        }, 100);
                    })
                    .on('focus', function () {
                        if (scope.mouseActive === false) {
                            element.addClass('md-focused');
                        }
                    })
                    .on('blur', function () {
                        element.removeClass('md-focused');
                    });

                ngModelCtrl.$render = render;

                function $$watchExpr(expr, htmlAttr, valueOpts) {
                    if (attr[expr]) {
                        scope.$watch(attr[expr], function (val) {
                            if (valueOpts[val]) {
                                element.attr(htmlAttr, valueOpts[val]);
                            }
                        });
                    }
                }

                function keypressHandler(ev) {
                    var keyCode = ev.which || ev.keyCode;
                    if (keyCode === $mdConstant.KEY_CODE.SPACE || keyCode === $mdConstant.KEY_CODE.ENTER) {
                        ev.preventDefault();

                        if (!element.hasClass('md-focused')) {
                            element.addClass('md-focused');
                        }

                        listener(ev);
                    }
                }

                function listener(ev) {
                    if (element[0].hasAttribute('disabled')) {
                        return;
                    }

                    (function () {
                        // Toggle the checkbox value...
                        var viewValue = attr.ngChecked ? attr.checked : !ngModelCtrl.$viewValue;

                        ngModelCtrl.$setViewValue(viewValue, ev && ev.type);
                        ngModelCtrl.$render();
                    }());

                    scope.$digest();
                }

                function render() {
                    if (ngModelCtrl.$viewValue) {
                        $animate.addClass(element, CHECKED_CSS);
                    } else {
                        $animate.removeClass(element, CHECKED_CSS);
                    }
                }
            };
        }
    }
    MdCheckboxDirective.$inject = ["inputDirective", "$mdAria", "$mdConstant", "$mdUtil", "$timeout", "$animate"];

})();
