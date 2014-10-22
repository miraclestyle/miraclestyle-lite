angular.module('app').factory('buyerEntity', 
function(endpoint, $window, entityManager, modelMeta, current_account) {
  var kind = '19',
   buyerEntity = {
    settings : function ()
    {
      var config = {
        kind : kind,
        action : 'update',
        excludeFields : ['account', 'read_arguments'],
        argumentLoader : function ($scope)
        {
          var cfg = $scope.config,
              args = cfg.defaultArgumentLoader($scope);
          args.account = current_account.key;
          return args;
        }
      };
      
      entityManager.create(config).read({}, {
        account : current_account.key
      });
      
    }
  };
  return buyerEntity;
});
