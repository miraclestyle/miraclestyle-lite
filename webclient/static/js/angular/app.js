angular.module('app.ui',
	  [
	   'app.ui.transition',
	   'app.ui.collapse', 
	   'app.ui.accordion',
	   'app.ui.modal',
	   'app.ui.select2',
	  ]
);

var MainApp = angular.module('MainApp', ['ui.router', 'ngBusy', 'ngStorage', 'checklist-model', 'app.ui'])
.config(['$httpProvider', '$locationProvider',
  function($httpProvider, $locationProvider) {
   
     $httpProvider.defaults.headers.common['X-Requested-With'] = 'XmlHttpRequest';
 
     $locationProvider.hashPrefix('!');
     
	 $locationProvider.html5Mode(true);
     
}])
.factory('RuleEngine', function () {
	
	function RuleEngine(data)
	{
		var that = this;
		
		this.executable = {};
		this.required = {};
	    this.invisible = {};
		this.writable = {};
		this.arguments = {};
		
		this._action_permission_translate = function (action_name)
		{
			return this._rule_action_permissions[this._rule_actions[action_name]['key']];
		};
 
		this._check_field = function (name, what)
	    {
	    	return this._rule_field_permissions[name][what];
	    };
	    
		this._writable = function (name)
	    {
	    	return this._check_field(name, 'writable');
	    };
	    
		this._invisible = function (name)
	    {
	    	return this._check_field(name, 'invisible');
	    };
	    
		this._required = function (name)
	    {
	    	return this._check_field(name, 'required');
	    };
		
		this._executable = function (action_name)
	    {
	    	var gets = this._action_permission_translate(action_name);
	    	
	    	return gets['executable'];
	    };		
		
		this.init = function ()
		{
	        angular.forEach(this._rule_actions, function (value, key) {
		    	that.executable[key] = that._executable(key);
		    	
		    	angular.forEach(value.arguments, function (argument_value, argument_key) {
		    		if (!that.arguments[key]) that.arguments[key] = {};
		    		
		    		that.arguments[key][argument_key] = argument_value;
		    	});
		    	
		    });
		    
		    angular.forEach(this._rule_field_permissions, function (value, key) {
		    	
		    	that.required[key] = that._required(key);
		    	that.writable[key] = that._writable(key);
		    	that.invisible[key] = that._invisible(key);
		    	
		    });
	    };
		
		this.update = function (info)
	    {
			
			this._rule = info['rule'];
			this._rule_action_permissions = this._rule['entity']['_action_permissions'];
			this._rule_field_permissions = this._rule['entity']['_field_permissions'];
			this._rule_actions = this._rule['entity']['_actions'];
			 
			this.init();
			
			
			 
		};
		
		if (data && data['rule'])
		{
			this.update(data);
	    }

		      
		}
  
	
	return {
		factory : function (data) {
			return new RuleEngine(data);
		}
	};
	  
})
.factory('Confirm', ['$modal', function ($modal) {
	
    var Confirm = function(options)
    {
    	 if (!options) options = {};
    	 
    	 var defaults = {
    	 	text : {
    	 		Yes : 'Yes',
    	 		No : 'No',
    	 	},
    	 	message : 'Are you sure you want to proceed with this action?',
    	 	templateUrl : logic_template('opt/misc', 'basic_confirm.html'),
    	 	windowClass : 'modal-small',
    	 	controller: function ($scope, $modalInstance) {
						  
				  $scope.data = options;
 
 				  $scope.yes = function (){
 				  	$modalInstance.dismiss('Yes');
 				  };
 				  
				  $scope.no = function () {
				    $modalInstance.dismiss('No');
				  };
			},
    	 	
    	 };
    	 
    	 options = angular.extend(defaults, options);
    	 
    	 var modalInstance = $modal.open(options);
    	  
    	 modalInstance.result.then(function close(what) {
 
		   }, function dismiss(what) {
 
			    if (angular.isFunction(options[what])) options[what]();
		   });
    };
	
	return {
		sure : function (options) {
			
			Confirm(options);
		},
		change : function (options) {
			
			Confirm(options);
		},
		
	};
}])
.factory('Endpoint', ['$http', function ($http) {
	
	var _compile = function(action, model, data, config)
	{
		 if (!config) config = {};
			
		 return [angular.extend({
				action_model : model,
				action_key : action,
			}, data), config];
		
	};
	
	return {
		post : function(action, model, data, config)
		{
		    compiled = _compile(action, model, data, config);
			
			return $http.post('/endpoint', compiled[0], compiled[1]);
		},
		get : function(action, model, data, config)
		{
		    compiled = _compile(action, model, data, config);
		    
		    compiled[1]['params'] = $.param(compiled[0]);
			
			return $http.get('/endpoint', compiled[1]);
		},
	};
}])
.run(function ($rootScope) {
    
    $rootScope.current_user = current_user;
});