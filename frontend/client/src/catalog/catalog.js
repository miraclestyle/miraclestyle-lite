(function () {
    'use strict';
    angular.module('app').directive('trackIfProductView', ng(function ($timeout) {
        return {
            restrict: 'A',
            link: function (scope, element, attrs) {
                var fired;
                scope.$watch(attrs.trackIfProductView, function (neww, old) {
                    if (fired) {
                        return;
                    }
                    if (angular.isObject(neww)) {
                        $timeout(function () {
                            element.find('[data-pricetag-id="' + neww.image + '-' + neww.id + '"]').click();
                            fired = true;
                        }, 100);
                    }
                });
            }
        };
    })).directive('catalogNewPricetag', ng(function ($parse) {
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
    })).controller('CatalogViewController', ng(function ($scope, $state, models) {
        $scope.site.toolbar.hidden = true;
        models['31'].viewModal($state.params.key, {
            popFrom: undefined,
            inDirection: false,
            outDirection: false,
            afterClose: function () {
                $state.go('home');
            }
        });

    })).controller('CatalogProductAddToCartController', ng(function ($scope, $state, helpers, models) {
        $scope.site.toolbar.hidden = true;
        models['31'].viewModal($state.params.key, {
            popFrom: undefined,
            inDirection: false,
            outDirection: false,
            variantSignatureAsDicts: helpers.url.jsonFromUrlsafe($state.params.variant),
            autoAddToCartQuantity: $state.params.quantity,
            afterClose: function () {
                $state.go('home');
            },
            loadProduct: {
                image: $state.params.image_id,
                id: $state.params.pricetag_id
            }
        });

    })).controller('CatalogProductViewController', ng(function ($scope, $state, models) {
        $scope.site.toolbar.hidden = true;
        models['31'].viewModal($state.params.key, {
            popFrom: undefined,
            inDirection: false,
            outDirection: false,
            afterClose: function () {
                $state.go('home');
            },
            loadProduct: {
                image: $state.params.image_id,
                id: $state.params.pricetag_id
            }
        });

    })).controller('EmbedCatalogViewController', ng(function ($scope, $state, models) {
        $scope.site.toolbar.hidden = true;
        models['31'].viewModal($state.params.key, {
            popFrom: undefined,
            inDirection: false,
            outDirection: false,
            noEscape: true,
            hideClose: true
        });

    })).controller('EmbedCatalogProductViewController', ng(function ($scope, $state, models) {
        $scope.site.toolbar.hidden = true;
        models['31'].viewModal($state.params.key, {
            popFrom: undefined,
            hideClose: true,
            noEscape: true,
            noEscapeOnProduct: true,
            inDirection: false,
            outDirection: false,
            loadProduct: {
                image: $state.params.image_id,
                id: $state.params.pricetag_id
            }
        });

    })).directive('catalogPricetagPosition', ng(function ($timeout, models) { // directives that are not used anywhere else other than this context are defined in their own context
        return {
            link: function (scope, element, attr) {

                var pricetag = scope.$eval(attr.catalogPricetagPosition),
                    resize = function (justElement) {
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
    })).directive('productInstanceCardView', ng(function ($compile) {
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
    })).run(ng(function (modelsEditor, modelsMeta, modelsConfig, currentAccount, $modal, modals, helpers, $q, GLOBAL_CONFIG, $mdSidenav, $timeout, $state, snackbar, social) {

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
                                $scope.hideClose = config ? config.hideClose : false;
                                $scope.currentVariation = [];
                                angular.forEach($scope.product.variants, function (v, i) {

                                    $scope.variants.push({
                                        name: v.name,
                                        options: v.options,
                                        option: (variantSignatureAsDicts ? variantSignatureAsDicts[i][v.name] : v.options[0]),
                                        description: v.description,
                                        allow_custom_value: v.allow_custom_value
                                    });

                                    $scope.variantSelection.push({
                                        type: 'SuperStringProperty',
                                        choices: (v.allow_custom_value ? null : v.options),
                                        code_name: 'option_' + i,
                                        ui: {
                                            //help: v.description,
                                            label: (v.allow_custom_value ? false : v.name),
                                            writable: true,
                                            attrs: {
                                                'ng-change': 'delayedChangeVariation()'
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
                                        if ( /*!v.allow_custom_value*/ 1) {
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
                            popFrom: config.popFrom,
                            noEscape: config.noEscape,
                            controller: ng(function ($scope, productInstanceResponse) {
                                var loadProductInstance, sellerKey, shareWatch, timer;
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
                                    var product,
                                        productInstance,
                                        toUpdate = ['images', 'code', 'unit_price', 'weight', 'volume',
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
                                            if (next !== null && next.length && next !== undefined) {
                                                $scope.product[field] = next;
                                            }
                                        });
                                    } else {
                                        $scope.resetVariantProduct();
                                    }

                                    $scope.variationApplied = true;
                                };

                                $scope.delayedChangeVariation = function () {
                                    if (timer) {
                                        $timeout.cancel(timer);
                                    }
                                    timer = $timeout(function () {
                                        timer = null;
                                        $scope.changeVariation();
                                    }, 500, false);
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

                                $scope.changedQuantity = function () {
                                    $scope.disableUpdateCart = false;
                                };

                                $scope.addToCart = function () {
                                    if (currentAccount._is_guest) {
                                        models['11'].login($state.href('catalog-product-add-to-cart', {
                                            key: $scope.catalog.key,
                                            image_id: $scope.catalog._images[0].id,
                                            pricetag_id: $scope.catalog._images[0].pricetags[0].id,
                                            variant: helpers.url.jsonToUrlsafe($scope.currentVariation),
                                            quantity: $scope.productQuantity
                                        }));
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


                                $scope.$watch('product.id', function (neww, old) {
                                    shareWatch();
                                });

                            })
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
                            snackbar.showK('noImagesInCatalog');
                            return;
                        }
                        $modal.open({
                            templateUrl: 'catalog/view.html',
                            windowClass: 'no-overflow',
                            popFrom: config.popFrom,
                            inDirection: config.inDirection,
                            outDirection: config.outDirection,
                            noEscape: config.noEscape,
                            controller: ng(function ($scope) {
                                $scope.catalogMenu = {};
                                helpers.sideNav.setup($scope.catalogMenu, 'right_catalog_sidenav', doNotRipple);
                                $scope.catalog = entity;
                                $scope.catalog.action_model = '31';
                                $scope.logoImageConfig = {};
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
                                    models['19'].current().then(function (response) {
                                        models['34'].manageModal(undefined, $scope.catalog._seller, response.data.entity, {
                                            cartMode: true
                                        });
                                    });
                                };

                                // cache current user's cart
                                if (!currentAccount._is_guest) {
                                    models['34'].current($scope.catalog._seller.key);
                                }

                                $scope.viewProduct = function (image, pricetag, $event) {
                                    var target = $event.target,
                                        theTarget = $(target).parents('.catalog-pricetag:first');
                                    if (theTarget.length) {
                                        target = theTarget.get(0);
                                    }
                                    that.viewProductModal($scope.catalog.key, image.key, pricetag.key, config.variantSignatureAsDicts, {
                                        popFrom: target,
                                        hideClose: config.hideCloseOnProduct,
                                        noEscape: config.noEscapeOnProduct,
                                        autoAddToCart: config.variantSignatureAsDicts ? true : false,
                                        autoAddToCartQuantity: config.autoAddToCartQuantity
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
                                    $scope.$close().then(function () {
                                        if (config.afterClose) {
                                            config.afterClose();
                                        }
                                    });
                                };
                            })
                        });
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
                                        sortableOptions: {
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
                                                toolbar: {}
                                            };
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

                                            imagesReader = models['31'].reader({
                                                key: $scope.args.key,
                                                next: {
                                                    _images: {}
                                                },
                                                access: accessImages,
                                                complete: function (items) {
                                                    $scope.args._images.extend(items);
                                                }
                                            });
                                            variantOptions = $scope.fieldProduct.modelclass._instances.modelclass.variant_options;
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
                                                                if (pricetag._image) {
                                                                    image = pricetag._image;
                                                                }
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

                                            $scope.droppableOptions = {
                                                accept: '.catalog-new-pricetag',
                                                tolerance: 'pointer'
                                            };

                                            $scope.draggableOptions = {containment : '.image-slider-outer', distance: 10};

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
                                                    rtop = posi2.top - posi.top,
                                                    rleft = posi2.left - posi.left,
                                                    vdom = $('<div style="visibility:hidden;"></div>'),
                                                    newPricetagConfig = {
                                                        position_top: rtop,
                                                        position_left: rleft,
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
                                                    $scope.fieldProduct.ui.specifics.manage(product, undefined, $event); // fire up modal dialog

                                                })['finally'](function () {
                                                    $scope.loadingManageProduct = false;
                                                });
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
                                                        _product: {},
                                                        ui: {
                                                            access: ['_images', ii, 'pricetags', image.pricetags.length]
                                                        }
                                                    };
                                                image.pricetags.push(newPricetag); // append new pricetag to image
                                                setupCurrentPricetag(image, newPricetag); // set current
                                                $scope.fieldProduct.ui.specifics.toolbar.templateActionsUrl = false;
                                                $scope.fieldProduct.ui.realPath = ['_images', ii, 'pricetags', image.pricetags.length - 1, '_product']; // set correct pathing for the new product
                                                recomputeRealPath($scope.fieldProduct);
                                                $scope.fieldProduct.ui.specifics.create(undefined, undefined, {
                                                    target: target
                                                });
                                            };

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
                                                                                    pricetags: {}
                                                                                }
                                                                            }
                                                                        }).then(function (response2) {
                                                                            var pricetag = response2.data.entity._images[0].pricetags[0];

                                                                            angular.forEach($scope.args._images, function (image, i) {
                                                                                if (response.image_key === image.key) {
                                                                                    pricetag.ui.access[1] = i;
                                                                                    pricetag.ui.access[3] = image.pricetags.length;
                                                                                    image.pricetags.push(pricetag);
                                                                                }
                                                                            });
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


                                            $.extend($scope.fieldProduct.modelclass._instances.ui, {
                                                label: GLOBAL_CONFIG.subheaders.productInstances,
                                                path: ['_images', 'pricetags'],
                                                specifics: {
                                                    layoutConfig: [{
                                                        label: 'Variant combinations',
                                                        fields: ["variant_options"]
                                                    }, {
                                                        label: 'Details',
                                                        fields: ["code", "description", "unit_price", "availability", "weight", "volume"]
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
                                                    sortableOptions: {
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
                                                    snackbar.showK('changesSaved');
                                                });
                                                return promise;
                                            };

                                            $scope.close = angular.bind($scope, helpers.form.leave, function () {
                                                $scope.$close();
                                            });
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
