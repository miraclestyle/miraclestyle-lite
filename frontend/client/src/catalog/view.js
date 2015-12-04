(function () {
    'use strict';
    angular.module('app').run(ng(function (modelsEditor, modelsMeta, modelsConfig, currentAccount, $modal, modals, helpers, $q, GLOBAL_CONFIG, $mdSidenav, $timeout, $state, snackbar, social) {

        modelsConfig(function (models) {
            var doNotRipple = ['.catalog-close-button', '.catalog-pricetag', '.catalog-pricetag-link'];
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

                            $scope.hideAddToCart = false;
                            $scope.hideClose = config ? config.hideClose : false;

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
                                            $scope.currentVariation = [];
                                            $scope.currentVariationPure = [];
                                            $scope.notInitialLoad = false;
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

                                                if (!buildVariantSignature.length) {
                                                    skip = true;
                                                }

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
                                    deleteOrder,
                                    fakeScope = response.fakeScope,
                                    productInstanceResponse = response.productResponse;
                                $scope.variantMenu = {};
                                $scope.productMenu = {};
                                $scope.productManager = {};
                                helpers.sideNav.setup($scope.productMenu, 'right_product_sidenav', doNotRipple);
                                helpers.sideNav.setup($scope.variantMenu, 'right_variantMenu_sidenav', doNotRipple);

                                $.extend($scope, fakeScope);

                                shareWatch = function () {
                                    if (!$scope.product) {
                                        $scope.socialMeta = {};
                                        return;
                                    }
                                    var key = (config.hideCloseCatalog ? 'embed-' : '') + 'catalog-product-' + ($scope.currentVariation.length ? 'variant-' : '') + 'view',
                                        productUrl = $state.href(key, {
                                            key: $scope.catalog.key,
                                            image_id: $scope.catalog._images[0].id,
                                            pricetag_id: $scope.catalog._images[0].pricetags[0].id,
                                            variant: helpers.url.jsonToUrlsafe($scope.currentVariation)
                                        }, {
                                            absolute: true
                                        }),
                                        image = function (size) {
                                            if ($scope.product.images && $scope.product.images.length) {
                                                return helpers.url.handleProtocol($scope.product.images[0].serving_url + '=s' + (size || '600'));
                                            }
                                            return undefined;
                                        };
                                    $scope.socialMeta = {
                                        facebook: {
                                            'u': productUrl
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

                                deleteOrder = function () {
                                    return models['34'].actions['delete']({
                                        key: $scope.order.key
                                    }).then(function (response) {
                                        var sellerCacheKey = 'current' + sellerKey,
                                            memoized = models['34'].getCache(sellerCacheKey);
                                        if (memoized) {
                                            $.extend(memoized.data.entity, response.data.entity);
                                        } else {
                                            models['34'].setCache(sellerCacheKey, response);
                                        }
                                        return response;
                                    });
                                };

                                $scope.displayShare = function () {
                                    shareWatch();
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
                                $scope.productManager.quantity = 0;
                                $scope.isInStock = false;
                                $scope.quantityIncrement = false;
                                $scope.stockText = '';

                                sellerKey = $scope.catalog._seller.key;
                                $scope.cartProductQuantity = function () {
                                    $scope.productManager.quantity = 0;
                                    $scope.hasThisProduct = false;
                                    $scope.disableUpdateCart = false;
                                    $scope.orderLineCount = 0;
                                    if (!currentAccount._is_guest) {
                                        (config.orderKey ? models['34'].actions.read({
                                            key: config.orderKey,
                                            read_arguments: {
                                                _lines: {
                                                    config: {
                                                        limit: 0
                                                    }
                                                }
                                            }
                                        }, {
                                            disableUI: false
                                        }) : models['34'].current(sellerKey, {
                                            disableUI: false
                                        })).then(function (response) {
                                            var order = response.data.entity;
                                            $scope.order = order;
                                            if (order.id) {
                                                $scope.orderLineCount = order._lines.length;
                                                angular.forEach(order._lines, function (line, iii) {
                                                    if (line.product._reference.parent.id === $scope.product.parent.id && line.product._reference.id === $scope.product.id && angular.toJson($scope.currentVariation) === angular.toJson(line.product.variant_signature)) {
                                                        $scope.productManager.quantity = parseInt(line.product.quantity, 10);
                                                        if ($scope.productManager.quantity > 0) {
                                                            $scope.hasThisProduct = true;
                                                            $scope.disableUpdateCart = true;
                                                        }
                                                    }
                                                });
                                                $scope.canAddToCart = order.ui.rule.action.update_line.executable;
                                            } else {
                                                $scope.canAddToCart = true;
                                            }

                                            $scope.isInStock = $scope.getAvailability(true);
                                            $scope.stockText = $scope.getAvailability();
                                            $scope.quantityIncrement = $scope.isInStock;

                                            if ($scope.canAddToCart && !$scope.hasThisProduct) {
                                                $scope.canAddToCart = $scope.isInStock;
                                            }

                                            if (!$scope.hasThisProduct && !$scope.canAddToCart) {
                                                $scope.disableUpdateCart = true;
                                            }

                                            if (!$scope.productManager.quantity) {
                                                $scope.productManager.quantity = 1;
                                            }

                                        });
                                    } else {
                                        $scope.productManager.quantity = 1;
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
                                    $scope.changeVariationPromise(forceSkip)
                                        .then(loadProductInstance)
                                        .then($scope.cartProductQuantity);
                                };

                                loadProductInstance(productInstanceResponse);

                                $scope.$watch(function currentAccountIsGuestWatch() {
                                    return currentAccount._is_guest;
                                }, function (neww, old) {
                                    $scope.cartProductQuantity();
                                });

                                $scope.spotQuantity = function () {
                                    if ($scope.hasThisProduct && !$scope.isInStock) {
                                        if ($scope.productManager.quantity > 0) {
                                            $scope.disableUpdateCart = true;
                                        } else {
                                            $scope.disableUpdateCart = false;
                                        }
                                    } else if (!$scope.canAddToCart) {
                                        $scope.disableUpdateCart = true;
                                    }
                                };

                                $scope.increaseQuantity = function () {
                                    $scope.disableUpdateCart = false;
                                    $scope.productManager.quantity = parseInt($scope.productManager.quantity, 10) + 1;
                                    $scope.spotQuantity();
                                };

                                $scope.decreaseQuantity = function () {
                                    if (parseInt($scope.productManager.quantity, 10) === 0) {
                                        return;
                                    }
                                    $scope.disableUpdateCart = false;
                                    $scope.productManager.quantity = parseInt($scope.productManager.quantity, 10) - 1;
                                    $scope.spotQuantity();
                                };

                                $scope.changedQuantity = function () {
                                    $scope.disableUpdateCart = false;
                                    $scope.spotQuantity();
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
                                            quantity: $scope.productManager.quantity
                                        }));
                                        return;
                                    }
                                    if (config.autoAddToCart) {
                                        $scope.productManager.quantity = config.autoAddToCartQuantity;
                                    }
                                    if (!$scope.isInStock && $scope.productManager.quantity > 0) {
                                        snackbar.showK('productOutOfStock');
                                        return;
                                    }
                                    if (!$scope.hasThisProduct && $scope.productManager.quantity < 1) {
                                        $scope.container.form.$setDirty();
                                        var productQuantityField = $scope.container.form.productQuantity;
                                        productQuantityField.$setViewValue(productQuantityField.$viewValue !== undefined ? productQuantityField.$viewValue : '');
                                        productQuantityField.$setDirty();
                                        productQuantityField.$setValidity('required', false);
                                        return;
                                    }
                                    $scope.activitySpinner.start();
                                    models['19'].current().then(function (response) {
                                        if ($scope.order && $scope.orderLineCount === 1 && $scope.productManager.quantity.toString() === '0') {
                                            return deleteOrder();
                                        }
                                        return models['34'].actions.update_line({
                                            buyer: response.data.entity.key,
                                            product: $scope.product.key,
                                            image: imageKey,
                                            quantity: $scope.productManager.quantity,
                                            variant_signature: $scope.currentVariation
                                        }, {
                                            handleError: GLOBAL_CONFIG.backendErrorHandling.productOutOfStock
                                        });
                                    }).then(function (response) {
                                        if (config.events && config.events.addToCart) {
                                            config.events.addToCart.call(this, response);
                                        }
                                        var sellerCacheKey = 'current' + sellerKey,
                                            memoized = models['34'].getCache(sellerCacheKey);
                                        if (memoized) {
                                            $.extend(memoized.data.entity, response.data.entity);
                                        } else {
                                            models['34'].setCache(sellerCacheKey, response);
                                        }

                                        if ($scope.productManager.quantity < 1) {
                                            $scope.hasThisProduct = false;
                                            $scope.productManager.quantity = 1;
                                            $scope.disableUpdateCart = !$scope.isInStock;
                                            $scope.canAddToCart = $scope.isInStock;
                                        } else {
                                            $scope.hasThisProduct = true;
                                            $scope.disableUpdateCart = true;
                                            $scope.canAddToCart = true;
                                        }

                                        $scope.orderLineCount = response.data.entity._lines.length;
                                        if ($scope.orderLineCount === 0) {
                                            deleteOrder();
                                        }

                                        snackbar.showK('cartUpdated');
                                    })['finally'](function () {
                                        $scope.activitySpinner.stop();
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

                                $scope.notInitialLoad = true;

                                $scope.$watch('product.id', function productIdWatch(neww, old) {
                                    shareWatch();
                                });

                                deferOpen.resolve();

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

                            $scope.hideClose = config.hideClose;
                            $scope.$state.promise(function () {
                                return that.actions.read({
                                    key: key,
                                    // 5 rpcs
                                    read_arguments: {
                                        _seller: {
                                            _content: {}
                                        },
                                        _images: {
                                            pricetags: {}
                                        }
                                    }
                                }, {
                                    disableUI: false,
                                    ignoreErrors: 2
                                });
                            }, function ($scope, response) {
                                $scope.close = function () {
                                    var promise = $scope.$close();
                                    promise.then(function () {
                                        if (config.afterClose) {
                                            config.afterClose();
                                        }
                                    });
                                    return promise;
                                };
                                if (response) {
                                    var errors = response.data.errors;
                                    if (errors && (errors.not_found || errors.malformed_key)) {
                                        $scope.notFound = true;
                                        return;
                                    }
                                }
                                var entity = response.data.entity;
                                if (!entity._images.length) {
                                    $scope.noImages = true;
                                    return;
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
                                    firstLoad: false,
                                    key: $scope.catalog.key,
                                    next: {
                                        _images: $scope.catalog._next_read_arguments._images
                                    },
                                    access: accessImages,
                                    complete: function (items) {
                                        $scope.catalog._images.extend(items);
                                    }
                                });
                                imagesReader.showLoaderAlways = true;

                                $scope.imagesReader = imagesReader;

                                $scope.socialMeta = {
                                    facebook: {
                                        'u': catalogUrl
                                    },
                                    twitter: {
                                        url: catalogUrl,
                                        text: 'Catalog - ' + $scope.catalog.name
                                    },
                                    pinterest: {
                                        url: catalogUrl,
                                        media: helpers.url.handleProtocol($scope.catalog._images[0].serving_url + '=s600'),
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
                                        autoAddToCart: (config.variantSignatureAsDicts && config.autoAddToCart) ? true : false,
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
                                        var pricetags = [];
                                        angular.forEach($scope.catalog._images, function (image) {
                                            if (image.id.toString() === config.loadProduct.image.toString()) {
                                                $scope.maybeLoadProduct = config.loadProduct;
                                                pricetags = image.pricetags;
                                            }
                                        });
                                        if (!$scope.maybeLoadProduct) {
                                            //return;
                                            var promise = imagesReader.load();
                                            if (promise) {
                                                promise.then(loadProduct);
                                            }
                                        } else {
                                            if (!_.findWhere(pricetags, {id: config.loadProduct.id})) {
                                                snackbar.showK('catalogProductNotFound');
                                            }
                                        }
                                    };

                                    loadProduct();
                                }

                                $scope.sellerDetails = models['23'].makeSellerDetails($scope.catalog._seller);

                            });
                        })
                    });
                }
            });

        });
    }));
}());
