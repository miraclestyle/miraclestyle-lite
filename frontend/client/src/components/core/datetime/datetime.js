(function () {
    'use strict';

    angular.module('app')
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
        }])
        .directive('timeDatePicker', [
            '$filter', '$sce', '$rootScope', '$parse',
            function ($filter, $sce, $rootScope, $parse) {
                var _dateFilter;
                _dateFilter = $filter('date');
                return {
                    restrict: 'AE',
                    replace: true,
                    scope: {
                        _modelValue: '=ngModel'
                    },
                    require: 'ngModel',
                    templateUrl: 'core/datetime/input.html',
                    link: function (scope, element, attrs, ngModel) {
                        var cancelFn, saveFn;
                        attrs.$observe('defaultMode', function (val) {
                            return scope._mode = val != null ? val : 'date';
                        });
                        attrs.$observe('displayMode', function (val) {
                            return scope._displayMode = val;
                        });
                        attrs.$observe('orientation', function (val) {
                            return scope._verticalMode = val === 'true';
                        });
                        attrs.$observe('displayTwentyfour', function (val) {
                            return scope._hours24 = (val != null) && val;
                        });
                        attrs.$observe('mindate', function (val) {
                            if ((val != null) && angular.isDate(val)) {
                                return scope.restrictions.mindate = val;
                            }
                        });
                        attrs.$observe('maxdate', function (val) {
                            if ((val != null) && angular.isDate(val)) {
                                return scope.restrictions.maxdate = val;
                            }
                        });
                        ngModel.$render = function () {
                            return scope.setDate(ngModel.$modelValue);
                        };
                        saveFn = $parse(attrs.onSave);
                        cancelFn = $parse(attrs.onCancel);
                        scope.save = function () {
                            scope._modelValue = scope.date;
                            ngModel.$setDirty();
                            return saveFn(scope.$parent, {
                                $value: scope.date
                            });
                        };
                        return scope.cancel = function () {
                            cancelFn(scope.$parent, {});
                            return ngModel.$render();
                        };
                    },
                    controller: [
                        '$scope',
                        function (scope) {
                            var i;
                            scope.restrictions = {
                                mindate: void 0,
                                maxdate: void 0
                            };
                            scope.setDate = function (newVal) {
                                scope.date = newVal != null ? new Date(newVal) : new Date();
                                scope.calendar._year = scope.date.getFullYear();
                                scope.calendar._month = scope.date.getMonth();
                                scope.clock._minutes = scope.date.getMinutes();
                                scope.clock._hours = scope._hours24 ? scope.date.getHours() : scope.date.getHours() % 12;
                                if (!scope._hours24 && scope.clock._hours === 0) {
                                    return scope.clock._hours = 12;
                                }
                            };
                            scope.display = {
                                fullTitle: function () {
                                    return _dateFilter(scope.date, 'EEEE d MMMM yyyy, h:mm a');
                                },
                                title: function () {
                                    if (scope._mode === 'date') {
                                        return _dateFilter(scope.date, (scope._displayMode === 'date' ? 'EEEE' : 'EEEE h:mm a'));
                                    } else {
                                        return _dateFilter(scope.date, 'MMMM d yyyy');
                                    }
                                },
                                "super": function () {
                                    if (scope._mode === 'date') {
                                        return _dateFilter(scope.date, 'MMM');
                                    } else {
                                        return '';
                                    }
                                },
                                main: function () {
                                    return $sce.trustAsHtml(scope._mode === 'date' ? _dateFilter(scope.date, 'd') : "" + (_dateFilter(scope.date, 'h:mm')) + "<small>" + (_dateFilter(scope.date, 'a')) + "</small>");
                                },
                                sub: function () {
                                    if (scope._mode === 'date') {
                                        return _dateFilter(scope.date, 'yyyy');
                                    } else {
                                        return _dateFilter(scope.date, 'HH:mm');
                                    }
                                }
                            };
                            scope.calendar = {
                                _month: 0,
                                _year: 0,
                                _months: (function () {
                                    var _i, _results;
                                    _results = [];
                                    for (i = _i = 0; _i <= 11; i = ++_i) {
                                        _results.push(_dateFilter(new Date(0, i), 'MMMM'));
                                    }
                                    return _results;
                                })(),
                                offsetMargin: function () {
                                    return new Date(this._year, this._month).getDay();
                                },
                                isVisible: function (d) {
                                    return new Date(this._year, this._month, d).getMonth() === this._month;
                                },
                                "class": function (d) {
                                    if ((scope.date != null) && new Date(this._year, this._month, d).getTime() === new Date(scope.date.getTime()).setHours(0, 0, 0, 0)) {
                                        return "selected";
                                    } else if (new Date(this._year, this._month, d).getTime() === new Date().setHours(0, 0, 0, 0)) {
                                        return "today";
                                    } else {
                                        return "";
                                    }
                                },
                                select: function (d) {
                                    var sets = scope.date.setFullYear(this._year, this._month, d);
                                    scope.save();
                                    return sets;
                                },
                                monthChange: function () {
                                    if ((this._year == null) || isNaN(this._year)) {
                                        this._year = new Date().getFullYear();
                                    }
                                    scope.date.setFullYear(this._year, this._month);
                                    if (scope.date.getMonth() !== this._month) {
                                        return scope.date.setDate(0);
                                    }
                                },
                                _incMonth: function (months) {
                                    this._month += months;
                                    while (this._month < 0 || this._month > 11) {
                                        if (this._month < 0) {
                                            this._month += 12;
                                            this._year--;
                                        } else {
                                            this._month -= 12;
                                            this._year++;
                                        }
                                    }
                                    return this.monthChange();
                                }
                            };
                            scope.clock = {
                                _minutes: 0,
                                _hours: 0,
                                _incHours: function (inc) {
                                    this._hours = scope._hours24 ? Math.max(0, Math.min(23, this._hours + inc)) : Math.max(1, Math.min(12, this._hours + inc));
                                    if (isNaN(this._hours)) {
                                        return this._hours = 0;
                                    }
                                },
                                _incMinutes: function (inc) {
                                    this._minutes = Math.max(0, Math.min(59, this._minutes + inc));
                                    if (isNaN(this._minutes)) {
                                        return this._minutes = 0;
                                    }
                                },
                                setAM: function (b) {
                                    if (b == null) {
                                        b = !this.isAM();
                                    }
                                    if (b && !this.isAM()) {
                                        return scope.date.setHours(scope.date.getHours() - 12);
                                    } else if (!b && this.isAM()) {
                                        return scope.date.setHours(scope.date.getHours() + 12);
                                    }
                                },
                                isAM: function () {
                                    return scope.date.getHours() < 12;
                                }
                            };
                            scope.$watch('clock._minutes', function (val, oldVal) {
                                if ((val != null) && val !== scope.date.getMinutes() && !isNaN(val) && (0 <= val && val <= 59)) {
                                    var sets = scope.date.setMinutes(val);
                                    sets = scope.date.setSeconds(0);
                                    scope.save();
                                    return sets;
                                }
                            });
                            scope.$watch('clock._hours', function (val) {
                                if ((val != null) && !isNaN(val)) {
                                    if (!scope._hours24) {
                                        if (val === 24) {
                                            val = 12;
                                        } else if (val === 12) {
                                            val = 0;
                                        } else if (!scope.clock.isAM()) {
                                            val += 12;
                                        }
                                    }
                                    if (val !== scope.date.getHours()) {
                                        var sets = scope.date.setHours(val);
                                        scope.save();
                                        return sets;
                                    }
                                }
                            });
                            scope.setNow = function () {
                                return scope.setDate();
                            };
                            scope._mode = 'date';
                            scope.modeClass = function () {
                                if (scope._displayMode != null) {
                                    scope._mode = scope._displayMode;
                                }
                                return "" + ((scope._verticalMode != null) && scope._verticalMode ? 'vertical ' : '') + (scope._displayMode === 'full' ? 'full-mode' : scope._displayMode === 'time' ? 'time-only' : scope._displayMode === 'date' ? 'date-only' : scope._mode === 'date' ? 'date-mode' : 'time-mode');
                            };
                            scope.modeSwitch = function () {
                                var _ref;
                                return scope._mode = (_ref = scope._displayMode) != null ? _ref : scope._mode === 'date' ? 'time' : 'date';
                            };
                            return scope.modeSwitchText = function () {
                                if (scope._mode === 'date') {
                                    return 'Clock';
                                } else {
                                    return 'Calendar';
                                }
                            };
                        }
                    ]
                };
            }
        ]).directive('timeDatePickerDialog', function ($modal, dateFilter, dateParser, GLOBAL_CONFIG) {
            return {
                require: ['ngModel', '^form'],
                link: function (scope, element, attrs, ctrls) {
                    var ngModel = ctrls[0],
                        form = ctrls[1];
                    ngModel.$render = function () {
                        element.val(dateFilter(ngModel.$modelValue, GLOBAL_CONFIG.date.format));
                    };

                    element.on('click', function (event) {
                        $modal.open({
                            windowClass: 'modal-medium',
                            targetEvent: event,
                            templateUrl: 'core/datetime/popup.html',
                            fullScreen: false,
                            controller: function ($scope) {
                                $scope.date = ngModel.$modelValue;
                                $scope.select = function () {
                                    ngModel.$setViewValue($scope.date);
                                    ngModel.$render();
                                    $scope.$close();
                                };
                            }
                        });

                        event.preventDefault();
                    });

                    ngModel.$parsers.unshift(function parseDate(viewValue) {
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
                    });
                }

            };
        });
}());
