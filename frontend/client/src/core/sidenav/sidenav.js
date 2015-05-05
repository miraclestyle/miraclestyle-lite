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
     * @name material.components.sidenav
     *
     * @description
     * A Sidenav QP component.
     */
    angular.module('material.components.sidenav', [
            'material.core',
            'material.components.backdrop'
        ])
        .factory('$mdSidenav', SidenavService)
        .directive('mdSidenav', SidenavDirective)
        .controller('$mdSidenavController', SidenavController);


    /**
     * @private
     * @ngdoc service
     * @name $mdSidenav
     * @module material.components.sidenav
     *
     * @description
     * `$mdSidenav` makes it easy to interact with multiple sidenavs
     * in an app.
     *
     * @usage
     * <hljs lang="js">
     * // Toggle the given sidenav
     * $mdSidenav(componentId).toggle();
     * </hljs>
     * <hljs lang="js">
     * // Open the given sidenav
     * $mdSidenav(componentId).open();
     * </hljs>
     * <hljs lang="js">
     * // Close the given sidenav
     * $mdSidenav(componentId).close();
     * </hljs>
     * <hljs lang="js">
     * // Exposes whether given sidenav is set to be open
     * $mdSidenav(componentId).isOpen();
     * </hljs>
     * <hljs lang="js">
     * // Exposes whether given sidenav is locked open
     * // If this is true, the sidenav will be open regardless of isOpen()
     * $mdSidenav(componentId).isLockedOpen();
     * </hljs>
     */
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

    /**
     * @ngdoc directive
     * @name mdSidenav
     * @module material.components.sidenav
     * @restrict E
     *
     * @description
     *
     * A Sidenav component that can be opened and closed programatically.
     *
     * By default, upon opening it will slide out on top of the main content area.
     *
     * @usage
     * <hljs lang="html">
     * <div layout="row" ng-controller="MyController">
     *   <md-sidenav md-component-id="left" class="md-sidenav-left">
     *     Left Nav!
     *   </md-sidenav>
     *
     *   <md-content>
     *     Center Content
     *     <md-button ng-click="openLeftMenu()">
     *       Open Left Menu
     *     </md-button>
     *   </md-content>
     *
     *   <md-sidenav md-component-id="right"
     *     md-is-locked-open="$media('min-width: 333px')"
     *     class="md-sidenav-right">
     *     Right Nav!
     *   </md-sidenav>
     * </div>
     * </hljs>
     *
     * <hljs lang="js">
     * var app = angular.module('myApp', ['ngMaterial']);
     * app.controller('MyController', function($scope, $mdSidenav) {
     *   $scope.openLeftMenu = function() {
     *     $mdSidenav('left').toggle();
     *   };
     * });
     * </hljs>
     *
     * @param {expression=} md-is-open A model bound to whether the sidenav is opened.
     * @param {string=} md-component-id componentId to use with $mdSidenav service.
     * @param {expression=} md-is-locked-open When this expression evalutes to true,
     * the sidenav 'locks open': it falls into the content's flow instead
     * of appearing over it. This overrides the `is-open` attribute.
     *
     * A $media() function is exposed to the is-locked-open attribute, which
     * can be given a media query or one of the `sm`, `gt-sm`, `md`, `gt-md`, `lg` or `gt-lg` presets.
     * Examples:
     *
     *   - `<md-sidenav md-is-locked-open="shouldLockOpen"></md-sidenav>`
     *   - `<md-sidenav md-is-locked-open="$media('min-width: 1000px')"></md-sidenav>`
     *   - `<md-sidenav md-is-locked-open="$media('sm')"></md-sidenav>` (locks open on small screens)
     */
    function SidenavDirective($timeout, $animate, $parse, $mdMedia, $mdConstant, $compile, $mdTheming, $q, $document, mdContextualMonitor) {
        return {
            restrict: 'E',
            scope: {
                isOpen: '=?mdIsOpen'
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
            var nothing = true;

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
            $mdTheming.inherit(backdrop, element);

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
                }
            };

            resize();

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
                }, backdropComplete = function () {
                    // If we opened, and haven't closed again before the animation finished
                    if (!scope.isOpen) {
                        backdrop.remove();
                    }
                };
                if (isOpen) {
                    element.removeClass('invisible out');
                    backdrop.removeClass('out');
                    promises.push($animate.addClass(backdrop, 'in').then(backdropComplete));
                    promises.push($animate.addClass(element, 'in').then(complete));
                } else {
                    element.removeClass('in');
                    backdrop.removeClass('in');
                    promises.push($animate.addClass(backdrop, 'out').then(backdropComplete));
                    promises.push($animate.addClass(element, 'out').then(complete));
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
    SidenavDirective.$inject = ["$timeout", "$animate", "$parse", "$mdMedia", "$mdConstant", "$compile", "$mdTheming", "$q", "$document", "mdContextualMonitor"];

    /*
     * @private
     * @ngdoc controller
     * @name SidenavController
     * @module material.components.sidenav
     *
     */
    function SidenavController($scope, $element, $attrs, $mdComponentRegistry, $q) {

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

        self.destroy = $mdComponentRegistry.register(self, $attrs.mdComponentId);
    }
    SidenavController.$inject = ["$scope", "$element", "$attrs", "$mdComponentRegistry", "$q"];



})();