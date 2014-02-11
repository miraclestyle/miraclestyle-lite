MainApp.run(['$rootScope',  '$http', '$location', '$modal', function ($rootScope, $http, $location, $modal) {
	
	$rootScope.makeNewDialog = function ()
	{
		$rootScope.manageAccount();
	};
	
	$rootScope.manageAccount = function ()
	{
		
		$rootScope.loading = true;
	
			var handle = function () {
				
				$rootScope.loading = false;
				  
				var modalInstance = $modal.open({
				      templateUrl: logic_template('srv/auth', 'account_accordion.html'),
				      controller: function ($scope, $modalInstance) {
				  
					  	  $scope.user = current_user;
					  	  $scope.identiy_info = {
					  	  	get : function (i)
					  	  	{
					  	  		var info = i.split('-');
					  	  		
					  	  		return login_methods[info[1]];
					  	  	}
					  	  };
					  	   
					  	  $scope.disAssociate = function(ident)
					  	  {
					  	  	 
					  	  	  angular.forEach($scope.user.identities, function (value) {
					  	  	  	   if (value.identity == ident)
					  	  	  	   {
					  	  	  	   	   value.associated = !value.associated;
					  	  	  	   	 
 					  	  	  	   }
					  	  	  });
					  	  };
				 
					  	  $scope.save = function ()
					  	  {
					  	  	var disassociated = [];
					  	  	
					  	  	angular.forEach($scope.user.identities, function (value) {
					  	  	  	 
					  	  	  	   	   if (!value.associated)
					  	  	  	   	   {
					  	  	  	   	   	  disassociated.push(value.identity);
					  	  	  	   	   }
					  	  	  	   
					  	  	  });
					  	  	
					  	  	$http.post('/endpoint', {
					  	  		primary_email : $scope.user.primary_email,
					  	  		disassociate : disassociated,
					  	  		action_model : 'srv.auth.User',
					  	  	    action_key : 'update',
					  	  	})
						     .success(function (data) {
								 $rootScope.current_user = $scope.user = data.updated_user;
							});
		
					  	  };
					  	  
						  $scope.cancel = function () {
						    $modalInstance.dismiss('cancel');
						  };
					  }
				    });
				    
					modalInstance.result.then(function (message) {
					     
					    }, function () {
			 			 
				    });
				 
			  };
			
			//handle();
			
			$http.get('/').success(handle);
		
	};
	 
}]);
