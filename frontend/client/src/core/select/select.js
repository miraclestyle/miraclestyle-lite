(function () {
    'use strict';
    angular.module('app')
        .directive('selectInputScrollToActive', ng(function ($timeout) {
            return {
                link: function (scope, element, attrs) {
                    scope.$watch(function () {
                        return scope.$eval(attrs.selectInputScrollToActive);
                    }, function (newValue, oldValue, scope) {
                        $timeout(function () {
                            if (newValue) {
                                var scrollElement = element.parents('.fixed-height:first'),
                                    active = scrollElement.find('.list-row-is-active:first');
                                if (!active.length) {
                                    return;
                                }
                                scrollElement.scrollTop(active.get(0).offsetTop);
                            }
                        }, 0, false);
                    });
                }
            };
        }))
        .directive('selectInputMultiple', ng(function ($timeout, underscoreTemplate, $q, $modal) {
            return {
                require: ['ngModel', '^?form'],
                link: function (scope, element, attrs, ctrls) {
                    var ngModel = ctrls[0],
                        formCtrl = ctrls[1],
                        grouping = scope.$eval(attrs.grouping),
                        items = scope.$eval(attrs.items),
                        view = scope.$eval(attrs.view),
                        listView = scope.$eval(attrs.listView),
                        search = scope.$eval(attrs.search),
                        defer = scope.$eval(attrs.defer),
                        resolve = function () {
                            if (defer) {
                                defer.resolve();
                            }
                        },
                        select = scope.$eval(attrs.select),
                        init = (select && select.init ? select.init : null);

                    select.getHash = function (item) {
                        return (angular.isObject(item) ? item.key : item);
                    };
                    select.search = search;
                    select.anyItems = 0;
                    select.async = true;
                    select.loading = false;
                    select.multiple = true;
                    select.items = [];
                    select.find = function (value) {
                        if (value === null || value === undefined) {
                            resolve();
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
                                    found = _.findWhere(select.items, {
                                        key: val
                                    });
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
                        if (select.search && select.search.ready) {
                            select.search.ready.then(function () {
                                if (select.search.missing && missing && missing.length) {
                                    select.search.missing(missing).then(resolve, resolve);
                                } else {
                                    resolve();
                                }
                            }, resolve);
                        } else {
                            resolve();
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
                        if (grouping) {
                            select.grouping = grouping(select.items);
                        }
                        select.anyItems = items.length;
                    };
                    select.isSelected = function (item) {
                        var hash = select.getHash(item);
                        if (select.multiple) {
                            return $.inArray(hash, ngModel.$modelValue) !== -1;
                        }
                        return ngModel.$modelValue === hash;
                    };
                    select.remove = function (item) {
                        select.select(item);
                    };
                    select.anySelected = function () {
                        var any = true;
                        angular.forEach(select.multipleSelection, function (value) {
                            if (!any) {
                                any = value;
                            }
                        });
                        return any;
                    };
                    select.multipleSelection = {};
                    select.multipleSelect = function (item, nocheck) {
                        var hash = select.getHash(item),
                            hasIt = nocheck ? select.multipleSelection[hash] : !select.multipleSelection[hash],
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
                        select.close();
                    };
                    // @todo this is causing problems
                    select.commitMultipleSelect = function (item) {
                        $timeout(function () {
                            select.multipleSelect(item, true);
                        }, 100);
                    };

                    select.collectActive = function () {
                        angular.forEach(select.items, function (item) {
                            var hash = select.getHash(item);
                            if (angular.isUndefined(select.multipleSelection[hash]) && $.inArray(hash, ngModel.$modelValue) !== -1) {
                                select.multipleSelection[hash] = true;
                            }
                        });
                    };

                    select.isChecked = function (item) {
                        return select.multipleSelection[select.getHash(item)];
                    };
                    select.select = function (item) {
                        select.multipleSelect(item);
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
                        var attachTo = element.parents('.modal:first').find('.modal-dialog:first'),
                            choices;

                        if (!attachTo.length) {
                            attachTo = element.parents('body:first');
                        }

                        choices = underscoreTemplate.get(select.openTemplate || 'core/select/choices.html')({
                            select: select
                        });
                        $modal.open({
                            template: underscoreTemplate.get('core/select/single.html')().replace('{{content}}', choices),
                            targetEvent: $event,
                            parent: attachTo,
                            inDirection: false,
                            windowClass: 'modal-medium-simple ' + (select.windowClass || ''),
                            outDirection: false,
                            fullScreen: false,
                            backdrop: true,
                            controller: ng(function ($scope) {
                                var resolved = $q.defer();
                                resolved.resolve();
                                $scope.$state.promise(function () {
                                    return ((select.search && select.search.ready) ? select.search.ready : resolved.promise);
                                }, function () {
                                    $scope.select = select;
                                });
                                $scope.$on('$destroy', function () {
                                    select.opened = false;
                                    select.close = angular.noop;
                                });
                                $scope.close = function () {
                                    $scope.$close().then(select.afterClose || angular.noop);
                                };
                                select.close = function () {
                                    $scope.close();
                                };
                            })
                        });
                    };
                    if (!view) {
                        view = function (item) {
                            return angular.isObject(item) ? item.name : item;
                        };
                    }
                    select.view = view;
                    select.listView = listView || view;
                    ngModel.$formatters.push(function (value) {
                        select.collectActive();
                        select.item = select.find(value);
                        return value;
                    });
                    if (grouping) {
                        select.hasGrouping = true;
                        select.grouping = [];
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

                    if (init) {
                        init(select, scope, element, attrs, ctrls);
                    }

                }
            };
        }))
        .directive('selectInput', ng(function ($simpleDialog, $$rAF, $mdConstant, underscoreTemplate, $timeout, $parse, helpers, $q, $modal) {
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
                        init = (search && search.init ? search.init : null),
                        multiple = scope.$eval(attrs.multiple),
                        async = scope.$eval(attrs.async),
                        grouping = scope.$eval(attrs.grouping),
                        listView = scope.$eval(attrs.listView),
                        placeholder = attrs.placeholder,
                        defer = scope.$eval(attrs.defer),
                        select = {},
                        resolve = function () {
                            if (defer) {
                                defer.resolve();
                            }
                        },
                        ngModelPipelineCheckValue,
                        dontOpen = false;
                    containerCtrl.input = element;
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
                    }).on('click', function (ev) {
                        if (!dontOpen) {
                            select.open();
                        }
                        dontOpen = false;

                        ev.preventDefault();
                    }).on('blur', function (ev) {
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
                    select.search = search;
                    select.async = async;
                    select.placeholder = placeholder;
                    select.loading = false;
                    select.multiple = multiple;
                    select.items = [];
                    select.find = function (value) {
                        if (value === null || value === undefined) {
                            resolve();
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
                                    found = _.findWhere(select.items, {
                                        key: val
                                    });
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
                        if (select.search && select.search.ready) {
                            select.search.ready.then(function () {
                                if (select.search.missing && missing && missing.length) {
                                    select.search.missing(missing).then(resolve, resolve);
                                } else {
                                    resolve();
                                }
                            }, resolve);
                        } else {
                            resolve();
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
                        if (grouping) {
                            select.grouping = grouping(select.items);
                        }
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
                    };
                    select.anySelected = function () {
                        return true;
                    };
                    select.multipleSelection = {};
                    select.multipleSelect = function (item) {
                        var hash = select.getHash(item),
                            hasIt = !select.multipleSelection[hash],
                            already = ngModel.$modelValue || [],
                            selected = $.inArray(hash, ngModel.$modelValue) !== -1;
                        select.multipleSelection[hash] = hasIt;
                        if (select.multiple) {
                            return;
                        }
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

                    select.completeMultiSelection = function () {
                        var selected = [],
                            founds = [];
                        angular.forEach(select.items, function (item) {
                            var hash = select.getHash(item);
                            if (select.multipleSelection[hash]) {
                                selected.push(hash);
                                founds.push(item);
                            }
                        });
                        ngModel.$setViewValue(selected);
                        formCtrl.$setDirty();
                        ngModelPipelineCheckValue(selected);
                        select.item = founds;
                        select.close();
                    };


                    select.collectActive = function () {
                        angular.forEach(select.items, function (item) {
                            var hash = select.getHash(item);
                            if (angular.isUndefined(select.multipleSelection[hash]) && $.inArray(hash, ngModel.$modelValue) !== -1) {
                                select.multipleSelection[hash] = true;
                            }
                        });
                    };

                    select.isChecked = function (item) {
                        return false;
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

                        var attachTo = element.parents('.modal:first').find('.modal-dialog:first'),
                            choices,
                            root;

                        if (!attachTo.length) {
                            attachTo = element.parents('body:first');
                        }

                        choices = underscoreTemplate.get(select.openTemplate || 'core/select/choices.html')({
                            select: select
                        });
                        root = choices;
                        if (select.multiple || async) {
                            root = underscoreTemplate.get('core/select/single.html')().replace('{{content}}', choices);
                            $event = undefined;
                        }

                        (select.multiple || async ? $modal.open : $simpleDialog.show)({
                            template: root,
                            popFrom: ($event ? $event.target : undefined),
                            targetEvent: $event,
                            parent: attachTo,
                            inDirection: false,
                            windowClass: 'modal-medium-simple ' + (select.windowClass ? select.windowClass : ''),
                            outDirection: false,
                            fullScreen: false,
                            backdrop: true,
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
                                                paddingTop = async ? 24 : 16,
                                                paddingBottom = async ? 24 : 16,
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
                                            if ((dialogEl.height() > parentHeight) || (scrollElement.prop('scrollHeight') > parentHeight) || (dialogEl.height() > innerHeight)) {
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
                                                dialogEl.css($mdConstant.CSS.TRANSFORMORIGIN, (wrapAroundOffset.left + target.width() / 2) + 'px ' + (wrapAroundOffset.top + active.height() / 2 - scrollElement.scrollTop()) + 'px 0px');
                                            }
                                        };
                                        options.resize();
                                        $(window).on('resize', function () {
                                            setTimeout(options.resize, 100);
                                        });

                                        dialogEl.oneAnimationEnd(function (ev) {
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
                                            dialogEl.addClass('opacity-in');
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
                                                    indx = $parse(nextActive.attr('item'))(nextActive.scope());
                                                } else {
                                                    indx = select.items[0];
                                                }
                                                if (indx) {
                                                    select.select(indx);
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
                                            dialogEl.addClass('fade in');
                                            dontOpen = false;
                                        });


                                    };

                                $$rAF(animateSelect);

                                return nextPromise;
                            },
                            controller: ng(function ($scope) {
                                var process = function () {
                                    select.close = function () {
                                        if (select.multiple || select.async) {
                                            $scope.close();
                                        } else {
                                            $simpleDialog.hide();
                                        }
                                    };
                                    $scope.select = select;
                                }, resolved = $q.defer();
                                resolved.resolve();
                                if ($scope.$state) {
                                    $scope.$state.promise(function () {
                                        return ((select.search && select.search.ready) ? select.search.ready : resolved.promise);
                                    }, process);
                                } else {
                                    process();
                                }
                                $scope.close = function () {
                                    $scope.$close().then(select.afterClose || angular.noop);
                                };
                                $scope.$on('$destroy', function () {
                                    select.opened = false;
                                    containerCtrl.setFocused(false);
                                    //dontOpen = true;
                                    element.focus();
                                });
                            })
                        });
                    };
                    if (!view) {
                        view = function (item) {
                            return angular.isObject(item) ? item.name : item;
                        };
                    }
                    select.view = view;
                    select.listView = listView || view;
                    ngModel.$formatters.push(function (value) {
                        select.item = select.find(value);
                        return value;
                    });

                    select.isFilterMatch = function (item) {
                        if (!search) {
                            return true;
                        }
                        var toFilter,
                            term = select.getFindTerm(),
                            match,
                            maybe = select.search.query;
                        if (select.search.filterProp) {
                            maybe = maybe[select.search.filterProp];
                        }
                        if (!maybe || maybe.length < 1) {
                            return true;
                        }
                        if (select.search.filterProp) {
                            toFilter = item[select.search.filterProp];
                        } else {
                            toFilter = item;
                        }
                        match = toFilter.toString().toLowerCase().indexOf(term) !== -1;
                        return match;
                    };

                    select.getFindTerm = function () {
                        return $parse(select.search.filterProp)(select.search.query);
                    };

                    if (grouping) {
                        select.hasGrouping = true;
                        select.grouping = [];
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

                    if (init) {
                        init(select, scope, element, attrs, ctrls);
                    }

                }
            };
        }));
}());
