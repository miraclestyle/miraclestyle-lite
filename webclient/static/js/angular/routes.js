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
        templateUrl: logic_template('app/view_search.html'),
        controller: 'AppSearch',
        resolve : {
        	menu : resolve_menu,
        	search : ['Endpoint', '$stateParams', function (Endpoint, $stateParams) {
        		  
        		  var query = JSON.parse($stateParams['query']);
        		  
        		  query['domain'] = $stateParams['domain_key'];
        		  
			      return Endpoint.post('search', $stateParams['kind'], query).then(function (output) {
							  return output.data;
						 });
        	}]
        }
      })
      .state('admin', {
      	url: '/admin',
      }).state('admin_apps', {
      	url: '/admin/apps',
        templateUrl: logic_template('admin/apps.html'),
        controller: 'AdminApps',
        resolve : {
        	apps : ['App', function (App) {
        		
        		return App.sudo_search().then(function (output) {
						return output.data;
					});
        		 
        	}]
        }
      })
      .state('admin_users', {
      	url: '/admin/users',
        templateUrl: logic_template('admin/users.html'),
        controller: 'AdminUsers',
        resolve : {
        	users : ['Account', function (Account) {
        		
        		return Account.sudo_search().then(function (output) {
						return output.data;
					});
        	}]
        }
      });
  
}]);