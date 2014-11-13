'use strict';
angular.module('app').run(function (modelsEditor, modelsMeta, modelsConfig, $modal) {

  modelsConfig(function (models) {

    var fields = modelsMeta.getActionArguments('31', 'update');
    fields._images.ui.template = 'catalog/underscore/image.html';
    $.extend(models['31'], {
      manageModal: function (entity, callback) {

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
                    $scope.args = angular.copy(parentScope.args._images);
                    $scope.save = function () {
                      $.extend(parentScope.args._images, $scope.args);
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