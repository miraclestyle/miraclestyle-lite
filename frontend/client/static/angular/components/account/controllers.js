(function () {
    'use strict';
    // code for account
    angular.module('app').constant('LOGIN_PROVIDERS', {
        '1': 'Google',
        '2': 'Facebook'
    }).controller('LoginLinksCtrl', function ($scope, endpoint, currentAccount, models) {

        $scope.authorization_urls = {};

        if (currentAccount._is_guest) {
            models['11'].actions.login({
                login_method: 'google'
            }).then(function (response) {
                $scope.authorization_urls = response.data.authorization_urls;
            });
        }

        $scope.login = function (type) {
            endpoint.invalidate_cache('currentAccount');
            window.location.href = $scope.authorization_urls[type];
        };

    }).controller('AccountManagementCtrl', function ($scope, currentAccount,
        models) {

        $scope.settings = function () {
            models['11'].settingsModal(currentAccount.key);
        };

        $scope.logout = function () {
            models['11'].logout(currentAccount.key);
        };
    });

}());