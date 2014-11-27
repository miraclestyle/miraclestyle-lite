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
                                                fieldProductsAfterSave;
                                            accessImages.push(fields._images.code_name);

                                            $scope.rootScope = parentScope.rootScope; // pass the rootScope
                                            $scope.entity = parentScope.entity;
                                            $scope.args = angular.copy(parentScope.args);
                                            $scope.config = $scope.rootScope.config;
                                            $scope.args._products = [];

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
                                                        console.log('moving left');

                                                    } else if (left === 0 && !moveLeft) {
                                                        // go to right
                                                        index += 1;
                                                        pass = true;
                                                        newParent = nextParent;
                                                        newPositionLeft = 5;
                                                        console.log('moving right');
                                                    }


                                                    console.log(left, currentLeft, index);

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
                                                            console.log('moving ', pricetag);

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

                                            fieldProductsAfterSave = function ($scope) {
                                                $scope.setAction('product_upload_images');
                                            };

                                            $scope.manageProduct = function (image, pricetag) {
                                                $scope.fieldProducts.ui.specifics.pricetag = pricetag;
                                                $scope.fieldProducts.ui.specifics.afterSave = function (fieldProductsScope) {
                                                    fieldProductsAfterSave(fieldProductsScope);
                                                    if (pricetag) {
                                                        pricetag.value = {
                                                            value: fieldProductsScope.args.unit_price,
                                                            name: fieldProductsScope.args.name
                                                        };
                                                        $scope.save();
                                                    }
                                                };
                                                models[config.kind].actions.read({
                                                    key: $scope.entity.key,
                                                    read_arguments: {
                                                        _products: {
                                                            config: {
                                                                keys: [pricetag.product]
                                                            }
                                                        }
                                                    }
                                                }).then(function (response) {
                                                    $scope.fieldProducts.ui.specifics.manage(response.data.entity._products[0]);
                                                });
                                            };

                                            $scope.createProduct = function (image, config) {
                                                $scope.fieldProducts.ui.specifics.afterSave = function (fieldProductsScope) {
                                                    fieldProductsAfterSave(fieldProductsScope);
                                                    var pricetag = _.findWhere(image.pricetags, {product: fieldProductsScope.args.key});
                                                    console.log(pricetag);
                                                    if (!pricetag) {
                                                        image.pricetags.push({
                                                            image_height: config.image_height,
                                                            image_width: config.image_width,
                                                            position_left: config.position_left,
                                                            position_top: config.position_top,
                                                            _position_left: config.position_left,
                                                            _position_top: config.position_top,
                                                            product: fieldProductsScope.args.key,
                                                            value: {
                                                                value: fieldProductsScope.args.unit_price,
                                                                name: fieldProductsScope.args.name
                                                            }
                                                        });

                                                    } else {
                                                        pricetag.value = {
                                                            value: fieldProductsScope.args.unit_price,
                                                            name: fieldProductsScope.args.name
                                                        };
                                                    }

                                                    $scope.save();
                                                };

                                                $scope.fieldProducts.ui.specifics.create();
                                            };

                                            $scope.fieldProducts = fields._products;
                                            $.extend($scope.fieldProducts, {
                                                ui: {
                                                    render: false,
                                                    label: false,
                                                    specifics: {
                                                        templateFooterUrl: 'catalog/products_modal_footer.html',
                                                        addText: 'Add Product',
                                                        getRootArgs: function () {
                                                            return angular.copy($scope.args);
                                                        },
                                                        afterSave: fieldProductsAfterSave,
                                                        afterComplete: function ($scope) {
                                                            $scope.setAction('update');
                                                        },
                                                        noComplete: function ($scope) {
                                                            $scope.setAction('update');
                                                        },
                                                        remove: function (product, close) {
                                                            product._state = 'deleted';
                                                            $scope.args._products.push(product);
                                                            this.pricetag._state = 'deleted';
                                                            close();
                                                        }
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
