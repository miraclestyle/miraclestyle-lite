(function () {
    'use strict';
    angular.module('app')
        .controller('RootController', ng(function ($scope, $mdSidenav, $timeout) {}))
        .directive('closeMasterMenu', ng(function ($mdSidenav, $timeout, $parse) {
            return {
                link: function (scope, element, attrs) {
                    var callback = $parse(attrs.closeMasterMenu);
                    element.on('click', function (event) {
                        scope.site.toolbar.menu.close().then(function () {
                            if (callback) {
                                if (scope.$$phase) {
                                    callback(scope, {
                                        $event: event
                                    });
                                } else {
                                    scope.$apply(function () {
                                        callback(scope, {
                                            $event: event
                                        });
                                    });
                                }
                            }
                        });
                    });
                }
            };
        }))
        .directive('toolbarPaddingControl', ng(function ($timeout) {
            return {
                restrict: 'A',
                controller: ng(function ($scope, $element) {
                    var that = this;
                    that.recalculate = function () {
                        var crumb = $element.find('.md-toolbar-item.md-breadcrumb'),
                            size = 0,
                            actions = $element.find('.md-toolbar-item.md-tools.actions-right');
                        if (actions.length) {
                            size = actions.outerWidth();
                        }
                        if (!size) {
                            size = 16;
                        }
                        crumb.css('padding-right', size);
                    };
                }),
                link: function (scope, element, attrs, ctrl) {
                    $timeout(ctrl.recalculate, 0, false);
                }
            };
        }))
        .directive('toolbarPaddingControlElement', ng(function ($timeout) {
            return {
                restrict: 'A',
                require: '^toolbarPaddingControl',
                link: function (scope, element, attrs, ctrl) {
                    $timeout(ctrl.recalculate, 0, false);
                    scope.$on('$destroy', function () {
                        $timeout(ctrl.recalculate, 100, false);
                    });
                }
            };
        }))
        .directive('homeSplash', ng(function ($animateCss) {
            return {
                restrict: 'A',
                link: function (scope, element, attrs) {
                    element.addClass('fade');
                    $animateCss(element, {
                        addClass: 'out'
                    }).start().done(function () {
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
            $rootScope.contentSpinner = {
                hide: [],
                show: [],
                requests: 0,
                last: null,
                stop: function () {
                    this.requests -= 1;
                    if (this.hide) {
                        var length = this.hide.length - 1;
                        angular.forEach(this.hide, function (cb, i) {
                            if (i === length) {
                                cb();
                            } else {
                                cb(true);
                            }
                        });
                    }
                },
                start: function () {
                    this.requests += 1;
                    var max = this.hide.length - 1;
                    angular.forEach(this.hide, function (cb, i) {
                        if (i === max) {
                            return;
                        }
                        cb();
                    });
                    if (this.show) {
                        (_.last(this.show) || angular.noop)();
                    }
                }
            };
            $rootScope.activitySpinner = angular.copy($rootScope.contentSpinner);
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
        .controller('AboutController', ng(function ($scope, helpers) {
            $scope.socials = [{
                    name: 'Facebook',
                    key: 'facebook',
                    command: 'https://www.facebook.com/themiraclestyle/'
                },
                /* {
                                name: 'Twitter',
                                key: 'twitter',
                                command: 'https://twitter.com/themiraclestyle'
                            }, {
                                name: 'Pinterest',
                                key: 'pinterest',
                                command: 'https://www.pinterest.com/themiraclestyle/'
                            }, {
                                name: 'Instagram',
                                key: 'instagram',
                                command: 'https://www.instagram.com/themiraclestyle/'
                            }, {
                                name: 'Linkedin',
                                key: 'linkedin',
                                command: 'https://www.linkedin.com/company/miraclestyle'
                            }, {
                                name: 'YouTube',
                                icon: 'youtube',
                                command: 'https://www.youtube.com/channel/UCy8iFLR6b1NXX8mhCgv2toA',
                            }, {
                                name: 'Google+',
                                icon: 'googleplus',
                                command: 'https://plus.google.com/b/117800240045842886424/',
                            }, {
                                name: 'Tumblr',
                                key: 'tumblr',
                                command: 'http://themiraclestyle.tumblr.com/'
                            }*/
            ];

            $scope.share = function (soc) {
                return soc.command;
            };

            $scope.getIcon = function (soc) {
                return soc.icon || soc.name.toLowerCase();
            };

            $scope.setPageToolbarTitle('about');

        }))
        .factory('guide', ng(function (GLOBAL_CONFIG, $modal, models, errorHandling, $state, helpers) {

            function open(config) {
                config = helpers.alwaysObject(config);
                var key = GLOBAL_CONFIG.guideKey,
                    controller;

                if (!key) {
                    return;
                }

                controller = ng(function ($scope) {
                    $scope.$state.promise(function () {
                        return models['31'].actions.read({
                            key: key,
                            // 5 rpcs
                            read_arguments: {
                                _seller: {},
                                _images: {
                                    config: {
                                        search: {
                                            options: {
                                                limit: 50000
                                            }
                                        }
                                    }
                                }
                            }
                        }, {
                            ignoreErrors: 2
                        });
                    }, function ($scope, response) {
                        var errors,
                            entity;
                        if (response) {
                            errors = response.data.errors;
                            if (errors) {
                                if ((errors.not_found || errors.malformed_key)) {
                                    $scope.close();
                                    $state.go('home');
                                    $scope.notFound = true;
                                } else {
                                    $scope.close();
                                    errorHandling.snackbar(errors);
                                }
                                return;
                            }
                        }
                        entity = response.data.entity;
                        if (!entity._images.length) {
                            $scope.noImages = true;
                            return;
                        }

                        $scope.close = function () {
                            if (!config.homepage) {
                                $state.go('home');
                            } else {
                                $.cookie('sawguide', 1, {expires: 30});
                            }
                            $scope.$close();
                        };
                        $scope.catalog = entity;
                    });
                });

                $modal.open({
                    templateUrl: 'home/guide.html',
                    windowClass: 'no-overflow',
                    controller: controller,
                    inDirection: false,
                    outDirection: false
                });
            }
            return {
                open: open
            };
        }))
        .controller('QuickGuideController', ng(function ($scope, guide, $timeout) {

            $scope.site.toolbar.hidden = true;
            $timeout(function () {
                guide.open();
            }, 300);
        }))
        .controller('HomePageController', ng(function ($scope, currentAccount, guide, $timeout, models, modals, $state, $stateParams, helpers, $q, modelsMeta) {
            var args = {
                    search: {
                        filters: [{
                            field: 'state',
                            operator: 'IN',
                            value: ['indexed']
                        }],
                        orders: [{
                            field: 'published_date',
                            operator: 'desc'
                        }]
                    }
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
                    popFrom: helpers.clicks.realEventTarget($event.target),
                    track: helpers.track.events.catalogHome
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
            defer.resolve();
            $scope.search = {
                results: [],
                loader: models['31'].paginate({
                    kind: '31',
                    args: args,
                    config: {
                        normalizeEntity: false
                    },
                    action: 'search',
                    complete: function (response) {
                        var results = response.data.entities;
                        $scope.search.results.extend(results);
                    }
                })
            };
            promise.then(function () {
                $scope.search.loader.load();
            });

            if (currentAccount._is_guest) {
                $timeout(function () {
                    guide.open({
                        homepage: true
                    });
                }, 300);
            }



        }));

}());
