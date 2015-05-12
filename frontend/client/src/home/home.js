(function () {
    'use strict';
    angular.module('app')
        .controller('MainMenuCtrl', function ($scope, $mdSidenav, $timeout) {
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
        .run(function ($rootScope, GLOBAL_CONFIG, currentAccount, helpers) {
            $rootScope.currentAccount = currentAccount;
            $rootScope.GLOBAL_CONFIG = GLOBAL_CONFIG;
            $rootScope.JSON = JSON;
            $rootScope.helpers = helpers;
            $rootScope.pageToolbarTitle = '';
            $rootScope.setPageTitle = function (title, notToolbarTitle) {
                $rootScope.pageTitle = helpers.toolbar.title(title);
                if (!notToolbarTitle) {
                    $rootScope.pageToolbarTitle = $rootScope.pageTitle;
                }
            };
            $rootScope.setPageToolbarTitle = function (title, notPageTitle) {
                $rootScope.pageToolbarTitle = helpers.toolbar.title(title);
                if (!notPageTitle) {
                    $rootScope.pageTitle = $rootScope.pageToolbarTitle;
                }
            };
        })
        .controller('HomePageCtrl', function ($scope, models, modals, $state, $stateParams, $q, modelsMeta) {
            var args = {search: {}},
                defer = $q.defer(),
                promise = defer.promise;

            $scope.setPageToolbarTitle('home');
            $scope.sellerDetail = false;
            $scope.view = function (key, config) {
                models['31'].viewModal(key, config);
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
            if ($state.current.name === 'following') {
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