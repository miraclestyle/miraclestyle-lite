(function () {
    'use strict';
    angular.module('app').run(ng(function (modelsEditor, modelsMeta, modelsConfig, errorHandling, currentAccount, $modal, modals, helpers, $q, GLOBAL_CONFIG, $mdSidenav, $timeout, $state, snackbar, social) {

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
                    function getTrack(relativePath) {
                        return helpers.track.proxyLabelToEvents(config.track, relativePath);
                    }
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
                        track,
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
                                            $scope.urlsafeCurrentVariation = [];
                                            $scope.currentVariationPure = [];
                                            $scope.notInitialLoad = false;
                                            angular.forEach($scope.product.variants, function (v, i) {

                                                $scope.variants.push({
                                                    name: v.name,
                                                    options: v.options,
                                                    option: (variantSignatureAsDicts && variantSignatureAsDicts[i] ? v.options[variantSignatureAsDicts[i]] : v.options[0]),
                                                    description: v.description,
                                                    allow_custom_value: v.allow_custom_value
                                                });

                                                $scope.variantSelection.push({
                                                    type: (v.allow_custom_value ? 'SuperTextProperty' : 'SuperStringProperty'),
                                                    choices: (v.allow_custom_value ? null : v.options),
                                                    code_name: 'option_' + i,
                                                    ui: {
                                                        help: v.allow_custom_value ? v.description : undefined,
                                                        label: v.name,
                                                        writable: true,
                                                        attrs: {
                                                            'ng-change': 'delayedChangeVariation(' + (v.allow_custom_value ? 'true' : 'false') + ')',
                                                            'ng-focus': 'getTrack().focusProductCustomVariant()'
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
                                                $scope.urlsafeCurrentVariation.empty();
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
                                                        v.option = '';
                                                    }
                                                    // custom inputs are not passed to url
                                                    $scope.urlsafeCurrentVariation.push(!v.allow_custom_value ? v.options.indexOf(v.option) : null);
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
                                    relativeProductUrl,
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
                                        buildUrl = function (a) {
                                            return $state.engineHref(key, {
                                                key: $scope.catalog.key,
                                                image_id: $scope.catalog._images[0].id,
                                                pricetag_id: $scope.catalog._images[0].pricetags[0].id,
                                                variant: helpers.url.jsonToUrlsafe($scope.urlsafeCurrentVariation)
                                            }, {
                                                absolute: a
                                            });
                                        },
                                        productUrl = buildUrl(true),
                                        image = function (size) {
                                            if ($scope.product.images && $scope.product.images.length) {
                                                return helpers.url.handleProtocol($scope.product.images[0].serving_url + '=s' + (size || '600'));
                                            }
                                            return undefined;
                                        };

                                    relativeProductUrl = buildUrl(false);
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

                                    track = getTrack(relativeProductUrl);
                                };

                                shareWatch();

                                deleteOrder = function () {
                                    return models['34'].actions['delete']({
                                        key: $scope.order.key
                                    }, {
                                        disableUI: true
                                    }).then(function (response) {
                                        var sellerCacheKey = 'current' + sellerKey,
                                            memoized = models['34'].getCache(sellerCacheKey);
                                        if (memoized) {
                                            $.extend(memoized.data.entity, response.data.entity);
                                        } else {
                                            models['34'].setCache(sellerCacheKey, response);
                                        }
                                        $scope.order = undefined;
                                        $scope.orderLineCount = 0;
                                        config.orderKey = undefined;
                                        return response;
                                    });
                                };

                                function spawnShare() {
                                    social.share($scope, $scope.socialMeta, false, undefined, {
                                        track: {
                                            openShareDrawer: track.openProductShareDrawer,
                                            closeShareDrawer: track.closeProductShareDrawer,
                                            focusShareLink: track.focusProductShareLink,
                                            focusShareEmbedCode: track.focusProductShareEmbedCode
                                        }
                                    });
                                }

                                spawnShare();

                                $scope.variantChooser = {};

                                $scope.displayShare = function () {
                                    spawnShare();
                                    $scope.share.menu.open();
                                };

                                $scope.setupVariantChooser = function (variant, indice) {
                                    variant.indice = indice;
                                    $scope.variantChooser = variant;
                                    $scope.variantMenu.open();
                                };

                                $scope.completeVariantChooser = function (option) {
                                    $scope.variantChooser.option = option;
                                    $scope.variantMenu.close();
                                    $scope.changeVariation();
                                    track.changeProductVariantOption();
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
                                            $scope.$state.instant(function () {
                                                $scope.markDown = true;
                                                $scope.content = content;
                                                track.openProductContent();

                                                $scope.close = function () {
                                                    $scope.$close();
                                                    track.closeProductContent();
                                                };
                                            });
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

                                sellerKey = config.sellerKey || $scope.catalog._seller.key;
                                $scope.cartProductQuantity = function () {
                                    $scope.productManager.quantity = 0;
                                    $scope.hasThisProduct = false;
                                    $scope.disableUpdateCart = false;
                                    $scope.orderLineCount = 0;
                                    if (!currentAccount._is_guest) {
                                        models['34'].current(sellerKey).then(function (response) {
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
                                        $scope.isInStock = $scope.getAvailability(true);
                                        $scope.stockText = $scope.getAvailability();
                                        $scope.quantityIncrement = $scope.isInStock;
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

                                $scope.getTrack = function () {
                                    return track;
                                };

                                $scope.delayedChangeVariation = function (forceSkip) {
                                    if (timer) {
                                        $timeout.cancel(timer);
                                    }
                                    timer = $timeout(function () {
                                        timer = null;
                                        $scope.changeVariation(forceSkip);
                                        track.changeProductVariantOption();
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

                                    track.changeProductQuantity();
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

                                function addToCart() {

                                    if (currentAccount._is_guest) {
                                        models['11'].login($state.engineHref((config.hideCloseCatalog ? 'embed-' : '') + 'catalog-product-add-to-cart', {
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

                                    function getsSeller(response) {
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
                                            disableUI: true,
                                            handleError: GLOBAL_CONFIG.backendErrorHandling.productOutOfStock
                                        });
                                    }


                                    function afterAddingToCart(response) {
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
                                            track.updateCartSuccess();
                                        } else {
                                            if (!$scope.hasThisProduct) {
                                                track.addToCartSuccess();
                                            } else {
                                                track.updateCartSuccess();
                                            }
                                            $scope.hasThisProduct = true;
                                            $scope.disableUpdateCart = true;
                                            $scope.canAddToCart = true;
                                        }

                                        if (response.data.entity._lines.length === 0 && $scope.orderLineCount > 1) {
                                            deleteOrder();
                                        }
                                        $scope.orderLineCount = response.data.entity._lines.length;

                                        snackbar.showK('cartUpdated');
                                    }

                                    function failureAddingToCart() {
                                        if (!$scope.hasThisProduct) {
                                            track.addToCartFail();
                                        } else {
                                            track.updateCartFail();
                                        }
                                    }

                                    function anyways() {
                                        $scope.activitySpinner.stop();
                                    }

                                    $scope.activitySpinner.start();
                                    models['19'].current().then(getsSeller).then(afterAddingToCart, failureAddingToCart)['finally'](anyways);
                                }

                                function close() {
                                    var promise = $scope.$close();
                                    promise.then(function () {
                                        track.closeProduct();
                                        if (config.afterClose) {
                                            config.afterClose();
                                        }
                                    });
                                    return promise;
                                }

                                function productIdWatch(neww, old) {
                                    shareWatch();
                                }

                                function productMenuStateChanged(state) {
                                    if (state) {
                                        track.openProductDrawer();
                                    } else {
                                        track.closeProductDrawer();
                                    }
                                }

                                $scope.addToCart = addToCart;

                                if (config.autoAddToCart) {
                                    $timeout(function () {
                                        $scope.addToCart();
                                        config.autoAddToCart = false;
                                    });
                                }

                                $scope.close = close;

                                $scope.notInitialLoad = true;

                                $scope.$watch('product.id', productIdWatch);

                                deferOpen.resolve();

                                track.openProduct();

                                $scope.productMenu.stateChanged = productMenuStateChanged;

                            }, failedOpen);

                        })
                    }).opened['catch'](failedOpen);

                    return openPromise;
                },
                viewModal: function (key, config) {
                    var that = this,
                        track,
                        sellerTrack;

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
                                    ignoreErrors: 2
                                });
                            }, function ($scope, response) {
                                $scope.close = function () {
                                    var promise = $scope.$close();
                                    promise.then(function () {
                                        if (config.afterClose) {
                                            config.afterClose();
                                        }
                                        if (track) {
                                            track.closeCatalog();
                                        }
                                    });
                                    return promise;
                                };
                                if (response) {
                                    var errors = response.data.errors;
                                    if (errors) {
                                        if ((errors.not_found || errors.malformed_key)) {
                                            $scope.notFound = true;
                                        } else {
                                            $scope.close();
                                            errorHandling.snackbar(errors);
                                        }
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
                                    buildUrl = function (a) {
                                        return $state.engineHref('catalog-view', {
                                            key: $scope.catalog.key
                                        }, {
                                            absolute: a
                                        });
                                    },
                                    relativeCatalogUrl = buildUrl(false),
                                    catalogUrl = buildUrl(true),
                                    embedCatalogUrl = $state.engineHref('embed-catalog-view', {
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
                                        track.loadMoreCatalogImages();
                                    }
                                });
                                imagesReader.showLoaderAlways = true;

                                track = helpers.track.proxyLabelToEvents(config.track || helpers.track.noop.homeCatalog, relativeCatalogUrl);
                                sellerTrack = helpers.track.proxyLabelToEvents(track.seller, relativeCatalogUrl);

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

                                social.share($scope, $scope.socialMeta, {
                                    src: embedCatalogUrl
                                }, undefined, {
                                    track: {
                                        openShareDrawer: track.openCatalogShareDrawer,
                                        closeShareDrawer: track.closeCatalogShareDrawer,
                                        focusShareLink: track.focusCatalogShareLink,
                                        focusShareEmbedCode: track.focusCatalogShareEmbedCode
                                    }
                                });

                                $scope.displayShare = function () {
                                    $scope.share.menu.open();
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
                                    var getLink = function (engineHref) {
                                        return $state[engineHref]((config.hideClose ? 'embed-' : '') + 'catalog-order-view', {
                                            key: $scope.catalog.key
                                        });
                                    };
                                    var link = getLink('engineHref');
                                    if (currentAccount._is_guest) {
                                        models['11'].login(link);
                                        return;
                                    }
                                    models['19'].current().then(function (response) {
                                        models['34'].manageModal(undefined, $scope.catalog._seller, response.data.entity, {
                                            cartMode: true,
                                            cartModeRead: true,
                                            relativeUrl: getLink('href'),
                                            track: track.cart
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
                                        productLink = config.productLink,
                                        theTarget = $(target).parents('.catalog-pricetag:first');
                                    if (theTarget.length) {
                                        target = theTarget.get(0);
                                    }
                                    config.productLink = false;
                                    $scope.loadingProduct = true;
                                    that.viewProductModal($scope.catalog.key, image.key, pricetag.key, config.variantSignatureAsDicts, {
                                        popFrom: target,
                                        hideClose: config.hideCloseOnProduct,
                                        hideCloseCatalog: config.hideClose,
                                        noEscapeCatalog: config.noEscape,
                                        noEscape: config.noEscapeOnProduct,
                                        autoAddToCart: (config.variantSignatureAsDicts && config.autoAddToCart) ? true : false,
                                        autoAddToCartQuantity: config.autoAddToCartQuantity,
                                        afterClose: config.afterCloseProduct,
                                        track: track.product
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

                                track.openCatalog();

                                $scope.sellerDetails = models['23'].makeSellerDetails($scope.catalog._seller);

                                $scope.sellerDetails.getTrack = function () {
                                    return sellerTrack;
                                };

                                $scope.catalogMenu.stateChanged = function (state) {
                                    if (state) {
                                        track.openCatalogDrawer();
                                    } else {
                                        track.closeCatalogDrawer();
                                    }
                                };


                            });
                        })
                    });
                }
            });

        });
    }));
}());
