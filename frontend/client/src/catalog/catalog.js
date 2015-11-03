(function () {
    'use strict';
    angular.module('app').run(ng(function (modelsEditor, modelsMeta, modelsConfig, currentAccount, $modal, modals, helpers, $q, GLOBAL_CONFIG, $mdSidenav, $timeout, $state, snackbar, social) {

        modelsConfig(function (models) {
            var doNotRipple = ['.catalog-close-button', '.catalog-pricetag', '.catalog-pricetag-link'],
                recomputeRealPath = function (field1, level) {
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
                        },
                        that = this,
                        deferOpen = $q.defer(),
                        openPromise = deferOpen.promise,
                        failedOpen = function () {
                            deferOpen.reject();
                        };
                    config = helpers.alwaysObject(config);
                    $modal.open({
                        templateUrl: 'catalog/product/view.html',
                        windowClass: 'no-overflow',
                        popFrom: config.popFrom,
                        noEscape: config.noEscape,
                        controller: ng(function ($scope) {

                            deferOpen.resolve();

                            $scope.$state.promise(function () {
                                return that.actions.read({
                                    key: catalogKey,
                                    read_arguments: readArguments
                                }, {
                                    disableUI: false
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
                                            $scope.hideClose = config ? config.hideClose : false;
                                            $scope.currentVariation = [];
                                            $scope.currentVariationPure = [];
                                            angular.forEach($scope.product.variants, function (v, i) {

                                                $scope.variants.push({
                                                    name: v.name,
                                                    options: v.options,
                                                    option: (variantSignatureAsDicts && variantSignatureAsDicts[i] ? variantSignatureAsDicts[i][v.name] : v.options[0]),
                                                    description: v.description,
                                                    allow_custom_value: v.allow_custom_value
                                                });

                                                $scope.variantSelection.push({
                                                    type: 'SuperStringProperty',
                                                    choices: (v.allow_custom_value ? null : v.options),
                                                    code_name: 'option_' + i,
                                                    ui: {
                                                        help: v.allow_custom_value ? v.description : undefined,
                                                        label: v.name,
                                                        writable: true,
                                                        attrs: {
                                                            'ng-change': 'delayedChangeVariation(' + (v.allow_custom_value ? 'true' : 'false') + ')'
                                                        },
                                                        args: 'variants[' + i + '].option'
                                                    }
                                                });

                                            });

                                            $scope.changeVariationPromise = function (forceSkip, disableUI) {
                                                var buildVariantSignature = [],
                                                    skip = false,
                                                    promise,
                                                    qdefer;

                                                $scope.currentVariation.empty();
                                                $scope.currentVariationPure.empty();

                                                angular.forEach($scope.variants, function (v) {
                                                    var d = {};
                                                    if (v.option === null) {
                                                        skip = true;
                                                    }
                                                    d[v.name] = v.option;
                                                    if (!v.allow_custom_value) {
                                                        buildVariantSignature.push(v.name + ': ' + v.option);
                                                        $scope.currentVariationPure.push(d);
                                                    } else if (!angular.isString(v.option) || !v.option.length) {
                                                        //return;
                                                    }
                                                    $scope.currentVariation.push(d);
                                                });

                                                if (skip || forceSkip) {
                                                    qdefer = $q.defer();
                                                    promise = qdefer.promise;
                                                    qdefer.resolve(forceSkip);
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
                                                }, {
                                                    disableUI: disableUI === undefined ? true : disableUI
                                                });
                                            };

                                            return $scope;
                                        }());

                                    return fakeScope.changeVariationPromise(undefined, false).then(function (productResponse) {
                                        return {
                                            catalog: catalog,
                                            fakeScope: fakeScope,
                                            productResponse: productResponse,
                                            response: response
                                        };
                                    });

                                }, failedOpen);
                            }, function ($scope, response) {
                                var loadProductInstance,
                                    sellerKey,
                                    shareWatch,
                                    timer,
                                    fakeScope = response.fakeScope,
                                    productInstanceResponse = response.productResponse;
                                $scope.variantMenu = {};
                                $scope.productMenu = {};
                                helpers.sideNav.setup($scope.productMenu, 'right_product_sidenav', doNotRipple);
                                helpers.sideNav.setup($scope.variantMenu, 'right_variantMenu_sidenav', doNotRipple);

                                $.extend($scope, fakeScope);

                                shareWatch = function () {
                                    if (!$scope.product) {
                                        $scope.socialMeta = {};
                                        return;
                                    }
                                    var productUrl = $state.href('catalog-product-view', {
                                            key: $scope.catalog.key,
                                            image_id: $scope.catalog._images[0].id,
                                            pricetag_id: $scope.catalog._images[0].pricetags[0].id
                                        }, {
                                            absolute: true
                                        }),
                                        image = function (size) {
                                            if ($scope.product.images && $scope.product.images.length) {
                                                return $scope.product.images[0].serving_url + '=s' + (size || '600');
                                            }
                                            return undefined;
                                        };
                                    $scope.socialMeta = {
                                        facebook: {
                                            'p[url]': productUrl,
                                            'p[images][0]': image(600),
                                            'p[title]': $scope.product.name
                                        },
                                        twitter: {
                                            url: productUrl,
                                            text: 'Product - ' + $scope.product.name
                                        },
                                        pinterest: {
                                            url: productUrl,
                                            media: image(600),
                                            description: 'Share on pinterest'
                                        },
                                        googleplus: {
                                            url: productUrl
                                        },
                                        reddit: {
                                            url: productUrl,
                                            title: $scope.product.name
                                        },
                                        linkedin: {
                                            url: productUrl,
                                            title: $scope.product.name
                                        },
                                        tumblr: {
                                            url: productUrl,
                                            name: $scope.product.name
                                        }
                                    };
                                };

                                $scope.displayShare = function () {
                                    return social.share($scope.socialMeta, false);
                                };

                                $scope.variantChooser = {};

                                $scope.setupVariantChooser = function (variant, indice) {
                                    variant.indice = indice;
                                    $scope.variantChooser = variant;
                                    $scope.variantMenu.open();
                                };

                                $scope.completeVariantChooser = function (option) {
                                    $scope.variantChooser.option = option;
                                    $scope.variantMenu.close();
                                    $scope.changeVariation();
                                };

                                $scope.resetVariation = function () {
                                    $scope.resetVariantProduct();
                                    $scope.variationApplied = false;
                                    angular.forEach($scope.variants, function (v) {
                                        v.option = null;
                                    });
                                };
                                $scope.resetVariantProduct = function () {
                                    $.extend($scope.product, $scope.originalProduct);
                                    $scope.productInstance = null;
                                };
                                $scope.variationApplied = false;
                                $scope.viewContent = function (content) {
                                    $modal.open({
                                        templateUrl: 'core/misc/content_view.html',
                                        controller: ng(function ($scope) {
                                            $scope.markDown = true;
                                            $scope.content = content;
                                        })
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
                                    if (!currentAccount._is_guest) {
                                        models['34'].current(sellerKey).then(function (response) {
                                            var order = response.data.entity;
                                            if (order.id) {
                                                angular.forEach(order._lines, function (line) {
                                                    if (line.product._reference.parent.id === $scope.product.parent.id && line.product._reference.id === $scope.product.id && angular.toJson($scope.currentVariation) === angular.toJson(line.product.variant_signature)) {
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

                                            if (!$scope.productQuantity) {
                                                $scope.productQuantity = 1;
                                            }

                                        });
                                    } else {
                                        $scope.productQuantity = 1;
                                    }
                                };

                                loadProductInstance = function (response) {
                                    if (response === true) {
                                        return response;
                                    }
                                    var product,
                                        productInstance,
                                        toUpdate = ['images', 'code', 'unit_price', 'weight', 'volume',
                                            'description', 'contents',
                                        ];
                                    try {
                                        product = response.data.entity._images[0].pricetags[0]._product;
                                    } catch (ignore) {}

                                    if (product) {
                                        productInstance = product._instances[0];
                                    }
                                    $scope.resetVariantProduct();
                                    if (productInstance) {
                                        $scope.productInstance = productInstance;
                                        angular.forEach(toUpdate, function (field) {
                                            var next = productInstance[field];
                                            if (next !== null && next.length && next !== undefined) {
                                                $scope.product[field] = next;
                                            }
                                        });
                                    }
                                    $scope.variationApplied = true;
                                };

                                $scope.delayedChangeVariation = function (forceSkip) {
                                    if (timer) {
                                        $timeout.cancel(timer);
                                    }
                                    timer = $timeout(function () {
                                        timer = null;
                                        $scope.changeVariation(forceSkip);
                                    }, 500, false);
                                };

                                $scope.changeVariation = function (forceSkip) {
                                    // rpc to check the instance
                                    $scope.changeVariationPromise(forceSkip)
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

                                $scope.changedQuantity = function () {
                                    $scope.disableUpdateCart = false;
                                };

                                $scope.getAvailability = function (isInStock) {
                                    var stock = $scope.product._stock,
                                        match = 'in stock',
                                        stop,
                                        currentVariationStr = JSON.stringify($scope.currentVariationPure);
                                    if (!stock || !stock.stocks.length) {
                                        return GLOBAL_CONFIG.fields.translateChoices['133'].availability[match];
                                    }
                                    angular.forEach(stock.stocks, function (st) {
                                        var findMatch = false;
                                        if ($scope.currentVariationPure.length) {
                                            findMatch = currentVariationStr === JSON.stringify(st.variant_signature);
                                        } else {
                                            findMatch = !st.variant_signature.length;
                                        }
                                        if (!stop && findMatch) {
                                            match = st.availability;
                                            stop = true;
                                        }
                                    });
                                    if (!stop) { // did not find any matches, try finding it manually
                                        angular.forEach(stock.stocks, function (st) {
                                            if (stop) {
                                                return;
                                            }
                                            var matching = [];
                                            angular.forEach($scope.currentVariationPure, function (part, i) {
                                                if (stop) {
                                                    return;
                                                }
                                                var partst, sig, passes;
                                                try {
                                                    sig = st.variant_signature[i];
                                                    partst = JSON.stringify(sig);
                                                    part = JSON.stringify(part);
                                                    passes = part === partst || _.values(sig)[0] === '***Any***';
                                                } catch (ignore) {
                                                    return; // exit if user did not configure the configuration properly
                                                }
                                                if (passes) {
                                                    matching.push(true);
                                                } else {
                                                    matching.push(false);
                                                }
                                            });
                                            if (!_.without(matching, true).length) { // remove all "true" values from list, if list is empty than we have a match
                                                match = st.availability;
                                                stop = true;
                                            }
                                        });
                                    }
                                    if (isInStock) {
                                        return match !== 'out of stock';
                                    }
                                    return GLOBAL_CONFIG.fields.translateChoices['133'].availability[match];
                                };

                                $scope.addToCart = function () {
                                    if (currentAccount._is_guest) {
                                        models['11'].login($state.href((config.hideCloseCatalog ? 'embed-' : '') + 'catalog-product-add-to-cart', {
                                            key: $scope.catalog.key,
                                            image_id: $scope.catalog._images[0].id,
                                            pricetag_id: $scope.catalog._images[0].pricetags[0].id,
                                            variant: helpers.url.jsonToUrlsafe($scope.currentVariation),
                                            quantity: $scope.productQuantity
                                        }));
                                        return;
                                    }
                                    if (!$scope.getAvailability(true)) {
                                        snackbar.showK('productOutOfStock');
                                        return;
                                    }
                                    if (config.autoAddToCart) {
                                        $scope.productQuantity = config.autoAddToCartQuantity;
                                    }
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
                                        }, {
                                            handleError: GLOBAL_CONFIG.backendErrorHandling.productOutOfStock
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
                                            $scope.productQuantity = 1;
                                        } else {
                                            $scope.hasThisProduct = true;
                                            $scope.disableUpdateCart = true;
                                        }

                                        snackbar.showK('cartUpdated');
                                    });
                                };

                                if (config.autoAddToCart) {
                                    $timeout(function () {
                                        $scope.addToCart();
                                        config.autoAddToCart = false;
                                    });
                                }

                                $scope.close = function () {
                                    var promise = $scope.$close();
                                    promise.then(function () {
                                        if (config.afterClose) {
                                            config.afterClose();
                                        }
                                    });
                                    return promise;
                                };


                                $scope.$watch('product.id', function (neww, old) {
                                    shareWatch();
                                });

                                $scope.$on('modalOpen', function () {
                                    deferOpen.resolve();
                                });

                            }, failedOpen);

                        })
                    }).opened['catch'](failedOpen);

                    return openPromise;
                },
                viewModal: function (key, config) {
                    var that = this;

                    $modal.open({
                        templateUrl: 'catalog/view.html',
                        windowClass: 'no-overflow',
                        popFrom: config.popFrom,
                        inDirection: config.inDirection,
                        outDirection: config.outDirection,
                        noEscape: config.noEscape,
                        controller: ng(function ($scope) {
                            $scope.$state.promise(function () {
                                return that.actions.read({
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
                                });
                            }, function ($scope, response) {
                                var entity = response.data.entity;
                                if (!entity._images.length) {
                                    snackbar.showK('noImagesInCatalog');
                                }
                                $scope.catalogMenu = {};
                                helpers.sideNav.setup($scope.catalogMenu, 'right_catalog_sidenav', doNotRipple);
                                $scope.catalog = entity;
                                $scope.catalog.action_model = '31';
                                $scope.logoImageConfig = {
                                    size: 560
                                };
                                var imagesReader,
                                    accessImages,
                                    loadProduct,
                                    catalogUrl = $state.href('catalog-view', {
                                        key: $scope.catalog.key
                                    }, {
                                        absolute: true
                                    }),
                                    embedCatalogUrl = $state.href('embed-catalog-view', {
                                        key: $scope.catalog.key
                                    }, {
                                        absolute: true
                                    });
                                accessImages = angular.copy($scope.catalog.ui.access);
                                accessImages.push('_images');

                                imagesReader = models['31'].reader({
                                    key: $scope.catalog.key,
                                    next: {
                                        _images: $scope.catalog._next_read_arguments._images
                                    },
                                    access: accessImages,
                                    complete: function (items) {
                                        $scope.catalog._images.extend(items);
                                    }
                                });

                                $scope.imagesReader = imagesReader;
                                imagesReader.showLoaderAlways = true;

                                $scope.socialMeta = {
                                    facebook: {
                                        'p[url]': catalogUrl,
                                        'p[images][0]': $scope.catalog._images[0].serving_url + '=s600',
                                        'p[title]': $scope.catalog.name
                                    },
                                    twitter: {
                                        url: catalogUrl,
                                        text: 'Catalog - ' + $scope.catalog.name
                                    },
                                    pinterest: {
                                        url: catalogUrl,
                                        media: $scope.catalog._images[0].serving_url + '=s600',
                                        description: 'Share on pinterest'
                                    },
                                    googleplus: {
                                        url: catalogUrl
                                    },
                                    reddit: {
                                        url: catalogUrl,
                                        title: $scope.catalog.name
                                    },
                                    linkedin: {
                                        url: catalogUrl,
                                        title: $scope.catalog.name
                                    },
                                    tumblr: {
                                        url: catalogUrl,
                                        name: $scope.catalog.name
                                    }
                                };

                                $scope.displayShare = function () {
                                    return social.share($scope.socialMeta, {
                                        src: embedCatalogUrl
                                    });
                                };

                                $scope.hideClose = config.hideClose;

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
                                    if (currentAccount._is_guest) {
                                        models['11'].login($state.href((config.hideClose ? 'embed-' : '') + 'catalog-order-view', {
                                            key: $scope.catalog.key
                                        }));
                                        return;
                                    }
                                    models['19'].current().then(function (response) {
                                        models['34'].manageModal(undefined, $scope.catalog._seller, response.data.entity, {
                                            cartMode: true
                                        });
                                    });
                                };

                                if (config.openCart) {
                                    $timeout(function () {
                                        $scope.displayCart();
                                    });
                                }

                                // cache current user's cart
                                if (!currentAccount._is_guest) {
                                    models['34'].current($scope.catalog._seller.key);
                                }

                                $scope.loadingProduct = false;

                                $scope.viewProduct = function (image, pricetag, $event) {
                                    var target = $event.target,
                                        theTarget = $(target).parents('.catalog-pricetag:first');
                                    if (theTarget.length) {
                                        target = theTarget.get(0);
                                    }
                                    $scope.loadingProduct = true;
                                    that.viewProductModal($scope.catalog.key, image.key, pricetag.key, config.variantSignatureAsDicts, {
                                        popFrom: target,
                                        hideClose: config.hideCloseOnProduct,
                                        hideCloseCatalog: config.hideClose,
                                        noEscapeCatalog: config.noEscape,
                                        noEscape: config.noEscapeOnProduct,
                                        autoAddToCart: config.variantSignatureAsDicts ? true : false,
                                        autoAddToCartQuantity: config.autoAddToCartQuantity,
                                        afterClose: config.afterCloseProduct
                                    })['finally'](function () {
                                        $scope.loadingProduct = false;
                                    });

                                    config.variantSignatureAsDicts = null;
                                };

                                $scope.openSellerDetails = function () {
                                    $scope.sellerDetails.menu.open();
                                };

                                $scope.maybeLoadProduct = null;

                                if (config.loadProduct) {
                                    loadProduct = function () {
                                        angular.forEach($scope.catalog._images, function (image) {
                                            if (image.id.toString() === config.loadProduct.image.toString()) {
                                                $scope.maybeLoadProduct = config.loadProduct;
                                            }
                                        });
                                        if (!$scope.maybeLoadProduct) {
                                            //return;
                                            var promise = imagesReader.load();
                                            if (promise) {
                                                promise.then(loadProduct);
                                            }
                                        }
                                    };

                                    loadProduct();
                                }

                                $scope.sellerDetails = models['23'].makeSellerDetails($scope.catalog._seller);

                                $scope.close = function () {
                                    var promise = $scope.$close();
                                    promise.then(function () {
                                        if (config.afterClose) {
                                            config.afterClose();
                                        }
                                    });
                                    return promise;
                                };
                            });
                        })
                    });
                },
                adminManageModal: function (account, extraConfig) {
                    return this.manageModal(account, undefined, extraConfig);
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
                            callback($scope.entity);
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
                                titleEdit: 'edit31',
                                titleAdd: 'add31'
                            },
                            afterSave: afterSave,
                            afterSaveError: afterSave,
                            afterComplete: afterComplete,
                            afterCompleteError: afterComplete,
                            init: function ($scope) {

                                $.extend(fields._images.ui, {
                                    label: false,
                                    specifics: {
                                        setupSortableOptions: function () {
                                            return {
                                                stop: function () {
                                                    if (fields._images.ui.specifics.parentArgs.length) {
                                                        var total = fields._images.ui.specifics.parentArgs[0].sequence,
                                                            dirty,
                                                            scope = fields._images.ui.directiveScope();
                                                        angular.forEach(fields._images.ui.specifics.parentArgs,
                                                            function (ent, i) {
                                                                i = (total - i);
                                                                if (ent.sequence !== i || ent._state === 'deleted') {
                                                                    dirty = true;
                                                                }
                                                                ent.sequence = i;
                                                                ent.ui.access[ent.ui.access.length - 1] = i;
                                                            });

                                                        if (dirty) {
                                                            scope.formSetDirty();
                                                        }
                                                        scope.$broadcast('itemOrderChanged');
                                                        scope.$apply();

                                                    }
                                                }
                                            };
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
                                                    snackbar.showK('catalogPublished');
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
                                                    snackbar.showK('catalogDiscontinued');
                                                    updateState(response.data.entity);
                                                });
                                            });
                                    },
                                    duplicate: function () {
                                        modals.confirm('duplicateCatalog',
                                            function () {
                                                models['11'].channelNotifications({
                                                    callback: function (response) {
                                                        models['31'].actions.read({
                                                            key: response.catalog_key,
                                                            read_arguments: {
                                                                cover: {}
                                                            }
                                                        }).then(function (response) {
                                                            snackbar.showK('catalogDuplicated');
                                                            callback(response.data.entity);
                                                        });
                                                    }
                                                }).then(function (response) {
                                                    models['31'].actions.catalog_duplicate({
                                                        key: $scope.entity.key,
                                                        channel: response.token
                                                    });
                                                });
                                            });
                                    },
                                    sudo: function () {
                                        modals.models.sudo($scope.entity, {
                                            templateUrl: 'catalog/administer.html',
                                            onConfirm: updateState
                                        });
                                    }
                                };
                            },
                            noComplete: noComplete,
                            scope: {
                                historyConfig: true,
                                addProducts: function () {
                                    var parentScope = this;
                                    $modal.open({
                                        templateUrl: 'core/models/manage.html',
                                        windowClass: 'no-overflow',
                                        controller: ng(function ($scope, $timeout) {
                                            var accessImages = angular.copy(parentScope.args.ui.access),
                                                imagesReader,
                                                setupCurrentPricetag,
                                                variantOptions,
                                                addNewPricetag,
                                                removePricetag,
                                                getTitle = function () {
                                                    return 'viewProducts';
                                                };
                                            accessImages.push(fields._images.code_name);
                                            $scope.rootScope = parentScope.rootScope; // pass the rootScope
                                            $scope.config = parentScope.rootScope.config;
                                            $scope.entity = parentScope.entity;
                                            $scope.args = angular.copy(parentScope.args);
                                            $scope.dialog = {
                                                templateBodyUrl: 'catalog/manage_products.html',
                                                toolbar: {
                                                    hideSave: true
                                                }
                                            };
                                            $scope.imagesLoaded = false;
                                            $scope.container = {};
                                            $scope.formSetPristine = angular.bind($scope, helpers.form.setPristine);
                                            $scope.formSetDirty = angular.bind($scope, helpers.form.setDirty);
                                            $scope.validateForm = angular.bind($scope, helpers.form.validate);
                                            $scope.fieldProduct = fields._images.modelclass.pricetags.modelclass._product;
                                            $scope.args._images = [];
                                            $scope.config._title_.push(getTitle);
                                            $scope.$on('$destroy', function () {
                                                $scope.config._title_.remove(getTitle);
                                                fields._images._title_.remove(getTitle);
                                                fields._images.modelclass.pricetags._title_.remove(getTitle);
                                                fields._images.modelclass.pricetags.modelclass._product._title_.remove(getTitle);
                                            });
                                            fields._images._title_ = $scope.config._title_.concat();
                                            fields._images.modelclass.pricetags._title_ = fields._images._title_.concat();
                                            $scope.fieldProduct._title_ = fields._images._title_.concat();
                                            $scope.dialog.toolbar.title = helpers.toolbar.buildTitle($scope.config._title_);

                                            $scope.trackPricetags = function (pricetag) {
                                                if (pricetag.key) {
                                                    return pricetag.key;
                                                }
                                                return 'new' + _.uniqueId();
                                            };

                                            imagesReader = models['31'].reader({
                                                key: $scope.args.key,
                                                next: {
                                                    _images: {}
                                                },
                                                access: accessImages,
                                                complete: function (items) {
                                                    $scope.args._images.extend(items);
                                                    $timeout(function () {
                                                        $scope.imagesLoaded = true;
                                                    }, 300);
                                                }
                                            });
                                            variantOptions = $scope.fieldProduct.modelclass._instances.modelclass.variant_options;
                                            if (!variantOptions.ui.specifics) {
                                                variantOptions.ui.specifics = {};
                                            }
                                            variantOptions.ui.specifics.checkboxes = true;
                                            variantOptions.ui.fieldset = true;
                                            if (!variantOptions.ui.specifics) {
                                                variantOptions.ui.specifics = {};
                                            }
                                            variantOptions.ui.specifics.listView = function (item) {
                                                return angular.isObject(item) ? item.full : item;
                                            };
                                            variantOptions.ui.specifics.grouping = function (items) {
                                                var list = [],
                                                    map = {};
                                                angular.forEach(items, function (value) {
                                                    var split = value.split(': '),
                                                        obj = map[split[0]];
                                                    if (!obj) {
                                                        obj = {
                                                            label: split[0],
                                                            items: []
                                                        };
                                                        map[split[0]] = obj;
                                                        list.push(obj);
                                                    }

                                                    obj.items.push({
                                                        name: split[1],
                                                        key: value,
                                                        full: value
                                                    });
                                                });
                                                return list;
                                            };

                                            addNewPricetag = function (image, pricetag) {
                                                image.pricetags.push(pricetag);
                                                var existing = _.findWhere($scope.rootScope.args._images, {
                                                    key: image.key
                                                });
                                                if (!existing) {
                                                    return;
                                                }
                                                existing.pricetags.push(pricetag);
                                            };

                                            removePricetag = function (image, pricetag) {
                                                if (angular.isDefined(pricetag._destroy)) {
                                                    pricetag._destroy();
                                                }
                                                image.pricetags.remove(pricetag);
                                                var existing = _.findWhere($scope.rootScope.args._images, {
                                                    key: image.key
                                                });
                                                if (!existing) {
                                                    return;
                                                }
                                                existing.pricetags.iremove(function (ipricetag) {
                                                    return ipricetag.key === pricetag.key;
                                                });
                                            };

                                            imagesReader.load();

                                            $scope.onStart = function (event, ui, image, pricetag) {
                                                $(ui.helper).addClass('dragged');
                                                $(ui.helper).find('a').addClass('dragged');
                                                if (angular.isUndefined(pricetag._image)) {
                                                    pricetag._image = $scope.args._images.indexOf(image);
                                                }
                                                $scope.syncStop();
                                            };

                                            $scope.onDrag = function (event, ui, image, pricetag) {};

                                            $scope.droppableOptions = {
                                                accept: '.catalog-new-pricetag',
                                                tolerance: 'pointer'
                                            };

                                            $scope.draggableOptions = {
                                                containment: '.image-slider-outer',
                                                distance: 10
                                            };

                                            $scope.onStop = function (event, ui, image, pricetag) {
                                                setTimeout(function () {
                                                    $(ui.helper).removeClass('dragged');
                                                    $(ui.helper).find('a').removeClass('dragged');
                                                }, 350);
                                                if (pricetag._state === 'deleted') {
                                                    return;
                                                }

                                                var target = $(event.target).parents('.image-slider-item:first'),
                                                    pricetagElement = $(event.target),
                                                    left = parseFloat(pricetagElement.css('left'), 10),
                                                    width = pricetagElement.width(),
                                                    targetWidth = target.width(),
                                                    tolerance = targetWidth - (width + left),
                                                    i = $scope.args._images.indexOf(image),
                                                    cwidth = 0,
                                                    pwidth = 0,
                                                    next,
                                                    extract;
                                                extract = function (what) {
                                                    var newImage,
                                                        exists,
                                                        newParent,
                                                        newPricetag,
                                                        newPositionLeft,
                                                        ocw = 0,
                                                        currentTop = parseFloat($(ui.helper).css('top'), 10);
                                                    next = target;
                                                    cwidth = what ? targetWidth : 0;
                                                    while (true) {
                                                        if (what) {
                                                            i += 1;
                                                            next = next.next();
                                                            cwidth += next.width();
                                                            if (cwidth > left) {
                                                                newParent = next;
                                                                newImage = $scope.args._images[i];
                                                                newPositionLeft = left - (pwidth || targetWidth);
                                                                break;
                                                            }
                                                            if (i > 10000) {
                                                                break;
                                                            }

                                                            pwidth = cwidth;
                                                        } else {
                                                            i -= 1;
                                                            next = next.prev();
                                                            ocw += next.width();
                                                            cwidth -= next.width();
                                                            if (cwidth < left) {
                                                                newParent = next;
                                                                newImage = $scope.args._images[i];
                                                                newPositionLeft = ocw + left;
                                                                break;
                                                            }
                                                            if (i < 0) {
                                                                break;
                                                            }
                                                        }
                                                    }
                                                    if (newImage) {
                                                        pricetag._state = 'deleted';
                                                        pricetagElement.addClass('ng-hide');
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
                                                        if (angular.isUndefined(exists)) {
                                                            newPricetag = angular.copy(pricetag);
                                                            newPricetag._state = null;
                                                            newPricetag._must_save = true;
                                                            if (angular.isUndefined(pricetag._image)) {
                                                                newPricetag._image = i;
                                                            }
                                                            addNewPricetag(newImage, newPricetag);
                                                        } else {
                                                            exists._state = null;
                                                        }
                                                    }
                                                };

                                                pricetag.position_top = ui.position.top;
                                                pricetag.position_left = ui.position.left;
                                                pricetag.image_width = target.width();
                                                pricetag.image_height = target.height();
                                                pricetag._position_top = pricetag.position_top;
                                                pricetag._position_left = pricetag.position_left;

                                                $scope.formSetDirty();

                                                if ((tolerance + width) < 3.3) {
                                                    //console.log('must go to next image');
                                                    extract(true);
                                                } else if (left < -8.5) {
                                                    //console.log('must go to the previous image');
                                                    extract();
                                                } else {
                                                    //console.log('stays');
                                                }

                                                if (!$scope.$$phase) {
                                                    $scope.$apply();
                                                }
                                                $scope.$broadcast('resizePricetags', pricetag);

                                                //$scope.syncStart();

                                            };

                                            $scope.onDrop = function (event, ui, image) {
                                                var target_drop = $(event.target),
                                                    posi = target_drop.offset(),
                                                    posi2 = ui.offset,
                                                    rtop = posi2.top - posi.top + 6,
                                                    rleft = posi2.left - posi.left + 4,
                                                    vdom = $('<div style="visibility:hidden;"></div>'),
                                                    newPricetagConfig = {
                                                        position_top: rtop,
                                                        position_left: rleft,
                                                        _image: $scope.args._images.indexOf(image),
                                                        image_width: target_drop.width(),
                                                        image_height: target_drop.height()
                                                    };
                                                vdom.css({
                                                    top: rtop,
                                                    position: 'absolute',
                                                    left: rleft,
                                                    width: ui.draggable.width(),
                                                    height: ui.draggable.height()
                                                });
                                                vdom.appendTo(target_drop);
                                                newPricetagConfig._destroy = function () {
                                                    $timeout(function () {
                                                        vdom.remove();
                                                    }, 2000, false);
                                                };
                                                $scope.createProduct(image, newPricetagConfig, vdom);
                                            };

                                            $scope.imagesReader = imagesReader;

                                            imagesReader.showLoaderAlways = true;

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
                                            $scope.manageProduct = function (image, pricetag, $event) {
                                                var syncing = ($scope.syncScheduleNext || $scope.syncLoading),
                                                    dirty = $scope.container.form.$dirty;
                                                if (syncing || dirty) {
                                                    return (syncing ? $scope.saveDefer.promise : $scope.save(true)).then(function () {
                                                        image = _.findWhere($scope.args._images, {
                                                            key: image.key
                                                        });
                                                        pricetag = _.findWhere(image.pricetags, {
                                                            key: pricetag.key
                                                        });
                                                        return $scope.realManageProduct(image, pricetag, $event);
                                                    });
                                                }
                                                return $scope.realManageProduct(image, pricetag, $event);
                                            };

                                            $scope.realManageProduct = function (image, pricetag, $event) {
                                                if ($scope.loadingManageProduct) {
                                                    return;
                                                }
                                                $scope.loadingManageProduct = true;
                                                setupCurrentPricetag(image, pricetag);
                                                // perform read catalog.images.0.pricetags.0._product
                                                var open = function () {
                                                    return models['31'].actions.read({
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
                                                            shouldAppearDropdown = false,
                                                            oldPricetagIndex = _.findIndex(image.pricetags, function (ipricetag) {
                                                                return ipricetag.key === pricetag.key;
                                                            }),
                                                            realPath = ['_images', ii, 'pricetags', oldPricetagIndex, '_product'];
                                                        if (!$scope.fieldProduct.ui.specifics.toolbar) {
                                                            $scope.fieldProduct.ui.specifics.toolbar = {};
                                                        }
                                                        shouldAppearDropdown = $scope.entity.ui.rule.action.catalog_pricetag_duplicate.executable || $scope.entity.ui.rule.field._images.pricetags.writable;
                                                        $scope.fieldProduct.ui.specifics.toolbar.templateActionsUrl = (shouldAppearDropdown ? 'catalog/product/manage_actions.html' : undefined);
                                                        pricetag._product = product;
                                                        if (!product._stock) {
                                                            product._stock = {
                                                                stocks: []
                                                            };
                                                        }
                                                        product.ui.access = realPath; // override normalizeEntity auto generated path
                                                        $scope.fieldProduct.ui.realPath = realPath; // set same path
                                                        recomputeRealPath($scope.fieldProduct);
                                                        return {
                                                            arg: product,
                                                            defaultArgs: undefined,
                                                            modalSettings: $event
                                                        };

                                                    })['finally'](function () {
                                                        $scope.loadingManageProduct = false;
                                                    });
                                                };

                                                $scope.fieldProduct.ui.specifics.manage(open, undefined, $event);
                                            };

                                            $scope.howToDrag = function ($event) {
                                                modals.alert('howToDropPricetag');
                                            };

                                            $scope.createProduct = function (image, config, target) {
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
                                                        _destroy: config._destroy,
                                                        _product: {
                                                            _stock: {
                                                                stocks: []
                                                            }
                                                        },
                                                        ui: {
                                                            access: ['_images', ii, 'pricetags', image.pricetags.length]
                                                        }
                                                    };
                                                addNewPricetag(image, newPricetag); // append new pricetag to image
                                                setupCurrentPricetag(image, newPricetag); // set current
                                                $scope.fieldProduct.ui.specifics.toolbar.templateActionsUrl = false;
                                                $scope.fieldProduct.ui.realPath = ['_images', ii, 'pricetags', image.pricetags.length - 1, '_product']; // set correct pathing for the new product
                                                recomputeRealPath($scope.fieldProduct);
                                                $scope.fieldProduct.ui.specifics.create(undefined, newPricetag._product, {
                                                    target: target
                                                });
                                            };

                                            $.extend($scope.fieldProduct.ui, {
                                                args: 'pricetag._product',
                                                parentArgs: 'pricetag',
                                                path: ['_images', 'pricetags', '_product'],
                                                render: false,
                                                label: false,
                                                specifics: {
                                                    remoteAutoload: false,
                                                    modal: true,
                                                    removeConfirm: function (arg, close) {
                                                        modals.confirm('removePricetagConfirm', function () {
                                                            $scope.pricetag._state = 'deleted';
                                                            $timeout(function () {
                                                                close().then(function () {
                                                                    $scope.save();
                                                                });
                                                            });
                                                        });
                                                    },
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
                                                            removePricetag($scope.image, $scope.pricetag); // remove the pricetag if we did not commit the product
                                                        }
                                                    },
                                                    afterSave: function (fieldScope) {
                                                        // after save hook
                                                        fieldScope.setAction('product_upload_images');
                                                        var updatedPricetag = fieldScope.response.data.entity._images[0].pricetags[0];
                                                        $scope.fieldProduct.ui.specifics.toolbar.templateActionsUrl = 'catalog/product/manage_actions.html';
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
                                                                models['11'].channelNotifications({
                                                                    callback: function (response) {
                                                                        models['31'].actions.read({
                                                                            key: response.catalog_key,
                                                                            read_arguments: {
                                                                                _images: {
                                                                                    config: {
                                                                                        keys: [response.image_key]
                                                                                    },
                                                                                    pricetags: {
                                                                                        config: {
                                                                                            keys: [response.pricetag_key]
                                                                                        }
                                                                                    }
                                                                                }
                                                                            }
                                                                        }).then(function (response2) {

                                                                            var image = _.findWhere($scope.args._images, {
                                                                                key: response.image_key
                                                                            });
                                                                            if (image) {
                                                                                angular.forEach(response2.data.entity._images[0].pricetags, function (value, key) {
                                                                                    if (!_.findWhere(image.pricetags, {
                                                                                            key: response.pricetag_key
                                                                                        })) {
                                                                                        image.pricetags.push(value);
                                                                                    }
                                                                                });
                                                                            }
                                                                            snackbar.showK('productDuplicated');
                                                                        });
                                                                    }
                                                                }).then(function (response) {
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

                                            $scope.fieldProduct.modelclass.category.ui.specifics = {
                                                search: {
                                                    enabled: true
                                                }
                                            };

                                            $.extend($scope.fieldProduct.modelclass._stock.ui, {
                                                specifics: {
                                                    canOpen: function () {
                                                        var currentFieldScope = $scope.fieldProduct.ui.specifics.getScope(),
                                                            currentArgs = currentFieldScope.args;
                                                        if (!currentArgs.id) {
                                                            snackbar.showK('saveProductFirst');
                                                            return false;
                                                        }
                                                        return true;
                                                    }
                                                }
                                            });


                                            $.extend($scope.fieldProduct.modelclass._stock.modelclass.stocks.ui, {
                                                specifics: {
                                                    cards: true,
                                                    cardView: 'product-stock-configuration-card-view',
                                                    init: function (fieldScope) {
                                                        var variants = $scope.fieldProduct.ui.specifics.getScope().args.variants,
                                                            availability = fieldScope.formBuilder[0].pop(),
                                                            swichables = [],
                                                            save,
                                                            i1 = 0;
                                                        fieldScope.formBuilder[0].empty();
                                                        fieldScope.variantCombination = {};
                                                        angular.forEach(variants, function (value) {
                                                            if (value.allow_custom_value) {
                                                                return;
                                                            }
                                                            try {
                                                                fieldScope.variantCombination[i1] = _.values(fieldScope.args.variant_signature[i1])[0];
                                                            } catch (ignore) {}
                                                            var computeWritable = (function () {
                                                                    var t = [];
                                                                    angular.forEach(fieldScope.args.ui.access, function (value, key) {
                                                                        if (!angular.isNumber(value)) {
                                                                            t.push("['" + value + "']");
                                                                        }
                                                                    });
                                                                    return t.join('');
                                                                }()),
                                                                field = {
                                                                    type: 'SuperStringProperty',
                                                                    choices: (function () {
                                                                        var list = value.options.concat(),
                                                                            values = [{
                                                                                key: '***Any***',
                                                                                name: 'Any'
                                                                            }];
                                                                        angular.forEach(list, function (v) {
                                                                            values.push({
                                                                                key: v,
                                                                                name: v
                                                                            });
                                                                        });
                                                                        return values;
                                                                    }()),
                                                                    code_name: 'variant_choice_' + i1,
                                                                    required: true,
                                                                    ui: {
                                                                        writable: 'entity.ui.rule.field' + computeWritable + '.variant_signature.writable',
                                                                        label: value.name,
                                                                        help: value.description,
                                                                        args: 'variantCombination[' + i1 + ']',
                                                                        attrs: {
                                                                            'ng-change': 'changeVariantCommit()'
                                                                        }
                                                                    }
                                                                };
                                                            swichables.push(field);
                                                            fieldScope.formBuilder[0].push(field);
                                                            i1 += 1;
                                                        });
                                                        fieldScope.formBuilder[0].push(availability);
                                                        fieldScope.changeVariantCommit = function () {
                                                            var i2 = 0;
                                                            angular.forEach(variants, function (value) {
                                                                if (value.allow_custom_value) {
                                                                    return;
                                                                }
                                                                var d = {};
                                                                d[value.name] = fieldScope.variantCombination[i2];
                                                                if (angular.isDefined(fieldScope.args.variant_signature[i2])) {
                                                                    fieldScope.args.variant_signature[i2] = d;
                                                                } else {
                                                                    fieldScope.args.variant_signature.push(d);
                                                                }
                                                                i2 += 1;
                                                            });
                                                        };

                                                        save = fieldScope.save;

                                                        fieldScope.save = function () {
                                                            var match,
                                                                matchStr = JSON.stringify(fieldScope.args.variant_signature);
                                                            angular.forEach(fieldScope.parentArgs, function (value, key) {
                                                                if (JSON.stringify(value.variant_signature) === matchStr) {
                                                                    match = value;
                                                                }
                                                            });
                                                            if (match) {
                                                                $.extend(match, fieldScope.args);
                                                                fieldScope.isNew = false;
                                                                fieldScope.liveArg = match;
                                                            }
                                                            return save();
                                                        };
                                                    }
                                                }
                                            });



                                            $.extend($scope.fieldProduct.modelclass._instances.ui, {
                                                label: GLOBAL_CONFIG.subheaders.productInstances,
                                                path: ['_images', 'pricetags'],
                                                specifics: {
                                                    layoutConfig: [{
                                                        label: GLOBAL_CONFIG.fields.label['28'].variant_options,
                                                        fields: ["variant_options"]
                                                    }, {
                                                        label: 'Details',
                                                        fields: ["code", "description", "unit_price", "weight", "volume"]
                                                    }, {
                                                        fields: ["images"]
                                                    }, {
                                                        fields: ["contents"]
                                                    }],
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
                                                    setupSortableOptions: function () {
                                                        return {
                                                            forcePlaceholderSize: true,
                                                            stop: function () {
                                                                var field = $scope.fieldProduct.modelclass._instances,
                                                                    total,
                                                                    dirty,
                                                                    scope = field.ui.directiveScope();
                                                                if (field.ui.specifics.parentArgs.length) {
                                                                    total = field.ui.specifics.parentArgs[0].sequence;
                                                                    angular.forEach(field.ui.specifics.parentArgs,
                                                                        function (ent, i) {
                                                                            i = (total - i);
                                                                            if (ent.sequence !== i || ent._state === 'deleted') {
                                                                                dirty = true;
                                                                            }
                                                                            ent.sequence = i;
                                                                            ent.ui.access[ent.ui.access.length - 1] = i;
                                                                        });
                                                                    if (dirty) {
                                                                        scope.formSetDirty();
                                                                    }
                                                                    scope.$broadcast('itemOrderChanged');
                                                                    scope.$apply();
                                                                }
                                                            }
                                                        };
                                                    },
                                                    canOpen: function () {
                                                        var currentFieldScope = $scope.fieldProduct.ui.specifics.getScope(),
                                                            currentArgs = currentFieldScope.args;
                                                        if (!currentArgs.id) {
                                                            snackbar.showK('saveProductFirst');
                                                            return false;
                                                        }
                                                        if (!currentArgs.variants.length) {
                                                            snackbar.showK('createVariantsFirst');
                                                            return false;
                                                        }
                                                        return true;
                                                    },
                                                    init: function () {
                                                        var currentFieldScope = $scope.fieldProduct.ui.specifics.getScope(),
                                                            currentArgs = currentFieldScope.args,
                                                            choices = [];

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


                                            if (!$scope.fieldProduct.modelclass.uom.ui.specifics) {
                                                $scope.fieldProduct.modelclass.uom.ui.specifics = {};
                                            }

                                            $scope.fieldProduct.modelclass.uom.ui.specifics.grouping = function (items) {
                                                var grouped = [],
                                                    current;
                                                angular.forEach(items, function (item) {
                                                    if (current && current.label !== item.measurement) {
                                                        current = null;
                                                    }
                                                    if (!current) {
                                                        current = {
                                                            label: item.measurement,
                                                            items: []
                                                        };
                                                        grouped.push(current);
                                                    }

                                                    current.items.push(item);
                                                });

                                                return grouped;
                                            };

                                            $scope.loadingSave = false;
                                            $scope.saveDefer = $q.defer();

                                            $scope.save = function (hideSnackbar) {
                                                var promise;
                                                $scope.loadingSave = true;
                                                $scope.rootScope.config.prepareReadArguments($scope);
                                                promise = models['31'].actions[$scope.args.action_id]($scope.args);
                                                promise.then(function (response) {
                                                    if (!$scope.syncScheduleNext) {
                                                        $.extend($scope.entity, response.data.entity);
                                                        var newArgs = $scope.rootScope.config.argumentLoader($scope);
                                                        $.extend(parentScope.args, angular.copy(newArgs));
                                                        $.extend($scope.args, angular.copy(newArgs));
                                                        $scope.formSetPristine();
                                                        if ($scope.saveDefer) {
                                                            $scope.saveDefer.resolve();
                                                        }
                                                        $scope.saveDefer = $q.defer();
                                                    }
                                                    if (!hideSnackbar) {
                                                        snackbar.showK('changesSaved');
                                                    }
                                                });
                                                promise['finally'](function () {
                                                    $scope.loadingSave = false;
                                                });
                                                return promise;
                                            };

                                            $scope.close = function () {
                                                if ($scope.container.form.$dirty) {
                                                    $scope.syncStop();
                                                    $scope.save();
                                                }
                                                return $scope.$close();
                                            };
                                            $scope.syncLoading = false;
                                            $scope.syncID = null;
                                            $scope.syncScheduleNext = false;
                                            $scope.syncStop = function () {
                                                clearTimeout($scope.syncID);
                                            };
                                            $scope.syncStart = function (hideSnackbar) {
                                                $scope.syncScheduleNext = true;
                                                $scope.syncStop();
                                                $scope.syncID = setTimeout(function () {
                                                    $scope.sync();
                                                }, 1000);
                                            };
                                            $scope.sync = function (hideSnackbar) {
                                                if ($scope.syncLoading) {
                                                    $scope.syncScheduleNext = true;
                                                    return;
                                                }
                                                $scope.syncLoading = true;
                                                $scope.syncScheduleNext = false;
                                                $scope.save(hideSnackbar).then(function (response) {
                                                    $scope.syncLoading = false;
                                                    if ($scope.syncScheduleNext) {
                                                        $scope.sync(hideSnackbar);
                                                    }
                                                    return response;
                                                });
                                            };
                                        })
                                    });

                                },
                                layouts: {
                                    groups: [{
                                        label: false,
                                        fields: ['name', 'discontinue_date'],
                                    }, {
                                        label: GLOBAL_CONFIG.subheaders.catalogImages,
                                        include: 'core/misc/action.html',
                                        action: function () {
                                            var scope = config.getScope();
                                            helpers.form.wakeUp(scope.container.form);
                                            if (!scope.container.form.$valid) {
                                                snackbar.showK('provideProperValues');
                                                return;
                                            }
                                            modals.fields.remote(config.getScope(), fields._images);
                                        }
                                    }, {
                                        label: GLOBAL_CONFIG.subheaders.catalogProducts,
                                        include: 'core/misc/action.html',
                                        action: function () {
                                            var scope = config.getScope();

                                            if (!scope.entity.cover) {
                                                snackbar.showK('uploadImagesFirst');
                                                return;
                                            }
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
                            }, {
                                handleError: GLOBAL_CONFIG.backendErrorHandling.sellerProfileNotFound
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
    }));
}());
