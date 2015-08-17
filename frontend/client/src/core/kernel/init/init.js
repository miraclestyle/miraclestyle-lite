(function () {
    'use strict';
    angular.module('app').config(ng(function ($stateProvider, GLOBAL_CONFIG) {

        $stateProvider
            .state('home', {
                url: '/',
                templateUrl: 'home/index.html',
                controller: 'HomePageController'
            })
            .state('following', {
                url: '/following',
                templateUrl: 'home/index.html',
                controller: 'HomePageController'
            })
            .state('seller-info', {
                url: '/seller/:key',
                controller: 'SellerInfo',
                template: ''
            })
            .state('embed-seller-info', {
                url: '/embed/seller/:key',
                controller: 'SellerEmbedInfo',
                template: ''
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
            .state('catalog-product-view', {
                url: '/catalog/:key/product/:image_id/:pricetag_id',
                controller: 'CatalogProductViewController',
                template: ''
            })
            .state('embed-catalog-view', {
                url: '/embed/catalog/:key',
                controller: 'EmbedCatalogViewController',
                template: ''
            })
            .state('embed-seller-view', {
                url: '/embed/seller/:key',
                controller: 'EmbedSellerViewController',
                template: ''
            })
            .state('embed-catalog-product-view', {
                url: '/embed/catalog/:key/product/:image_id/:pricetag_id',
                controller: 'EmbedCatalogProductViewController',
                template: ''
            })
            .state('sell-catalogs', {
                url: '/sell/catalogs',
                controller: 'SellCatalogsController',
                templateUrl: 'catalog/list.html'
            })
            .state('sell-orders', {
                url: '/sell/orders',
                controller: 'SellOrdersController',
                templateUrl: 'order/list.html'
            })
            .state('sell-carts', {
                url: '/sell/carts',
                controller: 'SellOrdersController',
                templateUrl: 'order/list.html'
            })
            .state('buy-orders', {
                url: '/buy/orders',
                controller: 'BuyOrdersController',
                templateUrl: 'order/list.html'
            })
            .state('buy-carts', {
                url: '/buy/carts',
                controller: 'BuyOrdersController',
                templateUrl: 'buyer/carts.html'
            })
            .state('login', {
                url: '/api/account/login/:provider',
                template: ''
            })
            .state('loginProviderConnected', {
                url: '/login_provider_connected/:provider',
                controller: 'LoginProviderConnectedController',
                template: ''
            })
            .state('order-payment-canceled', {
                url: '/order/payment/canceled/:key',
                controller: 'OrderPaymentCanceledController',
                template: ''
            })
            .state('order-payment-success', {
                url: '/order/payment/success/:key',
                controller: 'OrderPaymentSuccessController',
                template: ''
            })
            .state('login-status', {
                url: '/login/status',
                template: '',
                controller: 'AccountLoginStatusController'
            })
            .state('paypal-ipn', {
                url: '/api/order/complete/paypal',
                template: '',
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

    })).run(ng(function (modelsInfo, endpoint, models, currentAccount, GLOBAL_CONFIG, modelsUtil) {
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