(function () {
    'use strict';
    // code for account
    angular.module('app').constant('LOGIN_PROVIDERS', {
        '1': 'Google',
        '2': 'Facebook'
    }).controller('AccountLoginStatusCtrl', function ($scope, $location, $state, modals) {
        var data = $location.search(),
            errors;
        if (data.success) {
            $state.go('home');
        } else {
            if (data.errors) {
                errors = JSON.parse(data.errors);
                if (errors) {
                    if (errors.action_denied) {
                        modals.alert('Action you tried to perform is forbidden for this account.', function () {
                            $state.go('home');
                        });
                    }
                }
            }
        }
    }).controller('LoginLinksCtrl', function ($scope, endpoint, currentAccount, models) {

        $scope.authorization_urls = {};
        if (currentAccount._is_guest === undefined || currentAccount._is_guest) {
            models['11'].actions.login({
                login_method: 'google'
            }).then(function (response) {
                $scope.authorization_urls = response.data.authorization_urls;
            });
        }

        $scope.login = function (type) {
            endpoint.removeCache('currentAccount');
            window.location.href = $scope.authorization_urls[type];
        };

    }).controller('AccountManagementCtrl', function ($scope, currentAccount, models, modelsUtil) {

        $scope.settings = function () {
            models['11'].manageModal(currentAccount);
        };
        $scope.logout = function () {
            models['11'].logout(currentAccount.key);
        };
    }).filter('formatLoginProivider', function (LOGIN_PROVIDERS) {
        return function (value) {
            var splits = value.split('-'),
                out = '';
            if (splits && splits[1]) {
                out = LOGIN_PROVIDERS[splits[1]];
            }
            return out;
        };
    }).run(function (modelsConfig, channelApi, channelNotifications, endpoint, $window, modelsEditor, modelsMeta, modelsUtil, $modal, helpers, modals, $q) {

        modelsConfig(function (models) {

            $.extend(models['11'], {
                channel: function () {
                    var promise = this.actions.create_channel(undefined, {cache: 'accountChannel', cacheType: 'memory'});
                    return promise.then(function (response) {
                        var token = response.data.token;
                        return {token: token, channel: channelApi.create(token)};
                    });
                },
                channelNotifications: function (config) {
                    var promise = this.channel();
                    return promise.then(function (response) {
                        var token = response.token;
                        return {token: token, channel: channelNotifications.create(token)};
                    });
                },
                adminManageModal: function (account) {
                    return this.manageModal(account);
                },
                manageModal: function (account) {
                    var that = this,
                        config = {
                            kind: this.kind,
                            templateBodyUrl: 'account/manage_body.html',
                            toolbar: {
                                templateActionsUrl: 'account/manage_actions.html'
                            },
                            argumentLoader: function ($scope) {
                                var disassociate = [],
                                    entity = $scope.entity,
                                    identity = _.findWhere(entity.identities, {primary: true}),
                                    obj = $scope.config.defaultArgumentLoader($scope);
                                angular.forEach(entity.identities,
                                    function (value) {
                                        if (!value.associated) {
                                            disassociate.push(value.identity);
                                        }
                                    });
                                $.extend(obj, {
                                    action_id: $scope.config.action,
                                    action_model: $scope.config.kind,
                                    primary_identity: identity.identity,
                                    disassociate: disassociate,
                                    key: entity.key
                                });

                                return obj;
                            },
                            init: function ($scope) {
                                var entity = $scope.entity,
                                    updateFields = ['state', 'ui.rule', 'created', 'updated'],
                                    updateState = function (newArgs) {
                                        angular.forEach(['args', 'entity'], function (p) {
                                            helpers.update($scope[p], newArgs, updateFields);
                                        });
                                    };
                                $scope.actions.sudo = function () {
                                    $modal.open({
                                        templateUrl: 'core/models/manage.html',
                                        controller: function ($scope) {
                                            var sudoFields = modelsMeta.getActionArguments(that.kind, 'sudo');
                                            $scope.dialog = {
                                                templateBodyUrl: 'account/administer.html'
                                            };
                                            //state: entity.state
                                            $scope.args = {key: entity.key};

                                            /*
                                            sudoFields.state.ui.placeholder = 'Set state';
                                            sudoFields.message.ui.placeholder = 'Message for the user';
                                            sudoFields.note.ui.placeholder = 'Note for administrators';
                                            */

                                            $scope.fields = [sudoFields.state, sudoFields.message, sudoFields.note];
                                            angular.forEach($scope.fields, function (field) {
                                                field.ui.writable = true;
                                            });

                                            $scope.formSetPristine = angular.bind($scope, helpers.form.setPristine);
                                            $scope.formSetDirty = angular.bind($scope, helpers.form.setDirty);
                                            $scope.validateForm = angular.bind($scope, helpers.form.validate);
                                            $scope.close = angular.bind($scope, helpers.form.leave, function () {
                                                $scope.$close();
                                            });

                                            $scope.container = {};
                                            $scope.save = function () {
                                                var promise;
                                                if (!$scope.container.form.$valid) {
                                                    return false;
                                                }
                                                promise = models[that.kind].actions.sudo($scope.args);
                                                promise.then(function (response) {
                                                    updateState(response.data.entity);
                                                });
                                                return promise;
                                            };
                                        }
                                    });
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
                                    closeOthers: true,
                                    groups: [{
                                        label: false,
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

                    modelsEditor.create(config).read(account, {
                        key: account.key
                    });

                },
                logout: function (accountKey) {
                    var that = this;
                    modals.confirm('Are you sure you want to logout?', function () {
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

    });

}());
