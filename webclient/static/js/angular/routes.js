MainApp
.config(['$stateProvider',
  function($stateProvider) {
   
    $stateProvider.
      state('home', {
      	url : '/',
        templateUrl: logic_template('home', 'home.html'),
        controller: 'HomePage'
      }).
      state('login', {
        url: '/login/:provider',
        template: " ",
        controller: 'LoginPage'
      }).
      state('apps', {
      	url: '/apps',
        templateUrl: logic_template('srv/auth', 'apps.html'),
        controller: 'AppsPage',
        resolve : {
        	apps : ['App', function (App) {
        		
        		if ('entities' in initdata)
        		{
        			return initdata['entities'];
        		}
        		
        		return App.search().then(function (output) {
					return output.data.entities;
				});
        	}]
        }
      });
 
       
}]);