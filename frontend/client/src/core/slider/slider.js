(function () {
    'use strict';
    angular.module('app').directive('imageSlider', ng(function ($timeout, $parse) {
        return {
            restrict: 'A',
            link: function (scope, element, attrs) {
                var callback = $parse(attrs.imageSliderLoadMore),
                    parent = element.parent('.image-slider-outer:first'),
                    steadyScroll,
                    anyMore = true,
                    tryToLoadSteady = function (values, done) {
                        if (!anyMore) {
                            return false;
                        }
                        anyMore = false;
                        callback(scope, {
                            callback: function (response, state) {
                                done();
                                anyMore = state;
                            }
                        });
                    },
                    measure = function () {
                        var tw = 0,
                            notDisplayNone = function () {
                                return $(this).css('display') !== 'none';
                            };
                        element.find('.image-slider-item').filter(notDisplayNone).each(function () {
                            tw += $(this).width();
                        });

                        element.width(Math.ceil(tw) + element.find('.vertical-loader').filter(notDisplayNone).width());
                    },
                    resize = function () {
                        var height = parent.parents('.fixed-height:first').height(),
                            bar = parent.parents('.modal:first').find('.new-pricetag-bar');
                        if (bar.length) {
                            height -= bar.outerHeight();
                        }
                        if (height) {
                            parent.height(height);
                            scope.$broadcast('imageSliderResized', height);
                        }
                    };

                resize();
                resize = _.throttle(resize, 100);
                scope.$on('modalResize', resize);
                scope.$on('reMeasureImageSlider', function () {
                    resize();
                    measure();
                });

                scope.$on('readyImageSlider', function () {
                    resize();
                    measure();
                    steadyScroll = new Steady({
                        throttle: 200,
                        scrollElement: parent.get(0),
                        handler: tryToLoadSteady
                    });

                    steadyScroll.addTracker('checkLeft', function () {
                        if (!callback) {
                            return;
                        }
                        var p = parent.get(0),
                            maxscroll,
                            sense;
                        if (!p) {
                            steadyScroll.stop();
                            return;
                        }
                        maxscroll = p.scrollWidth - p.clientWidth;
                        sense = maxscroll - parent.scrollLeft();
                        if (sense < 300) {
                            return true;
                        }
                        return false;
                    });

                    steadyScroll.addCondition('checkLeft', true);
                    parent.data('steady', steadyScroll);
                });

                scope.$on('$destroy', function () {
                    if (steadyScroll) {
                        steadyScroll.stop();
                        parent.data('steady', undefined);
                    }
                });
            }
        };
    })).directive('sliderImage', ng(function ($timeout, helpers, GLOBAL_CONFIG) {
        return {
            restrict: 'A',
            link: function (scope, element, attrs) {
                var image = scope.$eval(attrs.sliderImage),
                    run = function () {
                        var bar = element.parents('.modal:first').find('.new-pricetag-bar'),
                            wholeHeight = element.parents('.fixed-height:first').innerHeight() - window.SCROLLBAR_WIDTH - (bar.length ? bar.outerHeight() : 0),
                            newHeight = wholeHeight,
                            newWidth = (newHeight * image.proportion),
                            imageSize = newHeight > newWidth ? newHeight : newWidth,
                            originalNewHeight = newHeight,
                            reactingElement = element.parents('.image-slider-item:first'),
                            fn = function () {
                                scope.$broadcast('readySingleImageSlider', reactingElement);
                                //console.log(element.get(0).width, newWidth);
                                element.off('load', fn);
                            };
                        newWidth = helpers.newWidthByHeight(newWidth, originalNewHeight, newHeight);

                        element.on('load', fn).attr('src', helpers.url.handleProtocol(image.serving_url) + '=s' + imageSize)
                            .width(newWidth)
                            .height(newHeight);

                        reactingElement
                            .width(newWidth)
                            .height(newHeight);
                    },
                    resize = function () {
                        run();
                        scope.$emit('reMeasureImageSlider');
                    };

                $timeout(function () {
                    run();
                    if (scope.$last) {
                        scope.$emit('readyImageSlider');
                    }
                });
                scope.$on('modalResize', resize);
                scope.$on('itemDelete', function () {
                    $timeout(resize);
                });

            }
        };
    }));
}());