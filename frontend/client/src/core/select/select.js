(function () {
    'use strict';
    angular.module('app')
        .directive('selectInput', function ($simpleDialog, $mdTheming,
            $mdInkRipple, $$rAF, $mdConstant, underscoreTemplate, $timeout, $parse, helpers, $q) {
            return {
                replace: true,
                transclude: true,
                require: ['ngModel', '^?mdInputContainer', '^?form'],
                templateUrl: 'core/select/input.html',
                scope: true,
                link: function (scope, element, attrs, ctrls) {
                    var ngModel = ctrls[0],
                        containerCtrl = ctrls[1],
                        formCtrl = ctrls[2],
                        items = scope.$eval(attrs.items),
                        view = scope.$eval(attrs.view),
                        search = scope.$eval(attrs.search),
                        multiple = scope.$eval(attrs.multiple),
                        placeholder = attrs.placeholder,
                        select = {},
                        timeout,
                        ngModelPipelineCheckValue,
                        dontOpen = false;
                    containerCtrl.input = element;
                    $mdTheming(element);
                    ngModelPipelineCheckValue = function (arg) {
                        var s = !ngModel.$isEmpty(arg);
                        if (angular.isArray(arg)) {
                            s = arg.length !== 0;
                        }
                        containerCtrl.setHasValue(s);
                        return arg;
                    };
                    scope.$watch(function () {
                        return ngModel.$invalid && ngModel.$touched;
                    }, containerCtrl.setInvalid);

                    ngModel.$parsers.push(ngModelPipelineCheckValue);
                    ngModel.$formatters.push(ngModelPipelineCheckValue);

                    element.on('keyup', function (ev) {
                        if (ev.keyCode === $mdConstant.KEY_CODE.ENTER) {
                            select.open();
                        }
                    });
                    element.on('click focus', function (ev) {
                        if (!dontOpen) {
                            //containerCtrl.setFocused(true);
                            select.open();
                        }
                        dontOpen = false;

                        ev.preventDefault();
                        ev.stopImmediatePropagation();
                        ev.stopPropagation();
                    });
                    element.on('blur', function (ev) {
                        containerCtrl.setFocused(false);
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
                    select.anyUnselected = function () {
                        return true;
                        return !select.multipleSelection || _.contains(select.multipleSelection, false);
                    };
                    select.anySelected = function () {
                        return true;
                        return _.some(select.multipleSelection);
                    };
                    select.multipleSelection = {};
                    select.multipleSelect = function (item) {
                        var hash = select.getHash(item),
                            hasIt = !select.multipleSelection[hash],
                            already = ngModel.$modelValue || [],
                            selected = $.inArray(hash, ngModel.$modelValue) !== -1;
                        select.multipleSelection[hash] = hasIt;
                        if (!angular.isArray(select.item)) {
                            select.item = already;
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
                        formCtrl.$setDirty();
                        ngModelPipelineCheckValue(already);
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
                        if (select.opened) {
                            return;
                        }
                        select.opened = true;
                        $timeout(function () {
                            select.openSimpleDialog($event);
                        });
                    };
                    select.openSimpleDialog = function ($event) {
                        if (element.attr('disabled')) {
                            return;
                        }
                        if (select.search) {
                            select.search.query = {};
                        }
                        select.multipleSelection = {};
                        select.collectActive();

                        var attachTo = element.parents('.modal:first').find('.modal-dialog:first');

                        if (!attachTo.length) {
                            attachTo = element.parents('body:first');
                        }

                        $simpleDialog.show({
                            template: underscoreTemplate.get('core/select/choices.html')({select: select}),
                            targetEvent: $event,
                            parent: attachTo,
                            disableScroll: [element.parents('md-content:first'), element.parents('.fixed-height:first')],
                            onBeforeHide: function (dialogEl, options) {
                                $(window).off('resize', options.resize);
                            },
                            onBeforeShow: function (dialogEl, options) {
                                var nextDefer = $q.defer(),
                                    nextPromise = nextDefer.promise,
                                    nextActive = false,
                                    firstTabbable = dialogEl.find('[tabindex="2"]'),
                                    animateSelect = function () {
                                        var target = element.parents('md-input-container:first');
                                        options.resize = function () {
                                            var targetOffset = target.offset(),
                                                elementOffset = element.offset(),
                                                parent = options.parent,
                                                parentOffset = parent.offset(),
                                                paddingTop = 24,
                                                paddingBottom = 24,
                                                parentHeight = options.parent.height(),
                                                scrollElement = dialogEl.find('md-content'),
                                                maxTop,
                                                activeOffset,
                                                active = dialogEl.find('.list-row-is-active'),
                                                toolbar = attachTo.find('md-toolbar'),
                                                toolbarHeight = 0,
                                                newTop,
                                                totalHeight,
                                                wrapAround,
                                                wrapAroundOffset,
                                                nextActive,
                                                innerHeight;
                                            if (active.length) {
                                                activeOffset = active.offset();
                                                wrapAroundOffset = activeOffset;
                                                wrapAround = active;
                                            } else {
                                                wrapAroundOffset = firstTabbable.offset();
                                                wrapAround = firstTabbable;
                                            }
                                            if (toolbar.length) {
                                                toolbarHeight = toolbar.height();
                                            }
                                            maxTop = parentOffset.top + paddingTop + toolbarHeight;
                                            innerHeight = parentHeight - (paddingBottom + paddingTop + toolbarHeight);
                                            dialogEl.width(target.width());
                                            if ((dialogEl.height() > parentHeight)
                                                    || (scrollElement.prop('scrollHeight') > parentHeight)
                                                    || (dialogEl.height() > innerHeight)) {
                                                dialogEl.css({
                                                    top: maxTop,
                                                    left: elementOffset.left
                                                }).height(innerHeight);
                                            } else {
                                                dialogEl.css(elementOffset);
                                                if (active.length) {
                                                    // position the selection at center of active item
                                                    newTop = elementOffset.top - activeOffset.top + (active.height() / 5);
                                                } else {
                                                    // position the div at the center if no item is selected
                                                    newTop = (targetOffset.top) - (dialogEl.height() / 2) + paddingTop;
                                                }
                                                if (newTop > maxTop) {
                                                    totalHeight = newTop + dialogEl.height();
                                                    if (totalHeight + 24 > parentHeight) {
                                                        newTop = newTop - (totalHeight - (parentHeight - 24));
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

                                            if (wrapAroundOffset) {
                                                dialogEl.css($mdConstant.CSS.TRANSFORMORIGIN,
                                                    (wrapAroundOffset.left + target.width() / 2) + 'px ' + (wrapAroundOffset.top + active.height() / 2 - scrollElement.scrollTop()) + 'px 0px');
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
                                                    nextDefer.resolve();
                                                    nextActive = dialogEl.find('.list-row-is-active:first');
                                                    if (!nextActive.length) {
                                                        nextActive = firstTabbable;
                                                    }
                                                    if (select.search) {
                                                        setTimeout(function () {
                                                            dialogEl.find('input[type="search"]').focus();
                                                        }, 100);
                                                    } else {
                                                        nextActive.focus();
                                                    }
                                                }
                                            }).on('keyup', function (ev) {
                                                if (!nextActive) {
                                                    return;
                                                }
                                                var original = nextActive,
                                                    doFocus = false,
                                                    indx = -1;
                                                if (ev.keyCode === $mdConstant.KEY_CODE.DOWN_ARROW) {
                                                    nextActive = nextActive.next();
                                                    doFocus = true;
                                                } else if (ev.keyCode === $mdConstant.KEY_CODE.UP_ARROW) {
                                                    nextActive = nextActive.prev();
                                                    doFocus = true;
                                                } else if (ev.keyCode === $mdConstant.KEY_CODE.ENTER) {
                                                    nextActive = dialogEl.find('.simple-dialog-option:focus');
                                                    if (!nextActive.length) {
                                                        nextActive = dialogEl.find('.list-row-is-active:first');
                                                    }
                                                    if (nextActive.length) {
                                                        indx = dialogEl.find('.simple-dialog-option').index(nextActive);
                                                    } else {
                                                        indx = 0;
                                                    }
                                                    if (indx !== -1) {
                                                        select.select(select.items[indx]);
                                                    }
                                                }
                                                if (!nextActive.length && doFocus) {
                                                    nextActive = original;
                                                }
                                                if (doFocus) {
                                                    nextActive.focus();
                                                }
                                            });
                                        $$rAF(function () {
                                            dialogEl.addClass('transition-in');
                                            dialogEl.css($mdConstant.CSS.TRANSFORM, '');
                                            dontOpen = false;
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
                                    dontOpen = true;
                                    element.focus();
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
                                }, 0, false);
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
                                }, 0, false);
                            }
                        }
                    });

                    scope.select = select;
                }
            };
        });
}());