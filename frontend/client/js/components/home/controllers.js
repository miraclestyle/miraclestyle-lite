(function () {
    'use strict';
    angular.module('app')
        .controller('MainMenuCtrl', function ($scope, currentAccount, GLOBAL_CONFIG) {
            $scope.currentAccount = currentAccount;
            $scope.GLOBAL_CONFIG = GLOBAL_CONFIG;
            $scope.JSON = JSON;
        })
        .controller('HomePageCtrl', function ($scope, models, modals) {
            $scope.search = {
                results: [],
                pagination: {}
            };
            $scope.view = function (key) {
                models['31'].viewModal(key);
            };

            $scope.scrollEnd = {loader: false};

            $scope.search.pagination = models['31'].paginate({
                kind: '31',
                args: {},
                config: {
                    normalizeEntity: false
                },
                action: 'public_search',
                complete: function (response) {
                    $scope.search.results.extend(response.data.entities);
                }
            });
            $scope.scrollEnd.loader = $scope.search.pagination;
            $scope.search.pagination.load();

        });

}());