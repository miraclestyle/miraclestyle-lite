/**
 *
 * Overrides for window scope
 */
/*global angular, window, console, jQuery, $, document*/
Array.prototype.remove = function(val) {

  var index = this.indexOf(val);
  this.splice(index, 1);

  return this;
};

Array.prototype.contains = function(value, all) {
  if (angular.isArray(value)) {
    var matches = [];

    angular.forEach(value, function(v) {
      matches.push((this.indexOf(value) > -1));
    });

    if (all) {
      return _.all(matches);
    } else {
      return _.some(matches);
    }
  }
  return this.indexOf(value) > -1;
};

Array.prototype.compare = function(array) {
  // if the other array is a falsy value, return
  if (!array)
  {
    return false;
  }
    

  // compare lengths - can save a lot of time
  if (this.length !== array.length)
  {
    return false;
  }
    
  var i;
  for (i = 0, l = this.length; i < l; i++) {
    // Check if we have nested arrays
    if (this[i] instanceof Array && array[i] instanceof Array) {
      // recurse into the nested arrays
      if (!this[i].compare(array[i]))
      {
        return false;
      }
        
    } else if (this[i] !== array[i]) {
      // Warning - two different object instances will never be equal: {x:20} != {x:20}
      return false;
    }
  }
  return true;
};

Array.prototype.extend = function(other_array) {
  var that = this;
  angular.forEach(other_array, function(v) {
    that.push(v);
  });
};
