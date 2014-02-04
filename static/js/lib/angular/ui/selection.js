angular.module('app.ui.selection', ['app.ui.transition'])
  .controller('SelectionController', ['$scope', '$log', '$attrs', function ($scope, $log, $attrs) {
  	  $log.debug($attrs, $scope);
  	  
  	  $scope.openOptions = function ()
  	  {
  	  	 alert('I would if i could...');
  	  };
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
	    },
 
      link: function (scope, element, attrs) {
  			
        var options = attrs.options;
         
        $log.debug(scope); 
        $log.debug(options);
        
      }
    };
}]);