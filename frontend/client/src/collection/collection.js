(function () {
    'use strict';
    angular.module('app').run(ng(function (modelsConfig, endpoint, $state, currentAccount, modelsMeta, GLOBAL_CONFIG, modelsEditor, helpers, $timeout, snackbar) {
        modelsConfig(function (models) {
            var read_arguments = {
                _sellers: {
                    _content: {},
                    _feedback: {}
                }
            };

            $.extend(models['18'], {
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
                        config,
                        that = this;
                    config = {
                        kind: this.kind,
                        action: 'update',
                        fields: _.toArray(fields),
                        toolbar: {
                            hideSave: true,
                            titleEdit: 'buyer.edit18'
                        },
                        templateBodyUrl: 'collection/manage_body.html',
                        excludeFields: ['account', 'read_arguments'],
                        init: function ($scope) {
                            var timeouts = [];
                            $scope.close = $scope.$close;
                            $scope.$watch('args.notify', function (neww, old) {
                                var notthis,
                                    cancelTimeouts = function (notthis) {
                                        if (timeouts.length) {
                                            angular.forEach(timeouts, function (timeout) {
                                                if (timeout !== notthis) {
                                                    $timeout.cancel(timeout);
                                                }
                                            });
                                            timeouts = [];
                                        }
                                    };
                                if (neww !== old) {
                                    cancelTimeouts();
                                    notthis = $timeout(function () {
                                        $scope.save().then(function () {
                                            snackbar.showK('changesSaved');
                                        });
                                        cancelTimeouts(notthis);
                                    }, 1000);
                                    timeouts.push(notthis);
                                }
                            });
                        },
                        afterComplete: function ($scope) {
                            $scope.entity._sellers.iremove(function (seller) {
                                return $.inArray(seller.key, $scope.entity.sellers) === -1;
                            });
                            if (that.getCache('current')) {
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
                            view: function (seller, $event) {
                                this.close().then(function () {
                                    $state.go('seller-info', {key: seller.parent.key});
                                });
                            },
                            layouts: {
                                groups: [{
                                    label: false
                                }, {
                                    label: GLOBAL_CONFIG.subheaders.collectionSeller
                                }]
                            }
                        }
                    };

                    modelsEditor.create(config).read({}, {
                        account: accountKey,
                        read_arguments: read_arguments
                    });

                }
            });

        });
    }));
}());