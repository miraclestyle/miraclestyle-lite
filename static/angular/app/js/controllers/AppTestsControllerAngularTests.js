AppControllers.controller('AppKernelControllerAngularTestsDialog', ['$scope', '$http', 'dialog', function ($scope, $http, dialog){
	 
		  $scope.close = function(result){
		     dialog.close(result);
  
		  };
	}])
  .controller('AppKernelControllerAngularTests', ['$scope', '$dialog', '$http', '$route', '$location', function($scope, $dialog, $http, $route, $location) {
 
  	   
		  var t = '<div class="modal-header">'+
		          '<h3>This is the title</h3>'+
		          '</div>'+
		          '<div class="modal-body">'+
		          '<p>Enter a {{shit}} value to pass to <code>close</code> as the result: <input ng-model="result" /></p>'+
		          '</div>'+
		          '<div class="modal-footer">'+
		          '<button ng-click="close(result)" class="btn btn-primary" >Close</button>'+
		          '</div>';
		
		  $scope.opts = {
		    backdrop: true,
		    keyboard: true,
		    backdropClick: true,
		    template:  t, // OR: templateUrl: 'path/to/view.html',
		    controller: 'AppKernelControllerAngularTestsDialog'
		  };
		  
		  $scope.changeEmail = function(email)
		  {
		  	  $scope.user.email = email;
		  };
		
		  $scope.openDialog = function(){
		  	
		  		$http.get().success(function (a) {
		   
		    	var d = $dialog.dialog($scope.opts);
		    
		    	d.open().then(function(result){
			    if(result)
			      {
			        alert('dialog closed with result: ' + result);
			      }
			    });
			    
			     $scope.shit = a.foo;
			     
		      });	
		      
		     
		  };
		
		  $scope.openMessageBox = function(){
		    var title = 'This is a message box';
		    var msg = 'This is the content of the message box';
		    var btns = [{result:'cancel', label: 'Cancel'}, {result:'ok', label: 'OK', cssClass: 'btn-primary'}];
		
		    $dialog.messageBox(title, msg, btns)
		      .open()
		      .then(function(result){
		        alert('dialog closed with result: ' + result);
		    });
		  };
		  
		  log($scope);
}]);