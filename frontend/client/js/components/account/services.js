(function () {
    'use strict';
    angular.module('app').run(function (modelsConfig, channelApi, channelNotifications, endpoint, $window, modelsEditor, modelsMeta, modelsUtil, $modal, helpers, modals, $q) {

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
                                        templateUrl: 'core/form/manage_entity.html',
                                        controller: function ($scope) {
                                            var sudoFields = modelsMeta.getActionArguments(that.kind, 'sudo');
                                            $scope.dialog = {
                                                templateBodyUrl: 'account/administer.html'
                                            };
                                            $scope.args = {key: entity.key, state: entity.state};

                                            /*
                                            sudoFields.state.ui.placeholder = 'Set state';
                                            sudoFields.message.ui.placeholder = 'Message for the user';
                                            sudoFields.note.ui.placeholder = 'Note for administrators';
                                            */

                                            $scope.fields = [sudoFields.state, sudoFields.message, sudoFields.note];
                                            angular.forEach($scope.fields, function (field) {
                                                field.ui.writable = true;
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
                                            $scope.close = function () {
                                                $scope.$close();
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
