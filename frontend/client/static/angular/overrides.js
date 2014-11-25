/**
 *
 * Overrides for window scope
 */
(function () {

    'use strict';

    Array.prototype.remove = function (val) {

        var index = this.indexOf(val);
        this.splice(index, 1);

        return this;
    };

    Array.prototype.contains = function (value, all) {
        if (angular.isArray(value)) {
            var matches = [];

            angular.forEach(value, function (v) {
                matches.push((this.indexOf(value) > -1));
            });

            if (all) {
                return _.all(matches);
            }

            return _.some(matches);
        }
        return this.indexOf(value) > -1;
    };

    Array.prototype.compare = function (array) {
        // if the other array is a falsy value, return
        if (!array) {
            return false;
        }


        // compare lengths - can save a lot of time
        if (this.length !== array.length) {
            return false;
        }

        var i, l = this.length;
        for (i = 0; i < l; i++) {
            // Check if we have nested arrays
            if (this[i] instanceof Array && array[i] instanceof Array) {
                // recurse into the nested arrays
                if (!this[i].compare(array[i])) {
                    return false;
                }

            } else if (this[i] !== array[i]) {
                // Warning - two different object instances will never be equal: {x:20} != {x:20}
                return false;
            }
        }
        return true;
    };

    Array.prototype.prepend = function (other_array) {
        var that = this;
        angular.forEach(other_array, function (v) {
            that.unshift(v);
        });
    };

    Array.prototype.extend = function (other_array) {
        var that = this;
        angular.forEach(other_array, function (v) {
            that.push(v);
        });
    };


    function deepExtend (obj) {
        var parentRE = /#{\s*?_\s*?}/,
          slice = Array.prototype.slice,
          hasOwnProperty = Object.prototype.hasOwnProperty;

        _.each(slice.call(arguments, 1), function (source) {
            for (var prop in source) {
              if (hasOwnProperty.call(source, prop)) {
                if (_.isUndefined(obj[prop]) || _.isFunction(obj[prop]) || _.isNull(source[prop]) || _.isDate(source[prop])) {
                  obj[prop] = source[prop];
                }
                else if (_.isString(source[prop]) && parentRE.test(source[prop])) {
                  if (_.isString(obj[prop])) {
                    obj[prop] = source[prop].replace(parentRE, obj[prop]);
                  }
                }
                else if (_.isArray(obj[prop]) || _.isArray(source[prop])){
                  if (!_.isArray(obj[prop]) || !_.isArray(source[prop])){
                    throw 'Error: Trying to combine an array with a non-array (' + prop + ')';
                  } else {
                    obj[prop] = _.reject(_.deepExtend(obj[prop], source[prop]), function (item) { return _.isNull(item);});
                  }
                }
                else if (_.isObject(obj[prop]) || _.isObject(source[prop])){
                  if (!_.isObject(obj[prop]) || !_.isObject(source[prop])){
                    throw 'Error: Trying to combine an object with a non-object (' + prop + ')';
                  } else {
                    obj[prop] = _.deepExtend(obj[prop], source[prop]);
                  }
                } else {
                  obj[prop] = source[prop];
                }
              }
            }
        });
        return obj;
    };
     
    _.mixin({'deepExtend': deepExtend });

}());
