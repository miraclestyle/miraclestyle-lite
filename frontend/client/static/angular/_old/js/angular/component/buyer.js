MainApp.factory('BuyerAddress', ['$rootScope', 'Endpoint', 'EntityEditor', 'Title', '$modal', 'Confirm',

    function ($rootScope, Endpoint, EntityEditor, Title, $modal, Confirm) {
    	
    	function make_scope() {
    	    return {
        
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
                                 
                                 $parentScope._onAddressUpdate(address);
                                  
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
                address._state = 'deleted';
                  
            },
            
            '_onAddressUpdate' : function (updated_address)
            {
                angular.forEach(this.entity.addresses, function (address) {
                    if (updated_address.default_billing || updated_address.default_shipping)
                    {
                        if (updated_address != address)
                        {
                            
                            if (updated_address.default_billing)
                            {
                                address.default_billing = false;
                            }
                            
                            if (updated_address.default_shipping)
                            {
                                address.default_shipping = false;
                            }
                        }
                         
                    }
                    
                });
            },
         
        };
        
    	}
  
        return {
            update: function (account, complete)
            {
            	var that = this;
            	
            	var entity = {'account' : account['key']};
             
                return EntityEditor.update({
                	 'kind' : '19',
                	 'entity' : entity,
                	 'scope' : make_scope(),
                	 'handle' : function (data)
			         {
			      		  this.history.args.account = entity['account'];
			         },
                	 'complete' : complete,
                	 'templateUrl' : logic_template('buyer/addresses.html'),
                	 'args' : {
                	 	'account' : entity['account'],
                	 }
                });
            }

        };

    }
]).factory('BuyerCollection', ['$rootScope', 'EntityEditor',

    function ($rootScope, EntityEditor) {
    	  
       return {
            update: function (account, complete)
            {
            	var that = this;
            	
            	var entity = {'account' : account['key']};
            	var scope = {
            		
            		'removeApp' : function (app)
            		{
            			 this.entity.sellers.remove(app.key);
            			 this.entity._sellers.remove(app);
            		}
            	};
             
                return EntityEditor.update({
                	 'kind' : '18',
                	 'entity' : entity,
                	 'scope' : scope,
                	 'handle' : function (data)
			         {
			      		  this.history.args.account = entity['account'];
			         },
                	 'complete' : complete,
                	 'templateUrl' : logic_template('buyer/collection_manage.html'),
                	 'args' : {
                	 	'account' : entity['account'],
                	 }
                });
            }

        };
    }
]).run(['$rootScope', 'BuyerAddress', 'BuyerCollection',
	function ($rootScope, BuyerAddress, BuyerCollection) {
  
	$rootScope.manageBuyer = function ()
	{
		BuyerAddress.update($rootScope.current_account);
	};
	
	$rootScope.manageCollection = function ()
	{
		BuyerCollection.update($rootScope.current_account);
	};
 
	 
}]);