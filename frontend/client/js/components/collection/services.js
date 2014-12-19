(function () {
    'use strict';
    angular.module('app').run(function (modelsConfig, endpoint, currentAccount, modelsMeta, modelsEditor) {
        modelsConfig(function (models) {
            var read_arguments = {
                _sellers: {
                    _content: {},
                    _feedback: {}
                }
            }, currentCacheKey = 'currentCollections';

            $.extend(models['18'], {
                current: function (args) {
                    if (!args) {
                        args = {};
                    }
                    args.account = currentAccount.key;
                    return this.actions.read(args, {
                        cache: currentCacheKey,
                        cacheType: 'memory'
                    });
                },
                manageModal: function (account_key) {
                    var fields = modelsMeta.getActionArguments(this.kind, 'update'),
                        config,
                        that = this;
                    config = {
                        kind: this.kind,
                        action: 'update',
                        fields: _.toArray(fields),
                        templateBodyUrl: 'collection/modal/manage_body.html',
                        excludeFields: ['account', 'read_arguments'],
                        afterComplete: function ($scope) {
                            $scope.entity._sellers.iremove(function (seller) {
                                return $.inArray(seller.key, $scope.entity.sellers) === -1;
                            });
                            var any = endpoint.getCache(currentCacheKey);
                            if (any) {
                                that.current().then(function (response) {
                                    $.extend(response.data.entity, $scope.entity);
                                });
                            }
                        },
                        scope: {
                            remove: function (seller) {
                                this.args.sellers.remove(seller.key);
                                this.entity._sellers.remove(seller);
                            },
                            view: function (seller) {
                                var that = this;
                                models['23'].actions.read({
                                    account: seller.parent.key,
                                    // 3 rpcs
                                    read_arguments: {
                                        _content: {},
                                        _feedback: {}
                                    }
                                }).then(function (response) {
                                    models['23'].viewModal(response.data.entity, function (updatedCollection) {
                                        that.entity._sellers.iremove(function (seller) {
                                            return $.inArray(seller.key, updatedCollection.sellers) === -1;
                                        });
                                        var rmkey = function (sellerKey) {
                                            return $.inArray(sellerKey, updatedCollection.sellers) === -1;
                                        };
                                        that.entity.sellers.iremove(rmkey);
                                        that.args.sellers.iremove(rmkey);
                                    });
                                });
                            },
                            accordions: {
                                closeOthers: true,
                                groups: [{
                                    label: 'General',
                                    open: true,
                                    key: 'general'
                                }, {
                                    label: 'Sellers'
                                }]
                            }
                        }
                    };

                    modelsEditor.create(config).read({}, {
                        account: account_key,
                        read_arguments: read_arguments
                    });

                }
            });

        });
    });
}());