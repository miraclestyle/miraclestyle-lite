/* Bootstrap file, it will try to load current account and model data and then bootstrap the application. */
(function () {
    'use strict';
    angular.element(document).ready(function () {
        var injector = angular.injector(['app']),
            endpoint = injector.get('endpoint');

        endpoint.modelsMeta().then(function () {
            return endpoint.currentAccount();
        }).then(function () {
            angular.bootstrap(document, ['app']);
        }, function () {
            alert('Could not bootstrap the application. Please reload the browser.');
        });

        /*
        
        depencies = [endpoint.modelsMeta(), endpoint.currentAccount()]
        $q.all(depencies).then(function () {
            angular.bootstrap(document, ['app']);
        }, function () {
            alert('Could not bootstrap the application. Please reload the browser.');
        });*/

    });
}());