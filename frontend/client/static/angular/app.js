// bootstrap file, introduces global App or MainApp
/*global angular, window, console, jQuery, $, document*/
'use strict';
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
    host : host,
    angularModules : ['ui.router', 'ui.sortable', 'ui.select', 'ngUpload', 'ui.bootstrap', 'ui.bootstrap.datetimepicker', 'ui.inflector', 'ngSanitize', 'angular-data.DSCacheFactory'], // this will be changed accordingly
    apimodelsMetaPath : host + '/api/model_meta',
    apiEndpointPath : host + '/api/endpoint',
    dateFormat : 'yyyy-MM-dd HH:mm:ss Z'
  };
 
  angular.module('app', GLOBAL_CONFIG.angularModules)// we can avoid a global if we build modules for each feature
  .constant('GLOBAL_CONFIG', GLOBAL_CONFIG).config(function($httpProvider, $locationProvider) {
    $httpProvider.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';
    $locationProvider.hashPrefix('!');
    $locationProvider.html5Mode(true);
  });


})();
