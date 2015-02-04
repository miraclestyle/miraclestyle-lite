/*
 * angular-ui-bootstrap
 * http://angular-ui.github.io/bootstrap/

 * Version: 0.11.2 - 2014-09-26
 * License: MIT
 */
angular.module("ui.bootstrap", ["ui.bootstrap.transition",
    "ui.bootstrap.collapse",
    "ui.bootstrap.accordion",
    "ui.bootstrap.bindHtml",
    "ui.bootstrap.dateparser",
    "ui.bootstrap.position",
    "ui.bootstrap.datepicker",
    "ui.bootstrap.modal",
    "ui.bootstrap.timepicker"
]);

angular.module('ui.bootstrap.transition', [])

/**
 * $transition service provides a consistent interface to trigger CSS 3 transitions and to be informed when they complete.
 * @param  {DOMElement} element  The DOMElement that will be animated.
 * @param  {string|object|function} trigger  The thing that will cause the transition to start:
 *   - As a string, it represents the css class to be added to the element.
 *   - As an object, it represents a hash of style attributes to be applied to the element.
 *   - As a function, it represents a function to be called that will cause the transition to occur.
 * @return {Promise}  A promise that is resolved when the transition finishes.
 */
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
}]);

angular.module('ui.bootstrap.collapse', ['ui.bootstrap.transition'])

.directive('collapse', ['$transition', function ($transition) {

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
}]);

angular.module('ui.bootstrap.accordion', ['ui.bootstrap.collapse'])

.constant('accordionConfig', {
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
        templateUrl: 'template/accordion/accordion.html'
    };
})

