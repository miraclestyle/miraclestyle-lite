angular.module('app').run(function(modelsConfig, endpoint, $window, modelsEditor, modelsMeta) {
   
   modelsConfig(function (models) {
     
      $.extend(models['11'], {
          settingsModal : function (account_key)
          {
            var info = modelsMeta.getActionArguments(this.kind, 'update');
                primary_email = info.primary_email;
      
            var config = {
              kind : this.kind,
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
            
            modelsEditor.create(config).read({
              key : account_key
            });
            
          },
          logout : function (account_key)
          {
            this.actions.logout({
              key : account_key
            }).then(function(response) {
                endpoint.invalidate_cache('currentAccount');
                $window.location.reload();
            });
          }
        });
     
   });
   
});
