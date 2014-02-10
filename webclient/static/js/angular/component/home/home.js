MainApp.config(['$routeProvider',
  function($routeProvider) {
   
    $routeProvider.
      when('/', {
        templateUrl: logic_template('home', 'home.html'),
        controller: 'HomePage'
      });
      
     
}]).controller('HomePage', ['$scope', function ($scope) {
	
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
				          return output;
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
.run(['$rootScope', '$http', '$location', '$modal', 'Login',
     function ($rootScope, $http, $location, $modal, Login) {
	
	$rootScope.toggleMainMenu = function ()
	{
		var mm = $('#main_menu');
		
		if (mm.is(':visible'))
		{
			mm.stop().animate({
				height : '0px'
			}, 400, function () {
				$(this).hide();
			});
		}
		else
		{
			mm.show();
			mm.stop().animate({
				height : ($(window).height() - $('#top_bar').height()) + 'px',
			}, 400, function () {
				
			});
		}
	};
	
	
	$rootScope.manageAccount = function ()
	{
		
		$rootScope.loading = true;
	
			var handle = function () {
				
				$rootScope.loading = false;
				  
				var modalInstance = $modal.open({
				      templateUrl: logic_template('srv/auth', 'account.html'),
				      controller: function ($scope, $modalInstance) {
			 
					  	  $scope.user = current_user;
					  	  $scope.save = function ()
					  	  {
					  	  	$http.post('/endpoint?action_model=srv.auth.User&action_key=update', $scope.user)
						     .success(function (data) {
								 $rootScope.current_user = data.updated_user;
							});
		
					  	  };
					  	  
						  $scope.cancel = function () {
						    $modalInstance.dismiss('cancel');
						  };
					  }
				    });
				    
					modalInstance.result.then(function (message) {
					     
					    }, function () {
			 			 
			 			 if (on_close) on_close();
				    });
				 
			  };
			
			handle();
		
	};
	
	$rootScope.doLogin = function ()
	{
		Login.ask(function () {
			$location.path('/');
		});
	};
	
	$rootScope.doLogout = function ()
	{
		
	   $http.get('/endpoint',
	     {
	   	   'csrf' : $rootScope.current_user.csrf,
	   	   'action_model' : 'srv.auth.User',
	   	   'action_key' : 'logout',
	     })
	     .success(function (data) {
			 $rootScope.current_user = data.anonymous_user;
			 $location.path('/');
			 $rootScope.toggleMainMenu();
		});
		
	};
	
}]);