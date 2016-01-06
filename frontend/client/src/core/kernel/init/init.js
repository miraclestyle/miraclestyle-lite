(function () {
    'use strict';
    angular.module('app').config(ng(function ($stateProvider, GLOBAL_CONFIG) {

        $stateProvider
            .state('home', {
                url: '/',
                templateUrl: 'home/index.html',
                controller: 'HomePageController'
            })
            .state('catalog-view', {
                url: '/catalog/:key',
                controller: 'CatalogViewController',
                template: ''
            })
            .state('catalog-product-add-to-cart', {
                url: '/catalog/:key/product-add-to-cart/:image_id/:pricetag_id/:variant/:quantity',
                controller: 'CatalogProductAddToCartController',
                template: ''
            })
            .state('embed-catalog-product-add-to-cart', {
                url: '/embed/catalog/:key/product-add-to-cart/:image_id/:pricetag_id/:variant/:quantity',
                controller: 'CatalogProductAddToCartController',
                template: ''
            })
            .state('catalog-order-view', {
                url: '/catalog/:key/order/view',
                controller: 'CatalogOrderViewController',
                template: ''
            })
            .state('embed-catalog-order-view', {
                url: '/embed/catalog/:key/order/view',
                controller: 'CatalogOrderViewController',
                template: ''
            })
            .state('catalog-product-view', {
                url: '/catalog/:key/product/:image_id/:pricetag_id',
                controller: 'CatalogProductViewController',
                template: ''
            })
            .state('catalog-product-variant-view', {
                url: '/catalog/:key/product/:image_id/:pricetag_id/:variant',
                controller: 'CatalogProductVariantViewController',
                template: ''
            })
            .state('embed-catalog-view', {
                url: '/embed/catalog/:key',
                controller: 'EmbedCatalogViewController',
                template: ''
            })
            .state('embed-catalog-product-variant-view', {
                url: '/embed/catalog/:key/product/:image_id/:pricetag_id/:variant',
                controller: 'EmbedCatalogProductVariantViewController',
                template: ''
            })
            .state('embed-catalog-product-view', {
                url: '/embed/catalog/:key/product/:image_id/:pricetag_id',
                controller: 'EmbedCatalogProductViewController',
                template: ''
            })
            .state('sell-catalogs', {
                url: '/seller/catalogs',
                controller: 'SellCatalogsController',
                templateUrl: 'catalog/list.html'
            })
            .state('sell-orders', {
                url: '/seller/orders',
                controller: 'SellOrdersController',
                templateUrl: 'order/list.html'
            })
            .state('sell-carts', {
                url: '/seller/carts',
                controller: 'SellOrdersController',
                templateUrl: 'order/list.html'
            })
            .state('buy-orders', {
                url: '/buyer/orders',
                controller: 'BuyOrdersController',
                templateUrl: 'order/list.html'
            })
            .state('buy-carts', {
                url: '/buyer/carts',
                controller: 'BuyOrdersController',
                templateUrl: 'buyer/carts.html'
            })
            .state('login', {
                url: '/api/account/login/:provider',
                template: ''
            })
            .state('login-provider-connected', {
                url: '/login_provider_connected/:provider',
                controller: 'LoginProviderConnectedController',
                template: ''
            })
            .state('order-payment-canceled', {
                url: '/order/payment/canceled/:key',
                controller: 'BuyOrdersController',
                templateUrl: 'order/list.html'
            })
            .state('order-payment-success', {
                url: '/order/payment/success/:key',
                controller: 'BuyOrdersController',
                templateUrl: 'order/list.html'
            })
            .state('seller-order-view', {
                url: '/seller/order/:key',
                controller: 'SellOrdersController',
                templateUrl: 'order/list.html'
            })
            .state('seller-cart-view', {
                url: '/seller/cart/:key',
                controller: 'SellOrdersController',
                templateUrl: 'order/list.html'
            })
            .state('buyer-order-view', {
                url: '/buyer/order/:key',
                controller: 'BuyOrdersController',
                templateUrl: 'order/list.html'
            })
            .state('buyer-cart-view', {
                url: '/buyer/cart/:key',
                controller: 'BuyOrdersController',
                templateUrl: 'buyer/carts.html'
            })
            .state('login-status', {
                url: '/login/status',
                template: '',
                controller: 'AccountLoginStatusController'
            })
            .state('order-notify', {
                url: '/api/order/notify/:method',
                template: '',
            })
            .state('about', {
                url: '/about',
                controller: 'AboutController',
                templateUrl: 'home/about.html',
            })
            .state('tos', {
                url: '/tos',
                title: 'tos',
                templateUrl: 'home/tos.html',
            })
            .state('support', {
                url: '/support',
                title: 'support',
                templateUrl: 'home/support.html',
            })
            .state('acceptable_use_policy', {
                url: '/acceptable_use_policy',
                title: 'acceptable_use_policy',
                templateUrl: 'home/acceptable_use_policy.html',
            })
            .state('privacy_policy', {
                url: '/privacy_policy',
                title: 'privacy_policy',
                templateUrl: 'home/privacy_policy.html',
            })
            .state('copyright_policy', {
                url: '/copyright_policy',
                title: 'copyright_policy',
                templateUrl: 'home/copyright_policy.html',
            })
            .state('admin-list', {
                url: '/admin/list/:kind/:query',
                templateUrl: function ($stateParams) {

                    var defaults = 'admin/list.html',
                        config;

                    if ($stateParams.kind !== undefined) {
                        config = GLOBAL_CONFIG.admin.listTemplates[$stateParams.kind];
                        if (config && config.templateUrl) {
                            defaults = config.templateUrl;
                        }
                    }

                    return defaults;
                },
                controller: 'AdminListController'
            });

    })).run(ng(function ($rootScope, modelsInfo, $state, endpoint, models, currentAccount, GLOBAL_CONFIG, modelsUtil, $animate) {
        $rootScope.disableUI = function (state) {
            $rootScope.disableUIState = state;
            $rootScope.$broadcast('disableUI', state);
        };
        $rootScope.overlays = 0;
        $state.engineHref = function () {
            var path = $state.href.apply($state, arguments);
            if (window.ENGINE.DESKTOP.ACTIVE) {
                return path;
            }
            return GLOBAL_CONFIG.host + path;
        };
        $rootScope.$on('$stateChangeSuccess',
            function (event, toState, toParams, fromState, fromParams) {
                if (toState.title) {
                    $rootScope.setPageToolbarTitle(toState.title);
                }
                if (window.ga && !window.tracker) {
                    window.tracker = window.ga.create(window.GOOGLE_ANALYTICS_TRACKING_ID);
                }
                if (window.tracker) {
                    var url = $state.href(toState, toParams);
                    window.tracker.send('pageview', url);
                }
            });
        $.extend(modelsInfo, window.MODELS_META);
        $.extend(currentAccount, window.CURRENT_ACCOUNT);
        modelsUtil.normalize(currentAccount);
        models.init();
        if (!GLOBAL_CONFIG.debug) {
            delete window.MODELS_META;
            delete window.CURRENT_ACCOUNT;
        }
    }));
}());