'use strict';
angular.module('app').run(function (modelsEditor, modelsMeta, modelsConfig, $modal) {

  modelsConfig(function (models) {


    $.extend(models['31'], {
      manageModal: function (entity, callback) {
        
        var fields = modelsMeta.getActionArguments('31', 'update');
        fields._images.ui.template = 'catalog/underscore/image.html';

        var isNew = !angular.isDefined(entity),
          afterSave = function ($scope) {
            $scope.setAction('catalog_upload_images');
            callback($scope.entity);
          },
          noComplete = function ($scope) {
            afterComplete($scope);
          },
          afterComplete = function ($scope) {
            $scope.setAction('update');
          },
          config = {
            kind: this.kind,
            action: (isNew ? 'create' : 'update'),
            fields: _.toArray(fields),
            templateBodyUrl: 'catalog/manage.html',
            templateFooterUrl: 'catalog/manage_footer.html',
            afterSave: afterSave,
            afterSaveError: afterSave,
            afterComplete: afterComplete,
            afterCompleteError: afterComplete,
            noComplete: noComplete,
            scope: {
              addProducts: function ()
              {
                var parentScope = this;
              
                $modal.open({
                  templateUrl: 'catalog/products.html',
                  controller: function ($scope, $modalInstance) {
                    $scope.entity = parentScope.entity; // important for config bellow
                    $scope.args = parentScope.args; // important for config bellow
                    // inner scope things
                    $scope.images = angular.copy(parentScope.args._images);
                    var access = angular.copy(parentScope.args.ui.access);
                    access.push(fields._images.code_name);
                    var reader = models['31'].reader(parentScope.entity, $scope.images, access, access);
                    
                    $scope.loadMoreImages = function (callback) {
                      if (reader.more) {
                        reader.load().then(callback);
                      }
                      else {
                        callback();
                      }
                       
                    };
                    
                    $scope.fieldProducts = angular.copy(fields._products);
                    $.extend(true, $scope.fieldProducts, {
                      ui: {
                        specifics: {
                          listFields: [{
                            label: 'Name',
                            ley: 'name'
                          }],
                          sortFields: ['country', 'region', 'city', 'postal_code',
                            'street', 'name', 'email', 'telephone',
                            'default_shipping', 'default_billing'
                          ]
                        }
                      }
                    });
                    
                    $scope.save = function () {
                      $scope.close();
                    };
                    
                    $scope.close = function () {
                      $modalInstance.dismiss('close');
                    };
                    
                    
                  }
                });
                
              },
              accordions: {
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
              }
            }
          };

        if (isNew) {
          // current seller
          models['23'].current().then(function (response) {
            modelsEditor.create(config).prepare({}, {
              seller: response.data.entity.key
            });
          });

        } else {

          modelsEditor.create(config).read(entity, {
            key: entity.key,
            read_arguments: {
              _images: {}
            }
          });

        }

      }
    });

  });


});