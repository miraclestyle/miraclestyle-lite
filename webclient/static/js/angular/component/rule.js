PERMISSION_TYPES = {
	'FieldPermission' : 'Field',
	'ActionPermission' : 'Action',
};

MainApp.filter('permissionResolveActionName', function() {
    return function(input) {
 
       var outputs = [];
       angular.forEach(input.actions, function (value) {
    	    outputs.push(KINDS.friendlyActionName(input.kind, value));
       });
 
       
       return outputs;
    };
}).factory('AppUser', ['$rootScope', 'Endpoint', 'EntityEditor', 'Title', '$modal', 'Confirm',

    function ($rootScope, Endpoint, EntityEditor, Title, $modal, Confirm) {
 
    	
        return {
        	
        	accept : function (entity_key, complete)
        	{
        		Confirm.sure(function () {
        			Endpoint.post('accept', '8', {
        				'key' : entity_key,
        			}).success(complete);
        		});
        	},
        	decline : function (entity_key, complete)
        	{
        		Confirm.sure(function () {
        			Endpoint.post('decline', '8', {
        				'key' : entity_key,
        			}).success(complete);
        		});
        	},
            create: function (domain_key, complete) {
              
               return EntityEditor.create({
	                	 'kind' : '8',
	                	 'entity' : {},
	                	 'action' : 'invite',
	                	 
	                	 'handle' : function (data)
				         {
				            this.roles = data['roles'];
				            this.entity['domain'] = domain_key;
				         },
	                	 'complete' : complete,
	                	 'templateUrl' : logic_template('rule/invite_user.html'),
	                	 'args' : {
	                	 	'domain' : domain_key,
	                	 }
                });
                
            },
            remove : function (entity, complete)
            {
               
               Confirm.sure(function () {
        			Endpoint.post('remove', '8', {
        				'key' : entity['key'],
        			}).success(complete);
        		});
         
            },
            update: function (entity, complete, $parentScope)
            {
            	var that = this;
             
                return EntityEditor.update({
                	 'kind' : '8',
                	 'entity' : entity,
                	 'scope' : {
				        'remove' : function ()
				    	 {
				    	 	var scope = this;
				    	 	that.remove(entity, function (data) {
				    	 		if (data['entity'])
				    	 		{
				    	 			$parentScope.removeItem(scope.live_entity);
				    	 			scope.cancel();
				    	 		}
				    	 	});
				    	    
				    	 },  
                	 },
                	 'handle' : function (data)
			         {
			            this.roles = data['roles'];
			         },
                	 'complete' : complete,
                	 'templateUrl' : logic_template('rule/manage_user.html'),
                	 'args' : {
                	 	'key' : entity['key'],
                	 }
                });
            }

        };

    }
]).factory('AppRole', ['$rootScope', 'Endpoint', 'EntityEditor', 'Title', '$modal',

    function ($rootScope, Endpoint, EntityEditor, Title, $modal) {
    	  
        var scope = {
    	
        	'_managePermission' : function (permission, entity)
        	{
        		var modalInstance = $modal.open({
                        templateUrl: logic_template('rule/manage_role_permission.html'),
                        controller: function ($scope, $modalInstance, RuleEngine) {
 
                            $scope.permission = angular.copy(permission ? permission : {});
                            $scope.kinds = FRIENDLY_KIND_NAMES;
                            $scope.types = PERMISSION_TYPES;
                            $scope.actions = {};
                            $scope.fields = {};
                            
                            $scope.get_meta = function ()
                            {
                            	 
                            	if ($scope.permission.kind == null) return;
                            	
                            	var info = KINDS.get($scope.permission.kind);
                            	
                            	var actions = {};
                            	var fields = {};
                            	
                            	angular.forEach(info['actions'], function (value, key) {
                            		actions[value.key] = key;
                            	});
                            	
                            	angular.forEach(info['fields'], function (value, key) {
                            		fields[key] = key;
                            	});
                            	
                            	$scope.actions = actions;
                            	$scope.fields = fields;
                            	
                            };
                            
                            $scope.get_meta();
                   
                            var new_permission = permission ? false : true;
             
                            $scope.save = function () {
                            	
                             
                                 if (new_permission)
                                 {
                                 	if (!entity.permissions)
                                 	{
                                 		entity.permissions = [];
                                 	}
                                 	 
                                 	entity.permissions.push($scope.permission);
                                 }
                                 else
                                 {
                                 	update(permission, $scope.permission);
                                 }
                                 
                                 $scope.cancel();
                            };

                            $scope.cancel = function () {
                                $modalInstance.dismiss('cancel');
                            };

                        }
                    });
        	},
    	 	'addPermission' : function ()
    	 	{
    	 		this._managePermission(false, this.entity);
    	 	},
    	 	'editPermission' : function (permission)
    	 	{
    	 		this._managePermission(permission, this.entity);
    	 	},
    	 	'removePermission' : function (perm)
    	 	{
    	 		this.entity.permissions.remove(perm);
  			      
    	 	},
    	 
    	};
    	
        return {
            create: function (domain_key, complete) {
             
            	  
               return EntityEditor.create({
                	 'kind' : '60',
                	 'entity' : {
                	 	'permissions' : [],
                	 },
                	 'scope' : scope,
                	 'handle' : function (data)
			         {
			            this.entity['domain'] = domain_key;
			         },
                	 'complete' : complete,
                	 'templateUrl' : logic_template('rule/manage_role.html'),
                	 'args' : {
                	 	'domain' : domain_key,
                	 }
                });
                
            },
            remove : function (entity, complete)
            {
               
               return EntityEditor.remove({
               	  'kind' : '60',
               	  'entity' : entity,
               	  'complete' : complete,
               });
         
            },
            update: function (entity, complete)
            {
             
                return EntityEditor.update({
                	 'kind' : '60',
                	 'entity' : entity,
                	 'scope' : scope,
                	 'complete' : complete,
                	 'templateUrl' : logic_template('rule/manage_role.html'),
                	 'args' : {
                	 	'key' : entity['key'],
                	 }
                });
            }

        };

    }
]);