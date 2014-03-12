MainApp.factory('Nav', ['$rootScope', '$modal', '$timeout', 'Endpoint', 'Title', 'Confirm',

    function ($rootScope, $modal, $timeout, Endpoint, Title, Confirm) {

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
            _manage_filter : function (filter, entity)
            {
            	
            	var modalInstance = $modal.open({
                        templateUrl: logic_template('nav/manage_filter.html'),
                        controller: function ($scope, $modalInstance, RuleEngine) {
 
                            $scope.filter = angular.copy(filter ? filter : {});
                            $scope.kinds = FRIENDLY_KIND_NAMES;
                            
                            var new_filter = filter ? false : true;
             
                            $scope.save = function () {

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
            create: function (domain_key, oncreate) {
                return this.manage(true, domain_key, oncreate);
            },
            remove : function (entity, ondelete)
            {
             
                Confirm.sure(function () {
            		
            		 Endpoint.post('delete', '62', entity).success(function (data) {
	            		if (data['entity'])
	            		{
	            			var modal = Confirm.notice('Successfully deleted widget!', ondelete);
	            			
	            			$timeout(function () {
	            				modal.dismiss();
	            			}, 1500);
	            		}
	            	});
            	});
            	
         
            },
            update: function (entity, onupdate)
            {
            	return this.manage(false, entity, onupdate);
            },
            manage: function (create, entity, oncomplete) {
            	
                var that = this;
                 
                var action = 'read';
                var action2 = 'update';
                var args = {'domain' : entity};
                
                if (create)
                {	
                	action = 'prepare';
                	action2 = 'create';
                }
                else
                {
                	args = {
                      'key': entity['key']
               		};
                }

                var handle = function (data) {

                    var modalInstance = $modal.open({
                        templateUrl: logic_template('nav/manage.html'),
                        controller: function ($scope, $modalInstance, RuleEngine) {
							
							if (!create)
							{
								update(entity, data['entity']);
								 
								$scope.history = {
	                                'kind': '62',
	                                'args': {
	                                    'key': entity['key'],
	                                }
	                            };
							}
                            else
                            {
                            	entity = data['entity'];
                            	entity['domain'] = args['domain'];
                            }
                            
                            
 							$scope.rule = RuleEngine.factory(data['entity']);
                            $scope.entity = angular.copy(entity);
                            $scope.roles = data['roles'];
                            
                            $scope.addFilter = function ()
                            {
                            	that._manage_filter(false, $scope.entity);
                            };
                            
                            $scope.editFilter = function (filter)
                            {
                            	that._manage_filter(filter, $scope.entity);
                            };
                            
                            $scope.removeFilter = function(filter)
                            {
                            	var index = $scope.entity.filters.indexOf(filter);
  								$scope.entity.filters.splice(index,1);     
                            };
                             
                            $scope.save = function () {
 
                                Endpoint.post(action2, '62', $scope.entity)
                                .success(function (data) {

                                        update(entity, $scope.entity, data['entity']);
                                        $scope.rule.update(data['entity']);
                                        
                                        if (angular.isFunction(oncomplete))
                                        {
                                        	oncomplete(entity);
                                        }
                                        
                                        $scope.cancel();

                                });
                            };

                            $scope.cancel = function () {
                                $modalInstance.dismiss('cancel');
                            };

                        }
                    });

                };
                
                Endpoint.post(action, '62', args).success(handle);

            }

        };

    }
]);