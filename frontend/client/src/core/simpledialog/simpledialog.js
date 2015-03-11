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
     * @name material.components.simpledialog
     */
    angular.module('material.components.simpledialog', ['material.core', 'material.components.backdrop'])
        .factory('mdContextualMonitor', mdContextualMonitor)
        .directive('simpleDialog', SimpleDialogDirective)
        .provider('$simpleDialog', SimpleDialogProvider);

    function mdContextualMonitor($rootElement, $mdConstant) {
        var callbacks = [],
            bound = false,
            id = 1,
            generateNextID = function () {
                id += 1;
                return id;
            },
            emptyHashery = function () {
                if (!callbacks.length) {
                    window.location.hash = '';
                    id = 1;
                }
            };
        return {
            dequeue: function (cb) {
                var index = callbacks.indexOf(cb);
                if (index !== -1) {
                    callbacks.splice(index, 1);
                }
                emptyHashery();
            },
            queue: function (cb) {
                var hashPrefix = 'context-monitor-',
                    lastHash = window.location.hash,
                    nextId = generateNextID(),
                    executeFirstInQueue = function (e) {
                        var next = callbacks.pop(),
                            execute = (next && next(e));
                        emptyHashery();
                        return execute;
                    };
                if (!bound) {
                    $rootElement.on('keyup', function (e) {
                        if (e.keyCode !== $mdConstant.KEY_CODE.ESCAPE) {
                            return;
                        }
                        executeFirstInQueue(e);
                    });
                    $(window).bind('hashchange', function () {
                        var newHash = window.location.hash,
                            isBack,
                            newHashId = parseInt(newHash.substr(hashPrefix.length + 1), 10),
                            oldHashId = parseInt(lastHash.substr(hashPrefix.length + 1), 10);
                        // Do something
                        if (isNaN(newHashId) || (!isNaN(oldHashId) && (newHashId < oldHashId))) {
                            isBack = true;
                        }
                        //At the end of the func:
                        lastHash = newHash;
                        if (isBack) {
                            executeFirstInQueue();
                        }
                    });

                    bound = true;
                }
                window.location.hash = hashPrefix + nextId;
                callbacks.push(cb);
            }
        };
    }
    mdContextualMonitor.$inject = ["$rootElement", "$mdConstant"];


    function SimpleDialogDirective($$rAF, $mdTheming) {
        return {
            restrict: 'E',
            link: function (scope, element, attr) {
                $mdTheming(element);
            }
        };
    }
    SimpleDialogDirective.$inject = ["$$rAF", "$mdTheming"];

    /**
     * @ngdoc service
     * @name $simpleDialog
     * @module material.components.simpledialog
     *
     * @description
     * `$simpleDialog` opens a dialog over the app and provides a simple promise API.
     *
     * ### Restrictions
     *
     * - The dialog is always given an isolate scope.
     * - The dialog's template must have an outer `<md-simpledialog>` element.
     *   Inside, use an `<md-content>` element for the dialog's content, and use
     *   an element with class `md-actions` for the dialog's actions.
     *
     * @usage
     * ##### HTML
     *
     * <hljs lang="html">
     * <div  ng-app="demoApp" ng-controller="EmployeeController">
     *   <md-button ng-click="showAlert()" class="md-raised md-warn">
     *     Employee Alert!
     *   </md-button>
     *   <md-button ng-click="closeAlert()" ng-disabled="!hasAlert()" class="md-raised">
     *     Close Alert
     *   </md-button>
     *   <md-button ng-click="showGreeting($event)" class="md-raised md-primary" >
     *     Greet Employee
     *   </md-button>
     * </div>
     * </hljs>
     *
     * ##### JavaScript
     *
     * <hljs lang="js">
     * (function(angular, undefined){
     *   "use strict";
     *
     *   angular
     *     .module('demoApp', ['ngMaterial'])
     *     .controller('EmployeeController', EmployeeEditor)
     *     .controller('GreetingController', GreetingController);
     *
     *   // Fictitious Employee Editor to show how to use simple and complex dialogs.
     *
     *   function EmployeeEditor($scope, $simpleDialog) {
     *     var alert;
     *
     *     $scope.showAlert = showAlert;
     *     $scope.closeAlert = closeAlert;
     *     $scope.showGreeting = showCustomGreeting;
     *
     *     $scope.hasAlert = function() { return !!alert };
     *     $scope.userName = $scope.userName || 'Bobby';
     *
     *     // Dialog #1 - Show simple alert dialog and cache
     *     // reference to dialog instance
     *
     *     function showAlert() {
     *       alert = $simpleDialog.alert()
     *         .title('Attention, ' + $scope.userName)
     *         .content('This is an example of how easy dialogs can be!')
     *         .ok('Close');
     *
     *       $simpleDialog
     *           .show( alert )
     *           .finally(function() {
     *             alert = undefined;
     *           });
     *     }
     *
     *     // Close the specified dialog instance and resolve with 'finished' flag
     *     // Normally this is not needed, just use '$simpleDialog.hide()' to close
     *     // the most recent dialog popup.
     *
     *     function closeAlert() {
     *       $simpleDialog.hide( alert, "finished" );
     *       alert = undefined;
     *     }
     *
     *     // Dialog #2 - Demonstrate more complex dialogs construction and popup.
     *
     *     function showCustomGreeting($event) {
     *         $simpleDialog.show({
     *           targetEvent: $event,
     *           template:
     *             '<md-simpledialog>' +
     *
     *             '  <md-content>Hello {{ employee }}!</md-content>' +
     *
     *             '  <div class="md-actions">' +
     *             '    <md-button ng-click="closeDialog()">' +
     *             '      Close Greeting' +
     *
     *             '    </md-button>' +
     *             '  </div>' +
     *             '</md-simpledialog>',
     *           controller: 'GreetingController',
     *           onComplete: afterShowAnimation,
     *           locals: { employee: $scope.userName }
     *         });
     *
     *         // When the 'enter' animation finishes...
     *
     *         function afterShowAnimation(scope, element, options) {
     *            // post-show code here: DOM element focus, etc.
     *         }
     *     }
     *   }
     *
     *   // Greeting controller used with the more complex 'showCustomGreeting()' custom dialog
     *
     *   function GreetingController($scope, $simpleDialog, employee) {
     *     // Assigned from construction <code>locals</code> options...
     *     $scope.employee = employee;
     *
     *     $scope.closeDialog = function() {
     *       // Easily hides most recent dialog shown...
     *       // no specific instance reference is needed.
     *       $simpleDialog.hide();
     *     };
     *   }
     *
     * })(angular);
     * </hljs>
     */

    /**
     * @ngdoc method
     * @name $simpleDialog#alert
     *
     * @description
     * Builds a preconfigured dialog with the specified message.
     *
     * @returns {obj} an `$simpleDialogPreset` with the chainable configuration methods:
     *
     * - $simpleDialogPreset#title(string) - sets title to string
     * - $simpleDialogPreset#content(string) - sets content / message to string
     * - $simpleDialogPreset#ok(string) - sets okay button text to string
     *
     */

    /**
     * @ngdoc method
     * @name $simpleDialog#confirm
     *
     * @description
     * Builds a preconfigured dialog with the specified message. You can call show and the promise returned
     * will be resolved only if the user clicks the confirm action on the dialog.
     *
     * @returns {obj} an `$simpleDialogPreset` with the chainable configuration methods:
     *
     * Additionally, it supports the following methods:
     *
     * - $simpleDialogPreset#title(string) - sets title to string
     * - $simpleDialogPreset#content(string) - sets content / message to string
     * - $simpleDialogPreset#ok(string) - sets okay button text to string
     * - $simpleDialogPreset#cancel(string) - sets cancel button text to string
     *
     */

    /**
     * @ngdoc method
     * @name $simpleDialog#show
     *
     * @description
     * Show a dialog with the specified options.
     *
     * @param {object} optionsOrPreset Either provide an `$simpleDialogPreset` returned from `alert()`,
     * `confirm()` or an options object with the following properties:
     *   - `templateUrl` - `{string=}`: The url of a template that will be used as the content
     *   of the dialog.
     *   - `template` - `{string=}`: Same as templateUrl, except this is an actual template string.
     *   - `targetEvent` - `{DOMClickEvent=}`: A click's event object. When passed in as an option,
     *     the location of the click will be used as the starting point for the opening animation
     *     of the the dialog.
     *   - `disableParentScroll` - `{boolean=}`: Whether to disable scrolling while the dialog is open.
     *     Default true.
     *   - `hasBackdrop` - `{boolean=}`: Whether there should be an opaque backdrop behind the dialog.
     *     Default true.
     *   - `clickOutsideToClose` - `{boolean=}`: Whether the user can click outside the dialog to
     *     close it. Default true.
     *     Default true.
     *   - `controller` - `{string=}`: The controller to associate with the dialog. The controller
     *     will be injected with the local `$hideDialog`, which is a function used to hide the dialog.
     *   - `locals` - `{object=}`: An object containing key/value pairs. The keys will be used as names
     *     of values to inject into the controller. For example, `locals: {three: 3}` would inject
     *     `three` into the controller, with the value 3. If `bindToController` is true, they will be
     *     copied to the controller instead.
     *   - `bindToController` - `bool`: bind the locals to the controller, instead of passing them in
     *   - `resolve` - `{object=}`: Similar to locals, except it takes promises as values, and the
     *     dialog will not open until all of the promises resolve.
     *   - `controllerAs` - `{string=}`: An alias to assign the controller to on the scope.
     *   - `parent` - `{element=}`: The element to append the dialog to. Defaults to appending
     *     to the root element of the application.
     *   - `onComplete` `{function=}`: Callback function used to announce when the show() action is
     *     finished.
     *
     * @returns {promise} A promise that can be resolved with `$simpleDialog.hide()` or
     * rejected with `mdAdialog.cancel()`.
     */

    /**
     * @ngdoc method
     * @name $simpleDialog#hide
     *
     * @description
     * Hide an existing dialog and resolve the promise returned from `$simpleDialog.show()`.
     *
     * @param {*=} response An argument for the resolved promise.
     */

    /**
     * @ngdoc method
     * @name $simpleDialog#cancel
     *
     * @description
     * Hide an existing dialog and reject the promise returned from `$simpleDialog.show()`.
     *
     * @param {*=} response An argument for the rejected promise.
     */

    function SimpleDialogProvider($$interimElementProvider) {

        var alertDialogMethods = ['title', 'content', 'ariaLabel', 'ok'];

        dialogDefaultOptions.$inject = ["$timeout", "$rootElement", "$compile", "$animate", "$mdAria", "$document", "$mdUtil", "$mdConstant", "$mdTheming", "$$rAF", "$q", "$simpleDialog", "mdContextualMonitor"];
        return $$interimElementProvider('$simpleDialog')
            .setDefaults({
                methods: ['disableParentScroll', 'hasBackdrop', 'clickOutsideToClose', 'targetEvent'],
                options: dialogDefaultOptions
            });


        /* @ngInject */
        function dialogDefaultOptions($timeout, $rootElement, $compile, $animate, $mdAria, $document,
            $mdUtil, $mdConstant, $mdTheming, $$rAF, $q, $simpleDialog, mdContextualMonitor) {
            return {
                hasBackdrop: true,
                isolateScope: true,
                onShow: onShow,
                onRemove: onRemove,
                clickOutsideToClose: true,
                targetEvent: null,
                disableParentScroll: true,
                transformTemplate: function (template) {
                    return '<div class="simple-dialog-container">' + template + '</div>';
                }
            };

            function discoverDirective(options) {
                return 'simple-dialog';
            }

            function discoverContainerClass(container, options) {}

            // On show method for dialogs
            function onShow(scope, element, options) {
                // Incase the user provides a raw dom element, always wrap it in jqLite
                options.parent = angular.element(options.parent);

                options.popInTarget = angular.element((options.targetEvent || {}).target);
                var closeButton = findCloseButton(),
                    directive = discoverDirective(options),
                    dialogEl = element.find(directive);

                configureAria(dialogEl);
                options.disableScrollInfo = [];
                if (!options.disableScroll) {
                    options.disableScroll = [];
                }
                if (options.disableParentScroll) {
                    options.disableScroll.push(options.parent);
                }
                angular.forEach(options.disableScroll, function (el) {
                    options.disableScrollInfo.push({
                        old: {
                            'overflow-y': el.css('overflow-y'),
                            'overflow-x': el.css('overflow-x')
                        },
                        element: el
                    });
                    el.css('overflow', 'hidden');
                    el.css('overflow-wrap', el.css('overflow-wrap') === 'normal' ? 'break-word' : 'normal');
                });

                if (options.hasBackdrop) {
                    options.backdrop = angular.element('<md-backdrop class="simple-dialog-backdrop" style="z-index: ' + options.zIndex + '">');
                    $mdTheming.inherit(options.backdrop, options.parent);
                    $animate.enter(options.backdrop, options.parent);
                }

                dialogEl.css('z-index', options.zIndex + 1);

                return dialogPopIn(element, options)
                    .then(function () {
                        options.rootElementKeyupCallback = function () {
                            if (options.stack.indexOf(options.interimElement) === 0) {
                                $timeout(function () {
                                    $simpleDialog.cancel('esc', options.interimElement);
                                });
                            }
                            return true;
                        };
                        mdContextualMonitor.queue(options.rootElementKeyupCallback);
                        if (options.clickOutsideToClose) {
                            options.dialogClickOutsideCallback = function (e) {
                                // Only close if we click the flex container outside the backdrop
                                if (e.target === options.backdrop[0]) {
                                    $timeout($simpleDialog.cancel);
                                }
                            };
                            options.backdrop.on('click', options.dialogClickOutsideCallback);
                        }
                        closeButton.focus();

                    });


                function findCloseButton() {
                    //If no element with class dialog-close, try to find the last
                    //button child in md-actions and assume it is a close button
                    var closeButton = element[0].querySelector('.dialog-close');
                    if (!closeButton) {
                        var actionButtons = element[0].querySelectorAll('.md-actions button');
                        closeButton = actionButtons[actionButtons.length - 1];
                    }
                    return angular.element(closeButton);
                }

            }

            // On remove function for all dialogs
            function onRemove(scope, element, options) {
                if (options.clickOutsideToClose && options.backdrop) {
                    options.backdrop.off('click', options.dialogClickOutsideCallback);
                }
                if (options.backdrop) {
                    $animate.leave(options.backdrop);
                }
                angular.forEach(options.disableScrollInfo, function (info) {
                    info.element.css(info.old);
                    info.element.css('overflow-wrap', info.element.css('overflow-wrap') === 'normal' ? 'break-word' : 'normal');
                });
                options.disableScrollInfo = [];
                $document[0].removeEventListener('scroll', options.captureScroll, true);
                mdContextualMonitor.dequeue(options.rootElementKeyupCallback);
                return dialogPopOut(element, options).then(function () {
                    options.scope.$destroy();
                    element.remove();
                    options.popInTarget && options.popInTarget.focus();
                });

            }

            /**
             * Inject ARIA-specific attributes appropriate for Dialogs
             */
            function configureAria(element) {
                element.attr({
                    'role': 'dialog'
                });

                var dialogContent = element.find('md-content');
                if (dialogContent.length === 0) {
                    dialogContent = element;
                }
                $mdAria.expectAsync(element, 'aria-label', function () {
                    var words = dialogContent.text().split(/\s+/);
                    if (words.length > 3) {
                        words = words.slice(0, 3).concat('...');
                    }
                    return words.join(' ');
                });
            }

            function dialogPopIn(container, options) {
                discoverContainerClass(container, options);
                var dialogEl = container.find(discoverDirective(options)),
                    parentElement = options.parent,
                    clickElement = options.popInTarget && options.popInTarget.length && options.popInTarget,
                    defer = $q.defer();
                parentElement.append(container);
                var promise = defer.promise,
                    nextPromise;
                nextPromise = promise.then(function () {
                    var maybeDefer = $q.defer(),
                        maybePromise = maybeDefer.promise,
                        maybePromiseOnBefore;
                    if (options.onBeforeShow) {
                        maybePromiseOnBefore = options.onBeforeShow(dialogEl, options);
                        if (maybePromiseOnBefore && maybePromiseOnBefore.then) {
                            return maybePromiseOnBefore;
                        }
                    }
                    maybeDefer.resolve();
                    return maybePromise;
                });
                defer.resolve();
                return nextPromise;
            }

            function dialogPopOut(container, options) {
                discoverContainerClass(container, options);
                var dialogEl = container.find(discoverDirective(options)),
                    parentElement = options.parent,
                    type,
                    clickElement = options.popInTarget && options.popInTarget.length && options.popInTarget;
                if (options.onBeforeHide) {
                    options.onBeforeHide(dialogEl, options);
                }
                dialogEl.addClass('transition-out').removeClass('transition-in');
                var promise = dialogTransitionEnd(dialogEl);
                promise.then(function () {
                    if (options.onAfterHide) {
                        options.onAfterHide(dialogEl, options);
                    }
                });
                return promise;
            }

            function transformToClickElement(dialogEl, clickElement) {
                if (clickElement) {
                    var clickRect = clickElement[0].getBoundingClientRect();
                    var dialogRect = dialogEl[0].getBoundingClientRect();

                    var scaleX = Math.min(0.5, clickRect.width / dialogRect.width);
                    var scaleY = Math.min(0.5, clickRect.height / dialogRect.height);

                    dialogEl.css($mdConstant.CSS.TRANSFORM, 'translate3d(' +
                        (-dialogRect.left + clickRect.left + clickRect.width / 2 - dialogRect.width / 2) + 'px,' +
                        (-dialogRect.top + clickRect.top + clickRect.height / 2 - dialogRect.height / 2) + 'px,' +
                        '0) scale(' + scaleX + ',' + scaleY + ')'
                    );
                }
            }

            function dialogTransitionEnd(dialogEl) {
                var deferred = $q.defer();
                dialogEl.on($mdConstant.CSS.TRANSITIONEND, finished);

                function finished(ev) {
                    //Make sure this transitionend didn't bubble up from a child
                    if (ev.target === dialogEl[0]) {
                        dialogEl.off($mdConstant.CSS.TRANSITIONEND, finished);
                        deferred.resolve();
                    }
                }
                return deferred.promise;
            }

        }
    }
    SimpleDialogProvider.$inject = ["$$interimElementProvider"];

})();
