angular.module('app').factory('buyerEntity', 
function(endpoint, $window, entityManager, modelMeta, $q) {
  var kind = '19',
   buyerEntity = {
    settings : function (account_key)
    {
      var fields = modelMeta.getActionArguments(kind, 'update');
       
      fields.addresses.ui = {specifics : {
        onlyListFields : ['name', '_country', '_region', 'address', 'default_billing', 'default_shipping'],
        fields : $.map(['name', 'email', 'phone', 'country', 'region', 'city',
         'postal_code', 'street', 'default_shipping', 'default_billing'], function (item) {
           return fields.addresses.modelclass[item];
        }),
        beforeSave : function ($scope, info)
        {
          var promises = [];
          
          if (info.config.repeated)
          {
       
          var updated_address = $scope.args; 
          if ((!updated_address._region && updated_address.region) || (updated_address._region && updated_address._region.key !== updated_address.region))
          {
            var promise = endpoint.post('search', '13', {
              search : {
                keys : [updated_address.region]
              }
            });
            
            promise.then(function (response) {
              updated_address._region = response.data.entities[0];
            });
            
            promises.push(promise);
          }
          
          if ((!updated_address._country && updated_address.country) || (updated_address._country && updated_address._country.key !== updated_address.country))
          {
            var promise = endpoint.post('search', '12', {
              search : {
                keys : [updated_address.country]
              }
            });
            promise.then(function (response) {
              updated_address._country = response.data.entities[0];
            });
            
            promises.push(promise);
          }
          
          angular.forEach($scope.parentArgs, function (address) {
                    if (updated_address.default_billing || updated_address.default_shipping)
                    {
                        if (updated_address != address)
                        {
                            
                            if (updated_address.default_billing)
                            {
                                address.default_billing = false;
                            }
                            
                            if (updated_address.default_shipping)
                            {
                                address.default_shipping = false;
                            }
                        }
                         
                    }
                    
                });
                
          }
          
          if (promises.length)
          {
            return $q.all(promises);
          }
          else
          {
            return false;
          }
           
        }
      }};
 
      var config = {
        fields : [fields.addresses],
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
