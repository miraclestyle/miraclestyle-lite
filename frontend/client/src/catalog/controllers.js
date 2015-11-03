(function () {
    'use strict';
    angular.module('app')
        .controller('CatalogViewController', ng(function ($scope, $state, models) {
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
            var embed = $state.current.name === 'embed-catalog-product-add-to-cart';
            $scope.site.toolbar.hidden = true;
            models['31'].viewModal($state.params.key, {
                popFrom: undefined,
                inDirection: false,
                outDirection: false,
                hideClose: embed,
                noEscape: embed,
                afterClose: embed ? undefined : function () {
                    $state.go('home');
                },
                variantSignatureAsDicts: helpers.url.jsonFromUrlsafe($state.params.variant),
                autoAddToCartQuantity: $state.params.quantity,
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

        })).controller('CatalogOrderViewController', ng(function ($scope, $state, models) {
            var embed = $state.current.name === 'embed-catalog-order-view';
            $scope.site.toolbar.hidden = true;
            models['31'].viewModal($state.params.key, {
                popFrom: undefined,
                inDirection: false,
                outDirection: false,
                openCart: true,
                afterClose: function () {
                    $state.go('home');
                },
                hideClose: embed,
                noEscape: embed
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

        }));

}());
