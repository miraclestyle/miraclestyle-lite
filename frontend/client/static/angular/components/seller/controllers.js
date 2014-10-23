// code for account
angular.module('app')
.controller('SellerManagementCtrl', function($scope, endpoint, current_account, sellerEntity) {
 
  $scope.settings = function ()
  {
    sellerEntity.settings(current_account.key);
  };

});