(function () {
    'use strict';
    angular.module('app').run(function (modelsMeta, modelsConfig, $modal, modals, helpers, $q, $filter) {

        var orderKind = '34';

        modelsConfig(function (models) {
            $.extend(models[orderKind], {
                viewCartModal: function (seller, buyer) {

                    models[orderKind].actions.view_order({
                        buyer: buyer.key,
                        seller: seller.key,
                        read_arguments: {
                            _messages: {}
                        }
                    }).then(function (response) {

                        if (!response.data.entity.id) {
                            modals.alert('No cart available, please add some products to your cart before you can view it');
                            return;
                        }

                        $modal.open({
                            templateUrl: 'order/modal/cart_view.html',
                            controller: function ($scope, $modalInstance) {
                                var addresses = buyer.addresses, reactOnStateChange,
                                    updateFields = modelsMeta.getActionArguments('34', 'update'),
                                    logMessageFields = modelsMeta.getActionArguments('34', 'log_message');
                                $.extend(logMessageFields.message.ui, {
                                    args: 'newMessage.message',
                                    parentArgs: 'newMessage',
                                    writable: true
                                });
                                logMessageFields.message.required = false;
                                $scope.order = response.data.entity;
                                $scope.seller = seller;
                                $scope.buyer = buyer;
                                $scope.newMessage = {
                                    message: null,
                                    key: $scope.order.key
                                };
                                $scope.order.selectedCarrier = $scope.order.carrier ? $scope.order.carrier.reference : null;
                                $scope.fields = {
                                    billingAddress: {
                                        kind: updateFields.billing_address_reference.kind,
                                        type: 'SuperKeyProperty',
                                        code_name: 'billing_address_reference',
                                        required: updateFields.billing_address_reference.required,
                                        ui: {
                                            args: 'order.billing_address_reference',
                                            label: 'Billing Address',
                                            writable: 'order.ui.rule.field.billing_address_reference.writable',
                                            specifics: {
                                                entities: addresses,
                                            }
                                        }
                                    },
                                    shippingAddress: {
                                        kind: updateFields.shipping_address_reference.kind,
                                        type: 'SuperKeyProperty',
                                        code_name: 'shipping_address_reference',
                                        required: updateFields.shipping_address_reference.required,
                                        ui: {
                                            args: 'order.shipping_address_reference',
                                            label: 'Shipping Address',
                                            writable: 'order.ui.rule.field.shipping_address_reference.writable',
                                            specifics: {
                                                entities: addresses
                                            }
                                        }
                                    },
                                    carrier: {
                                        kind: updateFields.carrier.kind,
                                        type: 'SuperKeyProperty',
                                        code_name: 'selectedCarrier',
                                        required: updateFields.carrier.required,
                                        ui: {
                                            args: 'order.selectedCarrier',
                                            label: 'Delivery Method',
                                            writable: 'order.ui.rule.field.shipping_address_reference.writable',
                                            specifics: {
                                                entities: (response.data.carriers ? $.map(response.data.carriers, function (item) {
                                                    if (!angular.isDefined(item.original_name)) {
                                                        item.original_name = item.name;
                                                    }
                                                    item.name = item.original_name + ' (' + $filter('displayCurrency')(item.price, $scope.order.currency) + ')';
                                                    return item;
                                                }) : [])
                                            }
                                        }
                                    },
                                    message: logMessageFields.message
                                };

                                $scope.remove = function (line) {
                                    line.quantity = 0;
                                };
                                $scope.update = function () {
                                    models[orderKind].actions.update({
                                        key: $scope.order.key,
                                        payment_method: $scope.order.payment_method,
                                        carrier: $scope.order.selectedCarrier,
                                        billing_address_reference: $scope.order.billing_address_reference,
                                        shipping_address_reference: $scope.order.shipping_address_reference,
                                        _lines: $scope.order._lines
                                    }).then(function (response) {
                                        var messages = $scope.order._messages;
                                        $.extend($scope.order, response.data.entity);
                                        $scope.order._messages = messages;
                                    });
                                };

                                reactOnStateChange = function (response) {
                                    helpers.update($scope.order, response.data.entity, ['state', 'ui']);
                                };

                                $scope.checkout = function () {
                                    if ($scope.order.state !== 'checkout') {
                                        modals.confirm('Are you sure you want to go to checkout? You will be in able to send messages to seller or cancel this order.', function () {
                                            models[orderKind].actions.checkout({
                                                key: $scope.order.key
                                            }).then(function (response) {
                                                reactOnStateChange(response);
                                            });
                                        });
                                    }
                                };

                                $scope.sendMessage = function () {
                                    models[orderKind].actions.log_message($scope.newMessage).then(function (response) {
                                        $scope.newMessage.message = '';
                                        $scope.order._messages.unshift(response.data.entity._messages[0]);
                                    });
                                };

                                $scope.cancel = function () {
                                    if ($scope.order.state === 'checkout') {
                                        modals.confirm('Are you sure you want to cancel this order?', function () {
                                            models[orderKind].actions.cancel({
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

                                $scope.notifyUrl = helpers.url.abs('api/order/complete/paypal');
                                $scope.completePath = helpers.url.abs('payment/completed/' + $scope.order.key);
                                $scope.cancelPath = helpers.url.abs('payment/canceled/' + $scope.order.key);
                                $scope.messagesReader = models[orderKind].reader({
                                    kind: orderKind,
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
