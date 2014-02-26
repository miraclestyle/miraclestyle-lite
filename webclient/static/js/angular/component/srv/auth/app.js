MainApp.factory('App', ['$rootScope', '$http', '$location', '$modal', 'Endpoint', 

	function ($rootScope, $http, $location, $modal, Endpoint) {
	 
	return {
		search : function ()
		{
			return Endpoint.post('apps', 'srv.auth.User', {});
		},
		create : function ()
		{
	    	var that = this;
	        	 
			var handle = function (output) {
 
				var modalInstance = $modal.open({
				      templateUrl: logic_template('srv/auth', 'app_create.html'),
				      controller: function ($scope, $modalInstance, RuleEngine, Confirm) {
				      	 
					  	 $scope.rule = RuleEngine.factory(output);
					  	 $scope.app = {};
					  	 $scope.step = 1;
					  	 $scope.upload_url = output.upload_url;
					   
					  	 
					  	 $scope.nextStep = function(which_step)
					  	 {
					  	 	  $scope.step = which_step;
					  	 };
				 
					     $scope.completed = function (data)
					  	  { 
				  	  		 if (data['entity']){
						     	  	
						     	  Confirm.notice('Your app is now in process of creation, you will recieve an e-mail as soon as the application is created.',
						     	  function ()
						     	  {
						     	  	  $scope.cancel();
						     	  });
					     	  }
					     	  else
					     	  {
					     	  	
					     	  	 Confirm.notice('An error occurred, please try again.', function () {
					     	  	 	  Endpoint.post('prepare', 'srv.auth.Domain',
					     	  	 	      {'upload_url' : Endpoint.url}).success(function (output) {
					     	  	 	  	  
					     	  	 	  	  $scope.upload_url = output.upload_url;
					     	  	 	  });
					     	  	 });
						     	 
					     	  }
		
					  	  };
					  	  
						 $scope.cancel = function () {
						    $modalInstance.dismiss('cancel');
						 };
						 
					  }
				    });
		  
			  };
			 
			Endpoint.post('prepare', 'srv.auth.Domain', {'upload_url' : Endpoint.url}).success(handle);
			 
		},
		update : function (app)
	    {
	    	var that = this;
	        	 
			var handle = function (output) {
	 
				var modalInstance = $modal.open({
				      templateUrl: logic_template('srv/auth', 'app_update.html'),
				      controller: function ($scope, $modalInstance, RuleEngine) {
				      	 
					  	 $scope.rule = RuleEngine.factory(output);
					  	 $scope.app = app;
					  	 $scope.history = {
					  	    'model' : 'srv.auth.Domain',
					  	    'args' : {
					  	    	'key' : app['key'],
					  	    }
					  	 };
	 
					  	 $parentScope = $scope; 
			  
						 $scope.sudo = function ()
						 {   
							var handle = function () {
						 
								var modalInstance = $modal.open({
								      templateUrl: logic_template('admin', 'sudo.html'),
								      windowClass : 'modal-medium',
								      controller: function ($scope, $modalInstance, RuleEngine) {
								      	  
								      	  $scope.rule = $parentScope.rule;
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
 
										     	update(app, data['entity']);
										     	
										     	$scope.rule.update(data);
										 
										     	$scope.cancel();
										     	  
											});
						
									  	  }; 
									  	  
										  $scope.cancel = function () {
										    $modalInstance.dismiss();
										  };
									  }
								    });
						  
							  };
							 
							handle();
						 };
						 
						 $scope._do_user_admin = function (app, action)
						 {  
						 	
							var handle = function () {
				 
								var modalInstance = $modal.open({
								      templateUrl: logic_template('srv/auth', 'app_user_admin.html'),
								      windowClass : 'modal-medium',
								      controller: function ($scope, $modalInstance, RuleEngine, $timeout) {
								      	  
								      	  $scope.rule = $parentScope.rule;
								      	  $scope.action = action;
								      	  $scope.log = {
								      	  	'message' : '',
								      	  	'key' : app['key'],
								      	  };
							 
									  	  $scope.save = function ()
									  	  {
									  	  	 
									  	  	Endpoint.post(action, 'srv.auth.Domain', $scope.log)
										     .success(function (data) {
 
										     	update(app, data['entity']);
										     	
										     	$scope.rule.update(data);
										 
										     	$scope.cancel();
										     	  
											});
						
									  	  }; 
									  	  
										  $scope.cancel = function () {
										    $modalInstance.dismiss();
										  };
									  }
								    });
						  
							  };
							 
							handle();
							
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
					  	  	 
					  	  	Endpoint.post('update', 'srv.auth.Domain', {
					  	  		'name' : $scope.app['name'],
					  	  		'primary_contact' : $scope.app['primary_contact'],
					  	  		'key' : $scope.app['key'],
					  	  	})
						     .success(function (data) {
						     	  
						     	 update($scope.app, data['entity']);
								 
								 $scope.rule.update(data);
						 
							});
		
					  	  };
					  	  
						 $scope.cancel = function () {
						    $modalInstance.dismiss('cancel');
						 };
						 
					  }
				    });
		  
			  };
			 
			Endpoint.post('read', 'srv.auth.Domain', {'key' : app['key']}).success(handle);
			 
	}
	
   };
	 
}])
.controller('AppList', ['$scope', 'App', 'apps', 'Confirm', 'RuleEngine', 'Title',
	function ($scope, App, apps, Confirm, RuleEngine, Title) {
		
	Title.set('Apps');
 
	apps = apps.entities;
 
	angular.forEach(apps, function (app, key) {
		app.domain.rule = RuleEngine.factory({'entity' : app.domain}); // compile rule engine for each domain in the list
		app.user.rule = RuleEngine.factory({'entity' : app.user}); // compile rule engine for each domain user in the list
	});
 
	$scope.apps = apps;
	
	$scope.toggleMainMenu(1);
	
	$scope.updateApp = function(app)
	{
		 App.update(app);
	};
	
	$scope.createApp = function ()
	{
		 App.create();
	};
 
}])
.run(['$rootScope', '$location', 'Account', 
	function ($rootScope, $location, Account) {
 
	 
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
