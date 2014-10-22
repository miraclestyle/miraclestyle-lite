angular.module('app').factory('buyerEntity', 
function(endpoint, $window, entityManager, modelMeta) {
  var kind = '19',
   buyerEntity = {
    settings : function (account_key)
    {
      var config = {
        kind : kind,
        action : 'update',
        excludeFields : ['account', 'read_arguments'],
        argumentLoader : function ($scope)
        {
          var cfg = $scope.config,
              args = cfg.defaultArgumentLoader($scope);
          args.account = account_key;
          return args;
        }
      };
      
      entityManager.create(config).read({}, {
        account : account_key
      });
      
    }
  };
  return buyerEntity;
});
