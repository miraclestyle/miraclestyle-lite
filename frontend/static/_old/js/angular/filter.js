/**
 * A collection of filters for AngularJS.
 * @version v1.1.0 - 2014-01-30
 * @author Francesco Pontillo
 * @link https://github.com/frapontillo/angular-filters
 * @license Apache License 2.0
**/

'use strict';
MainApp.filter('bool', function () {
  return function (input, valueTrue, valueFalse) {
    return input !== true ? valueFalse : valueTrue;
  };
})
.filter('default', function () {
  return function (input, value) {
    if (input !== null && input !== undefined && (input !== '' || angular.isNumber(input))) {
      return input;
    }
    return value || '';
  };
})
.filter('firstNotNull', function () {
  return function (input) {
    if (input) {
      var l = input.length - 1;
      for (var i = 0; i <= l; i++) {
        if (input[i] !== undefined && input[i] !== null) {
          return input[i];
        }
      }
    }
  };
})
.filter('join', function () {
  return function (array, separator) {
  	
  	if (!angular.isArray(array))
  	{
  		return array;
  	}
  	
    if (!array) {
      return '';
    }
    return array.join(separator);
  };
})
.filter('lastNotNull', function () {
  return function (input) {
    if (input) {
      var l = input.length - 1;
      for (var i = l; i >= 0; i--) {
        if (input[i] !== undefined) {
          return input[i];
        }
      }
    }
  };
})
.filter('max', function () {
  return function (input) {
    var out;
    if (input) {
      for (var i in input) {
        if (input[i] > out || out === undefined || out === null) {
          out = input[i];
        }
      }
    }
    return out;
  };
})
.filter('min', function () {
  return function (input) {
    var out;
    if (input) {
      for (var i in input) {
        if (input[i] < out || out === undefined || out === null) {
          out = input[i];
        }
      }
    }
    return out;
  };
})
.filter('output', ['dateFilter', '$rootScope', function (dateFilter, $rootScope) {
	
  return function (obj, key, args) {
  	
  	var input = obj[key];
    
    if (obj['kind'])
    {
    	
    	var objinfo = KINDS.get(obj['kind']);
    	
    	var ttype = objinfo['fields'][key];
    	
    	if (ttype)
    	{
    		if (ttype['type'] == 'SuperDateTimeProperty')
    		{
    			var date = new Date(input);
    			
    			return dateFilter(date, $rootScope.DATE_FULL);
    		}
    	}
    	
    }
  
    return input;
    
  };
  
}])
.filter('property', function () {
  return function (array, property) {
    var newArray = [];
    angular.forEach(array, function (element) {
      var evalProperty = element[property];
      newArray.push(evalProperty);
    });
    return newArray;
  };
});