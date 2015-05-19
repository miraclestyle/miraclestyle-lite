(function () {
    'use strict';
    angular.module('app').directive('actionDropdownList', function () {
        return {
            templateUrl: 'core/action/dropdown_list.html',
            transclude: true,
            replace: true
        };
    }).directive('actionDropdown', function ($simpleDialog, $$rAF, $mdConstant, underscoreTemplate, $timeout, $parse, $q, helpers) {
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

                dropdown.opened = false;
                dropdown.open = function ($event) {
                    if (dropdown.opened) {
                        return;
                    }
                    dropdown.opened = true;
                    $timeout(function () {
                        dropdown.openSimpleDialog($event);
                    });
                };
                dropdown.openSimpleDialog = function ($event) {
                    $simpleDialog.show({
                        templateUrl: template,
                        popFrom: $event.target,
                        parent: element.parents(attrs.parent),
                        onBeforeHide: function (dialogEl, options) {
                            $(window).off('resize', options.resize);
                        },
                        onBeforeShow: function (dialogEl, options) {
                            var nextDefer = $q.defer(), nextPromise = nextDefer.promise, animateSelect = function () {
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

                                $$rAF(function () {
                                    dialogEl.addClass('fade in');
                                });

                                dialogEl.oneAnimationEnd(function () {
                                    element.addClass('opacity-in');
                                    nextDefer.resolve();
                                });

                                return nextPromise;

                            };

                            $$rAF(animateSelect);

                            dialogEl.on('click', dropdown.close);
                        },
                        controller: function ($scope) {
                            $scope.parent = scope;
                            $scope.$on('$destroy', function () {
                                dropdown.opened = false;
                            });
                        }
                    });
                };
                dropdown.close = function () {
                    $simpleDialog.hide();
                };
                scope.dropdown = dropdown;
            }
        };
    }).directive('actionToolbar', function () {
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
