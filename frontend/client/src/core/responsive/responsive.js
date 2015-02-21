(function () {
    'use strict';
    angular.module('app').run(function (helpers) {
        helpers.responsive = {
            isTouch: function () {
                return Modernizr.touch;
            },
            isMobile: function () {
                return $('#is-mobile').css('visibility') === 'visible';
            },
            isTablet: function () {
                return $('#is-tablet').css('visibility') === 'visible';
            },
            isDesktop: function () {
                return !this.isMobile();
            },
            isLandscape: function () {
                return $('#is-landscape').css('visibility') === 'visible';
            },
            isPortrait: function () {
                return !this.isLandscape();
            }
        };
    });
}());
