(function () {
    'use strict';
    angular.module('app').config(function ($stateProvider, GLOBAL_CONFIG) {

        $stateProvider
            .state('home', {
                url: '/',
                templateUrl: 'home/index.html',
                controller: 'HomePageCtrl'
            })
            .state('sell-catalogs', {
                url: '/sell/catalogs',
                controller: 'SellCatalogsCtrl',
                templateUrl: 'catalog/list.html'
            })
            .state('sell-orders', {
                url: '/sell/orders',
                controller: 'SellOrdersCtrl',
                templateUrl: 'misc/common/orders.html'
            })
            .state('sell-carts', {
                url: '/sell/carts',
                controller: 'SellOrdersCtrl',
                templateUrl: 'misc/common/orders.html'
            })
            .state('buy-orders', {
                url: '/buy/orders',
                controller: 'BuyOrdersCtrl',
                templateUrl: 'misc/common/orders.html'
            })
            .state('buy-carts', {
                url: '/buy/carts',
                controller: 'BuyOrdersCtrl',
                templateUrl: 'buyer/carts.html'
            })
            .state('login-status', {
                url: '/login/status',
                template: '',
                controller: 'AccountLoginStatusCtrl'
            })
            .state('admin-list', {
                url: '/admin/list/:kind/:query',
                templateUrl: function ($stateParams) {

                    var defaults = 'admin/list.html',
                        config;

                    if ($stateParams.kind !== undefined) {
                        config = GLOBAL_CONFIG.admin.listTemplates[$stateParams.kind];
                        if (config && config.templateUrl) {
                            defaults = config.templateUrl;
                        }
                    }

                    return defaults;
                },
                controller: 'AdminListCtrl'
            });

    }).run(function (models) {
        models.init();
    });
}());
