/* Bootstrap file, it will try to load current account and model data and then bootstrap the application. */
(function () {
    'use strict';
    angular.element(document).ready(function () {
        var failure = function () {
                var choice = confirm('Could not start application. Reload your browser and try again?');
                if (choice) {
                    window.location.reload(true);
                }
            },
            injector = angular.injector(['config']),
            $http = injector.get('$http'),
            $q = injector.get('$q'),
            GLOBAL_CONFIG = injector.get('GLOBAL_CONFIG'),
            promises = [$http.get(GLOBAL_CONFIG.api.modelsMeta), $http.get(GLOBAL_CONFIG.api.endpoint.path + '?action_id=current_account&action_model=11')];

        $q.all(promises).then(function (response) {
            var d1 = response[0].data, d2 = response[1].data;
            window.MODELS_META = d1;
            window.CURRENT_ACCOUNT = d2.entity;
            if ((d1 && d1.errors) || (d2 && d2.errors)) {
                failure();
            } else {
                angular.bootstrap(document, ['app']);
            }
        }, failure);

    });
}());