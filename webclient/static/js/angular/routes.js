MainApp.config(['$stateProvider',
  function($stateProvider) {
  	
  	var resolve_menu = ['Nav', '$stateParams', function (Nav, $stateParams) {
        	return Nav.build_menu($stateParams['domain_key']);
        }];
   
    $stateProvider.state('home', {
      	url : '/',
        templateUrl: logic_template('home/index.html'),
        controller: 'HomePage'
      })
      .state('login', {
        url: '/login/:provider',
        controller: 'LoginPage',
      })
      .state('apps', {
      	url: '/apps',
        templateUrl: logic_template('app/apps.html'),
        controller: 'AppList',
        resolve : {
        	apps : ['App', function (App) {
        		
				return App.search().then(function (output) {
						return output.data;
					});
        	}]
        }
      })
      .state('app_view', {
      	url: '/app/:domain_key',
        template: '',
        controller: 'AppView',
        resolve : {
        	menu : resolve_menu,
        }
      })
      .state('app_view_search', {
      	url: '/app/:domain_key/search/:kind/:query',
        templateUrl: logic_template('app/search.html'),
        controller: 'AppSearch',
        resolve : {
        	menu : resolve_menu,
        	search : ['Endpoint', '$stateParams', function (Endpoint, $stateParams) {
        	 
        		  
        		  var query = JSON.parse($stateParams['query']);
        
        		  if (!angular.isObject(query)) query = {};
        		  
        		  query['domain'] = $stateParams['domain_key'];
        		  
			      return Endpoint.post('search', $stateParams['kind'], query).then(function (output) {
							  return output.data;
						 });
        	}]
        }
      })
      .state('admin_search', {
      	url: '/admin/search/:kind/:query',
        templateUrl: logic_template('admin/search.html'),
        controller: 'AppSearch',
        resolve : {
        	search : ['Endpoint', '$stateParams', function (Endpoint, $stateParams) {
        	  
        		  var query = JSON.parse($stateParams['query']);
        
        		  if (!angular.isObject(query)) query = {};
    
			      return Endpoint.post('search', $stateParams['kind'], query).then(function (output) {
							  return output.data;
						 });
        	}]
        }
      });
  
}]);