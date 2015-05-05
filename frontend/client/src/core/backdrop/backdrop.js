(function () {
    'use strict';

    angular.module('material.components.backdrop', [
            'material.core'
        ])
        .directive('mdBackdrop', BackdropDirective);

    function BackdropDirective($mdTheming) {
        return $mdTheming;
    }
    BackdropDirective.$inject = ["$mdTheming"];
})();
