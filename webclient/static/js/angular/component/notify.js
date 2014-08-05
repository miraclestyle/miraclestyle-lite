MainApp.factory('Notify', ['$rootScope', 'Endpoint', 'EntityEditor', 'Title', '$modal',

    function ($rootScope, Endpoint, EntityEditor, Title, $modal) {
    	
    	var actions = {};
    	
    	angular.forEach(KINDS.info, function (value, key) {
    		
    		 if (key in FRIENDLY_KIND_NAMES)
    		 {
    		 	angular.forEach(value._actions, function (action) {
	    		 	 actions[action.key] = FRIENDLY_KIND_NAMES[key] + '.' + action.id;
	    		 });
    		 }
    		 
    	});
    	
    	var TYPES = {
    		'63' : {
    			'label' : 'Http',
    			'sys' : 'http',
    		},
    		'58' : {
    			'label' : 'Mail',
    			'sys' : 'mail',
    		},
    	};
    	  
        var scope = {
         	 'actions' : actions,
         	 'removeTemplate' : function (template)
        	 {
        	 	 this.entity.templates.remove(template);
        	 },
        	 'createTemplate' : function ()
        	 {
        	 	
        	 	var that = this;
        	 	 
        	 	var modalInstance = $modal.open({
                        templateUrl: logic_template('notify/create.html'),
                        controller: function ($scope, $modalInstance, RuleEngine) {
 
                            $scope.entity = {};
                            $scope.types = TYPES;
                  
                            $scope.save = function () {
                                $scope.cancel();
                            	 
            				    that.manageTemplate($scope.entity, 1);
            				   
                            };

                            $scope.cancel = function () {
                                $modalInstance.dismiss('cancel');
                            };

                        }
                    });
        	 },
        	 'manageTemplate' : function (template, create) { 
        	 	
        	 	var that = this;
        	 	var sys = TYPES[template.kind]['sys'];
        	 	
        	 	var modalInstance = $modal.open({
                        templateUrl: logic_template('notify/manage_'+sys+'.html'),
                        controller: function ($scope, $modalInstance, RuleEngine) {
 
                            $scope.entity = angular.copy(template);
                      
                            var new_template = create;
             
                            $scope.save = function () {
           						 
           						 if (!that.entity.templates) that.entity.templates = [];
           						 
                                 if (new_template)
                                 {
                                 	that.entity.templates.push($scope.entity);
                                 }
                                 else
                                 {
                                 	update(template, $scope.entity);
                                 }
                                 
                                 $scope.cancel();
                            };

                            $scope.cancel = function () {
                                $modalInstance.dismiss('cancel');
                            };

                        }
                    });
        	 	
        	  },
    	};
    	
        return {
 
            create: function (domain_key, complete) {
              
               return EntityEditor.create({
                	 'kind' : '61',
                	 'entity' : {},
                	 'scope' : scope,
                	 'handle' : function (data)
			         {
			            this.entity['domain'] = domain_key;
 
			         },
                	 'complete' : complete,
                	 'templateUrl' : logic_template('notify/manage.html'),
                	 'args' : {
                	 	'domain' : domain_key,
                	 }
                });
                
            },
            remove : function (entity, complete)
            {
               
               return EntityEditor.remove({
               	  'kind' : entity['kind'],
               	  'entity' : entity,
               	  'complete' : complete,
               });
         
            },
            update: function (entity, complete)
            {
             
                return EntityEditor.update({
                	 'kind' : entity['kind'],
                	 'entity' : entity,
                	 'scope' : scope,
               
                	 'complete' : complete,
                	 'templateUrl' : logic_template('notify/manage.html'),
                	 'args' : {
                	 	'key' : entity['key'],
                	 }
                });
            }

        };

    }
]);