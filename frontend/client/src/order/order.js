(function () {
    'use strict';
    angular.module('app').directive('sendMessage', function ($parse) {
        return {
            restrict: 'A',
            link: function (scope, element, attrs) {
                var callback = $parse(attrs.sendMessage),
                    root = element.parents('.modal-dialog:first'),
                    textarea,
                    pane,
                    click = function (e) {
                        textarea = root.find('textarea');
                        pane = root.find('.overflow-y');
                        if (textarea.length && textarea.val()) {
                            callback(scope);
                        } else {
                            pane.stop().scrollTo(textarea, 100, function () {
                                textarea.focus();
                            });
                        }
                        e.preventDefault();
                    };

                element.on('click', click);

                scope.$on('$destroy', function () {
                    element.off('click', click);
                });

            }
        };
    }).directive('alwaysScrollToBottom', function ($timeout) {
        return {
            link: function (scope, element, attrs) {
                var cb = function () {
                    element.scrollTop(element[0].scrollHeight);
                };

                scope.$watchGroup(scope.$eval(attrs.alwaysScrollToBottom), function (neww, old) {
                    if (neww !== old) {
                        cb();
                    }
                });
            }
        };
    }).filter('displayTaxes', function () {
        return function (value) {
            var formatted = '';
            if (value) {
                formatted = $.map(value, function (item) {
                    return item.name;
                }).join(', ');
            }
            return formatted;
        };
    }).run(function (modelsMeta, modelsConfig, $modal, modals, helpers, endpoint, $q, $filter, currentAccount, $mdSidenav, $timeout) {
        modelsConfig(function (models) {
            $.extend(models['34'], {
                current: function (sellerKey) {
                    var that = this;
                    return models['19'].current().then(function (response) {
                        var buyer = response.data.entity;
                        return that.actions.view_order({
                            buyer: buyer.key,
                            seller: sellerKey
                        }, {
                            cache: that.getCacheKey('current' + sellerKey),
                            cacheType: 'memory'
                        });
                    });
                },
                adminManageModal: function (order) {
                    return this.manageModal(order, order._seller, undefined, {
                        sellerMode: true
                    });
                },
                manageModal: function (order, seller, buyer, config) {
                    config = helpers.alwaysObject(config);
                    var args, that = this,
                        cartMode = config.cartMode,
                        sellerMode = config.sellerMode,
                        rpc = {};
                    if (!cartMode) {
                        args = {
                            key: order.key,
                            read_arguments: {
                                _lines: {
                                    config: {
                                        options: {
                                            limit: 0
                                        }
                                    }
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
                                _messages: {
                                    _agent: {}
                                }
                            }
                        };
                    }

                    models['34'].actions[cartMode ? 'view_order' : 'read'](args, rpc).then(function (response) {

                        if (!response.data.entity.id) {
                            modals.alert('cartNotFound');
                            return;
                        }

                        $modal.open({
                            templateUrl: 'order/view.html',
                            controller: function ($scope) {
                                var locals = {
                                    updateLiveEntity: function (response) {
                                        var messages = $scope.order._messages;
                                        $.extend($scope.order, response.data.entity);
                                        $scope.order._messages = messages;
                                    },
                                    reactOnStateChange: function (response) {
                                        helpers.update($scope.order, response.data.entity, ['state', 'ui']);
                                        locals.reactOnUpdate();
                                    },
                                    reactOnUpdate: function () {
                                        if (order) {
                                            $.extend(order, $scope.order);
                                        }
                                        if (that.getCache('current' + $scope.seller.key)) {
                                            that.current($scope.seller.key).then(function (response) {
                                                $.extend(response.data.entity, $scope.order);
                                            });
                                        }
                                    },
                                    logMessageAction: modelsMeta.getActionArguments('34', 'log_message')
                                };

                                $.extend(locals.logMessageAction.message.ui, {
                                    label: false,
                                    args: 'messages.draft.message',
                                    parentArgs: 'messages.draft',
                                    writable: true,
                                    placeholder: 'Type message here.',
                                    attrs: {
                                        'native-placeholder': '',
                                        'class': 'primary'
                                    }
                                });

                                $scope.dialog = {
                                    toolbar: {
                                        templateRight: 'order/toolbar_actions.html'
                                    }
                                };

                                $scope.stage = {
                                    current: 1,
                                    next: function () {
                                        $scope.stage.current += 1;
                                        var cb = $scope.stage['callStage' + $scope.stage.current];
                                        if (cb) {
                                            cb();
                                        }
                                    }
                                };
                                $scope.cmd = {};
                                $scope.container = {};
                                $scope.cartMode = cartMode;
                                $scope.sellerMode = sellerMode;
                                $scope.order = response.data.entity;
                                $scope.seller = seller;
                                $scope.currentAccount = currentAccount;
                                $scope.addresses = {
                                    sameAsBilling: false,
                                    shipping: {},
                                    billing: {},
                                    fields: {
                                        shipping: {},
                                        billing: {}
                                    },
                                    useSaved: function () {}
                                };

                                $scope.payment = {
                                    method: $scope.order.payment_method
                                };

                                $scope.carrier = {
                                    selected: $scope.order.carrier ? $scope.order.carrier.reference : null,
                                    available: []
                                };

                                $scope.format = {
                                    variantLabel: function (variant) {
                                        return Object.keys(variant)[0];
                                    },
                                    variantValue: function (variant) {
                                        return variant[$scope.format.variantLabel(variant)];
                                    }
                                };

                                $scope.messages = {
                                    reader: models['34'].reader({
                                        kind: '34',
                                        key: $scope.order.key,
                                        next: {
                                            _messages: angular.copy($scope.order._next_read_arguments._messages)
                                        },
                                        access: ['_messages'],
                                        complete: function (items) {
                                            $scope.order._messages.prepend(items);
                                        }
                                    }),
                                    toggling: false,
                                    open: false,
                                    draft: {
                                        message: null,
                                        key: $scope.order.key
                                    },
                                    field: locals.logMessageAction.message,
                                    nav: function () {
                                        return $mdSidenav('right_messages');
                                    },
                                    sent: false,
                                    send: function (action) {
                                        models['34'].actions[action]($scope.messages.draft).then(function (response) {
                                            $scope.messages.draft.message = '';
                                            $scope.messages.sent = !$scope.messages.sent;
                                            $scope.order._messages.push(response.data.entity._messages[0]);
                                            locals.reactOnStateChange(response);
                                        });
                                    },
                                    logMessage: function () {
                                        return this.send('log_message');
                                    },
                                    reviewFeedback: function () {
                                        return this.send('review_feedback');
                                    },
                                    sudoFeedback: function () {
                                        return this.send('sudo_feedback');
                                    },
                                    leaveFeedback: function () {
                                        return this.send('leave_feedback');
                                    },
                                    reportFeedback: function () {
                                        return this.send('report_feedback');
                                    },
                                    close: function () {
                                        return $scope.message.toggle(true);
                                    },
                                    toggle: function (close) {
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
                                            });
                                        });
                                    },
                                };

                                $scope.feedback = {
                                    admin: function () {},
                                    buyer: function () {},
                                    seller: function () {}
                                };

                                $scope.cmd.order = {
                                    update: function (extra) {
                                        var data = {
                                            key: $scope.order.key,
                                            payment_method: $scope.payment.method,
                                            _lines: $scope.order._lines
                                        };
                                        if ($scope.stage.current > 1) {
                                            $.extend(data, {
                                                billing_address: $scope.addresses.billing,
                                                shipping_address: $scope.addresses.shipping
                                            });
                                        }

                                        if ($scope.stage.current > 2) {
                                            data.carrier = $scope.carriers.selected;
                                        }

                                        $.extend(data, extra);
                                        return models['34'].actions.update(data).then(function (response) {
                                            locals.updateLiveEntity(response);
                                            locals.reactOnUpdate();
                                        });
                                    },
                                    checkout: function () {
                                        if ($scope.order.state !== 'checkout') {
                                            return $scope.orderCmd.update({
                                                state: 'checkout'
                                            });
                                        }
                                    },
                                    cancel: function () {
                                        if ($scope.order.state === 'checkout') {
                                            modals.confirm('cancelOrder', function () {
                                                models['34'].actions.cancel({
                                                    key: $scope.order.key
                                                }).then(function (response) {
                                                    models['34'].removeCache('current' + seller.key);
                                                    $scope.close();
                                                });
                                            });
                                        }
                                    }
                                };

                                $scope.cmd.line = {
                                    view: function (line) {
                                        var path = line.product._reference;
                                        models['31'].viewProductModal(path.parent.parent.parent.key,
                                            path.parent.parent.key, path.pricetag.key,
                                            line.product.variant_signature, {
                                                events: {
                                                    addToCart: locals.updateLiveEntity
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
                                        models['23'].viewModal($scope.seller);
                                    }
                                };

                                $scope.close = function () {
                                    $scope.$close();
                                };

                                var gr = null;

                                $scope.lineSorting = {
                                    disabled: false,
                                    axis: 'x',
                                    whatSortMeans: function () {
                                        modals.alert('howToDeleteLine');
                                    },
                                    handle: '.sort-handle',
                                    sort: function (e, ui) {
                                        var deleteMode,
                                            division,
                                            helperWidth = ui.helper.width(),
                                            itemScope = ui.item.scope(),
                                            item = itemScope.$eval(ui.item.attr('current-item'));
                                        division = ui.offset.left + helperWidth;
                                        if (division < (helperWidth / 2)) {
                                            deleteMode = true;
                                        }
                                        if (item) {
                                            if (deleteMode) {
                                                ui.helper.addClass('about-to-delete');
                                                item._state = 'deleted';
                                            } else {
                                                ui.helper.removeClass('about-to-delete');
                                                item._state = null;
                                            }
                                        }
                                        if (gr === null) {
                                            gr = ui.helper.clone().attr('style', '').css('visibility', 'hidden');
                                            ui.helper.after(gr);
                                        }
                                    },
                                    stop: function (e, ui) {
                                        $scope.$apply();
                                        console.log('stop');
                                        gr.remove();
                                        gr = null;
                                    }
                                };

                                $scope.notifyUrl = helpers.url.abs('api/order/complete/paypal');
                                $scope.completePath = helpers.url.abs('payment/completed/' + $scope.order.key);
                                $scope.cancelPath = helpers.url.abs('payment/canceled/' + $scope.order.key);

                            }
                        });


                    });

                }
            });

        });

        // old
        modelsConfig(function (models) {
            if (models) {
                return;
            }
            $.extend(models['34'], {
                current: function (sellerKey) {
                    var that = this;
                    return models['19'].current().then(function (response) {
                        var buyer = response.data.entity;
                        return that.actions.view_order({
                            buyer: buyer.key,
                            seller: sellerKey
                        }, {
                            cache: that.getCacheKey('current' + sellerKey),
                            cacheType: 'memory'
                        });
                    });
                },
                adminManageModal: function (order) {
                    return this.manageModal(order, order._seller, undefined, {
                        sellerMode: true
                    });
                },
                manageModal: function (order, seller, buyer, config) {
                    config = helpers.alwaysObject(config);
                    var args, that = this,
                        cartMode = config.cartMode,
                        sellerMode = config.sellerMode,
                        rpc = {};

                    if (!cartMode) {
                        args = {
                            key: order.key,
                            read_arguments: {
                                _lines: {
                                    config: {
                                        options: {
                                            limit: 0
                                        }
                                    }
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
                                _messages: {
                                    _agent: {}
                                }
                            }
                        };
                    }

                    models['34'].actions[cartMode ? 'view_order' : 'read'](args, rpc).then(function (response) {

                        if (!response.data.entity.id) {
                            modals.alert('cartNotFound');
                            return;
                        }

                        $modal.open({
                            templateUrl: 'order/view.html',
                            controller: function ($scope) {
                                var billing_addresses, shipping_addresses, reactOnStateChange, reactOnUpdate, updateLiveEntity,
                                    orderActionsFields = modelsMeta.getActionArguments('34'),
                                    prepareMessageFields,
                                    displayAddress = function (address) {
                                        var addr = [];
                                        angular.forEach(['name', 'street', 'city', '_region.name', 'postal_code', '_country.name', 'email', 'telephone'], function (field) {
                                            var v = helpers.getProperty(address, field);
                                            if (v !== null && v !== undefined) {
                                                addr.push(v);
                                            }
                                        });
                                        return addr.join(', ');
                                    },
                                    carriers,
                                    messageSenderActions = ['log_message', 'leave_feedback', 'review_feedback', 'sudo_feedback'],
                                    getMessageField = function () {
                                        var action;
                                        angular.forEach(messageSenderActions, function (act) {
                                            if ($scope.order.ui.rule.action[act].executable) {
                                                action = act;
                                            }
                                        });
                                        if (!action) {
                                            return false;
                                        }
                                        return orderActionsFields[action].message;
                                    },
                                    getFeedbackField = function () {
                                        var action = false;
                                        if ($scope.order.ui.rule.action.sudo_feedback.executable) {
                                            action = 'sudo_feedback';
                                        }
                                        if ($scope.order.ui.rule.action.leave_feedback.executable) {
                                            action = 'leave_feedback';
                                        }
                                        if (!action) {
                                            return false;
                                        }
                                        return orderActionsFields[action].feedback;
                                    },
                                    messageField, feedbackField;

                                $scope.canShowMessageBox = function () {
                                    var truth = false;
                                    angular.forEach(messageSenderActions, function (act) {
                                        if ($scope.order.ui.rule.action[act].executable) {
                                            truth = true;
                                        }
                                    });
                                    return truth;
                                };
                                $scope.container = {};
                                $scope.selection = {};
                                $scope.cartMode = cartMode;
                                $scope.sellerMode = sellerMode;
                                $scope.order = response.data.entity;
                                $scope.seller = seller;
                                $scope.currentAccount = currentAccount;
                                $scope.newMessage = {
                                    message: null,
                                    key: $scope.order.key
                                };
                                carriers = response.data.carriers || ($scope.order.carrier ? [{
                                    name: $scope.order.carrier.description,
                                    price: $scope.order.carrier.unit_price,
                                    key: $scope.order.carrier.reference
                                }] : []);
                                carriers = $.map(carriers, function (item) {
                                    if (!item) {
                                        return '';
                                    }
                                    if (!angular.isDefined(item.original_name)) {
                                        item.original_name = item.name;
                                    }
                                    item.name = item.original_name + ' (' + $filter('formatCurrency')(item.price, $scope.order.currency) + ')';
                                    return item;
                                });

                                if (cartMode) {
                                    billing_addresses = response.data.billing_addresses;
                                    shipping_addresses = response.data.shipping_addresses;
                                    $scope.selection.billing_address = $scope.order.billing_address.reference;
                                    $scope.selection.shipping_address = $scope.order.shipping_address.reference;
                                } else {
                                    angular.forEach(['country', 'region'], function (field) {
                                        $scope.order.billing_address['_' + field] = {
                                            name: $scope.order.billing_address[field]
                                        };
                                        $scope.order.shipping_address['_' + field] = {
                                            name: $scope.order.billing_address[field]
                                        };
                                    });
                                    billing_addresses = [$scope.order.billing_address, $scope.order.shipping_address];
                                    shipping_addresses = billing_addresses;
                                    $scope.selection.billing_address = $scope.order.billing_address.key;
                                    $scope.selection.shipping_address = $scope.order.shipping_address.key;
                                }
                                $scope.selection.payment_method = $scope.order.payment_method;
                                $scope.selection.carrier = $scope.order.carrier ? $scope.order.carrier.reference : null;
                                $scope.fields = {
                                    billingAddress: {
                                        kind: orderActionsFields.update.billing_address_reference.kind,
                                        type: 'SuperKeyProperty',
                                        code_name: 'selection_billing_address',
                                        required: orderActionsFields.update.billing_address_reference.required,
                                        ui: {
                                            args: 'selection.billing_address',
                                            label: 'Billing Address',
                                            init: function (info) {
                                                info.config.ui.specifics.view = displayAddress;
                                            },
                                            writable: 'order.ui.rule.field.billing_address.reference.writable',
                                            specifics: {
                                                entities: function () {
                                                    return billing_addresses;
                                                }
                                            }
                                        }
                                    },
                                    shippingAddress: {
                                        kind: orderActionsFields.update.shipping_address_reference.kind,
                                        type: 'SuperKeyProperty',
                                        code_name: 'selection_shipping_address',
                                        required: orderActionsFields.update.shipping_address_reference.required,
                                        ui: {
                                            args: 'selection.shipping_address',
                                            label: 'Shipping Address',
                                            writable: 'order.ui.rule.field.shipping_address.reference.writable',
                                            init: function (info) {
                                                info.config.ui.specifics.view = displayAddress;
                                            },
                                            specifics: {
                                                entities: function () {
                                                    return shipping_addresses;
                                                }
                                            }
                                        }
                                    },
                                    carrier: {
                                        kind: orderActionsFields.update.carrier.kind,
                                        type: 'SuperKeyProperty',
                                        code_name: 'selection_carrier',
                                        required: orderActionsFields.update.carrier.required,
                                        ui: {
                                            args: 'selection.carrier',
                                            label: 'Delivery Method',
                                            writable: 'order.ui.rule.field.carrier.writable',
                                            specifics: {
                                                entities: function () {
                                                    return carriers;
                                                }
                                            }
                                        }
                                    }
                                };

                                prepareMessageFields = function () {
                                    messageField = getMessageField();
                                    feedbackField = getFeedbackField();

                                    // this must refresh based on state change
                                    if (messageField) {
                                        $.extend(messageField.ui, {
                                            args: 'newMessage.message',
                                            parentArgs: 'newMessage',
                                            writable: true
                                        });
                                        messageField.required = false;
                                    }
                                    if (feedbackField) {
                                        $.extend(feedbackField.ui, {
                                            args: 'newMessage.feedback',
                                            parentArgs: 'newMessage',
                                            writable: true
                                        });
                                        feedbackField.required = false;
                                    }
                                    $scope.fields.feedback = feedbackField;
                                    $scope.fields.message = messageField;
                                };

                                reactOnStateChange = function (response) {
                                    helpers.update($scope.order, response.data.entity, ['state', 'ui']);
                                    reactOnUpdate();
                                    prepareMessageFields();
                                };
                                reactOnUpdate = function () {
                                    if (order) {
                                        $.extend(order, $scope.order);
                                    }
                                    if (that.getCache('current' + seller.key)) {
                                        that.current(seller.key).then(function (response) {
                                            $.extend(response.data.entity, $scope.order);
                                        });
                                    }
                                };
                                updateLiveEntity = function (response) {
                                    var messages = $scope.order._messages;
                                    $.extend($scope.order, response.data.entity);
                                    $scope.order._messages = messages;
                                };
                                $scope.update = function () {
                                    models['34'].actions.update({
                                        key: $scope.order.key,
                                        payment_method: $scope.selection.payment_method,
                                        carrier: $scope.selection.carrier,
                                        billing_address_reference: ((cartMode && !sellerMode) ? $scope.selection.billing_address : $scope.order.billing_address.reference),
                                        shipping_address_reference: ((cartMode && !sellerMode) ? $scope.selection.shipping_address : $scope.order.shipping_address.reference),
                                        _lines: $scope.order._lines
                                    }).then(function (response) {
                                        updateLiveEntity(response);
                                        reactOnUpdate();
                                    });
                                };

                                $scope.checkout = function () {
                                    if ($scope.order.state !== 'checkout') {
                                        modals.confirm('toCheckout', function () {
                                            models['34'].actions.checkout({
                                                key: $scope.order.key
                                            }).then(function (response) {
                                                reactOnStateChange(response);
                                            });
                                        });
                                    }
                                };

                                $scope.formSetPaypalFormPristine = function () {
                                    if ($scope.container && $scope.container.paypalForm) {
                                        $scope.container.paypalForm.$setPristine();
                                    }
                                };
                                $scope.formSetPaypalFormDirty = function () {
                                    if ($scope.container && $scope.container.paypalForm) {
                                        $scope.container.paypalForm.$setDirty();
                                    }
                                };


                                $scope.removeLine = function (line) {
                                    line.product.quantity = 0;
                                    $scope.formSetPaypalFormDirty();
                                };

                                $scope.messaging = {
                                    send: function (action) {
                                        models['34'].actions[action]($scope.newMessage).then(function (response) {
                                            $scope.newMessage.message = '';
                                            $scope.order._messages.push(response.data.entity._messages[0]);
                                            reactOnStateChange(response);
                                        });
                                    },
                                    logMessage: function () {
                                        return this.send('log_message');
                                    },
                                    reviewFeedback: function () {
                                        return this.send('review_feedback');
                                    },
                                    sudoFeedback: function () {
                                        return this.send('sudo_feedback');
                                    },
                                    leaveFeedback: function () {
                                        return this.send('leave_feedback');
                                    },
                                    reportFeedback: function () {
                                        return this.send('report_feedback');
                                    }
                                };

                                $scope.canShowMessageBox = function () {
                                    var truth = false;
                                    angular.forEach(messageSenderActions, function (act) {
                                        if ($scope.order.ui.rule.action[act].executable) {
                                            truth = act;
                                        }
                                    });
                                    return truth;
                                };

                                $scope.cancel = function () {
                                    if ($scope.order.state === 'checkout') {
                                        modals.confirm('cancelOrder', function () {
                                            models['34'].actions.cancel({
                                                key: $scope.order.key
                                            }).then(function (response) {
                                                models['34'].removeCache('current' + seller.key);
                                                $scope.close();
                                            });
                                        });
                                    }
                                };

                                $scope.close = function () {
                                    $scope.$close();
                                };

                                $scope.viewProduct = function (line) {
                                    var path = line.product._reference;
                                    models['31'].viewProductModal(path.parent.parent.parent.key,
                                        path.parent.parent.key, path.pricetag.key,
                                        line.product.variant_signature, {
                                            events: {
                                                addToCart: updateLiveEntity
                                            }
                                        });
                                };

                                $scope.notifyUrl = helpers.url.abs('api/order/complete/paypal');
                                $scope.completePath = helpers.url.abs('payment/completed/' + $scope.order.key);
                                $scope.cancelPath = helpers.url.abs('payment/canceled/' + $scope.order.key);
                                $scope.messagesReader = models['34'].reader({
                                    kind: '34',
                                    key: $scope.order.key,
                                    next: $scope.order._next_read_arguments,
                                    access: ['_messages'],
                                    complete: function (items) {
                                        $scope.order._messages.extend(items);
                                    }
                                });

                                prepareMessageFields();

                            }
                        });


                    });

                }
            });

        });


    });
}());