// The accordion-group directive indicates a block of html that will expand and collapse in an accordion
.directive('accordionGroup', function () {
    return {
        require: '^accordion', // We need this directive to be inside an accordion
        restrict: 'EA',
        transclude: true, // It transcludes the contents of the directive into the template
        replace: true, // The element containing the directive will be replaced with the template
        templateUrl: 'template/accordion/accordion-group.html',
        scope: {
            heading: '@', // Interpolate the heading attribute onto this scope
            isOpen: '=?',
            isDisabled: '=?'
        },
        controller: function () {
            this.setHeading = function (element) {
                this.heading = element;
            };
        },
        link: function (scope, element, attrs, accordionCtrl) {
            accordionCtrl.addGroup(scope);

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
});

angular.module('ui.bootstrap.bindHtml', [])

.directive('bindHtmlUnsafe', function () {
    return function (scope, element, attr) {
        element.addClass('ng-binding').data('$binding', attr.bindHtmlUnsafe);
        scope.$watch(attr.bindHtmlUnsafe, function bindHtmlUnsafeWatchAction(value) {
            element.html(value || '');
        });
    };
});

angular.module('ui.bootstrap.dateparser', [])

.service('dateParser', ['$locale', 'orderByFilter', function ($locale, orderByFilter) {

    this.parsers = {};

    var formatCodeToRegex = {
        'yyyy': {
            regex: '\\d{4}',
            apply: function (value) {
                this.year = +value;
            }
        },
        'yy': {
            regex: '\\d{2}',
            apply: function (value) {
                this.year = +value + 2000;
            }
        },
        'y': {
            regex: '\\d{1,4}',
            apply: function (value) {
                this.year = +value;
            }
        },
        'MMMM': {
            regex: $locale.DATETIME_FORMATS.MONTH.join('|'),
            apply: function (value) {
                this.month = $locale.DATETIME_FORMATS.MONTH.indexOf(value);
            }
        },
        'MMM': {
            regex: $locale.DATETIME_FORMATS.SHORTMONTH.join('|'),
            apply: function (value) {
                this.month = $locale.DATETIME_FORMATS.SHORTMONTH.indexOf(value);
            }
        },
        'MM': {
            regex: '0[1-9]|1[0-2]',
            apply: function (value) {
                this.month = value - 1;
            }
        },
        'M': {
            regex: '[1-9]|1[0-2]',
            apply: function (value) {
                this.month = value - 1;
            }
        },
        'dd': {
            regex: '[0-2][0-9]{1}|3[0-1]{1}',
            apply: function (value) {
                this.date = +value;
            }
        },
        'd': {
            regex: '[1-2]?[0-9]{1}|3[0-1]{1}',
            apply: function (value) {
                this.date = +value;
            }
        },
        'EEEE': {
            regex: $locale.DATETIME_FORMATS.DAY.join('|')
        },
        'EEE': {
            regex: $locale.DATETIME_FORMATS.SHORTDAY.join('|')
        }
    };

    function createParser(format) {
        var map = [],
            regex = format.split('');

        angular.forEach(formatCodeToRegex, function (data, code) {
            var index = format.indexOf(code);

            if (index > -1) {
                format = format.split('');

                regex[index] = '(' + data.regex + ')';
                format[index] = '$'; // Custom symbol to define consumed part of format
                for (var i = index + 1, n = index + code.length; i < n; i++) {
                    regex[i] = '';
                    format[i] = '$';
                }
                format = format.join('');

                map.push({
                    index: index,
                    apply: data.apply
                });
            }
        });

        return {
            regex: new RegExp('^' + regex.join('') + '$'),
            map: orderByFilter(map, 'index')
        };
    }

    this.parse = function (input, format) {
        if (!angular.isString(input) || !format) {
            return input;
        }

        format = $locale.DATETIME_FORMATS[format] || format;

        if (!this.parsers[format]) {
            this.parsers[format] = createParser(format);
        }

        var parser = this.parsers[format],
            regex = parser.regex,
            map = parser.map,
            results = input.match(regex);

        if (results && results.length) {
            var fields = {
                    year: 1900,
                    month: 0,
                    date: 1,
                    hours: 0
                },
                dt;

            for (var i = 1, n = results.length; i < n; i++) {
                var mapper = map[i - 1];
                if (mapper.apply) {
                    mapper.apply.call(fields, results[i]);
                }
            }

            if (isValid(fields.year, fields.month, fields.date)) {
                dt = new Date(fields.year, fields.month, fields.date, fields.hours);
            }

            return dt;
        }
    };

    // Check if date is valid for specific month (and year for February).
    // Month: 0 = Jan, 1 = Feb, etc
    function isValid(year, month, date) {
        if (month === 1 && date > 28) {
            return date === 29 && ((year % 4 === 0 && year % 100 !== 0) || year % 400 === 0);
        }

        if (month === 3 || month === 5 || month === 8 || month === 10) {
            return date < 31;
        }

        return true;
    }
}]);

angular.module('ui.bootstrap.position', [])

/**
 * A set of utility methods that can be use to retrieve position of DOM elements.
 * It is meant to be used where we need to absolute-position DOM elements in
 * relation to other, existing elements (this is the case for tooltips, popovers,
 * typeahead suggestions etc.).
 */
.factory('$position', ['$document', '$window', function ($document, $window) {

    function getStyle(el, cssprop) {
        if (el.currentStyle) { //IE
            return el.currentStyle[cssprop];
        } else if ($window.getComputedStyle) {
            return $window.getComputedStyle(el)[cssprop];
        }
        // finally try and get inline style
        return el.style[cssprop];
    }

    /**
     * Checks if a given element is statically positioned
     * @param element - raw DOM element
     */
    function isStaticPositioned(element) {
        return (getStyle(element, 'position') || 'static') === 'static';
    }

    /**
     * returns the closest, non-statically positioned parentOffset of a given element
     * @param element
     */
    var parentOffsetEl = function (element) {
        var docDomEl = $document[0];
        var offsetParent = element.offsetParent || docDomEl;
        while (offsetParent && offsetParent !== docDomEl && isStaticPositioned(offsetParent)) {
            offsetParent = offsetParent.offsetParent;
        }
        return offsetParent || docDomEl;
    };

    return {
        /**
         * Provides read-only equivalent of jQuery's position function:
         * http://api.jquery.com/position/
         */
        position: function (element) {
            var elBCR = this.offset(element);
            var offsetParentBCR = {
                top: 0,
                left: 0
            };
            var offsetParentEl = parentOffsetEl(element[0]);
            if (offsetParentEl != $document[0]) {
                offsetParentBCR = this.offset(angular.element(offsetParentEl));
                offsetParentBCR.top += offsetParentEl.clientTop - offsetParentEl.scrollTop;
                offsetParentBCR.left += offsetParentEl.clientLeft - offsetParentEl.scrollLeft;
            }

            var boundingClientRect = element[0].getBoundingClientRect();
            return {
                width: boundingClientRect.width || element.prop('offsetWidth'),
                height: boundingClientRect.height || element.prop('offsetHeight'),
                top: elBCR.top - offsetParentBCR.top,
                left: elBCR.left - offsetParentBCR.left
            };
        },

        /**
         * Provides read-only equivalent of jQuery's offset function:
         * http://api.jquery.com/offset/
         */
        offset: function (element) {
            var boundingClientRect = element[0].getBoundingClientRect();
            return {
                width: boundingClientRect.width || element.prop('offsetWidth'),
                height: boundingClientRect.height || element.prop('offsetHeight'),
                top: boundingClientRect.top + ($window.pageYOffset || $document[0].documentElement.scrollTop),
                left: boundingClientRect.left + ($window.pageXOffset || $document[0].documentElement.scrollLeft)
            };
        },

        /**
         * Provides coordinates for the targetEl in relation to hostEl
         */
        positionElements: function (hostEl, targetEl, positionStr, appendToBody) {

            var positionStrParts = positionStr.split('-');
            var pos0 = positionStrParts[0],
                pos1 = positionStrParts[1] || 'center';

            var hostElPos,
                targetElWidth,
                targetElHeight,
                targetElPos;

            hostElPos = appendToBody ? this.offset(hostEl) : this.position(hostEl);

            targetElWidth = targetEl.prop('offsetWidth');
            targetElHeight = targetEl.prop('offsetHeight');

            var shiftWidth = {
                center: function () {
                    return hostElPos.left + hostElPos.width / 2 - targetElWidth / 2;
                },
                left: function () {
                    return hostElPos.left;
                },
                right: function () {
                    return hostElPos.left + hostElPos.width;
                }
            };

            var shiftHeight = {
                center: function () {
                    return hostElPos.top + hostElPos.height / 2 - targetElHeight / 2;
                },
                top: function () {
                    return hostElPos.top;
                },
                bottom: function () {
                    return hostElPos.top + hostElPos.height;
                }
            };

            switch (pos0) {
            case 'right':
                targetElPos = {
                    top: shiftHeight[pos1](),
                    left: shiftWidth[pos0]()
                };
                break;
            case 'left':
                targetElPos = {
                    top: shiftHeight[pos1](),
                    left: hostElPos.left - targetElWidth
                };
                break;
            case 'bottom':
                targetElPos = {
                    top: shiftHeight[pos0](),
                    left: shiftWidth[pos1]()
                };
                break;
            default:
                targetElPos = {
                    top: hostElPos.top - targetElHeight,
                    left: shiftWidth[pos1]()
                };
                break;
            }

            return targetElPos;
        }
    };
}]);

angular.module('ui.bootstrap.datepicker', ['ui.bootstrap.dateparser', 'ui.bootstrap.position'])

.constant('datepickerConfig', {
    formatDay: 'dd',
    formatMonth: 'MMMM',
    formatYear: 'yyyy',
    formatDayHeader: 'EEE',
    formatDayTitle: 'MMMM yyyy',
    formatMonthTitle: 'yyyy',
    datepickerMode: 'day',
    minMode: 'day',
    maxMode: 'year',
    showWeeks: true,
    startingDay: 0,
    yearRange: 20,
    minDate: null,
    maxDate: null
})

.controller('DatepickerController', ['$scope', '$attrs', '$parse', '$interpolate', '$timeout', '$log', 'dateFilter', 'datepickerConfig', function ($scope, $attrs, $parse, $interpolate, $timeout, $log, dateFilter, datepickerConfig) {
    var self = this,
        ngModelCtrl = {
            $setViewValue: angular.noop
        }; // nullModelCtrl;

    // Modes chain
    this.modes = ['day', 'month', 'year'];

    // Configuration attributes
    angular.forEach(['formatDay', 'formatMonth', 'formatYear', 'formatDayHeader', 'formatDayTitle', 'formatMonthTitle',
        'minMode', 'maxMode', 'showWeeks', 'startingDay', 'yearRange'
    ], function (key, index) {
        self[key] = angular.isDefined($attrs[key]) ? (index < 8 ? $interpolate($attrs[key])($scope.$parent) : $scope.$parent.$eval($attrs[key])) : datepickerConfig[key];
    });

    // Watchable date attributes
    angular.forEach(['minDate', 'maxDate'], function (key) {
        if ($attrs[key]) {
            $scope.$parent.$watch($parse($attrs[key]), function (value) {
                self[key] = value ? new Date(value) : null;
                self.refreshView();
            });
        } else {
            self[key] = datepickerConfig[key] ? new Date(datepickerConfig[key]) : null;
        }
    });

    $scope.datepickerMode = $scope.datepickerMode || datepickerConfig.datepickerMode;
    $scope.uniqueId = 'datepicker-' + $scope.$id + '-' + Math.floor(Math.random() * 10000);
    this.activeDate = angular.isDefined($attrs.initDate) ? $scope.$parent.$eval($attrs.initDate) : new Date();

    $scope.isActive = function (dateObject) {
        if (self.compare(dateObject.date, self.activeDate) === 0) {
            $scope.activeDateId = dateObject.uid;
            return true;
        }
        return false;
    };

    this.init = function (ngModelCtrl_) {
        ngModelCtrl = ngModelCtrl_;

        ngModelCtrl.$render = function () {
            self.render();
        };
    };

    this.render = function () {
        if (ngModelCtrl.$modelValue) {
            var date = new Date(ngModelCtrl.$modelValue),
                isValid = !isNaN(date);

            if (isValid) {
                this.activeDate = date;
            } else {
                $log.error('Datepicker directive: "ng-model" value must be a Date object, a number of milliseconds since 01.01.1970 or a string representing an RFC2822 or ISO 8601 date.');
            }
            ngModelCtrl.$setValidity('date', isValid);
        }
        this.refreshView();
    };

    this.refreshView = function () {
        if (this.element) {
            this._refreshView();

            var date = ngModelCtrl.$modelValue ? new Date(ngModelCtrl.$modelValue) : null;
            ngModelCtrl.$setValidity('date-disabled', !date || (this.element && !this.isDisabled(date)));
        }
    };

    this.createDateObject = function (date, format) {
        var model = ngModelCtrl.$modelValue ? new Date(ngModelCtrl.$modelValue) : null;
        return {
            date: date,
            label: dateFilter(date, format),
            selected: model && this.compare(date, model) === 0,
            disabled: this.isDisabled(date),
            current: this.compare(date, new Date()) === 0
        };
    };

    this.isDisabled = function (date) {
        return ((this.minDate && this.compare(date, this.minDate) < 0) || (this.maxDate && this.compare(date, this.maxDate) > 0) || ($attrs.dateDisabled && $scope.dateDisabled({
            date: date,
            mode: $scope.datepickerMode
        })));
    };

    // Split array into smaller arrays
    this.split = function (arr, size) {
        var arrays = [];
        while (arr.length > 0) {
            arrays.push(arr.splice(0, size));
        }
        return arrays;
    };

    $scope.select = function (date) {
        if ($scope.datepickerMode === self.minMode) {
            var dt = ngModelCtrl.$modelValue ? new Date(ngModelCtrl.$modelValue) : new Date(0, 0, 0, 0, 0, 0, 0);
            dt.setFullYear(date.getFullYear(), date.getMonth(), date.getDate());
            ngModelCtrl.$setViewValue(dt);
            ngModelCtrl.$render();
        } else {
            self.activeDate = date;
            $scope.datepickerMode = self.modes[self.modes.indexOf($scope.datepickerMode) - 1];
        }
    };

    $scope.move = function (direction) {
        var year = self.activeDate.getFullYear() + direction * (self.step.years || 0),
            month = self.activeDate.getMonth() + direction * (self.step.months || 0);
        self.activeDate.setFullYear(year, month, 1);
        self.refreshView();
    };

    $scope.toggleMode = function (direction) {
        direction = direction || 1;

        if (($scope.datepickerMode === self.maxMode && direction === 1) || ($scope.datepickerMode === self.minMode && direction === -1)) {
            return;
        }

        $scope.datepickerMode = self.modes[self.modes.indexOf($scope.datepickerMode) + direction];
    };

    // Key event mapper
    $scope.keys = {
        13: 'enter',
        32: 'space',
        33: 'pageup',
        34: 'pagedown',
        35: 'end',
        36: 'home',
        37: 'left',
        38: 'up',
        39: 'right',
        40: 'down'
    };

    var focusElement = function () {
        $timeout(function () {
            self.element[0].focus();
        }, 0, false);
    };

    // Listen for focus requests from popup directive
    $scope.$on('datepicker.focus', focusElement);

    $scope.keydown = function (evt) {
        var key = $scope.keys[evt.which];

        if (!key || evt.shiftKey || evt.altKey) {
            return;
        }

        evt.preventDefault();
        evt.stopPropagation();

        if (key === 'enter' || key === 'space') {
            if (self.isDisabled(self.activeDate)) {
                return; // do nothing
            }
            $scope.select(self.activeDate);
            focusElement();
        } else if (evt.ctrlKey && (key === 'up' || key === 'down')) {
            $scope.toggleMode(key === 'up' ? 1 : -1);
            focusElement();
        } else {
            self.handleKeyDown(key, evt);
            self.refreshView();
        }
    };
}])

.directive('datepicker', function () {
    return {
        restrict: 'EA',
        replace: true,
        templateUrl: 'template/datepicker/datepicker.html',
        scope: {
            datepickerMode: '=?',
            dateDisabled: '&'
        },
        require: ['datepicker', '?^ngModel'],
        controller: 'DatepickerController',
        link: function (scope, element, attrs, ctrls) {
            var datepickerCtrl = ctrls[0],
                ngModelCtrl = ctrls[1];

            if (ngModelCtrl) {
                datepickerCtrl.init(ngModelCtrl);
            }
        }
    };
})

.directive('daypicker', ['dateFilter', function (dateFilter) {
    return {
        restrict: 'EA',
        replace: true,
        templateUrl: 'template/datepicker/day.html',
        require: '^datepicker',
        link: function (scope, element, attrs, ctrl) {
            scope.showWeeks = ctrl.showWeeks;

            ctrl.step = {
                months: 1
            };
            ctrl.element = element;

            var DAYS_IN_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];

            function getDaysInMonth(year, month) {
                return ((month === 1) && (year % 4 === 0) && ((year % 100 !== 0) || (year % 400 === 0))) ? 29 : DAYS_IN_MONTH[month];
            }

            function getDates(startDate, n) {
                var dates = new Array(n),
                    current = new Date(startDate),
                    i = 0;
                current.setHours(12); // Prevent repeated dates because of timezone bug
                while (i < n) {
                    dates[i++] = new Date(current);
                    current.setDate(current.getDate() + 1);
                }
                return dates;
            }

            ctrl._refreshView = function () {
                var year = ctrl.activeDate.getFullYear(),
                    month = ctrl.activeDate.getMonth(),
                    firstDayOfMonth = new Date(year, month, 1),
                    difference = ctrl.startingDay - firstDayOfMonth.getDay(),
                    numDisplayedFromPreviousMonth = (difference > 0) ? 7 - difference : -difference,
                    firstDate = new Date(firstDayOfMonth);

                if (numDisplayedFromPreviousMonth > 0) {
                    firstDate.setDate(-numDisplayedFromPreviousMonth + 1);
                }

                // 42 is the number of days on a six-month calendar
                var days = getDates(firstDate, 42);
                for (var i = 0; i < 42; i++) {
                    days[i] = angular.extend(ctrl.createDateObject(days[i], ctrl.formatDay), {
                        secondary: days[i].getMonth() !== month,
                        uid: scope.uniqueId + '-' + i
                    });
                }

                scope.labels = new Array(7);
                for (var j = 0; j < 7; j++) {
                    scope.labels[j] = {
                        abbr: dateFilter(days[j].date, ctrl.formatDayHeader),
                        full: dateFilter(days[j].date, 'EEEE')
                    };
                }

                scope.title = dateFilter(ctrl.activeDate, ctrl.formatDayTitle);
                scope.rows = ctrl.split(days, 7);

                if (scope.showWeeks) {
                    scope.weekNumbers = [];
                    var weekNumber = getISO8601WeekNumber(scope.rows[0][0].date),
                        numWeeks = scope.rows.length;
                    while (scope.weekNumbers.push(weekNumber++) < numWeeks) {}
                }
            };

            ctrl.compare = function (date1, date2) {
                return (new Date(date1.getFullYear(), date1.getMonth(), date1.getDate()) - new Date(date2.getFullYear(), date2.getMonth(), date2.getDate()));
            };

            function getISO8601WeekNumber(date) {
                var checkDate = new Date(date);
                checkDate.setDate(checkDate.getDate() + 4 - (checkDate.getDay() || 7)); // Thursday
                var time = checkDate.getTime();
                checkDate.setMonth(0); // Compare with Jan 1
                checkDate.setDate(1);
                return Math.floor(Math.round((time - checkDate) / 86400000) / 7) + 1;
            }

            ctrl.handleKeyDown = function (key, evt) {
                var date = ctrl.activeDate.getDate();

                if (key === 'left') {
                    date = date - 1; // up
                } else if (key === 'up') {
                    date = date - 7; // down
                } else if (key === 'right') {
                    date = date + 1; // down
                } else if (key === 'down') {
                    date = date + 7;
                } else if (key === 'pageup' || key === 'pagedown') {
                    var month = ctrl.activeDate.getMonth() + (key === 'pageup' ? -1 : 1);
                    ctrl.activeDate.setMonth(month, 1);
                    date = Math.min(getDaysInMonth(ctrl.activeDate.getFullYear(), ctrl.activeDate.getMonth()), date);
                } else if (key === 'home') {
                    date = 1;
                } else if (key === 'end') {
                    date = getDaysInMonth(ctrl.activeDate.getFullYear(), ctrl.activeDate.getMonth());
                }
                ctrl.activeDate.setDate(date);
            };

            ctrl.refreshView();
        }
    };
}])

.directive('monthpicker', ['dateFilter', function (dateFilter) {
    return {
        restrict: 'EA',
        replace: true,
        templateUrl: 'template/datepicker/month.html',
        require: '^datepicker',
        link: function (scope, element, attrs, ctrl) {
            ctrl.step = {
                years: 1
            };
            ctrl.element = element;

            ctrl._refreshView = function () {
                var months = new Array(12),
                    year = ctrl.activeDate.getFullYear();

                for (var i = 0; i < 12; i++) {
                    months[i] = angular.extend(ctrl.createDateObject(new Date(year, i, 1), ctrl.formatMonth), {
                        uid: scope.uniqueId + '-' + i
                    });
                }

                scope.title = dateFilter(ctrl.activeDate, ctrl.formatMonthTitle);
                scope.rows = ctrl.split(months, 3);
            };

            ctrl.compare = function (date1, date2) {
                return new Date(date1.getFullYear(), date1.getMonth()) - new Date(date2.getFullYear(), date2.getMonth());
            };

            ctrl.handleKeyDown = function (key, evt) {
                var date = ctrl.activeDate.getMonth();

                if (key === 'left') {
                    date = date - 1; // up
                } else if (key === 'up') {
                    date = date - 3; // down
                } else if (key === 'right') {
                    date = date + 1; // down
                } else if (key === 'down') {
                    date = date + 3;
                } else if (key === 'pageup' || key === 'pagedown') {
                    var year = ctrl.activeDate.getFullYear() + (key === 'pageup' ? -1 : 1);
                    ctrl.activeDate.setFullYear(year);
                } else if (key === 'home') {
                    date = 0;
                } else if (key === 'end') {
                    date = 11;
                }
                ctrl.activeDate.setMonth(date);
            };

            ctrl.refreshView();
        }
    };
}])

.directive('yearpicker', ['dateFilter', function (dateFilter) {
    return {
        restrict: 'EA',
        replace: true,
        templateUrl: 'template/datepicker/year.html',
        require: '^datepicker',
        link: function (scope, element, attrs, ctrl) {
            var range = ctrl.yearRange;

            ctrl.step = {
                years: range
            };
            ctrl.element = element;

            function getStartingYear(year) {
                return parseInt((year - 1) / range, 10) * range + 1;
            }

            ctrl._refreshView = function () {
                var years = new Array(range);

                for (var i = 0, start = getStartingYear(ctrl.activeDate.getFullYear()); i < range; i++) {
                    years[i] = angular.extend(ctrl.createDateObject(new Date(start + i, 0, 1), ctrl.formatYear), {
                        uid: scope.uniqueId + '-' + i
                    });
                }

                scope.title = [years[0].label, years[range - 1].label].join(' - ');
                scope.rows = ctrl.split(years, 5);
            };

            ctrl.compare = function (date1, date2) {
                return date1.getFullYear() - date2.getFullYear();
            };

            ctrl.handleKeyDown = function (key, evt) {
                var date = ctrl.activeDate.getFullYear();

                if (key === 'left') {
                    date = date - 1; // up
                } else if (key === 'up') {
                    date = date - 5; // down
                } else if (key === 'right') {
                    date = date + 1; // down
                } else if (key === 'down') {
                    date = date + 5;
                } else if (key === 'pageup' || key === 'pagedown') {
                    date += (key === 'pageup' ? -1 : 1) * ctrl.step.years;
                } else if (key === 'home') {
                    date = getStartingYear(ctrl.activeDate.getFullYear());
                } else if (key === 'end') {
                    date = getStartingYear(ctrl.activeDate.getFullYear()) + range - 1;
                }
                ctrl.activeDate.setFullYear(date);
            };

            ctrl.refreshView();
        }
    };
}])

.constant('datepickerPopupConfig', {
    datepickerPopup: 'yyyy-MM-dd',
    currentText: 'Today',
    clearText: 'Clear',
    closeText: 'Done',
    closeOnDateSelection: true,
    appendToBody: false,
    showButtonBar: true
})

.directive('datepickerPopup', ['$compile', '$parse', '$document', '$position', 'dateFilter', 'dateParser', 'datepickerPopupConfig',
    function ($compile, $parse, $document, $position, dateFilter, dateParser, datepickerPopupConfig) {
        return {
            restrict: 'EA',
            require: 'ngModel',
            scope: {
                isOpen: '=?',
                currentText: '@',
                clearText: '@',
                closeText: '@',
                dateDisabled: '&'
            },
            link: function (scope, element, attrs, ngModel) {
                var dateFormat,
                    closeOnDateSelection = angular.isDefined(attrs.closeOnDateSelection) ? scope.$parent.$eval(attrs.closeOnDateSelection) : datepickerPopupConfig.closeOnDateSelection,
                    appendToBody = angular.isDefined(attrs.datepickerAppendToBody) ? scope.$parent.$eval(attrs.datepickerAppendToBody) : datepickerPopupConfig.appendToBody;

                scope.showButtonBar = angular.isDefined(attrs.showButtonBar) ? scope.$parent.$eval(attrs.showButtonBar) : datepickerPopupConfig.showButtonBar;

                scope.getText = function (key) {
                    return scope[key + 'Text'] || datepickerPopupConfig[key + 'Text'];
                };

                attrs.$observe('datepickerPopup', function (value) {
                    dateFormat = value || datepickerPopupConfig.datepickerPopup;
                    ngModel.$render();
                });

                // popup element used to display calendar
                var popupEl = angular.element('<div datepicker-popup-wrap><div datepicker></div></div>');
                popupEl.attr({
                    'ng-model': 'date',
                    'ng-change': 'dateSelection()'
                });

                function cameltoDash(string) {
                    return string.replace(/([A-Z])/g, function ($1) {
                        return '-' + $1.toLowerCase();
                    });
                }

                // datepicker element
                var datepickerEl = angular.element(popupEl.children()[0]);
                if (attrs.datepickerOptions) {
                    angular.forEach(scope.$parent.$eval(attrs.datepickerOptions), function (value, option) {
                        datepickerEl.attr(cameltoDash(option), value);
                    });
                }

                scope.watchData = {};
                angular.forEach(['minDate', 'maxDate', 'datepickerMode'], function (key) {
                    if (attrs[key]) {
                        var getAttribute = $parse(attrs[key]);
                        scope.$parent.$watch(getAttribute, function (value) {
                            scope.watchData[key] = value;
                        });
                        datepickerEl.attr(cameltoDash(key), 'watchData.' + key);

                        // Propagate changes from datepicker to outside
                        if (key === 'datepickerMode') {
                            var setAttribute = getAttribute.assign;
                            scope.$watch('watchData.' + key, function (value, oldvalue) {
                                if (value !== oldvalue) {
                                    setAttribute(scope.$parent, value);
                                }
                            });
                        }
                    }
                });
                if (attrs.dateDisabled) {
                    datepickerEl.attr('date-disabled', 'dateDisabled({ date: date, mode: mode })');
                }

                function parseDate(viewValue) {
                    if (!viewValue) {
                        ngModel.$setValidity('date', true);
                        return null;
                    } else if (angular.isDate(viewValue) && !isNaN(viewValue)) {
                        ngModel.$setValidity('date', true);
                        return viewValue;
                    } else if (angular.isString(viewValue)) {
                        var date = dateParser.parse(viewValue, dateFormat) || new Date(viewValue);
                        if (isNaN(date)) {
                            ngModel.$setValidity('date', false);
                            return undefined;
                        } else {
                            ngModel.$setValidity('date', true);
                            return date;
                        }
                    } else {
                        ngModel.$setValidity('date', false);
                        return undefined;
                    }
                }
                ngModel.$parsers.unshift(parseDate);

                // Inner change
                scope.dateSelection = function (dt) {
                    if (angular.isDefined(dt)) {
                        scope.date = dt;
                    }
                    ngModel.$setViewValue(scope.date);
                    ngModel.$render();

                    if (closeOnDateSelection) {
                        scope.isOpen = false;
                        element[0].focus();
                    }
                };

                element.bind('input change keyup', function () {
                    scope.$apply(function () {
                        scope.date = ngModel.$modelValue;
                    });
                });

                // Outter change
                ngModel.$render = function () {
                    var date = ngModel.$viewValue ? dateFilter(ngModel.$viewValue, dateFormat) : '';
                    element.val(date);
                    scope.date = parseDate(ngModel.$modelValue);
                };

                var documentClickBind = function (event) {
                    if (scope.isOpen && event.target !== element[0]) {
                        scope.$apply(function () {
                            scope.isOpen = false;
                        });
                    }
                };

                var keydown = function (evt, noApply) {
                    scope.keydown(evt);
                };
                element.bind('keydown', keydown);

                scope.keydown = function (evt) {
                    if (evt.which === 27) {
                        evt.preventDefault();
                        evt.stopPropagation();
                        scope.close();
                    } else if (evt.which === 40 && !scope.isOpen) {
                        scope.isOpen = true;
                    }
                };

                scope.$watch('isOpen', function (value) {
                    if (value) {
                        scope.$broadcast('datepicker.focus');
                        scope.position = appendToBody ? $position.offset(element) : $position.position(element);
                        scope.position.top = scope.position.top + element.prop('offsetHeight');

                        $document.bind('click', documentClickBind);
                    } else {
                        $document.unbind('click', documentClickBind);
                    }
                });

                scope.select = function (date) {
                    if (date === 'today') {
                        var today = new Date();
                        if (angular.isDate(ngModel.$modelValue)) {
                            date = new Date(ngModel.$modelValue);
                            date.setFullYear(today.getFullYear(), today.getMonth(), today.getDate());
                        } else {
                            date = new Date(today.setHours(0, 0, 0, 0));
                        }
                    }
                    scope.dateSelection(date);
                };

                scope.close = function () {
                    scope.isOpen = false;
                    element[0].focus();
                };

                var $popup = $compile(popupEl)(scope);
                // Prevent jQuery cache memory leak (template is now redundant after linking)
                popupEl.remove();

                if (appendToBody) {
                    $document.find('body').append($popup);
                } else {
                    element.after($popup);
                }

                scope.$on('$destroy', function () {
                    $popup.remove();
                    element.unbind('keydown', keydown);
                    $document.unbind('click', documentClickBind);
                });
            }
        };
    }
])

.directive('datepickerPopupWrap', function () {
    return {
        restrict: 'EA',
        replace: true,
        transclude: true,
        templateUrl: 'template/datepicker/popup.html',
        link: function (scope, element, attrs) {
            element.bind('click', function (event) {
                event.preventDefault();
                event.stopPropagation();
            });
        }
    };
});

angular.module('ui.bootstrap.modal', ['ui.bootstrap.transition'])

/**
 * A helper, internal data structure that acts as a map but also allows getting / removing
 * elements in the LIFO order
 */
.factory('$$stackedMap', function () {
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
        templateUrl: 'template/modal/backdrop.html',
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
                inDirection: '=',
                outDirection: '='
            },
            replace: true,
            transclude: true,
            templateUrl: function (tElement, tAttrs) {
                return tAttrs.templateUrl || 'template/modal/window.html';
            },
            link: function (scope, element, attrs) {
                var clickElement; // how to pass $event? .data() ?
                element.addClass(attrs.windowClass || '');
                scope.size = attrs.size;
                $timeout(function () {
                    // trigger CSS transitions
                    if (clickElement) {
                        var clickRect = clickElement[0].getBoundingClientRect();
                        var dialogRect = element[0].getBoundingClientRect();
                        var scaleX = Math.min(0.5, clickRect.width / dialogRect.width);
                        var scaleY = Math.min(0.5, clickRect.height / dialogRect.height);

                        element.css($mdConstant.CSS.TRANSFORM, 'translate3d(' +
                            (-dialogRect.left + clickRect.left + clickRect.width / 2 - dialogRect.width / 2) + 'px,' +
                            (-dialogRect.top + clickRect.top + clickRect.height / 2 - dialogRect.height / 2) + 'px,' +
                            '0) scale(' + scaleX + ',' + scaleY + ')'
                        );
                    } else {
                        if (scope.inDirection) {
                            element.css($mdConstant.CSS.TRANSFORM, 'translate3d(' + (scope.inDirection === 'right' ? '' : '-') + '100%, 0px, 0px)');
                        }
                    }
                    element.addClass('visible');
                    if (scope.inDirection) {
                        var cb = function () {
                            element.addClass('transition-in-' + scope.inDirection)
                                .css($mdConstant.CSS.TRANSFORM, '');
                        };
                    } else {
                        var cb = function () {
                            element.addClass('transition-in')
                                .css($mdConstant.CSS.TRANSFORM, '');
                        };
                    }

                    $$rAF(cb);

                    var deferred = $q.defer();
                    element.on($mdConstant.CSS.TRANSITIONEND, finished);

                    function finished(ev) {
                        //Make sure this transitionend didn't bubble up from a child
                        if (ev.target === element[0]) {
                            element.off($mdConstant.CSS.TRANSITIONEND, finished);
                            deferred.resolve();
                        }
                    }

                    $(window).triggerHandler('modal.open');

                    /**
                     * Auto-focusing of a freshly-opened modal element causes any child elements
                     * with the autofocus attribute to loose focus. This is an issue on touch
                     * based devices which will show and then hide the onscreen keyboard.
                     * Attempts to refocus the autofocus element via JavaScript will not reopen
                     * the onscreen keyboard. Fixed by updated the focusing logic to only autofocus
                     * the modal element if the modal does not contain an autofocus element.
                     */
                    deferred.promise.then(function () {
                        if (!element[0].querySelectorAll('[autofocus]').length) {
                            element[0].focus();
                        }
                        $(window).triggerHandler('modal.visible');
                    });

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

.factory('$modalStack', ['$transition', '$timeout', '$document', '$compile', '$rootScope', '$$stackedMap', 'mdEscFactory',
    '$mdConstant',
    function ($transition, $timeout, $document, $compile, $rootScope, $$stackedMap, mdEscFactory, $mdConstant) {

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
            var dialogEl = domEl,
                clickElement;

            if (!clickElement && scope.inDirection) {
                dialogEl.addClass('transition-out-' + scope.outDirection).removeClass('transition-in-' + scope.inDirection)
                    .css($mdConstant.CSS.TRANSFORM, 'translate3d(' + (scope.inDirection === 'right' ? '-' : '') + '100%, 0px, 0px)');
            } else {
                dialogEl.addClass('transition-out').removeClass('transition-in');
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

            dialogEl.on($mdConstant.CSS.TRANSITIONEND, afterAnimating);

            function afterAnimating(ev) {
                if (ev.target !== dialogEl[0]) {
                    return;
                }
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

        $modalStack.open = function (modalInstance, modal) {

            openedWindows.add(modalInstance, {
                deferred: modal.deferred,
                modalScope: modal.scope,
                backdrop: modal.backdrop,
                keyboard: modal.keyboard
            });

            modal.scope.inDirection = modal.inDirection;
            modal.scope.outDirection = modal.outDirection;

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

            var angularDomEl = angular.element('<div modal-window></div>');

            angularDomEl.attr({
                'template-url': modal.windowTemplateUrl,
                'window-class': modal.windowClass,
                'size': modal.size,
                'index': openedWindows.length() - 1,
                'in-direction': 'inDirection',
                'out-direction': 'outDirection',
                'animate': 'animate',
                'exiting': 'exiting'
            }).html(modal.content);

            var modalDomEl = $compile(angularDomEl)(modal.scope);
            openedWindows.top().value.modalDomEl = modalDomEl;
            body.append(modalDomEl);
            body.addClass(OPENED_MODAL_CLASS);

            if (modal.keyboard) {
                var esc = function (e) {
                    e.preventDefault();
                    $rootScope.$apply(function () {
                        modalInstance.withEscape = true;
                        $modalStack.dismiss(modalInstance, 'escape key press');
                    });
                    return true;
                };
                modalInstance.esc = esc;
                mdEscFactory.queue(esc);
            }
            
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
                mdEscFactory.dequeue(modalInstance.esc);
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
            keyboard: true,
            inDirection: 'right',
            outDirection: 'left'
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
                            keyboard: modalOptions.keyboard,
                            backdropClass: modalOptions.backdropClass,
                            windowClass: modalOptions.windowClass,
                            windowTemplateUrl: modalOptions.windowTemplateUrl,
                            size: modalOptions.size,
                            inDirection: modalOptions.inDirection,
                            outDirection: modalOptions.outDirection
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
});

angular.module('ui.bootstrap.timepicker', [])

.constant('timepickerConfig', {
    hourStep: 1,
    minuteStep: 1,
    showMeridian: true,
    meridians: null,
    readonlyInput: false,
    mousewheel: true
})

.controller('TimepickerController', ['$scope', '$attrs', '$parse', '$log', '$locale', 'timepickerConfig', function ($scope, $attrs, $parse, $log, $locale, timepickerConfig) {
    var selected = new Date(),
        ngModelCtrl = {
            $setViewValue: angular.noop
        }, // nullModelCtrl
        meridians = angular.isDefined($attrs.meridians) ? $scope.$parent.$eval($attrs.meridians) : timepickerConfig.meridians || $locale.DATETIME_FORMATS.AMPMS;

    this.init = function (ngModelCtrl_, inputs) {
        ngModelCtrl = ngModelCtrl_;
        ngModelCtrl.$render = this.render;

        var hoursInputEl = inputs.eq(0),
            minutesInputEl = inputs.eq(1);

        var mousewheel = angular.isDefined($attrs.mousewheel) ? $scope.$parent.$eval($attrs.mousewheel) : timepickerConfig.mousewheel;
        if (mousewheel) {
            this.setupMousewheelEvents(hoursInputEl, minutesInputEl);
        }

        $scope.readonlyInput = angular.isDefined($attrs.readonlyInput) ? $scope.$parent.$eval($attrs.readonlyInput) : timepickerConfig.readonlyInput;
        this.setupInputEvents(hoursInputEl, minutesInputEl);
    };

    var hourStep = timepickerConfig.hourStep;
    if ($attrs.hourStep) {
        $scope.$parent.$watch($parse($attrs.hourStep), function (value) {
            hourStep = parseInt(value, 10);
        });
    }

    var minuteStep = timepickerConfig.minuteStep;
    if ($attrs.minuteStep) {
        $scope.$parent.$watch($parse($attrs.minuteStep), function (value) {
            minuteStep = parseInt(value, 10);
        });
    }

    // 12H / 24H mode
    $scope.showMeridian = timepickerConfig.showMeridian;
    if ($attrs.showMeridian) {
        $scope.$parent.$watch($parse($attrs.showMeridian), function (value) {
            $scope.showMeridian = !!value;

            if (ngModelCtrl.$error.time) {
                // Evaluate from template
                var hours = getHoursFromTemplate(),
                    minutes = getMinutesFromTemplate();
                if (angular.isDefined(hours) && angular.isDefined(minutes)) {
                    selected.setHours(hours);
                    refresh();
                }
            } else {
                updateTemplate();
            }
        });
    }

    // Get $scope.hours in 24H mode if valid
    function getHoursFromTemplate() {
        var hours = parseInt($scope.hours, 10);
        var valid = ($scope.showMeridian) ? (hours > 0 && hours < 13) : (hours >= 0 && hours < 24);
        if (!valid) {
            return undefined;
        }

        if ($scope.showMeridian) {
            if (hours === 12) {
                hours = 0;
            }
            if ($scope.meridian === meridians[1]) {
                hours = hours + 12;
            }
        }
        return hours;
    }

    function getMinutesFromTemplate() {
        var minutes = parseInt($scope.minutes, 10);
        return (minutes >= 0 && minutes < 60) ? minutes : undefined;
    }

    function pad(value) {
        return (angular.isDefined(value) && value.toString().length < 2) ? '0' + value : value;
    }

    // Respond on mousewheel spin
    this.setupMousewheelEvents = function (hoursInputEl, minutesInputEl) {
        var isScrollingUp = function (e) {
            if (e.originalEvent) {
                e = e.originalEvent;
            }
            //pick correct delta variable depending on event
            var delta = (e.wheelDelta) ? e.wheelDelta : -e.deltaY;
            return (e.detail || delta > 0);
        };

        hoursInputEl.bind('mousewheel wheel', function (e) {
            $scope.$apply((isScrollingUp(e)) ? $scope.incrementHours() : $scope.decrementHours());
            e.preventDefault();
        });

        minutesInputEl.bind('mousewheel wheel', function (e) {
            $scope.$apply((isScrollingUp(e)) ? $scope.incrementMinutes() : $scope.decrementMinutes());
            e.preventDefault();
        });

    };

    this.setupInputEvents = function (hoursInputEl, minutesInputEl) {
        if ($scope.readonlyInput) {
            $scope.updateHours = angular.noop;
            $scope.updateMinutes = angular.noop;
            return;
        }

        var invalidate = function (invalidHours, invalidMinutes) {
            ngModelCtrl.$setViewValue(null);
            ngModelCtrl.$setValidity('time', false);
            if (angular.isDefined(invalidHours)) {
                $scope.invalidHours = invalidHours;
            }
            if (angular.isDefined(invalidMinutes)) {
                $scope.invalidMinutes = invalidMinutes;
            }
        };

        $scope.updateHours = function () {
            var hours = getHoursFromTemplate();

            if (angular.isDefined(hours)) {
                selected.setHours(hours);
                refresh('h');
            } else {
                invalidate(true);
            }
        };

        hoursInputEl.bind('blur', function (e) {
            if (!$scope.invalidHours && $scope.hours < 10) {
                $scope.$apply(function () {
                    $scope.hours = pad($scope.hours);
                });
            }
        });

        $scope.updateMinutes = function () {
            var minutes = getMinutesFromTemplate();

            if (angular.isDefined(minutes)) {
                selected.setMinutes(minutes);
                refresh('m');
            } else {
                invalidate(undefined, true);
            }
        };

        minutesInputEl.bind('blur', function (e) {
            if (!$scope.invalidMinutes && $scope.minutes < 10) {
                $scope.$apply(function () {
                    $scope.minutes = pad($scope.minutes);
                });
            }
        });

    };

    this.render = function () {
        var date = ngModelCtrl.$modelValue ? new Date(ngModelCtrl.$modelValue) : null;

        if (isNaN(date)) {
            ngModelCtrl.$setValidity('time', false);
            $log.error('Timepicker directive: "ng-model" value must be a Date object, a number of milliseconds since 01.01.1970 or a string representing an RFC2822 or ISO 8601 date.');
        } else {
            if (date) {
                selected = date;
            }
            makeValid();
            updateTemplate();
        }
    };

    // Call internally when we know that model is valid.
    function refresh(keyboardChange) {
        makeValid();
        ngModelCtrl.$setViewValue(new Date(selected));
        updateTemplate(keyboardChange);
    }

    function makeValid() {
        ngModelCtrl.$setValidity('time', true);
        $scope.invalidHours = false;
        $scope.invalidMinutes = false;
    }

    function updateTemplate(keyboardChange) {
        var hours = selected.getHours(),
            minutes = selected.getMinutes();

        if ($scope.showMeridian) {
            hours = (hours === 0 || hours === 12) ? 12 : hours % 12; // Convert 24 to 12 hour system
        }

        $scope.hours = keyboardChange === 'h' ? hours : pad(hours);
        $scope.minutes = keyboardChange === 'm' ? minutes : pad(minutes);
        $scope.meridian = selected.getHours() < 12 ? meridians[0] : meridians[1];
    }

    function addMinutes(minutes) {
        var dt = new Date(selected.getTime() + minutes * 60000);
        selected.setHours(dt.getHours(), dt.getMinutes());
        refresh();
    }

    $scope.incrementHours = function () {
        addMinutes(hourStep * 60);
    };
    $scope.decrementHours = function () {
        addMinutes(-hourStep * 60);
    };
    $scope.incrementMinutes = function () {
        addMinutes(minuteStep);
    };
    $scope.decrementMinutes = function () {
        addMinutes(-minuteStep);
    };
    $scope.toggleMeridian = function () {
        addMinutes(12 * 60 * ((selected.getHours() < 12) ? 1 : -1));
    };
}])

.directive('timepicker', function () {
    return {
        restrict: 'EA',
        require: ['timepicker', '?^ngModel'],
        controller: 'TimepickerController',
        replace: true,
        scope: {},
        templateUrl: 'template/timepicker/timepicker.html',
        link: function (scope, element, attrs, ctrls) {
            var timepickerCtrl = ctrls[0],
                ngModelCtrl = ctrls[1];

            if (ngModelCtrl) {
                timepickerCtrl.init(ngModelCtrl, element.find('input'));
            }
        }
    };
});
