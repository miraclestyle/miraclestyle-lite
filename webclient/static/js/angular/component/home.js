MainApp.controller('HomePage', ['$scope', 'Title', function ($scope, Title) {
 
}])
.run(['$rootScope',
     function ($rootScope) {
	
		$rootScope.toggleMainMenu = function (hide)
		{
			var mm = $('#main-menu');
			
			if (mm.is(':visible') || hide)
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