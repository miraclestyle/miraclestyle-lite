angular.module('app').factory('sellerEntity', 
function(endpoint, $window, entityManager, modelMeta) {
  var kind = '23',
   read_arguments = {
     _address : {},
     _content : {},
     _plugin_group : {}
   },
   sellerEntity = {
    settings : function (account_key)
    {
      var fields = modelMeta.getActionArguments(kind, 'update');
      fields._content.ui.label = false;
      var config = {
        kind : kind,
        action : 'update',
        fields : fields,
        excludeFields : ['account', 'read_arguments'],
        templateBodyUrl : 'seller/settings.html',
        argumentLoader : function ($scope)
        {
          var cfg = $scope.config,
              args = cfg.defaultArgumentLoader($scope);
          args.account = account_key;
          args.read_arguments = read_arguments;
          return args;
        },
        scope : {
          accordions : {
            closeOthers : true,
            general : {
              label : 'General',
              open : true
            },
            plugins : {
              label : 'Plugins',
              open : false
            },
            contents : {
              label : 'Contents',
              open : false
            }
          }
        }
      };
      
      entityManager.create(config).read({}, {
        account : account_key,
        read_arguments : read_arguments
      });
      
    }
  };
  return sellerEntity;
});
