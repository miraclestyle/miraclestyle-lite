(function () {
    'use strict';
    angular.module('app')
        .directive('repeatedText', ng(function (helpers) {
            return {
                require: 'ngModel',
                link: function (scope, element, attrs, ctrl) {

                    var worker = function (value, what) {

                            var test = false;

                            try {
                                if (what === 'list') {
                                    value = helpers.splitLines(value);
                                    value = _.uniq(value);
                                }
                                if (what === 'str') {
                                    if (angular.isArray(value)) {
                                        value = value.join('\n');
                                    }
                                }
                                test = true;

                            } catch (ignore) {}

                            ctrl.$setValidity('invalid', test);

                            return value;
                        },
                        parser = function (value) {
                            return worker(value, 'list');
                        },
                        formatter = function (value) {
                            return worker(value, 'str');
                        };

                    ctrl.$parsers.push(parser);
                    ctrl.$formatters.push(formatter);
                }
            };
        })).directive('checkNumeric', function () {
            return {
                require: ['ngModel', '^form'],
                link: function (scope, element, attrs, ctrls) {
                    var checkNumeric = function (value) {
                            var valid = !isNaN(parseInt(value, 10));
                            if (!valid) {
                                valid = !isNaN(parseFloat(value, 10));
                            }
                            return valid;
                        },
                        required = element.attr('required') === 'required';
                    ctrls[0].$parsers.unshift(function (value) {
                        var valid = checkNumeric(value),
                            out;
                        if (!required && (!valid || angular.isUndefined(value) || !value.length || !value.replace(/[^0-9+.]/g, ''))) {
                            valid = true;
                        }
                        ctrls[0].$setValidity('checkNumeric', valid);
                        // if it's valid, return the value to the model, 
                        // otherwise return undefined.
                        if (angular.isDefined(value)) {
                            out = value.replace(/[^0-9+.]/g, '');
                            if (out !== value) {
                                ctrls[0].$setViewValue(out);
                                ctrls[0].$render();
                            }
                            return out;
                        }

                        return valid ? value : undefined;
                    });
                }
            };
        }).constant('msdElasticConfig', {
            append: ''
        }).directive('msdElastic', [
            '$timeout', '$window', 'msdElasticConfig',
            function ($timeout, $window, config) {
                return {
                    require: 'ngModel',
                    restrict: 'A, C',
                    link: function (scope, element, attrs, ngModel) {

                        // cache a reference to the DOM element
                        var ta = element[0],
                            $ta = element;

                        // ensure the element is a textarea, and browser is capable
                        if (ta.nodeName !== 'TEXTAREA' || !$window.getComputedStyle) {
                            return;
                        }

                        // set these properties before measuring dimensions
                        $ta.css({
                            'overflow': 'hidden',
                            'overflow-y': 'hidden',
                            'word-wrap': 'break-word'
                        });

                        // force text reflow
                        var text = ta.value;
                        ta.value = '';
                        ta.value = text;

                        var append = attrs.msdElastic ? attrs.msdElastic.replace(/\\n/g, '\n') : config.append,
                            $win = angular.element($window),
                            mirrorInitStyle = 'position: absolute; top: -999px; right: auto; bottom: auto;' +
                            'left: 0; overflow: hidden; -webkit-box-sizing: content-box;' +
                            '-moz-box-sizing: content-box; box-sizing: content-box;' +
                            'min-height: 0 !important; height: 0 !important; padding: 0;' +
                            'word-wrap: break-word; border: 0;',
                            $mirror = angular.element('<textarea aria-hidden="true" tabindex="-1" ' +
                                'style="' + mirrorInitStyle + '"/>').data('elastic', true),
                            mirror = $mirror[0],
                            taStyle = getComputedStyle(ta),
                            resize = taStyle.getPropertyValue('resize'),
                            borderBox = taStyle.getPropertyValue('box-sizing') === 'border-box' ||
                            taStyle.getPropertyValue('-moz-box-sizing') === 'border-box' ||
                            taStyle.getPropertyValue('-webkit-box-sizing') === 'border-box',
                            boxOuter = !borderBox ? {
                                width: 0,
                                height: 0
                            } : {
                                width: parseInt(taStyle.getPropertyValue('border-right-width'), 10) +
                                    parseInt(taStyle.getPropertyValue('padding-right'), 10) +
                                    parseInt(taStyle.getPropertyValue('padding-left'), 10) +
                                    parseInt(taStyle.getPropertyValue('border-left-width'), 10),
                                height: parseInt(taStyle.getPropertyValue('border-top-width'), 10) +
                                    parseInt(taStyle.getPropertyValue('padding-top'), 10) +
                                    parseInt(taStyle.getPropertyValue('padding-bottom'), 10) +
                                    parseInt(taStyle.getPropertyValue('border-bottom-width'), 10)
                            },
                            minHeightValue = parseInt(taStyle.getPropertyValue('min-height'), 10),
                            heightValue = parseInt(taStyle.getPropertyValue('height'), 10),
                            minHeight = Math.max(minHeightValue, heightValue) - boxOuter.height,
                            maxHeight = parseInt(taStyle.getPropertyValue('max-height'), 10),
                            mirrored,
                            active,
                            copyStyle = ['font-family',
                                'font-size',
                                'font-weight',
                                'font-style',
                                'letter-spacing',
                                'line-height',
                                'text-transform',
                                'word-spacing',
                                'text-indent'
                            ];

                        // exit if elastic already applied (or is the mirror element)
                        if ($ta.data('elastic')) {
                            return;
                        }

                        // Opera returns max-height of -1 if not set
                        maxHeight = maxHeight && maxHeight > 0 ? maxHeight : 9e4;

                        // append mirror to the DOM
                        if (mirror.parentNode !== document.body) {
                            angular.element(document.body).append(mirror);
                        }

                        // set resize and apply elastic
                        $ta.css({
                            'resize': (resize === 'none' || resize === 'vertical') ? 'none' : 'horizontal'
                        }).data('elastic', true);

                        /*
                         * methods
                         */

                        function initMirror() {
                            var mirrorStyle = mirrorInitStyle;

                            mirrored = ta;
                            // copy the essential styles from the textarea to the mirror
                            taStyle = getComputedStyle(ta);
                            angular.forEach(copyStyle, function (val) {
                                mirrorStyle += val + ':' + taStyle.getPropertyValue(val) + ';';
                            });
                            mirror.setAttribute('style', mirrorStyle);
                        }

                        function adjust() {
                            var taHeight,
                                taComputedStyleWidth,
                                mirrorHeight,
                                width,
                                overflow;

                            if (mirrored !== ta) {
                                initMirror();
                            }

                            // active flag prevents actions in function from calling adjust again
                            if (!active) {
                                active = true;

                                mirror.value = ta.value + append; // optional whitespace to improve animation
                                mirror.style.overflowY = ta.style.overflowY;

                                taHeight = ta.style.height === '' ? 'auto' : parseInt(ta.style.height, 10);

                                taComputedStyleWidth = getComputedStyle(ta).getPropertyValue('width');

                                // ensure getComputedStyle has returned a readable 'used value' pixel width
                                if (taComputedStyleWidth.substr(taComputedStyleWidth.length - 2, 2) === 'px') {
                                    // update mirror width in case the textarea width has changed
                                    width = parseInt(taComputedStyleWidth, 10) - boxOuter.width;
                                    mirror.style.width = width + 'px';
                                }

                                mirrorHeight = mirror.scrollHeight;

                                if (mirrorHeight > maxHeight) {
                                    mirrorHeight = maxHeight;
                                    overflow = 'scroll';
                                } else if (mirrorHeight < minHeight) {
                                    mirrorHeight = minHeight;
                                }
                                mirrorHeight += boxOuter.height;
                                ta.style.overflowY = overflow || 'hidden';

                                if (taHeight !== mirrorHeight) {
                                    ta.style.height = mirrorHeight + 'px';
                                    scope.$emit('elastic:resize', $ta);
                                }

                                // small delay to prevent an infinite loop
                                $timeout(function () {
                                    active = false;
                                }, 1, false);

                            }
                        }

                        function forceAdjust() {
                            active = false;
                            adjust();
                        }

                        /*
                         * initialise
                         */

                        // listen
                        if ('onpropertychange' in ta && 'oninput' in ta) {
                            // IE9
                            ta['oninput'] = ta.onkeyup = adjust;
                        } else {
                            ta['oninput'] = adjust;
                        }

                        $win.bind('resize', forceAdjust);

                        scope.$watch(function () {
                            return ngModel.$modelValue;
                        }, function (newValue) {
                            forceAdjust();
                        });

                        scope.$on('elastic:adjust', function () {
                            initMirror();
                            forceAdjust();
                        });

                        $timeout(adjust);

                        /*
                         * destroy
                         */

                        scope.$on('$destroy', function () {
                            $mirror.remove();
                            $win.unbind('resize', forceAdjust);
                        });
                    }
                };
            }
        ]).run(ng(function (formInputTypes, GLOBAL_CONFIG, helpers) {
            $.extend(formInputTypes, {
                _SelectBox: function (info) {

                    if (!angular.isDefined(info.config.ui.specifics.searchEnabled)) {
                        if (info.config.choices.length < 10) {
                            info.config.ui.specifics.searchEnabled = false;
                        } else {
                            info.config.ui.specifics.searchEnabled = true;
                        }
                    }

                    if (info.config.choices.length && (info.config.ui.specifics && info.config.ui.specifics.translatedChoices !== false)) {
                        info.config.ui.specifics.translatedChoices = [];
                        angular.forEach(info.config.choices, function (value) {
                            // @todo this might cause problems when config.choices = some other list is applied trough the lifecycle
                            // the choices will not be re-parsed to translatedChoices
                            // this code will only run upon directive initilization
                            var hasit = helpers.getProperty(GLOBAL_CONFIG.fields.translateChoices, [info.config._maker_, info.config.code_name, value]);
                            if (angular.isUndefined(hasit)) {
                                hasit = value;
                            }
                            info.config.ui.specifics.translatedChoices.push({
                                key: value,
                                name: hasit
                            });
                        });
                    }

                    return 'select';
                },
                SuperStringProperty: function (info) {
                    var config = info.config;


                    if (config.ui.attrs.type === undefined) {
                        config.ui.attrs.type = 'text';
                    }

                    if (config.choices) {
                        if (config.repeated) {
                            return this._SuperStringRepeated(info);
                        }
                        if (info.config.ui.attrs['repeated-text'] !== undefined) {
                            delete info.config.ui.attrs['repeated-text'];
                        }
                        return this._SelectBox(info);
                    }

                    if (config.repeated) {
                        config.ui.attrs['repeated-text'] = '';
                        return this.SuperTextProperty(info);
                    }

                    return 'string';
                },
                SuperFloatProperty: function (info) {
                    var config = info.config;

                    if (config.choices) {
                        return this._SelectBox(info);
                    }
                    config.ui.attrs['check-numeric'] = '';
                    return this.SuperStringProperty(info);
                },
                SuperIntegerProperty: function (info) {
                    var config = info.config;

                    if (config.choices) {
                        return this._SelectBox(info);
                    }

                    config.ui.attrs['check-numeric'] = '';

                    return this.SuperFloatProperty(info);
                },
                SuperDecimalProperty: function (info) {
                    var config = info.config;
                    if (config.choices) {
                        return this._SelectBox(info);
                    }
                    config.ui.attrs['check-numeric'] = '';
                    return this.SuperFloatProperty(info);
                },
                _SuperStringRepeated: function (info) {
                    var select = {};
                    info.config.ui.specifics.select = select;
                    info.config._groupable = true;
                    return 'select_multiple';
                },
                SuperTextProperty: function (info) {
                    if (info.config.repeated) {
                        info.config.ui.attrs['repeated-text'] = '';
                    }
                    if (info.config.ui.specifics.autoGrow === undefined || info.config.ui.specifics.autoGrow) {
                        info.config.ui.attrs['msd-elastic'] = '';
                    }
                    return 'text';
                },
                SuperDateTimeProperty: function (info) {
                    info.config.ui.attrs['time-date-picker-dialog'] = '';
                    info.config.ui.attrs.readonly = 'true';
                    return 'string';
                }
            });
        }));
}());
