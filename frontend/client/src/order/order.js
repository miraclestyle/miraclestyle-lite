(function () {
    'use strict';


    angular.module('app')
        .run(ng(function (helpers) {
            if (!helpers.order) {
                helpers.order = {};
            }

            helpers.order.poolResultsComparator = function (current, value, setUpdater) {
                var passesUpdated = false,
                    passesTracker = false;
                if (!current.updated && value.updated) {
                    passesUpdated = true;
                }
                if ((current.updated && value.updated) && (current.updated.getTime() !== value.updated.getTime())) {
                    passesUpdated = true;
                }
                if (passesUpdated) {
                    setUpdater(current.key, 'updated', value.updated);
                } else {
                    setUpdater(current.key, 'updated', null, true);
                }
                if (current._tracker !== value._tracker) {
                    if ((current._tracker && value._tracker) && (((current._tracker.buyer !== value._tracker.buyer) || (value._tracker.seller !== current._tracker.seller)))) {
                        setUpdater(current.key, '_tracker', value._tracker);
                        passesTracker = true;

                    }

                    if ((current._tracker && !value._tracker) || (!current._tracker && value._tracker)) {
                        setUpdater(current.key, '_tracker', value._tracker);
                        passesTracker = true;
                    }

                    if (!passesTracker) {
                        setUpdater(current.key, '_tracker', null, true);
                    }
                }
            };
        }))
        .directive('alwaysScrollToBottom', ng(function ($timeout) {
            return {
                link: function (scope, element, attrs) {
                    var cb = function () {
                        element.scrollTop(element[0].scrollHeight);
                    };

                    scope.$watchGroup(scope.$eval(attrs.alwaysScrollToBottom), function (neww, old) {
                        if (JSON.stringify(neww) !== JSON.stringify(old)) {
                            $timeout(cb, 300, 0);
                        }
                    });
                }
            };
        }))
        .directive('validateCardNumber', function () {
            return {
                require: 'ngModel',
                link: function (scope, elem, attr, ngModel) {
                    //For DOM -> model validation
                    ngModel.$parsers.unshift(function (value) {
                        var valid = window.Stripe.card.validateCardNumber(value);
                        ngModel.$setValidity('invalid_card_number', valid);
                        return valid ? value : undefined;
                    });

                    //For model -> DOM validation
                    ngModel.$formatters.unshift(function (value) {
                        var valid = window.Stripe.card.validateCardNumber(value);
                        ngModel.$setValidity('invalid_card_number', valid);
                        return value;
                    });
                }
            };
        })
        .directive('validateCvc', function () {
            return {
                require: 'ngModel',
                link: function (scope, elem, attr, ngModel) {
                    //For DOM -> model validation
                    ngModel.$parsers.unshift(function (value) {
                        var valid = window.Stripe.card.validateCVC(value);
                        ngModel.$setValidity('invalid_card_cvc', valid);
                        return valid ? value : undefined;
                    });

                    //For model -> DOM validation
                    ngModel.$formatters.unshift(function (value) {
                        var valid = window.Stripe.card.validateCVC(value);
                        ngModel.$setValidity('invalid_card_cvc', valid);
                        return value;
                    });
                }
            };
        })
        .directive('validateCardDate', function () {
            return {
                require: '^validateCardDate',
                controller: function () {
                    this.models = {};
                },
                link: function (scope, elem, attr, validateCardDate) {
                    var controllers = validateCardDate.models;
                    scope.$watchGroup([attr.year, attr.month], function (oldvalues, newvalues) {
                        // Whenever the comparison model changes we'll re-validate
                        var valid = window.Stripe.card.validateExpiry(validateCardDate.models.month.$modelValue, validateCardDate.models.year.$modelValue);
                        angular.forEach(controllers, function (ngModel, key) {
                            ngModel.$setValidity('invalid_card_date', valid);
                        });
                    });
                }
            };
        })
        .directive('validateCardDateItem', function () {
            return {
                require: ['^validateCardDate', 'ngModel'],
                link: function (scope, elem, attr, ctrls) {
                    var ngModel = ctrls[1],
                        validateCardDate = ctrls[0];
                    validateCardDate.models[attr.validateCardDateItem] = ngModel;
                    scope.$on('$destroy', function () {
                        delete validateCardDate.models[attr.validateCardDateItem];
                    });
                }
            };
        })
        .directive('orderWentUp', ng(function ($timeout) {
            return {
                link: function (scope, element, attrs) {
                    var cb = function () {
                        if (element.hasClass('in')) {
                            scope.$eval(attrs.orderWentUp);
                        }
                    };
                    element.transitionEnd(cb);
                    scope.$on('$destroy', function () {
                        element.transitionEndOff(cb);
                    });
                }
            };
        })).filter('displayTaxes', ng(function () {
            return function (value) {
                var formatted = '';
                if (value) {
                    formatted = $.map(value, function (item) {
                        return item.name;
                    }).join(', ');
                }
                return formatted;
            };
        })).run(ng(function initModels(modelsMeta, modelsConfig, $sce, GLOBAL_CONFIG, $modal, modals, snackbar, $state, helpers, endpoint, $q, $filter, currentAccount, $mdSidenav, $timeout) {

            function init(models) {
                var cfg = {
                    current: function (sellerKey, opts) {
                        var that = this;
                        return models['19'].current().then(function (response) {
                            var buyer = response.data.entity;
                            return that.actions.view_order({
                                buyer: buyer.key,
                                seller: sellerKey
                            }, $.extend({
                                cache: that.getCacheKey('current' + sellerKey),
                                cacheType: 'memory'
                            }, opts));
                        });
                    },
                    adminManageModal: function (order, extraConfig) {
                        extraConfig = helpers.alwaysObject(extraConfig);
                        return this.manageModal(order, order._seller, undefined, $.extend({
                            sellerMode: true
                        }, extraConfig));
                    },
                    manageModal: function (order, seller, buyer, config) {
                        config = helpers.alwaysObject(config);
                        config.events = helpers.alwaysObject(config.events);
                        var args, that = this,
                            cartMode = config.cartMode,
                            cartModeRead = config.cartModeRead,
                            sellerMode = config.sellerMode,
                            openDefer = $q.defer(),
                            openPromise = openDefer.promise,
                            modalOpen,
                            controller,
                            track;
                        if (!cartMode) {
                            args = {
                                key: order.key,
                                read_arguments: {
                                    _lines: {
                                        config: {
                                            limit: 0
                                        }
                                    },
                                    _seller: {
                                        _content: {}
                                    },
                                    _messages: {
                                        _agent: {}
                                    }
                                }
                            };
                        } else {
                            args = {
                                buyer: buyer.key,
                                seller: seller.key,
                                read_arguments: {
                                    _seller: {
                                        _content: {}
                                    },
                                    _messages: {
                                        _agent: {}
                                    }
                                }
                            };
                        }

                        controller = ng(function ($scope) {
                            $scope.dialog = {
                                toolbar: {
                                    title: (((order && order.state && order.state !== 'cart') || !cartModeRead) ? 'Order' : 'Cart'),
                                    templateRight: 'order/toolbar_actions.html'
                                }
                            };
                            $scope.$state.promise(function () {
                                return models['34'].actions[cartMode ? 'view_order' : 'read'](args, {
                                    ignoreErrors: 2
                                });
                            }, function ($scope, response) {

                                $scope.messages = {
                                    toggle: function (close) {
                                        snackbar.showK('messangerDisabledWhenEmpty');
                                    }
                                };

                                $scope.close = function (override) {
                                    if (override !== true && ($scope.messages && $scope.messages.logMessages && $scope.messages.logMessages.length)) {
                                        modals.confirm('discard', function () {
                                            $scope.close(true);
                                        });
                                        return;
                                    }
                                    var promise = $scope.$close();
                                    promise.then(config.afterClose || angular.noop);
                                    if (track) {
                                        track.closeCart();
                                    }
                                    return promise;
                                };

                                if (response) {
                                    var errors = response.data.errors;
                                    if (errors && (errors.not_found || errors.malformed_key)) {
                                        $scope.notFound = cartModeRead === true ? 1 : 2;
                                        return;
                                    }
                                }
                                if (response.data.entity._seller) {
                                    seller = response.data.entity._seller;
                                }
                                var locals = {
                                    customPlaceholder: null,
                                    spawnAddress: null,
                                    updateLiveEntity: function (response, config) {
                                        config = helpers.alwaysObject(config);
                                        var messages = $scope.order._messages,
                                            lines = $scope.order._lines;
                                        $.extend($scope.order, response.data.entity);
                                        if (!config.deleted) {
                                            $scope.order._messages = messages;
                                        } else {
                                            lines = [];
                                            $scope.order._messages = [];
                                        }
                                        if (config.noLines) {
                                            $scope.order._lines = lines;
                                        }
                                        if (response.data.line_deleted_out_of_stock && response.data.line_deleted_out_of_stock.length) {
                                            angular.forEach($scope.order._lines.concat(), function (value, key) {
                                                if ($.inArray(value.key, response.data.line_deleted_out_of_stock) !== -1) {
                                                    $scope.order._lines.remove(value);
                                                }
                                            });
                                            snackbar.showK('outOfStockLinesRemoved');
                                        }
                                        lines = null;
                                    },
                                    reactOnStateChange: function (response) {
                                        helpers.update($scope.order, response.data.entity, ['state', 'ui']);
                                        locals.reactOnUpdate();
                                    },
                                    reactOnUpdate: function () {
                                        if (order) {
                                            $.extend(order, $scope.order);
                                        }
                                        that.removeCache('current' + seller.key);
                                    },
                                    logMessageAction: modelsMeta.getActionArguments('34', 'log_message'),
                                    orderUpdateFields: modelsMeta.getActionArguments('34', 'update'),
                                    billingAddressFields: [],
                                    shippingAddressFields: [],
                                    sorter: function (field, prev) {
                                        var indx = models['19'].manageModalFieldsOrder.indexOf(field.code_name),
                                            b = models['19'].manageModalFieldsOrder.indexOf(prev.code_name);
                                        if (indx === -1) {
                                            indx = 99999;
                                        }
                                        return indx - b;
                                    }
                                };

                                angular.forEach(locals.orderUpdateFields.shipping_address.modelclass, function (value) {
                                    $.extend(value.ui, {
                                        args: 'addresses.shipping.' + value.code_name,
                                        parentArgs: 'addresses.shipping',
                                        writable: true,
                                        writableCompiled: 'true',
                                        name: 'supplier_' + value.code_name
                                    });
                                    locals.shippingAddressFields.push(value);
                                });

                                angular.forEach(locals.orderUpdateFields.billing_address.modelclass, function (value) {
                                    $.extend(value.ui, {
                                        args: 'addresses.billing.' + value.code_name,
                                        parentArgs: 'addresses.billing',
                                        writable: true,
                                        writableCompiled: 'true',
                                        name: 'supplier_' + value.code_name
                                    });
                                    value.required = (value.required ? '!addresses.sameAsShipping' : false);
                                    locals.billingAddressFields.push(value);
                                });

                                locals.billingAddressFields.sort(locals.sorter);
                                locals.shippingAddressFields.sort(locals.sorter);

                                $.extend(locals.logMessageAction.message.ui, {
                                    label: false,
                                    args: 'messages.draft.message',
                                    parentArgs: 'messages.draft',
                                    writable: 'order.ui.rule.action.log_message.executable || !order.id',
                                    placeholder: 'Type a message here',
                                    attrs: {
                                        'native-placeholder': '',
                                        'class': 'primary',
                                        'min-length': '1',
                                        'on-enter': 'messages.logMessage()'
                                    }
                                });

                                $scope.dialog = {
                                    toolbar: {
                                        templateRight: 'order/toolbar_actions.html'
                                    }
                                };

                                $scope.$watch('order.state', function (neww, old) {
                                    var title = 'Cart';
                                    if (neww === 'order') {
                                        title = 'Order';
                                    }
                                    $scope.dialog.toolbar.title = title;
                                });

                                $scope.today = new Date();

                                $scope.writable = true;

                                $scope.stage = {
                                    checkout: null,
                                    time: 500,
                                    animating: 0,
                                    finishedAnimating: 1,
                                    isAnimating: function (c1) {
                                        return $scope.stage.finishedAnimating === c1;
                                    },
                                    endAnimation: function (ends) {
                                        $timeout(function () {
                                            $scope.stage.finishedAnimating = ends;
                                            $scope.stage.animating = -1;
                                        }, $scope.stage.time);
                                    },
                                    current: 1,
                                    out: [],
                                    canShowPay: function () {
                                        return $scope.order.payment_status === null && $scope.order.parent.parent.key === currentAccount.key;
                                    },
                                    isOut: function (indx) {
                                        return $.inArray(indx, $scope.stage.out) !== -1;
                                    },
                                    toCheckout: function () {
                                        $scope.stage.animating = 2;
                                        $scope.stage.out.push(1);
                                        $scope.stage.current = 2;
                                        helpers.fields.deferFormBuilderFields({
                                            '0': _.toArray(locals.orderUpdateFields.shipping_address.modelclass),
                                            '1': _.toArray(locals.orderUpdateFields.billing_address.modelclass)
                                        }).then(function () {
                                            $scope.addresses.finalizeFields = true;
                                        });

                                        track.proceedToCheckoutSuccess();
                                    },
                                    toDeliveryMethod: function () {
                                        var valid = $scope.addresses.form.shipping.$valid,
                                            addressing = {
                                                shipping_address: $scope.addresses.shipping
                                            };
                                        if (!$scope.addresses.sameAsShipping) {
                                            valid = valid && $scope.addresses.form.billing.$valid;
                                            addressing.billing_address = $scope.addresses.billing;
                                        } else {
                                            addressing.billing_address = $scope.addresses.shipping;
                                        }
                                        if (valid) {
                                            $scope.cmd.order.update(addressing, {
                                                disableUI: true
                                            }).then(function (response) {
                                                if (helpers.endpoint.isResponseError(response)) {
                                                    track.selectShippingMethodFail();
                                                    return;
                                                }
                                                $scope.stage.animating = 3;
                                                $scope.stage.out.push(2);
                                                $scope.stage.current = 3;
                                                track.selectShippingMethodSuccess();
                                            }, function () {
                                                track.selectShippingMethodFail();
                                            });
                                        } else {
                                            helpers.form.wakeUp($scope.addresses.form.shipping);
                                            if (!$scope.addresses.sameAsShipping) {
                                                helpers.form.wakeUp($scope.addresses.form.billing);
                                            }
                                            track.selectShippingMethodFail();
                                            snackbar.showK('actionFailedCheckForm');
                                        }
                                    },
                                    toReviewOrder: function () {
                                        if ($scope.carrier.form.$valid) {
                                            // state = 'checkout' is needed here
                                            $scope.cmd.order.update({
                                                carrier: $scope.carrier.selected
                                            }, {
                                                disableUI: true
                                            }).then(function () {
                                                $scope.stage.animating = 4;
                                                $scope.stage.out.push(3);
                                                $scope.stage.current = 4;
                                                track.reviewCartSuccess();
                                            }, function () {
                                                track.reviewCartFail();
                                            });
                                        } else {
                                            helpers.form.wakeUp($scope.carrier.form, false, true);
                                            track.reviewCartFail();
                                        }
                                    },
                                    toPayWithCreditCard: function () {
                                        $scope.stage.animating = 5;
                                        $scope.stage.out.push(4);
                                        $scope.stage.current = 5;
                                        track.payWithCardSuccess();
                                    },
                                    complete: function () {
                                        $scope.stage.out = [];
                                        $scope.stage.current = 1;
                                    }
                                };
                                $scope.logoImageConfig = {
                                    size: 280
                                };

                                locals.spawnAddress = function (addr) {
                                    if (!addr) {
                                        return addr;
                                    }
                                    addr._spawned = true;
                                    addr = angular.copy(addr);
                                    addr.country = null;
                                    addr.kind = '14';
                                    delete addr.key;
                                    addr.region = null;
                                    models['12'].all().then(function (response) {
                                        addr.country = _.findWhere(response.data.entities, {
                                            id: addr.country_code.toLowerCase()
                                        }).key;
                                        return models['13'].actions.search({
                                            search: {
                                                keys: [
                                                    [
                                                        ['12', addr.country_code.toLowerCase(), '13', addr.region_code.toLowerCase()]
                                                    ]
                                                ]
                                            }
                                        }, {
                                            cache: true
                                        }).then(function (response) {
                                            addr.region = response.data.entities[0].key;
                                        });
                                    });
                                    return addr;
                                };

                                $scope.cmd = {};
                                $scope.container = {};
                                $scope.cartMode = cartMode;
                                $scope.cartModeRead = cartMode;
                                $scope.sellerMode = sellerMode;
                                $scope.order = response.data.entity;
                                track = helpers.track.proxyLabelToEvents(config.track || helpers.track.noop.cartBuyerCarts, config.relativeUrl);
                                $scope.seller = seller;
                                $scope.currentAccount = currentAccount;
                                $scope.addresses = {
                                    finalizeFields: false,
                                    sameAsShipping: true,
                                    form: {},
                                    shipping: locals.spawnAddress($scope.order.shipping_address) || {},
                                    billing: locals.spawnAddress($scope.order.billing_address) || {},
                                    browse: function (type) {
                                        var parentScope = $scope;
                                        $modal.open({
                                            inDirection: false,
                                            windowClass: 'modal-medium-simple',
                                            outDirection: false,
                                            fullScreen: false,
                                            backdrop: true,
                                            templateUrl: 'order/browse_addresses.html',
                                            controller: ng(function ($scope) {
                                                $scope.$state.promise(function () {
                                                    return models['19'].current();
                                                }, function ($scope, response) {
                                                    $scope.addresses = response.data.entity.addresses;
                                                    $scope.select = function (ent) {
                                                        var doit = function () {
                                                            angular.forEach(ent, function (value, key) {
                                                                parentScope.addresses[type][key] = value;
                                                            });
                                                        };
                                                        doit();
                                                        $scope.$close().then(function () {
                                                            $timeout(doit, 100); // fix for region
                                                        }); // scope apply
                                                        if (type === 'billing') {
                                                            track.useSavedAddressForBilling();
                                                        } else {
                                                            track.useSavedAddressForShipping();
                                                        }
                                                    };
                                                    $scope.manage = function () {
                                                        models['19'].manageModal(response.data.entity.parent.key, function (buyerScope) {
                                                            $scope.addresses = buyerScope.args.addresses;
                                                        }, {
                                                            inDirection: false,
                                                            outDirection: false
                                                        });
                                                    };
                                                });
                                            })
                                        });
                                    },
                                    fields: {
                                        shipping: locals.shippingAddressFields,
                                        billing: locals.billingAddressFields,
                                        sameAsShipping: {
                                            type: 'SuperBooleanProperty',
                                            code_name: 'sameAsShipping',
                                            ui: {
                                                writable: true,
                                                parentArgs: 'addresses',
                                                args: 'addresses.sameAsShipping',
                                                specifics: {
                                                    type: 'checkbox'
                                                }
                                            }
                                        }
                                    }
                                };

                                if (!$scope.addresses.shipping._spawned) {
                                    helpers.location.updateDefaults($scope.addresses.shipping);
                                }

                                if (!$scope.addresses.billing._spawned) {
                                    helpers.location.updateDefaults($scope.addresses.billing);
                                }

                                $scope.payment = {
                                    method: $scope.order.payment_method
                                };

                                $scope.carrier = {
                                    selected: $scope.order.carrier ? $scope.order.carrier.reference : null,
                                    available: (response.data.carriers || []),
                                    form: null
                                };

                                $scope.format = {
                                    variantVisible: function (variant) {
                                        var value = $scope.format.variantValue(variant);
                                        if (!angular.isString(value) || !value.length) {
                                            return false;
                                        }
                                        return true;
                                    },
                                    variantLabel: function (variant) {
                                        return Object.keys(variant)[0];
                                    },
                                    variantValue: function (variant) {
                                        return variant[$scope.format.variantLabel(variant)];
                                    }
                                };

                                if ($scope.order._messages && $scope.order._messages.length) {
                                    $scope.order._messages.reverse();
                                }

                                $scope.messages = {
                                    sentQueue: 0,
                                    isToday: function (message) {
                                        if (!message.created) {
                                            return false;
                                        }
                                        return ($scope.today.getDay() === message.created.getDay() && $scope.today.getMonth() === message.created.getMonth());
                                    },
                                    reader: $scope.order.id ? models['34'].reader({
                                        key: $scope.order.key,
                                        next: {
                                            _messages: angular.copy($scope.order._next_read_arguments._messages)
                                        },
                                        access: ['_messages'],
                                        complete: function (items) {
                                            $scope.order._messages.prepend(items);
                                        }
                                    }) : {},
                                    toggling: false,
                                    open: false,
                                    stateChanged: function (state) {
                                        $timeout(function () {
                                            $scope.messages.sync.toggle(state);
                                        }, 2000, 0);
                                        if (state) {
                                            track.openMessages();
                                        } else {
                                            track.closeMessages();
                                        }
                                        if ($scope.order.ui.rule.action.see_messages.executable) {
                                            models['34'].actions.see_messages({
                                                key: $scope.order.key
                                            }).then(function () {
                                                $scope.order._tracker = null;
                                                locals.reactOnUpdate();
                                            });
                                        }
                                    },
                                    seen: false,
                                    sync: {
                                        timer: null,
                                        active: false,
                                        stop: function () {
                                            this.active = false;
                                            this.loading = false;
                                            clearTimeout(this.timer);
                                        },
                                        start: function () {
                                            if (!$scope.order.id || !$scope.order._lines.length) {
                                                return;
                                            }
                                            this.active = true;
                                            this.run();
                                        },
                                        toggle: function (what) {
                                            if (what) {
                                                this.start();
                                            } else {
                                                this.stop();
                                            }
                                        },
                                        loading: false,
                                        run: function () {
                                            var sync = this;
                                            if (this.loading || !this.active) {
                                                return;
                                            }
                                            clearTimeout(this.timer);
                                            this.loading = true;
                                            this.timer = setTimeout(function () {
                                                models['34'].actions.read({
                                                    key: $scope.order.key,
                                                    read_arguments: {
                                                        _messages: {
                                                            _agent: {}
                                                        }
                                                    }
                                                }).then(function (response) {
                                                    var map = {},
                                                        changed = false,
                                                        items = response.data.entity._messages;
                                                    angular.forEach($scope.order._messages, function (value, key) {
                                                        map[value.key] = value;
                                                    });
                                                    angular.forEach(items, function (value) {
                                                        if (!map[value.key]) {
                                                            $scope.order._messages.push(value);
                                                            changed = true;
                                                        } else {
                                                            $.extend(map[value.key], value);
                                                        }
                                                    });
                                                    if (changed) {
                                                        $scope.messages.forceReflow();
                                                    }
                                                })['finally'](function () {
                                                    sync.loading = false;
                                                    sync.timer = null;
                                                    sync.run();
                                                });
                                            }, 10000);
                                        },
                                    },
                                    draft: {
                                        message: null,
                                        key: $scope.order.key
                                    },
                                    field: locals.logMessageAction.message,
                                    nav: function () {
                                        return $mdSidenav($scope.messages.sidebarID);
                                    },
                                    sent: false,
                                    resendMaybe: function (message) {
                                        if (!message._failed) {
                                            return;
                                        }
                                        message._failed = false;
                                        var newMessage = angular.copy(message);
                                        newMessage.key = $scope.order.key;
                                        newMessage.message = newMessage.body;
                                        return models['34'].actions.log_message(newMessage).then(function (response) {
                                            $scope.messages.forceReflow();
                                            if (!response.data.entity) {
                                                return;
                                            }
                                            $.extend(message, response.data.entity._messages[0]);
                                            locals.reactOnStateChange(response);
                                            return response;
                                        }, function () {
                                            message._failed = true;
                                        });
                                    },
                                    send: function (action, justMessage, message) {
                                        var copydraft = message || angular.copy($scope.messages.draft),
                                            newMessage = (message || $.extend(copydraft, {
                                                body: copydraft.message
                                            })),
                                            success = function (response) {
                                                if (!response.data.entity) {
                                                    return;
                                                }
                                                var created = newMessage.created;
                                                $.extend(newMessage, response.data.entity._messages[0]);
                                                newMessage.created = created;
                                                newMessage._failed = false;
                                                locals.reactOnStateChange(response);
                                                track.sendMessageSuccess();
                                                return response;
                                            },
                                            failure = function () {
                                                newMessage._failed = true;
                                                track.sendMessageFail();
                                            };
                                        if (!message) {
                                            $scope.messages.draft.message = '';
                                            newMessage.created = new Date();
                                            $scope.order._messages.push(newMessage);
                                        }
                                        $scope.container.messages.$setSubmitted(true);
                                        $scope.container.messages.$setPristine(true);
                                        $scope.messages.forceReflow();
                                        copydraft.key = $scope.order.key;
                                        newMessage.key = $scope.order.key;
                                        if (justMessage) {
                                            return newMessage;
                                        }
                                        return models['34'].actions[action](copydraft).then(success, failure);
                                    },
                                    forceReflow: function () {
                                        $scope.messages.sent = new Date().getTime();
                                    },
                                    sidebarID: 'messages' + _.uniqueId(),
                                    logMessages: [],
                                    logMessage: function () {
                                        var that = this;
                                        if (!$scope.order._lines.length) {
                                            snackbar.showK('messangerDisabledWhenEmpty');
                                            return;
                                        }
                                        if ($scope.messages.draft.message === undefined || !$scope.messages.draft.message.length) {
                                            return;
                                        }
                                        if ($scope.container.messages.$valid) {
                                            $scope.messages.sentQueue += 1;
                                            $scope.messages.sync.stop();
                                            var finall = function () {
                                                    if ($scope.messages.logMessages.length) {
                                                        var cb = $scope.messages.logMessages.shift();
                                                        cb();
                                                    }
                                                    $scope.messages.sentQueue -= 1;
                                                    if (!$scope.messages.sentQueue) {
                                                        $scope.messages.sync.start();
                                                        $scope.messages.sentQueue = 0;
                                                    }
                                                },
                                                promise,
                                                prepare;
                                            if ($scope.messages.logMessages.length > 0) {
                                                prepare = that.send('log_message', true);
                                                $scope.messages.logMessages.push(function () {
                                                    var nextPromise = that.send('log_message', false, prepare);
                                                    nextPromise['finally'](finall);
                                                });
                                                return promise;
                                            }
                                            promise = this.send('log_message');
                                            var fn = function () {};
                                            $scope.messages.logMessages.push(fn);
                                            promise['finally'](function () {
                                                $scope.messages.logMessages.remove(fn);
                                                finall.apply(this, arguments);
                                            });
                                            return promise;
                                        }
                                        helpers.form.wakeUp($scope.container.messages, false, true);
                                    },
                                    close: function () {
                                        return $scope.message.toggle(true);
                                    },
                                    toggle: function (close) {
                                        if (!$scope.order._lines.length) {
                                            snackbar.showK('messangerDisabledWhenEmpty');
                                            return;
                                        }
                                        if ($scope.messages.toggling) {
                                            return;
                                        }
                                        var it = $scope.messages.nav(),
                                            isOpen = it.isOpen();
                                        $scope.messages.toggling = true;
                                        if (close === true) {
                                            isOpen = true;
                                        }
                                        $timeout(function () {
                                            it[isOpen ? 'close' : 'open']().then(function () {
                                                $scope.messages.toggling = false;
                                                $scope.messages.open = !isOpen;
                                                $scope.messages.forceReflow();
                                            });
                                        });
                                    }
                                };

                                $scope.cmd.order = {
                                    scheduleUpdatePromise: null,
                                    scheduleNext: true,
                                    scheduleLoading: false,
                                    scheduleUpdate: function (extra, config) {
                                        var that = this;
                                        if (that.scheduleLoading) {
                                            that.scheduleNext = [extra, config];
                                        } else {
                                            that.scheduleLoading = true;
                                            that.scheduleNext = null;
                                            that.scheduleUpdatePromise = that.update(extra, config).then(function (response) {
                                                that.scheduleLoading = false;
                                                if (that.scheduleNext) {
                                                    return that.scheduleUpdate.apply(that, that.scheduleNext);
                                                }
                                                return response;
                                            });
                                        }
                                        return that.scheduleUpdatePromise;
                                    },
                                    update: function (extra, config) {
                                        config = helpers.alwaysObject(config);
                                        var data = {
                                                key: $scope.order.key,
                                                payment_method: $scope.payment.method,
                                                _lines: $scope.order._lines
                                            },
                                            deleteMaybe,
                                            promise;
                                        $.extend(data, extra);
                                        deleteMaybe = function () {
                                            var allDeleted = true;
                                            angular.forEach($scope.order._lines, function (value) {
                                                if (value._state !== 'deleted' || value.product.quantity.toString() !== '0') {
                                                    allDeleted = false;
                                                }
                                            });
                                            if (allDeleted) {
                                                return $scope.cmd.order['delete'](false, true);
                                            }
                                            return false;
                                        };
                                        promise = deleteMaybe();
                                        if (promise) {
                                            return promise;
                                        }
                                        return models['34'].actions.update(data, {
                                            ignoreErrors: 2,
                                            activitySpinner: !config.noLoader,
                                            disableUI: (angular.isDefined(config.disableUI) ? config.disableUI : true)
                                        }).then(function (response) {
                                            var errors = response.data.errors;
                                            if (errors) {
                                                if (errors.plugin_error && $.inArray('invalid_address', errors.plugin_error) !== -1) {
                                                    snackbar.showK('sellerProhibtsAddress');
                                                }
                                                return response;
                                            }
                                            locals.updateLiveEntity(response, config);
                                            locals.reactOnUpdate();
                                            $scope.carrier.available = response.data.carriers;
                                            $scope.carrier.selected = response.data.entity.carrier ? response.data.entity.carrier.reference : null;
                                            deleteMaybe();
                                            return response;
                                        });
                                    },
                                    showNetTotalAmount: function () {
                                        var untaxed = parseFloat($scope.order.untaxed_amount, 10);
                                        if ($scope.stage.current === 1) {
                                            if ($scope.order.carrier && $scope.order.carrier.subtotal) {
                                                untaxed -= parseFloat($scope.order.carrier.subtotal, 10);
                                            }
                                            return untaxed;
                                        }
                                        return untaxed;
                                    },
                                    showTotalAmount: function () {
                                        var total = parseFloat($scope.order.total_amount, 10);
                                        if ($scope.stage.current === 1) {
                                            if ($scope.order.carrier && $scope.order.carrier.subtotal) {
                                                total -= parseFloat($scope.order.carrier.subtotal, 10);
                                            }
                                            if ($scope.order.tax_amount) {
                                                total -= parseFloat($scope.order.tax_amount, 10);
                                            }
                                            return total;
                                        }
                                        return total;
                                    },
                                    'delete': function (cart, now) {
                                        var execd,
                                            exec = function () {
                                                execd = true;
                                                var promise = models['34'].actions['delete']({
                                                    key: $scope.order.key
                                                }, {
                                                    activitySpinner: true,
                                                    disableUI: true
                                                });
                                                promise.then(function (response) {
                                                    locals.updateLiveEntity(response);
                                                    locals.reactOnUpdate();
                                                    snackbar.showK('cartUpdated');
                                                });
                                                return promise;
                                            };
                                        if (now) {
                                            return exec();
                                        }
                                        track.initiateEmptyCart();
                                        modals.confirm('delete' + (cart ? 'Cart' : 'Order'), function () {
                                            exec();
                                            track.confirmEmptyCart();
                                        }).result.then(function () {
                                            if (!execd) {
                                                track.cancelEmptyCart();
                                            }
                                        });
                                    }
                                };

                                $scope.$watch('order._state', function (neww) {
                                    if (neww === 'deleted') {
                                        $scope.stage.out = [];
                                        $scope.stage.current = 1;
                                    }
                                });

                                $scope.cmd.line = {
                                    view: function (line, $event) {
                                        var path = line.product._reference;
                                        models['31'].viewProductModal(path.parent.parent.parent.key,
                                            path.parent.parent.key, path.pricetag.key,
                                            line.product.variant_signature, {
                                                popFrom: helpers.clicks.realEventTarget($event.target),
                                                sellerKey: seller.key,
                                                track: track.product,
                                                events: {
                                                    addToCart: function (response, deleted) {
                                                        locals.updateLiveEntity.call($scope, response, {
                                                            deleted: deleted
                                                        });
                                                        locals.reactOnUpdate();
                                                    }
                                                }
                                            });
                                    },
                                    remove: function (line) {
                                        line.quantity = 0;
                                        line._state = 'deleted';
                                    }
                                };

                                $scope.cmd.seller = {
                                    view: function () {
                                        $scope.sellerDetails.menu.open();
                                    }
                                };

                                $scope.sellerDetails = models['23'].makeSellerDetails($scope.seller);

                                $scope.lineDrag = {
                                    options: {
                                        disabled: false,
                                        cancel: 'input,textarea,button,select,option,[disabled]',
                                        axis: 'x',
                                        handle: '.sort-handle',
                                        distance: 10,
                                        stop: function (e, ui) {
                                            $scope.$apply();
                                        }
                                    },
                                    whatSortMeans: function () {
                                        modals.alert('howToDeleteDragging');
                                    },
                                    onStart: function (e, ui, line) {
                                        $(ui.helper).find('.sort-handle').addClass('dragged');
                                    },
                                    onDrag: function (e, ui, line) {
                                        var deleteMode,
                                            division,
                                            helperWidth = ui.helper.width();
                                        division = ui.offset.left + helperWidth;
                                        if (division < (helperWidth / 2)) {
                                            deleteMode = true;
                                        }
                                        if (line) {
                                            if (deleteMode) {
                                                ui.helper.addClass('about-to-delete');
                                            } else {
                                                ui.helper.removeClass('about-to-delete');
                                            }
                                        }
                                    },
                                    onStop: function (e, ui, line) {
                                        if (ui.helper.hasClass('about-to-delete')) {
                                            ui.helper.animate({
                                                left: (ui.helper.width() * 2) * -1
                                            }, function () {
                                                $timeout(function () {
                                                    line.product.quantity = '0';
                                                    line._state = 'deleted';
                                                    ui.helper.hide();
                                                    $scope.cmd.order.scheduleUpdate(undefined, {
                                                        noLines: true,
                                                        disableUI: true
                                                    }).then(function (response) {
                                                        if (!(response && response.then)) {
                                                            snackbar.showK('cartUpdated');
                                                        }
                                                        track.removeLineSuccess();
                                                    }, function () {
                                                        line._state = null;
                                                        track.removeLineFail();
                                                    });
                                                });
                                            });
                                        } else {
                                            ui.helper.animate(ui.originalPosition, function () {
                                                ui.helper.attr('style', '');
                                            });
                                        }
                                    }
                                };

                                (function () {
                                    if ($scope.order.state === 'order') {
                                        $scope.stage.out.extend([1, 2, 3]);
                                        $scope.stage.current = 4;
                                        $scope.stage.checkout = 1;
                                    }
                                }());


                                $scope.$watch('order._lines.length', function (neww, old) {
                                    if (neww < 1) {
                                        $scope.notFound = 1;
                                    } else {
                                        $scope.notFound = undefined;
                                    }
                                    $timeout(function () {
                                        $(window).triggerHandler('resize');
                                    }, 100, false);
                                });

                                $scope.$on('$destroy', function () {
                                    $scope.messages.sync.stop();
                                });

                                $scope.sellerDetails.stateChanged = function (state) {
                                    if (state) {
                                        track.openSellerDrawer();
                                    } else {
                                        track.closeSellerDrawer();
                                    }
                                };

                                $scope.sellerDetails.getTrack = function () {
                                    return helpers.track.proxyLabelToEvents(track.seller, config.relativeUrl);
                                };

                                $scope.$watch('order.key', function (neww, old) {
                                    if (neww !== old && config.events.newOrder) {
                                        config.events.newOrder($scope.order);
                                    }
                                });
                                $scope.stripe = {
                                    args: {},
                                    pay: function () {
                                        window.Stripe.setPublishableKey($scope.seller._stripe_publishable_key);
                                        if (!$scope.stripe.form.$valid) {
                                            return helpers.form.wakeUp($scope.stripe.form);
                                        }
                                        $scope.disableUI(true);

                                        function stripeResponseHandler(status, response) {
                                            if (response.error) {
                                                // Show the errors on the form
                                                $scope.disableUI(false);
                                                snackbar.show(response.error.message);
                                                track.payFail();
                                            } else {
                                                // token contains id, last4, and card type
                                                models['34'].actions.pay({
                                                    key: $scope.order.key,
                                                    token: response.id
                                                }, {
                                                    activitySpinner: true,
                                                    disableUI: true
                                                }).then(function (response) {
                                                    locals.updateLiveEntity(response);
                                                    locals.reactOnUpdate();
                                                    snackbar.showK('orderPaymentCardSuccess');
                                                    $scope.stage.animating = 6;
                                                    $scope.stage.out.push(5);
                                                    $scope.stage.current = 6;
                                                    $scope.stage.checkout = 1;
                                                    track.paySuccess();
                                                }, function (response) {
                                                    track.payFail();
                                                    if (response && response.data.errors && response.data.errors.plugin_error) {
                                                        if ($.inArray('no_payment_method_supplied', response.data.errors.plugin_error) !== -1) {
                                                            snackbar.showK('orderPaymentNoPaymentMethodSupplied');
                                                        }
                                                        if ($.inArray('payment_failed', response.data.errors.plugin_error) !== -1) {
                                                            snackbar.showK('orderPaymentFailed');
                                                        }
                                                        if ($.inArray('invalid_number', response.data.errors.plugin_error) !== -1) {
                                                            snackbar.showK('orderPaymentInvalidNumber');
                                                        }
                                                        if ($.inArray('invalid_expiry_month', response.data.errors.plugin_error) !== -1) {
                                                            snackbar.showK('orderPaymentInvalidExpiryMonth');
                                                        }
                                                        if ($.inArray('invalid_expiry_year', response.data.errors.plugin_error) !== -1) {
                                                            snackbar.showK('orderPaymentInvalidExpiryYear');
                                                        }
                                                        if ($.inArray('invalid_cvc', response.data.errors.plugin_error) !== -1) {
                                                            snackbar.showK('orderPaymentInvalidCVC');
                                                        }
                                                        if ($.inArray('incorrect_number', response.data.errors.plugin_error) !== -1) {
                                                            snackbar.showK('orderPaymentIncorrectNumber');
                                                        }
                                                        if ($.inArray('expired_card', response.data.errors.plugin_error) !== -1) {
                                                            snackbar.showK('orderPaymentExpiredCard');
                                                        }
                                                        if ($.inArray('incorrect_cvc', response.data.errors.plugin_error) !== -1) {
                                                            snackbar.showK('orderPaymentIncorrectCVC');
                                                        }
                                                        if ($.inArray('incorrect_zip', response.data.errors.plugin_error) !== -1) {
                                                            snackbar.showK('orderPaymentIncorrectZip');
                                                        }
                                                        if ($.inArray('card_declined', response.data.errors.plugin_error) !== -1) {
                                                            snackbar.showK('orderPaymentCardDeclined');
                                                        }
                                                        if ($.inArray('missing', response.data.errors.plugin_error) !== -1) {
                                                            snackbar.showK('orderPaymentMissing');
                                                        }
                                                        if ($.inArray('processing_error', response.data.errors.plugin_error) !== -1) {
                                                            snackbar.showK('orderPaymentProcessingError');
                                                        }
                                                    }
                                                });
                                            }
                                        }

                                        window.Stripe.card.createToken({
                                            number: $scope.stripe.args.card_number,
                                            cvc: $scope.stripe.args.cvc,
                                            exp_month: $scope.stripe.args.card_exp_1,
                                            exp_year: $scope.stripe.args.card_exp_2
                                        }, stripeResponseHandler);
                                    },
                                    payWithConfidence: function () {
                                        $modal.open({
                                            templateUrl: 'core/models/manage.html',
                                            controller: ng(function ($scope) {
                                                $scope.dialog = {};
                                                $scope.dialog.templateBodyUrl = 'order/pay_with_confidence.html';
                                                $scope.dialog.toolbar = {
                                                    hideSave: true,
                                                    leftIcon: 'arrow_back',
                                                    title: GLOBAL_CONFIG.toolbar.titles.payWithConfidence
                                                };
                                            })
                                        });
                                    },
                                    fields: {
                                        cc: {
                                            _maker_: 'order',
                                            type: 'SuperStringProperty',
                                            code_name: 'card_number',
                                            required: true,
                                            ui: {
                                                args: 'stripe.args.card_number',
                                                writable: true,
                                                attrs: {
                                                    'validate-card-number': true
                                                }
                                            }
                                        },
                                        exp1: {
                                            _maker_: 'order',
                                            type: 'SuperStringProperty',
                                            code_name: 'card_exp_1',
                                            required: true,
                                            ui: {
                                                attrs: {
                                                    'validate-card-date-item': 'month'
                                                },
                                                hideMessages: true,
                                                label: false,
                                                args: 'stripe.args.card_exp_1',
                                                writable: true
                                            }
                                        },
                                        exp2: {
                                            _maker_: 'order',
                                            type: 'SuperStringProperty',
                                            code_name: 'card_exp_2',
                                            required: true,
                                            ui: {
                                                attrs: {
                                                    'validate-card-date-item': 'year'
                                                },
                                                hideMessages: true,
                                                label: false,
                                                args: 'stripe.args.card_exp_2',
                                                writable: true
                                            }
                                        },
                                        cvc: {
                                            _maker_: 'order',
                                            type: 'SuperStringProperty',
                                            code_name: 'cvc',
                                            required: true,
                                            ui: {
                                                attrs: {
                                                    'validate-cvc': true
                                                },
                                                args: 'stripe.args.cvc',
                                                writable: true
                                            }
                                        }
                                    },
                                    expires: {
                                        messages: function () {
                                            var messages = {
                                                help: true
                                            };
                                            angular.forEach([$scope.stripe.fields.exp1, $scope.stripe.fields.exp2], function (field) {
                                                if (field.ui.form.hasErrors() && field.ui.form.field().$dirty) {
                                                    messages = field.ui.form.messages();
                                                }
                                            });
                                            return messages;
                                        },
                                        shouldShowMessages: function () {
                                            return true;
                                        }
                                    }
                                };

                                track.openCart();

                                openDefer.resolve($scope.order);

                            });
                        });

                        modalOpen = {
                            templateUrl: 'order/view.html',
                            controller: controller
                        };

                        $.extend(modalOpen, config);

                        $modal.open(modalOpen);

                        return openPromise;

                    }
                };
                $.extend(models['34'], cfg);

            }

            modelsConfig(init);

        }));
}());
