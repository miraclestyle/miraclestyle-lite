(function () {
    'use strict';
    angular.module('app').factory('snackbar', ng(function (GLOBAL_CONFIG) {
        var snackbar = {
            show: $.noop,
            hide: $.noop,
            showK: function (key, config) {
                var gets = GLOBAL_CONFIG.snackbar.messages[key];
                if (angular.isUndefined(gets)) {
                    gets = key;
                }
                return snackbar.show($.extend({
                    message: gets
                }, config));
            }
        };
        if (GLOBAL_CONFIG.debug) {
            window._snackbar = snackbar;
        }
        return snackbar;
    })).directive('qsnackbar', ng(function (snackbar) {
        return {
            link: function (scope, element) {
                var kill = function () {
                    snackbar.hide();
                };
                element.on('click', kill);
                scope.$on('$destroy', function () {
                    element.off('click', kill);
                });
            }
        };
    })).directive('ngClick', ng(function (snackbar) {
        return {
            restrict: 'A',
            priority: 100,
            link: function (scope, element, attr) {
                var kill = function () {
                    if (!snackbar.animating) {
                        snackbar.hide();
                    }
                };
                element.on('click', kill);
                scope.$on('$destroy', function () {
                    element.off('click', kill);
                });
            }
        };
    })).directive('snackbar', ng(function (snackbar, $timeout, $animate, $animateCss, $q) {
        return {
            scope: true,
            require: 'snackbar',
            templateUrl: 'core/snackbar/view.html',
            controller: ng(function ($scope) {
                var digest = function () {
                        if (!$scope.$$phase) {
                            $scope.$digest();
                        }
                    },
                    timer;
                $scope.message = '';
                $scope.size = 1;
                $scope.element = null;

                snackbar.animating = false;
                snackbar.hide = function () {
                    $scope.element.removeClass('in');
                    return $animateCss($scope.element, {
                        addClass: 'out'
                    }).start();
                };
                snackbar.show = function (config) {
                    if (!angular.isObject(config)) {
                        config = {
                            message: config
                        };
                    }
                    $scope.message = config.message;
                    if (!config.hideAfter) {
                        config.hideAfter = (($scope.message.length / 16) * 2000) + 500;
                    }
                    $scope.size = config.size;
                    $scope.calculateSize = function () {
                        if (!$scope.size) {
                            return $scope.element.find('.brief').height() > 16 ? 2 : 1;
                        }
                        return $scope.size;
                    };
                    return snackbar.hide().done(function () {
                        $scope.element.removeClass('out');
                        return $animateCss($scope.element, {
                            addClass: 'in'
                        }).start().done(function () {
                            if (config.hideAfter) {
                                if (timer) {
                                    clearTimeout(timer);
                                }
                                timer = setTimeout(function () {
                                    snackbar.hide();
                                }, config.hideAfter);

                                digest();
                            }
                        });
                    });
                };
            }),
            link: function (scope, element, snackbarCtrl) {
                scope.element = element.find('.snackbar');
            }
        };
    }));
}());
