(function () {
    'use strict';

    angular.module('material.components.toolbar', [
            'material.core',
            'material.components.content'
        ])
        .directive('mdToolbar', mdToolbarDirective).run(function (helpers, GLOBAL_CONFIG) {
            if (angular.isUndefined(helpers.toolbar)) {
                helpers.toolbar = {};
            }
            $.extend(helpers.toolbar, {
                title: function (keys, separator) {
                    var splits,
                        gets = GLOBAL_CONFIG.toolbar.titles,
                        complete = [],
                        initial = gets[keys];
                    if (!separator) {
                        separator = ' / ';
                    }
                    if (angular.isDefined(initial)) {
                        return initial.join(separator);
                    }
                    if (!angular.isArray(keys)) {
                        splits = keys.split('.');
                    } else {
                        splits = keys;
                    }
                    angular.forEach(splits, function (key, i) {
                        var get = gets[key];
                        if (get === false) {
                            return;
                        }
                        complete.push(angular.isDefined(get) ? get : key);
                    });
                    if (!complete.length) {
                        return keys;
                    }
                    return complete.join(separator);
                },
                buildTitle: function (callbacks) {
                    var paths = [];
                    angular.forEach(callbacks, function (cb) {
                        paths.push(cb());
                    });
                    return helpers.toolbar.title(paths.join('.'));
                },
                makeTitle: function (word) {
                    return _.string.capitalize(_.string.camelize(word));
                }
            });
        });

    function mdToolbarDirective($$rAF, $mdConstant, $mdUtil, $mdTheming) {

        return {
            restrict: 'E',
            controller: angular.noop,
            link: function (scope, element, attr) {
                $mdTheming(element);

                if (angular.isDefined(attr.mdScrollShrink)) {
                    setupScrollShrink();
                }

                function setupScrollShrink() {
                    // Current "y" position of scroll
                    var y = 0;
                    // Store the last scroll top position
                    var prevScrollTop = 0;

                    var shrinkSpeedFactor = attr.mdShrinkSpeedFactor || 0.5;

                    var toolbarHeight;
                    var contentElement;

                    var debouncedContentScroll = $$rAF.throttle(onContentScroll);
                    var debouncedUpdateHeight = $mdUtil.debounce(updateToolbarHeight, 5 * 1000);

                    // Wait for $mdContentLoaded event from mdContent directive.
                    // If the mdContent element is a sibling of our toolbar, hook it up
                    // to scroll events.
                    scope.$on('$mdContentLoaded', onMdContentLoad);

                    function onMdContentLoad($event, newContentEl) {
                        // Toolbar and content must be siblings
                        if (element.parent()[0] === newContentEl.parent()[0]) {
                            // unhook old content event listener if exists
                            if (contentElement) {
                                contentElement.off('scroll', debouncedContentScroll);
                            }

                            newContentEl.on('scroll', debouncedContentScroll);
                            newContentEl.attr('scroll-shrink', 'true');

                            contentElement = newContentEl;
                            $$rAF(updateToolbarHeight);
                        }
                    }

                    function updateToolbarHeight() {
                        toolbarHeight = element.prop('offsetHeight');
                        // Add a negative margin-top the size of the toolbar to the content el.
                        // The content will start transformed down the toolbarHeight amount,
                        // so everything looks normal.
                        //
                        // As the user scrolls down, the content will be transformed up slowly
                        // to put the content underneath where the toolbar was.
                        contentElement.css(
                            'margin-top', (-toolbarHeight * shrinkSpeedFactor) + 'px'
                        );
                        onContentScroll();
                    }

                    function onContentScroll(e) {
                        var scrollTop = e ? e.target.scrollTop : prevScrollTop;

                        debouncedUpdateHeight();

                        y = Math.min(
                            toolbarHeight / shrinkSpeedFactor,
                            Math.max(0, y + scrollTop - prevScrollTop)
                        );

                        element.css(
                            $mdConstant.CSS.TRANSFORM,
                            'translate3d(0,' + (-y * shrinkSpeedFactor) + 'px,0)'
                        );
                        contentElement.css(
                            $mdConstant.CSS.TRANSFORM,
                            'translate3d(0,' + ((toolbarHeight - y) * shrinkSpeedFactor) + 'px,0)'
                        );

                        prevScrollTop = scrollTop;
                    }

                }

            }
        };

    }
    mdToolbarDirective.$inject = ["$$rAF", "$mdConstant", "$mdUtil", "$mdTheming"];
})();
