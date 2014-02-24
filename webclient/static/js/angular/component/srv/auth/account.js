login_methods = {
	'1' : 'Google',
	'2' : 'Facebook',
};

MainApp.controller('LoginPage', ['$scope', '$rootScope', '$location', 'Account', function ($scope, $rootScope, $location, Account) {
 
 	if (initdata['user'])
	{
		 $rootScope.current_user = initdata['user'];
	}
		
	if ($rootScope.current_user.is_guest)
	{
		Account.ask_login(function () {
			$location.path('/');
		});
	}
	else
	{ 
		$location.path('/');
	}
}])
.factory('authService', ['$rootScope','httpBuffer', function($rootScope, httpBuffer) {
    return {
      /**
       * Call this function to indicate that authentication was successfull and trigger a
       * retry of all deferred requests.
       * @param data an optional argument to pass on to $broadcast which may be useful for
       * example if you need to pass through details of the user that was logged in
       */
      loginConfirmed: function(data, configUpdater) {
        var updater = configUpdater || function(config) {return config;};
        $rootScope.$broadcast('event:auth-loginConfirmed', data);
        httpBuffer.retryAll(updater);
      },

      /**
       * Call this function to indicate that authentication should not proceed.
       * All deferred requests will be abandoned or rejected (if reason is provided).
       * @param data an optional argument to pass on to $broadcast.
       * @param reason if provided, the requests are rejected; abandoned otherwise.
       */
      loginCancelled: function(data, reason) {
        httpBuffer.rejectAll(reason);
        $rootScope.$broadcast('event:auth-loginCancelled', data);
      }
    };
  }])

  /**
   * $http interceptor.
   * On 401 response (without 'ignoreAuthModule' option) stores the request
   * and broadcasts 'event:angular-auth-loginRequired'.
   */
  .config(['$httpProvider', function($httpProvider) {
    $httpProvider.interceptors.push(['$rootScope', '$q', 'httpBuffer', '$injector', function($rootScope, $q, httpBuffer, $injector) {
      
      var handle_error = function (rejection)
      {
      	  var data = rejection.data;
      	  var Confirm = $injector.get('Confirm');
      	  
          if (!rejection.config.ignoreErrors) {
          	
          	if (rejection.status > 200)
          	{ 
          		Confirm.error500(rejection.data);
          		return $q.reject(rejection);
          	}
          	else
			{
          		if (data && data['errors'] && data['errors']['action_denied'])
          		{
          			Confirm.action_denied(rejection.data);
          			return $q.reject(rejection);
          		}
          	}
            
          }
          // otherwise, default behaviour
          return rejection || $q.when(rejection);
          
      };
      
      return {
      	response : handle_error,
        responseError: handle_error
      };
    }]);
    
  }])
  .factory('httpBuffer', ['$injector', function($injector) {
    /** Holds all the requests, so they can be re-requested in future. */
    var buffer = [];

    /** Service initialized later because of circular dependency problem. */
    var $http;

    function retryHttpRequest(config, deferred) {
      function successCallback(response) {
        deferred.resolve(response);
      }
      function errorCallback(response) {
        deferred.reject(response);
      }
      $http = $http || $injector.get('$http');
      $http(config).then(successCallback, errorCallback);
    }

    return {
      /**
       * Appends HTTP request configuration object with deferred response attached to buffer.
       */
      append: function(config, deferred) {
        buffer.push({
          config: config,
          deferred: deferred
        });
      },

      /**
       * Abandon or reject (if reason provided) all the buffered requests.
       */
      rejectAll: function(reason) {
        if (reason) {
          for (var i = 0; i < buffer.length; ++i) {
            buffer[i].deferred.reject(reason);
          }
        }
        buffer = [];
      },

      /**
       * Retries all the buffered requests clears the buffer.
       */
      retryAll: function(updater) {
        for (var i = 0; i < buffer.length; ++i) {
          retryHttpRequest(updater(buffer[i].config), buffer[i].deferred);
        }
        buffer = [];
      }
    };
}])
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
					  	  
					  	  $scope.apps = [{
					  	  	  name : 'Armani',
					  	  	  state : 'accepted',
					  	  }, {
					  	  	  name : 'Gucci',
					  	  	  state : 'invited',
					  	  }];
					  	  
					  	  $scope.removeFromApp = function(app)
					  	  {
					  	  	   app.state = 'removed';
					  	  };
					  	  
					  	  $scope.acceptApp = function (app)
					  	  {
					  	  	  app.state = 'accepted';
					  	  };
					  	  
					  	  $scope.declineApp = function(app)
					  	  {
					  	  	  app.state = 'declined';
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
