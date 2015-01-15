/* Bootstrap file, it will try to load current account and model data and then bootstrap the application. */
(function () {
    'use strict';
    angular.element(document).ready(function () {
        var injector = angular.injector(['app']),
            endpoint = injector.get('endpoint'),
            failure = function () {
                var choice = prompt('Could not start application. Reload your browser and try again?');
                if (choice) {
                    window.location.reload(true);
                }
            };
        // models meta must be loaded first above all things because entire application depends on it
        endpoint.modelsMeta().then(function () {
            return endpoint.currentAccount();
        }).then(function (response) {
            angular.bootstrap(document, ['app']);
        }, failure);

    });
}());