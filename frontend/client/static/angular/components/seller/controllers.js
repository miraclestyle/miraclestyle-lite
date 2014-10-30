// code for account
angular.module('app')
.controller('SellerManagementCtrl', function($scope, endpoint, currentAccount, models) {
 
  $scope.settings = function ()
  {
    models['23'].settingsModal(currentAccount.key);
  };

});