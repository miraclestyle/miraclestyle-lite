/* Bootstrap file, it will try to load current account and model data and then bootstrap the application. */
(function () {
    'use strict';
    angular.element(document).ready(function () {
        var failure = function () {
                var choice = prompt('Could not start application. Reload your browser and try again?');
                if (choice) {
                    window.location.reload(true);
                }
            };
        $.ajax({
            cache: true,
            dataType: 'json',
            url: '/api/model_meta',
            success: function (data) {
                window.MODELS_META = data;
                angular.bootstrap(document, ['app']);
            },
            error: failure
        });

    });
}());