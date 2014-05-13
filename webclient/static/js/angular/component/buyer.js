MainApp.factory('BuyerAddress', ['$rootScope', 'Endpoint', 'EntityEditor', 'Title', '$modal', 'Confirm',

    function ($rootScope, Endpoint, EntityEditor, Title, $modal, Confirm) {
    	
    	var scope = {
    	
        	'_manageAddress' : function (address, entity)
        	{
        		var modalInstance = $modal.open({
                        templateUrl: logic_template('buyer/address_manage.html'),
                        controller: function ($scope, $modalInstance, RuleEngine) {
 
                            $scope.address = angular.copy(address ? address : {});
                       
                            var new_address = address ? false : true;
             
                            $scope.save = function () {
                            	
                             
                                 if (new_address)
                                 {
                                 	if (!entity.addresses)
                                 	{
                                 		entity.addresses = [];
                                 	}
                                 	 
                                 	entity.addresses.push($scope.address);
                                 }
                                 else
                                 {
                                 	update(address, $scope.address);
                                 }
                                 
                                 $scope.cancel();
                            };

                            $scope.cancel = function () {
                                $modalInstance.dismiss('cancel');
                            };

                        }
                    });
        	},
    	 	'addAddress' : function ()
    	 	{
    	 		this._manageAddress(false, this.entity);
    	 	},
    	 	'editAddress' : function (address)
    	 	{
    	 		this._manageAddress(address, this.entity);
    	 	},
    	 	'removeAddress' : function (address)
    	 	{
    	 		this.entity.addresses.remove(address);
  			      
    	 	},
    	 
    	};
  
        return {
            update: function (entity, complete)
            {
            	var that = this;
             
                return EntityEditor.update({
                	 'kind' : '77',
                	 'entity' : {},
                	 'scope' : scope,
                	 'handle' : function (data)
			         {
			      
			         },
                	 'complete' : complete,
                	 'templateUrl' : logic_template('buyer/addresses.html'),
                	 'args' : {
                	 	'user' : $rootScope.current_user.key,
                	 }
                });
            }

        };

    }
]).factory('BuyerCollection', ['$rootScope', 'Endpoint', 'EntityEditor', 'Title', '$modal',

    function ($rootScope, Endpoint, EntityEditor, Title, $modal) {
    	  
        var scope = {
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
]).run(['$rootScope', 'BuyerAddress',
	function ($rootScope, BuyerAddress) {
 
	
	$rootScope.manageBuyer = function ()
	{
		BuyerAddress.update();
	};
 
	 
}]);