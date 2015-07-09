(function () {
    'use strict';
    // code for account
    angular.module('app').constant('LOGIN_PROVIDERS',
        [{
            name: 'Google',
            id: 1
        }, {
            name: 'Facebook',
            id: 2
        }, {
            name: 'Twitter',
            id: 3
        }, {
            name: 'Pinterest',
            id: 4
        }])
        .factory('mappedLoginProviders', ng(function (LOGIN_PROVIDERS) {
            var mappedLoginProviders = {};
            angular.forEach(LOGIN_PROVIDERS, function (value) {
                mappedLoginProviders[value.id] = value;
            });
            return mappedLoginProviders;
        }))
        .controller('AccountLoginStatusController', ng(function ($scope, $location, $state, modals) {
            var data = $location.search(),
                errors;
            if (data.success) {
                $state.go('home');
            } else {
                if (data.errors) {
                    errors = angular.fromJson(data.errors);
                    if (errors && errors.action_denied) {
                        modals.alert('forbidden', function () {
                            $state.go('home');
                        });
                    }
                }
            }
        })).controller('LoginLinksController', ng(function ($scope, endpoint, currentAccount, models) {

            $scope.authorization_urls = {};
            if (currentAccount._is_guest === undefined || currentAccount._is_guest) {
                models['11'].actions.login({
                    login_method: '1'
                }).then(function (response) {
                    $scope.authorization_urls = response.data.authorization_urls;
                });
            }

            $scope.login = function (type) {
                endpoint.removeCache('currentAccount');
                window.location.href = $scope.authorization_urls[type];
            };

        })).controller('AccountManagementController', ng(function ($scope, currentAccount, models, modelsUtil) {

            $scope.settings = function () {
                models['11'].manageModal(currentAccount);
            };
            $scope.logout = function () {
                models['11'].logout(currentAccount.key);
            };
        })).filter('formatLoginProivider', ng(function (mappedLoginProviders) {
            return function (value) {
                var splits = value.split('-'),
                    out = '';
                if (splits && splits[1]) {
                    out = mappedLoginProviders[splits[1]].name;
                }
                return out;
            };
        })).run(ng(function (modelsConfig, channelApi, channelNotifications, endpoint, $window, modelsEditor, GLOBAL_CONFIG, modelsMeta, modelsUtil, $modal, helpers, modals, $q, mappedLoginProviders, LOGIN_PROVIDERS, snackbar) {

            var getProvider = function (ident) {
                return ident.identity.split('-')[1];
            };
            modelsConfig(function (models) {

                $.extend(models['11'], {
                    channel: function () {
                        var promise = this.actions.create_channel(undefined, {
                            cache: 'accountChannel',
                            cacheType: 'memory'
                        });
                        return promise.then(function (response) {
                            var token = response.data.token;
                            return {
                                token: token,
                                channel: channelApi.create(token)
                            };
                        });
                    },
                    channelNotifications: function (config) {
                        var promise = this.channel();
                        return promise.then(function (response) {
                            var token = response.token;
                            return {
                                token: token,
                                channel: channelNotifications.create(token)
                            };
                        });
                    },
                    adminManageModal: function (account, extraConfig) {
                        return this.manageModal(account, extraConfig);
                    },
                    manageModal: function (account, extraConfig) {
                        extraConfig = helpers.alwaysObject(extraConfig);
                        var config = {
                                kind: this.kind,
                                templateBodyUrl: 'account/manage_body.html',
                                toolbar: {
                                    titleEdit: 'account.settings',
                                    hideSave: true
                                },
                                modalConfig: {
                                    popFrom: extraConfig.popFrom,
                                    inDirection: false,
                                    outDirection: false
                                },
                                init: function ($scope) {
                                    var entity = $scope.entity,
                                        updateFields = ['state', 'ui.rule', 'created', 'updated'],
                                        updateState = function (newArgs) {
                                            angular.forEach(['args', 'entity'], function (p) {
                                                helpers.update($scope[p], newArgs, updateFields);
                                            });
                                        },
                                        recompute = function () {
                                            var missing = Object.keys(mappedLoginProviders);
                                            $scope.identities = $scope.entity.identities.concat();
                                            angular.forEach($scope.identities, function (value) {
                                                var id = getProvider(value);
                                                if (missing[id]) {
                                                    delete missing[id];
                                                }
                                            });
                                            angular.forEach(LOGIN_PROVIDERS, function (value) {
                                                if (missing[value.id]) {
                                                    $scope.identities.push({
                                                        identity: '0-' + value.id,
                                                        associated: false
                                                    });
                                                }
                                            });
                                        };
                                    recompute();

                                    if (entity.ui.rule.action.sudo.executable) {
                                        config.toolbar.templateActionsUrl = 'account/manage_actions.html';
                                    }

                                    $scope.args.disassociate = [];
                                    $scope.maybeDisconnect = function (identity) {
                                        if (identity.email && identity.associated === undefined) {
                                            modals.confirm('disconnectSignInMethod', function () {
                                                $scope.args.disassociate.push(identity.identity);
                                                $scope.save().then(function () {
                                                    recompute();
                                                    snackbar.showK('identityDisconnected');
                                                });
                                            });
                                        } else {
                                            modals.confirm('connectSignInMethod', function () {
                                                models['11'].actions.login({
                                                    login_method: getProvider(identity)
                                                }).then(function (response) {
                                                    window.location.href = response.data.authorization_url;
                                                });
                                            });
                                        }
                                    };

                                    $scope.actions.sudo = function () {
                                        modals.models.sudo(entity, {templateUrl: 'account/administer.html', onConfirm: updateState});
                                    };
                                },
                                scope: {
                                    historyConfig: true,
                                    isAssociated: function (ident) {
                                        return $.inArray(ident.identity, this.args.disassociate) === -1;
                                    },
                                    setPrimary: function (ident) {
                                        this.container.form.$setDirty();
                                        this.args.primary_identity = ident.identity;
                                    },
                                    disassociate: function (ident) {
                                        this.container.form.$setDirty();
                                        if (this.isAssociated(ident)) {
                                            this.args.disassociate.push(ident.identity);
                                        } else {
                                            this.args.disassociate.remove(ident.identity);
                                        }
                                    },
                                    actions: {},
                                    layouts: {
                                        groups: [{
                                            label: false
                                        }, {
                                            label: GLOBAL_CONFIG.subheaders.loginMethods
                                        }]
                                    }
                                }
                            };

                        modelsEditor.create(config).read(account, {
                            key: account.key
                        });

                    },
                    logout: function (accountKey) {
                        var that = this;
                        modals.confirm('maybeLogout', function () {
                            that.actions.logout({
                                key: accountKey
                            }).then(function (response) {
                                endpoint.removeCache();
                                $window.location.reload(false);
                            });
                        });

                    }
                });

            });

        }));

}());
