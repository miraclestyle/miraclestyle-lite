// bootstrap file, introduces global App or MainApp
(function () {
    
    // global configuration for the application
    // this config file will expand
    var GLOBAL_CONFIG = {
        'angular_modules': ['ui.router', 'ngBusy', 'ngSanitize', 'ngUpload', 'ngStorage', 'app.ui', 'ngDragDrop'] // this will be changed accordingly
    };
    
    // implies global, we expose only 1 variable to global scope, that is our main module which
    // will contain all application code unless we want to separate some of the logic
    MainApp = angular.module('MainApp', GLOBAL_CONFIG['angular_modules']) // we can avoid a global if we build modules for each feature
    .constant('GLOBAL_CONFIG', GLOBAL_CONFIG)
    .config(['$httpProvider', '$locationProvider',
      function($httpProvider, $locationProvider) {
         
         $httpProvider.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';
      
         $locationProvider.hashPrefix('!');
         
         $locationProvider.html5Mode(true);
         
    }]);
     
})();
