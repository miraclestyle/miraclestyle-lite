MainApp.factory('App', ['$rootScope', '$http', '$location', '$modal', 'Endpoint', 
	function ($rootScope, $http, $location, $modal, Endpoint) {
	 
	return {
		list : function ()
		{
			return Endpoint.post('list', 'srv.auth.Domain', {});
		},
		manage : function (app, apps)
	    {
	    	var that = this;
	        	
	    	
			var handle = function (output) {
				 
	      	    if (!app['key']) 
			    app = output.entity;
	  
			    var action = 'create';
			    
			    	
		  	    if (app['key'])
		  	    {
		  	    	
		  	  	 action = 'update';
		  	  	 
		  	    }	
		  	  				 
				var modalInstance = $modal.open({
				      templateUrl: logic_template('srv/auth', 'app_'+(action == 'update' ? 'manage' : 'setup')+'.html'),
				      controller: function ($scope, $modalInstance, RuleEngine) {
				      	 
					  	 $scope.rule = RuleEngine.factory(output);
					  	 $scope.action = action;  
					  	 $scope.app = app;
					  	  
					  	 $parentScope = $scope; 
			  
						 $scope.sudo = function ()
						 {  
						 	
							var handle = function (output) {
				 
								var modalInstance = $modal.open({
								      templateUrl: logic_template('srv/auth', 'app_sudo.html'),
								      windowClass : 'modal-medium',
								      controller: function ($scope, $modalInstance, RuleEngine) {
								      	  
								      	  $scope.rule = RuleEngine(output);
								      	  $scope.log = {
								      	  	'message' : '',
								      	  	'note' : '',
								      	  	'state' : app['state'],
								      	  	'key' : app['key'],
								      	  };
							 
									  	  $scope.save = function ()
									  	  {
									  	  	 
									  	  	Endpoint.post('sudo', 'srv.auth.Domain', $scope.log)
										     .success(function (data) {
 
										     	update(app, data['updated_domain']);
										     	
										     	$parentScope.rule.update(data);
										 
										     	$scope.cancel();
										     	  
											});
						
									  	  }; 
									  	  
										  $scope.cancel = function () {
										    $modalInstance.dismiss();
										  };
									  }
								    });
						  
							  };
							 
							Endpoint.post('read', 'srv.auth.Domain', app).success(handle);
							
						 };
						 
						 $scope._do_user_admin = function (app, action)
						 {  
						 	
							var handle = function (output) {
				 
								var modalInstance = $modal.open({
								      templateUrl: logic_template('srv/auth', 'app_user_admin.html'),
								      windowClass : 'modal-medium',
								      controller: function ($scope, $modalInstance, RuleEngine, $timeout) {
								      	  
								      	  $scope.rule = RuleEngine.factory(output);
								      	  $scope.action = action;
								      	  $scope.log = {
								      	  	'message' : '',
								      	  	'key' : app['key'],
								      	  };
							 
									  	  $scope.save = function ()
									  	  {
									  	  	 
									  	  	Endpoint.post(action, 'srv.auth.Domain', $scope.log)
										     .success(function (data) {
 
										     	update(app, data['updated_domain']);
										     	
										     	$parentScope.rule.update(data);
										 
										     	$scope.cancel();
										     	  
											});
						
									  	  }; 
									  	  
										  $scope.cancel = function () {
										    $modalInstance.dismiss();
										  };
									  }
								    });
						  
							  };
							 
							Endpoint.post('read', 'srv.auth.Domain', app).success(handle);
							
						 };
						 
						 $scope.suspend = function ()
						 {
							this._do_user_admin(app, 'suspend');
						 };
						 
						 $scope.activate = function ()
						 {
							this._do_user_admin(app, 'activate');
						 };
						 
					     $scope.save = function ()
					  	  {
					  	  	 
					  	  	Endpoint.post(action, 'srv.auth.Domain', $scope.app)
						     .success(function (data) {
						     	 if (data['created_domain'])
						     	 {
						     	 	 update($scope.app, data['created_domain']);
						     	 	 apps.unshift($scope.app);
						     	 }
						     	 else
						     	 {
						     	 	 update($scope.app, data['updated_domain']);
						     	 }
								 
								 $scope.rule.update(data);
						 
							});
		
					  	  };
					  	  
						 $scope.cancel = function () {
						    $modalInstance.dismiss('cancel');
						 };
						 
					  }
				    });
		  
			  };
			
			
			Endpoint.post((app['key'] ? 'read' : 'prepare'), 'srv.auth.Domain', app).success(handle);
			
  
	}
	
   };
	 
}])
.controller('AppsPage', ['$scope', 'App', 'apps', 'Confirm', 
	function ($scope, App, apps, Confirm) {
 
	
	$scope.apps = apps;
	
	$scope.toggleMainMenu(1);
	
	$scope.manageApp = function(app)
	{
		 if (!app) app = {};
		 App.manage(app, $scope.apps);
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
