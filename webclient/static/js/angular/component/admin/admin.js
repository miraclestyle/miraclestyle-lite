MainApp.controller('AdminUsers', ['$scope', 'users', 'Account', 'Title', function ($scope, users, Account, Title) {
	
	Title.set(['Admin', 'Users']);
	
	$scope.users = users.entities;
	
	$scope.manage = function (user)
	{
		Account.update(user);
	};
	
}])
.controller('AdminApps', ['$scope', 'apps', 'App', 'Title', function ($scope, apps, App, Title) {
	
	Title.set(['Admin', 'Apps']);
	
	$scope.apps = apps.entities;
	
	$scope.manage = function (app)
	{
		App.update(app);
	};
	
}]);