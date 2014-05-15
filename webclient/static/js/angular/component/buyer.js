MainApp.factory('BuyerAddress', ['$rootScope', 'Endpoint', 'EntityEditor', 'Title', '$modal', 'Confirm',

    function ($rootScope, Endpoint, EntityEditor, Title, $modal, Confirm) {
    	
    	var scope = {
    	
        	'_manageAddress' : function (address, entity)
        	{
        		var $parentScope = this;
        		var modalInstance = $modal.open({
                        templateUrl: logic_template('buyer/address_manage.html'),
                        controller: function ($scope, $modalInstance, RuleEngine) {
 
                            $scope.entity = angular.copy(address ? address : {});
                            $scope.rule = $parentScope.rule;
                   
                            var new_address = address ? false : true;
                         
                            $scope.save = function () {
                  
                            	 // @todo missing async fetching for the country and region ._country etc.
                                 if (new_address)
                                 {
                                 	if (!entity.addresses)
                                 	{
                                 		entity.addresses = [];
                                 	}
                                 	 
                                 	entity.addresses.push($scope.entity);
                                 }
                                 else
                                 {
                                 	update(address, $scope.entity);
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
            update: function (user, complete)
            {
            	var that = this;
            	
            	var entity = {'user' : user['key']};
             
                return EntityEditor.update({
                	 'kind' : '77',
                	 'entity' : entity,
                	 'scope' : scope,
                	 'handle' : function (data)
			         {
			      		  this.history.args.user = entity['user'];
			         },
                	 'complete' : complete,
                	 'templateUrl' : logic_template('buyer/addresses.html'),
                	 'args' : {
                	 	'user' : entity['user'],
                	 }
                });
            }

        };

    }
]).factory('BuyerCollection', ['$rootScope', 'EntityEditor',

    function ($rootScope, EntityEditor) {
    	  
       return {
            update: function (user, complete)
            {
            	var that = this;
            	
            	var entity = {'user' : user['key']};
            	var scope = {
            		
            		'removeApp' : function (app)
            		{
            			this.entity.domains.remove(app.key);
            			this.entity._domains.remove(app);
            		}
            	};
             
                return EntityEditor.update({
                	 'kind' : '10',
                	 'entity' : entity,
                	 'scope' : scope,
                	 'handle' : function (data)
			         {
			      		  this.history.args.user = entity['user'];
			         },
                	 'complete' : complete,
                	 'templateUrl' : logic_template('buyer/collection_manage.html'),
                	 'args' : {
                	 	'user' : entity['user'],
                	 }
                });
            }

        };
    }
]).run(['$rootScope', 'BuyerAddress', 'BuyerCollection',
	function ($rootScope, BuyerAddress, BuyerCollection) {
 
	
	$rootScope.manageBuyer = function ()
	{
		BuyerAddress.update($rootScope.current_user);
	};
	
	$rootScope.manageCollection = function ()
	{
		BuyerCollection.update($rootScope.current_user);
	};
 
	 
}]);