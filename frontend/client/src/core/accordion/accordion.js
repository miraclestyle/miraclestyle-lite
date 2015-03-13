(function () {
    'use strict';
    angular.module('app')
        .factory('$transition', ['$q', '$timeout', '$rootScope', function ($q, $timeout, $rootScope) {

            var $transition = function (element, trigger, options) {
                options = options || {};
                var deferred = $q.defer();
                var endEventName = $transition[options.animation ? 'animationEndEventName' : 'transitionEndEventName'];

                var transitionEndHandler = function (event) {
                    $rootScope.$apply(function () {
                        element.unbind(endEventName, transitionEndHandler);
                        deferred.resolve(element);
                    });
                };

                if (endEventName) {
                    element.bind(endEventName, transitionEndHandler);
                }

                // Wrap in a timeout to allow the browser time to update the DOM before the transition is to occur
                $timeout(function () {
                    if (angular.isString(trigger)) {
                        element.addClass(trigger);
                    } else if (angular.isFunction(trigger)) {
                        trigger(element);
                    } else if (angular.isObject(trigger)) {
                        element.css(trigger);
                    }
                    //If browser does not support transitions, instantly resolve
                    if (!endEventName) {
                        deferred.resolve(element);
                    }
                });

                // Add our custom cancel function to the promise that is returned
                // We can call this if we are about to run a new transition, which we know will prevent this transition from ending,
                // i.e. it will therefore never raise a transitionEnd event for that transition
                deferred.promise.cancel = function () {
                    if (endEventName) {
                        element.unbind(endEventName, transitionEndHandler);
                    }
                    deferred.reject('Transition cancelled');
                };

                return deferred.promise;
            };

            // Work out the name of the transitionEnd event
            var transElement = document.createElement('trans');
            var transitionEndEventNames = {
                'WebkitTransition': 'webkitTransitionEnd',
                'MozTransition': 'transitionend',
                'OTransition': 'oTransitionEnd',
                'transition': 'transitionend'
            };
            var animationEndEventNames = {
                'WebkitTransition': 'webkitAnimationEnd',
                'MozTransition': 'animationend',
                'OTransition': 'oAnimationEnd',
                'transition': 'animationend'
            };

            function findEndEventName(endEventNames) {
                for (var name in endEventNames) {
                    if (transElement.style[name] !== undefined) {
                        return endEventNames[name];
                    }
                }
            }
            $transition.transitionEndEventName = findEndEventName(transitionEndEventNames);
            $transition.animationEndEventName = findEndEventName(animationEndEventNames);
            return $transition;
        }]).directive('collapse', ['$transition', function ($transition) {

            return {
                link: function (scope, element, attrs) {

                    var initialAnimSkip = true;
                    var currentTransition;

                    function doTransition(change) {
                        var newTransition = $transition(element, change);
                        if (currentTransition) {
                            currentTransition.cancel();
                        }
                        currentTransition = newTransition;
                        newTransition.then(newTransitionDone, newTransitionDone);
                        return newTransition;

                        function newTransitionDone() {
                            // Make sure it's this transition, otherwise, leave it alone.
                            if (currentTransition === newTransition) {
                                currentTransition = undefined;
                            }
                        }
                    }

                    function expand() {
                        if (initialAnimSkip) {
                            initialAnimSkip = false;
                            expandDone();
                        } else {
                            element.removeClass('collapse').addClass('collapsing');
                            doTransition({
                                height: element[0].scrollHeight + 'px'
                            }).then(expandDone);
                        }
                    }

                    function expandDone() {
                        element.removeClass('collapsing');
                        element.addClass('collapse in');
                        element.css({
                            height: 'auto'
                        });
                    }

                    function collapse() {
                        if (initialAnimSkip) {
                            initialAnimSkip = false;
                            collapseDone();
                            element.css({
                                height: 0
                            });
                        } else {
                            // CSS transitions don't work with height: auto, so we have to manually change the height to a specific value
                            element.css({
                                height: element[0].scrollHeight + 'px'
                            });
                            //trigger reflow so a browser realizes that height was updated from auto to a specific value
                            var x = element[0].offsetWidth;

                            element.removeClass('collapse in').addClass('collapsing');

                            doTransition({
                                height: 0
                            }).then(collapseDone);
                        }
                    }

                    function collapseDone() {
                        element.removeClass('collapsing');
                        element.addClass('collapse');
                    }

                    scope.$watch(attrs.collapse, function (shouldCollapse) {
                        if (shouldCollapse) {
                            collapse();
                        } else {
                            expand();
                        }
                    });
                }
            };
        }]).constant('accordionConfig', {
            closeOthers: true
        })

    .controller('AccordionController', ['$scope', '$attrs', 'accordionConfig', function ($scope, $attrs, accordionConfig) {

        // This array keeps track of the accordion groups
        this.groups = [];

        // Ensure that all the groups in this accordion are closed, unless close-others explicitly says not to
        this.closeOthers = function (openGroup) {
            var closeOthers = angular.isDefined($attrs.closeOthers) ? $scope.$eval($attrs.closeOthers) : accordionConfig.closeOthers;
            if (closeOthers) {
                angular.forEach(this.groups, function (group) {
                    if (group !== openGroup) {
                        group.isOpen = false;
                    }
                });
            }
        };

        // This is called from the accordion-group directive to add itself to the accordion
        this.addGroup = function (groupScope) {
            var that = this;
            this.groups.push(groupScope);

            groupScope.$on('$destroy', function (event) {
                that.removeGroup(groupScope);
            });
        };

        // This is called from the accordion-group directive when to remove itself
        this.removeGroup = function (group) {
            var index = this.groups.indexOf(group);
            if (index !== -1) {
                this.groups.splice(index, 1);
            }
        };

    }])

    // The accordion directive simply sets up the directive controller
    // and adds an accordion CSS class to itself element.
    .directive('accordion', function () {
        return {
            restrict: 'EA',
            controller: 'AccordionController',
            transclude: true,
            replace: false,
            templateUrl: 'core/accordion/accordion.html'
        };
    })

    // The accordion-group directive indicates a block of html that will expand and collapse in an accordion
    .directive('accordionGroup', function () {
        return {
            require: '^accordion', // We need this directive to be inside an accordion
            restrict: 'EA',
            transclude: true, // It transcludes the contents of the directive into the template
            replace: true, // The element containing the directive will be replaced with the template
            templateUrl: 'core/accordion/accordion_group.html',
            scope: {
                heading: '@', // Interpolate the heading attribute onto this scope
                isOpen: '=?',
                isDisabled: '=?',
                action: '=?'

            },
            controller: function () {
                this.setHeading = function (element) {
                    this.heading = element;
                };
            },
            link: function (scope, element, attrs, accordionCtrl) {
                accordionCtrl.addGroup(scope);

                if (scope.action) {
                    scope.toggleOpen = function () {
                        scope.action();
                    };
                    return;
                }

                scope.$watch('isOpen', function (value) {
                    if (value) {
                        accordionCtrl.closeOthers(scope);
                    }
                });

                scope.toggleOpen = function () {
                    if (!scope.isDisabled) {
                        scope.isOpen = !scope.isOpen;
                    }
                };
            }
        };
    })

    // Use accordion-heading below an accordion-group to provide a heading containing HTML
    // <accordion-group>
    //   <accordion-heading>Heading containing HTML - <img src="..."></accordion-heading>
    // </accordion-group>
    .directive('accordionHeading', function () {
        return {
            restrict: 'EA',
            transclude: true, // Grab the contents to be used as the heading
            template: '', // In effect remove this element!
            replace: true,
            require: '^accordionGroup',
            link: function (scope, element, attr, accordionGroupCtrl, transclude) {
                // Pass the heading to the accordion-group controller
                // so that it can be transcluded into the right place in the template
                // [The second parameter to transclude causes the elements to be cloned so that they work in ng-repeat]
                accordionGroupCtrl.setHeading(transclude(scope, function () {}));
            }
        };
    })

    // Use in the accordion-group template to indicate where you want the heading to be transcluded
    // You must provide the property on the accordion-group controller that will hold the transcluded element
    // <div class="accordion-group">
    //   <div class="accordion-heading" ><a ... accordion-transclude="heading">...</a></div>
    //   ...
    // </div>
    .directive('accordionTransclude', function () {
        return {
            require: '^accordionGroup',
            link: function (scope, element, attr, controller) {
                scope.$watch(function () {
                    return controller[attr.accordionTransclude];
                }, function (heading) {
                    if (heading) {
                        element.html('');
                        element.append(heading);
                    }
                });
            }
        };
    }).directive('bindHtmlUnsafe', function () {
        return function (scope, element, attr) {
            element.addClass('ng-binding').data('$binding', attr.bindHtmlUnsafe);
            scope.$watch(attr.bindHtmlUnsafe, function bindHtmlUnsafeWatchAction(value) {
                element.html(value || '');
            });
        };
    }).directive('accordionOnOpen', function ($timeout, helpers) {
        return {

            link: function (scope, element, attrs) {

                var accordions = scope.$eval(attrs.accordionOnOpen);

                if (accordions) {

                    angular.forEach(accordions.groups, function (accordion, i) {
                        scope.$watch(attrs.accordionOnOpen + '.groups[' + i + '].open', function (neww, old) {
                            var which = accordions.groups[i];
                            if (neww) {
                                scope.$broadcast('accordionOpened', which, i);
                            } else {
                                scope.$broadcast('accordionClosed', which, i);
                            }
                        });

                    });

                }

            }
        };
    }).directive('monitorAccordionFormState', function () {
            return {
                priority: -10000,
                restrict: 'A',
                require: ['^form'],
                link: function (scope, element, attrs, ctrls) {
                    var form = ctrls[0],
                        accordion = scope.$eval(attrs.monitorAccordionFormState),
                        check = function () {
                            element.find('[name]').each(function () {
                                var name = $(this).attr('name'),
                                    formElement = form[name],
                                    lastSet;
                                if (angular.isDefined(formElement)) {
                                    if (!formElement.$valid) {
                                        if (lastSet) {
                                            lastSet.open = false;
                                        }
                                        accordion.open = true;
                                        lastSet = accordion;
                                        form.$setDirty();
                                        formElement.$setViewValue(formElement.$viewValue !== undefined ? formElement.$viewValue : '');
                                        formElement.$setDirty();
                                        formElement.$setTouched();
                                        if (!scope.$$phase) {
                                            scope.$apply();
                                        }
                                    }
                                }
                            });
                        };
                    scope.$on('invalidForm', check);
                }
            };
        });

}());
