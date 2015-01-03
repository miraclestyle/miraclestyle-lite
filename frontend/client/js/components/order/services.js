(function () {
    'use strict';
    angular.module('app').run(function (modelsMeta, modelsConfig, $modal, modals, helpers, $q, $filter) {

        modelsConfig(function (models) {
            $.extend(models['34'], {
                viewOrderModal: function (seller, buyer, order, config) {
                    config = helpers.alwaysObject(config);
                    var args, cart = config.cart;

                    if (!cart) {
                        args = {
                            key: order.key,
                            read_arguments: {
                                _lines: {config: {
                                    options: {
                                        limit: 0
                                    }
                                }},
                                _messages: {}
                            }
                        };
                    } else {
                        args  = {
                            buyer: buyer.key,
                            seller: seller.key,
                            read_arguments: {
                                _messages: {}
                            }
                        };
                    }

                    models['34'].actions[cart ? 'view_order' : 'read'](args).then(function (response) {

                        if (!response.data.entity.id) {
                            modals.alert('No cart available, please add some products to your cart before you can view it');
                            return;
                        }

                        $modal.open({
                            templateUrl: 'order/modal/view.html',
                            controller: function ($scope, $modalInstance) {
                                var billing_addresses, shipping_addresses, reactOnStateChange, reactOnUpdate,
                                    updateFields = modelsMeta.getActionArguments('34', 'update'),
                                    logMessageFields = modelsMeta.getActionArguments('34', 'log_message'),
                                    displayAddress = function (address) {
                                        var addr = [];
                                        angular.forEach(['_country.name', '_region.name', 'city', 'postal_code', 'name', 'email', 'telephone'], function (field) {
                                            var v = helpers.getProperty(address, field);
                                            if (v !== null && v !== undefined) {
                                                addr.push(v);
                                            }
                                        });
                                        return addr.join(', ');
                                    },
                                    carriers;
                                $.extend(logMessageFields.message.ui, {
                                    args: 'newMessage.message',
                                    parentArgs: 'newMessage',
                                    writable: true
                                });
                                logMessageFields.message.required = false;
                                $scope.selection = {};
                                $scope.cartMode = !order;
                                $scope.order = response.data.entity;
                                $scope.seller = seller;
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

                                if (cart) {
                                    billing_addresses = response.data.billing_addresses;
                                    shipping_addresses = response.data.shipping_addresses;
                                    $scope.selection.billing_address = $scope.order.billing_address_reference;
                                    $scope.selection.shipping_address = $scope.order.shipping_address_reference;
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
                                        kind: updateFields.billing_address_reference.kind,
                                        type: 'SuperKeyProperty',
                                        code_name: 'selection_billing_address',
                                        required: updateFields.billing_address_reference.required,
                                        ui: {
                                            args: 'selection.billing_address',
                                            label: 'Billing Address',
                                            writable: 'order.ui.rule.field.billing_address_reference.writable',
                                            specifics: {
                                                entities: billing_addresses,
                                                view: displayAddress
                                            }
                                        }
                                    },
                                    shippingAddress: {
                                        kind: updateFields.shipping_address_reference.kind,
                                        type: 'SuperKeyProperty',
                                        code_name: 'selection_shipping_address',
                                        required: updateFields.shipping_address_reference.required,
                                        ui: {
                                            args: 'selection.shipping_address',
                                            label: 'Shipping Address',
                                            writable: 'order.ui.rule.field.shipping_address_reference.writable',
                                            specifics: {
                                                entities: shipping_addresses,
                                                view: displayAddress
                                            }
                                        }
                                    },
                                    carrier: {
                                        kind: updateFields.carrier.kind,
                                        type: 'SuperKeyProperty',
                                        code_name: 'selection_carrier',
                                        required: updateFields.carrier.required,
                                        ui: {
                                            args: 'selection.carrier',
                                            label: 'Delivery Method',
                                            writable: 'order.ui.rule.field.carrier.writable',
                                            specifics: {
                                                entities: carriers
                                            }
                                        }
                                    },
                                    message: logMessageFields.message
                                };

                                $scope.remove = function (line) {
                                    line.quantity = 0;
                                };
                                $scope.update = function () {
                                    models['34'].actions.update({
                                        key: $scope.order.key,
                                        payment_method: $scope.selection.payment_method,
                                        carrier: $scope.selection.carrier,
                                        billing_address_reference: $scope.selection.billing_address,
                                        shipping_address_reference: $scope.selection.shipping_address,
                                        _lines: $scope.order._lines
                                    }).then(function (response) {
                                        var messages = $scope.order._messages;
                                        $.extend($scope.order, response.data.entity);
                                        $scope.order._messages = messages;
                                        reactOnUpdate();
                                    });
                                };

                                reactOnStateChange = function (response) {
                                    helpers.update($scope.order, response.data.entity, ['state', 'ui']);
                                    reactOnUpdate();
                                };

                                reactOnUpdate = function () {
                                    if (order) {
                                        $.extend(order, $scope.order);
                                    }
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

                                $scope.sendMessage = function () {
                                    models['34'].actions.log_message($scope.newMessage).then(function (response) {
                                        $scope.newMessage.message = '';
                                        $scope.order._messages.unshift(response.data.entity._messages[0]);
                                    });
                                };

                                $scope.cancel = function () {
                                    if ($scope.order.state === 'checkout') {
                                        modals.confirm('Are you sure you want to cancel this order?', function () {
                                            models['34'].actions.cancel({
                                                key: $scope.order.key
                                            }).then(function (response) {
                                                reactOnStateChange(response);
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
                                    models['31'].viewProductModal(path.parent.parent.parent.key, path.parent.parent.key, path.parent.key);
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
