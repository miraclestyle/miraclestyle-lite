(function () {
    'use strict';
    angular.module('app').directive('trackIfProductView', ng(function ($timeout) {
        return {
            restrict: 'A',
            link: function (scope, element, attrs) {
                var fired;
                scope.$watch(attrs.trackIfProductView, function trackIfProductView(neww, old) {
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
    })).directive('catalogPricetagPosition', ng(function ($timeout, models) { // directives that are not used anywhere else other than this context are defined in their own context
        return {
            link: function (scope, element, attr) {

                var pricetag = scope.$eval(attr.catalogPricetagPosition),
                    resize = function (justElement) {
                        var pa = $(element).parents('.image-slider-item:first'),
                            sizes,
                            containerh = pa.height(),
                            pricetagHeight = 36;
                        sizes = models['31'].calculatePricetagPosition(
                            pricetag.position_top,
                            pricetag.position_left,
                            pricetag.image_width,
                            pricetag.image_height,
                            pa.width(),
                            containerh
                        );

                        if (sizes[0] < 0) {
                            sizes[0] = 0;
                        } else {
                            if (sizes[0] > containerh - pricetagHeight) {
                                sizes[0] = containerh - pricetagHeight;
                            }
                        }

                        pricetag._position_top = sizes[0];
                        pricetag._position_left = sizes[1];

                        $(element).css({
                            top: pricetag._position_top,
                            left: pricetag._position_left,
                            visibility: 'visible'
                        });
                    },
                    track = [];
                resize = _.throttle(resize, 100);
                $timeout(resize, 0, false);
                scope.$on('modalResize', resize);
                scope.$on('resizePricetags', function (event, tpricetag) {
                    if (tpricetag) {
                        if (tpricetag.key === pricetag.key) {
                            pricetag.position_top = tpricetag.position_top;
                            pricetag.position_left = tpricetag.position_left;
                            resize();
                        }
                    } else {
                        resize();
                    }
                });
                angular.forEach(['state', 'key', 'position_left', 'position_top', '_position_left', '_position_top'], function (value) {
                    track.push(attr.catalogPricetagPosition + '.' + value);
                });
                scope.$watch(function () {
                    return true;
                }, resize);
            }
        };
    })).directive('productInstanceCardView', ng(function (GLOBAL_CONFIG) {
        return {
            scope: {
                val: '=productInstanceCardView'
            },
            templateUrl: 'catalog/product/instance_card_view.html',
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
    })).directive('productStockConfigurationCardView', ng(function (GLOBAL_CONFIG) {
        return {
            scope: {
                val: '=productStockConfigurationCardView'
            },
            templateUrl: 'catalog/product/stock_configuration_card_view.html',
            link: function (scope) {
                scope.showVariantLabel = function (signature) {
                    return _.keys(signature)[0];
                };
                scope.showVariantValue = function (signature) {
                    var val = _.values(signature)[0];
                    if (val === '***Any***') {
                        return 'Any';
                    }
                    return val;
                };
                scope.showMainLabel = function (k) {
                    return GLOBAL_CONFIG.fields.translateChoices['133'].availability[k];
                };
            }
        };
    }));

}());
