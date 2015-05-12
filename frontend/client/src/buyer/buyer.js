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

        }).controller('BuyOrdersCtrl', function ($scope, modals, modelsEditor, modelsMeta, models, modelsUtil, $state) {

            var carts = $state.current.name === 'buy-carts';

            $scope.setPageToolbarTitle('buyer.' + (carts ? 'carts' : 'orders'));

            $scope.search = {
                results: [],
                pagination: {}
            };

            $scope.scrollEnd = {loader: false};

            $scope.view = function (order, event) {
                models['19'].current().then(function (response) {
                    return response.data.entity;
                }).then(function (buyer) {
                    models['34'].manageModal(order, order._seller, buyer, {
                        cartMode: carts,
                        targetEvent: event
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
                            if (errors.buyer) {
                                modals.alert('noBuyer');
                            }
                        } else {
                            $scope.search.results.extend(response.data.entities);
                        }
                    }
                });
                $scope.scrollEnd.loader = $scope.search.pagination;
                $scope.search.pagination.load();
            });
        }).directive('buyerAddressListView', function () {
            return {
                scope: {
                    val: '=buyerAddressListView'
                },
                templateUrl: 'buyer/address_list_view.html',
                controller: function ($scope) {
                    $scope.notEmpty = function (val) {
                        return angular.isString(val) || angular.isNumber(val);
                    };
                }
            };
        }).run(function ($window, modelsEditor, modelsMeta, $q, modelsConfig, currentAccount, endpoint) {

            modelsConfig(function (models) {

                $.extend(models['19'], {
                    current: function (args) {
                        if (!args) {
                            args = {};
                        }
                        args.account = currentAccount.key;
                        return this.actions.read(args, {
                            cache: this.getCacheKey('current'),
                            cacheType: 'memory'
                        });
                    },
                    manageModalFieldsOrder: ['country', 'region', 'city', 'postal_code', 'street', 'name'],
                    manageModal: function (accountKey, afterSave) {
                        var fields = modelsMeta.getActionArguments(this.kind, 'update'),
                            that = this,
                            config;
                        $.extend(fields.addresses.ui, {
                            label: false,
                            specifics: {
                                listView: 'buyer-address-list-view',
                                listConfig: {
                                    perLine: 3
                                },
                                sortFields: that.manageModalFieldsOrder,
                                beforeSave: function ($scope, info) {
                                    var promises = [],
                                        updatedAddress = $scope.args,
                                        promise;
                                    if (updatedAddress.region && (!updatedAddress._region || (updatedAddress.region !== updatedAddress._region.key))) {
                                        promise = models['13'].get(updatedAddress.region);
                                        promise.then(function (response) {
                                            if (response.data.entities.length) {
                                                updatedAddress._region = response.data.entities[0];
                                            }
                                        });
                                        promises.push(promise);
                                    }

                                    if (updatedAddress.country && (!updatedAddress._country || (updatedAddress.country !== updatedAddress._country.key))) {
                                        promise = models['12'].actions.search(undefined, {
                                            cache: true
                                        });
                                        promise.then(function (response) {
                                            if (response.data.entities.length) {
                                                var country = _.findWhere(response.data.entities, {
                                                    key: updatedAddress.country
                                                });
                                                if (angular.isDefined(country)) {
                                                    updatedAddress._country = country;
                                                }

                                            }

                                        });

                                        promises.push(promise);
                                    }
                                    if (promises.length) {
                                        return $q.all(promises);
                                    }

                                    return false;

                                }

                            }
                        });
                        config = {
                            fields: _.toArray(fields),
                            kind: this.kind,
                            action: 'update',
                            afterSave: function () {
                                endpoint.removeCache(that.getCacheKey('current'));
                                if (angular.isDefined(afterSave)) {
                                    afterSave();
                                }
                            },
                            scope: {
                                layouts: {
                                    groups: [{label: false, fields: ['addresses']}]
                                }
                            },
                            toolbar: {
                                titleEdit: 'buyer.viewAddresses'
                            },
                            excludeFields: ['account', 'read_arguments'],
                            argumentLoader: function ($scope) {
                                var args = this.defaultArgumentLoader($scope);
                                args.account = accountKey;
                                return args;
                            }
                        };

                        modelsEditor.create(config).read({}, {
                            account: accountKey
                        });
                    }
                });

            });

        });
}());