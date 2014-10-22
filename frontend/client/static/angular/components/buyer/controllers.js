// code for account
angular.module('app')
.controller('BuyerManagementCtrl', function($scope, endpoint, current_account, buyerEntity) {
 
  $scope.settings = function ()
  {
    buyerEntity.settings(current_account.key);
  };

});