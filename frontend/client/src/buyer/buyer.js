(function () {
    'use strict';
    angular.module('app')
        .run(ng(function (currentAccount, helpers) {
            if (!helpers.location) {
                helpers.location = {};
            }
            helpers.location.updateDefaults = function (args) {
                if (!angular.isObject(args)) {
                    return;
                }
                if (!args.country && currentAccount._country) {
                    args.country = currentAccount._country;
                }
                if (!args.region && currentAccount._region) {
                    args.region = currentAccount._region;
                }
                if (!args.city && currentAccount._city) {
                    args.city = _.string.capitalize(currentAccount._city);
                }
                return args;
            };
        }))
        .controller('BuyerManagementController', ng(function ($scope, endpoint, currentAccount, models) {

            $scope.settings = function () {
                models['19'].manageModal(currentAccount.key, undefined, {
                    inDirection: false,
                    outDirection: false
                });
            };

        })).controller('BuyOrdersController', ng(function ($scope, $timeout, modals, snackbar, modelsEditor, GLOBAL_CONFIG, modelsMeta, helpers, models, modelsUtil, $state) {

            var carts = ($state.current.name === 'buy-carts' || $state.current.name === 'buyer-cart-view'),
                isBuyerViewCart = $state.current.name === 'buyer-cart-view',
                isBuyerViewOrder = $state.current.name === 'buyer-order-view',
                isOrderPaymentCanceled = $state.current.name === 'order-payment-canceled',
                isOrderPaymentSuccess = $state.current.name === 'order-payment-success',
                wait = null,
                loaded = false,
                tick = null,
                gorder,
                maxTries = 10,
                scheduleTick = function () {
                    if (!$state.params.key) {
                        return;
                    }
                    if (tick) {
                        $timeout.cancel(tick);
                    }
                    tick = $timeout(function () {
                        if (!$state.params.key) {
                            return; // exit tick if request state changes
                        }
                        models['34'].actions.read({
                            key: $state.params.key
                        }, {disableUI: false}).then(function (response) {
                            if (gorder) {
                                helpers.update(gorder, response.data.entity, ['state', 'updated', 'payment_status', 'ui']);
                            }
                            if (response.data.entity.payment_status) {
                                snackbar.showK('orderPaymentSuccessProgress' + response.data.entity.payment_status);
                            } else {
                                scheduleTick();
                            }
                        }, function () {
                            maxTries += 1;
                            if (maxTries < 10) { // if it fails 10 rpcs then obv something wrong, abort
                                scheduleTick();
                            }
                        }); // schedule tick if error, and if entity state did not change from cart.
                    }, 30000);
                },
                viewOpts = {
                    inDirection: false,
                    outDirection: false,
                    afterClose: function () {
                        var state = 'buy-orders';
                        if (isBuyerViewCart) {
                            state = 'buy-carts';
                        }
                        $state.go(state);
                    }
                },
                viewThen = function (order) {
                    gorder = order;
                    if (!isOrderPaymentCanceled) {
                        if (!(isBuyerViewOrder || isBuyerViewCart)) {
                            scheduleTick();
                        }
                    }
                },
                maybeOpenOrder = function () {
                    if (loaded) {
                        return;
                    }
                    if (wait) {
                        clearTimeout(wait);
                    }
                    wait = setTimeout(function () {
                        var find = {
                            key: $state.params.key
                        }, order = _.findWhere($scope.search.results, find);
                        loaded = true;
                        if (order) {
                            return $scope.view(order, false);
                        }
                        models['34'].manageModal(find, undefined, undefined, viewOpts).then(viewThen);
                    }, 300);

                };

            if (isOrderPaymentCanceled || isOrderPaymentSuccess || isBuyerViewOrder) {
                carts = false;
            }


            $scope.setPageToolbarTitle('buyer.' + (carts ? 'carts' : 'orders'));

            $scope.listHelp = (carts ? GLOBAL_CONFIG.emptyHelp.cartBuyerList : GLOBAL_CONFIG.emptyHelp.orderBuyerList);

            $scope.search = {
                results: [],
                loader: false,
                loaded: false
            };

            $scope.$watch(function maybeRemoveSearchResult() {
                var maybe = false;
                $scope.search.results.iremove(function (ent) {
                    var truth = (!ent.id || ent._state === 'deleted') || (ent.state === 'order' && carts);
                    if (!maybe) {
                        maybe = truth;
                    }
                    return truth;
                });
                return maybe;
            }, angular.noop);

            $scope.view = function (order, $event) {
                models['19'].current().then(function (response) {
                    return response.data.entity;
                }).then(function (buyer) {
                    var opts = {
                        cartMode: carts,
                        popFrom: ($event ? helpers.clicks.realEventTarget($event.target) : false)
                    }, viewPromise, directView = $event === false;
                    if (directView) {
                        $.extend(opts, viewOpts);
                    }
                    viewPromise = models['34'].manageModal(order, order._seller, buyer, opts);
                    if (viewPromise && directView) {
                        viewPromise.then(viewThen);
                    }
                });
            };

            models['19'].current().then(function (response) {
                var buyerEntity = response.data.entity;
                $scope.search.loader = models['34'].paginate({
                    kind: '34',
                    args: {
                        search: {
                            ancestor: buyerEntity.key,
                            filters: [{field: 'state', operator: 'IN', value: [(carts ? 'cart' : 'order')]}],
                            orders: [{field: 'updated', operator: 'desc'}]
                        }
                    },
                    config: {
                        ignoreErrors: 2
                    },
                    complete: function (response) {
                        var errors = response.data.errors;
                        if (errors) {
                            if (errors.buyer) {
                                snackbar.showK('noBuyer');
                            }
                        } else {
                            $scope.search.results.extend(response.data.entities);
                        }

                        if (isOrderPaymentCanceled || isOrderPaymentSuccess || isBuyerViewCart || isBuyerViewOrder) {
                            maybeOpenOrder();
                        }
                    }
                });
                $scope.search.loader.load();
            });
        })).directive('buyerAddressListView', function () {
            return {
                scope: {
                    val: '=buyerAddressListView'
                },
                templateUrl: 'buyer/address_list_view.html',
                controller: ng(function ($scope) {
                    $scope.notEmpty = function (val) {
                        return angular.isString(val) || angular.isNumber(val);
                    };
                })
            };
        }).run(ng(function ($window, modelsEditor, helpers, modelsMeta, $q, modelsConfig, currentAccount, endpoint) {

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
                    manageModal: function (accountKey, afterSave, modalConfig) {
                        if (!modalConfig) {
                            modalConfig = {};
                        }
                        var fields = modelsMeta.getActionArguments(this.kind, 'update'),
                            that = this,
                            config;
                        $.extend(fields.addresses.ui, {
                            label: false,
                            specifics: {
                                defaultArgs: helpers.location.updateDefaults({}),
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
                                        promise = models['13'].get(updatedAddress.region, {activitySpinner: true, disableUI: false});
                                        promise.then(function (response) {
                                            if (response.data.entities.length) {
                                                updatedAddress._region = response.data.entities[0];
                                            }
                                        });
                                        promises.push(promise);
                                    }

                                    if (updatedAddress.country && (!updatedAddress._country || (updatedAddress.country !== updatedAddress._country.key))) {
                                        promise = models['12'].actions.search(undefined, {
                                            cache: true,
                                            cacheType: 'local',
                                            activitySpinner: true,
                                            disableUI: false
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
                            modalConfig: modalConfig,
                            afterSave: function ($scope) {
                                endpoint.removeCache(that.getCacheKey('current'));
                                if (angular.isDefined(afterSave)) {
                                    afterSave($scope);
                                }
                            },
                            scope: {
                                layouts: {
                                    groups: [{label: false, fields: ['addresses']}]
                                }
                            },
                            toolbar: {
                                titleEdit: 'buyer.viewAddresses',
                                titleAdd: 'buyer.viewAddresses'
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

        }));
}());