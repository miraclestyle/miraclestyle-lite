MainApp.run(['$rootScope', '$http', '$location', 'Login', 
			function ($rootScope, $http, $location, Login) {
	
	  
	$rootScope.doLogin = function ()
	{
		Login.ask(function () {
			$location.path('/');
		});
	};
	
	$rootScope.doLogout = function ()
	{
		
	   $http.post('/endpoint',
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
