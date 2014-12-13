(function () {
    'use strict';
    angular.module('app').run(function (modelsConfig, endpoint, $window, modelsEditor, modelsMeta, modelsUtil) {

        modelsConfig(function (models) {

            $.extend(models['11'], {
                manageModal: function (account) {
                    var config = {
                            kind: this.kind,
                            templateBodyUrl: 'account/modal/settings.html',
                            argumentLoader: function ($scope) {
                                var disassociate = [],
                                    entity = $scope.entity,
                                    identity = _.findWhere(entity.identities, {primary: true}),
                                    obj;
                                angular.forEach(entity.identities,
                                    function (value) {
                                        if (!value.associated) {
                                            disassociate.push(value.identity);
                                        }
                                    });
                                obj = {
                                    action_id: $scope.config.action,
                                    action_model: $scope.config.kind,
                                    primary_identity: identity.identity,
                                    disassociate: disassociate,
                                    key: entity.key
                                };

                                return obj;
                            },
                            scope: {
                                isAssociated: function (ident) {
                                    return $.inArray(ident.identity, this.args.disassociate) === -1;
                                },
                                setPrimary: function (ident) {
                                    this.args.primary_identity = ident.identity;
                                },
                                disassociate: function (ident) {
                                    if (this.isAssociated(ident)) {
                                        this.args.disassociate.push(ident.identity);
                                    } else {
                                        this.args.disassociate.remove(ident.identity);
                                    }
                                },
                                accordions: {
                                    closeOthers: true,
                                    groups: [{
                                        label: 'General',
                                        disabled: false,
                                        open: true
                                    }, {
                                        label: 'Login Methods',
                                        disabled: false,
                                        open: false
                                    }]
                                }
                            }
                        };

                    modelsEditor.create(config).read({
                        key: account.key
                    });

                },
                logout: function (account_key) {
                    this.actions.logout({
                        key: account_key
                    }).then(function (response) {
                        endpoint.invalidateCache('currentAccount');
                        $window.location.reload();
                    });
                }
            });

        });

    });
}());
