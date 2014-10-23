angular.module('app').factory('accountEntity', 
function(endpoint, $window, entityManager, modelMeta) {
  var accountEntity = {
    settings : function (account_key)
    {
      var info = modelMeta.get('11');
      var primary_email = angular.copy(info.mapped_actions.update.arguments.primary_email);

      var config = {
        kind : '11',
        templateBodyUrl : 'account/settings.html',
        argumentLoader : function ($scope)
        {
          var disassociate = [];
          angular.forEach($scope.entity.identities, function (value) {
                   if (!value.associated)
                   {
                       disassociate.push(value.identity);
                   }
              });
          return {
            primary_email : $scope.entity._primary_email,
            disassociate : disassociate,
            key: $scope.entity.key
          };
        },
        init : function ($scope)
        {
          $scope.primary_email.choices = $scope.entity.emails;
          $scope.primary_email.ui = {};
          $scope.primary_email.ui.writableName = '_primary_email';
        },
        scope : {
          primary_email : primary_email,
          isAssociated : function(ident)
          {
            return $.inArray(ident.identity, this.args.disassociate) === -1;
          },
          disassociate : function(ident)
          {
              if (this.isAssociated(ident))
              {
                 this.args.disassociate.push(ident.identity);
              }
              else
              {
                 this.args.disassociate.remove(ident.identity);
              }
          }
        }
      };
      
      entityManager.create(config).read({
        key : account_key
      });
      
    },
    logout : function (account_key)
    {
      endpoint.post('logout', '11', {
        key : account_key
      }).then(function(response) {
          endpoint.invalidate_cache('current_account');
          $window.location.reload();
      });
    }
  };
  return accountEntity;
});
