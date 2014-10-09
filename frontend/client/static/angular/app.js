// bootstrap file, introduces global App or MainApp
/*global angular, window, console, jQuery, $, document*/
(function() {

  if (!window.console) {
    window.console = {};
  }

  angular.forEach(['log', 'error', 'info'], function(method) {
    if (!window.console[method]) {
      window.console[method] = angular.noop;
    }
  });

  var host = location.protocol + '//' + location.host,
  // global configuration for the application
  // this config file will expand
  GLOBAL_CONFIG = {
    'host' : host,
    'angular_modules' : ['ui.router', 'ui.select', 'ui.bootstrap', 'ui.inflector', 'ngSanitize', 'angular-data.DSCacheFactory'], // this will be changed accordingly
    'api_model_meta_path' : host + '/api/model_meta',
    'api_endpoint_path' : host + '/api/endpoint'
  };

  angular.module('app', GLOBAL_CONFIG.angular_modules)// we can avoid a global if we build modules for each feature
  .constant('GLOBAL_CONFIG', GLOBAL_CONFIG).config(['$httpProvider', '$locationProvider',
  function($httpProvider, $locationProvider) {

    $httpProvider.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';

    $locationProvider.hashPrefix('!');

    $locationProvider.html5Mode(true);

  }]);

})();
