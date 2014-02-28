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
        		
				return useInit('entities', function () {
        			return App.search().then(function (output) {
						return output.data;
					});
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
        		
        		return useInit('entities', function () {
        			return App.sudo_search().then(function (output) {
						return output.data;
					});
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
        		
        		return useInit('entities', function () {
        			return Account.sudo_search().then(function (output) {
						return output.data;
					});
        		});
        	}]
        }
      });
  
}]);