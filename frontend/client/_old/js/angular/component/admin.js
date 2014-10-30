ADMIN_SEARCH_KIND_CONFIG = {
    '11': {
    	'title' : 'Accounts',
    	'service' : 'Account',
    	'templateUrl' : logic_template('admin/users.html'),
    },
 
    'default': {
    	'title' : 'No data specified for this kind',
    	'add_new' : 'N/A',
    	'service' : '',
    	'fields' : []
    },
};
MainApp.controller('AdminSearch', ['$scope', 'Title', 'Endpoint', '$stateParams', '$rootScope', 'RuleEngine', 'search', '$injector', '$state',
        function ($scope, Title, Endpoint, $stateParams, $rootScope, RuleEngine, search, $injector, $state) {
        
            angular.forEach(search.entities, function (value) {
                value.rule = RuleEngine.factory(value);
            });

            var kind = $stateParams['kind'];
            var config = ADMIN_SEARCH_KIND_CONFIG[kind];
   
            if (!config)
            {
            	config = ADMIN_SEARCH_KIND_CONFIG['default'];
            	var service = undefined;
            }
            else
            {
            	var service = $injector.get(config['service']);
            }

            $scope.search = search;
            $scope.fields = config['fields'];
            $scope.title = config['title'];
  
            $scope.removeItem = function (e) {
            	// $scope.search.entities.remove(e);
            	e._state = 'deleted';
            };
 
            $scope.update = function (entity) {
				service.update(entity, null, $scope);
            };
    

        }
]);