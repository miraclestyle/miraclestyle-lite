(function () {
    'use strict';
    angular.module('app').run(function (modelsMeta, modelsConfig, $modal, modals, helpers, $q) {

        var orderKind = '34';

        modelsConfig(function (models) {
            $.extend(models[orderKind], {
                viewCartModal: function (seller, buyer) {

                    models[orderKind].actions.view_order({
                        buyer: buyer.key,
                        seller: seller.key,
                    }).then(function (response) {

                        $modal.open({
                            templateUrl: 'order/modal/cart_view.html',
                            controller: function ($scope, $modalInstance, $timeout) {
                                var addresses = buyer.addresses;
                                $scope.order = response.data.entity;
                                $scope.seller = seller;
                                $scope.buyer = buyer;
                                $scope.fields = {
                                    billingAddress: {
                                        kind: '19',
                                        type: 'SuperKeyProperty',
                                        code_name: 'billingAddress',
                                        required: true,
                                        ui: {
                                            args: 'order.shipping_address_reference',
                                            label: 'Billing Address',
                                            writable: 'order.ui.rule.field.billing_address_reference.writable',
                                            specifics: {
                                                entities: addresses,
                                            }
                                        }
                                    },
                                    shippingAddress: {
                                        kind: '19',
                                        type: 'SuperKeyProperty',
                                        code_name: 'shippingAddress',
                                        required: true,
                                        ui: {
                                            args: 'order.shipping_address_reference',
                                            label: 'Shipping Address',
                                            writable: 'order.ui.rule.field.shipping_address_reference.writable',
                                            specifics: {
                                                entities: addresses
                                            }
                                        }
                                    },
                                    deliveryMethod: {
                                        kind: '19',
                                        type: 'SuperKeyProperty',
                                        code_name: 'deliveryMethod',
                                        required: true,
                                        ui: {
                                            args: 'order.delivery_method',
                                            label: 'Shipping Address',
                                            writable: 'order.ui.rule.field.delivery_method.writable',
                                            specifics: {
                                                entities: []
                                            }
                                        }
                                    }
                                };

                                $scope.remove = function (line) {
                                    line.quantity = 0;
                                };
                                $scope.update = function () {
                                    models[orderKind].actions.update({
                                        key: $scope.order.key,
                                        payment_method: $scope.order.payment_method,
                                        billing_address_reference: $scope.order.billing_address_reference,
                                        shipping_address_reference: $scope.order.shipping_address_reference,
                                        _lines: $scope.order._lines,
                                        read_arguments: {
                                            _lines: {
                                                config: {
                                                    limit: -1
                                                }
                                            },
                                            _payment_method: {},
                                        }
                                    }).then(function (response) {
                                        $.extend($scope.order, response.data.entity);
                                    });
                                };

                                $scope.checkout = function () {
                                    if ($scope.order.state !== 'checkout') {
                                        models[orderKind].actions.checkout({
                                            key: $scope.order.key
                                        }).then(function (response) {
                                            $scope.order.state = response.data.entity.state;
                                        });
                                    }
                                };

                                $scope.close = function () {
                                    $modalInstance.dismiss('close');
                                };

                                $scope.notifyUrl = helpers.url.abs('api/order/complete/' + $scope.order.key);
                                $scope.completePath = helpers.url.abs('payment/completed/' + $scope.order.key);
                                $scope.cancelPath = helpers.url.abs('payment/canceled/' + $scope.order.key);

                            }
                        });


                    });

                }
            });

        });


    });
}());
