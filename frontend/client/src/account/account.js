(function () {
    'use strict';
    // code for account
    var resolveAccountLoginError = function (snackbar, errors) {
        var found, oauth2error;
        if (errors.action_denied) {
            found = true;
            snackbar.showK('accessDenied');
        }
        if (errors.oauth2_error) {
            oauth2error = errors.oauth2_error[0];
            if (oauth2error === 'no_email_provided') {
                snackbar.showK('failedGettingEmail');
            } else if (oauth2error === 'failed_access_token') {
                snackbar.showK('incorrectAccessToken');
            } else if (oauth2error === 'rejected_account_access') {
                snackbar.showK('rejectedAccountAccess');
            } else if (oauth2error === 'taken_by_other_account') {
                snackbar.showK('takenByOtherAccount');
            } else if (oauth2error === 'state_error') {
                snackbar.showK('incorrectLinkSettings');
            } else {
                snackbar.showK('failedAuthentication');
            }
            found = true;
        }
        return found;
    };
    angular.module('app').constant('LOGIN_PROVIDERS', [{
            name: 'Facebook',
            key: '2'
        }, {
            name: 'Google',
            icon: 'googleplus',
            key: '1'
        }, {
            name: 'Linkedin',
            key: '3'
        }, {
            name: 'Twitter',
            key: '4'
        }])
        .factory('mappedLoginProviders', ng(function (LOGIN_PROVIDERS) {
            var mappedLoginProviders = {};
            angular.forEach(LOGIN_PROVIDERS, function (value, i) {
                value.sequence = i;
                mappedLoginProviders[value.key] = value;
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
                    if (errors) {
                        resolveAccountLoginError(snackbar, errors);
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
                },
                getLoginProvider = function (ident) {
                    return mappedLoginProviders[getProvider(ident)];
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
                    loginPopup: function (target, title, success, cancel, fail, autodestroy) {
                        var popup = helpers.popup.openCentered(target, title),
                            MATCH_LOGIN_INSTRUCTION = $state.href('login-status'),
                            loggedIn = false,
                            pollTimer,
                            loading = false,
                            handle = function (e) {
                                var url = '',
                                    check,
                                    destroy;
                                destroy = function () {
                                    endpoint.removeCache();
                                    loggedIn = true;
                                    popup.close();
                                };
                                if (autodestroy) {
                                    autodestroy = function () {
                                        destroy();
                                    };
                                } else {
                                    autodestroy = angular.noop;
                                }
                                if (window.ENGINE.CORDOVA.ACTIVE) {
                                    url = e.originalEvent.url;
                                }
                                if (popup.closed) {
                                    clearInterval(pollTimer);
                                    if (!loggedIn) {
                                        cancel();
                                    }
                                    return;
                                }
                                check = function (errors) {
                                    if (loading) {
                                        return;
                                    }
                                    if (errors) {
                                        autodestroy();
                                        return fail(errors, destroy);
                                    }
                                    loading = true;
                                    models['11'].actions.current_account(undefined, {
                                        ignoreErrors: 2
                                    }).then(function (response) {
                                        var user = response.data.entity;
                                        if (user && !user._is_guest) {
                                            $.extend(currentAccount, response.data.entity);
                                            autodestroy();
                                            success(response, destroy);
                                        }
                                    }, function (response) {
                                        autodestroy();
                                        fail(response, destroy);
                                    })['finally'](function () {
                                        loading = false;
                                    });
                                };
                                try {
                                    if (!window.ENGINE.CORDOVA.ACTIVE) {
                                        url = popup.document.URL;
                                    }
                                    if (url.indexOf(MATCH_LOGIN_INSTRUCTION) !== -1) {
                                        clearInterval(pollTimer);
                                        check(helpers.url.getQueryVariable(url, 'errors'));
                                    }
                                } catch (ignore) {
                                    if (ignore instanceof DOMException) {
                                        // check();
                                    }
                                }
                            };
                        if (window.ENGINE.CORDOVA.ACTIVE) {
                            $(popup).on('loadstart', handle);
                        } else {
                            pollTimer = window.setInterval(handle, 500);
                        }
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
                                    return $http.post($state.engineHref('login', {
                                        provider: '1'
                                    }), {
                                        action_id: 'login',
                                        action_model: '11',
                                        redirect_to: 'popup'
                                    });
                                }, function ($scope, login) {

                                    $scope.socials = LOGIN_PROVIDERS;

                                    $scope.getIcon = function (soc) {
                                        return helpers.url.local('client/dist/static/social/' + (soc.icon || soc.name.toLowerCase()) + '.png');
                                    };

                                    $scope.authorization_urls = login.data.authorization_urls;

                                    $scope.loginPopup = function (soc) {
                                        return models['11'].loginPopup($scope.authorization_urls[soc.key],
                                            'Login with ' + soc.name,
                                            function success() {
                                                snackbar.showK('loginSuccess');
                                                $scope.close();
                                            },
                                            function cancel() {
                                                snackbar.showK('loginCanceled');
                                            },
                                            function fail(errors) {
                                                var found = false;
                                                if (errors) {
                                                    found = resolveAccountLoginError(snackbar, angular.fromJson(errors));
                                                }
                                                if (!found) {
                                                    snackbar.showK('loginFailed');
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
                            extractEntity: function (response) {
                                var ent = response[0].data.entity;
                                ent._authorization_urls = response[1].data.authorization_urls;
                                return ent;
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
                                        if (!$scope.entity.identities.length) {
                                            $scope.entity._is_guest = true;
                                        }
                                        angular.forEach($scope.identities, function (value) {
                                            var id = getProvider(value);
                                            if (missing[id]) {
                                                delete missing[id];
                                            }
                                        });
                                        angular.forEach(LOGIN_PROVIDERS, function (value) {
                                            if (missing[value.key]) {
                                                $scope.identities.push({
                                                    identity: '0-' + value.key,
                                                    associated: false
                                                });
                                            }
                                        });

                                        $scope.identities.sort(function (prev, next) {
                                            return getLoginProvider(prev).sequence - getLoginProvider(next).sequence;
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
                                            $scope.save().then(function (response) {
                                                $.extend($scope.entity, response.data.entity);
                                                recompute();
                                                snackbar.showK('identityDisconnected');
                                            });
                                        });
                                    } else {
                                        modals.confirm('connectSignInMethod', function () {
                                            var providerid = getProvider(identity);
                                            models['11'].loginPopup($scope.entity._authorization_urls[providerid],
                                                'Login with ' + LOGIN_PROVIDERS[providerid].name,
                                                function success(successResponse, destroy) {
                                                    $http.post($state.engineHref('login', {
                                                        provider: '1'
                                                    }), {
                                                        action_id: 'login',
                                                        action_model: config.kind,
                                                        redirect_to: 'popup'
                                                    }).then(function (response) {
                                                        $.extend($scope.entity, successResponse.data.entity);
                                                        $scope.entity._authorization_urls = response.data.authorization_urls;
                                                        recompute();
                                                        var shown = false;
                                                        angular.forEach($scope.identities, function (value) {
                                                            if (!shown && value.associated === undefined && getProvider(value) === providerid) {
                                                                shown = true;
                                                                snackbar.showK('identityConnected');
                                                            }
                                                        });
                                                        if (!shown) {
                                                            snackbar.showK('identityTaken');
                                                        }
                                                        destroy();
                                                    });
                                                },
                                                function cancel(destroy) {
                                                    snackbar.showK('identityConnectionCanceled');
                                                },
                                                function fail(errors, destroy) {
                                                    var found = false;
                                                    if (errors) {
                                                        found = resolveAccountLoginError(snackbar, angular.fromJson(errors));
                                                    }
                                                    if (!found) {
                                                        snackbar.showK('identityConnectionFailed');
                                                    }
                                                    destroy();
                                                }, false);
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

                        return modelsEditor.create(config).openPromise(function () {
                            return $q.all([models[config.kind].actions.read({
                                key: account.key
                            }), $http.post($state.engineHref('login', {
                                provider: '1'
                            }), {
                                action_id: 'login',
                                action_model: config.kind,
                                redirect_to: 'popup'
                            })]);
                        }, account);

                    },
                    logout: function (accountKey) {
                        var that = this;
                        that.actions.logout({
                            key: accountKey
                        }, {
                            disableUI: true
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
