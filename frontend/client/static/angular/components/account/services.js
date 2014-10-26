angular.module('app').factory('accountEntity', 
function(endpoint, $window, entityManager, modelMeta) {
  var kind = '11';
  var accountEntity = {
    settings : function (account_key)
    {
      var info = modelMeta.getActionArguments(kind, 'update');
      var primary_email = info.primary_email;

      var config = {
        kind : kind,
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
      endpoint.post('logout', kind, {
        key : account_key
      }).then(function(response) {
          endpoint.invalidate_cache('current_account');
          $window.location.reload();
      });
    }
  };
  return accountEntity;
});
