(function () {
    'use strict';
    angular.module('app').directive('actionDropdownList', function () {
        return {
            templateUrl: 'core/action/dropdown_list.html',
            transclude: true,
            replace: true
        };
    }).directive('actionDropdown', function ($simpleDialog, $mdTheming,
        $mdInkRipple, $$rAF, $mdConstant, underscoreTemplate, $timeout, $parse, helpers) {
        return {
            replace: true,
            transclude: true,
            templateUrl: 'core/action/dropdown.html',
            scope: true,
            link: function (scope, element, attrs) {
                var dropdown = {},
                    template = scope.$eval(attrs.template);
                if (!template) {
                    return;
                }
                dropdown.open = function ($event) {
                    $simpleDialog.show({
                        templateUrl: template,
                        targetEvent: $event,
                        parent: element.parents(attrs.parent),
                        onBeforeHide: function (dialogEl, options) {
                            $(window).off('resize', options.resize);
                        },
                        onBeforeShow: function (dialogEl, options) {
                            var animateSelect = function () {
                                var target = element;
                                options.resize = function () {
                                    var targetOffset = target.offset(),
                                        parent = options.parent,
                                        paddingTop = parseInt(parent.css('padding-top'), 10) || 24,
                                        paddingBottom = parseInt(parent.css('padding-bottom'), 10) || 24,
                                        newTop = targetOffset.top,
                                        newLeft = (targetOffset.left - (dialogEl.width() - target.outerWidth())) - 12,
                                        height = parent.height() - (paddingBottom + paddingTop),
                                        maxLeft = parent.width() - dialogEl.width() - 16;
                                    newTop = targetOffset.top;
                                    if (newTop < 16) {
                                        newTop = 16;
                                    }
                                    if (newLeft < 16) {
                                        newLeft = 16;
                                    }
                                    if (newLeft > maxLeft) {
                                        newLeft = maxLeft;
                                    }
                                    dialogEl.css({
                                        top: newTop,
                                        left: newLeft
                                    });
                                    if (dialogEl.height() > height) {
                                        dialogEl.height(height);
                                    }
                                };
                                options.resize();
                                $(window).on('resize', options.resize);

                                dialogEl.css($mdConstant.CSS.TRANSFORM, 'scale(' +
                                        Math.min(target.width() / dialogEl.width(), 1.0) + ',' +
                                        Math.min(target.height() / dialogEl.height(), 1.0) + ')')
                                    .on($mdConstant.CSS.TRANSITIONEND, function (ev) {
                                        if (ev.target === dialogEl[0]) {
                                            dropdown.opened = true;
                                        }
                                    });
                                $$rAF(function () {
                                    dialogEl.addClass('transition-in');
                                    dialogEl.css($mdConstant.CSS.TRANSFORM, '');
                                });

                            };

                            $$rAF(animateSelect);

                            dialogEl.on('click', dropdown.close);
                        },
                        controller: function ($scope) {
                            $scope.parent = scope;
                        }
                    });
                };
                dropdown.close = function () {
                    $simpleDialog.hide().then(function () {
                        dropdown.opened = false;
                    });
                };
                scope.dropdown = dropdown;
            }
        };
    }).directive('actionToolbar', function ($mdInkRipple) {
        return {
            transclude: true,
            replace: true,
            scope: true,
            templateUrl: 'core/action/toolbar.html',
            link: function (scope, element, attrs) {
                scope.spec = scope.$eval(attrs.spec);
            }
        };
    });
}());
