(function () {
    'use strict';
    // code for account
    angular.module('app').constant('LOGIN_PROVIDERS', [{
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
        .controller('LoginProviderConnectedController', ng(function ($scope, snackbar, currentAccount, models) {
            models['11'].manageModal(currentAccount, {
                fromRedirect: true
            }).then(function () {
                snackbar.showK('identityConnected');
            });
        }))
        .controller('AccountLoginStatusController', ng(function ($scope, $location, $state, snackbar) {
            var data = $location.search(),
                errors;
            if (data.popup) {
                $scope.contentSpinner.start();
                return;
            }
            if (data.success) {
                $state.go('home');
            } else {
                if (data.errors) {
                    errors = angular.fromJson(data.errors);
                    if (errors && errors.action_denied) {
                        snackbar.showK('accessDenied');
                    }
                }
            }
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
        })).run(ng(function (modelsConfig, channelApi, channelNotifications, currentAccount, $http, $state, endpoint, $window, modelsEditor, GLOBAL_CONFIG, modelsMeta, modelsUtil, $modal, helpers, modals, $q, mappedLoginProviders, LOGIN_PROVIDERS, snackbar) {

            var getProvider = function (ident) {
                return ident.identity.split('-')[1];
            };
            modelsConfig(function (models) {

                $.extend(models['11'], {
                    channel: function () {
                        var promise = this.actions.create_channel(undefined, {
                            cache: 'accountChannel',
                            cacheType: 'memory'
                        }, {
                            activitySpinner: true
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
                        config = helpers.alwaysObject(config);
                        var promise = this.channel();
                        return promise.then(function (response) {
                            var token = response.token;
                            return {
                                token: token,
                                channel: channelNotifications.create(token, config.callback)
                            };
                        });
                    },
                    adminManageModal: function (account, extraConfig) {
                        return this.manageModal(account, extraConfig);
                    },
                    login: function (redirect_to) {
                        if (!redirect_to) {
                            redirect_to = '';
                        }
                        $modal.open({
                            templateUrl: 'account/login.html',
                            inDirection: false,
                            windowClass: 'modal-medium-simple',
                            outDirection: false,
                            fullScreen: false,
                            backdrop: true,
                            controller: ng(function ($scope) {
                                $scope.$state.promise(function () {
                                    return $http.post($state.href('login', {
                                        provider: '1'
                                    }, {
                                        disableUI: false
                                    }), {
                                        action_id: 'login',
                                        action_model: '11',
                                        redirect_to: 'popup'
                                    });
                                }, function ($scope, login) {
                                    var MATCH_LOGIN_INSTRUCTION = $state.href('login-status');

                                    $scope.socials = [{
                                        name: 'Facebook',
                                        key: '2'
                                    }, {
                                        name: 'Twitter',
                                        key: '3'
                                    }, {
                                        name: 'Pinterest',
                                        key: '4'
                                    }, {
                                        name: 'Reddit',
                                        key: '5'
                                    }, {
                                        name: 'Linkedin',
                                        key: '6'
                                    }, {
                                        name: 'Google+',
                                        icon: 'googleplus',
                                        key: '1'
                                    }, {
                                        name: 'Tumblr',
                                        key: '7'
                                    }];

                                    $scope.getIcon = function (soc) {
                                        return '/client/dist/static/social/' + (soc.icon || soc.name.toLowerCase()) + '.png';
                                    };

                                    $scope.authorization_urls = login.data.authorization_urls;

                                    $scope.onMessage = [];

                                    $scope.loginPopup = function (soc) {
                                        var popup = helpers.popup.openCentered($scope.authorization_urls[soc.key], 'Login with ' + soc.name),
                                            loggedIn = false,
                                            loading = false,
                                            pollTimer = window.setInterval(function () {
                                                if (popup.closed) {
                                                    clearInterval(pollTimer);
                                                    if (!loggedIn) {
                                                        snackbar.showK('loginCanceled');
                                                    }
                                                    return;
                                                }
                                                var check = function () {
                                                    if (loading) {
                                                        return;
                                                    }
                                                    loading = true;
                                                    models['11'].actions.current_account(undefined, {
                                                        ignoreErrors: 2
                                                    }).then(function (response) {
                                                        var user = response.data.entity;
                                                        if (!user._is_guest) {
                                                            $.extend(currentAccount, response.data.entity);
                                                            endpoint.removeCache();
                                                            snackbar.showK('loginSuccess');
                                                            loggedIn = true;
                                                            popup.close();
                                                            $scope.close();
                                                        }
                                                    }, function () {
                                                        snackbar.showK('loginFailed');
                                                    })['finally'](function () {
                                                        loading = false;
                                                    });
                                                };
                                                try {
                                                    if (popup.document.URL.indexOf(MATCH_LOGIN_INSTRUCTION) !== -1) {
                                                        clearInterval(pollTimer);
                                                        check();
                                                    }
                                                } catch (ignore) {
                                                    if (ignore instanceof DOMException) {
                                                        check();
                                                    }
                                                }
                                            }, 500);
                                    };

                                    $scope.login = function (soc) {
                                        $http.post($state.href('login', {
                                            provider: soc.key
                                        }), {
                                            action_id: 'login',
                                            action_model: '11',
                                            redirect_to: redirect_to
                                        }).then(function (response) {
                                            var data = response.data;
                                            if (data && !data.errors && data.authorization_urls) {
                                                window.top.location.href = data.authorization_url;
                                            } else {
                                                modals.alert('failedGeneratingAuthorizaitonUrl');
                                            }
                                        });
                                    };
                                });
                            })
                        });
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
                                    close,
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
                                            var redirect_to = $state.href('login-provider-connected', {
                                                provider: getProvider(identity)
                                            });
                                            $http.post($state.href('login', {
                                                provider: getProvider(identity)
                                            }), {
                                                action_id: 'login',
                                                action_model: '11',
                                                redirect_to: redirect_to
                                            }).then(function (response) {
                                                var data = response.data;
                                                if (data && !data.errors && data.authorization_url) {
                                                    window.location.href = data.authorization_url;
                                                } else {
                                                    modals.alert('failedGeneratingAuthorizaitonUrl');
                                                }
                                            });
                                        });
                                    }
                                };

                                $scope.actions.sudo = function () {
                                    modals.models.sudo(entity, {
                                        templateUrl: 'account/administer.html',
                                        onConfirm: updateState
                                    });
                                };
                            },
                            afterClose: function () {
                                if (extraConfig.fromRedirect) {
                                    $state.go('home');
                                }
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

                        return modelsEditor.create(config).read(account, {
                            key: account.key
                        });

                    },
                    logout: function (accountKey) {
                        var that = this;
                        that.actions.logout({
                            key: accountKey
                        }).then(function (response) {
                            endpoint.removeCache();
                            $.extend(currentAccount, response.data.entity);
                            $state.go('home');
                            snackbar.showK('loggedOut');
                        });

                    }
                });

            });

        }));

}());
