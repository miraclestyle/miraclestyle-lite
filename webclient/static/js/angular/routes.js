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
        	apps : ['Domain', function (Domain) {
        		
        		if (initdata['domains'])
        		{
        			return initdata['domains'];
        		}
        		
        		return Domain.list().then(function (output) {
					return output.data.domains;
				});
        	}]
        }
      });
 
       
}]);