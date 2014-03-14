MainApp.factory('Nav', ['$rootScope', 'Endpoint', 'EntityEditor', 'Title', '$modal',

    function ($rootScope, Endpoint, EntityEditor, Title, $modal) {
    	  
        var scope = {
        	
        	'_manageFilter' : function (filter, entity)
        	{
        		var modalInstance = $modal.open({
                        templateUrl: logic_template('nav/manage_filter.html'),
                        controller: function ($scope, $modalInstance, RuleEngine) {
 
                            $scope.filter = angular.copy(filter ? filter : {});
                            $scope.kinds = FRIENDLY_KIND_NAMES;
                            
                            $scope.filter.query = JSON.stringify($scope.filter.query);
                            
                            var new_filter = filter ? false : true;
             
                            $scope.save = function () {
                            	
                            	 $scope.filter.query = JSON.parse($scope.filter.query);

                                 if (new_filter)
                                 {
                                 	entity.filters.push($scope.filter);
                                 }
                                 else
                                 {
                                 	update(filter, $scope.filter);
                                 }
                                 
                                 $scope.cancel();
                            };

                            $scope.cancel = function () {
                                $modalInstance.dismiss('cancel');
                            };

                        }
                    });
        	},
    	 	'addFilter' : function ()
    	 	{
    	 		this._manageFilter(false, this.entity);
    	 	},
    	 	'editFilter' : function (filter)
    	 	{
    	 		this._manageFilter(filter, this.entity);
    	 	},
    	 	'removeFilter' : function (filter)
    	 	{
    	 		var index = this.entity.filters.indexOf(filter);
  			    this.entity.filters.splice(index,1);    
    	 	},
    	};
    	
        return {
            build_menu: function (domain_key) {

                if(!$rootScope.nav['menu']) {
                    return Endpoint.post('build_menu', '62', {
                        'domain': domain_key
                    }).then(function (output) {
                        update($rootScope.nav, output.data);
                        Title.set(['My Apps', $rootScope.nav.domain.name]);
                        return output.data;
                    });
                } else {
                    Title.set(['My Apps', $rootScope.nav.domain.name]);
                    return $rootScope.nav;
                }

            },
            create: function (domain_key, oncreate) {
             
            	  
               return EntityEditor.create({
                	 'kind' : '62',
                	 'entity' : {},
                	 'scope' : scope,
                	 'handle' : function (data)
			         {
			            this.roles = data['roles'];
			            this.entity['domain'] = domain_key;
			         },
                	 'complete' : oncreate,
                	 'templateUrl' : logic_template('nav/manage.html'),
                	 'args' : {
                	 	'domain' : domain_key,
                	 }
                });
                
            },
            remove : function (entity, ondelete)
            {
               
               return EntityEditor.remove({
               	  'kind' : '62',
               	  'entity' : entity,
               	  'complete' : ondelete,
               });
         
            },
            update: function (entity, onupdate)
            {
             
                return EntityEditor.update({
                	 'kind' : '62',
                	 'entity' : entity,
                	 'scope' : scope,
                	 'handle' : function (data)
			         {
			            this.roles = data['roles'];
			         },
                	 'complete' : onupdate,
                	 'templateUrl' : logic_template('nav/manage.html'),
                	 'args' : {
                	 	'key' : entity['key'],
                	 }
                });
            }

        };

    }
]);