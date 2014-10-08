/*global angular, window, console, jQuery, $, document*/
angular.module('app').directive('mainMenuToggler', ['$rootScope', function ($rootScope) {
  'use strict';
  return {
    link : function (scope, element)
    {
      var click = function (e, cmd)
      {
        var mm = $('#main-menu'),
            visible = mm.is(':visible');
        
        if ((visible || cmd === 1) && cmd !== 2)
        {
          mm.stop().animate({
            height : 0
          }, 400, function () {
            $(this).hide();
          });
        }
        else if (!visible || cmd === 2)
        {
          mm.height(0).show();
          mm.stop().animate({
            height : ($(window).height() - $('#top-bar').height())
          }, 400);
        }   
        if (e)
        {
           e.preventDefault();
        }
         
      };
      
      element.on('click', click);
      
      scope.$on('$destroy', function () {
         element.off('click', click);
      });
      
      $rootScope.$on('hide_menu', function () {
        click(null, 1);
      });
      
      $rootScope.$on('show_menu', function () {
        click(null, 2);
      });
  
    }
  };
}]).directive('formBuilder', [function () {
  /**
   * Main builder. It will construct a form based on a list of configuration params:
   * {
   *   'field_name' : {
   *    'type' : instance of property from backend,
   *    'model' : 'optional, e.g. "name",
   *    ...
   * }
   * }
   * Possible types of an input so far:
    String
    Number
    Select
    AutoCompleteSelect
    AutoCompleteRemoteSelect
    Structured
    DateTime
    Text
    Bool
    File
   */
  'use strict';
  return {
    link : function (scope, element, attrs)
    {
         var config = scope.$eval(attrs.formBuilder);
    }
  };
}]);
