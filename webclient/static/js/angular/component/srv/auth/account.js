MainApp.config(['$routeProvider',
  function($routeProvider) {
   
    $routeProvider.
      when('/manage_account', {
      	 controller: 'ManageAccount',
      	 templateUrl : logic_template('srv/auth', 'account.html'),
      	 resolve : {
      	 	// promise example
      	 	registered : ['$http', function ($http) {
      	 		return $http.get('/endpoint?action_model=srv.auth.User&action_key=account_manage').then(function (xhr) {
			  	    return xhr.data.data.registered;
			   });
      	 	}]
      	 }
      });
     
}])
.controller('ManageAccount', ['$scope', '$log', '$http', 'registered', function ($scope, $log, $http, registered) {
	
 
	  $scope.user = current_user;
	  $scope.user.registered = registered;
	  $scope.save = function ()
	  {
	  	   $log.info('Save called');
	  };
}]);