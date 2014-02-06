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
      when('/manage_account', {
      	 controller: 'ManageAccount',
      	 templateUrl : logic_template('srv/auth/account.html'),
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
.factory('Login', ['$http', '$modal', '$rootScope', 

    function ($http, $modal, $rootScope) {
    	
    return {
    	ask : function (on_close)
    	{
    		$rootScope.loading = true;
	
			var handle = function (output) {
				
				$rootScope.loading = false;
				 
			 
				var modalInstance = $modal.open({
				      templateUrl: logic_template('srv/auth/login.html'),
				      controller: function ($scope, $modalInstance, data) {
						  
						  $scope.data = data;
					  
						  $scope.cancel = function () {
						    $modalInstance.dismiss('cancel');
						  };
					  },
				      resolve: {
				        data: function () {
				          return output.data;
				        }
				      }
				    });
				    
					modalInstance.result.then(function (message) {
					      $log.debug(message);
					    }, function () {
			 			 
			 			 if (on_close) on_close();
				    });
				 
			  };
			
			$http.get('/login/google').success(handle);
    	}
    };
}])
.controller('HomePage', ['$scope', '$http', '$log', function ($scope, $http, $log) {
	 
}])
.controller('ManageAccount', ['$scope', '$log', '$http', function ($scope, $log, $http) {
	
	  $scope.user = current_user;
	 
	  $scope.save = function ()
	  {
	  	   $log.info('Save called');
	  };
}])
.controller('Login', ['$scope', '$location', 'Login',
    function ($scope, $location, Login) {
	
	Login.ask(function () {
		 $location.path('/');
	});
	
}]);