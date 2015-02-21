(function () {
    'use strict';
    angular.module('app').run(function (helpers) {
        helpers.grid = {
            calculate: function (canvas_width, max_width, min_width, margin) {
                /*
                velicina covera je uvek izmedju 240x360px i 180x270px
                padding sa svih strana covera je 1px
                preferirani broj covera u horizontali je 4 ili vise
                ako je ostatak ekrana izmedju 240px i 360px onda se opet preferira najveci cover
                sto se tice GAE blobstore-a najbolje je da se uvek radi fetch covera dimenzija 240x360 pa da se ostalo radi na client side.
                */
                var loop = max_width - min_width,
                    values = [],
                    i,
                    cover_width,
                    cover_count_raw,
                    cover_count,
                    cover_width_rounded,
                    sides;
                for (i = 0; i < loop; i++) {
                    cover_width = max_width - i;
                    cover_count_raw = canvas_width / cover_width;
                    cover_count = Math.floor(cover_count_raw);
                    cover_width = canvas_width / cover_count;
                    if (cover_width > max_width) {
                        cover_count = cover_count + 1;
                        cover_width = canvas_width / cover_count;
                        if (cover_width < min_width) {
                            cover_count = cover_count - 1;
                            cover_width = max_width;
                        }
                    }
                    cover_width_rounded = Math.floor(cover_width);
                    sides = Math.floor((canvas_width % (cover_width_rounded * cover_count)) / 2);
                    cover_width_rounded = cover_width_rounded - (margin * 2);
                    values = [cover_width_rounded, cover_count, sides, cover_width_rounded];
                    if (cover_count_raw > 4 || cover_count === 1) {
                        break;
                    }
                }
                return values;
            }
        };
        helpers.fancyGrid = {
            getHeight: function (images, width, margin) {
                margin = (margin * 2);
                width -= images.length * margin;
                var h = 0;
                angular.forEach(images, function (image) {
                    h += image.proportion;
                });
                return Math.floor(width / h);
            },
            setHeight: function (images, height) {

                angular.forEach(images, function (image) {
                    image.width = (height * image.proportion);
                    image.height = (height);
                });

            },
            resize: function (images, width) {
                this.setHeight(images, this.getHeight(images, width));
            },
            calculate: function (size, images, max_height, margin) {
                var n = 0,
                    providedImages = images,
                    i,
                    slice,
                    h; // reference entire array
                w: while (images.length > 0) {
                    for (i = 1; i < images.length + 1; ++i) {
                        slice = images.slice(0, i);
                        h = this.getHeight(slice, size, margin);
                        if (h < max_height) {
                            this.setHeight(slice, h);
                            n++;
                            images = images.slice(i);
                            continue w;
                        }
                    }
                    this.setHeight(slice, Math.min(max_height, h));
                    n++;
                    break;
                }
                return providedImages;
            }

        };
    }).directive('fancyGridGenerator', function (helpers, $timeout) {

        return {
            link: function (scope, element, attrs) {
                var resize = function () {
                    var originalCanvas = 0,
                        run = function (check) {
                            var canvas = element.outerWidth(true),
                                images = [],
                                margin = 1;
                            if (!canvas || (check && originalCanvas === canvas)) {
                                return; // do not measure if canvas is falsy or if the original canvas is the same as the current one
                            }
                            angular.forEach(scope.$eval(attrs.fancyGridGenerator), function (image) {
                                if (image._state !== 'deleted') {
                                    images.push(angular.copy(image));
                                }
                            });
                            helpers.fancyGrid.calculate(canvas, images, 240, margin);
                            element.find('.grid-item').filter(function () {
                                return $(this).css('display') !== 'none';
                            }).each(function (i) {
                                if (!angular.isDefined(images[i])) {
                                    return;
                                }
                                $(this).css({
                                    width: images[i].width,
                                    height: images[i].height
                                });
                                $(this).find('img').css({
                                    height: images[i].height
                                });
                            });
                        };
                    run();
                    setTimeout(function () {
                        run(true);
                    }, 50);
                };

                scope.$on('modalResize', resize);
                scope.$on('itemOrderChanged', resize);
                scope.$on('itemOrderSorting', resize);
                scope.$on('ngRepeatEnd', resize);
                scope.$on('accordionOpened', function () {
                    setTimeout(resize, 110);
                });
                scope.$on('itemDelete', function () {
                    $timeout(resize);
                });
                scope.$on(attrs.fancyGridGenerator + '.length', function () {
                    $timeout(resize);
                });

            }
        };
    }).directive('gridGenerator', function (GLOBAL_CONFIG, helpers, $timeout) {
        return {
            link: function (scope, element, attrs) {

                var config = scope.$eval(attrs.gridGenerator) || {},
                    margin = config.margin || 0,
                    maxWidth = config.maxWidth || GLOBAL_CONFIG.grid.maxWidth,
                    minWidth = config.minWidth || GLOBAL_CONFIG.grid.minWidth,
                    maxHeight = config.maxHeight || GLOBAL_CONFIG.grid.maxHeight,
                    fixedHeight = config.fixedHeight,
                    square = (angular.isDefined(config.square) ? config.square : true),
                    resize = function () {
                        element = $(element);
                        if (!element.length) {
                            return;
                        }
                        var wrapper = element,
                            canvasWidth = wrapper.outerWidth(true),
                            values;
                        if (canvasWidth) {
                            values = helpers.grid.calculate(canvasWidth,
                                maxWidth, minWidth, margin);

                            if (wrapper.css('paddingLeft') !== values[2] || wrapper.css('paddingRight') !== values[2]) {
                                wrapper.css({
                                    paddingRight: values[2],
                                    paddingLeft: values[2]
                                });
                            }

                            wrapper.find('.grid-item').filter(function () {
                                return $(this).css('display') !== 'none';
                            }).each(function () {
                                var box, newHeight = fixedHeight ? fixedHeight : helpers.newHeightByWidth(maxWidth, maxHeight, values[0]);
                                if (values[0] !== $(this).width() || $(this).height() !== newHeight) {
                                    box = $(this).width(values[0]);
                                    if (square) {
                                        box.height(values[0]);
                                    } else {
                                        $(this).height(newHeight);
                                    }
                                }

                            });

                        }
                    };

                $(window).bind('resize modal.close mainMenu.hide', resize);
                scope.$on('ngRepeatEnd', resize);
                scope.$on('accordionOpened', function () {
                    setTimeout(resize, 110);
                });
                scope.$on('itemDelete', resize);
                scope.$watch(attrs.gridGeneratorItems + '.length', resize);
                scope.$on('$destroy', function () {
                    $(window).off('resize modal.close mainMenu.hide', resize);
                });

            }
        };
    });
}());
