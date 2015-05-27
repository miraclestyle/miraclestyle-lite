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
        return [
            // Replace escaped @ symbols
            {
                type: 'output',
                //regex: '<iframe(.+?)</iframe>',
                filter: function (text) {
                    console.log(text);
                    return text;
                }
            }
        ];
    };

    // Client-side export
    if (typeof window !== 'undefined' && window.Showdown && window.Showdown.extensions) {
        window.Showdown.extensions.demo = demo;
    }
    // Server-side export
    if (typeof module !== 'undefined') module.exports = demo;
}());
