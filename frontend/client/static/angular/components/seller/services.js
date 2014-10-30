angular.module('app').run(function($window, modelsConfig, modelsMeta, modelsEditor) {
  modelsConfig(function (models) {
    var read_arguments = {
       _address : {},
       _content : {},
       _plugin_group : {}
     };
     
     $.extend(models['23'], {
      settingsModal : function (account_key)
      {
        var fields = modelsMeta.getActionArguments(this.kind, 'update');
        fields._content.ui.label = false;
        fields._content.modelclass.documents.ui = { 
          specifics : { 
            listFields : [{
            label : 'Title',
            key : 'title'
          }]
         }
        };
        fields._plugin_group.ui.label = false;
   
        var config = {
          kind : this.kind,
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
        
        modelsEditor.create(config).read({}, {
          account : account_key,
          read_arguments : read_arguments
        });
        
      }
    });
  
  });
   
});
