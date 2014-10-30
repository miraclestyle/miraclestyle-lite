angular.module('app').directive('addressRuleLocationDisplay', function ($compile) {
  return {
    scope : {
      val : '=addressRuleLocationDisplay',
      field : '=addressRuleLocationDisplayField'
    },
    templateUrl : 'seller/directive/address_rule_location_display.html',
    controller : function ($scope)
    {  
       $scope.notEmpty = function (val)
       {
         return angular.isString(val) || angular.isNumber(val);
       };
       
    }
  };
}).directive('carrierLineRuleDisplay', function ($compile) {
  return {
    scope : {
      val : '=carrierLineRuleDisplay',
      field : '=carrierLineRuleDisplayField'
    },
    templateUrl: 'seller/directive/carrier_line_rule_display.html',
    controller : function ($scope)
    {  
       $scope.notEmpty = function (val)
       {
         return angular.isString(val) || angular.isNumber(val);
       };
       
    }
  };
});
