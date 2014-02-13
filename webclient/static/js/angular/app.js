angular.module('app.ui',
	  [
	   'app.ui.transition',
	   'app.ui.collapse', 
	   'app.ui.accordion',
	   'app.ui.modal',
	   'app.ui.select2',
	  ]
);

var MainApp = angular.module('MainApp', ['ngRoute', 'ngBusy', 'ngStorage', 'checklist-model', 'app.ui'])
.config(['$httpProvider', '$locationProvider',
  function($httpProvider, $locationProvider) {
   
     $httpProvider.defaults.headers.common['X-Requested-With'] = 'XmlHttpRequest';
 
     $locationProvider.hashPrefix('!');
     
     $locationProvider.html5Mode(true);
     
}])
.factory('Endpoint', ['$http', function ($http) {
	
	var _compile = function(action, model, data, config)
	{
		 if (!config) config = {};
			
		 return [angular.extend({
				action_model : model,
				action_key : action,
			}, data), config];
		
	};
	
	return {
		post : function(action, model, data, config)
		{
		    compiled = _compile(action, model, data, config);
			
			return $http.post('/endpoint', compiled[0], compiled[1]);
		},
		get : function(action, model, data, config)
		{
		    compiled = _compile(action, model, data, config);
		    
		    compiled[1]['params'] = $.param(compiled[0]);
			
			return $http.get('/endpoint', compiled[1]);
		},
	};
}])
.run(function ($rootScope) {
    
    $rootScope.current_user = current_user;
    $rootScope.loading = false;
});