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
        }).run(function ($window, modelsEditor, modelsMeta, $q, modelsConfig, currentAccount, endpoint, toolbarTitle) {

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
                    manageModal: function (accountKey) {
                        var fields = modelsMeta.getActionArguments(this.kind, 'update'),
                            addressFields = fields.addresses.modelclass,
                            that = this,
                            config;
                        $.extend(fields.addresses.ui, {
                            label: false,
                            specifics: {
                                listView: 'buyer-address-list-view',
                                listConfig: {
                                    perLine: 3
                                },
                                sortFields: ['country', 'region', 'city', 'postal_code',
                                    'street', 'name', 'email', 'telephone'],
                                afterSave: function () {
                                    endpoint.removeCache(that.getCacheKey('current'));
                                },
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
                        /*
                        addressFields.country.ui.placeholder = 'Select address country (e.g., USA). This value is Required!';
                        addressFields.region.ui.placeholder = 'Select address region (e.g., California). This value is Optional!';
                        addressFields.city.ui.placeholder = 'Type in address city name (e.g., Beverly Hills). This value is Required!';
                        addressFields.postal_code.ui.placeholder = 'Type in address postal code (e.g., 90210). This value is Required!';
                        addressFields.street.ui.placeholder = 'Type in address street (e.g., Rodeo Drive). This value is Required!';
                        addressFields.name.ui.placeholder = 'Type in contact name (e.g., John Doe). This value is Required!'; // example
                        addressFields.email.ui.placeholder = 'Type in contact email (e.g., johndoe@example.com). This value is Optional.';
                        addressFields.telephone.ui.placeholder = 'Type in contact telephone number. Prefix phone with plus (+) sign, and all calling codes, starting with country code (e.g., ). This value is Optional.';
                        */
                        config = {
                            fields: [fields.addresses],
                            kind: this.kind,
                            action: 'update',
                            toolbar: {
                                title: toolbarTitle.get('buyer.addresses')
                            },
                            scope: {
                                layouts: {
                                    groups: [{label: false, fields: ['addresses']}]
                                }
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