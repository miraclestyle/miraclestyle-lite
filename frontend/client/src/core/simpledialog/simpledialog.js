(function () {
    'use strict';

    angular.module('material.components.simpledialog', ['material.core'])
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
                if (!callbacks.length && window.location.hash.length) {
                    window.location.hash = '';
                    id = 1;
                }
            },
            executeFirstInQueue = function (e) {
                var next = callbacks.pop(),
                    execute = (next && next(e));
                if (!execute && next) {
                    callbacks.push(next);
                }
                emptyHashery();
                return execute;
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
                    nextId = generateNextID();
                if (!bound) {
                    $rootElement.on('keyup', function (e) {
                        if (e.keyCode !== $mdConstant.KEY_CODE.ESCAPE) {
                            return;
                        }
                        if (!executeFirstInQueue(e)) {
                            e.preventDefault();
                        }
                    });
                    $(window).bind('hashchange', function (e) {
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
                            if (!executeFirstInQueue()) {
                                e.preventDefault();
                            }
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


    function SimpleDialogDirective($$rAF) {
        return {
            restrict: 'E'
        };
    }
    SimpleDialogDirective.$inject = ["$$rAF"];

    function SimpleDialogProvider($$interimElementProvider) {

        var alertDialogMethods = ['title', 'content', 'ariaLabel', 'ok'];

        dialogDefaultOptions.$inject = ["$timeout", "$rootElement", "$compile", "$animate", "$mdAria", "$document", "$mdUtil", "$mdConstant", "$$rAF", "$q", "$simpleDialog", "mdContextualMonitor"];
        return $$interimElementProvider('$simpleDialog')
            .setDefaults({
                methods: ['disableParentScroll', 'hasBackdrop', 'clickOutsideToClose', 'popFrom'],
                options: dialogDefaultOptions
            });


        /* @ngInject */
        function dialogDefaultOptions($timeout, $rootElement, $compile, $animate, $mdAria, $document,
            $mdUtil, $mdConstant, $$rAF, $q, $simpleDialog, mdContextualMonitor) {
            return {
                hasBackdrop: true,
                isolateScope: true,
                onShow: onShow,
                onRemove: onRemove,
                clickOutsideToClose: true,
                popFrom: null,
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

                options.popInTarget = angular.element(options.popFrom);
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
                var promise = dialogTransitionEnd(dialogEl);
                promise.then(function () {
                    if (options.onAfterHide) {
                        options.onAfterHide(dialogEl, options);
                    }
                });
                dialogEl.removeClass('transition-in').addClass('transition-out');
                setTimeout(function () {
                    dialogEl.addClass('opacity-out');
                }, 50);
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

                function finished(ev) {
                    //Make sure this transitionend didn't bubble up from a child
                    if (ev.target === dialogEl[0]) {
                        dialogEl.off($mdConstant.CSS.TRANSITIONEND, finished);
                        deferred.resolve();
                    }
                }
                dialogEl.on($mdConstant.CSS.TRANSITIONEND, finished);
                return deferred.promise;
            }

        }
    }
    SimpleDialogProvider.$inject = ["$$interimElementProvider"];

})();
