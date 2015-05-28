(function () {
    'use strict';
    angular.module('app').run(ng(function (modelsConfig, modelsMeta) {
        modelsConfig(function (models) {
            models['12'].config.cache = true;
            models['12'].getSubdivisions = function (countryKey, overrideConfig) {
                var subdivisionModel = models['13'],
                    defaultArgs = modelsMeta.getDefaultActionArguments(subdivisionModel.kind, 'search');
                defaultArgs.ancestor = countryKey;
                return subdivisionModel.search(defaultArgs, overrideConfig);
            };

        });

    }));
}());