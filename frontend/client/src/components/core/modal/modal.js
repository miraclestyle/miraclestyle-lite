(function () {
    'use strict';
    angular.module('app').factory('$$stackedMap', function () {
        return {
            createNew: function () {
                var stack = [];

                return {
                    add: function (key, value) {
                        stack.push({
                            key: key,
                            value: value
                        });
                    },
                    get: function (key) {
                        for (var i = 0; i < stack.length; i++) {
                            if (key == stack[i].key) {
                                return stack[i];
                            }
                        }
                    },
                    keys: function () {
                        var keys = [];
                        for (var i = 0; i < stack.length; i++) {
                            keys.push(stack[i].key);
                        }
                        return keys;
                    },
                    top: function () {
                        return stack[stack.length - 1];
                    },
                    remove: function (key) {
                        var idx = -1;
                        for (var i = 0; i < stack.length; i++) {
                            if (key == stack[i].key) {
                                idx = i;
                                break;
                            }
                        }
                        return stack.splice(idx, 1)[0];
                    },
                    removeTop: function () {
                        return stack.splice(stack.length - 1, 1)[0];
                    },
                    length: function () {
                        return stack.length;
                    }
                };
            }
        };
    })

    /**
     * A helper directive for the $modal service. It creates a backdrop element.
     */
    .directive('modalBackdrop', ['$timeout', function ($timeout) {
        return {
            restrict: 'EA',
            replace: true,
            templateUrl: 'core/modal/backdrop.html',
            link: function (scope, element, attrs) {
                scope.backdropClass = attrs.backdropClass || '';

                scope.animate = false;

                //trigger CSS transitions
                $timeout(function () {
                    scope.animate = true;
                });
            }
        };
    }])

    .directive('modalWindow', ['$modalStack', '$timeout', '$$rAF', '$mdConstant', '$q',
        function ($modalStack, $timeout, $$rAF, $mdConstant, $q) {
            return {
                restrict: 'EA',
                scope: {
                    index: '@',
                    animate: '=',
                    modalOptions: '='
                },
                replace: true,
                transclude: true,
                templateUrl: function (tElement, tAttrs) {
                    return tAttrs.templateUrl || 'core/modal/window.html';
                },
                link: function (scope, element, attrs) {
                    var clickElement = scope.modalOptions.targetEvent && scope.modalOptions.targetEvent.target;
                    element.addClass(!scope.modalOptions.fullScreen ? 'modal-medium' : ''); // attrs.windowClass
                    scope.size = attrs.size;
                    $timeout(function () {
                        // trigger CSS transitions
                        if (!scope.modalOptions.fullScreen) {
                            var modal = $(element).find('.modal-dialog'),
                                iwidth = modal.width(),
                                iheight = modal.height();
                            scope.modalOptions.resize = function () {
                                var wwidth = $(window).width(),
                                    wheight = $(window).height(),
                                    maxHeight,
                                    maxWidth,
                                    minWidth = '',
                                    minHeight = '';
                                if (iheight >= wheight) {
                                    maxHeight = wheight - 16 * 2;
                                } else {
                                    maxHeight = '';
                                    minHeight = iheight;
                                }
                                if (iwidth >= wwidth) {
                                    maxWidth = wwidth - 16 * 2;
                                } else {
                                    maxWidth = '';
                                    minWidth = iwidth;
                                }
                                modal.css('max-height', maxHeight);
                                modal.css('max-width', maxWidth);
                                modal.css('min-height', minHeight);
                                modal.css('min-width', minWidth);
                            };
                            scope.modalOptions.resize();
                            $(window).on('resize', scope.modalOptions.resize);
                        }
                        if (clickElement) {
                            var clickRect = clickElement.getBoundingClientRect();
                            var modalRect = element[0].getBoundingClientRect();
                            var scaleX = Math.min(0.5, clickRect.width / modalRect.width);
                            var scaleY = Math.min(0.5, clickRect.height / modalRect.height);

                            element.css($mdConstant.CSS.TRANSFORM, 'translate3d(' +
                                (-modalRect.left + clickRect.left + clickRect.width / 2 - modalRect.width / 2) + 'px,' +
                                (-modalRect.top + clickRect.top + clickRect.height / 2 - modalRect.height / 2) + 'px,' +
                                '0) scale(' + scaleX + ',' + scaleY + ')'
                            );
                        } else {
                            if (scope.modalOptions.inDirection) {
                                element.css($mdConstant.CSS.TRANSFORM, 'translate3d(' + (scope.modalOptions.inDirection === 'right' ? '' : '-') + '100%, 0px, 0px)');
                            }
                        }

                        if (scope.modalOptions.inDirection) {
                            element.addClass('visible');
                        }

                        if (scope.modalOptions.inDirection && !clickElement) {
                            var cb = function () {
                                element.addClass('transition-in-' + scope.modalOptions.inDirection)
                                    .css($mdConstant.CSS.TRANSFORM, '');
                            };
                        } else {
                            var cb = function () {
                                element.addClass('visible');
                                element.addClass('transition-in')
                                    .css($mdConstant.CSS.TRANSFORM, '');
                            };
                        }
                        var deferred = $q.defer();
                        deferred.promise.then(function () {
                            if (!element[0].querySelectorAll('[autofocus]').length) {
                                element[0].focus();
                            }
                            $(window).triggerHandler('modal.visible');
                        });

                        element.on($mdConstant.CSS.TRANSITIONEND, function finished(ev) {
                            if (ev.target === element[0]) {
                                element.off($mdConstant.CSS.TRANSITIONEND, finished);
                                deferred.resolve();
                            }
                        });

                        setTimeout(function () {
                            $$rAF(cb);
                        }, 100);

                        $(window).triggerHandler('modal.open');

                    });

                    scope.close = function (evt) {
                        var modal = $modalStack.getTop();
                        if (modal && modal.value.backdrop && modal.value.backdrop != 'static' && (evt.target === evt.currentTarget)) {
                            evt.preventDefault();
                            evt.stopPropagation();
                            $modalStack.dismiss(modal.key, 'backdrop click');
                        }
                    };
                }
            };
        }
    ])

    .directive('modalTransclude', function () {
        return {
            link: function ($scope, $element, $attrs, controller, $transclude) {
                $transclude($scope.$parent, function (clone) {
                    $element.empty();
                    $element.append(clone);
                });
            }
        };
    })

    .factory('$modalStack', ['$transition', '$timeout', '$document', '$compile', '$rootScope', '$$stackedMap', 'mdContextualMonitor',
        '$mdConstant',
        function ($transition, $timeout, $document, $compile, $rootScope, $$stackedMap, mdContextualMonitor, $mdConstant) {

            var OPENED_MODAL_CLASS = 'modal-open';
            var backdropDomEl, backdropScope;
            var openedWindows = $$stackedMap.createNew();
            var $modalStack = {};

            function backdropIndex() {
                var topBackdropIndex = -1;
                var opened = openedWindows.keys();
                for (var i = 0; i < opened.length; i++) {
                    if (openedWindows.get(opened[i]).value.backdrop) {
                        topBackdropIndex = i;
                    }
                }
                return topBackdropIndex;
            }

            $rootScope.$watch(backdropIndex, function (newBackdropIndex) {
                if (backdropScope) {
                    backdropScope.index = newBackdropIndex;
                }
            });

            function removeModalWindow(modalInstance) {

                var body = $document.find('body').eq(0);
                var modalWindow = openedWindows.get(modalInstance).value;

                //clean up the stack
                openedWindows.remove(modalInstance);

                //remove window DOM element
                backdropDomEl.removeClass('opaque');
                removeAfterAnimate(modalWindow.modalDomEl, modalWindow.modalScope, 300, function () {
                    modalWindow.modalScope.$destroy();
                    body.toggleClass(OPENED_MODAL_CLASS, openedWindows.length() > 0);
                    checkRemoveBackdrop();
                    $(window).triggerHandler('modal.close');
                });
            }

            function checkRemoveBackdrop() {
                //remove backdrop if no longer needed
                if (backdropDomEl && backdropIndex() == -1) {
                    var backdropScopeRef = backdropScope;
                    removeAfterAnimateOld(backdropDomEl, backdropScope, 150, function () {
                        backdropScopeRef.$destroy();
                        backdropScopeRef = null;
                    });

                    backdropDomEl = undefined;
                    backdropScope = undefined;
                }
            }

            function removeAfterAnimateOld(domEl, scope, emulateTime, done) {
                // Closing animation
                scope.animate = false;

                var transitionEndEventName = $transition.transitionEndEventName;
                if (transitionEndEventName) {
                    // transition out
                    var timeout = $timeout(afterAnimating, emulateTime);

                    domEl.bind(transitionEndEventName, function () {
                        $timeout.cancel(timeout);
                        afterAnimating();
                        scope.$apply();
                    });
                } else {
                    // Ensure this call is async
                    $timeout(afterAnimating);
                }

                function afterAnimating() {
                    if (afterAnimating.done) {
                        return;
                    }
                    afterAnimating.done = true;

                    domEl.remove();
                    if (done) {
                        done();
                    }
                }
            }

            function removeAfterAnimate(domEl, scope, emulateTime, done) {
                // Closing animation
                var modalEl = domEl,
                    clickElement = scope.modalOptions.targetEvent && scope.modalOptions.targetEvent.target;

                if (!clickElement && scope.modalOptions.inDirection) {
                    modalEl.addClass('transition-out-' + scope.modalOptions.outDirection).removeClass('transition-in-' + scope.modalOptions.inDirection)
                        .css($mdConstant.CSS.TRANSFORM, 'translate3d(' + (scope.modalOptions.outDirection === 'right' ? '' : '-') + '100%, 0px, 0px)');
                } else {
                    modalEl.addClass('transition-out').removeClass('transition-in');
                    if (clickElement) {
                        var clickRect = clickElement.getBoundingClientRect();
                        var modalRect = modalEl[0].getBoundingClientRect();
                        var scaleX = Math.min(0.5, clickRect.width / modalRect.width);
                        var scaleY = Math.min(0.5, clickRect.height / modalRect.height);

                        modalEl.css($mdConstant.CSS.TRANSFORM, 'translate3d(' +
                            (-modalRect.left + clickRect.left + clickRect.width / 2 - modalRect.width / 2) + 'px,' +
                            (-modalRect.top + clickRect.top + clickRect.height / 2 - modalRect.height / 2) + 'px,' +
                            '0) scale(' + scaleX + ',' + scaleY + ')'
                        );
                    }
                }

                modalEl.on($mdConstant.CSS.TRANSITIONEND, function afterAnimating(ev) {
                    if (ev.target !== modalEl[0]) {
                        return;
                    }
                    domEl.remove();
                    if (done) {
                        done();
                    }
                });
            }

            $modalStack.open = function (modalInstance, modal) {

                openedWindows.add(modalInstance, {
                    deferred: modal.deferred,
                    modalScope: modal.scope,
                    backdrop: modal.backdrop
                });

                modal.scope.modalOptions = {
                    inDirection: modal.inDirection,
                    outDirection: modal.outDirection,
                    targetEvent: modal.targetEvent,
                    fullScreen: modal.fullScreen
                };

                var body = $document.find('body').eq(0),
                    currBackdropIndex = backdropIndex();

                if (currBackdropIndex >= 0 && !backdropDomEl) {
                    backdropScope = $rootScope.$new(true);
                    backdropScope.index = currBackdropIndex;
                    var angularBackgroundDomEl = angular.element('<div modal-backdrop></div>');
                    angularBackgroundDomEl.attr('backdrop-class', modal.backdropClass);
                    backdropDomEl = $compile(angularBackgroundDomEl)(backdropScope);
                    body.append(backdropDomEl);
                }

                if (!modal.fullScreen) {
                    backdropDomEl.addClass('opaque');
                }

                var angularDomEl = angular.element('<div modal-window></div>');

                angularDomEl.attr({
                    'template-url': modal.windowTemplateUrl,
                    'window-class': modal.windowClass,
                    'size': modal.size,
                    'index': openedWindows.length() - 1,
                    'modal-options': 'modalOptions',
                    'animate': 'animate',
                    'exiting': 'exiting'
                }).html(modal.content);

                var modalDomEl = $compile(angularDomEl)(modal.scope);
                openedWindows.top().value.modalDomEl = modalDomEl;
                body.append(modalDomEl);
                body.addClass(OPENED_MODAL_CLASS);

                var esc = function (e) {
                    if (e) {
                        e.preventDefault();
                    }
                    $rootScope.$apply(function () {
                        modalInstance.withEscape = true;
                        $modalStack.dismiss(modalInstance, 'escape key press');
                    });
                    return true;
                };
                modalInstance.esc = esc;
                mdContextualMonitor.queue(esc);

            };

            $modalStack.close = function (modalInstance, result) {
                var modalWindow = openedWindows.get(modalInstance);
                if (modalWindow) {
                    modalWindow.value.deferred.resolve(result);
                    removeModalWindow(modalInstance);
                }
            };

            $modalStack.dismiss = function (modalInstance, reason) {
                var modalWindow = openedWindows.get(modalInstance);
                if (!modalInstance.withEscape) {
                    mdContextualMonitor.dequeue(modalInstance.esc);
                    if (modalWindow.value.modalScope.modalOptions.resize) {
                        $(window).off('resize', modalWindow.value.modalScope.modalOptions.resize);
                    }
                }
                if (modalWindow) {
                    modalWindow.value.deferred.reject(reason);
                    removeModalWindow(modalInstance);
                }
            };

            $modalStack.dismissAll = function (reason) {
                var topModal = this.getTop();
                while (topModal) {
                    this.dismiss(topModal.key, reason);
                    topModal = this.getTop();
                }
            };

            $modalStack.getTop = function () {
                return openedWindows.top();
            };

            return $modalStack;
        }
    ])

    .provider('$modal', function () {

        var $modalProvider = {
            options: {
                backdrop: true, //can be also false or 'static'
                inDirection: 'right',
                outDirection: 'right',
                fullScreen: true
            },
            $get: ['$injector', '$rootScope', '$q', '$http', '$templateCache', '$controller', '$modalStack',
                function ($injector, $rootScope, $q, $http, $templateCache, $controller, $modalStack) {

                    var $modal = {};

                    function getTemplatePromise(options) {
                        return options.template ? $q.when(options.template) :
                            $http.get(angular.isFunction(options.templateUrl) ? (options.templateUrl)() : options.templateUrl, {
                                cache: $templateCache
                            }).then(function (result) {
                                return result.data;
                            });
                    }

                    function getResolvePromises(resolves) {
                        var promisesArr = [];
                        angular.forEach(resolves, function (value) {
                            if (angular.isFunction(value) || angular.isArray(value)) {
                                promisesArr.push($q.when($injector.invoke(value)));
                            }
                        });
                        return promisesArr;
                    }

                    $modal.open = function (modalOptions) {

                        var modalResultDeferred = $q.defer();
                        var modalOpenedDeferred = $q.defer();

                        //prepare an instance of a modal to be injected into controllers and returned to a caller
                        var modalInstance = {
                            result: modalResultDeferred.promise,
                            opened: modalOpenedDeferred.promise,
                            close: function (result) {
                                $modalStack.close(modalInstance, result);
                            },
                            dismiss: function (reason) {
                                $modalStack.dismiss(modalInstance, reason);
                            }
                        };

                        //merge and clean up options
                        modalOptions = angular.extend({}, $modalProvider.options, modalOptions);
                        modalOptions.resolve = modalOptions.resolve || {};

                        //verify options
                        if (!modalOptions.template && !modalOptions.templateUrl) {
                            throw new Error('One of template or templateUrl options is required.');
                        }

                        var templateAndResolvePromise =
                            $q.all([getTemplatePromise(modalOptions)].concat(getResolvePromises(modalOptions.resolve)));


                        templateAndResolvePromise.then(function resolveSuccess(tplAndVars) {

                            var modalScope = (modalOptions.scope || $rootScope).$new();
                            modalScope.$close = modalInstance.close;
                            modalScope.$dismiss = modalInstance.dismiss;

                            var ctrlInstance, ctrlLocals = {};
                            var resolveIter = 1;

                            //controllers
                            if (modalOptions.controller) {
                                ctrlLocals.$scope = modalScope;
                                ctrlLocals.$modalInstance = modalInstance;
                                angular.forEach(modalOptions.resolve, function (value, key) {
                                    ctrlLocals[key] = tplAndVars[resolveIter++];
                                });

                                ctrlInstance = $controller(modalOptions.controller, ctrlLocals);
                                if (modalOptions.controllerAs) {
                                    modalScope[modalOptions.controllerAs] = ctrlInstance;
                                }
                            }

                            $modalStack.open(modalInstance, {
                                scope: modalScope,
                                deferred: modalResultDeferred,
                                content: tplAndVars[0],
                                backdrop: modalOptions.backdrop,
                                backdropClass: modalOptions.backdropClass,
                                windowClass: modalOptions.windowClass,
                                windowTemplateUrl: modalOptions.windowTemplateUrl,
                                size: modalOptions.size,
                                inDirection: modalOptions.inDirection,
                                outDirection: modalOptions.outDirection,
                                fullScreen: modalOptions.fullScreen,
                                targetEvent: modalOptions.targetEvent
                            });

                        }, function resolveError(reason) {
                            modalResultDeferred.reject(reason);
                        });

                        templateAndResolvePromise.then(function () {
                            modalOpenedDeferred.resolve(true);
                        }, function () {
                            modalOpenedDeferred.reject(false);
                        });

                        return modalInstance;
                    };

                    return $modal;
                }
            ]
        };

        return $modalProvider;
    }).directive('fitInModal', function () {
        return {
            link: function (scope, element, attrs) {
                var time,
                    fn = function () {
                        if (time) {
                            clearTimeout(time);
                        }
                        time = setTimeout(function () {
                            var modal = $(element).parents('.modal:first'),
                                modalDialog = modal.find('.modal-dialog:first'),
                                height = (modal.hasClass('modal-medium') ? modalDialog.height() : $(window).height());
                            modalDialog.find('.fixed-height, .min-height, .max-height').each(function () {
                                var newHeight = height,
                                    footer = modalDialog.find('.md-actions'),
                                    toolbar = modalDialog.find('md-toolbar'),
                                    css = 'height';
                                if (footer.length) {
                                    newHeight -= footer.outerHeight();
                                }
                                if (toolbar.length) {
                                    newHeight -= toolbar.outerHeight();
                                }
                                if ($(this).hasClass('min-height')) {
                                    css = 'min-height';
                                }
                                if ($(this).hasClass('max-height')) {
                                    css = 'max-height';
                                }
                                $(this).css(css, newHeight);
                            });
                            scope.$broadcast('modalResize');
                        }, 50);
                    };

                $(window).bind('resize modal.open', fn);
                scope.$on('$destroy', function () {
                    $(window).unbind('resize modal.open', fn);
                });
            }
        };
    }).factory('modals', function ($modal, $q, helpers) {

        var modals = {
            howToSort: function ($event) {
                return modals.alert('Grab the button to start sorting.', {
                    targetEvent: $event
                });
            },
            alert: function (message, extraConfig) {
                if (angular.isFunction(extraConfig)) {
                    extraConfig = {
                        ok: extraConfig
                    };
                }
                return this.create($.extend({
                    message: message,
                    type: 'alert'
                }, extraConfig));
            },
            confirm: function (messageOrConfig, callbackOrConfig) {
                var theConfig = {
                    message: 'Are you sure you want to do this?',
                    type: 'confirm'
                }, config;

                if (angular.isFunction(callbackOrConfig)) {
                    config = {
                        confirm: callbackOrConfig
                    };
                } else if (angular.isObject(callbackOrConfig)) {
                    config = callbackOrConfig;
                }
                if (angular.isDefined(messageOrConfig)) {
                    if (!angular.isObject(messageOrConfig)) {
                        config.message = messageOrConfig;
                    } else {
                        config = messageOrConfig;
                    }
                }
                config = helpers.alwaysObject(config);
                helpers.extendDeep(theConfig, config);
                theConfig.confirm = function () {
                    if (angular.isFunction(config.confirm)) {
                        config.confirm.call(this);
                    }

                    this.dismiss();
                };
                return this.create(theConfig, {
                    inDirection: false,
                    outDirection: false
                });
            },
            create: function (extraConfig, modalConfig) {
                var config = {
                    message: '',
                    type: 'notice'
                }, defaultModalConfig;
                helpers.extendDeep(config, extraConfig);
                defaultModalConfig = {
                    fullScreen: false,
                    targetEvent: extraConfig && extraConfig.targetEvent,
                    templateUrl: 'core/misc/' + config.type + '.html',
                    controller: function ($scope) {
                        var callback = (angular.isFunction(extraConfig) ? extraConfig : (extraConfig.ok ? extraConfig.ok : null));
                        config.dismiss = function () {
                            if (callback) {
                                callback.call(this);
                            }
                            $scope.$close();
                        };

                        if (!angular.isObject(extraConfig)) {
                            extraConfig = {};
                        }
                        $scope.config = config;
                    }
                };
                $.extend(defaultModalConfig, modalConfig);
                return $modal.open(defaultModalConfig);
            }
        };
        return modals;
    });

}());
