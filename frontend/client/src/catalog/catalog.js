(function () {
    'use strict';
    angular.module('app').directive('catalogNewPricetag', function ($parse) {
        return {
            restrict: 'A',
            link: function (scope, element, attrs) {
                var callback = $parse(attrs.catalogNewPricetag);
                element.on('click', function (event) {
                    var offset = element.offset(),
                        x = event.pageX - offset.left,
                        y = event.pageY - offset.top,
                        parent = element.parents('.image-slider-item:first'),
                        width = parent.width(),
                        height = parent.height();

                    scope.$apply(function () {
                        callback(scope, {
                            config: {
                                position_left: x,
                                position_top: y,
                                image_width: width,
                                image_height: height
                            }
                        });
                    });
                });
            }
        };
    }).directive('catalogPricetagPosition', function ($timeout, models) { // directives that are not used anywhere else other than this context are defined in their own context
        return {
            link: function (scope, element, attr) {

                var pricetag = scope.$eval(attr.catalogPricetagPosition),
                    resize = function () {
                        var pa = $(element).parents('.image-slider-item:first'),
                            sizes;

                        sizes = models['31'].calculatePricetagPosition(
                            pricetag.position_top,
                            pricetag.position_left,
                            pricetag.image_width,
                            pricetag.image_height,
                            pa.width(),
                            pa.height()
                        );

                        pricetag._position_top = sizes[0];
                        pricetag._position_left = sizes[1];

                        $(element).css({
                            top: pricetag._position_top,
                            left: pricetag._position_left,
                            visibility: 'visible'
                        });
                    };
                $timeout(resize, 0, false);
                scope.$on('modalResize', resize);
                scope.$watch(attr.catalogPricetagPosition + '._state', resize);
            }
        };
    }).directive('productInstanceCardView', function ($compile) {
        return {
            scope: {
                val: '=productInstanceCardView'
            },
            templateUrl: 'catalog/product/product_instance_card_view.html',
            link: function (scope) {
                scope.showVariantLabel = function (variant) {
                    return variant.split(':')[0];
                };
                scope.showVariantValue = function (variant) {
                    var splitOpen = variant.split(':');
                    return splitOpen.slice(1, splitOpen.length).join(':');
                };
            }
        };
    }).run(function (modelsEditor, modelsMeta, modelsConfig, $modal, modals, helpers, $q, $mdSidenav, $timeout) {

        modelsConfig(function (models) {
            var setupToggleMenu = function ($scope, id) {
                $scope.sidenavMenuID = id;
                $scope.notRipplable = ['.catalog-close-button', '.catalog-pricetag', '.catalog-pricetag-link'];
                $scope.toggling = false;
                $scope.toggleMenu = function ($event) {
                    if ($scope.toggling) {
                        return;
                    }
                    var it = $mdSidenav($scope.sidenavMenuID),
                        check = false,
                        target;
                    if ($event.target) {
                        target = $($event.target);
                        angular.forEach($scope.notRipplable, function (skip) {
                            if (target.is(skip) || target.parent().is(skip)) {
                                check = true;
                            }
                        });
                        if (check) {
                            return;
                        }
                    }
                    $scope.toggling = true;
                    $timeout(function () {
                        it[it.isOpen() ? 'close' : 'open']().then(function () {
                            $scope.toggling = false;
                        });
                    });
                };
            }, recomputeRealPath = function (field1, level) {
                if (!level) {
                    level = 0;
                }
                var field2 = field1.modelclass;
                angular.forEach(field2, function (value) {
                    if (value.ui.realPath) {
                        var con = field1.ui.realPath.concat();
                        con.push(value.code_name);
                        value.ui.realPath = con;
                        value.ui.initialRealPath = con;
                        if (value.modelclass) {
                            recomputeRealPath(value, level + 1);
                        }
                    }
                });
            };
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
                            fakeScope = (function () {
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
                                            help: v.description,
                                            label: v.name,
                                            writable: true,
                                            attrs: {
                                                'ng-change': 'changeVariation()'
                                            },
                                            args: 'variants[' + i + '].option'
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
                                                config: {
                                                    keys: [imageKey]
                                                },
                                                pricetags: {
                                                    config: {
                                                        keys: [pricetagKey]
                                                    },
                                                    _product: {
                                                        _instances: {
                                                            config: {
                                                                search: {
                                                                    filters: [{
                                                                        field: 'variant_options',
                                                                        operator: 'ALL_IN',
                                                                        value: buildVariantSignature
                                                                    }]
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
                            }());
                        $modal.open({
                            resolve: {
                                productInstanceResponse: function () {
                                    return fakeScope.changeVariationPromise().then(function (response) {
                                        return response;
                                    });
                                }
                            },
                            templateUrl: 'catalog/product/view.html',
                            windowClass: 'no-overflow',
                            targetEvent: config.targetEvent,
                            transformOrigin: true,
                            controller: function ($scope, productInstanceResponse) {
                                var loadProductInstance, sellerKey;
                                $.extend($scope, fakeScope);
                                setupToggleMenu($scope, 'right_product_sidenav');
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
                                        templateUrl: 'core/models/manage.html',
                                        controller: function ($scope) {
                                            $scope.dialog = {
                                                templateBodyUrl: 'core/misc/content_view_body.html',
                                                toolbar: {
                                                    hideSave: true
                                                }
                                            };
                                            $scope.content = content;
                                            $scope.close = function () {
                                                $scope.$close();
                                            };
                                        }
                                    });
                                };
                                $scope.canAddToCart = true;
                                $scope.hasThisProduct = false;
                                $scope.disableUpdateCart = false;
                                $scope.productQuantity = 0;

                                sellerKey = $scope.catalog._seller.key;
                                $scope.cartProductQuantity = function () {
                                    $scope.productQuantity = 0;
                                    $scope.hasThisProduct = false;
                                    $scope.disableUpdateCart = false;
                                    models['34'].current(sellerKey).then(function (response) {
                                        var order = response.data.entity;
                                        if (order.id) {
                                            angular.forEach(order._lines, function (line) {
                                                if (line.product._reference.parent.id === $scope.product.parent.id
                                                        && line.product._reference.id === $scope.product.id
                                                        && angular.toJson($scope.currentVariation) === angular.toJson(line.product.variant_signature)) {
                                                    $scope.productQuantity = parseInt(line.product.quantity, 10);
                                                    if ($scope.productQuantity > 0) {
                                                        $scope.hasThisProduct = true;
                                                        $scope.disableUpdateCart = true;
                                                    }
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
                                            'description', 'contents', 'availability'
                                        ];
                                    try {
                                        product = response.data.entity._images[0].pricetags[0]._product;
                                    } catch (ignore) {}

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
                                    $scope.disableUpdateCart = false;
                                    $scope.productQuantity = parseInt($scope.productQuantity, 10) + 1;
                                };

                                $scope.decreaseQuantity = function () {
                                    if (parseInt($scope.productQuantity, 10) === 0) {
                                        return;
                                    }
                                    $scope.disableUpdateCart = false;
                                    $scope.productQuantity = parseInt($scope.productQuantity, 10) - 1;
                                };

                                $scope.addToCart = function () {
                                    if (!$scope.hasThisProduct && $scope.productQuantity < 1) {
                                        $scope.container.form.$setDirty();
                                        var productQuantityField = $scope.container.form.productQuantity;
                                        productQuantityField.$setViewValue(productQuantityField.$viewValue !== undefined ? productQuantityField.$viewValue : '');
                                        productQuantityField.$setDirty();
                                        productQuantityField.$setValidity('required', false);
                                        return;
                                    }
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

                                        if ($scope.productQuantity < 1) {
                                            $scope.hasThisProduct = false;
                                        } else {
                                            $scope.hasThisProduct = true;
                                            $scope.disableUpdateCart = true;
                                        }
                                    });
                                };

                                $scope.close = function () {
                                    $scope.$close();
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
                            modals.alert('noImagesInCatalog');
                            return;
                        }
                        $modal.open({
                            templateUrl: 'catalog/view.html',
                            windowClass: 'no-overflow',
                            targetEvent: config.targetEvent,
                            controller: function ($scope) {
                                setupToggleMenu($scope, 'right_catalog_sidenav');
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
                                    next: {
                                        _images: $scope.catalog._next_read_arguments._images
                                    },
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
                                        models['34'].manageModal(undefined, $scope.catalog._seller, response.data.entity, {
                                            cartMode: true
                                        });
                                    });
                                };

                                // cache current user's cart
                                models['34'].current($scope.catalog._seller.key);

                                $scope.viewProduct = function (image, pricetag, config) {
                                    config.targetEvent.target = $(config.targetEvent.target).parents('.catalog-pricetag:first').get(0);
                                    that.viewProductModal($scope.catalog.key, image.key, pricetag.key, null, config);
                                };

                                $scope.sellerDetails = function () {
                                    models['23'].viewModal($scope.catalog._seller);
                                };

                                $scope.close = angular.bind($scope, helpers.form.leave, function () {
                                    $scope.$close();
                                });
                            }
                        });
                    });
                },
                adminManageModal: function (catalog) {
                    return this.manageModal(catalog);
                },
                manageModal: function (catalog, callback, modalConfig) { // modal dialog for managing the catalog

                    modalConfig = helpers.alwaysObject(modalConfig);

                    var fields = modelsMeta.getActionArguments('31', 'update'),
                        isNew = !angular.isDefined(catalog),
                        afterSave = function ($scope) {
                            $scope.setAction('catalog_upload_images');
                            $scope.dialog.toolbar.templateActionsUrl = 'catalog/manage_actions.html';
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
                            modalConfig: modalConfig,
                            fields: _.toArray(fields),
                            toolbar: {
                                templateActionsUrl: (isNew ? false : 'catalog/manage_actions.html'),
                                titleEdit: 'seller.edit31',
                                titleAdd: 'seller.add31'
                            },
                            afterSave: afterSave,
                            afterSaveError: afterSave,
                            afterComplete: afterComplete,
                            afterCompleteError: afterComplete,
                            init: function ($scope) {

                                $.extend(fields._images.ui, {
                                    label: false,
                                    specifics: {
                                        addNewText: 'Select Images',
                                        sortableOptions: {
                                            stop: function () {
                                                if (fields._images.ui.specifics.parentArgs.length) {
                                                    var total = fields._images.ui.specifics.parentArgs[0].sequence,
                                                        cmp = [],
                                                        cmp2 = [],
                                                        scope = fields._images.ui.directiveScope();
                                                    angular.forEach(fields._images.ui.specifics.parentArgs,
                                                        function (ent, i) {
                                                            i = (total - i);
                                                            cmp.push(ent.sequence);
                                                            cmp2.push(i);
                                                            ent.sequence = i;
                                                            ent.ui.access[ent.ui.access.length - 1] = i;
                                                        });

                                                    if (!cmp.equals(cmp2)) {
                                                        scope.formSetDirty();
                                                    }
                                                    scope.$broadcast('itemOrderChanged');

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
                                        modals.confirm('publishCatalog',
                                            function () {
                                                models['31'].actions.publish({
                                                    key: $scope.entity.key
                                                }).then(function (response) {
                                                    modals.alert('catalogPublished');
                                                    updateState(response.data.entity);
                                                });
                                            });
                                    },
                                    discontinue: function () {
                                        modals.confirm('discontinueCatalog',
                                            function () {
                                                models['31'].actions.discontinue({
                                                    key: $scope.entity.key
                                                }).then(function (response) {
                                                    modals.alert('catalogDiscontinued');
                                                    updateState(response.data.entity);
                                                });
                                            });
                                    },
                                    duplicate: function () {
                                        modals.confirm('duplicateCatalog',
                                            function () {
                                                models['11'].channelNotifications().then(function (response) {
                                                    models['31'].actions.catalog_duplicate({
                                                        key: $scope.entity.key,
                                                        channel: response.token
                                                    }).then(function (response) {
                                                        modals.alert('duplicationInProgressCatalog');
                                                    });
                                                });
                                            });
                                    },
                                    sudo: function () {
                                        modals.models.sudo($scope.entity, {templateUrl: 'catalog/administer.html', onConfirm: updateState});
                                    }
                                };
                            },
                            noComplete: noComplete,
                            scope: {
                                historyConfig: true,
                                addProducts: function () {
                                    var parentScope = this;
                                    if (!parentScope.args.id) {
                                        modals.alert('noImagesInCatalog');
                                        return false;
                                    }
                                    $modal.open({
                                        templateUrl: 'core/models/manage.html',
                                        windowClass: 'no-overflow',
                                        controller: function ($scope, $timeout) {
                                            var accessImages = angular.copy(parentScope.args.ui.access),
                                                imagesReader,
                                                setupCurrentPricetag,
                                                getTitle;
                                            accessImages.push(fields._images.code_name);
                                            $scope.rootScope = parentScope.rootScope; // pass the rootScope
                                            $scope.config = parentScope.rootScope.config;
                                            $scope.entity = parentScope.entity;
                                            $scope.args = angular.copy(parentScope.args);
                                            $scope.dialog = {
                                                templateBodyUrl: 'catalog/manage_products.html',
                                                toolbar: {}
                                            };
                                            $scope.container = {};
                                            $scope.formSetPristine = angular.bind($scope, helpers.form.setPristine);
                                            $scope.formSetDirty = angular.bind($scope, helpers.form.setDirty);
                                            $scope.validateForm = angular.bind($scope, helpers.form.validate);

                                            $scope.args._images = [];

                                            getTitle = function () {
                                                return 'viewProducts';
                                            };

                                            $scope.config._title_.push(getTitle);
                                            $scope.$on('$destroy', function () {
                                                $scope.config._title_.remove(getTitle);
                                                fields._images._title_.remove(getTitle);
                                                fields._images.modelclass.pricetags._title_.remove(getTitle);
                                                fields._images.modelclass.pricetags.modelclass._product._title_.remove(getTitle);
                                            });

                                            fields._images._title_ = $scope.config._title_.concat();
                                            fields._images.modelclass.pricetags._title_ = fields._images._title_.concat();
                                            fields._images.modelclass.pricetags.modelclass._product._title_ = fields._images._title_.concat();

                                            $scope.dialog.toolbar.title = helpers.toolbar.buildTitle($scope.config._title_);

                                            imagesReader = models['31'].reader({
                                                kind: '31',
                                                key: $scope.args.key,
                                                next: {
                                                    _images: {}
                                                },
                                                access: accessImages,
                                                complete: function (items) {
                                                    $scope.args._images.extend(items);
                                                }
                                            });

                                            imagesReader.load();

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
                                                        exists = false,
                                                        newPricetag;

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
                                                            exists = _.findWhere(newImage.pricetags, {
                                                                key: pricetag.key
                                                            });
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
                                                                newPricetag = angular.copy(pricetag);
                                                                newPricetag._image = image;
                                                                newImage.pricetags.push(newPricetag);
                                                                pricetag._state = 'deleted';
                                                            }

                                                            if (!$scope.$$phase) {
                                                                $scope.$digest();
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

                                                if (!$scope.$$phase) {
                                                    $scope.$digest();
                                                }

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

                                            $scope.loadingManageProduct = false;

                                            $scope.manageProduct = function (image, pricetag) {
                                                if (pricetag._image) {
                                                    image = pricetag._image;
                                                }
                                                if ($scope.loadingManageProduct) {
                                                    return;
                                                }
                                                $scope.loadingManageProduct = true;
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
                                                                _product: {}
                                                            }
                                                        }
                                                    }
                                                }).then(function (response) {
                                                    var responseEntity = response.data.entity,
                                                        ii = $scope.args._images.indexOf(image),
                                                        product = responseEntity._images[0].pricetags[0]._product,
                                                        realPath = ['_images', ii, 'pricetags', image.pricetags.indexOf(pricetag), '_product'];
                                                    if (!$scope.fieldProduct.ui.specifics.toolbar) {
                                                        $scope.fieldProduct.ui.specifics.toolbar = {};
                                                    }
                                                    $scope.fieldProduct.ui.specifics.toolbar.templateActionsUrl = 'catalog/product/manage_actions.html';
                                                    pricetag._product = product;
                                                    product.ui.access = realPath; // override normalizeEntity auto generated path
                                                    $scope.fieldProduct.ui.realPath = realPath; // set same path
                                                    recomputeRealPath($scope.fieldProduct);
                                                    $scope.fieldProduct.ui.specifics.manage(product); // fire up modal dialog

                                                })['finally'](function () {
                                                    $scope.loadingManageProduct = false;
                                                });
                                            };

                                            $scope.howToDrag = function ($event) {
                                                modals.alert('howToDropPricetag');
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
                                                    };

                                                image.pricetags.push(newPricetag); // append new pricetag to image
                                                setupCurrentPricetag(image, newPricetag); // set current
                                                $scope.fieldProduct.ui.realPath = ['_images', ii, 'pricetags', image.pricetags.length - 1, '_product']; // set correct pathing for the new product
                                                recomputeRealPath($scope.fieldProduct);
                                                $scope.fieldProduct.ui.specifics.create();
                                            };

                                            $scope.fieldProduct = fields._images.modelclass.pricetags.modelclass._product;
                                            $.extend($scope.fieldProduct.ui, {
                                                init: function (field) {
                                                    field.config.ui.specifics.remove = function (product, close) {
                                                        // removing the actual product removes the pricetag actually
                                                        $scope.pricetag._state = 'deleted';
                                                        $scope.formSetDirty();
                                                        close();
                                                    };
                                                },
                                                args: 'pricetag._product',
                                                parentArgs: 'pricetag',
                                                path: ['_images', 'pricetags', '_product'],
                                                render: false,
                                                label: false,
                                                specifics: {
                                                    remoteAutoload: false,
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
                                                    templateFooterUrl: 'catalog/product/manage_footer.html',
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
                                                    duplicate: function () {
                                                        modals.confirm('duplicateCatalogPricetag',
                                                            function () {
                                                                models['11'].channelNotifications().then(function (response) {
                                                                    models['31'].actions.catalog_pricetag_duplicate({
                                                                        key: $scope.entity.key,
                                                                        channel: response.token,
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
                                                                        modals.alert('duplicationInProgressCatalogPricetag');
                                                                    });
                                                                });
                                                            });
                                                    }
                                                }
                                            });

                                            $.extend($scope.fieldProduct.modelclass.images.ui, {
                                                name: 'images'
                                            });

                                            $.extend($scope.fieldProduct.modelclass._instances.modelclass.images.ui, {
                                                name: 'images'
                                            });

                                            $.extend($scope.fieldProduct.modelclass._instances.ui, {
                                                label: 'Product Instances',
                                                path: ['_images', 'pricetags'],
                                                specifics: {
                                                    cards: true,
                                                    cardView: 'product-instance-card-view',
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
                                                            var field = $scope.fieldProduct.modelclass._instances,
                                                                total,
                                                                cmp = [],
                                                                cmp2 = [],
                                                                currentFieldScope = $scope.fieldProduct.ui.specifics.getScope();
                                                            if (field.ui.specifics.parentArgs.length) {
                                                                total = field.ui.specifics.parentArgs[0].sequence;
                                                                angular.forEach(field.ui.specifics.parentArgs,
                                                                    function (ent, i) {
                                                                        i = (total - i);
                                                                        cmp.push(ent.sequence);
                                                                        cmp2.push(i);
                                                                        ent.sequence = i;
                                                                        ent.ui.access[ent.ui.access.length - 1] = i;
                                                                    });
                                                                if (!cmp.equals(cmp2)) {
                                                                    currentFieldScope.formSetDirty();
                                                                }
                                                                currentFieldScope.$broadcast('itemOrderChanged');
                                                            }
                                                        }
                                                    },
                                                    canCreate: function () {
                                                        var currentFieldScope = $scope.fieldProduct.ui.specifics.getScope(),
                                                            currentArgs = currentFieldScope.args;
                                                        if (!currentArgs.id) {
                                                            modals.alert('saveProductFirst');
                                                            return false;
                                                        }
                                                        if (!currentArgs.variants.length) {
                                                            modals.alert('createVariantsFirst');
                                                            return false;
                                                        }
                                                        return true;
                                                    },
                                                    init: function () {
                                                        var currentFieldScope = $scope.fieldProduct.ui.specifics.getScope(),
                                                            currentArgs = currentFieldScope.args,
                                                            choices = [],
                                                            variantOptions = $scope.fieldProduct.modelclass._instances.modelclass.variant_options;

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
                                                    excludeFields: ['created', 'sequence']
                                                }
                                            });

                                            $.extend($scope.fieldProduct.modelclass.contents.ui, {
                                                specifics: {}
                                            });

                                            $.extend($scope.fieldProduct.modelclass.images.ui, {
                                                name: 'images',
                                                specifics: {}
                                            });

                                            $.extend($scope.fieldProduct.modelclass.variants.ui, {
                                                specifics: {}
                                            });

                                            $scope.save = function () {
                                                var promise;
                                                $scope.rootScope.config.prepareReadArguments($scope);
                                                promise = models['31'].actions[$scope.args.action_id]($scope.args);
                                                promise.then(function (response) {
                                                    $.extend($scope.entity, response.data.entity);
                                                    var newArgs = $scope.rootScope.config.argumentLoader($scope);
                                                    parentScope.args = angular.copy(newArgs);
                                                    $scope.args = angular.copy(newArgs);
                                                    $scope.formSetPristine();
                                                });
                                                return promise;
                                            };

                                            $scope.close = angular.bind($scope, helpers.form.leave, function () {
                                                $scope.$close();
                                            });
                                        }
                                    });

                                },
                                layouts: {
                                    groups: [{
                                        label: false,
                                        fields: ['name', 'discontinue_date'],
                                    }, {
                                        label: 'Images',
                                        include: 'core/misc/action.html',
                                        action: function () {
                                            modals.fields.remote(config.getScope(), fields._images);
                                        }
                                    }, {
                                        label: 'Products',
                                        include: 'core/misc/action.html',
                                        action: function () {
                                            config.getScope().addProducts();
                                        }
                                    }]
                                }
                            }
                        };

                    if (isNew) {
                        // get current seller
                        models['23'].current().then(function (response) {
                            modelsEditor.create(config).prepare({}, {
                                seller: response.data.entity.key
                            });
                        });

                    } else {
                        modelsEditor.create(config).read(catalog, {
                            key: catalog.key
                        });

                    }

                }
            });

        });
    });
}());
