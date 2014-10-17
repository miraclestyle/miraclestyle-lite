/* Bootstrap file, it will try to load current account and model data and then bootstrap the application. */
'use strict';
angular.element(document).ready(function () {
   var injector = angular.injector(['app']),
       endpoint = injector.get('endpoint'),
       $q = injector.get('$q'),
       depencies = [endpoint.model_meta(), endpoint.current_account()];
       
       $q.all(depencies).then(function () {
           angular.bootstrap(document, ['app']);
       }, function () {
         alert('Could not bootstrap the application. Please reload the browser.');
       });
        
});