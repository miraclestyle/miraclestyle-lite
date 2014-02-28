MainApp.directive('scrollEnd', ['$timeout', '$log', function ($timeout, $log) {
	  return {
	    link : function (scope, element, attrs)
	    {
	    	element = $(element);
	    	
	    	var sensitivity = 20;
	    
	    	var hide_load_more = function () {
	    		var has_vertical_scroll = element.prop('scrollHeight') > element.height();
	    		
	    		$log.debug(element.prop('scrollHeight'), element.height());
	     
	    		if (has_vertical_scroll)
	    		{
	    			element.find('.load-more').css('visibility', 'hidden');
	    		}
	    		else
	    		{
	    			element.find('.load-more').css('visibility', 'visible');;
	    		}
	    	};
	    	
	    	$timeout(function () {
	    		hide_load_more();
	    	});
	    	
	    	$(window).on('resize', hide_load_more);
	    	
	    	var scroller = function () {
	    		
	    		 var el = $(this);
	    		
	    		 var scrollTop = el.scrollTop(), 
	    		     scrollHeight = el.prop('scrollHeight'), 
	    		     thisHeight = el.height();
	    		     
	    		 var total = (scrollHeight - scrollTop) - thisHeight;
	    		 
	    		 if (total < sensitivity)
	    		 {
	    		 	scope.$broadcast('scrollEnd', el);
	    		 	 
	    		 }
	    	};
	    	
	    	element.on('scroll', scroller);
	    	
	    	scope.$on('$destroy', function () {
	    		
	    		element.off('scroll', scroller);
	    		$(window).off('resize', hide_load_more);
	    		
	    	});
	    }
	  };
}]);
