(function () {
    'use strict';
    angular.module('app').config(function ($stateProvider) {

        $stateProvider
            .state('home', {
                url: '/',
                templateUrl: 'home/index.html',
                controller: 'HomePageCtrl'
            })
            .state('login', {
                url: '/login/:provider',
                controller: 'LoginPageCtrl'
            }).state('sell-catalogs', {
                url: '/sell/catalogs',
                controller: 'SellCatalogsCtrl',
                templateUrl: 'catalog/list.html'
            });
        /*
        .state('admin_search', {
            url: '/admin/search/:kind/:query',
            templateUrl: function (stateParams) {

                var defaults = 'admin/search.html',
                    config;

                if (stateParams.kind !== undefined) {
                    config = ADMIN_SEARCH_KIND_CONFIG[stateParams.kind];
                    if (config && config.templateUrl) {
                        defaults = config.templateUrl;
                    }
                }

                return defaults;
            },
            controller: 'AdminSearchCtrl'
        })*/

    }).run(function (models) {
        models.init();
    });
}());
