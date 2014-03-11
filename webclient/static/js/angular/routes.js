MainApp.config(['$stateProvider',
  function($stateProvider) {
   
    $stateProvider.state('home', {
      	url : '/',
        templateUrl: logic_template('home', 'home.html'),
        controller: 'HomePage'
      })
      .state('login', {
        url: '/login/:provider',
        controller: 'LoginPage',
      })
      .state('apps', {
      	url: '/apps',
        templateUrl: logic_template('srv/auth', 'apps.html'),
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
      	url: '/app/:app_id',
        templateUrl: logic_template('srv/auth', 'app_view.html'),
        controller: 'AppView',
      })
      .state('app_view_search', {
      	url: '/app/:app_id/search/:widget_id/:filter',
        templateUrl: logic_template('srv/auth', 'app_view_search.html'),
        controller: 'AppSearch',
        resolve : {
        	search : ['Endpoint', '$stateParams', function (Endpoint, $stateParams) {
 
			       return Endpoint.post('search', 'srv.nav.Widget', {
								'filter' : $stateParams.filter,
								'key' : $stateParams.widget_id,
						   }).then(function (output) {
							  return output.data;
						   });
        	}]
        }
      })
      .state('admin', {
      	url: '/admin',
      }).state('admin_apps', {
      	url: '/admin/apps',
        templateUrl: logic_template('admin', 'apps.html'),
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
        templateUrl: logic_template('admin', 'users.html'),
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