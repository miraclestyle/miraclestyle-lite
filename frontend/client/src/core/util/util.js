(function () {
    'use strict';

    (function () {
        'use strict';


        angular.module('material.core', [])
            .config(MdCoreConfigure);

        function MdCoreConfigure($provide) {
            $provide.decorator('$$rAF', ["$delegate", rAFDecorator]);
        }
        MdCoreConfigure.$inject = ["$provide"];

        function rAFDecorator($delegate) {
            /**
             * Use this to throttle events that come in often.
             * The throttled function will always use the *last* invocation before the
             * coming frame.
             *
             * For example, window resize events that fire many times a second:
             * If we set to use an raf-throttled callback on window resize, then
             * our callback will only be fired once per frame, with the last resize
             * event that happened before that frame.
             *
             * @param {function} callback function to debounce
             */
            $delegate.throttle = function (cb) {
                var queueArgs, alreadyQueued, queueCb, context;
                return function debounced() {
                    queueArgs = arguments;
                    context = this;
                    queueCb = cb;
                    if (!alreadyQueued) {
                        alreadyQueued = true;
                        $delegate(function () {
                            queueCb.apply(context, queueArgs);
                            alreadyQueued = false;
                        });
                    }
                };
            };
            return $delegate;
        }

        angular.module('material.core')
            .factory('$mdConstant', MdConstantFactory);

        function MdConstantFactory($$rAF, $sniffer) {

            var webkit = /webkit/i.test($sniffer.vendorPrefix);

            function vendorProperty(name) {
                return webkit ? ('webkit' + name.charAt(0).toUpperCase() + name.substring(1)) : name;
            }

            function cssVendorProperty(name) {
                return webkit ? '-webkit-' + name : name;
            }

            return {
                KEY_CODE: {
                    ENTER: 13,
                    ESCAPE: 27,
                    SPACE: 32,
                    LEFT_ARROW: 37,
                    UP_ARROW: 38,
                    RIGHT_ARROW: 39,
                    DOWN_ARROW: 40
                },
                RAW_CSS: {
                    TRANSFORM: cssVendorProperty('transform'),
                    TRANSFORMORIGIN: cssVendorProperty('transformOrigin'),
                    TRANSITION: cssVendorProperty('transition'),
                    TRANSITION_DURATION: cssVendorProperty('transitionDuration'),
                    ANIMATION_PLAY_STATE: cssVendorProperty('animationPlayState'),
                    ANIMATION_DURATION: cssVendorProperty('animationDuration'),
                    ANIMATION_NAME: cssVendorProperty('animationName'),
                    ANIMATION_TIMING: cssVendorProperty('animationTimingFunction'),
                    ANIMATION_DIRECTION: cssVendorProperty('animationDirection')
                },
                CSS: {
                    /* Constants */
                    TRANSITIONEND: 'transitionend' + (webkit ? ' webkitTransitionEnd' : ''),
                    ANIMATIONEND: 'animationend' + (webkit ? ' webkitAnimationEnd' : ''),

                    TRANSFORM: vendorProperty('transform'),
                    TRANSFORMORIGIN: vendorProperty('transformOrigin'),
                    TRANSITION: vendorProperty('transition'),
                    TRANSITION_DURATION: vendorProperty('transitionDuration'),
                    ANIMATION_PLAY_STATE: vendorProperty('animationPlayState'),
                    ANIMATION_DURATION: vendorProperty('animationDuration'),
                    ANIMATION_NAME: vendorProperty('animationName'),
                    ANIMATION_TIMING: vendorProperty('animationTimingFunction'),
                    ANIMATION_DIRECTION: vendorProperty('animationDirection')
                },
                MEDIA: {
                    'sm': '(max-width: 600px)',
                    'gt-sm': '(min-width: 600px)',
                    'md': '(min-width: 600px) and (max-width: 960px)',
                    'gt-md': '(min-width: 960px)',
                    'lg': '(min-width: 960px) and (max-width: 1200px)',
                    'gt-lg': '(min-width: 1200px)'
                }
            };
        }
        MdConstantFactory.$inject = ["$$rAF", "$sniffer"];

    })();
    (function () {

        angular
            .module('material.core')
            .config(["$provide", function ($provide) {
                $provide.decorator('$mdUtil', ['$delegate', function ($delegate) {
                    /**
                     * Inject the iterator facade to easily support iteration and accessors
                     * @see iterator below
                     */
                    $delegate.iterator = Iterator;

                    return $delegate;
                }]);
            }]);

        /**
         * iterator is a list facade to easily support iteration and accessors
         *
         * @param items Array list which this iterator will enumerate
         * @param reloop Boolean enables iterator to consider the list as an endless reloop
         */
        function Iterator(items, reloop) {
            var trueFn = function () {
                return true;
            };

            reloop = !!reloop;
            var _items = items || [];

            // Published API
            return {
                items: getItems,
                count: count,

                inRange: inRange,
                contains: contains,
                indexOf: indexOf,
                itemAt: itemAt,

                findBy: findBy,

                add: add,
                remove: remove,

                first: first,
                last: last,
                next: angular.bind(null, findSubsequentItem, false),
                previous: angular.bind(null, findSubsequentItem, true),

                hasPrevious: hasPrevious,
                hasNext: hasNext

            };

            /**
             * Publish copy of the enumerable set
             * @returns {Array|*}
             */
            function getItems() {
                return [].concat(_items);
            }

            /**
             * Determine length of the list
             * @returns {Array.length|*|number}
             */
            function count() {
                return _items.length;
            }

            /**
             * Is the index specified valid
             * @param index
             * @returns {Array.length|*|number|boolean}
             */
            function inRange(index) {
                return _items.length && (index > -1) && (index < _items.length);
            }

            /**
             * Can the iterator proceed to the next item in the list; relative to
             * the specified item.
             *
             * @param item
             * @returns {Array.length|*|number|boolean}
             */
            function hasNext(item) {
                return item ? inRange(indexOf(item) + 1) : false;
            }

            /**
             * Can the iterator proceed to the previous item in the list; relative to
             * the specified item.
             *
             * @param item
             * @returns {Array.length|*|number|boolean}
             */
            function hasPrevious(item) {
                return item ? inRange(indexOf(item) - 1) : false;
            }

            /**
             * Get item at specified index/position
             * @param index
             * @returns {*}
             */
            function itemAt(index) {
                return inRange(index) ? _items[index] : null;
            }

            /**
             * Find all elements matching the key/value pair
             * otherwise return null
             *
             * @param val
             * @param key
             *
             * @return array
             */
            function findBy(key, val) {
                return _items.filter(function (item) {
                    return item[key] === val;
                });
            }

            /**
             * Add item to list
             * @param item
             * @param index
             * @returns {*}
             */
            function add(item, index) {
                if (!item) return -1;

                if (!angular.isNumber(index)) {
                    index = _items.length;
                }

                _items.splice(index, 0, item);

                return indexOf(item);
            }

            /**
             * Remove item from list...
             * @param item
             */
            function remove(item) {
                if (contains(item)) {
                    _items.splice(indexOf(item), 1);
                }
            }

            /**
             * Get the zero-based index of the target item
             * @param item
             * @returns {*}
             */
            function indexOf(item) {
                return _items.indexOf(item);
            }

            /**
             * Boolean existence check
             * @param item
             * @returns {boolean}
             */
            function contains(item) {
                return item && (indexOf(item) > -1);
            }

            /**
             * Return first item in the list
             * @returns {*}
             */
            function first() {
                return _items.length ? _items[0] : null;
            }

            /**
             * Return last item in the list...
             * @returns {*}
             */
            function last() {
                return _items.length ? _items[_items.length - 1] : null;
            }

            /**
             * Find the next item. If reloop is true and at the end of the list, it will
             * go back to the first item. If given ,the `validate` callback will be used
             * determine whether the next item is valid. If not valid, it will try to find the
             * next item again.
             * @param item
             * @param {optional} validate Validate function
             * @param {optional} limit Recursion limit
             * @returns {*}
             */
            function findSubsequentItem(backwards, item, validate, limit) {
                validate = validate || trueFn;

                var curIndex = indexOf(item);
                if (!inRange(curIndex)) {
                    return null;
                }

                var nextIndex = curIndex + (backwards ? -1 : 1);
                var foundItem = null;
                if (inRange(nextIndex)) {
                    foundItem = _items[nextIndex];
                } else if (reloop) {
                    foundItem = backwards ? last() : first();
                    nextIndex = indexOf(foundItem);
                }

                if ((foundItem === null) || (nextIndex === limit)) {
                    return null;
                }

                if (angular.isUndefined(limit)) {
                    limit = nextIndex;
                }

                return validate(foundItem) ? foundItem : findSubsequentItem(backwards, foundItem, validate, limit);
            }
        }

    })();

    angular.module('material.core')
        .factory('$mdMedia', mdMediaFactory);

    /**
     * Exposes a function on the '$mdMedia' service which will return true or false,
     * whether the given media query matches. Re-evaluates on resize. Allows presets
     * for 'sm', 'md', 'lg'.
     *
     * @example $mdMedia('sm') == true if device-width <= sm
     * @example $mdMedia('(min-width: 1200px)') == true if device-width >= 1200px
     * @example $mdMedia('max-width: 300px') == true if device-width <= 300px (sanitizes input, adding parens)
     */
    function mdMediaFactory($mdConstant, $rootScope, $window) {
        var queries = {};
        var results = {};

        return $mdMedia;

        function $mdMedia(query) {
            var validated = queries[query];
            if (angular.isUndefined(validated)) {
                validated = queries[query] = validate(query);
            }

            var result = results[validated];
            if (angular.isUndefined(result)) {
                result = add(validated);
            }

            return result;
        }

        function validate(query) {
            return $mdConstant.MEDIA[query] ||
                ((query.charAt(0) !== '(') ? ('(' + query + ')') : query);
        }

        function add(query) {
            var result = $window.matchMedia(query);
            result.addListener(onQueryChange);
            return (results[result.media] = !!result.matches);
        }

        function onQueryChange() {
            var query = this;
            $rootScope.$evalAsync(function () {
                results[query.media] = !!query.matches;
            });
        }

    }
    mdMediaFactory.$inject = ["$mdConstant", "$rootScope", "$window"];

    (function () {
        'use strict';

        /*
         * This var has to be outside the angular factory, otherwise when
         * there are multiple material apps on the same page, each app
         * will create its own instance of this array and the app's IDs
         * will not be unique.
         */
        var nextUniqueId = ['0', '0', '0'];

        angular.module('material.core')
            .factory('$mdUtil', ["$document", "$timeout", function ($document, $timeout) {
                var Util;

                return Util = {
                    now: window.performance ? angular.bind(window.performance, window.performance.now) : Date.now,

                    elementRect: function (element, offsetParent) {
                        var node = element[0];
                        offsetParent = offsetParent || node.offsetParent || document.body;
                        offsetParent = offsetParent[0] || offsetParent;
                        var nodeRect = node.getBoundingClientRect();
                        var parentRect = offsetParent.getBoundingClientRect();
                        return {
                            left: nodeRect.left - parentRect.left + offsetParent.scrollLeft,
                            top: nodeRect.top - parentRect.top + offsetParent.scrollTop,
                            width: nodeRect.width,
                            height: nodeRect.height
                        };
                    },

                    fakeNgModel: function () {
                        return {
                            $fake: true,
                            $setViewValue: function (value) {
                                this.$viewValue = value;
                                this.$render(value);
                                this.$viewChangeListeners.forEach(function (cb) {
                                    cb();
                                });
                            },
                            $isEmpty: function (value) {
                                return ('' + value).length === 0;
                            },
                            $parsers: [],
                            $formatters: [],
                            $viewChangeListeners: [],
                            $render: angular.noop
                        };
                    },

                    // Returns a function, that, as long as it continues to be invoked, will not
                    // be triggered. The function will be called after it stops being called for
                    // N milliseconds.
                    // @param wait Integer value of msecs to delay (since last debounce reset); default value 10 msecs
                    // @param invokeApply should the $timeout trigger $digest() dirty checking
                    debounce: function (func, wait, scope, invokeApply) {
                        var timer;

                        return function debounced() {
                            var context = scope,
                                args = Array.prototype.slice.call(arguments);

                            $timeout.cancel(timer);
                            timer = $timeout(function () {

                                timer = undefined;
                                func.apply(context, args);

                            }, wait || 10, invokeApply);
                        };
                    },

                    // Returns a function that can only be triggered every `delay` milliseconds.
                    // In other words, the function will not be called unless it has been more
                    // than `delay` milliseconds since the last call.
                    throttle: function throttle(func, delay) {
                        var recent;
                        return function throttled() {
                            var context = this;
                            var args = arguments;
                            var now = Util.now();

                            if (!recent || (now - recent > delay)) {
                                func.apply(context, args);
                                recent = now;
                            }
                        };
                    },

                    /**
                     * nextUid, from angular.js.
                     * A consistent way of creating unique IDs in angular. The ID is a sequence of alpha numeric
                     * characters such as '012ABC'. The reason why we are not using simply a number counter is that
                     * the number string gets longer over time, and it can also overflow, where as the nextId
                     * will grow much slower, it is a string, and it will never overflow.
                     *
                     * @returns an unique alpha-numeric string
                     */
                    nextUid: function () {
                        var index = nextUniqueId.length;
                        var digit;

                        while (index) {
                            index--;
                            digit = nextUniqueId[index].charCodeAt(0);
                            if (digit == 57 /*'9'*/ ) {
                                nextUniqueId[index] = 'A';
                                return nextUniqueId.join('');
                            }
                            if (digit == 90 /*'Z'*/ ) {
                                nextUniqueId[index] = '0';
                            } else {
                                nextUniqueId[index] = String.fromCharCode(digit + 1);
                                return nextUniqueId.join('');
                            }
                        }
                        nextUniqueId.unshift('0');
                        return nextUniqueId.join('');
                    },

                    // Stop watchers and events from firing on a scope without destroying it,
                    // by disconnecting it from its parent and its siblings' linked lists.
                    disconnectScope: function disconnectScope(scope) {
                        if (!scope) return;

                        // we can't destroy the root scope or a scope that has been already destroyed
                        if (scope.$root === scope) return;
                        if (scope.$$destroyed) return;

                        var parent = scope.$parent;
                        scope.$$disconnected = true;

                        // See Scope.$destroy
                        if (parent.$$childHead === scope) parent.$$childHead = scope.$$nextSibling;
                        if (parent.$$childTail === scope) parent.$$childTail = scope.$$prevSibling;
                        if (scope.$$prevSibling) scope.$$prevSibling.$$nextSibling = scope.$$nextSibling;
                        if (scope.$$nextSibling) scope.$$nextSibling.$$prevSibling = scope.$$prevSibling;

                        scope.$$nextSibling = scope.$$prevSibling = null;

                    },

                    // Undo the effects of disconnectScope above.
                    reconnectScope: function reconnectScope(scope) {
                        if (!scope) return;

                        // we can't disconnect the root node or scope already disconnected
                        if (scope.$root === scope) return;
                        if (!scope.$$disconnected) return;

                        var child = scope;

                        var parent = child.$parent;
                        child.$$disconnected = false;
                        // See Scope.$new for this logic...
                        child.$$prevSibling = parent.$$childTail;
                        if (parent.$$childHead) {
                            parent.$$childTail.$$nextSibling = child;
                            parent.$$childTail = child;
                        } else {
                            parent.$$childHead = parent.$$childTail = child;
                        }
                    },
                    /*
                     * getClosest replicates jQuery.closest() to walk up the DOM tree until it finds a matching nodeName
                     *
                     * @param el Element to start walking the DOM from
                     * @param tagName Tag name to find closest to el, such as 'form'
                     */
                    getClosest: function getClosest(el, tagName) {
                        tagName = tagName.toUpperCase();
                        do {
                            if (el.nodeName === tagName) {
                                return el;
                            }
                        } while (el = el.parentNode);
                        return null;
                    }
                };

            }]);

        /*
         * Since removing jQuery from the demos, some code that uses `element.focus()` is broken.
         *
         * We need to add `element.focus()`, because it's testable unlike `element[0].focus`.
         *
         * TODO(ajoslin): This should be added in a better place later.
         */

        angular.element.prototype.focus = angular.element.prototype.focus || function () {
            if (this.length) {
                this[0].focus();
            }
            return this;
        };
        angular.element.prototype.blur = angular.element.prototype.blur || function () {
            if (this.length) {
                this[0].blur();
            }
            return this;
        };

    })();

    (function () {
        'use strict';

        angular.module('material.core')
            .service('$mdAria', AriaService);

        function AriaService($$rAF, $log, $window) {

            return {
                expect: expect,
                expectAsync: expectAsync,
                expectWithText: expectWithText
            };

            /**
             * Check if expected attribute has been specified on the target element or child
             * @param element
             * @param attrName
             * @param {optional} defaultValue What to set the attr to if no value is found
             */
            function expect(element, attrName, defaultValue) {
                var node = element[0];

                if (!node.hasAttribute(attrName) && !childHasAttribute(node, attrName)) {

                    defaultValue = angular.isString(defaultValue) && defaultValue.trim() || '';
                    if (defaultValue.length) {
                        element.attr(attrName, defaultValue);
                    } else {
                        //$log.warn('ARIA: Attribute "', attrName, '", required for accessibility, is missing on node:', node);
                    }

                }
            }

            function expectAsync(element, attrName, defaultValueGetter) {
                // Problem: when retrieving the element's contents synchronously to find the label,
                // the text may not be defined yet in the case of a binding.
                // There is a higher chance that a binding will be defined if we wait one frame.
                $$rAF(function () {
                    expect(element, attrName, defaultValueGetter());
                });
            }

            function expectWithText(element, attrName) {
                expectAsync(element, attrName, function () {
                    return element.text().trim();
                });
            }

            function childHasAttribute(node, attrName) {
                var hasChildren = node.hasChildNodes(),
                    hasAttr = false;

                function isHidden(el) {
                    var style = el.currentStyle ? el.currentStyle : $window.getComputedStyle(el);
                    return (style.display === 'none');
                }

                if (hasChildren) {
                    var children = node.childNodes;
                    for (var i = 0; i < children.length; i++) {
                        var child = children[i];
                        if (child.nodeType === 1 && child.hasAttribute(attrName)) {
                            if (!isHidden(child)) {
                                hasAttr = true;
                            }
                        }
                    }
                }
                return hasAttr;
            }
        }
        AriaService.$inject = ["$$rAF", "$log", "$window"];
    })();

    (function () {
        'use strict';

        angular.module('material.core')
            .service('$mdCompiler', mdCompilerService);

        function mdCompilerService($q, $http, $injector, $compile, $controller, $templateCache) {
            /* jshint validthis: true */

            /*
             * @ngdoc service
             * @name $mdCompiler
             * @module material.core
             * @description
             * The $mdCompiler service is an abstraction of angular's compiler, that allows the developer
             * to easily compile an element with a templateUrl, controller, and locals.
             *
             * @usage
             * <hljs lang="js">
             * $mdCompiler.compile({
             *   templateUrl: 'modal.html',
             *   controller: 'ModalController',
             *   locals: {
             *     modal: myModalInstance;
             *   }
             * }).then(function(compileData) {
             *   compileData.element; // modal.html's template in an element
             *   compileData.link(myScope); //attach controller & scope to element
             * });
             * </hljs>
             */

            /*
             * @ngdoc method
             * @name $mdCompiler#compile
             * @description A helper to compile an HTML template/templateUrl with a given controller,
             * locals, and scope.
             * @param {object} options An options object, with the following properties:
             *
             *    - `controller` - `{(string=|function()=}` Controller fn that should be associated with
             *      newly created scope or the name of a registered controller if passed as a string.
             *    - `controllerAs` - `{string=}` A controller alias name. If present the controller will be
             *      published to scope under the `controllerAs` name.
             *    - `template` - `{string=}` An html template as a string.
             *    - `templateUrl` - `{string=}` A path to an html template.
             *    - `transformTemplate` - `{function(template)=}` A function which transforms the template after
             *      it is loaded. It will be given the template string as a parameter, and should
             *      return a a new string representing the transformed template.
             *    - `resolve` - `{Object.<string, function>=}` - An optional map of dependencies which should
             *      be injected into the controller. If any of these dependencies are promises, the compiler
             *      will wait for them all to be resolved, or if one is rejected before the controller is
             *      instantiated `compile()` will fail..
             *      * `key` - `{string}`: a name of a dependency to be injected into the controller.
             *      * `factory` - `{string|function}`: If `string` then it is an alias for a service.
             *        Otherwise if function, then it is injected and the return value is treated as the
             *        dependency. If the result is a promise, it is resolved before its value is 
             *        injected into the controller.
             *
             * @returns {object=} promise A promise, which will be resolved with a `compileData` object.
             * `compileData` has the following properties: 
             *
             *   - `element` - `{element}`: an uncompiled element matching the provided template.
             *   - `link` - `{function(scope)}`: A link function, which, when called, will compile
             *     the element and instantiate the provided controller (if given).
             *   - `locals` - `{object}`: The locals which will be passed into the controller once `link` is
             *     called. If `bindToController` is true, they will be coppied to the ctrl instead
             *   - `bindToController` - `bool`: bind the locals to the controller, instead of passing them in
             */
            this.compile = function (options) {
                var templateUrl = options.templateUrl;
                var template = options.template || '';
                var controller = options.controller;
                var controllerAs = options.controllerAs;
                var resolve = options.resolve || {};
                var locals = options.locals || {};
                var transformTemplate = options.transformTemplate || angular.identity;
                var bindToController = options.bindToController;

                // Take resolve values and invoke them.  
                // Resolves can either be a string (value: 'MyRegisteredAngularConst'),
                // or an invokable 'factory' of sorts: (value: function ValueGetter($dependency) {})
                angular.forEach(resolve, function (value, key) {
                    if (angular.isString(value)) {
                        resolve[key] = $injector.get(value);
                    } else {
                        resolve[key] = $injector.invoke(value);
                    }
                });
                //Add the locals, which are just straight values to inject
                //eg locals: { three: 3 }, will inject three into the controller
                angular.extend(resolve, locals);

                if (templateUrl) {
                    resolve.$template = $http.get(templateUrl, {
                            cache: $templateCache
                        })
                        .then(function (response) {
                            return response.data;
                        });
                } else {
                    resolve.$template = $q.when(template);
                }

                // Wait for all the resolves to finish if they are promises
                return $q.all(resolve).then(function (locals) {

                    var template = transformTemplate(locals.$template);
                    var element = angular.element('<div>').html(template.trim()).contents();
                    var linkFn = $compile(element);

                    //Return a linking function that can be used later when the element is ready
                    return {
                        locals: locals,
                        element: element,
                        link: function link(scope) {
                            locals.$scope = scope;

                            //Instantiate controller if it exists, because we have scope
                            if (controller) {
                                var ctrl = $controller(controller, locals);
                                if (bindToController) {
                                    angular.extend(ctrl, locals);
                                }
                                //See angular-route source for this logic
                                element.data('$ngControllerController', ctrl);
                                element.children().data('$ngControllerController', ctrl);

                                if (controllerAs) {
                                    scope[controllerAs] = ctrl;
                                }
                            }

                            return linkFn(scope);
                        }
                    };
                });

            };
        }
        mdCompilerService.$inject = ["$q", "$http", "$injector", "$compile", "$controller", "$templateCache"];
    })();

    (function (jQuery) {
        'use strict';
        var HANDLERS = {};

        /* The state of the current 'pointer'
         * The pointer represents the state of the current touch.
         * It contains normalized x and y coordinates from DOM events,
         * as well as other information abstracted from the DOM.
         */
         
        var pointer, lastPointer, forceSkipClickHijack = false;

        /**
         * The position of the most recent click if that click was on a label element.
         * @type {{x: number, y: number}?}
         */
        var lastLabelClickPos = null;

        // Used to attach event listeners once when multiple ng-apps are running.
        var isInitialized = false;

        angular
          .module('material.core.gestures', [ ])
          .provider('$mdGesture', MdGestureProvider)
          .factory('$$MdGestureHandler', MdGestureHandler)
          .run( attachToDocument );

        /**
           * @ngdoc service
           * @name $mdGestureProvider
           * @module material.core.gestures
           *
           * @description
           * In some scenarios on Mobile devices (without jQuery), the click events should NOT be hijacked.
           * `$mdGestureProvider` is used to configure the Gesture module to ignore or skip click hijacking on mobile
           * devices.
           *
           * <hljs lang="js">
           *   app.config(function($mdGestureProvider) {
           *
           *     // For mobile devices without jQuery loaded, do not
           *     // intercept click events during the capture phase.
           *     $mdGestureProvider.skipClickHijack();
           *
           *   });
           * </hljs>
           *
           */
        function MdGestureProvider() { }

        MdGestureProvider.prototype = {

          // Publish access to setter to configure a variable  BEFORE the
          // $mdGesture service is instantiated...
          skipClickHijack: function() {
            return forceSkipClickHijack = true;
          },

          /**
           * $get is used to build an instance of $mdGesture
           * ngInject
           */
          $get : ["$$MdGestureHandler", "$$rAF", "$timeout", function($$MdGestureHandler, $$rAF, $timeout) {
               return new MdGesture($$MdGestureHandler, $$rAF, $timeout);
          }]
        };



        /**
         * MdGesture factory construction function
         * ngInject
         */
        function MdGesture($$MdGestureHandler, $$rAF, $timeout) {
          var userAgent = navigator.userAgent || navigator.vendor || window.opera;
          var isIos = userAgent.match(/ipad|iphone|ipod/i);
          var isAndroid = userAgent.match(/android/i);
          var hasJQuery =  (typeof window.jQuery !== 'undefined') && (angular.element === window.jQuery);

          var self = {
            handler: addHandler,
            register: register,
            // On mobile w/out jQuery, we normally intercept clicks. Should we skip that?
            isHijackingClicks: (isIos || isAndroid) && !hasJQuery && !forceSkipClickHijack
          };

          if (self.isHijackingClicks) {
            var maxClickDistance = 8;
            self.handler('click', {
              options: {
                maxDistance: maxClickDistance
              },
              onEnd: checkDistanceAndEmit('click')
            });

            self.handler('focus', {
              options: {
                maxDistance: maxClickDistance
              },
              onEnd: function(ev, pointer) {
                if (pointer.distance < this.state.options.maxDistance) {
                  if (canFocus(ev.target)) {
                    this.dispatchEvent(ev, 'focus', pointer);
                    ev.target.focus();
                  }
                }

                function canFocus(element) {
                  var focusableElements = ['INPUT', 'SELECT', 'BUTTON', 'TEXTAREA', 'VIDEO', 'AUDIO'];

                  return (element.getAttribute('tabindex') != '-1') &&
                      !element.hasAttribute('DISABLED') &&
                      (element.hasAttribute('tabindex') || element.hasAttribute('href') ||
                      (focusableElements.indexOf(element.nodeName) != -1));
                }
              }
            });

            self.handler('mouseup', {
              options: {
                maxDistance: maxClickDistance
              },
              onEnd: checkDistanceAndEmit('mouseup')
            });

            self.handler('mousedown', {
              onStart: function(ev) {
                this.dispatchEvent(ev, 'mousedown');
              }
            });
          }

          function checkDistanceAndEmit(eventName) {
            return function(ev, pointer) {
              if (pointer.distance < this.state.options.maxDistance && !ev.jqueryui) {
                this.dispatchEvent(ev, eventName, pointer);
              }
            };
          }

          /*
           * Register an element to listen for a handler.
           * This allows an element to override the default options for a handler.
           * Additionally, some handlers like drag and hold only dispatch events if
           * the domEvent happens inside an element that's registered to listen for these events.
           *
           * @see GestureHandler for how overriding of default options works.
           * @example $mdGesture.register(myElement, 'drag', { minDistance: 20, horziontal: false })
           */
          function register(element, handlerName, options) {
            var handler = HANDLERS[handlerName.replace(/^\$md./, '')];
            if (!handler) {
              throw new Error('Failed to register element with handler ' + handlerName + '. ' +
              'Available handlers: ' + Object.keys(HANDLERS).join(', '));
            }
            return handler.registerElement(element, options);
          }

          /*
           * add a handler to $mdGesture. see below.
           */
          function addHandler(name, definition) {
            var handler = new $$MdGestureHandler(name);
            angular.extend(handler, definition);
            HANDLERS[name] = handler;

            return self;
          }
          if (!window.touchHelpers) {
            window.touchHelpers = {};
          }
          window.touchHelpers.getEventPoint = getEventPoint;
          window.touchHelpers.updatePointerState = updatePointerState;
          window.touchHelpers.makeStartPointer = makeStartPointer;
          window.touchHelpers.typesMatch = typesMatch;

          /*
           * Register handlers. These listen to touch/start/move events, interpret them,
           * and dispatch gesture events depending on options & conditions. These are all
           * instances of GestureHandler.
           * @see GestureHandler 
           */
          return self
            /*
             * The press handler dispatches an event on touchdown/touchend.
             * It's a simple abstraction of touch/mouse/pointer start and end.
             */
            .handler('press', {
              onStart: function (ev, pointer) {
                this.dispatchEvent(ev, '$md.pressdown');
              },
              onEnd: function (ev, pointer) {
                this.dispatchEvent(ev, '$md.pressup');
              }
            })

            /*
             * The hold handler dispatches an event if the user keeps their finger within
             * the same <maxDistance> area for <delay> ms.
             * The hold handler will only run if a parent of the touch target is registered
             * to listen for hold events through $mdGesture.register()
             */
            .handler('hold', {
              options: {
                maxDistance: 6,
                delay: 500
              },
              onCancel: function () {
                $timeout.cancel(this.state.timeout);
              },
              onStart: function (ev, pointer) {
                // For hold, require a parent to be registered with $mdGesture.register()
                // Because we prevent scroll events, this is necessary.
                if (!this.state.registeredParent) return this.cancel();

                this.state.pos = {x: pointer.x, y: pointer.y};
                this.state.timeout = $timeout(angular.bind(this, function holdDelayFn() {
                  this.dispatchEvent(ev, '$md.hold');
                  this.cancel(); //we're done!
                }), this.state.options.delay, false);
              },
              onMove: function (ev, pointer) {
                // Don't scroll while waiting for hold.
                // If we don't preventDefault touchmove events here, Android will assume we don't
                // want to listen to anymore touch events. It will start scrolling and stop sending
                // touchmove events.
                ev.preventDefault();

                // If the user moves greater than <maxDistance> pixels, stop the hold timer
                // set in onStart
                var dx = this.state.pos.x - pointer.x;
                var dy = this.state.pos.y - pointer.y;
                if (Math.sqrt(dx * dx + dy * dy) > this.options.maxDistance) {
                  this.cancel();
                }
              },
              onEnd: function () {
                this.onCancel();
              }
            })

            /*
             * The drag handler dispatches a drag event if the user holds and moves his finger greater than
             * <minDistance> px in the x or y direction, depending on options.horizontal.
             * The drag will be cancelled if the user moves his finger greater than <minDistance>*<cancelMultiplier> in
             * the perpindicular direction. Eg if the drag is horizontal and the user moves his finger <minDistance>*<cancelMultiplier>
             * pixels vertically, this handler won't consider the move part of a drag.
             */
            .handler('drag', {
              options: {
                minDistance: 6,
                horizontal: true,
                cancelMultiplier: 1.5
              },
              onStart: function (ev) {
                // For drag, require a parent to be registered with $mdGesture.register()
                if (!this.state.registeredParent) this.cancel();
              },
              onMove: function (ev, pointer) {
                var shouldStartDrag, shouldCancel;
                // Don't scroll while deciding if this touchmove qualifies as a drag event.
                // If we don't preventDefault touchmove events here, Android will assume we don't
                // want to listen to anymore touch events. It will start scrolling and stop sending
                // touchmove events.
                ev.preventDefault();

                if (!this.state.dragPointer) {
                  if (this.state.options.horizontal) {
                    shouldStartDrag = Math.abs(pointer.distanceX) > this.state.options.minDistance;
                    shouldCancel = Math.abs(pointer.distanceY) > this.state.options.minDistance * this.state.options.cancelMultiplier;
                  } else {
                    shouldStartDrag = Math.abs(pointer.distanceY) > this.state.options.minDistance;
                    shouldCancel = Math.abs(pointer.distanceX) > this.state.options.minDistance * this.state.options.cancelMultiplier;
                  }

                  if (shouldStartDrag) {
                    // Create a new pointer representing this drag, starting at this point where the drag started.
                    this.state.dragPointer = makeStartPointer(ev);
                    updatePointerState(ev, this.state.dragPointer);
                    this.dispatchEvent(ev, '$md.dragstart', this.state.dragPointer);

                  } else if (shouldCancel) {
                    this.cancel();
                  }
                } else {
                  this.dispatchDragMove(ev);
                }
              },
              // Only dispatch dragmove events every frame; any more is unnecessray
              dispatchDragMove: $$rAF.throttle(function (ev) {
                // Make sure the drag didn't stop while waiting for the next frame
                if (this.state.isRunning) {
                  updatePointerState(ev, this.state.dragPointer);
                  this.dispatchEvent(ev, '$md.drag', this.state.dragPointer);
                }
              }),
              onEnd: function (ev, pointer) {
                if (this.state.dragPointer) {
                  updatePointerState(ev, this.state.dragPointer);
                  this.dispatchEvent(ev, '$md.dragend', this.state.dragPointer);
                }
              }
            })

            /*
             * The swipe handler will dispatch a swipe event if, on the end of a touch,
             * the velocity and distance were high enough.
             * TODO: add vertical swiping with a `horizontal` option similar to the drag handler.
             */
            .handler('swipe', {
              options: {
                minVelocity: 0.65,
                minDistance: 10
              },
              onEnd: function (ev, pointer) {
                if (Math.abs(pointer.velocityX) > this.state.options.minVelocity &&
                  Math.abs(pointer.distanceX) > this.state.options.minDistance) {
                  var eventType = pointer.directionX == 'left' ? '$md.swipeleft' : '$md.swiperight';
                  this.dispatchEvent(ev, eventType);
                }
              }
            });

        }
        MdGesture.$inject = ["$$MdGestureHandler", "$$rAF", "$timeout"];

        /**
         * MdGestureHandler
         * A GestureHandler is an object which is able to dispatch custom dom events
         * based on native dom {touch,pointer,mouse}{start,move,end} events.
         *
         * A gesture will manage its lifecycle through the start,move,end, and cancel
         * functions, which are called by native dom events.
         *
         * A gesture has the concept of 'options' (eg a swipe's required velocity), which can be
         * overridden by elements registering through $mdGesture.register()
         */
        function GestureHandler (name) {
          this.name = name;
          this.state = {};
        }

        function MdGestureHandler() {
          var hasJQuery =  (typeof window.jQuery !== 'undefined') && (angular.element === window.jQuery);

          GestureHandler.prototype = {
            options: {},
            // jQuery listeners don't work with custom DOMEvents, so we have to dispatch events
            // differently when jQuery is loaded
            dispatchEvent: hasJQuery ?  jQueryDispatchEvent : nativeDispatchEvent,

            // These are overridden by the registered handler
            onStart: angular.noop,
            onMove: angular.noop,
            onEnd: angular.noop,
            onCancel: angular.noop,

            // onStart sets up a new state for the handler, which includes options from the
            // nearest registered parent element of ev.target.
            start: function (ev, pointer) {
              if (this.state.isRunning) return;
              var parentTarget = this.getNearestParent(ev.target);
              // Get the options from the nearest registered parent
              var parentTargetOptions = parentTarget && parentTarget.$mdGesture[this.name] || {};

              this.state = {
                isRunning: true,
                // Override the default options with the nearest registered parent's options
                options: angular.extend({}, this.options, parentTargetOptions),
                // Pass in the registered parent node to the state so the onStart listener can use
                registeredParent: parentTarget
              };
              this.onStart(ev, pointer);
            },
            move: function (ev, pointer) {
              if (!this.state.isRunning) return;
              this.onMove(ev, pointer);
            },
            end: function (ev, pointer) {
              if (!this.state.isRunning) return;
              this.onEnd(ev, pointer);
              this.state.isRunning = false;
            },
            cancel: function (ev, pointer) {
              this.onCancel(ev, pointer);
              this.state = {};
            },

            // Find and return the nearest parent element that has been registered to
            // listen for this handler via $mdGesture.register(element, 'handlerName').
            getNearestParent: function (node) {
              var current = node;
              while (current) {
                if ((current.$mdGesture || {})[this.name]) {
                  return current;
                }
                current = current.parentNode;
              }
              return null;
            },

            // Called from $mdGesture.register when an element reigsters itself with a handler.
            // Store the options the user gave on the DOMElement itself. These options will
            // be retrieved with getNearestParent when the handler starts.
            registerElement: function (element, options) {
              var self = this;
              element[0].$mdGesture = element[0].$mdGesture || {};
              element[0].$mdGesture[this.name] = options || {};
              element.on('$destroy', onDestroy);

              return onDestroy;

              function onDestroy() {
                delete element[0].$mdGesture[self.name];
                element.off('$destroy', onDestroy);
              }
            }
          };

          return GestureHandler;

          /*
           * Dispatch an event with jQuery
           * TODO: Make sure this sends bubbling events
           *
           * @param srcEvent the original DOM touch event that started this.
           * @param eventType the name of the custom event to send (eg 'click' or '$md.drag')
           * @param eventPointer the pointer object that matches this event.
           */
          function jQueryDispatchEvent(srcEvent, eventType, eventPointer) {
            eventPointer = eventPointer || pointer;
            var eventObj = new angular.element.Event(eventType);

            eventObj.$material = true;
            eventObj.pointer = eventPointer;
            eventObj.srcEvent = srcEvent;
            eventObj.jqueryui = srcEvent.jqueryui;

            angular.extend(eventObj, {
              clientX: eventPointer.x,
              clientY: eventPointer.y,
              screenX: eventPointer.x,
              screenY: eventPointer.y,
              pageX: eventPointer.x,
              pageY: eventPointer.y,
              ctrlKey: srcEvent.ctrlKey,
              altKey: srcEvent.altKey,
              shiftKey: srcEvent.shiftKey,
              metaKey: srcEvent.metaKey
            });
            angular.element(eventPointer.target).trigger(eventObj);
          }

          /*
           * NOTE: nativeDispatchEvent is very performance sensitive.
           * @param srcEvent the original DOM touch event that started this.
           * @param eventType the name of the custom event to send (eg 'click' or '$md.drag')
           * @param eventPointer the pointer object that matches this event.
           */
          function nativeDispatchEvent(srcEvent, eventType, eventPointer) {
            eventPointer = eventPointer || pointer;
            var eventObj;

            if (eventType === 'click' || eventType == 'mouseup' || eventType == 'mousedown' ) {
              eventObj = document.createEvent('MouseEvents');
              eventObj.initMouseEvent(
                eventType, true, true, window, srcEvent.detail,
                eventPointer.x, eventPointer.y, eventPointer.x, eventPointer.y,
                srcEvent.ctrlKey, srcEvent.altKey, srcEvent.shiftKey, srcEvent.metaKey,
                srcEvent.button, srcEvent.relatedTarget || null
              );

            } else {
              eventObj = document.createEvent('CustomEvent');
              eventObj.initCustomEvent(eventType, true, true, {});
            }
            eventObj.$material = true;
            eventObj.pointer = eventPointer;
            eventObj.srcEvent = srcEvent;
            eventObj.jqueryui = srcEvent.jqueryui;
            eventPointer.target.dispatchEvent(eventObj);
          }

        }

        /**
         * Attach Gestures: hook document and check shouldHijack clicks
         * ngInject
         */
        function attachToDocument( $mdGesture, $$MdGestureHandler ) {

          // Polyfill document.contains for IE11.
          // TODO: move to util
          document.contains || (document.contains = function (node) {
            return document.body.contains(node);
          });

          if (!isInitialized && $mdGesture.isHijackingClicks ) {
            /*
             * If hijack clicks is true, we preventDefault any click that wasn't
             * sent by ngMaterial. This is because on older Android & iOS, a false, or 'ghost',
             * click event will be sent ~400ms after a touchend event happens.
             * The only way to know if this click is real is to prevent any normal
             * click events, and add a flag to events sent by material so we know not to prevent those.
             * 
             * Two exceptions to click events that should be prevented are:
             *  - click events sent by the keyboard (eg form submit)
             *  - events that originate from an Ionic app
             */
            document.addEventListener('click'    , clickHijacker     , true);
            document.addEventListener('mouseup'  , mouseInputHijacker, true);
            document.addEventListener('mousedown', mouseInputHijacker, true);
            document.addEventListener('focus'    , mouseInputHijacker, true);

            console.log('clickHijacker');

            isInitialized = true;
          }

          function mouseInputHijacker(ev) {
            var isKeyClick = !ev.clientX && !ev.clientY;
            if (!isKeyClick && !ev.$material && !ev.isIonicTap
              && !isInputEventFromLabelClick(ev)) {
              ev.preventDefault();
              ev.stopPropagation();
            }
          }

          function clickHijacker(ev) {
            var isKeyClick = ev.clientX === 0 && ev.clientY === 0;
            if (!isKeyClick && !ev.$material && !ev.isIonicTap && !ev.jqueryui
              && !isInputEventFromLabelClick(ev)) {
              ev.preventDefault();
              ev.stopPropagation();
              lastLabelClickPos = null;
            } else {
              lastLabelClickPos = null;
              if (ev.target.tagName.toLowerCase() == 'label') {
                lastLabelClickPos = {x: ev.x, y: ev.y};
              }
            }
          }


          // Listen to all events to cover all platforms.
          var START_EVENTS = 'mousedown touchstart pointerdown';
          var MOVE_EVENTS = 'mousemove touchmove pointermove';
          var END_EVENTS = 'mouseup mouseleave touchend touchcancel pointerup pointercancel';

          angular.element(document)
            .on(START_EVENTS, gestureStart)
            .on(MOVE_EVENTS, gestureMove)
            .on(END_EVENTS, gestureEnd)
            // For testing
            .on('$$mdGestureReset', function gestureClearCache () {
              lastPointer = pointer = null;
            });

          /*
           * When a DOM event happens, run all registered gesture handlers' lifecycle
           * methods which match the DOM event.
           * Eg when a 'touchstart' event happens, runHandlers('start') will call and
           * run `handler.cancel()` and `handler.start()` on all registered handlers.
           */
          function runHandlers(handlerEvent, event) {
            var handler;
            for (var name in HANDLERS) {
              handler = HANDLERS[name];
              if( handler instanceof $$MdGestureHandler ) {

                if (handlerEvent === 'start') {
                  // Run cancel to reset any handlers' state
                  handler.cancel();
                }
                handler[handlerEvent](event, pointer);

              }
            }
          }

          /*
           * gestureStart vets if a start event is legitimate (and not part of a 'ghost click' from iOS/Android)
           * If it is legitimate, we initiate the pointer state and mark the current pointer's type
           * For example, for a touchstart event, mark the current pointer as a 'touch' pointer, so mouse events
           * won't effect it.
           */
          function gestureStart(ev) {
            // If we're already touched down, abort
            if (pointer) return;

            var now = +Date.now();

            // iOS & old android bug: after a touch event, a click event is sent 350 ms later.
            // If <400ms have passed, don't allow an event of a different type than the previous event
            if (lastPointer && !typesMatch(ev, lastPointer) && (now - lastPointer.endTime < 1500)) {
              return;
            }

            pointer = makeStartPointer(ev);

            runHandlers('start', ev);
          }
          /*
           * If a move event happens of the right type, update the pointer and run all the move handlers.
           * "of the right type": if a mousemove happens but our pointer started with a touch event, do nothing.
           */
          function gestureMove(ev) {
            if (!pointer || !typesMatch(ev, pointer)) return;

            updatePointerState(ev, pointer);
            runHandlers('move', ev);
          }
          /*
           * If an end event happens of the right type, update the pointer, run endHandlers, and save the pointer as 'lastPointer'
           */
          function gestureEnd(ev) {
            if (!pointer || !typesMatch(ev, pointer)) return;

            updatePointerState(ev, pointer);
            pointer.endTime = +Date.now();

            runHandlers('end', ev);

            lastPointer = pointer;
            pointer = null;
          }

        }
        attachToDocument.$inject = ["$mdGesture", "$$MdGestureHandler"];

        // ********************
        // Module Functions
        // ********************

        /*
         * Initiate the pointer. x, y, and the pointer's type.
         */
        function makeStartPointer(ev) {
          var point = getEventPoint(ev);
          var startPointer = {
            startTime: +Date.now(),
            target: ev.target,
            // 'p' for pointer events, 'm' for mouse, 't' for touch
            type: ev.type.charAt(0)
          };
          startPointer.startX = startPointer.x = point.pageX;
          startPointer.startY = startPointer.y = point.pageY;
          return startPointer;
        }

        /*
         * return whether the pointer's type matches the event's type.
         * Eg if a touch event happens but the pointer has a mouse type, return false.
         */
        function typesMatch(ev, pointer) {
          return ev && pointer && ev.type.charAt(0) === pointer.type;
        }

        /**
         * Gets whether the given event is an input event that was caused by clicking on an
         * associated label element.
         *
         * This is necessary because the browser will, upon clicking on a label element, fire an
         * *extra* click event on its associated input (if any). mdGesture is able to flag the label
         * click as with `$material` correctly, but not the second input click.
         *
         * In order to determine whether an input event is from a label click, we compare the (x, y) for
         * the event to the (x, y) for the most recent label click (which is cleared whenever a non-label
         * click occurs). Unfortunately, there are no event properties that tie the input and the label
         * together (such as relatedTarget).
         *
         * @param {MouseEvent} event
         * @returns {boolean}
         */
        function isInputEventFromLabelClick(event) {
          return lastLabelClickPos
              && lastLabelClickPos.x == event.x
              && lastLabelClickPos.y == event.y;
        }

        /*
         * Update the given pointer based upon the given DOMEvent.
         * Distance, velocity, direction, duration, etc
         */
        function updatePointerState(ev, pointer) {
          var point = getEventPoint(ev);
          var x = pointer.x = point.pageX;
          var y = pointer.y = point.pageY;

          pointer.distanceX = x - pointer.startX;
          pointer.distanceY = y - pointer.startY;
          pointer.distance = Math.sqrt(
            pointer.distanceX * pointer.distanceX + pointer.distanceY * pointer.distanceY
          );

          pointer.directionX = pointer.distanceX > 0 ? 'right' : pointer.distanceX < 0 ? 'left' : '';
          pointer.directionY = pointer.distanceY > 0 ? 'up' : pointer.distanceY < 0 ? 'down' : '';

          pointer.duration = +Date.now() - pointer.startTime;
          pointer.velocityX = pointer.distanceX / pointer.duration;
          pointer.velocityY = pointer.distanceY / pointer.duration;
        }

        /*
         * Normalize the point where the DOM event happened whether it's touch or mouse.
         * @returns point event obj with pageX and pageY on it.
         */
        function getEventPoint(ev) {
          ev = ev.originalEvent || ev; // support jQuery events
          return (ev.touches && ev.touches[0]) ||
            (ev.changedTouches && ev.changedTouches[0]) ||
            ev;
        }

    })(window.jQuery);

    (function () {
        'use strict';

        angular.module('material.core')
            .provider('$$interimElement', InterimElementProvider);

        /*
         * @ngdoc service
         * @name $$interimElement
         * @module material.core
         *
         * @description
         *
         * Factory that contructs `$$interimElement.$service` services.
         * Used internally in material design for elements that appear on screen temporarily.
         * The service provides a promise-like API for interacting with the temporary
         * elements.
         *
         * ```js
         * app.service('$mdToast', function($$interimElement) {
         *   var $mdToast = $$interimElement(toastDefaultOptions);
         *   return $mdToast;
         * });
         * ```
         * @param {object=} defaultOptions Options used by default for the `show` method on the service.
         *
         * @returns {$$interimElement.$service}
         *
         */

        function InterimElementProvider() {
            createInterimElementProvider.$get = InterimElementFactory;
            InterimElementFactory.$inject = ["$document", "$q", "$rootScope", "$timeout", "$rootElement", "$animate", "$interpolate", "$mdCompiler"];
            return createInterimElementProvider;

            /**
             * Returns a new provider which allows configuration of a new interimElement
             * service. Allows configuration of default options & methods for options,
             * as well as configuration of 'preset' methods (eg dialog.basic(): basic is a preset method)
             */
            function createInterimElementProvider(interimFactoryName) {
                var EXPOSED_METHODS = ['onHide', 'onShow', 'onRemove'];
                var providerConfig = {
                    presets: {}
                };
                var provider = {
                    setDefaults: setDefaults,
                    addPreset: addPreset,
                    $get: factory
                };

                /**
                 * all interim elements will come with the 'build' preset
                 */
                provider.addPreset('build', {
                    methods: ['controller', 'controllerAs', 'resolve',
                        'template', 'templateUrl', 'themable', 'transformTemplate', 'parent'
                    ]
                });

                factory.$inject = ["$$interimElement", "$animate", "$injector"];
                return provider;

                /**
                 * Save the configured defaults to be used when the factory is instantiated
                 */
                function setDefaults(definition) {
                    providerConfig.optionsFactory = definition.options;
                    providerConfig.methods = (definition.methods || []).concat(EXPOSED_METHODS);
                    return provider;
                }

                /**
                 * Save the configured preset to be used when the factory is instantiated
                 */
                function addPreset(name, definition) {
                    definition = definition || {};
                    definition.methods = definition.methods || [];
                    definition.options = definition.options || function () {
                        return {};
                    };

                    if (/^cancel|hide|show$/.test(name)) {
                        throw new Error("Preset '" + name + "' in " + interimFactoryName + " is reserved!");
                    }
                    if (definition.methods.indexOf('_options') > -1) {
                        throw new Error("Method '_options' in " + interimFactoryName + " is reserved!");
                    }
                    providerConfig.presets[name] = {
                        methods: definition.methods.concat(EXPOSED_METHODS),
                        optionsFactory: definition.options,
                        argOption: definition.argOption
                    };
                    return provider;
                }

                /**
                 * Create a factory that has the given methods & defaults implementing interimElement
                 */
                /* @ngInject */
                function factory($$interimElement, $animate, $injector) {
                    var defaultMethods;
                    var defaultOptions;
                    var interimElementService = $$interimElement();

                    /*
                     * publicService is what the developer will be using.
                     * It has methods hide(), cancel(), show(), build(), and any other
                     * presets which were set during the config phase.
                     */
                    var publicService = {
                        hide: interimElementService.hide,
                        cancel: interimElementService.cancel,
                        show: showInterimElement
                    };

                    defaultMethods = providerConfig.methods || [];
                    // This must be invoked after the publicService is initialized
                    defaultOptions = invokeFactory(providerConfig.optionsFactory, {});

                    angular.forEach(providerConfig.presets, function (definition, name) {
                        var presetDefaults = invokeFactory(definition.optionsFactory, {});
                        var presetMethods = (definition.methods || []).concat(defaultMethods);

                        // Every interimElement built with a preset has a field called `$type`,
                        // which matches the name of the preset.
                        // Eg in preset 'confirm', options.$type === 'confirm'
                        angular.extend(presetDefaults, {
                            $type: name
                        });

                        // This creates a preset class which has setter methods for every
                        // method given in the `.addPreset()` function, as well as every
                        // method given in the `.setDefaults()` function.
                        //
                        // @example
                        // .setDefaults({
                        //   methods: ['hasBackdrop', 'clickOutsideToClose', 'escapeToClose', 'targetEvent'],
                        //   options: dialogDefaultOptions
                        // })
                        // .addPreset('alert', {
                        //   methods: ['title', 'ok'],
                        //   options: alertDialogOptions
                        // })
                        //
                        // Set values will be passed to the options when interimElemnt.show() is called.
                        function Preset(opts) {
                            this._options = angular.extend({}, presetDefaults, opts);
                        }
                        angular.forEach(presetMethods, function (name) {
                            Preset.prototype[name] = function (value) {
                                this._options[name] = value;
                                return this;
                            };
                        });

                        // Create shortcut method for one-linear methods
                        if (definition.argOption) {
                            var methodName = 'show' + name.charAt(0).toUpperCase() + name.slice(1);
                            publicService[methodName] = function (arg) {
                                var config = publicService[name](arg);
                                return publicService.show(config);
                            };
                        }

                        // eg $mdDialog.alert() will return a new alert preset
                        publicService[name] = function (arg) {
                            // If argOption is supplied, eg `argOption: 'content'`, then we assume
                            // if the argument is not an options object then it is the `argOption` option.
                            //
                            // @example `$mdToast.simple('hello')` // sets options.content to hello
                            //                                     // because argOption === 'content'
                            if (arguments.length && definition.argOption && !angular.isObject(arg) &&
                                !angular.isArray(arg)) {
                                return (new Preset())[definition.argOption](arg);
                            } else {
                                return new Preset(arg);
                            }

                        };
                    });

                    return publicService;

                    function showInterimElement(opts) {
                        // opts is either a preset which stores its options on an _options field,
                        // or just an object made up of options
                        if (opts && opts._options) opts = opts._options;
                        return interimElementService.show(
                            angular.extend({}, defaultOptions, opts)
                        );
                    }

                    /**
                     * Helper to call $injector.invoke with a local of the factory name for
                     * this provider.
                     * If an $mdDialog is providing options for a dialog and tries to inject
                     * $mdDialog, a circular dependency error will happen.
                     * We get around that by manually injecting $mdDialog as a local.
                     */
                    function invokeFactory(factory, defaultVal) {
                        var locals = {};
                        locals[interimFactoryName] = publicService;
                        return $injector.invoke(factory || function () {
                            return defaultVal;
                        }, {}, locals);
                    }

                }

            }

            /* @ngInject */
            function InterimElementFactory($document, $q, $rootScope, $timeout, $rootElement, $animate,
                $interpolate, $mdCompiler) {
                var startSymbol = $interpolate.startSymbol(),
                    endSymbol = $interpolate.endSymbol(),
                    usesStandardSymbols = ((startSymbol === '{{') && (endSymbol === '}}')),
                    processTemplate = usesStandardSymbols ? angular.identity : replaceInterpolationSymbols;

                return function createInterimElementService() {
                    /*
                     * @ngdoc service
                     * @name $$interimElement.$service
                     *
                     * @description
                     * A service used to control inserting and removing an element into the DOM.
                     *
                     */
                    var stack = [];
                    var service;
                    return service = {
                        show: show,
                        hide: hide,
                        cancel: cancel
                    };

                    /*
                     * @ngdoc method
                     * @name $$interimElement.$service#show
                     * @kind function
                     *
                     * @description
                     * Adds the `$interimElement` to the DOM and returns a promise that will be resolved or rejected
                     * with hide or cancel, respectively.
                     *
                     * @param {*} options is hashMap of settings
                     * @returns a Promise
                     *
                     */
                    function show(options) {
                        options.zIndex = 80 + stack.length;
                        var interimElement = new InterimElement(options);

                        stack.unshift(interimElement);
                        return interimElement.show().then(function () {
                            return interimElement.deferred.promise;
                        });
                    }

                    /*
                     * @ngdoc method
                     * @name $$interimElement.$service#hide
                     * @kind function
                     *
                     * @description
                     * Removes the `$interimElement` from the DOM and resolves the promise returned from `show`
                     *
                     * @param {*} resolveParam Data to resolve the promise with
                     * @returns a Promise that will be resolved after the element has been removed.
                     *
                     */
                    function hide(response, interimElementAt) {
                        var interimElement;
                        if (interimElementAt !== undefined) {
                            interimElement = interimElementAt;
                            stack.splice(stack.indexOf(interimElementAt), 1);
                        } else {
                            interimElement = stack.shift();
                        }
                        interimElement && interimElement.remove().then(function () {
                            interimElement.deferred.resolve(response);
                        });

                        return interimElement ? interimElement.deferred.promise : $q.when(response);
                    }

                    /*
                     * @ngdoc method
                     * @name $$interimElement.$service#cancel
                     * @kind function
                     *
                     * @description
                     * Removes the `$interimElement` from the DOM and rejects the promise returned from `show`
                     *
                     * @param {*} reason Data to reject the promise with
                     * @returns Promise that will be rejected after the element has been removed.
                     *
                     */
                    function cancel(reason, interimElementAt) {
                        var interimElement;
                        if (interimElementAt !== undefined) {
                            interimElement = interimElementAt;
                            stack.splice(stack.indexOf(interimElementAt), 1);
                        } else {
                            interimElement = stack.shift();
                        }
                        interimElement && interimElement.remove().then(function () {
                            interimElement.deferred.reject(reason);
                        });

                        return interimElement ? interimElement.deferred.promise : $q.reject(reason);
                    }


                    /*
                     * Internal Interim Element Object
                     * Used internally to manage the DOM element and related data
                     */
                    function InterimElement(options) {
                        var self;
                        var hideTimeout, element;

                        options = options || {};
                        options = angular.extend({
                            scope: options.scope || $rootScope.$new(options.isolateScope),
                            onShow: function (scope, element, options) {
                                return $animate.enter(element, options.parent);
                            },
                            onRemove: function (scope, element, options) {
                                // Element could be undefined if a new element is shown before
                                // the old one finishes compiling.
                                return element && $animate.leave(element) || $q.when();
                            }
                        }, options);

                        if (options.template) {
                            options.template = processTemplate(options.template);
                        }

                        self = {
                            options: options,
                            deferred: $q.defer(),
                            show: function () {
                                return $mdCompiler.compile(options).then(function (compileData) {
                                    angular.extend(compileData.locals, self.options);

                                    // Search for parent at insertion time, if not specified
                                    if (angular.isString(options.parent)) {
                                        options.parent = angular.element($document[0].querySelector(options.parent));
                                    } else if (!options.parent) {
                                        options.parent = $rootElement.find('body');
                                        if (!options.parent.length) options.parent = $rootElement;
                                    }

                                    element = compileData.link(options.scope);
                                    element.css('z-index', options.zIndex);

                                    var ret = options.onShow(options.scope, element, options);
                                    return $q.when(ret)
                                        .then(function () {
                                            // Issue onComplete callback when the `show()` finishes
                                            (options.onComplete || angular.noop)(options.scope, element, options);
                                            startHideTimeout();
                                        });

                                    function startHideTimeout() {
                                        if (options.hideDelay) {
                                            hideTimeout = $timeout(service.cancel, options.hideDelay);
                                        }
                                    }
                                });
                            },
                            cancelTimeout: function () {
                                if (hideTimeout) {
                                    $timeout.cancel(hideTimeout);
                                    hideTimeout = undefined;
                                }
                            },
                            remove: function () {
                                self.cancelTimeout();
                                var ret = options.onRemove(options.scope, element, options);
                                return $q.when(ret).then(function () {
                                    options.scope.$destroy();
                                });
                            }
                        };

                        options.interimElement = self;
                        options.stack = stack;

                        return self;
                    }
                };

                /*
                 * Replace `{{` and `}}` in a string (usually a template) with the actual start-/endSymbols used
                 * for interpolation. This allows pre-defined templates (for components such as dialog, toast etc)
                 * to continue to work in apps that use custom interpolation start-/endSymbols.
                 *
                 * @param {string} text The text in which to replace `{{` / `}}`
                 * @returns {string} The modified string using the actual interpolation start-/endSymbols
                 */
                function replaceInterpolationSymbols(text) {
                    if (!text || !angular.isString(text)) return text;
                    return text.replace(/\{\{/g, startSymbol).replace(/}}/g, endSymbol);
                }
            }

        }

    })();
    (function () {
        'use strict';

        angular.module('material.core')
            .provider('$$interimStackableElement', InterimElementProvider);

        /*
         * @ngdoc service
         * @name $$interimStackableElement
         * @module material.core
         *
         * @description
         *
         * Factory that contructs `$$interimStackableElement.$service` services.
         * Used internally in material design for elements that appear on screen temporarily.
         * The service provides a promise-like API for interacting with the temporary
         * elements.
         *
         * ```js
         * app.service('$mdToast', function($$interimStackableElement) {
         *   var $mdToast = $$interimStackableElement(toastDefaultOptions);
         *   return $mdToast;
         * });
         * ```
         * @param {object=} defaultOptions Options used by default for the `show` method on the service.
         *
         * @returns {$$interimStackableElement.$service}
         *
         */

        function InterimElementProvider() {
            createInterimElementProvider.$get = InterimElementFactory;
            InterimElementFactory.$inject = ["$document", "$q", "$rootScope", "$timeout", "$rootElement", "$animate", "$interpolate", "$mdCompiler"];
            return createInterimElementProvider;

            /**
             * Returns a new provider which allows configuration of a new interimElement
             * service. Allows configuration of default options & methods for options,
             * as well as configuration of 'preset' methods (eg dialog.basic(): basic is a preset method)
             */
            function createInterimElementProvider(interimFactoryName) {
                var EXPOSED_METHODS = ['onHide', 'onShow', 'onRemove'];
                var providerConfig = {
                    presets: {}
                };
                var provider = {
                    setDefaults: setDefaults,
                    addPreset: addPreset,
                    $get: factory
                };

                /**
                 * all interim elements will come with the 'build' preset
                 */
                provider.addPreset('build', {
                    methods: ['controller', 'controllerAs', 'resolve',
                        'template', 'templateUrl', 'themable', 'transformTemplate', 'parent'
                    ]
                });

                factory.$inject = ["$$interimStackableElement", "$animate", "$injector"];
                return provider;

                /**
                 * Save the configured defaults to be used when the factory is instantiated
                 */
                function setDefaults(definition) {
                    providerConfig.optionsFactory = definition.options;
                    providerConfig.methods = (definition.methods || []).concat(EXPOSED_METHODS);
                    return provider;
                }

                /**
                 * Save the configured preset to be used when the factory is instantiated
                 */
                function addPreset(name, definition) {
                    definition = definition || {};
                    definition.methods = definition.methods || [];
                    definition.options = definition.options || function () {
                        return {};
                    };

                    if (/^cancel|hide|show$/.test(name)) {
                        throw new Error("Preset '" + name + "' in " + interimFactoryName + " is reserved!");
                    }
                    if (definition.methods.indexOf('_options') > -1) {
                        throw new Error("Method '_options' in " + interimFactoryName + " is reserved!");
                    }
                    providerConfig.presets[name] = {
                        methods: definition.methods.concat(EXPOSED_METHODS),
                        optionsFactory: definition.options,
                        argOption: definition.argOption
                    };
                    return provider;
                }

                /**
                 * Create a factory that has the given methods & defaults implementing interimElement
                 */
                /* @ngInject */
                function factory($$interimStackableElement, $animate, $injector) {
                    var defaultMethods;
                    var defaultOptions;
                    var interimElementService = $$interimStackableElement();

                    /*
                     * publicService is what the developer will be using.
                     * It has methods hide(), cancel(), show(), build(), and any other
                     * presets which were set during the config phase.
                     */
                    var publicService = {
                        hide: interimElementService.hide,
                        cancel: interimElementService.cancel,
                        show: showInterimElement
                    };

                    defaultMethods = providerConfig.methods || [];
                    // This must be invoked after the publicService is initialized
                    defaultOptions = invokeFactory(providerConfig.optionsFactory, {});

                    angular.forEach(providerConfig.presets, function (definition, name) {
                        var presetDefaults = invokeFactory(definition.optionsFactory, {});
                        var presetMethods = (definition.methods || []).concat(defaultMethods);

                        // Every interimElement built with a preset has a field called `$type`,
                        // which matches the name of the preset.
                        // Eg in preset 'confirm', options.$type === 'confirm'
                        angular.extend(presetDefaults, {
                            $type: name
                        });

                        function Preset(opts) {
                            this._options = angular.extend({}, presetDefaults, opts);
                        }
                        angular.forEach(presetMethods, function (name) {
                            Preset.prototype[name] = function (value) {
                                this._options[name] = value;
                                return this;
                            };
                        });

                        // Create shortcut method for one-linear methods
                        if (definition.argOption) {
                            var methodName = 'show' + name.charAt(0).toUpperCase() + name.slice(1);
                            publicService[methodName] = function (arg) {
                                var config = publicService[name](arg);
                                return publicService.show(config);
                            };
                        }

                        // eg $mdDialog.alert() will return a new alert preset
                        publicService[name] = function (arg) {
                            // If argOption is supplied, eg `argOption: 'content'`, then we assume
                            // if the argument is not an options object then it is the `argOption` option.
                            //
                            // @example `$mdToast.simple('hello')` // sets options.content to hello
                            //                                     // because argOption === 'content'
                            if (arguments.length && definition.argOption && !angular.isObject(arg) &&
                                !angular.isArray(arg)) {
                                return (new Preset())[definition.argOption](arg);
                            } else {
                                return new Preset(arg);
                            }

                        };
                    });

                    return publicService;

                    function showInterimElement(opts) {
                        // opts is either a preset which stores its options on an _options field,
                        // or just an object made up of options
                        if (opts && opts._options) opts = opts._options;
                        return interimElementService.show(
                            angular.extend({}, defaultOptions, opts)
                        );
                    }

                    /**
                     * Helper to call $injector.invoke with a local of the factory name for
                     * this provider.
                     * If an $mdDialog is providing options for a dialog and tries to inject
                     * $mdDialog, a circular dependency error will happen.
                     * We get around that by manually injecting $mdDialog as a local.
                     */
                    function invokeFactory(factory, defaultVal) {
                        var locals = {};
                        locals[interimFactoryName] = publicService;
                        return $injector.invoke(factory || function () {
                            return defaultVal;
                        }, {}, locals);
                    }

                }

            }

            /* @ngInject */
            function InterimElementFactory($document, $q, $rootScope, $timeout, $rootElement, $animate,
                $interpolate, $mdCompiler) {
                var startSymbol = $interpolate.startSymbol(),
                    endSymbol = $interpolate.endSymbol(),
                    usesStandardSymbols = ((startSymbol === '{{') && (endSymbol === '}}')),
                    processTemplate = usesStandardSymbols ? angular.identity : replaceInterpolationSymbols;

                return function createInterimElementService() {
                    /*
                     * @ngdoc service
                     * @name $$interimStackableElement.$service
                     *
                     * @description
                     * A service used to control inserting and removing an element into the DOM.
                     *
                     */
                    var stack = [];
                    var service;
                    return service = {
                        show: show,
                        hide: hide,
                        cancel: cancel
                    };

                    /*
                     * @ngdoc method
                     * @name $$interimStackableElement.$service#show
                     * @kind function
                     *
                     * @description
                     * Adds the `$interimElement` to the DOM and returns a promise that will be resolved or rejected
                     * with hide or cancel, respectively.
                     *
                     * @param {*} options is hashMap of settings
                     * @returns a Promise
                     *
                     */
                    function show(options) {
                        options.zIndex = 80 + stack.length;
                        var interimElement = new InterimElement(options);

                        stack.unshift(interimElement);
                        return interimElement.show().then(function () {
                            return interimElement.deferred.promise;
                        });
                    }

                    /*
                     * @ngdoc method
                     * @name $$interimStackableElement.$service#hide
                     * @kind function
                     *
                     * @description
                     * Removes the `$interimElement` from the DOM and resolves the promise returned from `show`
                     *
                     * @param {*} resolveParam Data to resolve the promise with
                     * @returns a Promise that will be resolved after the element has been removed.
                     *
                     */
                    function hide(response, interimElementAt) {
                        var interimElement;
                        if (interimElementAt !== undefined) {
                            interimElement = interimElementAt;
                            stack.splice(stack.indexOf(interimElementAt), 1);
                        } else {
                            interimElement = stack.shift();
                        }
                        interimElement && interimElement.remove().then(function () {
                            interimElement.deferred.resolve(response);
                        });

                        return interimElement ? interimElement.deferred.promise : $q.when(response);
                    }

                    /*
                     * @ngdoc method
                     * @name $$interimStackableElement.$service#cancel
                     * @kind function
                     *
                     * @description
                     * Removes the `$interimElement` from the DOM and rejects the promise returned from `show`
                     *
                     * @param {*} reason Data to reject the promise with
                     * @returns Promise that will be rejected after the element has been removed.
                     *
                     */
                    function cancel(reason, interimElementAt) {
                        var interimElement;
                        if (interimElementAt !== undefined) {
                            interimElement = interimElementAt;
                            stack.splice(stack.indexOf(interimElementAt), 1);
                        } else {
                            interimElement = stack.shift();
                        }
                        interimElement && interimElement.remove().then(function () {
                            interimElement.deferred.reject(reason);
                        });

                        return interimElement ? interimElement.deferred.promise : $q.reject(reason);
                    }


                    /*
                     * Internal Interim Element Object
                     * Used internally to manage the DOM element and related data
                     */
                    function InterimElement(options) {
                        var self;
                        var hideTimeout, element;

                        options = options || {};
                        options = angular.extend({
                            scope: options.scope || $rootScope.$new(options.isolateScope),
                            onShow: function (scope, element, options) {
                                return $animate.enter(element, options.parent);
                            },
                            onRemove: function (scope, element, options) {
                                // Element could be undefined if a new element is shown before
                                // the old one finishes compiling.
                                return element && $animate.leave(element) || $q.when();
                            }
                        }, options);

                        if (options.template) {
                            options.template = processTemplate(options.template);
                        }

                        self = {
                            options: options,
                            deferred: $q.defer(),
                            show: function () {
                                return $mdCompiler.compile(options).then(function (compileData) {
                                    angular.extend(compileData.locals, self.options);

                                    // Search for parent at insertion time, if not specified
                                    if (angular.isString(options.parent)) {
                                        options.parent = angular.element($document[0].querySelector(options.parent));
                                    } else if (!options.parent) {
                                        options.parent = $rootElement.find('body');
                                        if (!options.parent.length) options.parent = $rootElement;
                                    }

                                    element = compileData.link(options.scope);
                                    element.css('z-index', options.zIndex);

                                    var ret = options.onShow(options.scope, element, options);
                                    return $q.when(ret)
                                        .then(function () {
                                            // Issue onComplete callback when the `show()` finishes
                                            (options.onComplete || angular.noop)(options.scope, element, options);
                                            startHideTimeout();
                                        });

                                    function startHideTimeout() {
                                        if (options.hideDelay) {
                                            hideTimeout = $timeout(service.cancel, options.hideDelay);
                                        }
                                    }
                                });
                            },
                            cancelTimeout: function () {
                                if (hideTimeout) {
                                    $timeout.cancel(hideTimeout);
                                    hideTimeout = undefined;
                                }
                            },
                            remove: function () {
                                self.cancelTimeout();
                                var ret = options.onRemove(options.scope, element, options);
                                return $q.when(ret).then(function () {
                                    options.scope.$destroy();
                                });
                            }
                        };

                        options.interimElement = self;
                        options.stack = stack;

                        return self;
                    }
                };

                /*
                 * Replace `{{` and `}}` in a string (usually a template) with the actual start-/endSymbols used
                 * for interpolation. This allows pre-defined templates (for components such as dialog, toast etc)
                 * to continue to work in apps that use custom interpolation start-/endSymbols.
                 *
                 * @param {string} text The text in which to replace `{{` / `}}`
                 * @returns {string} The modified string using the actual interpolation start-/endSymbols
                 */
                function replaceInterpolationSymbols(text) {
                    if (!text || !angular.isString(text)) return text;
                    return text.replace(/\{\{/g, startSymbol).replace(/}}/g, endSymbol);
                }
            }

        }

    })();
    (function () {
        'use strict';

        /**
         * @ngdoc module
         * @name material.core.componentRegistry
         *
         * @description
         * A component instance registration service.
         * Note: currently this as a private service in the SideNav component.
         */
        angular.module('material.core')
            .factory('$mdComponentRegistry', ComponentRegistry);

        /*
         * @private
         * @ngdoc factory
         * @name ComponentRegistry
         * @module material.core.componentRegistry
         *
         */
        function ComponentRegistry($log, $q) {

            var self;
            var instances = [];
            var pendings = {};

            return self = {
                /**
                 * Used to print an error when an instance for a handle isn't found.
                 */
                notFoundError: function (handle) {
                    $log.error('No instance found for handle', handle);
                },
                /**
                 * Return all registered instances as an array.
                 */
                getInstances: function () {
                    return instances;
                },

                /**
                 * Get a registered instance.
                 * @param handle the String handle to look up for a registered instance.
                 */
                get: function (handle) {
                    if (!isValidID(handle)) return null;

                    var i, j, instance;
                    for (i = 0, j = instances.length; i < j; i++) {
                        instance = instances[i];
                        if (instance.$$mdHandle === handle) {
                            return instance;
                        }
                    }
                    return null;
                },

                /**
                 * Register an instance.
                 * @param instance the instance to register
                 * @param handle the handle to identify the instance under.
                 */
                register: function (instance, handle) {
                    if (!handle) return angular.noop;

                    instance.$$mdHandle = handle;
                    instances.push(instance);
                    resolveWhen();

                    return deregister;

                    /**
                     * Remove registration for an instance
                     */
                    function deregister() {
                        var index = instances.indexOf(instance);
                        if (index !== -1) {
                            instances.splice(index, 1);
                        }
                    }

                    /**
                     * Resolve any pending promises for this instance
                     */
                    function resolveWhen() {
                        var dfd = pendings[handle];
                        if (dfd) {
                            dfd.resolve(instance);
                            delete pendings[handle];
                        }
                    }
                },

                /**
                 * Async accessor to registered component instance
                 * If not available then a promise is created to notify
                 * all listeners when the instance is registered.
                 */
                when: function (handle) {
                    if (isValidID(handle)) {
                        var deferred = $q.defer();
                        var instance = self.get(handle);

                        if (instance) {
                            deferred.resolve(instance);
                        } else {
                            pendings[handle] = deferred;
                        }

                        return deferred.promise;
                    }
                    return $q.reject("Invalid `md-component-id` value.");
                }

            };

            function isValidID(handle) {
                return handle && (handle !== "");
            }

        }
        ComponentRegistry.$inject = ["$log", "$q"];


    })();

    (function () {
        'use strict';

        function isSafari() {
            var ua = navigator.userAgent.toLowerCase(); 
            if (ua.indexOf('safari') !== -1) { 
                if (ua.indexOf('chrome') === -1) {
                  return true;
                }
            }
            return false;
        }

        angular.module('material.core')
            .factory('$mdInkRipple', InkRippleService)
            .directive('mdInkRipple', InkRippleDirective)
            .directive('mdNoInk', attrNoDirective())
            .directive('mdNoBar', attrNoDirective())
            .directive('mdNoStretch', attrNoDirective());

        function InkRippleDirective($mdInkRipple, $parse) {
            return {
                controller: angular.noop,
                link: function (scope, element, attr) {
                    if (attr.hasOwnProperty('mdInkRippleCheckbox')) {
                        $mdInkRipple.attachCheckboxBehavior(scope, element);
                    } else {
                        $mdInkRipple.attachButtonBehavior(scope, element);
                    }
                }
            };
        }
        InkRippleDirective.$inject = ["$mdInkRipple", "$parse"];

        function InkRippleService($window, $timeout, $parse, $$rAF, $animateCss) {

            return {
                attachButtonBehavior: attachButtonBehavior,
                attachCheckboxBehavior: attachCheckboxBehavior,
                attachTabBehavior: attachTabBehavior,
                attach: attach
            };

            function attachButtonBehavior(scope, element, options) {
                return attach(scope, element, angular.extend({
                    isFAB: element.hasClass('md-fab'),
                    isMenuItem: element.hasClass('md-menu-item'),
                    center: false,
                    dimBackground: true
                }, options));
            }

            function attachCheckboxBehavior(scope, element, options) {
                return attach(scope, element, angular.extend({
                    center: true,
                    dimBackground: false,
                    fitRipple: true
                }, options));
            }

            function attachTabBehavior(scope, element, options) {
                return attach(scope, element, angular.extend({
                    center: false,
                    dimBackground: true,
                    outline: true
                }, options));
            }

            function attach(scope, element, options) {
                if (element.controller('mdNoInk')) return angular.noop;

                var ignore = element.attr('md-ink-ripple-ignore'),
                    eventHandler = (!element.attr('md-ink-ripple-click') ? '$md.pressdown' : 'click'),
                    pulsateOptions = scope.$eval(element.attr('md-ink-ripple-pulsate-options')) || {},
                    pulsates = pulsateOptions.repeat || 9,
                    pulsateColor = pulsateOptions.color || false,
                    PULSATE_FREQUENCY = pulsateOptions.speed || 2000,
                    lastColor = (pulsateOptions.color ? 'ripple-dark': null);


                ignore = (ignore ? $parse(ignore)(scope) : undefined);

                options = angular.extend({
                    colorElement: element,
                    mousedown: true,
                    hover: true,
                    focus: true,
                    center: false,
                    mousedownPauseTime: 150,
                    dimBackground: false,
                    outline: false,
                    isFAB: false,
                    isMenuItem: false,
                    fitRipple: false
                }, options);

                var rippleSize,
                    controller = element.controller('mdInkRipple') || {},
                    counter = 0,
                    ripples = [],
                    states = [],
                    isActiveExpr = element.attr('md-highlight'),
                    isActive = false,
                    isHeld = false,
                    node = element[0],
                    rippleSizeSetting = element.attr('md-ripple-size');

                switch (rippleSizeSetting) {
                case 'full':
                    options.isFAB = true;
                    break;
                case 'partial':
                    options.isFAB = false;
                    break;
                }

                element.addClass('ripple-presence');

                // expose onInput for ripple testing
                element.on(eventHandler, onPressDown);

                if (element.attr('md-ink-ripple-pulsate')) {
                    scope.$watch(element.attr('md-ink-ripple-pulsate'), function (neww) {
                        if (neww) {
                            var ets = element[0].getBoundingClientRect();
                            onPressDown2({
                                clientY: ets.top + (ets.width / 2),
                                clientX: ets.left + (ets.height / 2)
                            }, PULSATE_FREQUENCY);
                        }
                    });
                }

                // Publish self-detach method if desired...
                return function detach() {
                    element.off(eventHandler, onPressDown);
                    //.off('$md.pressup', onPressUp);
                    //.off('click', onPressDown);
                    element.removeClass('ripple-presence');
                };


                /**
                 * Handles user input start and stop events
                 *
                 */
                // temporary fix for the safari ripple
                var k = null;

                function onPressDown(ev) {
                    if (k) {
                        clearTimeout(k);
                    }
                    k = setTimeout(function () {
                        onPressDown2(ev);
                    }, (isSafari() ? 90 : 0));
                }

                function onPressDown2(ev, time) {
                    if (!isRippleAllowed()) return;

                    var cls = 'ripple-animation',
                        element_position = {top: 0, left: 0},
                        parent_height = 0,
                        parent_width = 0;

                    if (ev.target) {
                        pulsates = 0;
                        lastColor = undefined;
                        pulsateColor = false;
                    }

                    if (ignore && ev.target) {
                        var target = $(ev.target),
                            skip = false;
                        angular.forEach(ignore, function (ig) {
                            if (target.is(ig) || target.parent().is(ig)) {
                                skip = true;
                            }
                        });
                        if (skip) {
                            return;
                        }
                    }
                    isHeld = true;
                    var worker = {};
                    worker.style = {
                        'top': '0',
                        'left': '0'
                    };
                    var ripple = angular.element('<div class="ripple-active"></div>');
                    ripple.css(worker.style);
                    
                    if (lastColor) {
                        if (lastColor === 'ripple-dark') {
                            ripple.addClass('ripple-light');
                            lastColor = 'ripple-light';
                        } else {
                            ripple.addClass('ripple-dark');
                            lastColor = 'ripple-dark';
                        }
                    } else {
                        if (element[0].hasAttribute('ripple-dark')) {
                            ripple.addClass('ripple-dark');
                            if (pulsateColor) {
                                lastColor = 'ripple-dark';
                            }
                        } else if (element[0].hasAttribute('ripple-light')) {
                            ripple.addClass('ripple-light');
                            if (pulsateColor) {
                                lastColor = 'ripple-light';
                            }
                        }
                    }
                    element.find('.ripple-active').remove(); // remove all previous ripples
                    element.append(ripple);
                    var squared = element[0].hasAttribute('md-ink-ripple-action') || element[0].hasAttribute('ripple-action');
                    if (squared) {
                        worker.style = {
                            'top': '0px',
                            'left': '0px',
                            'height': element.outerWidth() + 'px',
                            'width': element.outerWidth() + 'px'
                        };
                        cls += ' ripple-action';
                    } else if (element[0].hasAttribute('md-ink-ripple-switch')) {
                        worker.style = {
                            'top': '-14px',
                            'left': '-14px',
                            'height': '48px',
                            'width': '48px'
                        };
                    } else {
                        element_position = element[0].getBoundingClientRect();
                        parent_width = element_position.width;
                        parent_height = element_position.height;
                        //parent_width = element.width();
                        //parent_height = element.height();
                        var parent_diagonal = 2 * (Math.round(Math.sqrt((parent_width * parent_width) + (parent_height * parent_height))));
                        if (parent_diagonal > 2000) {
                            parent_diagonal = 2000;
                        }
                        var margin = -(parent_diagonal / 2);
                        worker.style = {
                            'top': (ev.clientY - element_position.top),
                            'left': (ev.clientX - element_position.left),
                            'height': parent_diagonal,
                            'width': parent_diagonal,
                            'margin-top': margin,
                            'margin-left': margin
                        };
                    }

                    ripple.css(worker.style);

                    $timeout(function () {
                        $animateCss(ripple, {
                            addClass: cls
                        }).start().done(function () {
                            ripple.removeClass(cls);
                            var infinite = pulsates === 'infinite';
                            if ((infinite || pulsates) && time) {
                                if (!infinite) {
                                    pulsates -= 1;
                                }
                                setTimeout(function () {
                                    onPressDown2({
                                        clientY: element_position.top + (parent_height / 2),
                                        clientX: element_position.left + (parent_width / 2)
                                    }, PULSATE_FREQUENCY);
                                }, PULSATE_FREQUENCY - 600);
                            }
                        });
                    }, 0, false);

                }
                function onPressUp(ev) {
                    isHeld = false;
                }

                /**
                 * Determines if the ripple is allowed
                 *
                 * @returns {boolean} true if the ripple is allowed, false if not
                 */
                function isRippleAllowed() {
                    var parent = node.parentNode;
                    var grandparent = parent && parent.parentNode;
                    var ancestor = grandparent && grandparent.parentNode;
                    return !isDisabled(node) && !isDisabled(parent) && !isDisabled(grandparent) && !isDisabled(ancestor);

                    function isDisabled(elem) {
                        var disabled = elem && elem.hasAttribute && elem.hasAttribute('disabled');
                        if (!disabled) {
                            disabled = $(elem).hasClass('md-ink-ripple-disabled');
                        }
                        return disabled;
                    }
                }

            }
        }
        InkRippleService.$inject = ["$window", "$timeout", "$parse", "$$rAF", "$animateCss"];

        function attrNoDirective() {
            return function () {
                return {
                    controller: angular.noop
                };
            };
        }
    })();



}());
