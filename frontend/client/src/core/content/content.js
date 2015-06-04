(function () {
    'use strict';

    angular.module('material.components.content', [
            'material.core'
        ])
        .directive('mdContent', mdContentDirective).config(['markdownConverterProvider', function (markdownConverterProvider) {
            markdownConverterProvider.config({
                extensions: ['demo']
            });
        }]);


    function mdContentDirective() {
        return {
            restrict: 'E',
            controller: ['$scope', '$element', ContentController],
            link: function (scope, element, attr) {
                var node = element[0];
                scope.$broadcast('$mdContentLoaded', element);

                iosScrollFix(element[0]);
            }
        };

        function ContentController($scope, $element) {
            this.$scope = $scope;
            this.$element = $element;
        }
    }
    mdContentDirective.$inject = [];

    function iosScrollFix(node) {
        // IOS FIX:
        // If we scroll where there is no more room for the webview to scroll,
        // by default the webview itself will scroll up and down, this looks really
        // bad.  So if we are scrolling to the very top or bottom, add/subtract one
        angular.element(node).on('$md.pressdown', function (ev) {
            // Only touch events
            if (ev.pointer.type !== 't') return;
            // Don't let a child content's touchstart ruin it for us.
            if (ev.$materialScrollFixed) return;
            ev.$materialScrollFixed = true;

            if (node.scrollTop === 0) {
                node.scrollTop = 1;
            } else if (node.scrollHeight === node.scrollTop + node.offsetHeight) {
                node.scrollTop -= 1;
            }
        });
    }
})();


(function () {
    var demo = function (converter) {
        return [{
            type: 'output',
            filter: function (text) {
                if (window._allow) {
                    return text;
                }
                try {
                    $.parseHTML(text); // any invalid html will be shown as blank
                }catch (e){
                    return '';
                }
                var dom = $('<div />').html(text),
                    whiteListIframe = function (a) {
                        // regex for whitelisted providers... @todo
                        return a;
                    },
                    whiteListA = {
                        '_blank': true
                    },
                    intOrPercentage = function (a) {
                        var percentage = a.indexOf('%') !== -1,
                            px = a.indexOf('px') !== -1,
                            suffix = '';
                        if (percentage) {
                            suffix = '%';
                        }
                        if (px) {
                            suffix = 'px';
                        }
                        return parseInt(a, 10) + suffix;
                    },
                    allowedTags = {
                        strong: true,
                        b: true,
                        hr: true,
                        ol: true,
                        blockquote: true,
                        kbd: true,
                        code: true,
                        i: true,
                        em: true,
                        h1: true,
                        h2: true,
                        h3: true,
                        h4: true,
                        /*a: {
                            href: function (a) {
                                var regex = /^http/,
                                    regex2 = '/^#/';
                                if (a.match(regex) || a.match(regex2)) {
                                    return a;
                                }
                                return '';
                            },
                            target: function (a) {
                                if (whiteListA[a]) {
                                    return a;
                                }
                                return '';
                            },
                        },*/
                        h5: true,
                        h6: true,
                        ul: true,
                        li: true,
                        div: true,
                        pre: true,
                        p: true,
                        br: true,
                        iframe: {
                            width: intOrPercentage,
                            height: intOrPercentage,
                            src: whiteListIframe,
                            allowfullscreen: function () {
                                return '';
                            },
                            frameborder: function (a) {
                                return parseInt(a, 10);
                            }
                        }
                    };
                dom.find('*').each(function () {
                    var item = $(this),
                        name = item.get(0).nodeName.toLowerCase(),
                        allowed = allowedTags[name];
                    if (allowed) {
                        $.each(this.attributes, function () {
                            var propertySpec = angular.isObject(allowed) ? allowed[this.name] : false;
                            if (!propertySpec) {
                                item.removeAttr(this.name);
                            } else {
                                item.attr(this.name, propertySpec(item.attr(this.name)));
                            }
                        });
                    } else {
                        item.remove();
                    }
                });

                return dom.html();
            }
        }];
    };

    // Client-side export
    if (typeof window !== 'undefined' && window.Showdown && window.Showdown.extensions) {
        window.Showdown.extensions.demo = demo;
    }
    // Server-side export
    if (typeof module !== 'undefined') module.exports = demo;
}());
