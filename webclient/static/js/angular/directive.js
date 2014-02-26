MainApp.directive('scrollEnd', function () {
	  return {
	    restrict:'EA',
	    link : function (scope, element)
	    {
	    	element = $(element);
	    	
	    	var sensitivity = 20;
	    	
	    	element.on('scroll', function () {
	    		
	    		 var el = $(this);
	    		
	    		 var scrollTop = el.scrollTop(), 
	    		     scrollHeight = el.prop('scrollHeight'), 
	    		     thisHeight = el.height();
	    		     
	    		 var total = (scrollHeight - scrollTop) - thisHeight;
	    		 
	    		 if (total < sensitivity)
	    		 {
	    		 	scope.$broadcast('scrollEnd', el);
	    
	    		 }
	    	});
	    }
	  };
});
