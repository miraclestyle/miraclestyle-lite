// code for account
angular.module('app')
  .controller('SellCatalogsCtrl', function ($scope, modelsEditor, modelsMeta, models, modelsUtil) {

    $scope.create = function () {
      models['31'].manageModal();
    };
    
    $scope.manage = function (entity)
    {
      models['31'].manageModal(entity);
    };
    
    
    $scope.search = {
      results: []
    };
    
    models['23'].current().then(function (response) {
       var args = modelsMeta.getActionArguments('31', 'search');
       args.search['default'].ancestor = response.data.entity.key;
       models['31'].actions.search(args.search['default']).then(function (response) {
        $scope.search.results = response.data.entities;
      });
    });
    
    

  });