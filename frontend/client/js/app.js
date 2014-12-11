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
                'ngSanitize', 'angular-data.DSCacheFactory', 'ngDragDrop', 'currencyFilter'], // this will be changed accordingly
            apimodelsMetaPath: host + '/api/model_meta',
            apiEndpointPath: host + '/api/endpoint',
            dateFormat: 'yyyy-MM-dd HH:mm:ss Z',
            defaultImage: 'http://placehold.it/240x100',
            defaultLogo: 'http://placehold.it/240x100',
            defaultCatalogCover: 'http://placehold.it/240x360',
            gridMaxWidth: 240,
            gridMinWidth: 180
        };

    angular.module('app', GLOBAL_CONFIG.angularModules) // we can avoid a global if we build modules for each feature
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