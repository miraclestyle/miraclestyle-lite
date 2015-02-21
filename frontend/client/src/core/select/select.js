(function () {
    'use strict';
    angular.module('app')
        .directive('selectInput', function ($simpleDialog, $mdTheming,
            $mdInkRipple, $$rAF, $mdConstant, underscoreTemplate, $timeout, $parse, helpers, $q) {
            return {
                replace: true,
                transclude: true,
                require: ['ngModel', '^?mdInputContainer'],
                templateUrl: 'core/select/input.html',
                scope: true,
                link: function (scope, element, attrs, ctrls) {
                    var ngModel = ctrls[0],
                        containerCtrl = ctrls[1],
                        items = scope.$eval(attrs.items),
                        view = scope.$eval(attrs.view),
                        search = scope.$eval(attrs.search),
                        multiple = scope.$eval(attrs.multiple),
                        placeholder = attrs.placeholder,
                        select = {},
                        timeout,
                        ngModelPipelineCheckValue,
                        isErrorGetter;
                    containerCtrl.input = element;
                    $mdTheming(element);
                    ngModelPipelineCheckValue = function (arg) {
                        containerCtrl.setHasValue(!ngModel.$isEmpty(arg));
                        return arg;
                    };
                    isErrorGetter = containerCtrl.isErrorGetter || function () {
                        return ngModel.$invalid && ngModel.$touched;
                    };
                    scope.$watch(isErrorGetter, containerCtrl.setInvalid);

                    ngModel.$parsers.push(ngModelPipelineCheckValue);
                    ngModel.$formatters.push(ngModelPipelineCheckValue);

                    element.on('click', function (ev) {
                        containerCtrl.setFocused(true);
                    });
                    scope.$on('$destroy', function () {
                        containerCtrl.setFocused(false);
                        containerCtrl.setHasValue(false);
                        containerCtrl.input = null;
                    });
                    select.getHash = function (item) {
                        return (angular.isObject(item) ? item.key : item);
                    };
                    select.placeholder = placeholder;
                    select.loading = false;
                    select.multiple = multiple;
                    select.items = [];
                    select.find = function (value) {
                        if (value === null) {
                            return undefined;
                        }
                        var active,
                            missing,
                            get = function (val) {
                                var i,
                                    found;
                                if (!angular.isObject(select.items[0])) {
                                    i = select.items.indexOf(val);
                                    if (i !== -1) {
                                        found = select.items[i];
                                    }
                                } else {
                                    found = _.findWhere(select.items, {key: val});
                                }
                                return found;
                            };
                        if (select.multiple) {
                            missing = [];
                            active = [];
                            if (value && value.length) {
                                angular.forEach(value, function (val) {
                                    var gets = get(val);
                                    if (angular.isUndefined(gets)) {
                                        missing.push(val);
                                    } else {
                                        active.push(gets);
                                    }
                                });
                            }
                        } else {
                            active = get(value);
                            if (angular.isUndefined(active)) {
                                missing = value;
                            }
                        }
                        if (angular.isDefined(missing) && missing.length && select.search && select.search.ready) {
                            select.search.ready.then(function () {
                                if (select.search.missing) {
                                    select.search.missing(missing);
                                }
                            });
                        }
                        return active;
                    };
                    select.getActive = function () {
                        select.item = select.find(ngModel.$modelValue);
                        return select.item;
                    };
                    select.setItems = function (items) {
                        select.items = items;
                        select.collectActive();
                    };
                    select.isSelected = function (item) {
                        var hash = select.getHash(item);
                        if (select.multiple) {
                            return $.inArray(hash, ngModel.$modelValue) !== -1;
                        }
                        return ngModel.$modelValue === hash;
                    };
                    select.anyChecks = function () {
                        return _.some(select.multipleSelection);
                    };
                    select.multipleSelection = {};
                    select.multipleSelect = function (item) {
                        var hash = select.getHash(item),
                            hasIt = select.multipleSelection[hash],
                            already = ngModel.$modelValue || [],
                            selected = $.inArray(hash, ngModel.$modelValue) !== -1;
                        if (!angular.isArray(select.item)) {
                            select.item = [];
                        }
                        if (hasIt) {
                            if (!selected) {
                                already.push(hash);
                                select.item.push(item);
                            }
                        } else {
                            if (selected) {
                                already.remove(hash);
                                select.item.remove(item);
                            }
                        }
                        ngModel.$setViewValue(already);
                    };

                    select.collectActive = function () {
                        angular.forEach(select.items, function (item) {
                            var hash = select.getHash(item);
                            if (angular.isUndefined(select.multipleSelection[hash])
                                    && $.inArray(hash, ngModel.$modelValue) !== -1) {
                                select.multipleSelection[hash] = true;
                            }
                        });
                    };

                    select.isChecked = function (item) {
                        return select.multipleSelection[select.getHash(item)];
                    };
                    select.select = function (item) {
                        var val = select.getHash(item);
                        ngModel.$setViewValue(val);
                        select.item = item;
                        select.close();
                    };
                    select.close = angular.noop;
                    select.opened = false;
                    select.open = function ($event) {
                        if (element.attr('disabled')) {
                            return;
                        }
                        if (select.search) {
                            select.search.query = {};
                        }
                        select.multipleSelection = {};
                        select.collectActive();

                        var attachTo = element.parents('md-content:first');

                        if (!attachTo.length) {
                            attachTo = element.parents('.fixed-height:first');
                        }

                        $simpleDialog.show({
                            template: underscoreTemplate.get('core/select/choices.html')({select: select}),
                            targetEvent: $event,
                            parent: attachTo,
                            onBeforeHide: function (dialogEl, options) {
                                $(window).off('resize', options.resize);
                            },
                            onBeforeShow: function (dialogEl, options) {
                                options.parent.css('overflow-wrap', options.parent.css('overflow-wrap') === 'normal' ? 'break-word' : 'normal');
                                var nextDefer = $q.defer(),
                                    nextPromise = nextDefer.promise,
                                    animateSelect = function () {
                                        var target = element.parents('md-input-container:first');
                                        options.resize = function () {
                                            var targetPosition = target.position(),
                                                targetPaddingLeft = parseInt(target.css('paddingLeft'), 10),
                                                parent = options.parent,
                                                parentHeight = options.parent.height(),
                                                parentScrollTop = parent.scrollTop(),
                                                paddingTop = parseInt(parent.css('padding-top'), 10) || 16,
                                                paddingBottom = parseInt(parent.css('padding-bottom'), 10) || 16,
                                                scrollElement = dialogEl.find('md-content'),
                                                maxTop = paddingTop,
                                                active = dialogEl.find('.list-row--is-active'),
                                                newTop,
                                                totalHeight;
                                            targetPosition.left += targetPaddingLeft;
                                            if (parentScrollTop > 0) {
                                                maxTop = parentScrollTop + paddingTop;
                                            }
                                            dialogEl.width(target.width());
                                            if ((dialogEl.height() > parentHeight)
                                                    || (scrollElement.prop('scrollHeight') > parentHeight)) {
                                                dialogEl.css({
                                                    top: maxTop,
                                                    left: targetPosition.left
                                                }).height(options.parent.height() - (paddingBottom + paddingTop));
                                            } else {
                                                dialogEl.css(targetPosition);
                                                if (active.length) {
                                                    // position the selection at center of active item
                                                    newTop = (targetPosition.top + parentScrollTop) - (active.position().top + (element.height() / 4)) + paddingTop;
                                                } else {
                                                    // position the div at the center if no item is selected
                                                    newTop = (targetPosition.top + parentScrollTop) - (dialogEl.height() / 2) + paddingTop;
                                                }
                                                if (newTop > maxTop) { // if newTop is larger then maxTop, attempt to check if that calculated top is possible
                                                    totalHeight = newTop + dialogEl.height(); // if the top + dialogEl exceedes parentHeight
                                                    if (totalHeight > (parentHeight + parentScrollTop)) {
                                                        newTop = newTop - (totalHeight - (parentHeight + parentScrollTop - paddingBottom)); // new top is calculated by substracting the extra space from the entire space
                                                        if (newTop < maxTop) {
                                                            newTop = maxTop;
                                                        }
                                                    }
                                                    dialogEl.css('top', newTop);
                                                } else {
                                                    dialogEl.css('top', maxTop);
                                                }
                                            }
                                            if (active.length && !select.multiple) {
                                                scrollElement.scrollTop(scrollElement.scrollTop() - scrollElement.offset().top + active.offset().top);
                                            }
                                        };
                                        options.resize();
                                        $(window).on('resize', function () {
                                            setTimeout(options.resize, 100);
                                        });

                                        dialogEl.css($mdConstant.CSS.TRANSFORM, 'scale(' +
                                            Math.min(target.width() / dialogEl.width(), 1.0) + ',' +
                                            Math.min(target.height() / dialogEl.height(), 1.0) + ')')
                                            .on($mdConstant.CSS.TRANSITIONEND, function (ev) {
                                                if (ev.target === dialogEl[0]) {
                                                    select.opened = true;
                                                    nextDefer.resolve();
                                                    if (select.search) {
                                                        dialogEl.find('input[type="search"]').focus();
                                                    }
                                                }
                                            });
                                        $$rAF(function () {
                                            dialogEl.addClass('transition-in');
                                            dialogEl.css($mdConstant.CSS.TRANSFORM, '');
                                        });

                                    };

                                $$rAF(animateSelect);

                                return nextPromise;
                            },
                            controller: function ($scope) {
                                select.close = function () {
                                    $simpleDialog.hide();
                                };
                                $scope.select = select;
                                $scope.$on('$destroy', function () {
                                    select.opened = false;
                                    containerCtrl.setFocused(false);
                                });
                            }
                        });
                    };
                    select.view = view;
                    if (!view) {
                        select.view = function (item) {
                            return angular.isObject(item) ? item.name : item;
                        };
                    }
                    ngModel.$formatters.push(function (value) {
                        select.item = select.find(value);
                        return value;
                    });

                    select.getFindTerm = function () {
                        return $parse(select.search.filterProp)(select.search.query);
                    };

                    if (search) {
                        select.search = {
                            query: {},
                            delay: 200,
                            doFind: function () {
                                var term = select.getFindTerm();
                                if (timeout) {
                                    clearTimeout(timeout);
                                }
                                if (select.search.find) {
                                    timeout = setTimeout(function () {
                                        select.search.find(term);
                                    }, select.search.delay);
                                }

                                $timeout(function () {
                                    $(window).triggerHandler('resize');
                                });
                            }
                        };
                        $.extend(select.search, search);
                        select.search.filterProp = (select.search.filterProp ? select.search.filterProp : 'name');
                        if (!select.search.model) {
                            select.search.model = 'select.search.query' + ('.' + select.search.filterProp);
                        }
                        if (!select.search.filter) {
                            select.search.filter = '| filter:select.search.query' + ((items && angular.isString(items[0])) ? ('.' + select.search.filterProp) : '');
                        }
                    }
                    select.setItems(items);
                    scope.$watchGroup([attrs.items + '.length', attrs.items], function (neww, old) {
                        if (neww[0] !== old[0] || neww[1] !== old[1]) {
                            select.setItems(scope.$eval(attrs.items));
                            select.getActive();
                            if (select.opened) {
                                $timeout(function () {
                                    $(window).triggerHandler('resize');
                                });
                            }
                        }
                    });

                    scope.select = select;
                }
            };
        });
}());