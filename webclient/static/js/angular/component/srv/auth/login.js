MainApp.config(['$routeProvider',
  function($routeProvider) {
   
    $routeProvider.
      when('/login', {
        controller: 'Login',
        template : " ",
      });
     
}])
.factory('Login', ['$http', '$modal', '$rootScope', 

    function ($http, $modal, $rootScope) {
    	
    return {
    	ask : function (on_close)
    	{
    		$rootScope.loading = true;
	
			var handle = function (output) {
				
				$rootScope.loading = false;
				 
			 
				var modalInstance = $modal.open({
				      templateUrl: logic_template('srv/auth', 'login.html'),
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
.controller('Login', ['$scope', '$location', 'Login',
    function ($scope, $location, Login) {
	
	Login.ask(function () {
		 $location.path('/');
	});
	
}]);
