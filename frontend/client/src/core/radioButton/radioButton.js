/*!
 * Angular Material Design
 * https://github.com/angular/material
 * @license MIT
 * v0.7.1
 */
(function () {
    'use strict';


    /**
     * @ngdoc module
     * @name material.components.radioButton
     * @description radioButton module!
     */
    angular.module('material.components.radioButton', [
            'material.core'
        ])
        .directive('mdRadioGroup', mdRadioGroupDirective)
        .directive('mdRadioButton', mdRadioButtonDirective);

    function mdRadioGroupDirective($mdUtil, $mdConstant) {
        RadioGroupController.prototype = createRadioGroupControllerProto();

        return {
            restrict: 'E',
            controller: ['$element', RadioGroupController],
            require: ['mdRadioGroup', '?ngModel'],
            link: {
                pre: linkRadioGroup
            }
        };

        function linkRadioGroup(scope, element, attr, ctrls) {
 
            var rgCtrl = ctrls[0];
            var ngModelCtrl = ctrls[1] || $mdUtil.fakeNgModel();

            function keydownListener(ev) {
                switch (ev.keyCode) {
                case $mdConstant.KEY_CODE.LEFT_ARROW:
                case $mdConstant.KEY_CODE.UP_ARROW:
                    ev.preventDefault();
                    rgCtrl.selectPrevious();
                    break;

                case $mdConstant.KEY_CODE.RIGHT_ARROW:
                case $mdConstant.KEY_CODE.DOWN_ARROW:
                    ev.preventDefault();
                    rgCtrl.selectNext();
                    break;

                case $mdConstant.KEY_CODE.ENTER:
                    var form = angular.element($mdUtil.getClosest(element[0], 'form'));
                    if (form.length > 0) {
                        form.triggerHandler('submit');
                    }
                    break;
                }
            }

            rgCtrl.init(ngModelCtrl);

            element.attr({
                    'role': 'radiogroup',
                    'tabIndex': element.attr('tabindex') || '0'
                })
                .on('keydown', keydownListener);

        }

        function RadioGroupController($element) {
            this._radioButtonRenderFns = [];
            this.$element = $element;
        }

        function createRadioGroupControllerProto() {
                return {
                    init: function (ngModelCtrl) {
                        this._ngModelCtrl = ngModelCtrl;
                        this._ngModelCtrl.$render = angular.bind(this, this.render);
                    },
                    add: function (rbRender) {
                        this._radioButtonRenderFns.push(rbRender);
                    },
                    remove: function (rbRender) {
                        var index = this._radioButtonRenderFns.indexOf(rbRender);
                        if (index !== -1) {
                            this._radioButtonRenderFns.splice(index, 1);
                        }
                    },
                    render: function () {
                        this._radioButtonRenderFns.forEach(function (rbRender) {
                            rbRender();
                        });
                    },
                    setViewValue: function (value, eventType) {
                        this._ngModelCtrl.$setViewValue(value, eventType);
                        // update the other radio buttons as well
                        this.render();
                    },
                    getViewValue: function () {
                        return this._ngModelCtrl.$viewValue;
                    },
                    selectNext: function () {
                        return changeSelectedButton(this.$element, 1);
                    },
                    selectPrevious: function () {
                        return changeSelectedButton(this.$element, -1);
                    },
                    setActiveDescendant: function (radioId) {
                        this.$element.attr('aria-activedescendant', radioId);
                    }
                };
            }
            /**
             * Change the radio group's selected button by a given increment.
             * If no button is selected, select the first button.
             */
        function changeSelectedButton(parent, increment) {
            // Coerce all child radio buttons into an array, then wrap then in an iterator
            var buttons = $mdUtil.iterator(
                Array.prototype.slice.call(parent[0].querySelectorAll('md-radio-button')),
                true
            );

            if (buttons.count()) {
                var validate = function (button) {
                    // If disabled, then NOT valid
                    return !angular.element(button).attr("disabled");
                };
                var selected = parent[0].querySelector('md-radio-button.md-checked');
                var target = buttons[increment < 0 ? 'previous' : 'next'](selected, validate) || buttons.first();
                // Activate radioButton's click listener (triggerHandler won't create a real click event)
                angular.element(target).triggerHandler('click');


            }
        }

    }
    mdRadioGroupDirective.$inject = ["$mdUtil", "$mdConstant"];


    function mdRadioButtonDirective($mdAria, $mdUtil) {

        var CHECKED_CSS = 'md-checked';

        return {
            restrict: 'E',
            require: '^mdRadioGroup',
            transclude: true,
            template: '<div class="md-container list-primary-tile">' +
                '<div class="avatar-small"><div><icon class="button-square" type="radio_button_on"></icon>' +
                '<icon class="button-square" type="radio_button_off"></icon></div>' +
                '</div></div>' +
                '<div ng-transclude class="md-label"></div>',
            link: link
        };

        function link(scope, element, attr, rgCtrl) {
            var lastChecked;
            configureAria(element, scope);

            rgCtrl.add(render);
            attr.$observe('value', render);

            element
                .on('click', listener)
                .on('$destroy', function () {
                    rgCtrl.remove(render);
                });

            function listener(ev) {
                if (element[0].hasAttribute('disabled')) return;

                scope.$apply(function () {
                    rgCtrl.setViewValue(attr.value, ev && ev.type);
                });
            }

            function render() {
                    var checked = (rgCtrl.getViewValue() == attr.value);
                    if (checked === lastChecked) {
                        return;
                    }
                    lastChecked = checked;
                    element.attr('aria-checked', checked);
                    if (checked) {
                        element.addClass(CHECKED_CSS);
                        rgCtrl.setActiveDescendant(element.attr('id'));
                    } else {
                        element.removeClass(CHECKED_CSS);
                    }
                }
                /**
                 * Inject ARIA-specific attributes appropriate for each radio button
                 */
            function configureAria(element, scope) {
                scope.ariaId = buildAriaID();

                element.attr({
                    'id': scope.ariaId,
                    'role': 'radio',
                    'aria-checked': 'false'
                });

                $mdAria.expectWithText(element, 'aria-label');

                /**
                 * Build a unique ID for each radio button that will be used with aria-activedescendant.
                 * Preserve existing ID if already specified.
                 * @returns {*|string}
                 */
                function buildAriaID() {
                    return attr.id || ('radio' + "_" + $mdUtil.nextUid());
                }
            }
        }
    }
    mdRadioButtonDirective.$inject = ["$mdAria", "$mdUtil"];

})();
