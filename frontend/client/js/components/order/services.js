(function () {
    'use strict';
    angular.module('app').run(function (modelsMeta, modelsConfig, $modal, modals, helpers, endpoint, $q, $filter, currentAccount) {
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
                viewModal: function (seller, buyer, order, config) {
                    config = helpers.alwaysObject(config);
                    var args, that = this, cartMode = config.cartMode, sellerMode = config.sellerMode, rpc = {};

                    if (!cartMode) {
                        args = {
                            key: order.key,
                            read_arguments: {
                                _lines: {config: {
                                    options: {
                                        limit: 0
                                    }
                                }},
                                _messages: {
                                    _agent: {}
                                }
                            }
                        };
                    } else {
                        args  = {
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
                            modals.alert('No cart available, please add some products to your cart before you can view it');
                            return;
                        }

                        $modal.open({
                            templateUrl: 'order/modal/view.html',
                            controller: function ($scope, $modalInstance) {
                                var billing_addresses, shipping_addresses, reactOnStateChange, reactOnUpdate, updateLiveEntity,
                                    orderActionsFields = modelsMeta.getActionArguments('34'), prepareMessageFields,
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
                                    item.name = item.original_name + ' (' + $filter('displayCurrency')(item.price, $scope.order.currency) + ')';
                                    return item;
                                });

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
                                            writable: true,
                                            placeholder: 'Select feedback...'
                                        });
                                        feedbackField.required = false;
                                    }
                                };

                                prepareMessageFields();

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
                                            writable: 'order.ui.rule.field.billing_address.reference.writable',
                                            specifics: {
                                                entities: billing_addresses,
                                                view: displayAddress
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
                                            specifics: {
                                                entities: shipping_addresses,
                                                view: displayAddress
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
                                                entities: carriers
                                            }
                                        }
                                    },
                                    feedback: feedbackField,
                                    message: messageField
                                };

                                reactOnStateChange = function (response) {
                                    helpers.update($scope.order, response.data.entity, ['state', 'ui']);
                                    reactOnUpdate();
                                    prepareMessageFields();
                                    $scope.fields.feedback = feedbackField;
                                    $scope.fields.message = messageField;
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
                                        modals.confirm('Are you sure you want to go to checkout? You will be in able to send messages to seller or cancel this order.', function () {
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
                                            $scope.order._messages.unshift(response.data.entity._messages[0]);
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
                                        modals.confirm('Are you sure you want to cancel this order?', function () {
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
                                    $modalInstance.dismiss('close');
                                };

                                $scope.viewProduct = function (line) {
                                    var path = line.product._reference;
                                    models['31'].viewProductModal(path.parent.parent.parent.key,
                                                                  path.parent.parent.key, path.parent.key,
                                                                  line.product.variant_signature, {events: {addToCart: updateLiveEntity}});
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

                            }
                        });


                    });

                }
            });

        });


    });
}());
