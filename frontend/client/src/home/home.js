(function () {
    'use strict';
    angular.module('app')
        .controller('RootController', ng(function ($scope, $mdSidenav, $timeout) {}))
        .directive('closeMasterMenu', ng(function ($mdSidenav, $timeout) {
            return {
                priority: 3333,
                link: function (scope, element, attrs) {
                    element.on('click', function () {
                        $timeout(scope.site.toolbar.menu.close, 200, 0);
                    });
                }
            };
        }))
        .directive('homeSplash', ng(function ($animate) {
            return {
                restrict: 'A',
                link: function (scope, element, attrs) {
                    element.addClass('fade out').oneAnimationEnd(function () {
                        element.addClass('ng-hide');
                    });
                }
            };
        }))
        .controller('LoginLinksController', ng(function ($scope, models) {
            $scope.login = function () {
                models['11'].login();
            };
        }))
        .run(ng(function ($rootScope, GLOBAL_CONFIG, currentAccount, helpers) {
            $rootScope.site = {
                title: '',
                toolbar: {
                    hideRight: true,
                    hideLeft: false,
                    title: '',
                    menu: {}
                }
            };
            $rootScope.currentAccount = currentAccount;
            $rootScope.GLOBAL_CONFIG = GLOBAL_CONFIG;
            $rootScope.JSON = JSON;
            $rootScope.helpers = helpers;
            $rootScope.setPageTitle = function (title, notToolbarTitle) {
                $rootScope.site.title = helpers.toolbar.title(title);
                if (!notToolbarTitle) {
                    $rootScope.site.toolbar.title = $rootScope.site.title;
                }
            };
            $rootScope.setPageToolbarTitle = function (title, notPageTitle) {
                $rootScope.site.toolbar.title = helpers.toolbar.title(title);
                if (!notPageTitle) {
                    $rootScope.site.title = $rootScope.site.toolbar.title;
                }
            };

            $rootScope.$on('$stateChangeStart', function () {
                $rootScope.site.toolbar.hideRight = true;
                $rootScope.site.toolbar.actionRight = undefined;
                $rootScope.site.toolbar.hidden = false;
            });

            helpers.sideNav.setup($rootScope.site.toolbar.menu, 'left');
        }))
        .controller('AboutController', ng(function ($scope) {
            $scope.socials = [{
                name: 'Facebook',
                key: 'facebook',
                command: 'https://www.facebook.com/fbpage'
            }, {
                name: 'Twitter',
                key: 'twitter',
                command: 'https://twitter.com/twitteracc'
            }, {
                name: 'Pinterest',
                key: 'pinterest',
                command: 'https://www.pinterest.com/pinterestacc'
            }, {
                name: 'Reddit',
                key: 'reddit',
                command: 'https://www.reddit.com/subreddit'
            }, {
                name: 'Linkedin',
                key: 'linkedin',
                command: 'https://www.linkedin.com/profile'
            }, {
                name: 'Google+',
                icon: 'googleplus',
                command: 'https://plus.google.com/pageid',
            }, {
                name: 'Tumblr',
                key: 'tumblr',
                command: 'https://www.tumblr.com/profile'
            }];

            $scope.share = function (soc) {
                return soc.command;
            };

            $scope.getIcon = function (soc) {
                return '/client/dist/static/social/' + (soc.icon || soc.name.toLowerCase()) + '.png';
            };

            $scope.setPageToolbarTitle('about');

        }))
        .controller('HomePageController', ng(function ($scope, models, modals, $state, $stateParams, helpers, $q, modelsMeta) {
            var args = {
                    search: {}
                },
                defer = $q.defer(),
                promise = defer.promise;

            $scope.setPageToolbarTitle('home');
            $scope.sellerDetails = false;
            $scope.viewProfile = function (key, $event) {
                models['23'].viewProfileModal(key, {
                    popFrom: $event.target
                });
            };
            $scope.view = function (key, $event) {
                models['31'].viewModal(key, {
                    popFrom: helpers.clicks.realEventTarget($event.target)
                });
            };

            if ($stateParams.key) {
                $scope.sellerMode = true;
                $scope.setPageToolbarTitle('sellerProfile');
                args.search.filters = [{
                    field: 'seller_account_key',
                    operator: 'IN',
                    value: $stateParams.key
                }];
                models['23'].actions.read({
                    account: $stateParams.key,
                    read_arguments: {
                        _feedback: {},
                        _content: {}
                    }
                }).then(function (response) {
                    $scope.sellerDetails = models['23'].makeSellerDetails(response.data.entity);
                });

                $scope.site.toolbar.hideRight = false;
                $scope.site.toolbar.actionRight = function () {
                    $scope.sellerDetails.menu.open();
                };
            }
            if ($state.current.name === 'following') {
                promise = models['18'].current();
                promise.then(function (response) {
                    $scope.search.pagination.args.search.filters = [{
                        field: 'ancestor',
                        operator: 'IN',
                        value: response.data.entity.sellers
                    }];
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
            $scope.scrollEnd = {
                loader: false
            };
            $scope.scrollEnd.loader = $scope.search.pagination;
            promise.then(function () {
                $scope.search.pagination.load();
            });


        }));

}());
