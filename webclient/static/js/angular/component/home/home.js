MainApp.config(['$routeProvider',
  function($routeProvider) {
   
    $routeProvider.
      when('/', {
        templateUrl: logic_template('home', 'home.html'),
        controller: 'HomePage'
      });
      
     
}]).controller('HomePage', ['$scope', function ($scope) {
	
}]);