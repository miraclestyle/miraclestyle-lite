(function () {
    'use strict';
    angular.module('app').run(function (modelsEditor, modelsMeta, modelsConfig, $modal, modals) {

        modelsConfig(function (models) {
            $.extend(models['31'], {
                manageModal: function (entity, callback) { // modal dialog for managing the catalog

                    var fields = modelsMeta.getActionArguments('31', 'update'),
                        isNew = !angular.isDefined(entity),
                        afterSave = function ($scope) {
                            $scope.setAction('catalog_upload_images');
                            callback($scope.entity);
                        },
                        afterComplete = function ($scope) {
                            $scope.setAction('update');
                        },
                        noComplete = function ($scope) {
                            afterComplete($scope);
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
                            scope: { // scope for this modal dialog
                                addProducts: function () {
                                    var parentScope = this;

                                    $modal.open({
                                        templateUrl: 'catalog/products.html',
                                        controller: function ($scope, $modalInstance) {
                                            var access = angular.copy(parentScope.args.ui.access), reader;
                                            access.push(fields._images.code_name);
                                            $scope.entity = parentScope.entity;
                                            $scope.args = angular.copy(parentScope.args); // for modifying
                                            $scope.modelsEditorScope = parentScope.modelsEditorScope;
                                            reader = models['31'].reader(parentScope.entity, $scope.args._images, access, access);

                                            $scope.loadMoreImages = function (callback) {
                                                if (reader.more) {
                                                    reader.load().then(callback);
                                                } else {
                                                    callback();
                                                }

                                            };

                                            $scope.fieldProducts = angular.copy(fields._products);
                                            // @todo this needs more work
                                            $.extend($scope.fieldProducts, {
                                                ui: {
                                                    specifics: {
                                                        sortable: false,
                                                        listFields: [{
                                                            label: 'Name',
                                                            key: 'name'
                                                        }]
                                                    }
                                                }
                                            });

                                            $.extend($scope.fieldProducts.modelclass._instances, {
                                                ui: {
                                                    specifics: {
                                                        sortable: false,
                                                        beforeManage: function (entity) {
                                                            if (!entity || !entity._instances.length) {
                                                                modals.alert('You must add variations in order to create instance');
                                                                return false;
                                                            }
                                                        },
                                                        label: 'Product Instances',
                                                        addText: 'Add Product Instance',
                                                        listFields: [{
                                                            label: 'Code',
                                                            key: 'code'
                                                        }, {
                                                            label: 'Price Adjustment',
                                                            key: 'unit_price'
                                                        }, {
                                                            label: 'Weight Adjustment',
                                                            key: 'weight'
                                                        }, {
                                                            label: 'Volume Adjustment',
                                                            key: 'volume'
                                                        }]
                                                    }
                                                }
                                            });

                                            $.extend($scope.fieldProducts.modelclass.contents, {
                                                ui: {
                                                    specifics: {
                                                        addText: 'Add Content',
                                                        listFields: [{
                                                            label: 'Title',
                                                            key: 'title'
                                                        }]
                                                    }
                                                }
                                            });

                                            $.extend($scope.fieldProducts.modelclass.variants, {
                                                ui: {
                                                    specifics: {
                                                        addText: 'Add Variant',
                                                        listFields: [{
                                                            label: 'Name',
                                                            key: 'name'
                                                        }]
                                                    }
                                                }
                                            });

                                            $scope.save = function () {
                                                // @todo must do an rpc to save the data...
                                                $scope.close();
                                            };

                                            $scope.close = function () {
                                                $modalInstance.dismiss('close');
                                            };


                                        }
                                    });

                                },
                                accordions: { // accordion listeners & labels
                                    closeOthers: true,
                                    groups: [{
                                        label: 'General',
                                        open: true,
                                        key: 'general'
                                    }, {
                                        label: 'Products',
                                        open: false,
                                        key: 'products'
                                    }]
                                }
                            }
                        };

                    fields._images.ui.template = 'catalog/underscore/image.html';

                    if (isNew) {
                        // get current seller
                        models['23'].current().then(function (response) {
                            modelsEditor.create(config).prepare({}, {
                                seller: response.data.entity.key,
                                read_arguments: {
                                    _images: {}
                                }
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
}());
