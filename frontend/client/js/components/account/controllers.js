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
            endpoint.invalidateCache('currentAccount');
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