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
.directive('createUploadUrlOnSelect', ['Endpoint', function (Endpoint) {
	return {
		link : function (scope, element, attrs)
		{
			var change = function () {
				
				var that = $(this);
				
				if (!that.val()) return false;
		 
				var options = resolve_defaults({
					'kind' : scope.entity.kind,
					'action' : 'prepare',
					'args' : {},
				}, scope.$eval(attrs.createUploadUrlOnSelect));
			 
				Endpoint.post(options['action'], 
							  options['kind'], 
							  angular.extend({'upload_url' : Endpoint.url}, options['args'])
							 )
							 .success(function (data) {
				        	 	 if ('complete' in options)
				        	 	 options['complete'](data);
			            	});
            };
           
			$(element).on('change', change);
			
			scope.$on('$destroy', function () {
				$(element).off('change', change);
			});
		}
	};
}])
.directive('uploadOnSelect', ['Endpoint', function (Endpoint) {
	return {
		link : function (scope, element, attrs)
		{
			var change = function () {
				
				var that = $(this);
				
				if (!that.val()) return false;
				
				var form = that.parents('[ng-form]:first');
				if (!form.length)
				{
					form = that.parents('form:first');
				}
				var options = resolve_defaults({
					'kind' : scope.entity.kind,
					'action' : 'upload_images',
					'args' : {
						'key' : scope.entity.key,
					},
				}, scope.$eval(attrs.uploadOnSelect));
				 
			 
				Endpoint.post(options['action'], options['kind'], angular.extend({'upload_url' : Endpoint.url}, options['args'])).success(function (data) {
	        	 	form.attr('action', data.upload_url).trigger('submit');
	            });
            
            };
           
			$(element).on('change', change);
			
			scope.$on('$destroy', function () {
				$(element).off('change', change);
			});
		}
	};
}])
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
