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

var MainApp = angular.module('MainApp', ['ui.router', 'ngBusy', 'ngSanitize', 'ngUpload', 'ngStorage', 'checklist-model', 'app.ui', 'ngDragDrop'])
.config(['$httpProvider', '$locationProvider',
  function($httpProvider, $locationProvider) {
  	 
     $httpProvider.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';
  
     $locationProvider.hashPrefix('!');
     
	 $locationProvider.html5Mode(true);
     
}])
.constant('MAX_GRID_WIDTH', 240)
.constant('MIN_GRID_WIDTH', 180)
.factory('Select2Options', ['Endpoint', function (Endpoint) {
	return {
		exchange : function (entity, name, name2, what)
        {
        	if (!entity[name2])
        	{
        		entity[name] = null;
        	}
        	else
        	{
        		entity[name] = entity[name2][what];
        	}
                                
        },
		factory : function (new_opts)
		{
			var opts = {
				'field': 'name',
				'operator' : 'contains',
				'order_by' : 'name',
				'order_dir' : 'asc',
				'label' : 'name',
				'filters' : [],
				'action' : 'search',
				'cache' : false,
				'filter_callback' : angular.noop,
				'args_callback' : angular.noop,
				'select2' : {},
				'endpoint' : {},
			};
			
			opts = angular.extend(opts, new_opts);
	  
 			var csearch = {
			    minimumInputLength: 0,
			    ajax: { // instead of writing the function to execute the request we use Select2's convenient helper
			        quietMillis: 200,
			        transport: function (params)
			        { 
			        	return Endpoint.post(opts['action'], opts['kind'], params.data, opts['endpoint']).success(params.success);
			        },
			        data: function (term, page) {
			        	 
			        	  var find = [{'value' : term, 'operator':'contains', 'field' : opts['field']}];
			        	  
			        	  if (term == '' || opts['cache'])
			        	  {
			        	  	find = [];
			        	  }
			        	  
			        	  find.extend(opts.filters);
			        	  
			        	  opts['filter_callback']($(this), find, term, page);
			        	  
			              var args = {
			            	 "search" : {
			            	 			 "filters": find,
		  							     "order_by":{"field":opts['order_by'],"operator":opts['order_dir']}
		  							    } 
			                };
			                
			              opts['args_callback']($(this), args, term, page);
			                
			              return args;
			        },
			        results: function (data, page) { // parse the results into the format expected by Select2.
			            // since we are using custom formatting functions we do not need to alter remote JSON data
			            var results = [];
			            angular.forEach(data.entities, function (value) {
			            	results.push({text: value[opts['label']], id: value.key});
			            });
			            return {results: results};
			        }
			    },
			    initSelection: function(element, callback) {
				        // the input tag has a value attribute preloaded that points to a preselected movie's id
				        // this function resolves that id attribute to an object that select2 can render
				        // using its formatResult renderer - that way the movie name is shown preselected
				        var id = $(element).val();
				        var initial_id = id;
			          
				        var select2 = $(element).data('select2');
				        
				        if (select2.opts.multiple)
				        {
				        	if (id)
				        	{
				        		id = id.split(',');
				        	}
				        }
			          
			            if (id != '')
			            {
			            	var find = [{'value' : id, 'operator': 'IN', 'field' : 'key'}];
			            }
			        	else
			        	{
			        		var find = [];
			        		find.extend(opts.filters);
			        		
			        		return;
			        	}
			          
			        	var args = {  
		            	   "search" : {
		            		  "filters":find,
		            	    } 
				        };
			        	
			        	opts['args_callback']($(this), args);
			      
	 					Endpoint.cached_post('search_' + initial_id, opts['action'], opts['kind'], args, function (data) {
				                	try
				                	{
				                	  
				                	  if (select2.opts.multiple)
								      {
								        	var items = [];
								        	angular.forEach(data.entities, function (value) {
								        		items.push({text: value[opts['label']], id: value['key']});
								        	});
								      }
								      else
								      {
								          var value = data.entities[0];
								          var items = {text: value[opts['label']], id: value['key']};
			            		  	     
								      }
								      
								       callback(items); 
				                	   
				                	}catch(e){
				                		
				                	}
				                	
				                },  opts['endpoint']);
				      
			      
			    },
			    dropdownCssClass: "bigdrop", // apply css that makes the dropdown taller}
	   };
	   
	   if (opts['cache'])
	   {
		   	 csearch['query'] = function (options)
		   	 {
		   	 	 var that = this;
		   	 	 
		   	 	 Endpoint.cached_post(opts['cache'], opts['action'], opts['kind'], that.ajax.data(), function (data) {
		   	 	 	var out = [];
		   	 	 	angular.forEach(data.entities, function (entity) {
		   	 	 		var match = entity[opts['label']];
		   	 	 		if (that.matcher(options.term, match, options.element))
		   	 	 		{
		   	 	 			out.push({id : entity['key'], text : match});
		   	 	 		}
		   	 	 		
		   	 	 	});
		   	 	 	
		   	 	 	options.callback({results : out});
		   	 	 	
		   	 	 }, opts['endpoint']);
		   	 };
	   }	   
	   
	   return angular.extend(csearch, opts['select2']);
	}
};}])
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
	        	
	        	if (!that.action[value.id])
	        	{
	        		that.action[value.id] = {};
	        	}
	        	
		    	that.action[value.id]['executable'] = that._executable(key);
		    	
		    	angular.forEach(value.arguments, function (argument_value, argument_key) {
		    		if (!that.input[value.id]) that.input[value.id] = {};
		    		
		    		that.input[value.id][argument_key] = argument_value;
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
    	 
    	 options = resolve_defaults(defaults, options);
  
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
.factory('Endpoint', ['$http', '$cacheFactory', function ($http, $cacheFactory) {
	
	var cache = $cacheFactory('endpoint_cache');
	 
	var endpoint_url = '/endpoint';
	
	var _compile = function(action, model, data, config)
	{
		 config = always_object(config);
		 data = always_object(data);
			
		 return [angular.extend({
				action_model : model,
				action_id : action,
			}, data), config];
		
	};
	
	return {
		url : endpoint_url,
		cached_post : function (key, action, model, data, success, config)
		{
 
			var loading_key = key + '_loading';
			var loading = cache.get(loading_key);
			var cached = cache.get(key);
 
			if (!cached)
			{
				if (!loading)
				{
					cache.put(loading_key, true);
					return this.post(action, model, data, config).success(function (response) {
						cache.put(key, response);
						try
						{
							success(response);
							
						}catch(e){console.log(e);}
						cache.put(loading_key, false);
					}).error(function () {
						cache.put(loading_key, false);
					});
			
			    }
			  
			}
			else
			{
				 success(cached);
			}
		   
		},
		post : function(action, model, data, config)
		{
		    compiled = _compile(action, model, data, config);
			
			return $http.post(endpoint_url, compiled[0], compiled[1]);
		},
		get : function(action, model, data, config)
		{
		    compiled = _compile(action, model, data, config);
	 
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
    $scope.history.args.log_read_more = true;
    
	$scope.commander = {'isOpen' : false, 'first' : false, 'loading' : false};
	  
	var loadMore = function (that)
	{ 
			if (!$scope.commander.loading && $scope.history.args.log_read_more)
			{
				$scope.commander.loading = true;
				
				Endpoint.post('read_records', $scope.history.kind, $scope.history.args).success(function (data) {
					
					$scope.commander.first = true;
				 
					angular.forEach(data.entity._records, function (value) {
					     $scope.logs.push(value);
					});
 
					$scope.history.args.log_read_cursor = data.log_read_cursor;
					$scope.history.args.log_read_more = data.log_read_more;
					
					if (!$scope.history.args.log_read_cursor)
				    {
				    	delete $scope.history.args.log_read_cursor;
				    }	
					 
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
    	
    	var resolve_options = function (options)
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
        	update_entity : function ($scope, data, exclude)
        	{
        		if (exclude)
        		{
        			angular.forEach(exclude, function (field) {
        				if (field in data['entity'])
        				{
        					delete data['entity'][field];
        				}
        			});
        		}
        		update($scope.entity, data['entity']);
        		
        		if ('live_entity' in $scope)
        		{
        			update($scope.live_entity, data['entity']);
        		}
        		
        		if ('entity' in $scope)
        		{
        			update($scope.entity, data['entity']);
        		}
        	   
        	   this.update_rule($scope, data);
        	},
        	
        	update_rule : function ($scope, data)
        	{
        		 
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
             
             	options = resolve_options(options);
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
  
            	options = resolve_options(options);
            	
                var that = this;
                 
                var action = 'update';
                var action2 = 'read';
                var args = {};
                
                if ('action' in options) action = options['action'];
                if ('action2' in options) action2 = options['action2'];
           
                if (create)
                {	
                	action = (options['create_action'] ? options['create_action'] : 'create');
                	action2 = (options['create_action2'] ? options['create_action2'] : 'prepare');
                }
                
               
                
                args = options['args'];
            
                var handle = function (data) {

                    var modalInstance = $modal.open({
                        templateUrl: options['templateUrl'],
                        controller: function ($scope, $modalInstance, RuleEngine) {
                  
                        	var _resolve_options = function(opts, do_scope)
                        	{
                        	 
	                            $scope.resolve_handle = opts['handle'];
	                            $scope.resolve_complete = opts['complete'];
	                            $scope.resolve_cancel = opts['cancel'];
	                            update($scope.options, opts);
	                            if (do_scope)
	                            {
	                            	update($scope, opts['scope']);
	                            }
                        	};
                        	
                        	var entity = options['entity'];
                        	
                        	update(entity, data['entity']);
                        	
                        	$scope.options = options;
                        	$scope.container = {};
                        	 
 							$scope.rule = RuleEngine.factory(data['entity']);
 							$scope.live_entity = entity;
                            $scope.entity = angular.copy(entity);
                            $scope.action = action;
                            $scope.action2 = action2;
                        
                            $scope.history = {
	                            	'kind' : entity['kind'],
	                            	'args' : {
	                            		'key' : entity['key'],
	                            	}
	                        };
	                         
	                        _resolve_options(options);
                            
                            $scope.save = function () {
                            	
                            	if (angular.isFunction($scope.pre_save))
	                               $scope.pre_save();
                            	  
                                Endpoint.post(action, $scope.options['kind'], (('save_data' in $scope) ? $scope.save_data : $scope.entity))
                                .success(function (data) {
                                	
                                	 	var initial_action = action;
                                	 	var initial_action2 = action2;
                                	 	
                                	 	action2 = initial_action;
                                	 	action = initial_action2;
                                	 	
                                        $scope.action = action;
                					    $scope.action2 = action2;
                					    
                					    $scope.history['args']['key'] = data['entity']['key'];
                                	
                                		if (data['errors'])
                                		{
    
                                			angular.forEach(data['errors'], function (fields, actual_type) {
                                		 		var type = 'invalid';
                                		 		if (actual_type == 'required')
                                		 		{
                                		 			type = actual_type;
                                		 		}
                                				if (type == 'required' || type == 'non_property_error')
                                				{
                                					if (('container' in $scope)
                                					     && ('main' in $scope.container))
                                					{
                                						angular.forEach(fields, function (field) {
                                							if (field in $scope.container.main)
                                							{
                                								$scope.container.main[field].$setValidity(type, true);
                                							}
                                							
                                						});
                                					}
                                					
                                				}
                                			});
                                			 
                                			return false;
                                		}
                                	  
                                        that.update_entity($scope, data);
                                        
                                        if (!data['errors'])
                                        {
                                        	
                                        	$scope.resolve_complete(entity, initial_action);
	                                        
	                                        if (options['close'])
	                                        {
	                                        	$scope.cancel();
	                                        }
	                                        
	                                        if (options['options_after_update'])
	                                        {
	                                        	_resolve_options(options['options_after_update'], true);
	                                        	$scope.resolve_handle(data);
	                                         
	                                        }
	                                    
	                                        if (angular.isFunction($scope.after_save))
	                                        $scope.after_save();
                                        	
                                        }
                                
                                });
                            };
 
                            update($scope, options['scope']);
                            
                            $scope.resolve_handle(data);
                             
                            $scope.cancel = function () {
                            	try
                            	{
                            		if (angular.isFunction($scope.resolve_cancel))
	                            	$scope.resolve_cancel($modalInstance);
	                            	
	                                $modalInstance.dismiss('cancel');
	                                
                            	}catch(e)
                            	{
                            		console.log(e);
                            	}
                            	
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
.run(['$rootScope', '$state', 'Title', 'Select2Options', function ($rootScope, $state, Title, Select2Options) {
    
    $rootScope.ADMIN_KINDS = {
    	'0' : 'Users',
    	'6' : 'Apps',
    }; 
    
    var active_filter = [{'value' : true, 'operator':'==', 'field' : 'active'}];
   	
   	$rootScope.commonSelect2Options = {
   		'country' : Select2Options.factory({
   			kind : '15',
   			cache : 'country',
   			filters : active_filter,
   		}),
   		'region' : Select2Options.factory({
   			kind : '16',
   			filters : active_filter,
   		    filter_callback : function(element, filter, term, page)
   			{
   				var scope = element.scope();
   				var country = element.data('country');
   				 
   				if (country.length)
   				{
   					var country_id = scope.$eval(country);
   					
   					if (country_id && country_id.length)
   					{
   						
   						filter.push({
	   						value : country_id,
	   						operator : '==',
	   						field : 'ancestor',
	   					});
   						
   					}
   					
   				}
   			}
   		}),
   		'role' : Select2Options.factory({
   			kind : '60',
   			filters : active_filter,
   			args_callback : function (element, args)
   			{
   				args['domain'] = $rootScope.nav.domain.key;
   			}
   		}),
   		
   		'domain_user' : Select2Options.factory({
   			kind : '8',
   			args_callback : function (element, args)
   			{
   				args['domain'] = $rootScope.nav.domain.key;
   			}
   	    }),
   
   		'units' : Select2Options.factory({
   			kind : '19',
   			cache : 'units',
   			filters: active_filter,
   		}),
   		
   		'product_category' : Select2Options.factory({
   			kind : '17',
   			filters : [{'value' : 'searchable', 'operator':'==', 'field' : 'state'}],
   			label : 'complete_name',
   		}),
   		 
   	};
   	 
	var measurements = ['length', 'surface', 'time', 'unit', 'volume', 'weight'];
	
	angular.forEach(measurements, function (v) {
		$rootScope.commonSelect2Options[v] = Select2Options.factory({
   			kind : '19',
   			filters : [{'value' : true, 'operator':'==', 'field' : 'active'},
   					   {'value' : ['18', v], 'operator':'==', 'field' : 'ancestor'}],
   		    cache : v,
   		});
	});
   	
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
    				search_argument = kindinfo.mapped_actions['search']['arguments']['search'];	
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
    				search_argument = kindinfo.mapped_actions['search']['arguments']['search'];	
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
    			 
    	   }else
    	   {
    	   	this.hide = true;
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