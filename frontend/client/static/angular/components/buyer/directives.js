angular.module('app').directive('buyerAddressDisplay', function ($compile) {
  return {
    scope: {
      val: '=buyerAddressDisplay',
      field: '=buyerAddressDisplayField'
    },
    templateUrl: 'buyer/directive/buyer_address_display.html',
    controller: function ($scope) {
      $scope.notEmpty = function (val) {
        return angular.isString(val) || angular.isNumber(val);
      };

    }
  };
});