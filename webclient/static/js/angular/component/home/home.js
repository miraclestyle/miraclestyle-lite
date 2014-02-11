login_methods = {
	'1' : 'Google',
	'2' : 'Facebook',
};


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
.run(['$rootScope',
     function ($rootScope) {
	
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
	 
}]);