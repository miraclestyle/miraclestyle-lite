angular.module('app').run(function(modelsConfig, modelsMeta) {
  modelsConfig(function(models) {
    models['12'].config.cache = true;
    models['12'].getSubdivisions = function(country_key, overrideConfig) {
      var subdivisionModel = models['13'], defaultArgs = modelsMeta.getDefaultActionArguments(subdivisionModel.kind, 'search');
      defaultArgs.ancestor = country_key;
      return subdivisionModel.search(defaultArgs, overrideConfig);
    };
 
  });

});
