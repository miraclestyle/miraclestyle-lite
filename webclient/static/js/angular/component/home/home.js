MainApp.config(['$routeProvider',
  function($routeProvider) {
   
    $routeProvider.
      when('/', {
        templateUrl: logic_template('home', 'home.html'),
        controller: 'HomePage'
      });
      
     
}]).controller('HomePage', ['$scope', function ($scope) {
	
}])
.run(['$rootScope',
     function ($rootScope) {
	
	$rootScope.toggleMainMenu = function ()
	{
		var mm = $('#main-menu');
		
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
				height : ($(window).height() - $('#top-bar').height()) + 'px',
			}, 400, function () {
				
			});
		}
	};
	 
}]);