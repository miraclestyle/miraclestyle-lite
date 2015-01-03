(function () {
    'use strict';
    angular.module('app')
        .controller('SellerManagementCtrl', function ($scope, endpoint,
            currentAccount, models) {

            $scope.settings = function () {
                models['23'].manageModal(currentAccount.key);
            };

        }).controller('SellCatalogsCtrl', function ($scope, modals, modelsEditor, modelsMeta, models, modelsUtil, visualAid, $rootScope) {

            $rootScope.pageTitle = 'Sell Catalogs';

            var newEntity = function (entity) {
                if (!_.findWhere($scope.search.results, {
                        key: entity.key
                    })) {
                    $scope.search.results.unshift(entity);
                }
            };

            $scope.create = function () {
                models['31'].manageModal(undefined, newEntity);
            };

            $scope.preview = function (key) {
                models['31'].previewModal(key);
            };

            $scope.manage = function (entity) {
                models['31'].manageModal(entity, newEntity);
            };


            $scope.search = {
                results: [],
                pagination: {}
            };

            $scope.scrollEnd = {loader: false};

            models['23'].current().then(function (response) {
                var sellerEntity = response.data.entity;
                $scope.search.pagination = models['31'].paginate({
                    kind: '31',
                    args: {
                        search: {
                            ancestor: sellerEntity.key
                        }
                    },
                    config: {
                        ignoreErrors: true
                    },
                    complete: function (response) {
                        var errors = response.data.errors;
                        if (errors) {
                            if (errors['not_found_' + sellerEntity.key]) {
                                modals.alert('You do not have any seller information yet.');
                            }
                        } else {
                            $scope.search.results.extend(response.data.entities);
                        }
                    }
                });
                $scope.scrollEnd.loader = $scope.search.pagination;
                $scope.search.pagination.load();
            });

        }).controller('SellOrdersCtrl', function ($scope, modals, modelsEditor, modelsMeta, models, modelsUtil, visualAid, $rootScope, $state) {

            var carts = $state.current.name === 'sell-carts';

            $rootScope.pageTitle = 'Seller ' + (carts ? 'Carts' : 'Orders');

            $scope.search = {
                results: [],
                pagination: {}
            };

            $scope.scrollEnd = {loader: false};

            $scope.view = function (order) {
                models['34'].viewOrderModal(order._seller, undefined, order);
            };

            models['23'].current().then(function (response) {
                var sellerEntity = response.data.entity;
                $scope.search.pagination = models['34'].paginate({
                    kind: '34',
                    args: {
                        search: {
                            filters: [{field: 'seller_reference', operator: '==', value: sellerEntity.key}, {field: 'state', operator: 'IN', value: (carts ? ['cart', 'checkout'] : ['completed', 'canceled'])}],
                            orders: [{field: 'created', operator: 'desc'}, {field: 'key', operator: 'desc'}]
                        }
                    },
                    config: {
                        ignoreErrors: true
                    },
                    complete: function (response) {
                        var errors = response.data.errors;
                        if (errors) {
                            if (errors['not_found_' + sellerEntity.key]) {
                                modals.alert('You do not have any seller information yet.');
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