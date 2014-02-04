angular.module('app.ui.selection', ['app.ui.transition'])
  .controller('SelectionController', ['$scope', '$log', '$attrs', function ($scope, $log, $attrs) {
 	
  	  
  }])
  .directive('selection', ['$log', '$transition', function ($log, $transition) {
    return {
 
	  restrict:'EA',
	  controller:'SelectionController',
	  transclude: true,
	  templateUrl: ngtemplate_path + 'template/selection/selection.html',
	  
	   scope: {
	      label: '@',               // Interpolate the heading attribute onto this scope
	      isMultiple: '=?',
	      name : '@'
	    },
 
      link: function (scope, element, attrs) {
   
        scope.options = scope.$eval(attrs.options);
        scope.selectedOption = null;
        
        var init_label = scope.label;
        
        scope.active = attrs.active;
        scope.name = attrs.name;
      
        scope.opened = false;
        
	    scope.openOptions = function ()
	    {
	  	  	 scope.opened = !scope.opened;
	    };
	    
	    scope.selectOption = function (option)
	    {
	    	scope.active = option.value;
	    	scope.selectedOption = option;
	    	
	    	scope.label = option.label;
	    	
	    	scope.openOptions();
	    	
	    	return false;
	    };
        
      }
    };
}]);