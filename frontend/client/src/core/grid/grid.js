(function () {
    'use strict';
    angular.module('app').run(ng(function (helpers) {
        helpers.grid = {
            calculate: function (canvas_width, max_width, min_width, margin) {
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
                    values = [cover_width_rounded, cover_count, sides];
                    if (cover_count_raw > 4 || cover_count === 1) {
                        break;
                    }
                }
                return values;
            }
        };
        helpers.gridStacked = {
            getHeight: function (images, width, margin) {
                margin = (margin * 2);
                width -= images.length * margin;
                var h = 0;
                angular.forEach(images, function (image) {
                    h += image.proportion;
                });
                // Math.floor
                return (width / h);
            },
            setHeight: function (images, height) {

                angular.forEach(images, function (image) {
                    image.width = (height * image.proportion);
                    image.height = height;
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
    })).directive('gridStacked', ng(function (helpers, $timeout) {

        return {
            link: function (scope, element, attrs) {
                var resize = function () {
                    var originalCanvas = 0,
                        run = function (check) {
                            var canvas = element.width(),
                                images = [],
                                margin = 1;
                            if (!canvas || (check && originalCanvas === canvas)) {
                                return; // do not measure if canvas is falsy or if the original canvas is the same as the current one
                            }
                            angular.forEach(scope.$eval(attrs.gridStacked), function (image) {
                                if (image._state !== 'deleted') {
                                    images.push(angular.copy(image));
                                }
                            });
                            helpers.gridStacked.calculate(canvas, images, 240, margin);
                            element.find('.grid-item').filter(function () {
                                return $(this).css('display') !== 'none';
                            }).each(function (i) {
                                if (!angular.isDefined(images[i])) {
                                    return;
                                }
                                $(this).css({
                                    width: images[i].width,
                                    height: images[i].height
                                }).addClass('visible');
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

                resize = _.throttle(resize, 100);

                scope.$on('modalResize', resize);
                scope.$on('itemOrderChanged', resize);
                scope.$on('itemOrderSorting', resize);
                scope.$on('ngRepeatEnd', resize);

                scope.$on('itemDelete', function () {
                    $timeout(resize, 0, false);
                });
                scope.$watch(attrs.gridStacked + '.length', function () {
                    $timeout(resize, 0, false);
                });

            }
        };
    })).directive('gridGenerator', ng(function (GLOBAL_CONFIG, helpers, $timeout) {
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
                            canvasWidth = wrapper.width(),
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

                                $(this).addClass('visible');

                            });

                        }
                    };

                resize = _.throttle(resize, 100);

                $(window).bind('resize', resize);
                scope.$on('ngRepeatEnd', resize);
                scope.$on('itemDelete', resize);
                scope.$watch(attrs.gridGeneratorItems + '.length', resize);
                scope.$on('$destroy', function () {
                    $(window).off('resize', resize);
                });

            }
        };
    })).directive('gridScale', ng(function (helpers, $timeout, GLOBAL_CONFIG) {
        return {
            controller: ng(function ($scope, $element) {
                var that = this,
                    tracker = 0;
                that.items = [];
                that.config = {};
                that.columns = 1;
                that.calc = [];
                that.getColumns = function () {
                    var calc = helpers.grid.calculate($element.width(), that.config.maxWidth, that.config.minWidth, that.config.margin);
                    that.columns = calc[1];
                    that.calc = calc;
                };
                that.add = function (item) {
                    tracker += 1;
                    that.items.push(item);
                    that.calculate(item);
                    if (tracker === that.columns) {
                        tracker = 0;
                        //that.resize(true);
                    }
                };
                that.remove = function (item) {
                    that.items.remove(item);
                    that.resize();
                };
                that.calculate = function (item) {
                    if (that.columns < 2 && $element.width() > that.config.maxWidth) {
                        item.css('width', 'calc((100%) - ' + (that.config.margin * 2) + 'px)');
                        $element.css({
                            marginLeft: that.calc[2],
                            marginRight: that.calc[2]
                        });
                        return;
                    }
                    $element.css({
                        marginLeft: '',
                        marginRight: ''
                    });
                    item.css('width', 'calc((' + (100 / that.columns) + '%) - ' + (that.config.margin * 2) + 'px)');
                };
                that.resize = function (doAll) {
                    that.getColumns();
                    angular.forEach(that.items, function (item) {
                        that.calculate(item);
                        if (doAll) {
                            if (that.config.square) {
                                //item.height(item.width());
                            } else {
                                //item.height(helpers.newHeightByWidth(that.config.maxWidth, that.config.maxHeight, item.width()));
                            }
                        }
                    });
                };

                that.resize = _.throttle(that.resize, 100);

                $(window).on('resize', that.resize);

                $scope.$on('$destroy', function () {
                    $(window).off('resize', that.resize);
                });
            }),
            link: function (scope, element, attrs, ctrl) {
                $.extend(ctrl.config, GLOBAL_CONFIG.grid, scope.$eval(attrs.gridScale) || {});
                ctrl.getColumns();
            }
        };
    })).directive('gridScaleItem', ng(function (helpers) {
        return {
            require: '^gridScale',
            link: function (scope, element, attrs, gridScaleCtrl) {
                var appear = function (event, img) {
                    if (img) {
                        var scale = img.parents('[grid-scale-item]:first');
                        if (scale.length && scale.get(0) === element.get(0)) {
                            element.addClass('visible');
                        }
                    } else {
                        element.addClass('visible');
                    }
                }, config = scope.$eval(attrs.gridScaleItem) || {};
                gridScaleCtrl.add(element);
                if (config.image) {
                    scope.$on('displayImageLoaded', appear);
                } else {
                    setTimeout(appear, 50);
                }
                scope.$on('$destroy', function () {
                    gridScaleCtrl.remove(element);
                });
            }
        };
    }));
}());
