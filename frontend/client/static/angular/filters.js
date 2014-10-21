// global filters
'use strict';
angular.module('app').filter('propsFilter', function() {
  return function(items, props) {
    var out = [];

    if (angular.isArray(items)) {
      items.forEach(function(item) {
        var itemMatches = false;

        var keys = Object.keys(props);
        for (var i = 0; i < keys.length; i++) {
          var prop = keys[i];
          var text = props[prop].toLowerCase();
          if (item[prop].toString().toLowerCase().indexOf(text) !== -1) {
            itemMatches = true;
            break;
          }
        }

        if (itemMatches) {
          out.push(item);
        }
      });
    } else {
      // Let the output be the input untouched
      out = items;
    }

    return out;
  };
}).filter('output', function (dateFilter, GLOBAL_CONFIG, modelMeta) {
  
  return function (obj, key, args) {
    
    var input = obj[key];
    
    if (obj['kind'])
    { 
      var objinfo = modelMeta.get(obj['kind']);
      
      var ttype = objinfo['fields'][key];
      
      if (ttype)
      {
        if (ttype['type'] == 'SuperDateTimeProperty')
        {
          var date = new Date(input);
          
          return dateFilter(date, GLOBAL_CONFIG.dateFormat);
        }
        // this is more generic approach to structured objects
        if (input && typeof input === 'object' && input.hasOwnProperty('name'))
        {
          return input.name;
        }
      }
      
    }
  
    return input;
    
  };
  
});
