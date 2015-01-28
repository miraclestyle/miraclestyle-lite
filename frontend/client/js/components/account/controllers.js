(function () {
    'use strict';
    // code for account
    angular.module('app').constant('LOGIN_PROVIDERS', {
        '1': 'Google',
        '2': 'Facebook'
    }).controller('AccountLoginStatusCtrl', function ($scope, $location, $state, modals) {
        var data = $location.search(), errors;
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
    });

}());