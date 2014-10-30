angular.module('app').directive('addressRuleLocationDisplay', function ($compile) {
  return {
    scope : {
      addressRuleLocationDisplay : '=addressRuleLocationDisplay',
      addressRuleLocationDisplayField : '=addressRuleLocationDisplayField'
    },
    link : function (scope, element)
    { 
        var cvar = function (name)
        {
          return '{{addressRuleLocationDisplay.' + name + '}}';
        };
        
        var calc = function (item, field)
        {
          /*  
            <city> <state> <zip> to <zip2>
            <country_name>
           * */
          var things = [];
  
          
            var thing = [];
          
            if (item.city !== null && item.city.length)
            { 
              thing.push(cvar('city'));
            }
            
            if (item._region !== null && item._region)
            {
              thing.push(cvar('_region.name'));
            }
            if ((item.postal_code_from !== null && item.postal_code_from.length) && (item.postal_code_to !== null && item.postal_code_to.length))
            {
              thing.push(cvar('postal_code_from') + ' - ');
              thing.push(cvar('postal_code_to'));
            }
    
            
            if (thing.length)
            {
              things.push(thing.join(' '));
            }
              
          if (item._country !== null && angular.isObject(item._country))
          {
            things.push(cvar('_country.name'));
          }
           
          return things;
        }
        
       var template = calc(scope.addressRuleLocationDisplay, scope.addressRuleLocationDisplayField).join('<br />');
       element.html(template);
       $compile(element.contents())(scope);
       
    }
  };
});
