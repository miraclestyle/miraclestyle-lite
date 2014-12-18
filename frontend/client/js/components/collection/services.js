(function () {
    'use strict';
    angular.module('app').run(function (modelsConfig, currentAccount, modelsMeta, modelsEditor) {
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
                        cache: 'currentCollections',
                        cacheType: 'memory'
                    });
                },
                manageModal: function (account_key) {
                    var fields = modelsMeta.getActionArguments(this.kind, 'update'), config;
                    config = {
                        kind: this.kind,
                        action: 'update',
                        fields: _.toArray(fields),
                        templateBodyUrl: 'collection/modal/manage_body.html',
                        excludeFields: ['account', 'read_arguments'],
                        scope: {
                            remove: function (seller) {
                                this.args.sellers.remove(seller.key);
                                this.entity._sellers.remove(seller);
                            },
                            view: function (seller) {
                                models['23'].viewModal(seller);
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