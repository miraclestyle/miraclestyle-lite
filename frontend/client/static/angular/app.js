// bootstrap file, introduces global App or MainApp
(function() {

    if (!window.console)
        window.console = {};
    if (!'log' in window.console) {
        window.console.log = angular.noop;
    }
    

    var host = location.protocol + '//' + location.host;

    // global configuration for the application
    // this config file will expand
    var GLOBAL_CONFIG = {
        'host' : host,
        'angular_modules' : ['ui.router', 'angular-data.DSCacheFactory'], // this will be changed accordingly
        'api_model_meta_path' : host + '/api/model_meta',
        'api_endpoint_path' : host + '/api/endpoint'
    };

    // implies global, we expose only 1 variable to global scope, that is our main module which
    // will contain all application code unless we want to separate some of the logic
    app = angular.module('app', GLOBAL_CONFIG['angular_modules'])// we can avoid a global if we build modules for each feature
    .constant('GLOBAL_CONFIG', GLOBAL_CONFIG).config(['$httpProvider', '$locationProvider',
    function($httpProvider, $locationProvider) {

        $httpProvider.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';

        $locationProvider.hashPrefix('!');

        $locationProvider.html5Mode(true);

    }]);

})();
