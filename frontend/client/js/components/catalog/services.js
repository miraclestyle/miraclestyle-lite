(function () {
    'use strict';
    angular.module('app').run(function (modelsEditor, modelsMeta, modelsConfig, $modal, modals, helpers) {

        var catalogKind = '31';

        modelsConfig(function (models) {
            $.extend(models[catalogKind], {
                previewModal: function (key, config) {
                    config = helpers.alwaysObject(config);
                    config.hideAddToCart = true;
                    return this.viewModal(key, config);
                },
                viewModal: function (key, config) {
                    models[catalogKind].actions.read({
                        key: key,
                        // 5 rpcs
                        read_arguments: {
                            _seller: {
                                _content: {},
                                _feedback: {}
                            },
                            _images: {
                                pricetags: {}
                            }
                        }
                    }).then(function (response) {
                        var entity = response.data.entity;
                        if (!entity._images.length) {
                            modals.alert('Catalog has no images, add some in order to view it');
                            return;
                        }
                        $modal.open({
                            templateUrl: 'catalog/modal/view.html',
                            windowClass: 'no-overflow',
                            controller: function ($scope, $modalInstance) {
                                $scope.catalog = entity;
                                $scope.catalog.action_model = catalogKind;
                                $scope.logoImageConfig = {};
                                var imagesReader,
                                    accessImages,
                                    catalogUrl = helpers.url.abs('catalog/' + $scope.catalog.key);
                                accessImages = angular.copy($scope.catalog.ui.access);
                                accessImages.push('_images');

                                imagesReader = models[catalogKind].reader({
                                    kind: $scope.catalog.kind,
                                    key: $scope.catalog.key,
                                    next: {_images: $scope.catalog._next_read_arguments._images},
                                    access: accessImages,
                                    callback: function (items) {
                                        $scope.catalog._images.extend(items);
                                    }
                                });
                                $scope.social = {
                                    fb: {
                                        url: catalogUrl
                                    },
                                    twitter: {
                                        url: catalogUrl,
                                        text: 'Check out this catalog!'
                                    },
                                    pinterest: {
                                        url: catalogUrl,
                                        image: $scope.catalog._images[0].serving_url + '=s600'
                                    },
                                    gplus: {
                                        url: catalogUrl
                                    }
                                };

                                $scope.loadMoreImages = function (callback) {
                                    if (imagesReader.more) {
                                        imagesReader.load().then(function () {
                                            callback.call(this, response, imagesReader.more);
                                        });
                                    } else {
                                        callback.call(this, undefined, imagesReader.more);
                                    }
                                };

                                $scope.viewProduct = function (image, pricetag) {
                                    var readArguments = {
                                            _images: {
                                                config: {
                                                    keys: [image.key]
                                                },
                                                pricetags: {
                                                    config: {
                                                        keys: [pricetag.key]
                                                    },
                                                    _product: {
                                                        _product_category: {}
                                                    }
                                                }
                                            }
                                        };
                                    models[catalogKind].actions.read({
                                        key: $scope.catalog.key,
                                        read_arguments: readArguments
                                    }).then(function (response) {
                                        var parentScope = $scope;
                                        $modal.open({
                                            templateUrl: 'catalog/product/modal/view.html',
                                            windowClass: 'no-overflow',
                                            controller: function ($scope, $modalInstance) {
                                                $scope.product = response.data.entity._images[0].pricetags[0]._product;
                                                $scope.originalProduct = angular.copy($scope.product);
                                                $scope.catalog = parentScope.catalog;
                                                $scope.variants = [];
                                                $scope.variantSelection = [];
                                                $scope.image = image;
                                                $scope.pricetag = pricetag;
                                                $scope.hideAddToCart = config.hideAddToCart;
                                                angular.forEach($scope.product.variants, function (v, i) {

                                                    $scope.variants.push({
                                                        name: v.name,
                                                        options: v.options,
                                                        option: null,
                                                    });

                                                    $scope.variantSelection.push({
                                                        type: 'SuperStringProperty',
                                                        choices: v.options,
                                                        code_name: 'option_' + i,
                                                        ui: {
                                                            label: v.name,
                                                            writable: true,
                                                            attrs: {
                                                                'ng-change': 'changeVariation()'
                                                            },
                                                            placeholder: 'Select option...',
                                                            args: 'variants.' + i + '.option'
                                                        }
                                                    });

                                                });

                                                $scope.resetVariation = function () {
                                                    $.extend($scope.product, $scope.originalProduct);
                                                    $scope.variationApplied = false;
                                                    angular.forEach($scope.variants, function (v) {
                                                        v.option = null;
                                                    });
                                                };

                                                $scope.variationApplied = false;

                                                $scope.changeVariation = function () {
                                                    var variantSignature = [],
                                                        productInstance,
                                                        skip = false;

                                                    angular.forEach($scope.variants, function (v) {
                                                        var d = {};
                                                        if (v.option === null) {
                                                            skip = true;
                                                        }
                                                        d[v.name] = v.option;
                                                        variantSignature.push(d);
                                                    });

                                                    if (skip) {
                                                        return;
                                                    }

                                                    // rpc to check the instance
                                                    models[catalogKind].actions.read({
                                                        key: $scope.catalog.key,
                                                        // 4 rpcs
                                                        read_arguments: {
                                                            _images: {
                                                                config: {keys: [$scope.image.key]},
                                                                pricetags: {
                                                                    config: {
                                                                        keys: [$scope.pricetag.key]
                                                                    },
                                                                    _product: {
                                                                        _instances: {
                                                                            config: {
                                                                                keys: [{
                                                                                    input: {
                                                                                        variant_signature: variantSignature
                                                                                    }
                                                                                }]
                                                                            }
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }).then(function (response) {
                                                        var product,
                                                            toUpdate = ['images', 'code', 'unit_price', 'weight', 'weight_uom', 'volume', 'volume_uom',
                                                                             'description', 'contents', 'availability'];
                                                        try {
                                                            product = response.data.entity._images[0].pricetags[0]._product;
                                                        } catch (ignore) { }

                                                        if (product) {
                                                            productInstance = product._instances[0];
                                                        }

                                                        if (productInstance) {

                                                            angular.forEach(toUpdate, function (field) {
                                                                var next = productInstance[field];
                                                                if (next !== null && next.length) {
                                                                    $scope.product[field] = next;
                                                                }
                                                            });
                                                        }

                                                        $scope.variationApplied = true;
                                                    });
                                                };

                                                $scope.close = function () {
                                                    $modalInstance.dismiss('close');
                                                };
                                            }
                                        });
                                    });
                                };

                                $scope.sellerDetails = function () {
                                    models['23'].viewModal($scope.catalog._seller);
                                };

                                $scope.close = function () {
                                    $modalInstance.close();
                                };
                            }
                        });
                    });
                },
                manageModal: function (entity, callback) { // modal dialog for managing the catalog

                    var fields = modelsMeta.getActionArguments(catalogKind, 'update'),
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
                            templateFooterUrl: 'catalog/modal/manage_footer.html',
                            afterSave: afterSave,
                            afterSaveError: afterSave,
                            afterComplete: afterComplete,
                            afterCompleteError: afterComplete,
                            init: function ($scope) {

                                $.extend(fields._images, {
                                    ui: {
                                        label: false,
                                        template: 'catalog/underscore/form/image.html',
                                        specifics: {
                                            sortableOptions: {
                                                stop: function () {
                                                    if (fields._images.ui.specifics.parentArgs.length) {
                                                        var total = fields._images.ui.specifics.parentArgs[0].sequence;
                                                        angular.forEach(fields._images.ui.specifics.parentArgs,
                                                            function (ent, i) {
                                                                i = ((total + 1) - i);
                                                                ent.sequence = i;
                                                                ent.ui.access[ent.ui.access.length - 1] = i;
                                                            });

                                                        $scope.$broadcast('itemOrderChanged');
                                                    }
                                                }
                                            }
                                        }
                                    }
                                });

                                var updateFields = ['state', 'ui.rule', 'created', 'updated'],
                                    updateState = function (newArgs) {
                                        angular.forEach(['args', 'entity'], function (p) {
                                            helpers.update($scope[p], newArgs, updateFields);
                                        });
                                    };

                                $scope.actions = {
                                    publish: function () {
                                        modals.confirm('Publish this catalog will make it not editable and visible to the public.' +
                                                       ' Are you sure you want to do this?',
                                            function () {
                                                models[catalogKind].actions.publish({
                                                    key: $scope.entity.key
                                                }).then(function (response) {
                                                    modals.alert('Catalog published. It will be public in few minutes.');
                                                    updateState(response.data.entity);
                                                });
                                            });
                                    },
                                    discontinue: function () {
                                        modals.confirm('By discontinuing this catalog you will remove it from public, and it will be delted after 40 days.' +
                                                       ' Are you sure you want to do this?',
                                            function () {
                                                models[catalogKind].actions.discontinue({
                                                    key: $scope.entity.key
                                                }).then(function (response) {
                                                    modals.alert('Catalog discontinued successfully.');
                                                    updateState(response.data.entity);
                                                });
                                            });
                                    },
                                    duplicate: function () {
                                        modals.confirm('Are you sure you want to duplicate this catalog?',
                                            function () {
                                                models[catalogKind].actions.catalog_duplicate({
                                                    key: $scope.entity.key
                                                }).then(function (response) {
                                                    modals.alert('You will be notified when the catalog is duplicated.');
                                                });
                                            });
                                    },
                                    sudo: function () {
                                        $modal.open({
                                            templateUrl: 'catalog/modal/administer.html',
                                            controller: function ($scope, $modalInstance) {
                                                var sudoFields = modelsMeta.getActionArguments(catalogKind, 'sudo');
                                                $scope.args = {key: entity.key, state: entity.state};

                                                sudoFields.state.ui.placeholder = 'Set state';
                                                sudoFields.index_state.ui.placeholder = 'Index action';
                                                sudoFields.message.ui.placeholder = 'Message for the user';
                                                sudoFields.note.ui.placeholder = 'Note for administrators';

                                                $scope.fields = [sudoFields.state, sudoFields.index_state, sudoFields.message, sudoFields.note];
                                                angular.forEach($scope.fields, function (field) {
                                                    field.ui.writable = true;
                                                });

                                                $scope.container = {};
                                                $scope.save = function () {
                                                    if (!$scope.container.form.$valid) {
                                                        return false;
                                                    }
                                                    models[catalogKind].actions.sudo($scope.args).then(function (response) {
                                                        updateState(response.data.entity);
                                                    });
                                                };
                                                $scope.close = function () {
                                                    $modalInstance.dismiss('close');
                                                };
                                            }
                                        });
                                    }
                                };
                            },
                            noComplete: noComplete,
                            scope: { // scope for this modal dialog
                                addProducts: function () {
                                    // this function is completely custom, meaning that the entire workflow defined here is for
                                    // pricetag positioning and product editing...
                                    var parentScope = this;
                                    if (!parentScope.args._images || !parentScope.args._images.length) {
                                        modals.alert('Add some images first!');
                                        return false;
                                    }
                                    $modal.open({
                                        templateUrl: 'catalog/modal/products.html',
                                        windowClass: 'no-overflow',
                                        controller: function ($scope, $modalInstance, $timeout) {
                                            var accessImages = angular.copy(parentScope.args.ui.access),
                                                imagesReader,
                                                setupCurrentPricetag;
                                            accessImages.push(fields._images.code_name);

                                            $scope.rootScope = parentScope.rootScope; // pass the rootScope
                                            $scope.entity = parentScope.entity;
                                            $scope.args = angular.copy(parentScope.args);
                                            $scope.config = $scope.rootScope.config;

                                            imagesReader = models[catalogKind].reader({
                                                kind: catalogKind,
                                                key: $scope.args.key,
                                                next: $scope.args._next_read_arguments,
                                                access: accessImages,
                                                callback: function (items) {
                                                    $scope.args._images.extend(items);
                                                }
                                            });
                                            // set next arguments from initially loaded data from root scope
                                            imagesReader.state(parentScope.config.ui.specifics.reader);

                                            $scope.onStart = function (event, ui, image, pricetag) {
                                                $(ui.helper).addClass('dragged');
                                                $(ui.helper).find('a').addClass('dragged');
                                            };

                                            $scope.onDrag = function (event, ui, image, pricetag) {
                                                var fn = function () {
                                                    var helper = $(ui.helper),
                                                        parent = helper.parents('.image-slider-item:first'),
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
                                                        pass = false,
                                                        exists = false;

                                                    if (!parent.length || !helperW) {
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
                                                            pricetag._state = 'deleted';
                                                            exists = _.findWhere(newImage.pricetags, {key: pricetag.key});
                                                            if (exists) {
                                                                pricetag = exists;
                                                            }
                                                            pricetag.image_width = newParent.width();
                                                            pricetag.image_height = newParent.height();
                                                            pricetag.position_left = newPositionLeft;
                                                            pricetag.position_top = currentTop;
                                                            pricetag._position_left = newPositionLeft;
                                                            pricetag._position_top = currentTop;
                                                            pricetag._state = null;
                                                            if (!exists) {
                                                                newImage.pricetags.push(angular.copy(pricetag));
                                                                pricetag._state = 'deleted';
                                                            }

                                                        }
                                                    }
                                                };
                                                fn();

                                            };

                                            $scope.onStop = function (event, ui, image, pricetag) {
                                                if (pricetag._state === 'deleted') {
                                                    return;
                                                }

                                                var target = $(event.target).parents('.image-slider-item:first');

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
                                                    imagesReader.load().then(function (response) {
                                                        callback.call(this, response, imagesReader.more);
                                                    });
                                                } else {
                                                    callback.call(this, undefined, imagesReader.more);
                                                }
                                            };

                                            setupCurrentPricetag = function (image, pricetag) {
                                                $scope.image = image;
                                                $scope.pricetag = pricetag;
                                            };

                                            $scope.manageProduct = function (image, pricetag) {
                                                setupCurrentPricetag(image, pricetag);
                                                // perform read catalog.images.0.pricetags.0._product
                                                models[catalogKind].actions.read({
                                                    key: $scope.entity.key,
                                                    read_arguments: {
                                                        _images: {
                                                            config: {
                                                                keys: [image.key]
                                                            },
                                                            pricetags: {
                                                                config: {
                                                                    keys: [pricetag.key],
                                                                },
                                                                _product: {
                                                                    _instances: {
                                                                        config: {}
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }).then(function (response) {
                                                    var responseEntity = response.data.entity,
                                                        ii = $scope.args._images.indexOf(image),
                                                        product = responseEntity._images[0].pricetags[0]._product,
                                                        realPath = ['_images', ii, 'pricetags', image.pricetags.indexOf(pricetag), '_product'];
                                                    product.ui.access = realPath; // override normalizeEntity auto generated path
                                                    $scope.fieldProduct.ui.realPath = realPath; // set same path
                                                    pricetag._product = product;
                                                    $scope.fieldProduct.modelclass._instances.ui.specifics.readerSettings = {
                                                        next: response.data.entity._next_read_arguments
                                                    };
                                                    $scope.fieldProduct.ui.specifics.manage(product); // fire up modal dialog

                                                });
                                            };

                                            $scope.createProduct = function (image, config) {

                                                var ii = $scope.args._images.indexOf(image),
                                                    newPricetag = {
                                                        _sequence: image.pricetags.length,
                                                        image_height: config.image_height,
                                                        image_width: config.image_width,
                                                        position_left: config.position_left,
                                                        position_top: config.position_top,
                                                        _position_left: config.position_left,
                                                        _position_top: config.position_top,
                                                        value: {},
                                                        _product: {},
                                                        ui: {
                                                            access: ['_images', ii, 'pricetags', image.pricetags.length]
                                                        }
                                                    },
                                                    realPath = ['_images', ii, 'pricetags', image.pricetags.length, '_product'];

                                                image.pricetags.push(newPricetag); // append new pricetag to image
                                                setupCurrentPricetag(image, newPricetag); // set current
                                                $scope.fieldProduct.ui.realPath = realPath; // set correct pathing for the new product
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
                                                        beforeSave: function (fieldScope) {
                                                            fieldScope.setAction('update');
                                                            // before saving entity, set the name and unit price for the pricetag.
                                                            var findPricetag = _.last(fieldScope.sendRootArgs._images[0].pricetags);
                                                            findPricetag.value = {
                                                                name: fieldScope.args.name,
                                                                price: fieldScope.args.unit_price
                                                            };
                                                        },
                                                        templateFooterUrl: 'catalog/product/modal/manage_footer.html',
                                                        addText: 'Add Product',
                                                        getRootArgs: function () {
                                                            // root args is data that gets sent with rpc
                                                            return $scope.args;
                                                        },
                                                        afterClose: function (fieldProductScope) {
                                                            // after close hook
                                                            $scope.pricetag._product = null;
                                                            if (!fieldProductScope.args.key) {
                                                                $scope.image.pricetags.remove($scope.pricetag); // remove the pricetag if we did not commit the product
                                                            }
                                                        },
                                                        afterSave: function (fieldScope) {
                                                            // after save hook
                                                            fieldScope.setAction('product_upload_images');
                                                            var updatedPricetag = fieldScope.response.data.entity._images[0].pricetags[0];
                                                            $.extend($scope.pricetag, updatedPricetag); // after save, always update the live pricetag, because there is no way that field scope can access this scope
                                                        },
                                                        afterComplete: function (fieldScope) {
                                                            // after complete hook
                                                            fieldScope.setAction('update');
                                                        },
                                                        noComplete: function (fieldScope) {
                                                            // hook for no complete event - complete event only fires if there are images to be uploaded
                                                            fieldScope.setAction('update');
                                                        },
                                                        remove: function (product, close) {
                                                            // removing the actual product removes the pricetag actually
                                                            $scope.pricetag._state = 'deleted';
                                                            close();
                                                        },
                                                        duplicate: function () {
                                                            modals.confirm('Are you sure you want to duplicate this pricetag?',
                                                                function () {
                                                                    models[catalogKind].actions.catalog_pricetag_duplicate({
                                                                        key: $scope.entity.key,
                                                                        read_arguments: {
                                                                            _images: {
                                                                                config: {
                                                                                    keys: [$scope.image.key]
                                                                                },
                                                                                pricetags: {
                                                                                    config: {
                                                                                        keys: [$scope.pricetag.key]
                                                                                    }
                                                                                }
                                                                            }
                                                                        }
                                                                    }).then(function (response) {
                                                                        modals.alert('Pricetag is getting duplicated. You will get notified by e-mail.');
                                                                    });
                                                                });
                                                        }
                                                    }
                                                }
                                            });

                                            $scope.fieldProduct.modelclass.images.ui = {
                                                formName: 'images'
                                            };

                                            $scope.fieldProduct.modelclass._instances.modelclass.images.ui = {
                                                formName: 'images'
                                            };

                                            $.extend($scope.fieldProduct.modelclass._instances, {
                                                ui: {
                                                    label: 'Product Instances',
                                                    path: ['_images', 'pricetags'],
                                                    specifics: {
                                                        showListItem: 'product-instance-display',
                                                        getRootArgs: function () {
                                                            return $scope.args;
                                                        },
                                                        beforeSave: function (fieldScope) {
                                                            fieldScope.setAction('update');
                                                        },
                                                        afterSave: function (fieldScope) {
                                                            fieldScope.setAction('product_instance_upload_images');
                                                        },
                                                        afterComplete: function (fieldScope) {
                                                            fieldScope.setAction('update');
                                                        },
                                                        noComplete: function (fieldScope) {
                                                            fieldScope.setAction('update');
                                                        },
                                                        sortable: false,
                                                        create: function () {
                                                            var that = this,
                                                                begin,
                                                                promise,
                                                                currentFieldScope = $scope.fieldProduct.ui.specifics.getScope(),
                                                                currentArgs = currentFieldScope.args,
                                                                subParentScope = $scope;

                                                            if (!currentArgs.variants.length) {
                                                                modals.alert('Please create some variants first.');
                                                                return false;
                                                            }

                                                            begin = function () {
                                                                $modal.open({
                                                                    templateUrl: 'catalog/product/modal/variant_choices.html',
                                                                    controller: function ($scope, $modalInstance) {
                                                                        $scope.variants = [];
                                                                        $scope.variantSelection = [];

                                                                        angular.forEach(currentArgs.variants, function (v, i) {

                                                                            $scope.variants.push({
                                                                                name: v.name,
                                                                                options: v.options,
                                                                                option: null,
                                                                            });

                                                                            $scope.variantSelection.push({
                                                                                type: 'SuperStringProperty',
                                                                                choices: v.options,
                                                                                code_name: 'option_' + i,
                                                                                ui: {
                                                                                    label: v.name,
                                                                                    writable: true,
                                                                                    placeholder: 'Select option...',
                                                                                    args: 'variants.' + i + '.option'
                                                                                }
                                                                            });

                                                                        });

                                                                        $scope.close = function () {
                                                                            $modalInstance.dismiss('close');
                                                                        };

                                                                        $scope.choose = function () {

                                                                            var variantSignature = [],
                                                                                productInstance;

                                                                            angular.forEach($scope.variants, function (v) {
                                                                                var d = {};
                                                                                d[v.name] = v.option;
                                                                                variantSignature.push(d);
                                                                            });

                                                                            // rpc to check the instance
                                                                            models[catalogKind].actions.read({
                                                                                key: subParentScope.entity.key,
                                                                                read_arguments: {
                                                                                    _images: {
                                                                                        config: {keys: [subParentScope.image.key]},
                                                                                        pricetags: {
                                                                                            config: {
                                                                                                keys: [subParentScope.pricetag.key]
                                                                                            },
                                                                                            _product: {
                                                                                                _instances: {
                                                                                                    config: {
                                                                                                        keys: [{
                                                                                                            input: {
                                                                                                                variant_signature: variantSignature
                                                                                                            }
                                                                                                        }]
                                                                                                    }
                                                                                                }
                                                                                            }
                                                                                        }
                                                                                    }
                                                                                }
                                                                            }).then(function (response) {
                                                                                var product;
                                                                                try {
                                                                                    product = response.data.entity._images[0].pricetags[0]._product;
                                                                                } catch (ignore) { }

                                                                                if (product) {
                                                                                    productInstance = product._instances[0];
                                                                                }
                                                                                if (!productInstance) {
                                                                                    that.manage(undefined, {variant_signature: variantSignature});
                                                                                } else {
                                                                                    that.manage(productInstance);
                                                                                }

                                                                                $scope.close();

                                                                            });

                                                                        };

                                                                    }
                                                                });

                                                            };

                                                            if (!$scope.pricetag._product.key) {
                                                                promise = currentFieldScope.save();
                                                                if (!promise) {
                                                                    modals.alert('Please save the product first');
                                                                } else {
                                                                    promise.then(function () {
                                                                        begin();
                                                                    });
                                                                }
                                                            } else {
                                                                begin();
                                                            }
                                                        },
                                                        addText: 'Add Product Instance',
                                                        listFields: [{
                                                            label: 'Variant Signature',
                                                            key: 'variant_signature'
                                                        }],
                                                        excludeFields: ['created', 'variant_signature']
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
                                                var promise = models[catalogKind].actions[$scope.args.action_id]($scope.args);

                                                promise.then(function (response) {
                                                    $.extend($scope.entity, response.data.entity);
                                                    var newArgs = $scope.rootScope.config.argumentLoader($scope);
                                                    parentScope.args = angular.copy(newArgs);
                                                    $scope.args = angular.copy(newArgs);
                                                    parentScope.config.ui.specifics.reader.state(imagesReader);
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
                                        fields: ['name', 'discontinue_date'],
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