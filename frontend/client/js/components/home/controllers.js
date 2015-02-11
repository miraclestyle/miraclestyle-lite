(function () {
    'use strict';
    angular.module('app')
        .controller('MainMenuCtrl', function ($scope, currentAccount, GLOBAL_CONFIG, $mdSidenav, $timeout) {
            $scope.currentAccount = currentAccount;
            $scope.GLOBAL_CONFIG = GLOBAL_CONFIG;
            $scope.JSON = JSON;
            $scope.closeMenu = function () {
                $timeout(function () {
                    $mdSidenav('left').close();
                });
            };
            $scope.openMenu = function () {
                $timeout(function () {
                    $mdSidenav('left').open();
                });
            };
        })
        .controller('HomePageCtrl', function ($scope, models, modals, $state, $stateParams, $q, modelsMeta) {
            var args = {search: {}},
                defer = $q.defer(),
                promise = defer.promise;
            $scope.sellerDetail = false;
            $scope.view = function (key) {
                models['31'].viewModal(key);
            };

            if ($stateParams.key) {
                args.search.filters = [{field: 'seller_account_key', operator: 'IN', value: $stateParams.key}];
                $scope.sellerDetail = {};
                models['23'].actions.read({
                    account: $stateParams.key,
                    read_arguments: {
                        _feedback: {},
                        _content: {}
                    }
                }).then(function (response) {
                    $.extend($scope.sellerDetail, response.data.entity);
                });

                $scope.viewSeller = function () {
                    models['23'].viewModal($scope.sellerDetail);
                };
            }
            if ($state.current.name === 'collections') {
                promise = models['18'].current();
                promise.then(function (response) {
                    $scope.search.pagination.args.search.filters = [{field: 'ancestor', operator: 'IN', value: response.data.entity.sellers}];
                });
            } else {
                defer.resolve();
            }
            $scope.search = {
                results: [],
                pagination: models['31'].paginate({
                    kind: '31',
                    args: args,
                    config: {
                        normalizeEntity: false
                    },
                    action: 'public_search',
                    complete: function (response) {
                        var results = response.data.entities;
                        models['31'].formatPublicSearchResults(results);
                        $scope.search.results.extend(results);
                    }
                })
            };
            $scope.scrollEnd = {loader: false};
            $scope.scrollEnd.loader = $scope.search.pagination;
            promise.then(function () {
                $scope.search.pagination.load();
            });


        });

}());