/* Bootstrap file, it will try to load current account and model data and then bootstrap the application. */
angular.element(document).ready(function () {
   var injector = angular.injector(['app']),
       Endpoint = injector.get('Endpoint'),
       $q = injector.get('$q'),
       depencies = [Endpoint.model_meta(), Endpoint.current_account()];
       
       $q.all(depencies).then(function () {
           angular.bootstrap(document, ['app']);
       }, function () {
         alert('Could not bootstrap the application. Please reload the browser.');
       });
        
});