'use strict';

/* Directives  */
 
var AppDirectives = angular.module('App.directives', []).
  directive('appVersion', ['version', function(version) {
    return function(scope, elm, attrs) {
      elm.text(version);
    };
  }]);
