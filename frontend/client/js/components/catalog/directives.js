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
                        callback(scope, {config: {
                            position_left: x,
                            position_top: y,
                            image_width: width,
                            image_height: height
                        }});
                    });
                });
            }
        };
    }).directive('catalogPricetagPosition', function ($timeout, models) { // directives that are not used anywhere else other than this context are defined in their own context
        return {
            link: function (scope, element, attr) {

                var pricetag = scope.$eval(attr.catalogPricetagPosition), resize = function () {
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

                $timeout(resize);

                $(window).on('resize', resize);

                scope.$watch(attr.catalogPricetagPosition + '._state', resize);

                scope.$on('$destroy', function () {
                    $(window).off('resize', resize);
                });
            }
        };
    }).directive('productInstanceDisplay', function ($compile) {
        return {
            scope: {
                val: '=productInstanceDisplay',
                field: '=productInstanceDisplayField'
            },
            templateUrl: 'catalog/product/directive/product_instance_display.html'
        };
    }).directive('catalogButtonBottomFloaterPosition', function () {
        return {
            link: function (scope, element, attrs) {
                element.css('bottom', parseInt(element.css('bottom'), 10) + window.SCROLLBAR_WIDTH);
            }
        };
    }).directive('catalogViewMenu', function ($timeout) {
        return {
            restrict: 'A',
            link: function (scope, element, attrs) {
                var content = element.find('.catalog-view-menu-content');
                scope.menu = {
                    hide: true,
                    init: false,
                    toggle: function () {
                        this.init = true;
                        this.hide = !this.hide;
                        var that = this;
                        $timeout(function () {
                            if (!that.hide) {
                                if (!content.data('width')) {
                                    content.data('width', parseInt(content.css('width'), 10));
                                }
                                var width = content.data('width');
                                if (width > $(window).width()) {
                                    width = $(window).width();
                                }
                                content.stop().width(0).css('visibility', 'visible').show().animate({
                                    width: width
                                }, 50, function () {
                                    $(this).show();
                                });

                            } else {
                                content.stop().animate({
                                    width: 0
                                }, 50, function () {
                                    $(this).hide();
                                });
                            }
                        });
                    }
                };
            }
        };
    }).directive('catalogProductShowToggler', function (helpers) {
        return {
            restrict: 'A',
            link: function (scope, element, attrs) {
                var modal = element.parents('.modal:first'),
                    productImages = modal.find('.product-left'),
                    productDetails = modal.find('.product-right'),
                    inImages = attrs.catalogProductShowToggler === 'true',
                    showDetails = productImages.find('.catalog-product-show-details-wrapper'),
                    click = function () {
                        var isMobile = helpers.responsive.isMobile();
                        if (inImages) {
                            if (!isMobile) {
                                productImages.removeClass('t100', 100);
                                productDetails.removeClass('t0', 100);
                            } else {
                                productImages.hide();
                                productDetails.show();
                            }

                            showDetails.hide();
                        } else {
                            if (!isMobile) {
                                productImages.addClass('t100', 100);
                                productDetails.addClass('t0', 100, function () {
                                    showDetails.show();
                                });
                            } else {
                                productDetails.hide();
                                productImages.show();
                                showDetails.show();
                                productImages.scrollLeft(0);
                            }
                        }
                    };
                element.click(click);
                scope.$on('$destroy', function () {
                    element.off('click', click);
                });
            }
        };
    });

}());
