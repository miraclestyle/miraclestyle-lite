angular.module('app.ui',
	  [
	   'app.ui.transition', 
	   'app.ui.tabs',
	   'app.ui.collapse', 
	   'app.ui.accordion',
	   'app.ui.modal',
	   'app.ui.dropdown',
	   'app.ui.select2',
	  ]
);

var MainApp = angular.module('MainApp', ['ngRoute', 'app.ui'])
.config(['$httpProvider', '$locationProvider',
  function($httpProvider, $locationProvider) {
   
     $httpProvider.defaults.headers.common['X-Requested-With'] = 'XmlHttpRequest';
     
     $locationProvider.hashPrefix('!');
     
}])
.run(function ($rootScope) {
    
    $rootScope.current_user = current_user;
    $rootScope.loading = false;
});