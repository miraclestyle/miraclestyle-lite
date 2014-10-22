// code for account
angular.module('app').constant('LOGIN_PROVIDERS', {
  '1' : 'Google',
  '2' : 'Facebook'
}).controller('LoginLinksCtrl', function($scope, endpoint, current_account) {

  $scope.authorization_urls = {};

  if (current_account._is_guest) {
    endpoint.post('login', '11', {
      login_method : 'google'
    }).then(function(response) {
      $scope.authorization_urls = response.data.authorization_urls;
    });
  }

  $scope.login = function(type) {
    endpoint.invalidate_cache('current_account');
    window.location.href = $scope.authorization_urls[type];
  };

}).controller('AccountManagementCtrl', function($scope, current_account, accountEntity) {

  $scope.settings = function() {
    accountEntity.settings(current_account.key);
  };

  $scope.logout = function() {
    accountEntity.logout(current_account.key);
  };
});
