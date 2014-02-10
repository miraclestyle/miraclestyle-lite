MainApp.config(['$routeProvider',
  function($routeProvider) {
   
    $routeProvider.
      when('/manage_account', {
      	 controller: 'ManageAccount',
      	 templateUrl : logic_template('srv/auth', 'account.html'),
 
      });
     
}])
.controller('ManageAccount', ['$scope', '$log', '$http', function ($scope, $log, $http) {
	 
	  $scope.user = current_user;
	  $scope.save = function ()
	  {
	  	   $log.info('Save called');
	  };
}]);