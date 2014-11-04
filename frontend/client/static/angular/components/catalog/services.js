'use strict';
angular.module('app').run(function (modelsEditor, modelsMeta, modelsConfig) {
   
    modelsConfig(function (models) {
      
      var read_arguments = {
        _images : {}
      },
      accordions = function ()
      {
        return {
                closeOthers: true,
                general: {
                  label: 'General',
                  open: true
                },
                images: {
                  label: 'Images',
                  open: false
                },
                products: {
                  label: 'Products',
                  open: false
                },
                embed: {
                  label: 'Embed',
                  open: false
                }
            };
      };
      
      var fields = modelsMeta.getActionArguments('31', 'update');
 
      $.extend(models['31'], {
        manageModal: function (entity) {
 
          var isNew = !angular.isDefined(entity),
          config = {
            kind: this.kind,
            action: (isNew ? 'create' : 'update'),
            fields : _.toArray(fields),
            templateBodyUrl: 'catalog/manage.html',
            templateFooterUrl : 'catalog/manage_footer.html',
            afterSave: function ($scope)
            {
               $scope.args.action_id = 'catalog_upload_images'; 
            },
            afterComplete: function ($scope)
            {
              $scope.args.action_id = 'update';
            },
            scope: {
              accordions: accordions()
            }
          };
          
          if (isNew)
          {
            
            // current seller
            models['23'].current().then(function (response) {
              
              modelsEditor.create(config).prepare({}, {
                seller: response.data.entity.key
              });
              
            });
            
          }
          else
          {
            
            modelsEditor.create(config).read(entity, {
              key: entity.key,
              read_arguments: read_arguments
            });
            
          }
          
          
  
        }
      });

  });
  
  
});
