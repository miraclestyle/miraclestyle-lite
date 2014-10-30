angular.module('app').directive('buyerAddressDisplay', function ($compile) {
  return {
    scope : {
      buyerAddressDisplay : '=buyerAddressDisplay',
      buyerAddressDisplayField : '=buyerAddressDisplayField'
    },
    link : function (scope, element)
    { 
        var cvar = function (name)
        {
          return '{{buyerAddressDisplay.' + name + '}}';
        };
        
        var calc = function (item, field)
        {
          /*
            <name>
            <address>
            <city> <state> <zip>
            <country_name>
           * */
          var things = [];
          
          if (item.name !== null && item.name.length)
          {
            things.push(cvar('name'));
          }
          
          if (item.street !== null && item.street.length)
          {
            things.push(cvar('street'));
          }
          
            var thing = [];
          
            if (item.city !== null && item.city.length)
            {
              
              thing.push(cvar('city'));
            }
            
            if (item._region !== null && item._region)
            {
              thing.push(cvar('_region.name'));
            }
            if (item.postal_code !== null && item.postal_code.length)
            {
              thing.push(cvar('postal_code'));
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
        
       var template = calc(scope.buyerAddressDisplay, scope.buyerAddressDisplayField).join('<br />');
       element.html(template);
       $compile(element.contents())(scope);
       
    }
  };
});
