(function () {
    'use strict';
    angular.module('app').run(function (modelsEditor, modelsMeta, modelsConfig, $modal, modals, helpers, $q) {

        modelsConfig(function (models) {
            $.extend(models['31'], {
                formatPublicSearchResults: function (results) {
                    angular.forEach(results, function (result) {
                        result._cover = {
                            serving_url: result.cover,
                            proportion: result.cover_proportion
                        };
                        result._seller_logo = {
                            serving_url: result.seller_logo,
                            proportion: 2.4
                        };
                    });
                },
                calculatePricetagPosition: function (ihp, ivp, iiw, iih, ciw, cih) {
                    /*  
                    ihp - Initial Horizontal Price Tag Position 
                    ivp - Initial Vertical Price Tag Position 
                    iiw - Initial Image Width  
                    iih - Initial Image Height  

                    ciw - Current Image Width  
                    cih - Current Image Height  
                    chp - Current Horizontal Price Tag Position  
                    cvp - Current Vertical Price Tag Position  
                    */
                    var chp = (ihp / iiw) * ciw,
                        cvp = (ivp / iih) * cih;
                    return [chp, cvp];
                },
                previewModal: function (key, config) {
                    config = helpers.alwaysObject(config);
                    config.hideAddToCart = true;
                    return this.viewModal(key, config);
                },
                viewProductModal: function (catalogKey, imageKey, pricetagKey, variantSignatureAsDicts, config) {
                    var readArguments = {
                            _seller: {},
                            _images: {
                                config: {
                                    keys: [imageKey]
                                },
                                pricetags: {
                                    config: {
                                        keys: [pricetagKey]
                                    },
                                    _product: {
                                        _category: {}
                                    }
                                }
                            }
                        };
                    config = helpers.alwaysObject(config);
                    this.actions.read({
                        key: catalogKey,
                        read_arguments: readArguments
                    }).then(function (response) {
                        var catalog = response.data.entity,
                            makeFakeScope = function () {
                                var $scope = {};
                                $scope.product = catalog._images[0].pricetags[0]._product;
                                $scope.originalProduct = angular.copy($scope.product);
                                $scope.catalog = catalog;
                                $scope.variants = [];
                                $scope.variantSelection = [];
                                $scope.hideAddToCart = false;
                                $scope.currentVariation = [];
                                angular.forEach($scope.product.variants, function (v, i) {

                                    $scope.variants.push({
                                        name: v.name,
                                        options: v.options,
                                        option: (variantSignatureAsDicts ? variantSignatureAsDicts[i][v.name] : v.options[0]),
                                    });

                                    $scope.variantSelection.push({
                                        type: 'SuperStringProperty',
                                        choices: (v.allow_custom_value ? null : v.options),
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

                                $scope.changeVariationPromise = function () {
                                    var buildVariantSignature = [],
                                        skip = false,
                                        promise;

                                    $scope.currentVariation.splice(0, $scope.currentVariation.length);

                                    angular.forEach($scope.variants, function (v) {
                                        var d = {};
                                        if (v.option === null) {
                                            skip = true;
                                        }
                                        if (!v.allow_custom_value) {
                                            buildVariantSignature.push(v.name + ': ' + v.option);
                                            d[v.name] = v.option;
                                            $scope.currentVariation.push(d);
                                        }
                                    });

                                    if (skip) {
                                        promise = $q.defer().promise;
                                        promise.resolve();
                                        return promise;
                                    }
                                    // rpc to check the instance
                                    return models['31'].actions.read({
                                        key: this.catalog.key,
                                        // 4 rpcs
                                        read_arguments: {
                                            _images: {
                                                config: {keys: [imageKey]},
                                                pricetags: {
                                                    config: {
                                                        keys: [pricetagKey]
                                                    },
                                                    _product: {
                                                        _instances: {
                                                            config: {
                                                                search: {
                                                                    filters: [{field: 'variant_options', operator: 'ALL_IN', value: buildVariantSignature}]
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    });
                                };

                                return $scope;
                            },
                            fakeScope = makeFakeScope();
                        $modal.open({
                            resolve: {productInstanceResponse: function () {
                                return fakeScope.changeVariationPromise().then(function (response) {
                                    return response;
                                });
                            }},
                            templateUrl: 'catalog/product/modal/view.html',
                            windowClass: 'no-overflow',
                            controller: function ($scope, $modalInstance, productInstanceResponse) {
                                var loadProductInstance, sellerKey;
                                $.extend($scope, fakeScope);
                                $scope.resetVariation = function () {
                                    this.resetVariantProduct();
                                    $scope.variationApplied = false;
                                    angular.forEach($scope.variants, function (v) {
                                        v.option = null;
                                    });
                                };
                                $scope.resetVariantProduct = function () {
                                    $.extend(this.product, this.originalProduct);
                                    $scope.productInstance = null;
                                };
                                $scope.variationApplied = false;
                                $scope.viewContent = function (content) {
                                    $modal.open({
                                        templateUrl: 'entity/modal/editor.html',
                                        controller: function ($scope, $modalInstance) {
                                            $scope.config = {};
                                            $scope.config.templateBodyUrl = 'misc/modal/content_view_body.html';
                                            $scope.config.templateFooterUrl = 'misc/modal/content_view_footer.html';
                                            $scope.content = content;
                                            $scope.close = function () {
                                                $modalInstance.dismiss('close');
                                            };
                                        }
                                    });
                                };
                                $scope.canAddToCart = true;
                                $scope.productQuantity = 0;
                                sellerKey = $scope.catalog._seller.key;
                                $scope.cartProductQuantity = function () {
                                    models['34'].current(sellerKey).then(function (response) {
                                        var order = response.data.entity;
                                        if (order.id) {
                                            angular.forEach(order._lines, function (line) {
                                                if (line.product._reference.parent.id === $scope.product.parent.id
                                                        && line.product._reference.id === $scope.product.id
                                                        && JSON.stringify($scope.currentVariation) === JSON.stringify(line.product.variant_signature)) {
                                                    $scope.productQuantity = parseInt(line.product.quantity, 10);
                                                }
                                            });
                                            $scope.canAddToCart = order.ui.rule.action.update_line.executable;
                                        } else {
                                            $scope.canAddToCart = true;
                                        }

                                    });
                                };

                                loadProductInstance = function (response) {
                                    var product,
                                        productInstance,
                                        toUpdate = ['images', 'code', 'unit_price', 'weight', 'weight_uom', 'volume', 'volume_uom',
                                                         'description', 'contents', 'availability'];
                                    try {
                                        product = response.data.entity._images[0].pricetags[0]._product;
                                    } catch (ignore) { }

                                    if (product) {
                                        productInstance = product._instances[0];
                                    }
                                    if (productInstance) {
                                        $scope.productInstance = productInstance;
                                        angular.forEach(toUpdate, function (field) {
                                            var next = productInstance[field];
                                            if (next !== null && next.length) {
                                                $scope.product[field] = next;
                                            }
                                        });
                                    } else {
                                        $scope.resetVariantProduct();
                                    }

                                    $scope.variationApplied = true;
                                };

                                $scope.changeVariation = function () {
                                    // rpc to check the instance
                                    this.changeVariationPromise()
                                        .then(loadProductInstance)
                                        .then($scope.cartProductQuantity);
                                };

                                loadProductInstance(productInstanceResponse);

                                $scope.cartProductQuantity();

                                $scope.increaseQuantity = function () {
                                    $scope.productQuantity += 1;
                                };

                                $scope.decreaseQuantity = function () {
                                    if ($scope.productQuantity === 0) {
                                        return;
                                    }
                                    $scope.productQuantity -= 1;
                                };

                                $scope.addToCart = function () {
                                    models['19'].current().then(function (response) {
                                        return models['34'].actions.update_line({
                                            buyer: response.data.entity.key,
                                            product: $scope.product.key,
                                            image: imageKey,
                                            quantity: $scope.productQuantity,
                                            variant_signature: $scope.currentVariation
                                        });
                                    }).then(function (response) {
                                        if (config.events && config.events.addToCart) {
                                            config.events.addToCart.call(this, response);
                                        }
                                        if (models['34'].getCache('current' + sellerKey)) {
                                            models['34'].current(sellerKey).then(function (cached) {
                                                $.extend(cached.data.entity, response.data.entity);
                                            });
                                        }
                                    });
                                };

                                $scope.close = function () {
                                    $modalInstance.dismiss('close');
                                };
                            }
                        });
                    });
                },
                viewModal: function (key, config) {
                    var that = this;
                    that.actions.read({
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
                                $scope.catalog.action_model = '31';
                                $scope.logoImageConfig = {};
                                var imagesReader,
                                    accessImages,
                                    catalogUrl = helpers.url.abs('catalog/' + $scope.catalog.key);
                                accessImages = angular.copy($scope.catalog.ui.access);
                                accessImages.push('_images');

                                imagesReader = models['31'].reader({
                                    kind: $scope.catalog.kind,
                                    key: $scope.catalog.key,
                                    next: {_images: $scope.catalog._next_read_arguments._images},
                                    access: accessImages,
                                    complete: function (items) {
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
                                        image: $scope.catalog._images[0].serving_url + '=s600',
                                        text: 'Share on pinterest'
                                    },
                                    gplus: {
                                        url: catalogUrl
                                    }
                                };

                                $scope.loadMoreImages = function (callback) {
                                    var promise = imagesReader.load();
                                    if (promise) {
                                        promise.then(function () {
                                            callback.call(this, response, imagesReader.more);
                                        });
                                    } else {
                                        callback.call(this, undefined, imagesReader.more);
                                    }
                                };

                                $scope.displayCart = function () {
                                    models['19'].current().then(function (response) {
                                        models['34'].viewModal($scope.catalog._seller, response.data.entity, undefined, {
                                            cartMode: true
                                        });
                                    });
                                };

                                // cache current user's cart
                                models['34'].current($scope.catalog._seller.key);

                                $scope.viewProduct = function (image, pricetag) {
                                    that.viewProductModal($scope.catalog.key, image.key, pricetag.key);
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

                                                        $scope.formSetDirty();

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
                                                models['31'].actions.publish({
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
                                                models['31'].actions.discontinue({
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
                                                models['31'].actions.catalog_duplicate({
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
                                                var sudoFields = modelsMeta.getActionArguments('31', 'sudo');
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
                                                    models['31'].actions.sudo($scope.args).then(function (response) {
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
                                historyConfig: true,
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
                                            $scope.container = {};
                                            $scope.formSetPristine = function () {
                                                if ($scope.container && $scope.container.form) {
                                                    $scope.container.form.$setPristine();
                                                }
                                            };
                                            $scope.formSetDirty = function () {
                                                if ($scope.container && $scope.container.form) {
                                                    $scope.container.form.$setDirty();
                                                }
                                            };

                                            imagesReader = models['31'].reader({
                                                kind: '31',
                                                key: $scope.args.key,
                                                next: $scope.args._next_read_arguments,
                                                access: accessImages,
                                                complete: function (items) {
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

                                                $scope.formSetDirty();

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
                                                var promise = imagesReader.load();
                                                if (promise) {
                                                    promise.then(function (response) {
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
                                                models['31'].actions.read({
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
                                                                    models['31'].actions.catalog_pricetag_duplicate({
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
                                                        sortableOptions: {
                                                            stop: function () {
                                                                var field = $scope.fieldProduct.modelclass._instances, total,
                                                                    currentFieldScope = $scope.fieldProduct.ui.specifics.getScope();
                                                                if (field.ui.specifics.parentArgs.length) {
                                                                    total = field.ui.specifics.parentArgs[0].sequence;
                                                                    angular.forEach(field.ui.specifics.parentArgs,
                                                                        function (ent, i) {
                                                                            i = ((total + 1) - i);
                                                                            ent.sequence = i;
                                                                            ent.ui.access[ent.ui.access.length - 1] = i;
                                                                        });

                                                                    currentFieldScope.formSetDirty();
                                                                    currentFieldScope.$broadcast('itemOrderChanged');
                                                                }
                                                            }
                                                        },
                                                        init: function () {
                                                            var currentFieldScope = $scope.fieldProduct.ui.specifics.getScope(),
                                                                currentArgs = currentFieldScope.args,
                                                                choices = [],
                                                                variantOptions = $scope.fieldProduct.modelclass._instances.modelclass.variant_options;
                                                            if (!currentArgs.variants.length) {
                                                                modals.alert('Please create some variants first.');
                                                                return false;
                                                            }

                                                            angular.forEach(currentArgs.variants, function (variant) {
                                                                if (variant.allow_custom_value) {
                                                                    return;
                                                                }
                                                                angular.forEach(variant.options, function (variantOpt) {
                                                                    choices.push(variant.name + ': ' + variantOpt);
                                                                });
                                                            });

                                                            variantOptions.choices = choices;
                                                        },
                                                        addText: 'Add Product Instance',
                                                        listFields: [{
                                                            label: 'Variant Signature',
                                                            key: 'variant_signature'
                                                        }],
                                                        excludeFields: ['created', 'sequence']
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
                                                var promise = models['31'].actions[$scope.args.action_id]($scope.args);

                                                promise.then(function (response) {
                                                    $.extend($scope.entity, response.data.entity);
                                                    var newArgs = $scope.rootScope.config.argumentLoader($scope);
                                                    parentScope.args = angular.copy(newArgs);
                                                    $scope.args = angular.copy(newArgs);
                                                    parentScope.config.ui.specifics.reader.state(imagesReader);
                                                    $scope.formSetPristine();
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