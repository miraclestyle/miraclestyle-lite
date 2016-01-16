(function () {
    'use strict';

    angular.module('material.components.sidenav', [
            'material.core'
        ])
        .factory('$mdSidenav', SidenavService)
        .directive('mdSidenav', SidenavDirective)
        .controller('$mdSidenavController', SidenavController)
        .run(ng(function (helpers, $mdSidenav, $timeout, $q) {
            if (!helpers.sideNav) {
                helpers.sideNav = {};
            }
            helpers.sideNav.setup = function (menu, id, notRipplable) {
                if (!notRipplable) {
                    notRipplable = [];
                }
                id = id + _.uniqueId();
                menu.id = id;
                menu.notRipplable = notRipplable;
                menu.toggling = false;
                menu.close = function () {
                    return menu.toggle(undefined, 'close');
                };
                menu.open = function () {
                    return menu.toggle(undefined, 'open');
                };
                menu.get = function () {
                    return $mdSidenav(menu.id);
                };
                menu.toggle = function ($event, dowhat) {
                    var it = menu.get(),
                        check = false,
                        defer = $q.defer(),
                        promise = defer.promise,
                        target;
                    if (menu.toggling) {
                        defer.resolve();
                        return promise;
                    }
                    if ($event && $event.target) {
                        target = $($event.target);
                        angular.forEach(menu.notRipplable, function (skip) {
                            if (target.is(skip) || target.parent().is(skip)) {
                                check = true;
                            }
                        });
                        if (check) {
                            defer.resolve();
                            return promise;
                        }
                    }
                    menu.toggling = true;
                    $timeout(function () {
                        it[dowhat || (it.isOpen() ? 'close' : 'open')]().then(function () {
                            menu.toggling = false;
                            defer.resolve();
                        });
                    });

                    return promise;
                };
            };
        }));

    function SidenavService($mdComponentRegistry, $q) {
        return function (handle) {
            var errorMsg = "SideNav '" + handle + "' is not available!";

            // Lookup the controller instance for the specified sidNav instance
            var instance = $mdComponentRegistry.get(handle);
            if (!instance) {
                $mdComponentRegistry.notFoundError(handle);
            }

            return {
                isOpen: function () {
                    return instance && instance.isOpen();
                },
                isLockedOpen: function () {
                    return instance && instance.isLockedOpen();
                },
                toggle: function () {
                    return instance ? instance.toggle() : $q.reject(errorMsg);
                },
                open: function () {
                    return instance ? instance.open() : $q.reject(errorMsg);
                },
                close: function () {
                    return instance ? instance.close() : $q.reject(errorMsg);
                }
            };
        };
    }
    SidenavService.$inject = ["$mdComponentRegistry", "$q"];

    function SidenavDirective($timeout, $animateCss, $parse, $mdMedia, $mdConstant, $compile, $q, $document, mdContextualMonitor) {
        return {
            restrict: 'E',
            scope: {
                isOpen: '=?mdIsOpen',
                componentID: '=?mdComponentId',
                stateChanged: '=?mdStateChanged'
            },
            controller: '$mdSidenavController',
            compile: function (element) {
                element.addClass('md-closed slide drawer out invisible');
                element.attr('tabIndex', '-1');
                return postLink;
            }
        };

        /**
         * Directive Post Link function...
         */
        function postLink(scope, element, attr, sidenavCtrl) {
            var triggeringElement = null;
            var promise = $q.when(true);
            var working = false;
            var nothing = !scope.isOpen;

            var isLockedOpenParsed = $parse(attr.mdIsLockedOpen);
            var isLocked = function () {
                return isLockedOpenParsed(scope.$parent, {
                    $media: $mdMedia
                });
            };
            var backdrop = $compile(
                '<md-backdrop class="md-sidenav-backdrop md-opaque fade">'
            )(scope);

            element.on('$destroy', sidenavCtrl.destroy);

            var initialWidth = element.css('width');
            var resize = function () {
                var tolerate = $(window).width() - 56;
                if (tolerate > initialWidth) {
                    element.css({
                        width: '',
                        'min-width': ''
                    });
                    return;
                }
                if (element.width() > tolerate) {
                    element.css({
                        width: tolerate,
                        'min-width': tolerate
                    });
                } else {
                    element.css({
                        width: '',
                        'min-width': ''
                    });
                }
            };

            resize();

            resize = _.throttle(resize, 100);

            $(window).bind('resize', resize);

            scope.$watch(isLocked, updateIsLocked);
            scope.$watch('isOpen', updateIsOpen);
            scope.$on('$destroy', function () {
                $(window).off('resize', resize);
            });


            // Publish special accessor for the Controller instance
            sidenavCtrl.$toggleOpen = toggleOpen;

            /**
             * Toggle the DOM classes to indicate `locked`
             * @param isLocked
             */
            function updateIsLocked(isLocked, oldValue) {
                scope.isLockedOpen = isLocked;
                if (isLocked === oldValue) {
                    element.toggleClass('md-locked-open', !!isLocked);
                } else {
                    $animate[isLocked ? 'addClass' : 'removeClass'](element, 'md-locked-open');
                }
                backdrop.toggleClass('md-locked-open', !!isLocked);
            }

            /**
             * Toggle the SideNav view and attach/detach listeners
             * @param isOpen
             */
            function updateIsOpen(isOpen) {
                if (nothing) {
                    nothing = false;
                    return;
                }
                var parent = element.parent(),
                    promises = [];
                backdrop[isOpen ? 'on' : 'off']('click', function (ev) {
                    var that = this;
                    $timeout(function () {
                        close.apply(that, ev);
                    });
                });
                mdContextualMonitor[isOpen ? 'queue' : 'dequeue'](onKeyDown);
                if (isOpen) {
                    // Capture upon opening..
                    triggeringElement = $document[0].activeElement;
                }
                element.before(backdrop);
                var complete = function () {
                        // If we opened, and haven't closed again before the animation finished
                        if (scope.isOpen) {
                            element.focus();
                        }
                        working = false;
                        if (scope.stateChanged) {
                            scope.stateChanged(scope.isOpen);
                        }
                    },
                    backdropComplete = function () {
                        // If we opened, and haven't closed again before the animation finished
                        if (!scope.isOpen) {
                            backdrop.remove();
                        }
                    };
                if (isOpen) {
                    element.removeClass('invisible out');
                    backdrop.removeClass('out');
                    promises.push($animateCss(backdrop, {addClass: 'in'}).start().done(backdropComplete));
                    promises.push($animateCss(element, {addClass: 'in'}).start().done(complete));
                } else {
                    element.removeClass('in');
                    backdrop.removeClass('in');
                    promises.push($animateCss(backdrop, {addClass: 'out'}).start().done(backdropComplete));
                    promises.push($animateCss(element, {addClass: 'out'}).start().done(complete));
                }
                promise = $q.all(promises);
                return promise;
            }

            /**
             * Toggle the sideNav view and publish a promise to be resolved when
             * the view animation finishes.
             *
             * @param isOpen
             * @returns {*}
             */
            function toggleOpen(isOpen) {
                if (scope.isOpen == isOpen || working) {

                    return $q.when(true);

                } else {
                    working = true;
                    var deferred = $q.defer();

                    // Toggle value to force an async `updateIsOpen()` to run
                    scope.isOpen = isOpen;

                    $timeout(function () {

                        // When the current `updateIsOpen()` animation finishes
                        promise.then(function (result) {

                            if (!scope.isOpen) {
                                // reset focus to originating element (if available) upon close
                                triggeringElement && triggeringElement.focus();
                                triggeringElement = null;
                            }

                            if (isOpen) {
                                resize();
                            }

                            deferred.resolve(result);
                        });

                    }, 0, false);

                    return deferred.promise;
                }
            }

            /**
             * Auto-close sideNav when the `escape` key is pressed.
             * @param evt
             */
            function onKeyDown(ev) {
                $timeout(function () {
                    close(ev);
                });
                return true;
            }

            /**
             * With backdrop `clicks` or `escape` key-press, immediately
             * apply the CSS close transition... Then notify the controller
             * to close() and perform its own actions.
             */
            function close(ev) {
                if (ev) {
                    ev.preventDefault();
                    ev.stopPropagation();
                }
                return sidenavCtrl.close();
            }

        }
    }
    SidenavDirective.$inject = ["$timeout", "$animateCss", "$parse", "$mdMedia", "$mdConstant", "$compile", "$q", "$document", "mdContextualMonitor"];

    /*
     * @private
     * @ngdoc controller
     * @name SidenavController
     * @module material.components.sidenav
     *
     */
    function SidenavController($scope, $element, $attrs, $mdComponentRegistry, $q, $parse) {

        var self = this;

        // Use Default internal method until overridden by directive postLink

        self.$toggleOpen = function () {
            return $q.when($scope.isOpen);
        };
        self.isOpen = function () {
            return !!$scope.isOpen;
        };
        self.isLockedOpen = function () {
            return !!$scope.isLockedOpen;
        };
        self.open = function () {
            return self.$toggleOpen(true);
        };
        self.close = function () {
            return self.$toggleOpen(false);
        };
        self.toggle = function () {
            return self.$toggleOpen(!$scope.isOpen);
        };
        self.destroy = $mdComponentRegistry.register(self, $scope.componentID || $attrs.mdComponentId);
    }
    SidenavController.$inject = ["$scope", "$element", "$attrs", "$mdComponentRegistry", "$q", "$parse"];

}());
