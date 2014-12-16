// bootstrap file, introduces global App or MainApp
(function () {

    'use strict';

    if (!window.console) {
        window.console = {};
    }

    angular.forEach(['log', 'error', 'info'], function (method) {
        if (!window.console[method]) {
            window.console[method] = angular.noop;
        }
    });

    var host = window.location.protocol + '//' + window.location.host,
        // global configuration for the application
        // this config file will expand
        GLOBAL_CONFIG = {
            host: host,
            angularModules: ['ui.router', 'ui.sortable', 'ui.select', 'ngUpload',
                'ui.bootstrap', 'ui.bootstrap.datetimepicker', 'ui.inflector', 'monospaced.elastic',
                'ngSanitize', 'angular-data.DSCacheFactory', 'ngDragDrop'], // this will be changed accordingly
            apimodelsMetaPath: host + '/api/model_meta',
            apiEndpointPath: host + '/api/endpoint',
            dateFormat: 'yyyy-MM-dd HH:mm:ss Z',
            defaultImage: 'http://placehold.it/240x100',
            defaultLogo: 'http://placehold.it/240x100',
            defaultCatalogCover: 'http://placehold.it/240x360',
            grid: {
                maxWidth: 240,
                minWidth: 180,
                maxHeight: 360
            },
            imageSizes: _.range(50, 1650, 50), // loading ranges for get serving url
            admin: {
                listTemplates: {},
                listDisplayDirective: ['31', '11'],
                listTitles: {
                    '31': 'Catalogs',
                    '11': 'Users'
                }
            }
        };

    angular.module('app', GLOBAL_CONFIG.angularModules)
        .constant('GLOBAL_CONFIG', GLOBAL_CONFIG).config(function ($httpProvider, $locationProvider) {
            $httpProvider.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';
            $locationProvider.hashPrefix('!');
            $locationProvider.html5Mode(true);
        });


}());

$(function () {
    'use strict';
    var container = $("<div>").css({ height: 1, overflow: "scroll" }).appendTo("body"),
        child = $("<div>").css({ height: 2 }).appendTo(container);
    window.SCROLLBAR_WIDTH = container.width() - child.width();
    container.remove();
});