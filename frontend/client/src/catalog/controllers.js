(function () {
    'use strict';
    angular.module('app')
        .controller('CatalogViewController', ng(function ($scope, $state, helpers, models) {
            $scope.site.toolbar.hidden = true;
            models['31'].viewModal($state.params.key, {
                popFrom: undefined,
                inDirection: false,
                outDirection: false,
                track: helpers.track.events.linkCatalog,
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
                autoAddToCart: true,
                noEscape: embed,
                afterClose: embed ? undefined : function () {
                    $state.go('home');
                },
                track: helpers.track.events.linkCatalog,
                productLink: true,
                variantSignatureAsDicts: helpers.url.jsonFromUrlsafe($state.params.variant),
                autoAddToCartQuantity: $state.params.quantity,
                loadProduct: {
                    image: $state.params.image_id,
                    id: $state.params.pricetag_id
                }
            });

        })).controller('CatalogProductVariantViewController', ng(function ($scope, $state, helpers, models) {
            $scope.site.toolbar.hidden = true;
            models['31'].viewModal($state.params.key, {
                popFrom: undefined,
                inDirection: false,
                outDirection: false,
                link: true,
                productLink: true,
                track: helpers.track.events.linkCatalog,
                variantSignatureAsDicts: helpers.url.jsonFromUrlsafe($state.params.variant),
                afterClose: function () {
                    $state.go('home');
                },
                loadProduct: {
                    image: $state.params.image_id,
                    id: $state.params.pricetag_id
                }
            });

        })).controller('CatalogProductViewController', ng(function ($scope, helpers, $state, models) {
            $scope.site.toolbar.hidden = true;
            models['31'].viewModal($state.params.key, {
                popFrom: undefined,
                inDirection: false,
                outDirection: false,
                productLink: true,
                track: helpers.track.events.linkCatalog,
                afterClose: function () {
                    $state.go('home');
                },
                loadProduct: {
                    image: $state.params.image_id,
                    id: $state.params.pricetag_id
                }
            });

        })).controller('CatalogOrderViewController', ng(function ($scope, helpers, $state, models) {
            var embed = $state.current.name === 'embed-catalog-order-view';
            $scope.site.toolbar.hidden = true;
            models['31'].viewModal($state.params.key, {
                popFrom: undefined,
                inDirection: false,
                outDirection: false,
                openCart: true,
                track: helpers.track.events.linkCatalog,
                afterClose: function () {
                    $state.go('home');
                },
                hideClose: embed,
                noEscape: embed
            });

        })).controller('EmbedCatalogViewController', ng(function ($scope, $state, helpers, models) {
            $scope.site.toolbar.hidden = true;
            models['31'].viewModal($state.params.key, {
                popFrom: undefined,
                inDirection: false,
                outDirection: false,
                noEscape: true,
                hideClose: true,
                track: helpers.track.events.embedCatalog
            });

        })).controller('EmbedCatalogProductViewController', ng(function ($scope, helpers, $state, models) {
            $scope.site.toolbar.hidden = true;
            models['31'].viewModal($state.params.key, {
                popFrom: undefined,
                hideClose: true,
                noEscape: true,
                noEscapeOnProduct: true,
                inDirection: false,
                outDirection: false,
                track: helpers.track.events.embedCatalog,
                loadProduct: {
                    image: $state.params.image_id,
                    id: $state.params.pricetag_id
                }
            });

        })).controller('EmbedCatalogProductVariantViewController', ng(function ($scope, $state, helpers, models) {
            $scope.site.toolbar.hidden = true;
            models['31'].viewModal($state.params.key, {
                popFrom: undefined,
                hideClose: true,
                noEscape: true,
                noEscapeOnProduct: true,
                inDirection: false,
                outDirection: false,
                track: helpers.track.events.embedCatalog,
                variantSignatureAsDicts: helpers.url.jsonFromUrlsafe($state.params.variant),
                loadProduct: {
                    image: $state.params.image_id,
                    id: $state.params.pricetag_id
                }
            });

        }));

}());
