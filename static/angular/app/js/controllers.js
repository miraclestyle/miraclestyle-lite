'use strict';

/* Here we define kernel controllers and deploy the AppControllers module */

var AppControllers = angular.module('App.controllers', [])
    .controller('Boot', ['$scope', function($scope) {
		$scope.user = crUser;
		log('Boot');
}]);