MainApp.directive('scrollEnd', ['$timeout', '$log', function ($timeout, $log) {
	  return {
	    link : function (scope, element, attrs)
	    {
	    	element = $(element);
	    	
	    	var sensitivity = 20;
	    
	    	var hide_load_more = function () {
	    		var has_vertical_scroll = element.prop('scrollHeight') > element.height();
	    
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
}])
.directive('submitOnChange', ['$parse', function ($parse) {
 
	return {
		
		
        link: function(scope, element, attrs, controller) {
        	
        	var callback = $parse(attrs.submitOnChange);
        	
        	element.bind('change', function () {
        		
        		scope.$apply(function() {
     
			        callback(scope, {'form' : $(element).parents('form:first')});
			    });
			    
        	});
        }
    };
}]).directive('onFinishRender', function ($timeout) {
    return {
        restrict: 'A',
        link: function (scope, element, attr) {
            if (scope.$last === true) {
                $timeout(function () {
                    scope.$emit('ngRepeatFinished');
                });
            }
        }
    };
})
.directive('catalogSliderLoadMore', function () {
	return {
		restrict: 'A',
		link : function (scope, element, attr)
		{
			var scroll = function ()
			{
				var current_scroll = $(this).children(':first').innerWidth()-$(this).scrollLeft();
				
				// this does not work cuz of fucking scrollLeft() bug OR WHATEVER it is - it just plainly does not return the current scroll left properly
			};
			
			$(element).bind('scroll', scroll);
			
			scope.$on('$destroy', function () {
	            	$(element).unbind('scroll', scroll);
	        });
			
		}
	};
})
.directive('catalogSlider', function ($timeout) {
    return {
        restrict: 'A',
        priority : -515,
        link: function (scope, element, attr) {
    	    
           if (scope.$last === true) {
           	
           	    var resize = function ()
           	    {
           	    	 var that = $(element);
				     
				     var h = that.parents('.modal-body').height();
				     
				     var master = that.parents('.overflow-master:first');
				     
				     var w = 0;
	 
				     master.find('.catalog-image-scroll').each(function () {
				     	var img = $(this).find('.img');
				     	img.height(h);
				     	var cw = $(this).data('width'), ch = $(this).data('height');
				     	
				     	var neww = new_width_by_height(cw, ch, h);
				     	
				     	img.width(neww);
				     	
				     	w += neww;
				     });
				 
				     master.width(Math.ceil(w));
           	    };
           	
                $timeout(function () {
			        resize();
	            });
	            
	            $(window).resize(resize);
	            
	            scope.$on('$destroy', function () {
	            	$(window).unbind('resize', resize);
	            });
	          
            }	
        }
    };
})
.directive('toggle', function() {
    return {
        scope: {
            ngModel: '='
        },
        link: function(scope, element, attrs, controller) {
        	
        	var toggle = attrs.toggle;
        	if (!toggle) toggle = 'Yes/No';
        	var splits = toggle.split('/');
 
        	var init = function ()
        	{
        		if (scope.ngModel)
	        	{
	        		element.text(splits[0]);
	        	}
	        	else
	        	{
	        		element.text(splits[1]);
	        	}
        	};
        	
        	init();
        	
            element.bind('click', function() {
                scope.$apply(function() {
                    scope.ngModel = !scope.ngModel;
                    
                    init();
                });
            });
        }
    };
});
