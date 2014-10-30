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
}).filter('output', function (modelsMeta, outputTypes) {
  
  var types = outputTypes;
  
  return function (obj, key, args) {
    
    var input = obj[key];
    
    if (obj['kind'])
    { 
      var fields = modelsMeta.getModelFields(obj['kind']),
          field = fields[key];
      
      if (angular.isDefined(field))
      { 
        var format = types[field['type']];
        if (angular.isDefined(format))
        {
          return format(input, field);
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