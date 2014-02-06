ngtemplate_path = '/static/js/lib/angular/ui/template/';
nglogic_template_path = '/static/js/app/template/';

function logic_template(file)
{
	return nglogic_template_path + file;
}
function ui_template(file)
{
	return ngtemplate_path + file;
}

angular.module('app.ui',
	  [
	   'app.ui.transition', 
	   'app.ui.collapse', 
	   'app.ui.accordion',
	   'app.ui.modal',
	   'app.ui.dropdown',
	   'app.ui.select2',
	  ]
);

angular.module('MainApp', ['ngRoute', 'app.ui'])
.config(['$routeProvider',
  function($routeProvider) {
    $routeProvider.
      when('/', {
        templateUrl: logic_template('home.html'),
        controller: 'Login'
      }).
      when('/login', {
        controller: 'Login'
      });
}])
.controller('HomePage', ['$scope', '$log', function ($scope, $log) {
	$log.debug('Ey man');
}])
.controller('Login', ['$scope', '$http', '$log', '$modal', function ($scope, $http, $log, $modal) {
	 
	$http.get('/login/google?force_ajax=1').success(function (data) {
		
		$log.debug(data);
		
		var modalInstance = $modal.open({
		      templateUrl: logic_template('login.html'),
		      controller: function ($scope, $modalInstance, items) {
				 
				  $scope.login = function () {
				    $modalInstance.close('closed');
				  };
				
				  $scope.cancel = function () {
				    $modalInstance.dismiss('cancel');
				  };
			  },
		      resolve: {
		        items: function () {
		          return $scope.items;
		        }
		      }
		    });
		    
		 modalInstance.result.then(function (message) {
		      $log.debug(message);
		    }, function () {
		      $log.info(args);
		 });
		 
	  });
 
	
}]);