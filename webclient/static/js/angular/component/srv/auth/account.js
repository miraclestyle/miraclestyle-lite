login_methods = {
	'1' : 'Google',
	'2' : 'Facebook',
};

MainApp
.factory('Account', ['$rootScope', '$http', '$location', '$modal', 'Endpoint', 
	function ($rootScope, $http, $location, $modal, Endpoint) {
	 
	return {
		
		logout : function (on_logout)
		{
			Endpoint.post('logout', 'srv.auth.User',
		     {
		   	   'csrf' : $rootScope.current_user.csrf,
		     })
		     .success(function (data) {
				 $rootScope.current_user = data.anonymous_user;
				 
				 if (angular.isFunction(on_logout))
				 on_logout();
				 
				 $rootScope.toggleMainMenu();
			});
		},
		ask_login : function (on_close)
		{
 
			var handle = function (output) {
 
				var modalInstance = $modal.open({
				      templateUrl: logic_template('srv/auth', 'login.html'),
				      controller: function ($scope, $modalInstance, data) {
						  
						  $scope.data = data;
						  
						  $scope.login_methods = login_methods;
					  
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
		 
					    }, function () {
			 			 
			 			 if (angular.isFunction(on_close)) on_close();
				    });
				 
			  };
			
			$http.get('/login/google').success(handle);			
		},
		manage : function ()
	    {
 
			var handle = function () {
 
				var modalInstance = $modal.open({
				      templateUrl: logic_template('srv/auth', 'account.html'),
				      controller: function ($scope, $modalInstance) {
			 
					  	  $scope.identiy_info = function (i)
					  	  {
					  	  		var info = i.split('-');
					  	  		
					  	  		return login_methods[info[1]];
					  	  };
					  	   
					  	  $scope.disAssociate = function(ident)
					  	  {
					  	  	 
					  	  	  angular.forEach($rootScope.current_user.identities, function (value) {
					  	  	  	   if (value.identity == ident)
					  	  	  	   {
					  	  	  	   	   value.associated = !value.associated;
					  	  	  	   	 
 					  	  	  	   }
					  	  	  });
			 
					  	  };
				 
					  	  $scope.save = function ()
					  	  {
					  	  	var disassociated = [];
					  	  	
					  	  	angular.forEach($rootScope.current_user.identities, function (value) {
					  	  	  	 
					  	  	  	   	   if (!value.associated)
					  	  	  	   	   {
					  	  	  	   	   	  disassociated.push(value.identity);
					  	  	  	   	   }
					  	  	  	   
					  	  	  });
					  	  	
					  	  	Endpoint.post('update', 'srv.auth.User', {
					  	  		primary_email : $rootScope.current_user.primary_email,
					  	  		disassociate : disassociated,
					  	  	})
						     .success(function (data) {
								 $rootScope.current_user = data.updated_user;
							});
		
					  	  };
					  	  
						  $scope.cancel = function () {
						    $modalInstance.dismiss('cancel');
						  };
					  }
				    });
		  
			  };
			
			handle();
  
	}
	
   };
	 
}])
.run(['$rootScope', '$location', 'Account', 
	function ($rootScope, $location, Account) {
	 
	$rootScope.manageAccount = function ()
	{
  		 Account.manage();
	};
	 
    $rootScope.doLogin = function ()
	{
		Account.ask_login(function () {
			$location.path('/');
		});
	};
	
	$rootScope.doLogout = function ()
	{
		
	   Account.logout(function () {
			$location.path('/');
		});
		
	};
	 
}]);
