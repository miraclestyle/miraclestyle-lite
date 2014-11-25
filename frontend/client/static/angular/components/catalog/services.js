(function () {
    'use strict';
    angular.module('app').run(function (modelsEditor, modelsMeta, modelsConfig, $modal, modals, helpers) {

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
                            init: function ($scope) {
                                $.extend(fields._images, {
                                    ui: {
                                        label: 'Products',
                                        template: 'catalog/underscore/image.html',
                                        specifics: {
                                            sortableOptions: {
                                                stop: function () {
                                                    if (fields._images.ui.specifics.parentArgs.length) {
                                                        var total = fields._images.ui.specifics.parentArgs[0].sequence;
                                                        angular.forEach(fields._images.ui.specifics.parentArgs,
                                                            function (ent, i) {
                                                                i = ((total + 1) - i);
                                                                ent.sequence = i;
                                                            });

                                                        $scope.$broadcast('itemOrderChanged');
                                                    }
                                                }
                                            }
                                        }
                                    }
                                });
                            },
                            noComplete: noComplete,
                            scope: { // scope for this modal dialog
                                addProducts: function () {
                                    // this function is completely custom, meaning that the entire workflow defined here is for
                                    // pricetag positioning and product editing...
                                    var parentScope = this;
                                    $modal.open({
                                        templateUrl: 'catalog/products.html',
                                        controller: function ($scope, $modalInstance) {
                                            var accessImages = angular.copy(parentScope.args.ui.access),
                                                accessProducts = angular.copy(parentScope.args.ui.access),
                                                imagesReader,
                                                productsReader;
                                            accessImages.push(fields._images.code_name);
                                            accessProducts.push(fields._products.code_name);

                                            $scope.rootScope = parentScope.rootScope; // pass the rootScope
                                            $scope.entity = parentScope.entity;
                                            $scope.args = angular.copy(parentScope.args);

                                            // readers here could work but generally not very good
                                            imagesReader = models[config.kind].reader($scope.args, accessImages, function (items) {
                                                $scope.args._images.extend(items);
                                            });
                                            // set next arguments from initially loaded data from root scope
                                            imagesReader.state(parentScope.config.ui.specifics.reader); // this is not good
                                            productsReader = models[config.kind].reader($scope.args, accessProducts, function (items) {
                                                $scope.args._products.extend(items);
                                            });

                                            $scope.loadMoreImages = function (callback) {
                                                if (imagesReader.more) {
                                                    imagesReader.load().then(callback);
                                                } else {
                                                    callback();
                                                }
                                            };

                                            productsReader.load(); // load first 10 products

                                            $scope.fieldProducts = fields._products;
                                            $.extend($scope.fieldProducts, {
                                                ui: {
                                                    specifics: {
                                                        addText: 'Add Product',
                                                        getRootArgs: function () {
                                                            return angular.copy($scope.args);
                                                        },
                                                        sortable: false,
                                                        listFields: [{
                                                            label: 'Name',
                                                            key: 'name'
                                                        }],
                                                        afterSave: function ($scope) {
                                                            $scope.setAction('product_upload_images');
                                                        },
                                                        afterComplete: function ($scope) {
                                                            $scope.setAction('update');
                                                        },
                                                        noComplete: function ($scope) {
                                                            $scope.setAction('update');
                                                        },
                                                        reader: productsReader
                                                    }
                                                }
                                            });

                                            $scope.fieldProducts.modelclass.images.ui = {
                                                formName: 'images'
                                            };

                                            $.extend($scope.fieldProducts.modelclass._instances, {
                                                ui: {
                                                    label: 'Product Instances',
                                                    specifics: {
                                                        getRootArgs: function () {
                                                            return angular.copy($scope.args);
                                                        },
                                                        sortable: false,
                                                        canManage: function (entity) {
                                                            if (!entity || !entity._instances.length) {
                                                                modals.alert('You must add variations in order to create instance.');
                                                                return false;
                                                            }
                                                        },
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
                                                        }],
                                                        excludeFields: ['variant_signature'],
                                                        afterSave: function ($scope) {
                                                            $scope.setAction('product_instance_upload_images');
                                                        },
                                                        afterComplete: function ($scope) {
                                                            $scope.setAction('update');
                                                        },
                                                        noComplete: function ($scope) {
                                                            $scope.setAction('update');
                                                        }
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

                                            $.extend($scope.fieldProducts.modelclass.images, {
                                                ui: {
                                                    formName: 'images',
                                                    specifics: {}
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
                                                // @todo rpc to save pricetag data
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
