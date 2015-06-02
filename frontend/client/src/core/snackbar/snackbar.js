(function () {
    'use strict';
    angular.module('app').factory('snackbar', ng(function (GLOBAL_CONFIG) {
        var snackbar = {
            show: $.noop,
            hide: $.noop,
            showK: function (key) {
                var gets = GLOBAL_CONFIG.snackbar.messages[key];
                if (angular.isUndefined(gets)) {
                    gets = key;
                }
                return snackbar.show(gets);
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
                    snackbar.hide();
                };
                element.on('click', kill);
                scope.$on('$destroy', function () {
                    element.off('click', kill);
                });
            }
        };
    })).directive('snackbar', ng(function (snackbar, $timeout, $animate, $q) {
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
                snackbar.hide = function () {
                    var defer = $q.defer();
                    $scope.element.removeClass('in');
                    if (!$scope.element.hasClass('out')) {
                        $animate.addClass($scope.element, 'out').then(function () {
                            defer.resolve();
                        });
                        digest();
                    } else {
                        defer.resolve();
                    }
                    return defer.promise;
                };
                snackbar.show = function (config) {
                    if (!angular.isObject(config)) {
                        config = {
                            message: config
                        };
                    }
                    $scope.message = config.message;
                    if (!config.size) {
                        config.size = 1;
                    }
                    if (!config.hideAfter) {
                        config.hideAfter = (($scope.message.length / 16) * 1000) + 500;
                    }
                    $scope.size = config.size;
                    digest();
                    return snackbar.hide().then(function () {
                        $animate.removeClass($scope.element, 'out');
                        return $animate.addClass($scope.element, 'in').then(function () {
                            if (config.hideAfter) {
                                if (timer) {
                                    clearTimeout(timer);
                                }
                                timer = setTimeout(function () {
                                    snackbar.hide();
                                }, config.hideAfter);
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
