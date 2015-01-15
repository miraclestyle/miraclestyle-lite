(function () {
    'use strict';
    angular.module('app')
        .controller('BuyerManagementCtrl', function ($scope, endpoint, currentAccount, models) {

            $scope.settings = function () {
                models['19'].manageModal(currentAccount.key);
            };

            $scope.manageCollection = function () {
                models['18'].manageModal(currentAccount.key);
            };

        }).controller('BuyOrdersCtrl', function ($scope, modals, modelsEditor, modelsMeta, models, modelsUtil, $rootScope, $state) {

            var carts = $state.current.name === 'buy-carts';

            $rootScope.pageTitle = 'Buyer ' + (carts ? 'Carts' : 'Orders');

            $scope.search = {
                results: [],
                pagination: {}
            };

            $scope.scrollEnd = {loader: false};

            $scope.view = function (order) {
                models['19'].current().then(function (response) {
                    return response.data.entity;
                }).then(function (buyer) {
                    models['34'].manageModal(order, order._seller, buyer, {
                        cartMode: carts
                    });
                });
            };

            models['19'].current().then(function (response) {
                var buyerEntity = response.data.entity;
                $scope.search.pagination = models['34'].paginate({
                    kind: '34',
                    args: {
                        search: {
                            ancestor: buyerEntity.key,
                            filters: [{field: 'state', operator: 'IN', value: (carts ? ['cart', 'checkout'] : ['completed', 'canceled'])}],
                            orders: [{field: 'updated', operator: 'desc'}, {field: 'key', operator: 'asc'}]
                        }
                    },
                    config: {
                        ignoreErrors: true
                    },
                    complete: function (response) {
                        var errors = response.data.errors;
                        if (errors) {
                            if (errors['not_found_' + buyerEntity.key]) {
                                modals.alert('You do not have any buyer information yet.');
                            }
                        } else {
                            $scope.search.results.extend(response.data.entities);
                        }
                    }
                });
                $scope.scrollEnd.loader = $scope.search.pagination;
                $scope.search.pagination.load();
            });
        });
}());
