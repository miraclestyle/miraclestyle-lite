angular.module('app.ui',
	  [
	   'app.ui.transition', 
	   'app.ui.collapse', 
	   'app.ui.accordion',
	   'app.ui.modal',
	   'app.ui.dropdown',
	   'app.ui.select2',
	  ]
);

var MainApp = angular.module('MainApp', ['ngRoute', 'app.ui'])
.config(['$routeProvider', '$httpProvider', '$locationProvider',
  function($routeProvider, $httpProvider, $locationProvider) {
  	
    $routeProvider.
      when('/', {
        templateUrl: logic_template('home.html'),
        controller: 'HomePage'
      }).
      when('/login', {
        controller: 'Login',
        template : " ",
      });
 
     $httpProvider.defaults.headers.common['X-Requested-With'] = 'XmlHttpRequest';
     
     $locationProvider.hashPrefix('!');
     
}])
.run(function ($rootScope) {
    
    $rootScope.current_user = current_user;
    $rootScope.loading = false;
})
.controller('HomePage', ['$scope', '$http', '$log', function ($scope, $http, $log) {
	 
}])
.controller('Login', ['$scope', '$http', '$log', '$modal', '$location', '$rootScope', 
    function ($scope, $http, $log, $modal, $location) {
	
	$scope.loading = true;
	
	var handle = function (output) {
		
		$scope.loading = false;
		
		$scope.data = output.data;
	 
		var modalInstance = $modal.open({
		      templateUrl: logic_template('login.html'),
		      controller: function ($scope, $modalInstance, data) {
				  
				  $scope.data = data;
			  
				  $scope.cancel = function () {
				    $modalInstance.dismiss('cancel');
				    $location.path('/');
				  };
			  },
		      resolve: {
		        data: function () {
		          return $scope.data;
		        }
		      }
		    });
		    
			modalInstance.result.then(function (message) {
			      $log.debug(message);
			    }, function () {
	 
		    });
		 
	  };
	
	$http.get('/login/google').success(handle);
	
}]);