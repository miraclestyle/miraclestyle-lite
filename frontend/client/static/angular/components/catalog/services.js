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
                            templateFooterUrl: 'catalog/manage_footer.html',
                            afterSave: afterSave,
                            afterSaveError: afterSave,
                            afterComplete: afterComplete,
                            afterCompleteError: afterComplete,
                            init: function ($scope) {
                                $.extend(fields._images, {
                                    ui: {
                                        label: false,
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
                                        controller: function ($scope, $modalInstance, $timeout) {
                                            var accessImages = angular.copy(parentScope.args.ui.access),
                                                imagesReader,
                                                fieldProductAfterSave;
                                            accessImages.push(fields._images.code_name);

                                            $scope.rootScope = parentScope.rootScope; // pass the rootScope
                                            $scope.entity = parentScope.entity;
                                            $scope.args = angular.copy(parentScope.args);
                                            $scope.config = $scope.rootScope.config;

                                            // readers here could work but generally not very good
                                            imagesReader = models[config.kind].reader($scope.args, accessImages, function (items) {
                                                $scope.args._images.extend(items);
                                            });
                                            // set next arguments from initially loaded data from root scope
                                            imagesReader.state(parentScope.config.ui.specifics.reader); // this is not good

                                            $scope.fakeProducts = [{
                                                _state: '_deleted'
                                            }];

                                            $scope.onStart = function (event, ui, image, pricetag) {
                                                $(ui.helper).addClass('dragged');
                                                $(ui.helper).find('a').addClass('dragged');
                                            };

                                            $scope.onDrag = function (event, ui, image, pricetag) {
                                                var fn = function () {
                                                    var helper = $(ui.helper),
                                                        parent = helper.parents('.catalog-slider-item:first'),
                                                        helperW = helper.outerWidth(),
                                                        parentW = parent.width(),
                                                        nextParent = parent.next(),
                                                        prevParent = parent.prev(),
                                                        newParent,
                                                        newPositionLeft,
                                                        currentTop = parseInt(helper.css('top'), 10),
                                                        newImage,
                                                        currentLeft = parseInt(helper.css('left'), 10),
                                                        left,
                                                        moveLeft = true,
                                                        index = $scope.args._images.indexOf(image),
                                                        pass = false;

                                                    if (!parent.length) {
                                                        return; // jquery ui callback fallthrough
                                                    }

                                                    if (currentLeft === 0) {
                                                        left = 0;
                                                    } else {
                                                        left = (parentW - (currentLeft + helperW));
                                                        moveLeft = false;
                                                    }
                                                    if (left === 0 && moveLeft) {
                                                        // go to left
                                                        index -= 1;
                                                        pass = true;
                                                        newParent = prevParent;
                                                        newPositionLeft = (prevParent.width() - helperW) - 5;

                                                    } else if (left === 0 && !moveLeft) {
                                                        // go to right
                                                        index += 1;
                                                        pass = true;
                                                        newParent = nextParent;
                                                        newPositionLeft = 5;
                                                    }

                                                    if (index !== -1 && pass) {
                                                        newImage = $scope.args._images[index];
                                                        if (angular.isDefined(newImage)) {
                                                            pricetag.image_width = newParent.width();
                                                            pricetag.image_height = newParent.height();
                                                            pricetag.position_left = newPositionLeft;
                                                            pricetag.position_top = currentTop;
                                                            pricetag._position_left = newPositionLeft;
                                                            pricetag._position_top = currentTop;
                                                            image.pricetags.remove(pricetag);
                                                            newImage.pricetags.push(angular.copy(pricetag));

                                                        }
                                                    }
                                                };
                                                fn();

                                            };

                                            $scope.onStop = function (event, ui, image, pricetag) {

                                                var target = $(event.target).parents('.catalog-slider-item:first');

                                                pricetag.position_top = ui.position.top;
                                                pricetag.position_left = ui.position.left;
                                                pricetag.image_width = target.width();
                                                pricetag.image_height = target.height();

                                                pricetag._position_top = pricetag.position_top;
                                                pricetag._position_left = pricetag.position_left;

                                            };

                                            $scope.onDrop = function (event, ui, image) {
                                                var target_drop = $(event.target),
                                                    posi = target_drop.offset(),
                                                    posi2 = ui.offset,
                                                    newPricetagConfig = {
                                                        position_top: posi2.top - posi.top,
                                                        position_left: posi2.left - posi.left,
                                                        image_width: target_drop.width(),
                                                        image_height: target_drop.height()
                                                    };
                                                $scope.createProduct(image, newPricetagConfig);
                                            };

                                            $scope.loadMoreImages = function (callback) {
                                                if (imagesReader.more) {
                                                    imagesReader.load().then(callback);
                                                } else {
                                                    callback();
                                                }
                                            };

                                            fieldProductAfterSave = function (fieldScope) {
                                                fieldScope.setAction('product_upload_images');
                                                var image = _.findWhere(fieldScope.response.data.entity._images, {key: $scope.image.key}),
                                                    updatedPricetag = image.pricetags;
                                                if (!$scope.pricetag.key) {
                                                    updatedPricetag = _.last(updatedPricetag);
                                                } else {
                                                    updatedPricetag = _.findWhere(updatedPricetag, {key: $scope.pricetag.key});
                                                }
                                                $.extend($scope.pricetag, updatedPricetag);
                                            };

                                            $scope.manageProduct = function (image, pricetag) {
                                                $scope.image = image;
                                                $scope.pricetag = pricetag;
                                                models['31'].actions.read({
                                                    key: $scope.entity.key,
                                                    read_arguments: {
                                                        _images: {
                                                            config: {
                                                                keys: [image.key]
                                                            },
                                                            pricetags: {
                                                                config: {},
                                                                _product: {
                                                                    config: {}
                                                                }
                                                            }
                                                        }
                                                    }
                                                }).then(function (response) {
                                                    var responseEntity = response.data.entity,
                                                        loadedPricetag = _.findWhere(responseEntity._images[0].pricetags, {key: $scope.pricetag.key});
                                                    $scope.pricetag._product = loadedPricetag._product;
                                                    $scope.fieldProduct.ui.specifics.manage(loadedPricetag._product);
                                                });
                                            };

                                            $scope.createProduct = function (image, config) {

                                                var newPricetag = {
                                                    image_height: config.image_height,
                                                    image_width: config.image_width,
                                                    position_left: config.position_left,
                                                    position_top: config.position_top,
                                                    _position_left: config.position_left,
                                                    _position_top: config.position_top,
                                                    value: {},
                                                    _product: {},
                                                    ui: {
                                                        access: ['_images', 'pricetags', image.pricetags.length]
                                                    }
                                                }, ii = $scope.args._images.indexOf(image);

                                                $scope.fieldProduct.ui.realPath = ['_images', ii, 'pricetags', image.pricetags.length, '_product'];
                                                $scope.args._images[ii].pricetags.push(newPricetag);
                                                $scope.pricetag = newPricetag;
                                                $scope.image = image;
                                                $scope.fieldProduct.ui.specifics.create();
                                            };

                                            $scope.fieldProduct = fields._images.modelclass.pricetags.modelclass._product;
                                            $.extend($scope.fieldProduct, {
                                                ui: {
                                                    args: 'pricetag._product',
                                                    parentArgs: 'pricetag',
                                                    path: ['_images', 'pricetags', '_product'],
                                                    render: false,
                                                    label: false,
                                                    specifics: {
                                                        modal: true,
                                                        templateFooterUrl: 'catalog/products_modal_footer.html',
                                                        addText: 'Add Product',
                                                        getRootArgs: function () {
                                                            return angular.copy($scope.args);
                                                        },
                                                        afterSave: fieldProductAfterSave,
                                                        afterComplete: function ($scope) {
                                                            $scope.setAction('update');
                                                        },
                                                        noComplete: function ($scope) {
                                                            $scope.setAction('update');
                                                        },
                                                        remove: function (product, close) {
                                                            $scope.pricetag._state = 'deleted';
                                                            close();
                                                        }
                                                    }
                                                }
                                            });

                                            $scope.fieldProduct.modelclass.images.ui = {
                                                formName: 'images'
                                            };

                                            $.extend($scope.fieldProduct.modelclass._instances, {
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

                                            $.extend($scope.fieldProduct.modelclass.contents, {
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

                                            $.extend($scope.fieldProduct.modelclass.images, {
                                                ui: {
                                                    formName: 'images',
                                                    specifics: {}
                                                }
                                            });

                                            $.extend($scope.fieldProduct.modelclass.variants, {
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
                                                $scope.rootScope.config.prepareReadArguments($scope);
                                                var promise = models[config.kind].actions[$scope.args.action_id]($scope.args);

                                                promise.then(function (response) {
                                                    $.extend($scope.entity, response.data.entity);
                                                    var new_args = $scope.rootScope.config.argumentLoader($scope);
                                                    $.extend($scope.args, new_args);
                                                    $.extend(parentScope.args, new_args);
                                                    $scope.args = angular.copy($scope.args);
                                                    parentScope.args = angular.copy(parentScope.args);
                                                }, function (response) {
                                                    // here handle error...
                                                });

                                                return promise;
                                            };

                                            $scope.close = function () {
                                                $modalInstance.dismiss('close');
                                            };
                                        }
                                    });

                                },
                                accordions: {
                                    closeOthers: true,
                                    groups: [{
                                        label: 'General',
                                        open: true,
                                        fields: ['name', 'publish_date', 'discontinue_date'],
                                    }, {
                                        label: 'Products',
                                        open: false,
                                        fields: ['_images']
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
