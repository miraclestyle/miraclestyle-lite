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
                    }).then(function (response) {

                        if (!response.data.entity.id) {
                            modals.alert('No cart available, please add some products to your cart before you can view it');
                            return;
                        }

                        $modal.open({
                            templateUrl: 'order/modal/cart_view.html',
                            controller: function ($scope, $modalInstance) {
                                var addresses = buyer.addresses, reactOnStateChange;
                                $scope.order = response.data.entity;
                                $scope.seller = seller;
                                $scope.buyer = buyer;
                                $scope.order.selectedCarrier = $scope.order.carrier ? $scope.order.carrier.reference : null;
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
                                    carrier: {
                                        kind: '19',
                                        type: 'SuperKeyProperty',
                                        code_name: 'carrier',
                                        required: true,
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
                                    }
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
                                        $.extend($scope.order, response.data.entity);
                                    });
                                };

                                reactOnStateChange = function (response) {
                                    helpers.update($scope.order, response.data.entity, ['state', 'ui']);
                                };

                                $scope.checkout = function () {
                                    if ($scope.order.state !== 'checkout') {
                                        models[orderKind].actions.checkout({
                                            key: $scope.order.key
                                        }).then(function (response) {
                                            reactOnStateChange(response);
                                        });
                                    }
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
