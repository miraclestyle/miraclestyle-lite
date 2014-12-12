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
    }).directive('catalogPricetagPosition', function ($timeout, helpers) { // directives that are not used anywhere else other than this context are defined in their own context
        return {
            link: function (scope, element, attr) {

                var pricetag = scope.$eval(attr.catalogPricetagPosition), resize = function () {
                    var pa = $(element).parents('.image-slider-item:first'),
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
