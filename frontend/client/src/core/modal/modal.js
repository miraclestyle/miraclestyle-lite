(function () {
    'use strict';

    var getClickElement = function (options) {
            var clickElement = options.popFrom;
            return (clickElement ? $(clickElement) : clickElement);
        },
        maybeFindTarget = function (ev) {
            if (!ev) {
                return;
            }
            if (ev.target) {
                var target = $(ev.target);
                if (!target.attr('ng-click')) {
                    target = target.parents('[ng-click]:first');
                }
                if (target.length) {
                    return target;
                }
                return null;
            }
        },
        hidePrevModal = function (element) {
            //element.prev().css('visibility', 'hidden').prev().css('visibility', 'hidden');
        },
        showPrevModal = function (element) {
            //element.prev().css('visibility', 'visible').prev().css('visibility', 'visible');
        },
        getPositionOverClickElement = function (clickElement, element) {
            var clickRect = clickElement[0].getBoundingClientRect(),
                modalRect = element[0].getBoundingClientRect(),

                initial_width = clickElement.width(),
                initial_height = clickElement.height(),
                final_width = element.width(),
                final_height = element.height(),

                width_divider = final_width / initial_width,
                initial_width_scale = 1 / width_divider,

                height_divider = final_height / initial_height,
                initial_height_scale = 1 / height_divider,

                left = (-modalRect.left + clickRect.left + clickRect.width / 2 - modalRect.width / 2),
                top = (-modalRect.top + clickRect.top + clickRect.height / 2 - modalRect.height / 2);

            return {
                top: top,
                left: left,
                scale: {
                    x: initial_width_scale,
                    y: initial_height_scale
                }
            };

        };

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
                        var i;
                        for (i = 0; i < stack.length; i++) {
                            if (key === stack[i].key) {
                                return stack[i];
                            }
                        }
                    },
                    keys: function () {
                        var keys = [],
                            i;
                        for (i = 0; i < stack.length; i++) {
                            keys.push(stack[i].key);
                        }
                        return keys;
                    },
                    top: function () {
                        return stack[stack.length - 1];
                    },
                    remove: function (key) {
                        var idx = -1,
                            i;
                        for (i = 0; i < stack.length; i++) {
                            if (key === stack[i].key) {
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
    }).directive('modalBackdrop', ['$timeout', '$animateCss', function ($timeout, $animateCss) {
        return {
            restrict: 'EA',
            replace: true,
            templateUrl: 'core/modal/backdrop.html',
            link: function (scope, element, attrs) {
                scope.backdropClass = attrs.backdropClass || '';
                $timeout(function () {
                    $animateCss(element, {
                        addClass: 'in'
                    }).start();
                }, 0, false);
            }
        };
    }]).directive('modalWindow', ['$modalStack', '$timeout', '$$rAF', '$mdConstant', '$q', '$animate', '$animateCss', 'animationGenerator', '$rootScope',
        function ($modalStack, $timeout, $$rAF, $mdConstant, $q, $animate, $animateCss, animationGenerator, $rootScope) {
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
                    //$rootScope.disableUI(true);
                    var clickElement = getClickElement(scope.modalOptions),
                        ready;
                    element.addClass(!scope.modalOptions.fullScreen ? 'modal-medium' : ''); // add class for confirmation dialog
                    if (attrs.windowClass) {
                        element.addClass(attrs.windowClass);
                    }
                    scope.size = attrs.size;
                    scope.$isRendered = true;
                    // Observe function will be called on next digest cycle after compilation, ensuring that the DOM is ready.
                    // In order to use this way of finding whether DOM is ready, we need to observe a scope property used in modal's template.
                    ready = function () {
                        var where = scope.modalOptions.inDirection,
                            isSlide = (where && !clickElement),
                            isFromClick = clickElement,
                            isFade = (!isSlide && !isFromClick),
                            isConfirmation = !scope.modalOptions.fullScreen,
                            cb,
                            modal,
                            spec,
                            iwidth,
                            iheight,
                            animator,
                            end;
                        if (isSlide) {
                            cb = function () {
                                element.addClass(where + ' slide drawer visible');
                                return $animateCss(element, {
                                    addClass: 'in'
                                });
                            };
                        } else if (isConfirmation) {
                            modal = element.find('.modal-dialog');
                            iwidth = modal.width();
                            iheight = modal.height();
                            scope.modalOptions.resize = _.throttle(function () {
                                var wwidth = $(window).width() - 40 * 2,
                                    wheight = $(window).height() - 24 * 2,
                                    maxHeight,
                                    maxWidth,
                                    cwidth = modal.width(),
                                    cheight = modal.height(),
                                    overHeight = iheight >= wheight,
                                    overWidth = iwidth >= wwidth;
                                if (overHeight || (cheight < wheight && overHeight)) {
                                    maxHeight = wheight;
                                } else {
                                    maxHeight = '';
                                }
                                if (overWidth || (cwidth < wwidth && overWidth)) {
                                    maxWidth = wwidth;
                                } else {
                                    maxWidth = '';
                                }
                                modal.css('max-height', maxHeight);
                                modal.css('max-width', maxWidth);
                            }, 100);
                            scope.modalOptions.resize();
                            $(window).on('resize', scope.modalOptions.resize);
                        }

                        if (clickElement) {
                            spec = getPositionOverClickElement(clickElement, element);
                            animator = animationGenerator.single('pop-in',
                                '0% {top: ' + spec.top + 'px; left: ' + spec.left + 'px; ' + $mdConstant.RAW_CSS.TRANSFORM + ': scale(' + spec.scale.x + ', ' + spec.scale.y + '); }' +
                                '1% { opacity:1; }' +
                                '75% { top: 0px; left: 0px;}' +
                                '100% { top: 0px; left: 0px; ' + $mdConstant.RAW_CSS.TRANSFORM + ': scale(1, 1);opacity:1;}');
                            cb = function () {
                                $$rAF(function () {
                                    clickElement.css('opacity', 0); // separate frame for opacity
                                });
                                element.addClass('pop').data('animator', animator);
                                return $animateCss(element, {
                                    addClass: animator.className
                                });
                            };
                        } else if (isFade) {
                            cb = function () {
                                element.addClass('fade');
                                return $animateCss(element, {addClass: 'in'});
                            };
                        }

                        end = function () {
                            element.addClass('visible rendered');
                            $(window).triggerHandler('modal.visible', [element]);
                            scope.modalOptions.opened = true;
                            scope.$emit('modalOpened');
                            scope.$broadcast('modalOpened');
                            scope.$apply();
                            //$rootScope.disableUI(false);
                            if (scope.modalOptions.fullScreen) {
                                hidePrevModal(element);
                            }
                        };

                        $(window).triggerHandler('modal.open', [element]);

                        cb().start().done(end);
                    };
                    attrs.$observe('modalRender', function (value) {
                        if (value === 'true') {
                            $timeout(ready, 50, false);
                        }
                    });
                    scope.backdropClose = function ($event) {
                        if (scope.modalOptions.cantCloseWithBackdrop) {
                            return;
                        }
                        if ($event.target === $event.currentTarget) {
                            scope.$parent.close();
                        }
                    };
                }
            };
        }
    ]).directive('modalTransclude', function () {
        return {
            link: function ($scope, $element, $attrs, controller, $transclude) {
                $transclude($scope.$parent, function (clone) {
                    $element.empty();
                    $element.append(clone);
                });
            }
        };
    }).factory('$modalStack', ['$timeout', '$document', '$compile', '$rootScope', '$$stackedMap', 'mdContextualMonitor',
        '$mdConstant', '$q', 'animationGenerator', '$animateCss', '$$rAF',
        function ($timeout, $document, $compile, $rootScope, $$stackedMap, mdContextualMonitor, $mdConstant, $q, animationGenerator, $animateCss, $$rAF) {

            var OPENED_MODAL_CLASS = 'modal-open',
                openedWindows = $$stackedMap.createNew(),
                $modalStack = {};

            function backdropIndex() {
                return openedWindows.length() - 1;
            }

            function removeAfterAnimate(domEl, scope, done) {
                var clickElement = getClickElement(scope.modalOptions),
                    spec,
                    demise,
                    animator,
                    inclass = 'in',
                    outclass = 'out',
                    animation,
                    popin = domEl.data('animator');

                if (scope.modalOptions.fullScreen) {
                    showPrevModal(domEl);
                }

                if (clickElement && popin) {
                    spec = getPositionOverClickElement(clickElement, domEl);
                    animator = animationGenerator.single('pop-out',
                        '0% { opacity:1;top: 0px; left: 0px; ' + $mdConstant.RAW_CSS.TRANSFORM + ': scale(1, 1);}' +
                        '75% { top: 0px; left: 0px;}' +
                        '100% { opacity:1;top: ' + spec.top + 'px; left: ' + spec.left + 'px; ' + $mdConstant.RAW_CSS.TRANSFORM + ': scale(' + spec.scale.x + ', ' + spec.scale.y + '); }');

                    outclass = animator.className;
                    inclass = popin.className;
                }


                animation = $animateCss(domEl, {
                    removeClass: inclass,
                    addClass: outclass
                }).start();

                demise = function (e) {
                    domEl.remove();
                    if (done) {
                        done();
                    }
                    if (clickElement) {
                        clickElement.css('opacity', 1);
                    }

                    domEl = undefined;

                    if (popin) {
                        popin.destroy();
                    }

                    if (animator) {
                        animator.destroy();
                    }
                };

                animation.done(demise); // this might never fire sometimes, but fix is to remove dom after n miliseconds if it doesn't
            }

            function removeModalWindow(modalInstance, defer) {

                var body = $document.find('body').eq(0),
                    modalWindow = openedWindows.get(modalInstance).value,
                    backdropDomEl = modalWindow.backdropDomEl,
                    backdropScope = modalWindow.backdropScope;

                //clean up the stack
                openedWindows.remove(modalInstance);

                //remove window DOM element
                $animateCss(backdropDomEl, {
                    removeClass: 'in',
                    addClass: 'out'
                }).start().done(function () {
                    backdropDomEl.remove();
                    backdropScope.$destroy();
                    modalWindow.backdropScope = undefined;
                    modalWindow.backdropDomEl = undefined;
                });

                removeAfterAnimate(modalWindow.modalDomEl, modalWindow.modalScope, function () {
                    modalWindow.modalScope.$destroy();
                    body.toggleClass(OPENED_MODAL_CLASS, openedWindows.length() > 0);
                    $rootScope.overlays = openedWindows.length();
                    $(window).triggerHandler('modal.close');
                    defer.resolve();
                });
            }

            $modalStack.open = function (modalInstance, modal) {

                var backdropDomEl,
                    backdropScope,
                    body,
                    config = {
                        deferred: modal.deferred,
                        modalScope: modal.scope,
                        backdrop: modal.backdrop
                    },
                    currBackdropIndex,
                    angularBackgroundDomEl,
                    modalDomEl,
                    angularDomEl;

                openedWindows.add(modalInstance, config);

                modal.scope.modalOptions = {
                    inDirection: modal.inDirection,
                    outDirection: modal.outDirection,
                    cantCloseWithBackdrop: (angular.isUndefined(modal.cantCloseWithBackdrop) ? modal.fullScreen : modal.cantCloseWithBackdrop),
                    popFrom: modal.popFrom,
                    fullScreen: modal.fullScreen,
                    noEscape: modal.noEscape,
                    opened: false
                };

                body = $document.find('body').eq(0);
                currBackdropIndex = backdropIndex();

                backdropScope = $rootScope.$new(true);
                backdropScope.index = currBackdropIndex;
                angularBackgroundDomEl = angular.element('<div class="opaque" modal-backdrop></div>');
                angularBackgroundDomEl.attr('backdrop-class', modal.backdropClass);
                backdropDomEl = $compile(angularBackgroundDomEl)(backdropScope);
                body.append(backdropDomEl);

                config.backdropDomEl = backdropDomEl;
                config.backdropScope = backdropScope;

                angularDomEl = angular.element('<div modal-window></div>');

                angularDomEl.attr({
                    'template-url': modal.windowTemplateUrl,
                    'window-class': modal.windowClass,
                    size: modal.size,
                    index: openedWindows.length() - 1,
                    'modal-options': 'modalOptions',
                    animate: 'animate',
                    exiting: 'exiting'
                }).html(modal.content);

                modalDomEl = $compile(angularDomEl)(modal.scope);
                openedWindows.top().value.modalDomEl = modalDomEl;
                body.append(modalDomEl);
                body.addClass(OPENED_MODAL_CLASS);
                $rootScope.overlays = openedWindows.length();
                modal.scope.modalOptions.overlay = $rootScope.overlays;

                if (!modal.noEscape) {
                    modalInstance.esc = function (e) {
                        var modalWindow = openedWindows.get(modalInstance);
                        if (e) {
                            e.preventDefault();
                        }
                        if (modalWindow && modalWindow.value && modalWindow.value.modalScope && modalWindow.value.modalScope._close_) {
                            return modalWindow.value.modalScope._close_();
                        }

                        $rootScope.$apply(function () {
                            if (modalWindow && modalWindow.value && modalWindow.value.modalScope) {
                                return modalWindow.value.modalScope.close();
                            }
                            $modalStack.dismiss(modalInstance, 'escape key press');
                        });

                        return true;
                    };
                    mdContextualMonitor.queue(modalInstance.esc);
                }

            };

            $modalStack._dequeue = function (modalWindow, modalInstance) {

                if (modalWindow && modalWindow.value) {
                    if (!modalWindow.value.modalScope.modalOptions.noEscape) {
                        mdContextualMonitor.dequeue(modalInstance.esc);
                    }
                    if (modalWindow.value.modalScope.modalOptions.resize) {
                        $(window).off('resize', modalWindow.value.modalScope.modalOptions.resize);
                    }
                }
            };

            $modalStack.close = function (modalInstance, result, what) {
                if (!what) {
                    what = 'resolve';
                }
                var modalWindow = openedWindows.get(modalInstance),
                    defer = $q.defer();
                $modalStack._dequeue(modalWindow, modalInstance);
                if (modalWindow) {
                    modalWindow.value.deferred[what](result);
                    removeModalWindow(modalInstance, defer);
                } else {
                    defer.resolve();
                }
                return defer.promise;
            };

            $modalStack.dismiss = function (modalInstance, reason) {
                return $modalStack.close(modalInstance, reason, 'reject');
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
    ]).provider('$modal', function () {

        var $modalProvider = {
            options: {
                backdrop: false,
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
                                return $modalStack.close(modalInstance, result);
                            },
                            dismiss: function (reason) {
                                return $modalStack.dismiss(modalInstance, reason);
                            }
                        };

                        //merge and clean up options
                        modalOptions = $.extend({}, $modalProvider.options, modalOptions);
                        modalOptions.resolve = modalOptions.resolve || {};

                        //verify options
                        if (!modalOptions.template && !modalOptions.templateUrl) {
                            throw new Error('One of template or templateUrl options is required.');
                        }

                        var templateAndResolvePromise = $q.all([getTemplatePromise(modalOptions)].concat(getResolvePromises(modalOptions.resolve)));


                        templateAndResolvePromise.then(function resolveSuccess(tplAndVars) {

                            var modalScope = (modalOptions.scope || $rootScope).$new();
                            modalScope.$close = modalInstance.close;
                            modalScope.close = modalScope.$close;
                            modalScope.$dismiss = modalInstance.dismiss;
                            modalScope.$state = {
                                completed: false,
                                errored: false,
                                using: false,
                                isCompleted: function () {
                                    return modalScope.$state.completed || modalScope.$state.using === false;
                                },
                                complete: function () {
                                    modalScope.$state.completed = true;
                                    modalScope.$broadcast('modalStateComplete');
                                },
                                instant: function (callback, failure) {
                                    return this.promise(function () {
                                        var defer = $q.defer();
                                        setTimeout(function () {
                                            defer.resolve();
                                        }, 100);
                                        return defer.promise;
                                    }, callback, failure);
                                },
                                promise: function (promise, callback, failure) {
                                    modalScope.$state.using = true;
                                    if (!failure) {
                                        failure = function () {
                                            modalScope.close();
                                        };
                                    }
                                    var execute = function () {
                                        if (modalScope.$state.completed) {
                                            return; // never call already completed
                                        }
                                        if (angular.isFunction(promise)) {
                                            promise = promise();
                                        }
                                        if (angular.isArray(promise)) {
                                            promise = $q.all(promise);
                                        }
                                        return promise.then(function (response) {
                                            var maybePromise = callback.call(modalScope, modalScope, response);
                                            if (maybePromise && maybePromise.then) {
                                                return maybePromise.then(modalScope.$state.complete, failure);
                                            }
                                            return modalScope.$state.complete();
                                        }, failure);
                                    };
                                    if (angular.isFunction(promise)) {
                                        modalScope.$state.ready = execute;
                                    } else {
                                        return execute();
                                    }
                                }
                            };
                            modalScope.$on('modalOpened', function (e) {
                                if (modalScope.$state.ready) {
                                    modalScope.$state.ready();
                                }
                            });

                            var ctrlInstance, ctrlLocals = {};
                            var resolveIter = 1;

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
                                cantCloseWithBackdrop: modalOptions.cantCloseWithBackdrop,
                                size: modalOptions.size,
                                inDirection: modalOptions.inDirection,
                                outDirection: modalOptions.outDirection,
                                fullScreen: modalOptions.fullScreen,
                                popFrom: modalOptions.popFrom,
                                noEscape: modalOptions.noEscape
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
                    fn,
                    rawFn = function (e) {
                        var modal = $(element).parents('.modal:first'),
                            measure,
                            rendered = modal.hasClass('rendered');
                        if (time) {
                            clearTimeout(time);
                        }
                        measure = function () {
                            var modalDialog = modal.find('.modal-dialog:first'),
                                height = (modal.hasClass('modal-medium') ? (parseInt((modalDialog.css('max-height').indexOf('%') === -1 ? modalDialog.css('max-height') : 0), 10) || modalDialog.height()) : $(window).height());

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
                        };
                        if (rendered) {
                            time = setTimeout(measure, 50);
                        } else {
                            measure();
                        }
                    };

                fn = _.throttle(rawFn, 100);

                $(window).bind('resize modal.open', fn);
                scope.$on('$destroy', function () {
                    $(window).unbind('resize modal.open', fn);
                });
                scope.$watch('$state.completed', function watchStateCompleted(newValue, oldValue) {
                    if (newValue === true && newValue !== oldValue) {
                        rawFn();
                    }
                });
            }
        };
    }).factory('modals', ng(function ($modal, $q, helpers, GLOBAL_CONFIG) {

        var modals = {
            alert: function (key, callbackOrConfig, messageOrConfig) {
                return modals.confirm(key, callbackOrConfig, messageOrConfig, true);
            },
            confirm: function (key, callbackOrConfig, messageOrConfig, alert) {
                var theConfig = {
                        message: key + ' missing config, see core/config/config.js'
                    },
                    config;

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
                helpers.extendDeep(theConfig, config, GLOBAL_CONFIG.modals[!alert ? 'confirmations' : 'alerts'][key]);
                theConfig.noSecondary = alert;
                theConfig.confirm = function () {
                    var that = this;
                    if (config.noAutoDismiss) {
                        return config.confirm.call(that);
                    }
                    if (angular.isFunction(config.confirm)) {
                        config.confirm.call(that);
                    }
                    this.dismiss().then(function () {}); // run callback immidiately
                };
                return this.create(theConfig, theConfig.modal);
            },
            create: function (extraConfig, modalConfig) {
                var config = {
                        message: ''
                    },
                    defaultModalConfig;
                helpers.extendDeep(config, extraConfig);
                defaultModalConfig = {
                    fullScreen: false,
                    inDirection: false,
                    outDirection: false,
                    cantCloseWithBackdrop: true,
                    templateUrl: 'core/misc/confirm.html',
                    controller: ng(function ($scope) {
                        var callback = (angular.isFunction(extraConfig) ? extraConfig : (extraConfig.ok || null));
                        config.dismiss = function () {
                            var close = $scope.$close();
                            close.then(function () {
                                if (callback) {
                                    callback.call($scope);
                                }
                            });
                            return close;
                        };

                        if (!angular.isObject(extraConfig)) {
                            extraConfig = {};
                        }

                        if (config.message && !config.messages) {
                            config.messages = [config.message];
                        }

                        $scope.config = config;
                        $.extend($scope, config.scope);
                        config.scope = undefined;
                    })
                };
                $.extend(defaultModalConfig, modalConfig);
                return $modal.open(defaultModalConfig);
            }
        };
        if (GLOBAL_CONFIG.debug) {
            window._modals = modals;
        }
        return modals;
    })).directive('modalLoading', function () {
        return {
            templateUrl: 'core/modal/loading.html'
        };
    });

}());
