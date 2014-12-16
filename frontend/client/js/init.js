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
            .state('login-status', {
                url: '/login_status',
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
