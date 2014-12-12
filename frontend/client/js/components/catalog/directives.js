(function () {
    'use strict';

    angular.module('app').directive('catalogSlider', function ($timeout, $parse) {
        return {
            restrict: 'A',
            link: function (scope, element, attrs) {
                var loading = null,
                    callback = $parse(attrs.catalogSliderLoadMore),
                    parent = element.parent('.catalog-slider-outer:first'),
                    tryToLoad = function (settings) {
                        var p = parent.get(0),
                            maxscroll = p.scrollWidth - p.clientWidth,
                            sense = maxscroll - parent.scrollLeft();
                        if (sense < 300 && !loading) {
                            loading = setTimeout(function () {
                                callback(scope, {callback: function () {
                                    loading = null;
                                }});
                            }, 200);

                        }
                    },
                    measure = function () {
                        var tw = 0;
                        element.find('.catalog-slider-item').filter(function () {
                            return $(this).css('display') !== 'none';
                        }).each(function () {
                            tw += $(this).width();
                        });

                        element.width(Math.ceil(tw));
                    },
                    resize = function () {
                        if (parent.parents('.modal').length) {
                            var height = $(window).height(),
                                footer = parent.parents('.modal').find('.modal-footer');
                            if (footer.length) {
                                height -= (footer.outerHeight());
                            }
                            parent.height(height);
                        }
                    };

                resize();
                $(window).bind('resize', resize);

                scope.$on('reMeasureCatalogSlider', function () {
                    resize();
                    measure();
                });

                scope.$on('readyCatalogSlider', function () {
                    resize();
                    measure();
                    parent.scroll(tryToLoad);
                });

                scope.$on('$destroy', function () {
                    $(window).off('resize', resize);
                });
            }
        };
    }).directive('catalogSliderImage', function ($timeout, helpers) {
        return {
            restrict: 'A',
            link: function (scope, element, attrs) {

                var sizingScopes = _.range(0, 1700, 100),
                    image = scope.$eval(attrs.catalogSliderImage),
                    run = function () {
                        var newHeight = element.parents('.modal-body:first').innerHeight() - window.SCROLLBAR_WIDTH,
                            newWidth = Math.ceil(newHeight * image.proportion),
                            imageSize = helpers.closestLargestNumber(sizingScopes, newHeight);

                        element.attr('src', image.serving_url + '=s' + imageSize)
                            .width(newWidth)
                            .height(newHeight);

                        element.parents('.catalog-slider-item:first')
                            .width(newWidth)
                            .height(newHeight);
                    },
                    resize = function () {
                        run();
                        scope.$emit('reMeasureCatalogSlider');
                    };

                $timeout(function () {
                    run();
                    if (scope.$last) {
                        scope.$emit('readyCatalogSlider');
                    }
                });

                $(window).bind('resize', resize);

                scope.$on('itemDelete', function () {
                    $timeout(resize);
                });
                scope.$on('$destroy', function () {
                    $(window).off('resize', resize);
                });

            }
        };
    }).directive('catalogNewPricetag', function ($parse) {
        return {
            restrict: 'A',
            link: function (scope, element, attrs) {
                var callback = $parse(attrs.catalogNewPricetag);
                element.on('click', function (event) {
                    var offset = element.offset(),
                        x = event.pageX - offset.left,
                        y = event.pageY - offset.top,
                        parent = element.parents('.catalog-slider-item:first'),
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
    }).directive('catalogPricetagPosition', function ($timeout, helpers) { // directives that are not used anywhere else other than this context are defined in their own context
        return {
            link: function (scope, element, attr) {

                var pricetag = scope.$eval(attr.catalogPricetagPosition), resize = function () {
                    var pa = $(element).parents('.catalog-slider-item:first'),
                        sizes;

                    sizes = helpers.calculatePricetagPosition(
                        pricetag.position_top,
                        pricetag.position_left,
                        pricetag.image_width,
                        pricetag.image_height,
                        pa.width(),
                        pa.height()
                    );

                    console.log(pricetag, sizes);

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
    });

}());
