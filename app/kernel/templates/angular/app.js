'use strict';

var log = function()
{
	if ('console' in window)
	{
		console.log(arguments);
	}
};

var AppTemplates = {{templates|to_json|safe}};

// Declare app level module which depends on filters, and services
var App = angular.module('App', ['ui.bootstrap', 'App.filters', 'App.services', 'App.directives', 'App.controllers']).
  config(['$routeProvider', '$locationProvider', function($routeProvider, $locationProvider) {
      $routeProvider{% for k in ROUTES %}
      				.when({{k.angular_path|to_json|safe}}, {% if k.angular_config %}angular.extend({{k.angular_config|to_json|safe}}, {% endif %} { {% if k.angular_template %}templateUrl: {{k.angular_template|to_json|safe}},{% endif %} controller: {{k.angular_controller|to_json|safe}}}{% if k.angular_config %}){% endif %}){% endfor %};
    			  
      $locationProvider.html5Mode(true);
}]);

App.run(function($templateCache) {
	 angular.forEach(AppTemplates, function (v) {
	 	$templateCache.put(v.slug, v.content);
	 });
});