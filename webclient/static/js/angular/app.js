
angular.module('app.ui',
	  [
	   'app.ui.transition',
	   'app.ui.collapse', 
	   'app.ui.accordion',
	   'app.ui.modal',
	   'app.ui.select2',
	   'app.ui.position',
	   'app.ui.datepicker',
	   'app.ui.sortable',
	   
	  ]
);

var MainApp = angular.module('MainApp', ['ui.router', 'ngBusy', 'ngSanitize', 'ngUpload', 'ngStorage', 'checklist-model', 'app.ui'])
.config(['$httpProvider', '$locationProvider',
  function($httpProvider, $locationProvider) {
  	 
     $httpProvider.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';
  
     $locationProvider.hashPrefix('!');
     
	 $locationProvider.html5Mode(true);
     
}])
.factory('RuleEngine', function () {
	
	function RuleEngine(data)
	{
		var that = this;
 
		this.action = {};
		this.input = {};
		
		this.toJSON = function()
		{
			return {};
		};
  
		this._action_permission_translate = function (action_name)
		{
			return this._rule_action_permissions[this._rule_actions[action_name]['key']];
		};
 
		this._check_field = function (name, what)
	    {
	    	return this._rule_field_permissions[name][what];
	    };
	 
		this._executable = function (action_name)
	    {
	    	var gets = this._action_permission_translate(action_name);
	    	
	    	return gets['executable'];
	    };		
		
		this.init = function ()
		{
	        angular.forEach(this._rule_actions, function (value, key) {
	        	
	        	if (!that.action[key])
	        	{
	        		that.action[key] = {};
	        	}
	        	
		    	that.action[key]['executable'] = that._executable(key);
		    	
		    	angular.forEach(value.arguments, function (argument_value, argument_key) {
		    		if (!that.input[key]) that.input[key] = {};
		    		
		    		that.input[key][argument_key] = argument_value;
		    	});
		    	
		    });
		    
		    that.field = that._rule_field_permissions;
		  
	    };
		
		this.update = function (info)
	    {
	    	
	    	if (!info || !info['_action_permissions'])
	    	{
	    		return;
	    	}
	    	
	    	var kind_info = KINDS.get(info['kind']);
	  
			this._rule_action_permissions = info['_action_permissions'];
			this._rule_field_permissions = info['_field_permissions'];
			this._rule_actions = kind_info['actions'];
			 
			this.init();
			
			
			 
		};
	
		if ((data && data['_action_permissions']))
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
    	 	templateUrl : logic_template('misc/basic_confirm.html'),
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
			
			callbacks : {Yes : angular.noop, No : angular.noop}
    	 	
    	 };
    	 
    	 options =  resolve_defaults(defaults, options);
  
    	 var modalInstance = $modal.open(options);
    	  
    	 modalInstance.result.then(function close(what) {
 
		   }, function dismiss(what) {
 
			    if (angular.isFunction(options['callbacks'][what]))
			    {
			    	options['callbacks'][what]();
			    }
			    else if (angular.isFunction(options['callbacks']['Default']))
			    {
			    	options['callbacks']['Default']();
			    }
			     
		   });
		   
		 return modalInstance;
    };
	
	return {
		notice : function (message, ok, options)
		{
			var defaults = {
				message : message,
				callbacks : {
					Yes : ok,
					Default : ok,
				},
				text : {
					Yes : 'Close',
				}
			};
			
			options = angular.extend(defaults, options);
			
			return Confirm(options);
		},
		sure : function (yes, no, options) {
			
			var defaults = {
				message : 'Are you sure you want to proceed with this action?',
				callbacks : {
					Yes : yes,
					No : no,
				},
				text : {
					Yes : 'Yes',
					No : 'No',
				}
			};
			
			options = angular.extend(defaults, options);
			
			return Confirm(options);
			
		},
		error500 : function (output, options)
		{
			var defaults = {
				message : output,
				templateUrl : logic_template('misc/error500.html'),
				windowClass : '',
				text : {
					Yes : 'Close',
				}
			};
			
			options = angular.extend(defaults, options);
			
			return Confirm(options);
		},
		
		action_denied : function (output, options)
		{
			var defaults = {
				message : 'You do not have permission to perform this action.',
				templateUrl : logic_template('misc/action_denied.html'),
				text : {
					Yes : 'Ok',
				}
			};
			
			options = angular.extend(defaults, options);
			
			return Confirm(options);
		},
		
		changes : function (ok, no, options) {
			
			var defaults = {
				message : 'Do you want to save your changes before leaving?',
				callbacks : {
					Yes : ok,
					No : no,
				},
				text : {
					Yes : 'Yes',
					No : 'No',
				}
			};
			
			options = angular.extend(defaults, options);
			
			return Confirm(options);
		},
		
	};
}])
.factory('Endpoint', ['$http', function ($http) {
	
	
	var endpoint_url = '/endpoint';
	
	var _compile = function(action, model, data, config)
	{
		 config = always_object(config);
		 data = always_object(data);
			
		 return [angular.extend({
				action_model : model,
				action_key : action,
			}, data), config];
		
	};
	
	return {
		url : endpoint_url,
		post : function(action, model, data, config)
		{
		    compiled = _compile(action, model, data, config);
			
			return $http.post(endpoint_url, compiled[0], compiled[1]);
		},
		get : function(action, model, data, config)
		{
		    compiled = _compile(action, model, data, config);
		    
		    compiled[1]['params'] = $.param(compiled[0]);
			
			return $http.get(endpoint_url, compiled[1]);
		},
	};
}])
.factory('Title', ['$rootScope', function ($rootScope) {
	
	var suffix = 'MIRACLESTYLE', titles = [];
 
	$rootScope.pageTitle = '';
	
	var _compile = function (title_to_compile)
	{
 
		title_to_compile.push(suffix);
		
		return title_to_compile.join(' - ');
	};
	
	return {
		set : function (title)
		{
		   $rootScope.pageTitle = _compile(angular.isArray(title) ? title : [title]);
		   
		   return this;
		},
		append : function (title) {
 
		   if (angular.isArray(title))
		   {
		   	  angular.forEach(title, function (a) {
		   	  	  titles.push(a);
		   	  });
		   }
		   else
		   {
		   	  titles.push(title);
		   } 	
		     
		   return this;
			
		},
		prepend : function (title) {
			
		   if (angular.isArray(title))
		   {
		   	  angular.forEach(title, function (a) {
		   	  	  titles.unshift(a);
		   	  });
		   }
		   else
		   {
		   	  titles.unshift(title);
		   } 	
		 	
			
			return this;
		},
		reset : function()
		{
			titles = [];
			
			$rootScope.pageTitle = _compile([]);
			
			return this;
		},
		finalize : function ()
		{
 
			$rootScope.pageTitle = _compile(titles);
			
			return this;
		}
	};
}])
.controller('HandleLog', ['$scope', 'Endpoint', '$timeout', function ($scope, Endpoint, $timeout) {
	
	
	if (!$scope.history) return false;
 
    $scope.logs = [];
    $scope.history.args.more = true;
    
	$scope.commander = {'isOpen' : false, 'first' : false, 'loading' : false};
	  
	var loadMore = function (that)
	{ 
			if (!$scope.commander.loading && $scope.history.args.more)
			{
				$scope.commander.loading = true;
				
				Endpoint.post('read_records', $scope.history.kind, $scope.history.args).success(function (data) {
					
					$scope.commander.first = true;
				 
					angular.forEach(data.entity._records, function (value) {
					     $scope.logs.push(value);
					});
 
					$scope.history.args.next_cursor = data.next_cursor;
					$scope.history.args.more = data.more;
					 
					$scope.commander.loading = false;
			 
					$timeout(function () {
						$(window).trigger('resize');
					});
					
				});		
		 
		}		
		
	};
	
	$scope.loadMore = loadMore;
	 
	$scope.$on('scrollEnd', function (that) {
		
		if ($scope.commander.isOpen)
		{
			loadMore(that);
		}
 		
	});
	
	$scope.$watch('commander.isOpen', function (isOpen) {
	
		if (isOpen && !$scope.commander.first)
		{
			loadMore();
		}  
	});
}])
.factory('EntityEditor', ['$rootScope', '$modal', '$timeout', 'Endpoint', 'Confirm',

    function ($rootScope, $modal, $timeout, Endpoint, Confirm) {
    	
    	var defaults = {
    		'scope' : {},
    		'entity' : {},
    		'close' : true,
    		'complete' : angular.noop,
    		'handle' : angular.noop,
    		'cancel' : angular.noop,
    		'dismiss' : true,
    		'confirm_options' : {},
    		'message_success' : 'Successfully deleted!',
    		'templateUrl' : '',
    		'args' : {},
    		'kind' : '',
    	};
    	
    	var resolveOptions = function (options)
    	{
    		options = resolve_defaults(defaults, options);
    		
    		var functs = ['complete', 'handle', 'cancel'];
    		
    		angular.forEach(functs, function (value) {
    			 if (!angular.isFunction(options[value]))
    			 {
    			 	options[value] = angular.noop;
    			 }
    		});
    		
    		return options;
    	};

        return {
        	update_entity : function ($scope, data)
        	{
        		update($scope.entity, data['entity']);
        		
        		if ('live_entity' in $scope)
        		{
        			update($scope.live_entity, data['entity']);
        		}
        		
        		if ('entity' in $scope)
        		{
        			update($scope.entity, data['entity']);
        		}
        	    
        	    if ('rule' in $scope)
        	    {
        	    	$scope.rule.update(data['entity']);
        	    }
        		 
        		if ('rule' in $scope.live_entity)
        		{
        			$scope.live_entity.rule.update(data['entity']);
        		}
        		
        		if ('rule' in $scope.entity)
        		{
        			$scope.entity.rule.update(data['entity']);
        		}
        	},
            create: function (options) {
            
                return this.manage(true, options);
                
            },
            remove : function (options)
            {
             
             	options = resolveOptions(options);
             	var action = 'delete';
             	
             	if (options['action']) action = options['action'];
             	
             	var confirm_defaults = {
					message : 'Are you sure you want to proceed with this action?',
					callbacks : {
						Yes : function () {
            		
		            		 Endpoint.post(action, options['kind'], options['entity']).success(function (data) {
			            		if (data['entity'])
			            		{
			            			var modal = Confirm.notice(options['message_success'], options['complete']);
			            			
			            			if (options['dismiss'])
			            			{
			            				$timeout(function () {
			      							try
			      							{
			      								modal.dismiss();
			      								
			      							}catch(e) {}
				            				
				            			}, 1500);
			            			}
			            			
			            		}
			            	});
		            	},
			 
					},
				 
				};
				
				angular.extend(confirm_defaults, options['confirm_options']);
			 
                Confirm.sure(null, null, confirm_defaults);
            	 
            },
            update: function (options)
            {
            	return this.manage(false, options);
            },
            manage: function (create, options) {
            	
            	options = resolveOptions(options);
            	
                var that = this;
                 
                var action = 'update';
                var action2 = 'read';
                var args = {};
           
                if (create)
                {	
                	action = 'create';
                	action2 = 'prepare';
                }
                
                if ('action' in options) action = options['action'];
                if ('action2' in options) action2 = options['action2'];
                
                args = options['args'];
            
                var handle = function (data) {

                    var modalInstance = $modal.open({
                        templateUrl: options['templateUrl'],
                        controller: function ($scope, $modalInstance, RuleEngine) {
                        	
                        	var entity = options['entity'];
                        	
                        	update(entity, data['entity']);
                        	
                        	$scope.options = options;
                        	 
 							$scope.rule = RuleEngine.factory(data['entity']);
 							$scope.live_entity = entity;
                            $scope.entity = angular.copy(entity);
                            $scope.action = action;
                            $scope.action2 = action2;
                            
                            if (!create)
                            {
                            	$scope.history = {
	                            	'kind' : entity['kind'],
	                            	'args' : {
	                            		'key' : entity['key'],
	                            	}
	                            };
                            }
                            
                            
                            $scope.resolve_handle = options['handle'];
                            $scope.resolve_complete = options['complete'];
                            $scope.resolve_cancel = options['cancel'];
                              
                            $scope.save = function () {
 
                                Endpoint.post(action, options['kind'], $scope.entity)
                                .success(function (data) {

                                        that.update_entity($scope, data);
                                        
                                        $scope.resolve_complete(entity);
                                        
                                        if (options['close'])
                                        {
                                        	$scope.cancel();
                                        } 
                                         
                                });
                            };
 
                            update($scope, options['scope']);
                            
                            $scope.resolve_handle(data);
                             
                            $scope.cancel = function () {
                            	
                            	$scope.resolve_cancel($modalInstance);
                                $modalInstance.dismiss('cancel');
                            };

                        }
                    });

                };
                
                if ('data' in options)
                {
                	handle(options['data']);
                }
                else
                {
                	Endpoint.post(action2, options['kind'], args).success(handle);
                }
                 
            }

        };

    }
])
.run(['$rootScope', '$state', 'Title', function ($rootScope, $state, Title) {
    
    $rootScope.ADMIN_KINDS = {
    	'0' : 'Users',
    	'6' : 'Apps',
    }; 
   
    $rootScope.FRIENDLY_KIND_NAMES = FRIENDLY_KIND_NAMES;
    $rootScope.current_user = current_user;
    $rootScope.$state = $state;
    $rootScope.ui_template = ui_template;
    $rootScope.logic_template = logic_template;
    $rootScope.DATE_FULL = "yyyy-MM-dd HH:mm:ss Z";
    $rootScope.JSON = JSON;
    $rootScope.search = {
    	'kind' : null,
    	'hide' : false,
    	'filters' : {},
    	'order_by' : {},
    	'indexes' : [],
    	'resetFilters' : function ()
    	{
    		this.send.filters = [];
    		this.send.order_by = {};
    	},
    	'changeKind' : function ()
    	{
    	 
    		var kindinfo = KINDS.get(this.kind);
    		if (kindinfo)
    		{
    			var search_argument = null;
    			
    			try
    			{
    				search_argument = kindinfo.actions['search']['arguments']['search'];	
    			}
    			catch(e){}
    			
    			if (!search_argument)
    			{
    				this.hide = true;
    				search_argument = {};
    			}
    			else
    			{
    				this.hide = false;
    			}
    			
    			this.filters = search_argument['filters'] || {};
    			this.order_by = search_argument['order_by'] || {};
    			this.indexes = search_argument['indexes'] || [];
    		 
    		}
    		
    	},
    	'removeFilter' : function(filter)
    	{
    		this.send.filters.remove(filter);
    	},
    	'makeComposites' : function ()
    	{
    		var fields = [];
 
    		angular.forEach(this.filters, function (value) {
    			fields.push(value.field);
    		});
    		
    		return fields;
    	},
    	'newFilter' : function ()
    	{
    		var fields = this.makeComposites();
    		var order_by = this.send.order_by;
     
    		angular.forEach(this.indexes, function (value) {
    			 
    		});
    		
    		this.send.filters.push({
    			'field' : '',
    			'operator' : '',
    			'value' : '',
    		});
    	},
    	'setSearch' : function (kind, search)
    	{
    		 
    		if (kind == undefined || kind == null)
    		{
    			this.hide = true;
    			return;
    			
    		}
    		if (this.kind != kind)
        	{
        	 	this.kind = kind;
        	 	this.changeKind();
        	 	this.resetFilters();
        	}
    		
    		var kindinfo = KINDS.get(this.kind);
    		if (kindinfo)
    		{
    			var search_argument = null;
    			
    			try
    			{
    				search_argument = kindinfo.actions['search']['arguments']['search'];	
    			}
    			catch(e){}
    			
    			if (search_argument)
				{
    				if (search == undefined && search_argument['default'])
		    		{
		    			this.send = search_argument['default'];
		    		}
		    		else if (search)
		    		{
		    			this.send = search;
		    		}
    			}
    			
	    			
    	   }
    		 
    	},
    	'doSearch' : function ()
            {
            	$state.go('admin_search', {
	                'kind': this.kind,
	                'query': JSON.stringify({
	                	'search' : this.send,
	                })
	            });
         },
    	'submitSearch' : function ()
    	{
    		 $rootScope.toggleMainMenu(1);
    		 this.doSearch();
    	},
    	'send' : {
    		'filters' : [],
    		'order_by' : {},
    	}, 
    };
    
    $rootScope.$on('$stateChangeStart',
		function(event, toState, toParams, fromState, fromParams){
		    Title.reset();
		});
  
}]);