(function () {
    'use strict';

    angular.module('app').directive('sendMessage', function ($parse) {
        return {
            restrict: 'A',
            link: function (scope, element, attrs) {
                var callback = $parse(attrs.sendMessage),
                    root = element.parents('.modal-dialog:first'),
                    textarea,
                    pane,
                    click = function (e) {
                        textarea = root.find('textarea');
                        pane = root.find('.overflow-y');
                        if (textarea.length && textarea.val()) {
                            callback(scope);
                        } else {
                            pane.stop().scrollTo(textarea, 100, function () {
                                textarea.focus();
                            });
                        }
                        e.preventDefault();
                    };

                element.on('click', click);

                scope.$on('$destroy', function () {
                    element.off('click', click);
                });

            }
        };
    });

}());
