MainApp
.directive('homepageGrid', ['MAX_GRID_WIDTH', 'MIN_GRID_WIDTH', function(MAX_GRID_WIDTH, MIN_GRID_WIDTH) {
	return {
		link : function (scope, element, attr)
		{
			if (scope.$last)
			{
				
			
			 var resize = function ()
			 {
			 
			 	var wrapper = $(element).parents('.grid-wrapper'); 
				var canvas_width = wrapper.width();
				var calc = calculate_grider(canvas_width, MAX_GRID_WIDTH, MIN_GRID_WIDTH);
				/*
				    values[0] = rounded;
				    values[1] = sides;
				    values[2] = cover_width;
				    values[3] = cover_count;
				 * */
				 
				var r = calc[1] / 2;
				wrapper.css({
					marginRight : r,
					marginLeft : r,
				});
				
				wrapper.find('.grid-item').width(calc[0]).height(calc[0]*1.5);
			 	
			 };
			 
			 resize();
			 
			 $(window).bind('resize', resize);
			 
			 scope.$on('$destroy', function () {
			 	$(window).unbind('resize', resize);
			 });
			 
			 
			
			}
		 
		}
	};
}])
.controller('HomePage', ['$scope', 'Title', 'Endpoint', function ($scope, Title, Endpoint) {
    $scope.catalogs = [];
    Endpoint.post('search', '82').success(function (data) {
    	$scope.catalogs = data.entities;
    });
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