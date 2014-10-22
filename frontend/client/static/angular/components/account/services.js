angular.module('app').factory('accountEntity', 
function(endpoint, $window, entityManager, modelMeta) {
  var accountEntity = {
    settings : function (account)
    {
      var info = modelMeta.get(account.kind);
      var primary_email = angular.copy(info.mapped_actions.update.arguments.primary_email);
      primary_email.choices = account.emails;
      primary_email.ui = {};
      primary_email.ui.writableName = '_primary_email';
      var config = {
        kind : '11',
        body : 'account/settings.html',
        argumentLoader : function ()
        {
          var disassociate = [];
          angular.forEach(this.entity.identities, function (value) {
                   if (!value.associated)
                   {
                       disassociate.push(value.identity);
                   }
              });
          return {
            primary_email : this.entity._primary_email,
            disassociate : disassociate,
            key: this.entity.key
          };
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
      
      entityManager.create(config).read(account);
      
    },
    logout : function (account)
    {
      endpoint.post('logout', '11', {
        key : account.key
      }).then(function(response) {
          endpoint.invalidate_cache('current_account');
          $window.location.reload();
      });
    }
  };
  return accountEntity;
});
