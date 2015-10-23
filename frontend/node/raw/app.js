if (!window.ng) {
    window.ng = function (fn) {
        return fn;
    };
}

function Steady(opts) {
  if ( !opts ) throw new Error('missing options');
  if ( !opts.handler ) throw new Error('missing handler parameter');


  this.scrollElement = opts.scrollElement || window;
  this.conditions = opts.conditions || {};
  this.handler   = opts.handler;
  this.values    = {};
  this.tracked   = {};
  this.success   = false;
  this.throttleVal = opts.throttle || 100;
  this.processing = false;
  this.stopped = false;


  this._parse();

  if ( 'pageYOffset' in this.scrollElement ) {
    this._addBottom();
    this._addTop();
  } else {
    this._addBottomEl();
    this._addTopEl();
    this._addScrollLeft();
  }

  this._addWidth();
  this._onScroll();

}


Steady.prototype.addCondition = function(name, value) {
  this.conditions[name] = value;
  this._parse();
};
Steady.prototype.removeCondition = function(name) {
  delete this.conditions[name];
  this._parse();
};
Steady.prototype.addTracker  = function(name, fn) {
  this.tracked[name] = { cb: fn, name: name};
};

Steady.prototype._addBottom = function() {
  this.addTracker('bottom', function(scrollable) {
    var height = Math.max(
      document.body.scrollHeight,
      document.body.offsetHeight, 
      document.documentElement.clientHeight,
      document.documentElement.scrollHeight,
      document.documentElement.offsetHeight
    );
    return height - (scrollable.pageYOffset + scrollable.innerHeight);
  });
};

Steady.prototype._addTop = function() {
  this.addTracker('top', function(scrollable) {
    return scrollable.pageYOffset;
  });
};

Steady.prototype._addBottomEl = function() {
  var self = this;
  this.addTracker('bottom', function(scrollable) {
    var height = Math.max(
      scrollable.scrollHeight,
      scrollable.offsetHeight
    );
    return height - ( scrollable.scrollTop + scrollable.offsetHeight);
  });
};

Steady.prototype._addTopEl = function() {
  this.addTracker('top', function(scrollable) {
    return scrollable.scrollTop;
  });
};

Steady.prototype._addScrollLeft = function() {
  var self = this;
  this.addTracker('scrollLeft', function(scrollable) {
    return scrollable.scrollLeft;
  });
};

Steady.prototype._addWidth = function() {
  this.addTracker('width', function(scrollable) {
    return scrollable.innerWidth;
  });
};


Steady.prototype._parse = function() {
  this._parsed = {};
  this._wantedTrackers = [];
  this._parsedMax = {};
  this._parsedMin = {};

  for ( var condition in this.conditions ) {
    if( !this.conditions.hasOwnProperty(condition) ) continue;
    
    var operator = condition.substr(0, 4);

    switch(operator) {
      case 'min-':
        this._wantedTrackers.push(condition.substr(4, condition.length));
        this._parsedMin[condition.substr(4, condition.length)] = this.conditions[condition];
        break;
      case 'max-':
        this._wantedTrackers.push(condition.substr(4, condition.length));
        this._parsedMax[condition.substr(4, condition.length)] = this.conditions[condition];
        break;
      default:
        this._wantedTrackers.push(condition);
        this._parsed[condition] = this.conditions[condition];
    }

  }
};

Steady.prototype._check = function() {
  var results = [];
  
  for( var name in this.values ) {
    if ( this._parsed.hasOwnProperty(name) ) {
      results.push( this._parsed[name] == this.values[name] );
    }
    if ( this._parsedMin.hasOwnProperty(name) ) {
      results.push( this._parsedMin[name] <= this.values[name] ); 
    }

    if ( this._parsedMax.hasOwnProperty(name) ) {
      results.push( this._parsedMax[name] >= this.values[name] );
    }
  }

  if ( results.length && results.indexOf(false) == -1 ) {
    this.processing = true;

    var cb = this._done.bind(this);
    window.requestAnimationFrame(this.handler.bind(this, this.values, cb));
  }
};

Steady.prototype._done = function() {
  this.processing = false;
};

Steady.prototype._onScroll = function() {
  this._onScrollHandler = this._throttledHandler();
  this.scrollElement.addEventListener('scroll', this._onScrollHandler, false);
};

Steady.prototype._throttledHandler = function() {
  var self = this;
  return this.throttle(function(e) {

    if ( !self._wantedTrackers.length || self.processing ) return;
    
    for (var i = 0; i < self._wantedTrackers.length; i++) {

      if ( !self.tracked[self._wantedTrackers[i]] ) continue;

      self.values[self._wantedTrackers[i]] = self.tracked[self._wantedTrackers[i]].cb(self.scrollElement || window);
    }
    
    window.requestAnimationFrame(self._check.bind(self));
  }, this.throttleVal);
};

Steady.prototype.stop = function() {
  if ( ! this.stopped  ) {
    this.scrollElement.removeEventListener('scroll', this._onScrollHandler, false);
    this.stopped = true;
  }
};

Steady.prototype.resume = function() {
  if ( this.stopped  ) 
    this._onScroll();
    this.stopped = false;
};


// i use it to avoid calling the onscroll function many times.
Steady.prototype.throttle = function(fn, delay) {
  var timer;
  var isFirstTime = true;
  return function () {
    var context = this;
    var args = arguments;

    if ( isFirstTime ) {
      fn.apply(context, args);
      isFirstTime = false;
      return;
    }

    if ( timer ) return;

    timer = true;
    setTimeout(function () {
      fn.apply(context, args);
      timer = false;
    }, delay);
  };
};


if (typeof module === 'object' && module.exports) {
  module.exports = Steady;
}

(function () {

    var base64EncodeChars =
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    var base64DecodeChars = new Array(-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -
        1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -
        1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 62, -1, -1, -
        1, 63,
        52, 53, 54, 55, 56, 57, 58, 59, 60, 61, -1, -1, -1, -1, -1, -1, -1, 0,
        1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14,
        15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, -1, -1, -1, -1, -1, -1, 26,
        27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40,
        41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, -1, -1, -1, -1, -1);

    function base64encode(str) {
        var out, i, len;
        var c1, c2, c3;

        len = str.length;
        i = 0;
        out = "";
        while (i < len) {
            c1 = str.charCodeAt(i++) & 0xff;
            if (i == len) {
                out += base64EncodeChars.charAt(c1 >> 2);
                out += base64EncodeChars.charAt((c1 & 0x3) << 4);
                out += "==";
                break;
            }
            c2 = str.charCodeAt(i++);
            if (i == len) {
                out += base64EncodeChars.charAt(c1 >> 2);
                out += base64EncodeChars.charAt(((c1 & 0x3) << 4) | ((c2 & 0xF0) >>
                    4));
                out += base64EncodeChars.charAt((c2 & 0xF) << 2);
                out += "=";
                break;
            }
            c3 = str.charCodeAt(i++);
            out += base64EncodeChars.charAt(c1 >> 2);
            out += base64EncodeChars.charAt(((c1 & 0x3) << 4) | ((c2 & 0xF0) >>
                4));
            out += base64EncodeChars.charAt(((c2 & 0xF) << 2) | ((c3 & 0xC0) >>
                6));
            out += base64EncodeChars.charAt(c3 & 0x3F);
        }
        return out;
    }

    function base64decode(str) {
        var c1, c2, c3, c4;
        var i, len, out;

        len = str.length;
        i = 0;
        out = "";
        while (i < len) {
            /* c1 */
            do {
                c1 = base64DecodeChars[str.charCodeAt(i++) & 0xff];
            } while (i < len && c1 == -1);
            if (c1 == -1)
                break;

            /* c2 */
            do {
                c2 = base64DecodeChars[str.charCodeAt(i++) & 0xff];
            } while (i < len && c2 == -1);
            if (c2 == -1)
                break;

            out += String.fromCharCode((c1 << 2) | ((c2 & 0x30) >> 4));

            /* c3 */
            do {
                c3 = str.charCodeAt(i++) & 0xff;
                if (c3 == 61)
                    return out;
                c3 = base64DecodeChars[c3];
            } while (i < len && c3 == -1);
            if (c3 == -1)
                break;

            out += String.fromCharCode(((c2 & 0XF) << 4) | ((c3 & 0x3C) >> 2));

            /* c4 */
            do {
                c4 = str.charCodeAt(i++) & 0xff;
                if (c4 == 61)
                    return out;
                c4 = base64DecodeChars[H4];
            } while (i < len && c4 == -1);
            if (c4 == -1)
                break;
            out += String.fromCharCode(((c3 & 0x03) << 6) | c4);
        }
        return out;
    }

    if (!window.btoa) window.btoa = base64encode;
    if (!window.atob) window.atob = base64decode;

})();

// Production steps of ECMA-262, Edition 5, 15.4.4.14
// Reference: http://es5.github.io/#x15.4.4.14
if (!Array.prototype.indexOf) {
  Array.prototype.indexOf = function(searchElement, fromIndex) {

    var k;

    // 1. Let O be the result of calling ToObject passing
    //    the this value as the argument.
    if (this == null) {
      throw new TypeError('"this" is null or not defined');
    }

    var O = Object(this);

    // 2. Let lenValue be the result of calling the Get
    //    internal method of O with the argument "length".
    // 3. Let len be ToUint32(lenValue).
    var len = O.length >>> 0;

    // 4. If len is 0, return -1.
    if (len === 0) {
      return -1;
    }

    // 5. If argument fromIndex was passed let n be
    //    ToInteger(fromIndex); else let n be 0.
    var n = +fromIndex || 0;

    if (Math.abs(n) === Infinity) {
      n = 0;
    }

    // 6. If n >= len, return -1.
    if (n >= len) {
      return -1;
    }

    // 7. If n >= 0, then Let k be n.
    // 8. Else, n<0, Let k be len - abs(n).
    //    If k is less than 0, then let k be 0.
    k = Math.max(n >= 0 ? n : len - Math.abs(n), 0);

    // 9. Repeat, while k < len
    while (k < len) {
      // a. Let Pk be ToString(k).
      //   This is implicit for LHS operands of the in operator
      // b. Let kPresent be the result of calling the
      //    HasProperty internal method of O with argument Pk.
      //   This step can be combined with c
      // c. If kPresent is true, then
      //    i.  Let elementK be the result of calling the Get
      //        internal method of O with the argument ToString(k).
      //   ii.  Let same be the result of applying the
      //        Strict Equality Comparison Algorithm to
      //        searchElement and elementK.
      //  iii.  If same is true, return k.
      if (k in O && O[k] === searchElement) {
        return k;
      }
      k++;
    }
    return -1;
  };
}
/**
 *
 * Overrides for window scope
 */
(function () {

    'use strict';

    Array.prototype.iremove = function (callback) {
        var i = this.length;
        while (i--) {
            if (callback(this[i], i)) {
                this.splice(i, 1);
            }
        }
    };

    Array.prototype.remove = function (val) {
        var index = this.indexOf(val);
        if (index !== -1) {
            this.splice(index, 1);
        }
        return this;
    };

    Array.prototype.empty = function (val) {
        this.splice(0, this.length);
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

    // attach the .equals method to Array's prototype to call it on any array
    Array.prototype.equals = function (array) {
        // if the other array is a falsy value, return
        if (!array)
            return false;

        // compare lengths - can save a lot of time 
        if (this.length !== array.length) {
            return false;
        }

        for (var i = 0, l=this.length; i < l; i++) {
            // Check if we have nested arrays
            if (this[i] instanceof Array && array[i] instanceof Array) {
                // recurse into the nested arrays
                if (!this[i].equals(array[i])) {
                    return false;
                }        
            }           
            else if (this[i] !== array[i]) { 
                // Warning - two different object instances will never be equal: {x:20} != {x:20}
                return false;   
            }           
        }       
        return true;
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

}());
// bootstrap file, introduces global App or MainApp
(function () {

    'use strict';

    if (!window.console) {
        window.console = {};
    }

    angular.forEach(['log', 'error', 'trace', 'debug', 'info'], function (method) {
        if (!window.console[method]) {
            window.console[method] = angular.noop;
        }
    });

    var host = window.location.protocol + '//' + window.location.host,
        // global configuration for the application
        // this config file will expand
        GLOBAL_CONFIG = {
            debug: true, // debug mode
            host: host,
            modules: ['config', 
                      'ngAnimate', 
                      'ngMessages', 
                      'ui.router', 
                      'ui.sortable', 
                      'ui.inflector', 'ngSanitize',
                      'ngDragDrop',
                      'timer', 
                      'googlechart',
                      'btford.markdown',
                      'material.core',
                      'material.core.gestures',
                      'material.components.button',
                      'material.components.checkbox',
                      'material.components.content',
                      'material.components.simpledialog',
                      'material.components.input',
                      'material.components.radioButton',
                      'material.components.sidenav',
                      'material.components.swipe',
                      'material.components.textField',
                      'material.components.toolbar'], // this will be changed accordingly
            api: {
                endpoint: {
                    path: host + '/api/endpoint'
                },
                modelsMeta: '/api/model_meta'
            },
            date: {
                format: 'd MMM yyyy, HH:mm'
            },
            toolbar: {
                titles: {}
            },
            snackbar: {
                messages: {}
            },
            subheaders: {},
            fields: {
                help: {},
                label: {},
                translateChoices: {},
                emptyHelp: {}
            },
            sellerPluginName: {},
            labels: {},
            modals: {
                confirmations: {},
                alerts: {}
            },
            defaultImage: 'http://placehold.it/240x100',
            defaultLogo: '/client/dist/static/720x300_placeholder.png',
            defaultCatalogCover: 'http://placehold.it/240x240',
            grid: {
                maxWidth: 240,
                minWidth: 180,
                maxHeight: 360,
                margin: 1
            },
            emptyHelp: {},
            imageSizes: _.range(50, 1650, 50), // loading ranges for get serving url
            social: {
                facebook: {
                    id: '125702284258635'
                }
            },
            admin: {
                listTemplates: {},
                menu: [{name: 'Accounts', kind: 11}, {name: 'Catalogs', kind: 31}, {name: 'Orders', kind: '34'}], // admin paths shown in the menu
                listViewDirective: {
                    31: true,
                    11: true,
                    34: true
                },
                listTitles: {
                    '31': 'catalogs',
                    '11': 'users',
                    '34': 'orders'
                }
            }
        };

    if (GLOBAL_CONFIG.debug) {
        window._GLOBAL_CONFIG = GLOBAL_CONFIG;
    }
 
    angular.module('config', ['ng'])
        .constant('GLOBAL_CONFIG', GLOBAL_CONFIG)
        .config(ng(function ($httpProvider, $locationProvider) {
            $httpProvider.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';
            $locationProvider.hashPrefix('!');
            $locationProvider.html5Mode(true);
        }));
    angular.module('app', GLOBAL_CONFIG.modules);
}());

$(function () {
    'use strict';
    var container = $('<div>').css({ height: 1, overflow: 'scroll' }).appendTo('body'),
        child = $('<div>').css({ height: 2 }).appendTo(container);
    window.SCROLLBAR_WIDTH = container.width() - child.width();
    if (Modernizr.touch) {
        window.SCROLLBAR_WIDTH = 0;
    }
    container.remove();
});
/* Bootstrap, it will try to load current account and model data and then bootstrap the application. */
(function () {
    'use strict';
    angular.element(document).ready(function () {
        var failure = function () {
                var choice = confirm('Could not start application. Reload your browser and try again?');
                if (choice) {
                    window.location.reload(true);
                }
            },
            injector = angular.injector(['config']),
            $http = injector.get('$http'),
            $q = injector.get('$q'),
            GLOBAL_CONFIG = injector.get('GLOBAL_CONFIG'),
            promises = [$http.get(GLOBAL_CONFIG.api.modelsMeta), $http.get(GLOBAL_CONFIG.api.endpoint.path + '?action_id=current_account&action_model=11')];

        $q.all(promises).then(function (response) {
            var d1 = response[0].data, d2 = response[1].data;
            window.MODELS_META = d1;
            window.CURRENT_ACCOUNT = d2.entity;
            if ((d1 && d1.errors) || (d2 && d2.errors)) {
                failure();
            } else {
                angular.bootstrap(document, ['app'], {
                      strictDi: !window.DEBUG
                    });
            }
        }, failure);

    });
}());(function () {
    'use strict';
    angular.module('app').factory('errorHandling', ng(function ($modal, snackbar, GLOBAL_CONFIG, modals) {
        var translations = GLOBAL_CONFIG.backendErrorHandling,
            errorHandling = {
                translate: function (k, v) {
                    var possible = translations[k];
                    if (angular.isString(possible)) {
                        return possible;
                    }
                    if (angular.isFunction(possible)) {
                        return possible(v);
                    }
                    return v;
                },
                modal: function (errors) {
                    modals.alert(null, {
                        title: 'Error while performing an action',
                        templateUrl: 'core/misc/errors.html',
                        text: {
                            primary: 'Got it'
                        },
                        errors: (function () {
                            var formatErrors = [];
                            angular.forEach(errors, function (error, key) {
                                formatErrors.push([key, errorHandling.translate(key, error)]);
                            });
                            return formatErrors;
                        }())
                    });
                },
                snackbar: function (errors, callback) {
                    if (errors.traceback) {
                        return snackbar.showK('errorWithTraceback');
                        //return errorHandling.modal(errors);
                    }
                    var messages = (function () {
                            var formatErrors = [];
                            angular.forEach(errors, function (error, key) {
                                formatErrors.push(errorHandling.translate(key, error));
                            });
                            return formatErrors;
                        }()).join('\n'),
                        other;

                    if (callback) {
                        other = callback(errors);
                        if (other !== false) {
                            messages = other;
                        }
                    }

                    snackbar.show(messages);
                }
            };

        return errorHandling;
    })).factory('helpers', ng(function (GLOBAL_CONFIG) {

        var helpers = {
            callable: function (fn) {
                if (angular.isFunction(fn)) {
                    return fn;
                }
                return angular.noop;
            },
            alwaysObject: function (obj) {
                if (!angular.isObject(obj)) {
                    return {};
                }
                return obj;
            },
            splitLines: function (val) {
                return val.match(/[^\r\n]+/g);
            },
            addslashes: function (str) {
                return (str.toString()).replace(/[\\"']/g, '\\$&').replace(/\u0000/g, '\\0');
            },
            resolveDefaults: function (defaults, options) {
                options = helpers.alwaysObject(options);

                angular.forEach(defaults, function (value, key) {
                    if (!angular.isUndefined(options[key])) {
                        options[key] = value;
                    }
                });

                return options;
            },
            setProperty: function (obj, prop, value) {
                //console.trace('helpers.setProperty', obj, prop, value);
                var path = prop,
                    of,
                    last;
                if (!angular.isArray(prop)) {
                    prop = prop.split('.');
                    path = prop;
                }
                last = _.last(path);
                path = path.slice(0, path.length - 1);
                if (!path.length) {
                    obj[prop.join('')] = value;
                    return;
                }
                of = this.getProperty(obj, path);
                of[last] = value;
            },
            forceSetProperty: function (obj, prop, value) {
                var next = obj,
                    prev,
                    last;
                if (!angular.isArray(prop)) {
                    prop = prop.split('.');
                }
                if (prop.length === 1) {
                    obj[prop.join('')] = value;
                    return;
                }
                angular.forEach(prop, function (key, i) {
                    prev = next;
                    next = next[key];
                    last = i === (prop.length - 1);
                    if (angular.isUndefined(next) && !last) {
                        next = {};
                        prev[key] = next;
                    }

                    if (last) {
                        prev[key] = value;
                    }
                });
            },
            getProperty: function (obj, prop, defaultMaybe) {
                //console.trace('helpers.getProperty', obj, prop);
                var path = prop;
                if (!angular.isArray(path)) {
                    path = prop.split('.');
                }
                angular.forEach(path, function (path) {
                    try {
                        obj = obj[path];
                    } catch (e) {
                        return defaultMaybe;
                    }
                });
                if (angular.isUndefined(obj)) {
                    return defaultMaybe;
                }
                return obj;

            },
            extendDeep: function (dst) {
                angular.forEach(arguments, function (obj) {
                    if (obj !== dst) {
                        angular.forEach(obj, function (value, key) {
                            if (dst[key] && angular.isObject(dst[key])) {
                                helpers.extendDeep(dst[key], value);
                            } else {
                                dst[key] = value;
                            }
                        });
                    }
                });
                return dst;
            },
            extend: function (dst) {
                angular.forEach(arguments, function (obj) {
                    if (obj !== dst) {
                        angular.forEach(obj, function (value, key) {
                            dst[key] = value;
                        });
                    }
                });
                return dst;
            },
            merge: function (dst) {
                angular.forEach(arguments, function (obj) {
                    if (obj !== dst) {
                        angular.forEach(obj, function (value, key) {
                            if (!angular.isDefined(dst[key])) {
                                dst[key] = value;
                            }
                        });
                    }
                });
                return dst;
            },
            mergeDeep: function (dst) {
                angular.forEach(arguments, function (obj) {
                    if (obj !== dst) {
                        angular.forEach(obj, function (value, key) {
                            if (dst[key] && angular.isObject(dst[key])) {
                                helpers.mergeDeep(dst[key], value);
                            } else if (!angular.isDefined(dst[key])) {
                                dst[key] = value;
                            }
                        });
                    }
                });
                return dst;
            },
            update: function (obj1, obj2, paths) {
                if (angular.isDefined(paths)) {
                    angular.forEach(paths, function (path) {
                        var val1 = helpers.getProperty(obj2, path);
                        helpers.setProperty(obj1, path, val1);
                    });
                } else {
                    $.extend(obj1, obj2); // shallow merge
                }
            }
        };
        if (GLOBAL_CONFIG.debug) {
            window._helpers = helpers;
        }
        return helpers;
    })).factory('endpoint', ng(function ($http, generalLocalCache, GLOBAL_CONFIG,
        helpers, modelsUtil, $rootScope, $q, $cacheFactory, $injector) {

        var onlyInMemoryCache = $cacheFactory('endpointOnlyInMemory'),
            getCache = function (type) {
                if (type === undefined || type === 'local') {
                    return generalLocalCache;
                }
                if (type === 'memory') {
                    return onlyInMemoryCache;
                }
                console.error('Invalid type of cache provided: ' + type);
            },
            _compile = function (action, model, data, config) {
                config = helpers.alwaysObject(config);
                data = helpers.alwaysObject(data);

                return [angular.extend({
                    action_model: model,
                    action_id: action
                }, data), config];

            },
            cache_prefix = 'endpoint_',
            cacheRegistry = [],
            endpoint;

        cacheRegistry.push(onlyInMemoryCache);
        cacheRegistry.push(generalLocalCache);

        endpoint = {
            getCache: function (key) {
                var result = null;
                angular.forEach(cacheRegistry, function (cache) {
                    if (!result) {
                        result = cache.get(cache_prefix + key);
                    }
                });
                return result;
            },
            removeCache: function (key) {

                if (!angular.isDefined(key)) {
                    angular.forEach(cacheRegistry, function (cache) {
                        cache.removeAll();
                    });
                    return true;
                }
                if (angular.isArray(key)) {
                    angular.forEach(key, function (k) {
                        endpoint.removeCache(k);
                    });

                    return true;
                }

                angular.forEach(cacheRegistry, function (cache) {
                    cache.remove(cache_prefix + key);
                });

            },
            url: GLOBAL_CONFIG.api.endpoint.path,
            cached: function (key, action, model, data, config) {
                var cacheEngine = getCache(config ? config.cacheType : undefined),
                    cache_key = cache_prefix + key,
                    exists = cacheEngine.get(cache_key),
                    is_promise = (exists && angular.isFunction(exists.then)),
                    deffered,
                    promise;
                if (is_promise) {
                    return exists;
                }
                if (exists === undefined) {
                    promise = endpoint[config.method ? config.method.toLowerCase() : 'post'](action, model, data, config);
                    promise.then(function (response) {
                        cacheEngine.put(cache_key, response);
                    }, function () {
                        cacheEngine.remove(cache_key);
                    });
                    cacheEngine.put(cache_key, promise);
                    return promise;
                }

                deffered = $q.defer();
                promise = deffered.promise;
                deffered.resolve(exists);
                return promise;


            },
            post: function (action, model, data, config) {
                var compiled = _compile(action, model, data, config),
                    defaults = {
                        method: 'POST',
                        url: endpoint.url
                    },
                    cache_id;
                compiled[0] = modelsUtil.argumentsToJson(compiled[0]);
                if (compiled[1] && angular.isString(compiled[1].cache)) {
                    cache_id = compiled[1].cache;
                    compiled[1].cache = false;
                    // avoid recursion
                    return endpoint.cached(cache_id, action, model, data, compiled[1]);
                }
                angular.extend(defaults, compiled[1]);
                defaults.data = compiled[0];
                return $http(defaults);
            },
            get: function (action, model, data, config) {
                var compiled = _compile(action, model, data, config),
                    gets = {
                        params: compiled[0]
                    },
                    defaults = {
                        method: 'GET',
                        url: endpoint.url
                    },
                    cache_id;
                compiled[0] = modelsUtil.argumentsToJson(compiled[0]);
                $.extend(gets, compiled[1]);
                angular.extend(defaults, gets);
                if (defaults && angular.isString(defaults.cache)) {
                    cache_id = defaults.cache;
                    defaults.cache = false;
                    return endpoint.cached(cache_id, action, model, data, gets);
                }
                return $http(defaults);
            }
        };

        if (GLOBAL_CONFIG.debug) {
            window._endpoint = endpoint;
        }

        return endpoint;

    })).factory('generalLocalCache', ng(function (DSCacheFactory, $cacheFactory) {
        // combination of LocalStorageCache and inMemory cache
        var inMemory = $cacheFactory('localStoragePolyfillInMemory'),
            // in memory cache for non-serizible jsons
            nothing = '___undefined___',
            memory_only = '___in_memory_only___',
            localStoragePolyfill,
            generalLocalCache;

        function prepare(key, val) {
            if (val && ((val.value && angular.isFunction(val.value.then)) || (angular.isObject(val.value) && val.value[memory_only] !== undefined))) {
                return nothing;
            }
            return angular.toJson(val);
        }

        localStoragePolyfill = {
            getItem: function (key) {
                var out = inMemory.get(key);
                if (out && angular.isObject(out) && out[memory_only] !== undefined) {
                    out = out[memory_only];
                }
                if (out === undefined) {
                    // this done to prevent constant json deserializations / serializations
                    out = localStorage.getItem(key);
                }
                if (out !== nothing) {
                    return out;
                }
                return undefined;
            },
            setItem: function (key, value) {
                var yes;
                inMemory.put(key, value);
                value = prepare(key, value);
                try {
                    yes = localStorage.setItem(key, value);
                } catch (ignore) {} // in case the localStorage is full it throws error
                return yes;
            },
            removeItem: function (key) {
                inMemory.remove(key);
                return localStorage.removeItem(key);
            }
        };
        generalLocalCache = DSCacheFactory('generalCache', {
            storageMode: 'localStorage',
            storageImpl: localStoragePolyfill
        });

        generalLocalCache.inMemory = function (value) {
            var only_in_memory = {};
            only_in_memory[memory_only] = value;
            return only_in_memory;
        };

        return generalLocalCache;

    })).run(ng(function ($http, generalLocalCache) {

        $http.defaults.cache = generalLocalCache;

    })).config(['$httpProvider', function ($httpProvider) {

        $httpProvider.interceptors.push(['$rootScope', '$q', '$injector',
            function ($rootScope, $q, $injector) {

                var handleResponse = function (rejection) {

                    var data = rejection.data,
                        normalizeEntity = (rejection.config.normalizeEntity === undefined || rejection.config.normalizeEntity),
                        errorHandling = $injector.get('errorHandling'),
                        modelsUtil = $injector.get('modelsUtil'),
                        enableUI = function () {
                            $rootScope.$broadcast('disableUI', false);
                        },
                        reject,
                        shouldDisable = (rejection.config.disableUI === undefined || rejection.config.disableUI === true);

                    if (!rejection.config.ignoreErrors) {

                        if (rejection.status > 200) {
                            errorHandling.snackbar(angular.isString(rejection.data) ? {
                                traceback: rejection.data
                            } : rejection.data.errors, rejection.config.handleError);
                            if (shouldDisable) {
                                enableUI();
                            }
                            return $q.reject(rejection);
                        }
                        if (data && data.errors) {
                            errorHandling.snackbar(rejection.data.errors, rejection.config.handleError);
                            reject = (rejection.config.rejectOnErrors === undefined || rejection.config.rejectOnErrors === true);
                            if (data.errors.action_denied) {
                                reject = true;
                            }
                            if (reject && shouldDisable) {
                                enableUI();
                                return $q.reject(rejection);
                            }

                        }
                    }

                    if (normalizeEntity && data) {
                        if (angular.isDefined(data.entities)) {
                            modelsUtil.normalizeMultiple(data.entities);
                        } else if (angular.isDefined(data.entity)) {
                            modelsUtil.normalize(data.entity);
                        }

                    }
                    if (shouldDisable) {
                        enableUI();
                    }
                    // otherwise, default behaviour
                    return rejection || $q.when(rejection);

                };

                return {
                    response: handleResponse,
                    responseError: handleResponse,
                    request: function (config) {
                        var shouldDisable = (config.disableUI === undefined || config.disableUI === true);
                        if (shouldDisable) {
                            $rootScope.$broadcast('disableUI', true);
                        }
                        return config || $q.when(config);
                    }
                };
            }
        ]);

    }]).factory('underscoreTemplate', ng(function ($templateCache) {

        return {
            get: function (path) {
                return _.template($templateCache.get(path));
            }
        };
    })).factory('animationGenerator', function () {
        var animationGenerator = {
            classNamePrefix: 'tmp-',
            prefix: function (thing) {
                return (/WebKit/.test(navigator.userAgent) ? '-webkit-' : '') + thing;
            },
            compile: function (props) {
                var str = '';
                angular.forEach(props, function (value, key) {
                    str += animationGenerator.prefix(key) + ': ' + value + ';' + "\n";
                });
                return str;
            },
            make: function (name, definition) {
                var str = '@' + animationGenerator.prefix('keyframes') + ' ' + name + ' {' + "\n";

                str += definition;

                str += "\n" + '} .' + animationGenerator.classNamePrefix + name + '{' + animationGenerator.prefix('animation-name') + ':' + name + ';}';
                return str;
            },
            single: function (name, codes) {
                var nextuid = _.uniqueId(),
                    id = 'temporary-animator' + nextuid,
                    style = $('#' + id);
                name = name + nextuid;
                if (!style.length) {
                    style = $('<style/>').attr('id', id);
                    style.appendTo('head');
                }
                style.text(animationGenerator.make(name, codes));
                return {
                    name: name,
                    className: animationGenerator.classNamePrefix + name,
                    destroy: function () {
                        style.remove();
                    }
                };
            }
        };
        return animationGenerator;
    });
}());
(function () {
    'use strict';

    angular.module('app').config(ng(function (GLOBAL_CONFIG) {
        var locals = {};

        $.extend(GLOBAL_CONFIG.modals.confirmations, {
            discardWithFieldsRequired: {
                title: 'Discard changes?',
                message: 'There are some invalid changes on the form you are trying to leave. If you discard them, the changes will not be applied and will be lost permanently.',
                text: {
                    primary: 'Discard'
                }
            },
            disconnectSignInMethod: {
                title: 'Disconnect the identity?',
                message: 'If this is the only sign in identity connected to your Miraclestyle account, you will permanently lose access to the account and all of its data after this action is completed!',
                text: {
                    primary: 'Disconnect'
                }
            },
            removePricetagConfirm: {
                title: 'Remove the product?',
                message: 'The product will be permanently removed from the catalog! You will be notified once this action is completed.',
                text: {
                    primary: 'Remove'
                }
            },
            connectSignInMethod: {
                title: 'Connect the identity?',
                message: 'If this sign in identity is already connected to another Miraclestyle account, you will have to disconnect it before you proceed with this action!',
                text: {
                    primary: 'Connect'
                }
            },
            discard: {
                title: 'Discard unsaved changes?',
                message: 'There are some unsaved changes on the form you are trying to close. If you discard them, the changes will be lost permanently, and the form will revert to previously saved state.',
                text: {
                    primary: 'Discard'
                }
            },
            maybeLogout: {
                title: 'Confirm sign out',
                message: 'Are you sure you want to sign out?',
                text: {
                    primary: 'Sign out'
                },
            },
            cancelOrder: {
                title: 'Reset the cart?',
                message: 'This cart will be emptied, and all of its settings will be lost after this action is completed.',
                text: {
                    primary: 'Reset'
                }
            },
            toCheckout: {
                title: 'Review the cart?',
                message: 'You won\'t be able to update the cart after this step. However, you will be able to reset the cart, or place an order by making a payment.',
                text: {
                    primary: 'Review'
                }
            },
            publishCatalog: {
                title: 'Publish the catalog?',
                message: 'A published catalog is accessible to the general public and can be shared and embedded to third party websites. With an exception of a product "Availability" field, a published catalog cannot be edited. However, a published catalog can be duplicated, and the duplicate is ready for editing. You will be notified once this action is completed.',
                text: {
                    primary: 'Publish'
                }
            },
            discontinueCatalog: {
                title: 'Discontinue the catalog?',
                message: 'A discontinued catalog is not accessible to the general public and is eventually entirely removed from the Miraclestyle app. However, products of a discontinued catalog remain accessible for the 180 days to those who have purchased them. A discontinued catalog cannot be edited or duplicated. You will be notified once this action is completed.',
                text: {
                    primary: 'Discontinue'
                }
            },
            duplicateCatalogPricetag: {
                title: 'Schedule duplication?',
                message: 'Duplication can take a while to complete! You will be notified once this action is completed.',
                text: {
                    primary: 'Schedule'
                }
            },
            duplicateCatalog: {
                title: 'Schedule duplication?',
                message: 'Duplication can take a while to complete! You will be notified once this action is completed.',
                text: {
                    primary: 'Schedule'
                }
            }
        });

        locals.gotit = {
            primary: 'Got it'
        };

        $.extend(GLOBAL_CONFIG.modals.alerts, {
            howToSort: {
                title: 'How to use this action',
                messages: ['Reorder the item by dragging it within its group.',
                    'Remove the item by dragging it outside the left edge of the screen.'
                ],
                text: locals.gotit
            },
            howToDeleteDragging: {
                title: 'How to use this action',
                message: 'Remove the item by dragging it outside the left edge of the screen.',
                text: locals.gotit
            },
            howToDropPricetag: {
                title: 'How to use this action',
                messages: ['Add a new product to the catalog by dragging the "Add" tag to a catalog image. While dragging, it is preferable to aim the tag dot for the image area that shows the product that the tag will link to. Add one tag per product per catalog.',
                    'Reposition a tag by dragging it within images area.',
                    'Click on a tag to open the "Edit Product" form while editing the catalog.',
                    'Click on a tag to open the product view while viewing the catalog.'
                ],
                text: locals.gotit
            }
        });


        $.extend(GLOBAL_CONFIG.labels, {
            account: {
                active: 'Active',
                suspended: 'Suspended'
            },
            catalog: {
                draft: 'Draft',
                published: 'Published',
                discontinued: 'Discontinued',
                unindex: 'Unindex',
                index: 'Index'
            },
            order: {
                cart: 'Cart',
                checkout: 'Checkout',
                completed: 'Completed',
                canceled: 'Canceled',
                positive: 'Positive',
                negative: 'Negative',
                neutral: 'Neutral',
                revision: 'Review',
                reported: 'Reported',
                sudo: 'Administered',
                review: 'Review'
            }
        });

        locals.fieldhelpForProduct = {
            weight: 'Product weight, expressed in kilograms, per unit of measurement. This field is used by the Carrier rule for calculating delivery costs.',
            volume: 'Product volume, expressed in liters, per unit of measurement. This field is used by the Carrier rule for calculating delivery costs.'
        };

        $.extend(GLOBAL_CONFIG.fields.help, {
            '124-update': {
                condition_type: 'Condition under which this line applies.',
                price_type: 'Price formula that calculates this price.'
            },
            '106': {
                postal_codes: 'Postal codes this location affects. Specify one postal code per line.'
            },
            '108': {
                reciever_email: 'Primary email address for your PayPal account.',
                business: 'Email address on which you want to receive your PayPal payments. This value will be the same as "Receiver Email" in case that you have only one email address associated with your PayPal account.'
            },
            '109': {
                product_codes: 'Specific product codes this rule applies to. Specify one product code per line.',
                address_type: 'Buyer address type this rule applies to.'
            },
            '124': {
                product_codes: 'Specific product codes this line applies to. Specify one product code per line.'
            },
            '117': {
                currency: 'Currency you accept, and your product unit prices are expressed in.'
            },
            '111-update': {
                condition_type: 'Condition under which this price applies.',
                price_type: 'Price formula that calculates this price.'
            },
            '23-update': {
                name: 'Name of the brand, company, or store that you represent.',
                logo: 'Click on the logo above to upload logo image of the brand, company, or store that you represent. Logo must be of 2.4:1 aspect ratio, preferably 720 pixels wide and 300 pixels high.'
            },
            '14': {
                name: 'Recipient\'s full name or business name.'
            },
            '107': {
                address_type: 'Buyer address type this rule applies to.'
            },
            '27': locals.fieldhelpForProduct,
            '28': locals.fieldhelpForProduct,
            '31-update': {
                discontinue_date: 'Date when this catalog will be automatically discontinued and become unavailable to the general public.'
            },
            '26': {
                name: 'Name of the variant input control that is visible on the product view.',
                options: 'Options that are available for selection on the variant input control. Specify one option per line.',
                description: 'Brief description visible beneath the variant input control.',
                allow_custom_value: 'If enabled, options defined above will be ignored, and buyers will be able to supply a custom value in the variant input control'
            }
        });

        $.extend(GLOBAL_CONFIG.fields.label, {
            search: {
                indexID: 'Search options',
                ancestor: 'Ancestor',
                operator: 'Operator'
            },
            plugins: {
                kind: 'Rule'
            },
            '28': {
                uom: 'Unit of measurement',
                variant_options: 'Select all variant options you want this configuration to be matched with',
                weight: 'Weight (kilogram)',
                volume: 'Volume (liter)'
            },
            '27': {
                uom: 'Unit of measurement',
                weight: 'Weight (kilogram)',
                volume: 'Volume (liter)'
            },
            '109': {
                carriers: 'Carriers this rule applies to'
            },
            '112': {
                rules: 'Prices'
            },
            '124': {
                discount_value: 'Discount (%)',
                product_categories: 'Product categories'
            },
            '31-update': {
                discontinue_date: 'Expiration date'
            },
            '124-update': {
                condition_type: 'Condition',
                price_type: 'Price'
            },
            '111-update': {
                condition_type: 'Condition',
                price_type: 'Price'
            },
            '23-update': {
                logo: 'Seller logo'
            },
            '18-update': {
                notify: 'Receive email notifications when a catalog is published or discontinued by the seller that you are following'
            }
        });

        locals.conditionOperatorSpec = {
            '==': 'equals to',
            '!=': 'is not equal to',
            '>': 'is greater than',
            '<': 'is less than',
            '>=': 'is greater than or equal to',
            '<=': 'is less than or equal to'
        };
        locals.addressTypeSpec = {
            billing: 'Billing',
            shipping: 'Shipping'
        };
        locals.conditionTypeSpec = {
            weight: 'weight',
            volume: 'volume',
            'weight*volume': 'weight multiplied by volume',
            price: 'price',
            quantity: 'quantity'
        };
        $.extend(GLOBAL_CONFIG.fields.translateChoices, {
            '107': {
                address_type: locals.addressTypeSpec
            },
            '109': {
                address_type: locals.addressTypeSpec,
                type: {
                    proportional: 'Proportional (%)',
                    fixed: 'Fixed (Amount)'
                }
            },
            '111': {
                condition_type: locals.conditionTypeSpec,
                condition_operator: locals.conditionOperatorSpec,
                price_type: {
                    fixed: 'fixed',
                    variable: 'varied by'
                },
                price_operator: {
                     weight: 'weight multiplied by',
                     volume: 'volume multiplied by',
                     'weight*volume': 'weight multiplied by volume multiplied by',
                     price: 'price multiplied by',
                     quantity: 'quantity multiplied by'
                 }
            },
            '124': {
                condition_operator: locals.conditionOperatorSpec
            },
            rules: {
                kind: {
                    '109': 'Tax',
                    '126': 'Discount',
                    '107': 'Address',
                    '117': 'Currency',
                    '108': 'PayPal',
                    '113': 'Carrier'
                }
            }
        });


        $.extend(GLOBAL_CONFIG.fields.emptyHelp, {
            '19-update': {
                addresses: 'buyer/help/addresses.html'
            },
            '31-update': {
                _images: 'catalog/help/images.html'
            },
            '109': {
                carriers: 'seller/help/carriers.html',
                product_categories: 'seller/help/product_categories.html',
                locations: 'seller/help/locations.html'
            },
            '124': {
                product_categories: 'seller/help/product_categories_line.html'
            },
            '113': {
                lines: 'seller/help/carrier_lines.html',
            },
            '112': {
                locations: 'seller/help/locations_line.html',
                prices: 'seller/help/prices.html',
            },
            '126': {
                lines: 'seller/help/discount_lines.html'
            },
            '107': {
                locations: 'seller/help/locations.html'
            },
            '28': {
                images: 'catalog/product/help/images.html',
                contents: 'catalog/product/help/contents.html',
                variants: 'catalog/product/help/variants.html',
                _instances: 'catalog/product/help/instances.html'
            },
            '27': {
                images: 'catalog/product/help/images.html',
                contents: 'catalog/product/help/contents.html',
                variant_options: 'catalog/product/help/variant_options.html'
            },
            '21': {
                documents: 'seller/help/contents.html'
            }
        });

        if (!GLOBAL_CONFIG.fields.radioLabel) {
            GLOBAL_CONFIG.fields.radioLabel = {};
        }

        $.extend(GLOBAL_CONFIG.fields.radioLabel, {
            pluginLocation: {
                falseLabel: 'Applies to all locations except those listed in the Locations section',
                trueLabel: 'Applies only to the locations listed in the Locations section'
            }
        });

        $.extend(GLOBAL_CONFIG.subheaders, {
            loginMethods: 'Sign in identities',
            productInstances: 'Variant configurations',
            catalogImages: 'Images',
            catalogProducts: 'Products',
            collectionSeller: 'Sellers',
            history: 'History',
            record: 'Log Entry',
            sellerContents: 'Contents',
            sellerPlugins: 'Rules'
        });

        $.extend(GLOBAL_CONFIG.emptyHelp, {
            orderSellerList: 'seller/help/orders.html',
            cartSellerList: 'seller/help/carts.html',
            orderBuyerList: 'buyer/help/orders.html',
            cartBuyerList: 'buyer/help/carts.html',
            catalogList: 'catalog/help/list.html',
            cart: 'order/help/empty.html',
            cartMessages: 'order/help/messages.html',
            following: 'collection/help/sellers.html',
            sellerProfileCatalogList: 'seller/help/profile_catalogs.html'
        });

        $.extend(GLOBAL_CONFIG.snackbar.messages, {
            changesSaved: 'Changes saved.',
            cartUpdated: 'Cart updated.',
            catalogPublished: 'Catalog published.',
            catalogDiscontinued: 'Catalog discontinued.',
            duplicationInProgressCatalog: 'Catalog scheduled for duplication.',
            administered: 'Administered.',
            identityDisconnected: 'Identity disconnected.',
            identityConnected: 'Identity connected.',
            createVariantsFirst: 'Create some variants first.',
            saveProductFirst: 'Save product first.',
            provideProperValues: 'Provide proper values in the form fields first!',
            uploadImagesFirst: 'Navigate to the "Images" to upload and arrange catalog images first.',
            messangerDisabledWhenEmpty: 'Messenger is disabled for empty shopping carts!',
            feedbackReviewed: 'Feedback reviewed.',
            feedbackReported: 'Feedback reported.',
            feedbackLeft: 'Feedback left.',
            accessDenied: 'Action denied! Your account is not authorized to perform this action.',
            noBuyer: 'No buyer address. You did not provide any buyer information.',
            sellerProfileNotFound: 'Navigate to the "Seller / Settings" to configure seller profile first.',
            productDuplicated: 'Product duplicated.',
            catalogDuplicated: 'Catalog duplicated.',
            errorWithTraceback: 'Server errored with traceback.',
            actionFailedCheckForm: 'Action failed! Inspect the form for errors.',
            orderPaymentSuccessProgress: 'Order processing is in pogress.',
            orderPaymentSuccessProgresscanceled: 'Order payment is canceled.',
            orderPaymentSuccessProgresscompleted: 'Order payment is completed.',
            sellerProhibtsAddress: 'The seller prohibits one of the addresses that you have supplied.'
        });

        $.extend(GLOBAL_CONFIG.toolbar.titles, {
            seller: 'Seller',
            edit31: 'Catalog',
            add31: 'Catalog',
            viewImages: 'Images',
            viewProducts: 'Products',
            editProduct: 'Edit Product',
            addProduct: 'Add Product',
            editPluginGroup: false,
            settings: 'Settings',
            addPlugins: 'Add Rule',
            editPlugins: 'Edit Rule',
            addVariants: 'Add Variant',
            editVariants: 'Edit Variant',
            home: 'Home',
            about: 'About',
            acceptable_use_policy: 'Acceptable Use Policy',
            tos: 'Terms of Service',
            copyright_policy: 'Copyright & Trademark',
            privacy_policy: 'Privacy Policy',
            buyer: 'Buyer',
            carts: 'Carts',
            orders: 'Orders',
            catalogs: 'Catalogs',
            addLines: 'Add Line',
            edit18: 'Following',
            viewAddresses: 'Addresses',
            addAddresses: 'Add Address',
            editAddresses: 'Edit Address',
            addLocations: 'Add Location',
            editLocations: 'Edit Location',
            editLines: 'Edit Line',
            addPrice: 'Add Price',
            addPrices: 'Add Price',
            editPrice: 'Edit Price',
            viewInstances: 'Variant Configurations',
            editInstances: 'Edit Variant Configuration',
            addInstances: 'Add Variant Configuration',
            addContents: 'Add Content',
            editContents: 'Edit Content',
            account: 'Account',
            admin: 'Admin',
            users: 'Accounts',
            aboutRules: 'About Rules',
            addDocuments: 'Add Content',
            editDocuments: 'Edit Content',
            editContent: false,
            sellerProfile: 'Seller Profile'
        });

        if (!GLOBAL_CONFIG.backendErrorHandling) {
            GLOBAL_CONFIG.backendErrorHandling = {};
        }
        $.extend(GLOBAL_CONFIG.backendErrorHandling, {
            sellerProfileNotFound: function (errors) {
                if (errors.not_found && $.inArray('seller', errors.not_found) !== -1) {
                    return GLOBAL_CONFIG.snackbar.messages.sellerProfileNotFound;
                }
                return false;
            },
            action_denied: function (reason) {
                return 'You do not have permission to perform this action.';
            },
            not_found: function (fields) {
                return 'Requested data ' + fields.join(', ') + ' could not be found in database.';
            },
            invalid_image_type: 'You have supplied incorrect type of image format.',
            invalid_model: 'You have requested access to resource that does not exist,',
            invalid_action: 'You have requested access to the action that does not exist.',
            required: function (fields) {
                return 'Some values are missing: ' + fields.join(', ') + '.';
            },
            traceback: function (trace) {
                var parse = $.parseHTML(trace);
                return $(parse).filter('pre').text();
            },
            transaction: function (reason) {
                if (reason === 'timeout') {
                    return 'Transaction was not completed due timeout. Please try again.';
                }
                if (reason === 'failed') {
                    return 'Transaction was not completed due failure. Please try again.';
                }
                return reason;
            }
        });

    }));
}());
(function () {
    'use strict';

    angular.module('material.components.button', [
            'material.core'
        ])
        .directive('mdButton', MdButtonDirective);

    function MdButtonDirective($mdInkRipple, $mdAria) {

        return {
            restrict: 'E',
            replace: true,
            transclude: true,
            template: getTemplate,
            link: postLink
        };

        function isAnchor(attr) {
            return angular.isDefined(attr.href) || angular.isDefined(attr.ngHref);
        }

        function getTemplate(element, attr) {
            return isAnchor(attr) ?
                '<a class="md-button" ng-transclude></a>' :
                '<button class="md-button" ng-transclude></button>';
        }

        function postLink(scope, element, attr) {
            var node = element[0];
            $mdInkRipple.attachButtonBehavior(scope, element);

            var elementHasText = node.textContent.trim();
            if (!elementHasText) {
                $mdAria.expect(element, 'aria-label');
            }

            // For anchor elements, we have to set tabindex manually when the 
            // element is disabled
            if (isAnchor(attr) && angular.isDefined(attr.ngDisabled)) {
                scope.$watch(attr.ngDisabled, function (isDisabled) {
                    element.attr('tabindex', isDisabled ? -1 : 0);
                });
            }
        }

    }
    MdButtonDirective.$inject = ["$mdInkRipple", "$mdAria"];
})();
(function () {
    'use strict';

    angular.module('material.components.checkbox', [
            'material.core'
        ])
        .directive('mdCheckbox', MdCheckboxDirective);

    function MdCheckboxDirective(inputDirective, $mdAria, $mdConstant, $mdUtil) {
        inputDirective = inputDirective[0];
        var CHECKED_CSS = 'md-checked';

        return {
            restrict: 'E',
            transclude: true,
            require: '?ngModel',
            template: '<div class="md-container list-primary-tile">' +
                '<div class="avatar-small"><div><icon class="button-square" type="check_box"></icon>' +
                '<icon class="button-square" type="check_box_outline_blank"></icon></div>' +
                '</div></div>' +
                '<div ng-transclude class="md-label"></div>',
            compile: compile
        };

        // **********************************************************
        // Private Methods
        // **********************************************************

        function compile(tElement, tAttrs) {

            tAttrs.type = 'checkbox';
            tAttrs.tabIndex = 0;
            tElement.attr('role', tAttrs.type);

            return function postLink(scope, element, attr, ngModelCtrl) {
                ngModelCtrl = ngModelCtrl || $mdUtil.fakeNgModel();
                var checked = false;
                $mdAria.expectWithText(element, 'aria-label');

                // Reuse the original input[type=checkbox] directive from Angular core.
                // This is a bit hacky as we need our own event listener and own render
                // function.
                inputDirective.link.pre(scope, {
                    on: angular.noop,
                    0: {}
                }, attr, [ngModelCtrl]);

                element.on('click', listener)
                    .on('keypress', keypressHandler);
                ngModelCtrl.$render = render;

                function keypressHandler(ev) {
                    if (ev.which === $mdConstant.KEY_CODE.SPACE) {
                        ev.preventDefault();
                        listener(ev);
                    }
                }

                function listener(ev) {
                    if (element[0].hasAttribute('disabled')) return;

                    scope.$apply(function () {
                        checked = !checked;
                        ngModelCtrl.$setViewValue(checked, ev && ev.type);
                        ngModelCtrl.$render();
                    });
                }

                function render() {
                    checked = ngModelCtrl.$viewValue;
                    if (checked) {
                        element.addClass(CHECKED_CSS);
                    } else {
                        element.removeClass(CHECKED_CSS);
                    }
                }
            };
        }
    }
    MdCheckboxDirective.$inject = ["inputDirective", "$mdAria", "$mdConstant", "$mdUtil"];

})();
(function () {
    'use strict';

    angular.module('material.components.content', [
            'material.core'
        ])
        .directive('mdContent', mdContentDirective).config(['markdownConverterProvider', function (markdownConverterProvider) {
            markdownConverterProvider.config({
                extensions: ['demo']
            });
        }]);


    function mdContentDirective() {
        return {
            restrict: 'E',
            controller: ['$scope', '$element', ContentController],
            link: function (scope, element, attr) {
                var node = element[0];
                scope.$broadcast('$mdContentLoaded', element);

                iosScrollFix(element[0]);
            }
        };

        function ContentController($scope, $element) {
            this.$scope = $scope;
            this.$element = $element;
        }
    }
    mdContentDirective.$inject = [];

    function iosScrollFix(node) {
        // IOS FIX:
        // If we scroll where there is no more room for the webview to scroll,
        // by default the webview itself will scroll up and down, this looks really
        // bad.  So if we are scrolling to the very top or bottom, add/subtract one
        angular.element(node).on('$md.pressdown', function (ev) {
            // Only touch events
            if (ev.pointer.type !== 't') return;
            // Don't let a child content's touchstart ruin it for us.
            if (ev.$materialScrollFixed) return;
            ev.$materialScrollFixed = true;

            if (node.scrollTop === 0) {
                node.scrollTop = 1;
            } else if (node.scrollHeight === node.scrollTop + node.offsetHeight) {
                node.scrollTop -= 1;
            }
        });
    }
})();


(function () {
    var demo = function (converter) {
        return [{
            type: 'output',
            filter: function (text) {
                if (window._allow) {
                    return text;
                }
                try {
                    $.parseHTML(text); // any invalid html will be shown as blank
                }catch (e){
                    return '';
                }
                var dom = $('<div />').html(text),
                    whiteListIframe = function (a) {
                        // regex for whitelisted providers... @todo
                        return a;
                    },
                    whiteListA = {
                        '_blank': true
                    },
                    intOrPercentage = function (a) {
                        var percentage = a.indexOf('%') !== -1,
                            px = a.indexOf('px') !== -1,
                            suffix = '';
                        if (percentage) {
                            suffix = '%';
                        }
                        if (px) {
                            suffix = 'px';
                        }
                        return parseInt(a, 10) + suffix;
                    },
                    allowedTags = {
                        strong: true,
                        b: true,
                        hr: true,
                        ol: true,
                        blockquote: true,
                        kbd: true,
                        code: true,
                        i: true,
                        em: true,
                        h1: true,
                        h2: true,
                        h3: true,
                        h4: true,
                        /*a: {
                            href: function (a) {
                                var regex = /^http/,
                                    regex2 = '/^#/';
                                if (a.match(regex) || a.match(regex2)) {
                                    return a;
                                }
                                return '';
                            },
                            target: function (a) {
                                if (whiteListA[a]) {
                                    return a;
                                }
                                return '';
                            },
                        },*/
                        h5: true,
                        h6: true,
                        ul: true,
                        li: true,
                        div: true,
                        pre: true,
                        p: true,
                        br: true,
                        iframe: {
                            width: intOrPercentage,
                            height: intOrPercentage,
                            src: whiteListIframe,
                            allowfullscreen: function () {
                                return '';
                            },
                            frameborder: function (a) {
                                return parseInt(a, 10);
                            }
                        }
                    };
                dom.find('*').each(function () {
                    var item = $(this),
                        name = item.get(0).nodeName.toLowerCase(),
                        allowed = allowedTags[name];
                    if (allowed) {
                        $.each(this.attributes, function () {
                            var propertySpec = angular.isObject(allowed) ? allowed[this.name] : false;
                            if (!propertySpec) {
                                item.removeAttr(this.name);
                            } else {
                                item.attr(this.name, propertySpec(item.attr(this.name)));
                            }
                        });
                    } else {
                        item.remove();
                    }
                });

                return dom.html();
            }
        }];
    };

    // Client-side export
    if (typeof window !== 'undefined' && window.Showdown && window.Showdown.extensions) {
        window.Showdown.extensions.demo = demo;
    }
    // Server-side export
    if (typeof module !== 'undefined') module.exports = demo;
}());
(function () {
    'use strict';

    (function () {
        'use strict';


        angular.module('material.core', [])
            .config(MdCoreConfigure);

        function MdCoreConfigure($provide) {
            $provide.decorator('$$rAF', ["$delegate", rAFDecorator]);
        }
        MdCoreConfigure.$inject = ["$provide"];

        function rAFDecorator($delegate) {
            /**
             * Use this to throttle events that come in often.
             * The throttled function will always use the *last* invocation before the
             * coming frame.
             *
             * For example, window resize events that fire many times a second:
             * If we set to use an raf-throttled callback on window resize, then
             * our callback will only be fired once per frame, with the last resize
             * event that happened before that frame.
             *
             * @param {function} callback function to debounce
             */
            $delegate.throttle = function (cb) {
                var queueArgs, alreadyQueued, queueCb, context;
                return function debounced() {
                    queueArgs = arguments;
                    context = this;
                    queueCb = cb;
                    if (!alreadyQueued) {
                        alreadyQueued = true;
                        $delegate(function () {
                            queueCb.apply(context, queueArgs);
                            alreadyQueued = false;
                        });
                    }
                };
            };
            return $delegate;
        }

        angular.module('material.core')
            .factory('$mdConstant', MdConstantFactory);

        function MdConstantFactory($$rAF, $sniffer) {

            var webkit = /webkit/i.test($sniffer.vendorPrefix);

            function vendorProperty(name) {
                return webkit ? ('webkit' + name.charAt(0).toUpperCase() + name.substring(1)) : name;
            }

            function cssVendorProperty(name) {
                return webkit ? '-webkit-' + name : name;
            }

            return {
                KEY_CODE: {
                    ENTER: 13,
                    ESCAPE: 27,
                    SPACE: 32,
                    LEFT_ARROW: 37,
                    UP_ARROW: 38,
                    RIGHT_ARROW: 39,
                    DOWN_ARROW: 40
                },
                RAW_CSS: {
                    TRANSFORM: cssVendorProperty('transform'),
                    TRANSFORMORIGIN: cssVendorProperty('transformOrigin'),
                    TRANSITION: cssVendorProperty('transition'),
                    TRANSITION_DURATION: cssVendorProperty('transitionDuration'),
                    ANIMATION_PLAY_STATE: cssVendorProperty('animationPlayState'),
                    ANIMATION_DURATION: cssVendorProperty('animationDuration'),
                    ANIMATION_NAME: cssVendorProperty('animationName'),
                    ANIMATION_TIMING: cssVendorProperty('animationTimingFunction'),
                    ANIMATION_DIRECTION: cssVendorProperty('animationDirection')
                },
                CSS: {
                    /* Constants */
                    TRANSITIONEND: 'transitionend' + (webkit ? ' webkitTransitionEnd' : ''),
                    ANIMATIONEND: 'animationend' + (webkit ? ' webkitAnimationEnd' : ''),

                    TRANSFORM: vendorProperty('transform'),
                    TRANSFORMORIGIN: vendorProperty('transformOrigin'),
                    TRANSITION: vendorProperty('transition'),
                    TRANSITION_DURATION: vendorProperty('transitionDuration'),
                    ANIMATION_PLAY_STATE: vendorProperty('animationPlayState'),
                    ANIMATION_DURATION: vendorProperty('animationDuration'),
                    ANIMATION_NAME: vendorProperty('animationName'),
                    ANIMATION_TIMING: vendorProperty('animationTimingFunction'),
                    ANIMATION_DIRECTION: vendorProperty('animationDirection')
                },
                MEDIA: {
                    'sm': '(max-width: 600px)',
                    'gt-sm': '(min-width: 600px)',
                    'md': '(min-width: 600px) and (max-width: 960px)',
                    'gt-md': '(min-width: 960px)',
                    'lg': '(min-width: 960px) and (max-width: 1200px)',
                    'gt-lg': '(min-width: 1200px)'
                }
            };
        }
        MdConstantFactory.$inject = ["$$rAF", "$sniffer"];

    })();
    (function () {

        angular
            .module('material.core')
            .config(["$provide", function ($provide) {
                $provide.decorator('$mdUtil', ['$delegate', function ($delegate) {
                    /**
                     * Inject the iterator facade to easily support iteration and accessors
                     * @see iterator below
                     */
                    $delegate.iterator = Iterator;

                    return $delegate;
                }]);
            }]);

        /**
         * iterator is a list facade to easily support iteration and accessors
         *
         * @param items Array list which this iterator will enumerate
         * @param reloop Boolean enables iterator to consider the list as an endless reloop
         */
        function Iterator(items, reloop) {
            var trueFn = function () {
                return true;
            };

            reloop = !!reloop;
            var _items = items || [];

            // Published API
            return {
                items: getItems,
                count: count,

                inRange: inRange,
                contains: contains,
                indexOf: indexOf,
                itemAt: itemAt,

                findBy: findBy,

                add: add,
                remove: remove,

                first: first,
                last: last,
                next: angular.bind(null, findSubsequentItem, false),
                previous: angular.bind(null, findSubsequentItem, true),

                hasPrevious: hasPrevious,
                hasNext: hasNext

            };

            /**
             * Publish copy of the enumerable set
             * @returns {Array|*}
             */
            function getItems() {
                return [].concat(_items);
            }

            /**
             * Determine length of the list
             * @returns {Array.length|*|number}
             */
            function count() {
                return _items.length;
            }

            /**
             * Is the index specified valid
             * @param index
             * @returns {Array.length|*|number|boolean}
             */
            function inRange(index) {
                return _items.length && (index > -1) && (index < _items.length);
            }

            /**
             * Can the iterator proceed to the next item in the list; relative to
             * the specified item.
             *
             * @param item
             * @returns {Array.length|*|number|boolean}
             */
            function hasNext(item) {
                return item ? inRange(indexOf(item) + 1) : false;
            }

            /**
             * Can the iterator proceed to the previous item in the list; relative to
             * the specified item.
             *
             * @param item
             * @returns {Array.length|*|number|boolean}
             */
            function hasPrevious(item) {
                return item ? inRange(indexOf(item) - 1) : false;
            }

            /**
             * Get item at specified index/position
             * @param index
             * @returns {*}
             */
            function itemAt(index) {
                return inRange(index) ? _items[index] : null;
            }

            /**
             * Find all elements matching the key/value pair
             * otherwise return null
             *
             * @param val
             * @param key
             *
             * @return array
             */
            function findBy(key, val) {
                return _items.filter(function (item) {
                    return item[key] === val;
                });
            }

            /**
             * Add item to list
             * @param item
             * @param index
             * @returns {*}
             */
            function add(item, index) {
                if (!item) return -1;

                if (!angular.isNumber(index)) {
                    index = _items.length;
                }

                _items.splice(index, 0, item);

                return indexOf(item);
            }

            /**
             * Remove item from list...
             * @param item
             */
            function remove(item) {
                if (contains(item)) {
                    _items.splice(indexOf(item), 1);
                }
            }

            /**
             * Get the zero-based index of the target item
             * @param item
             * @returns {*}
             */
            function indexOf(item) {
                return _items.indexOf(item);
            }

            /**
             * Boolean existence check
             * @param item
             * @returns {boolean}
             */
            function contains(item) {
                return item && (indexOf(item) > -1);
            }

            /**
             * Return first item in the list
             * @returns {*}
             */
            function first() {
                return _items.length ? _items[0] : null;
            }

            /**
             * Return last item in the list...
             * @returns {*}
             */
            function last() {
                return _items.length ? _items[_items.length - 1] : null;
            }

            /**
             * Find the next item. If reloop is true and at the end of the list, it will
             * go back to the first item. If given ,the `validate` callback will be used
             * determine whether the next item is valid. If not valid, it will try to find the
             * next item again.
             * @param item
             * @param {optional} validate Validate function
             * @param {optional} limit Recursion limit
             * @returns {*}
             */
            function findSubsequentItem(backwards, item, validate, limit) {
                validate = validate || trueFn;

                var curIndex = indexOf(item);
                if (!inRange(curIndex)) {
                    return null;
                }

                var nextIndex = curIndex + (backwards ? -1 : 1);
                var foundItem = null;
                if (inRange(nextIndex)) {
                    foundItem = _items[nextIndex];
                } else if (reloop) {
                    foundItem = backwards ? last() : first();
                    nextIndex = indexOf(foundItem);
                }

                if ((foundItem === null) || (nextIndex === limit)) {
                    return null;
                }

                if (angular.isUndefined(limit)) {
                    limit = nextIndex;
                }

                return validate(foundItem) ? foundItem : findSubsequentItem(backwards, foundItem, validate, limit);
            }
        }

    })();

    angular.module('material.core')
        .factory('$mdMedia', mdMediaFactory);

    /**
     * Exposes a function on the '$mdMedia' service which will return true or false,
     * whether the given media query matches. Re-evaluates on resize. Allows presets
     * for 'sm', 'md', 'lg'.
     *
     * @example $mdMedia('sm') == true if device-width <= sm
     * @example $mdMedia('(min-width: 1200px)') == true if device-width >= 1200px
     * @example $mdMedia('max-width: 300px') == true if device-width <= 300px (sanitizes input, adding parens)
     */
    function mdMediaFactory($mdConstant, $rootScope, $window) {
        var queries = {};
        var results = {};

        return $mdMedia;

        function $mdMedia(query) {
            var validated = queries[query];
            if (angular.isUndefined(validated)) {
                validated = queries[query] = validate(query);
            }

            var result = results[validated];
            if (angular.isUndefined(result)) {
                result = add(validated);
            }

            return result;
        }

        function validate(query) {
            return $mdConstant.MEDIA[query] ||
                ((query.charAt(0) !== '(') ? ('(' + query + ')') : query);
        }

        function add(query) {
            var result = $window.matchMedia(query);
            result.addListener(onQueryChange);
            return (results[result.media] = !!result.matches);
        }

        function onQueryChange() {
            var query = this;
            $rootScope.$evalAsync(function () {
                results[query.media] = !!query.matches;
            });
        }

    }
    mdMediaFactory.$inject = ["$mdConstant", "$rootScope", "$window"];

    (function () {
        'use strict';

        /*
         * This var has to be outside the angular factory, otherwise when
         * there are multiple material apps on the same page, each app
         * will create its own instance of this array and the app's IDs
         * will not be unique.
         */
        var nextUniqueId = ['0', '0', '0'];

        angular.module('material.core')
            .factory('$mdUtil', ["$document", "$timeout", function ($document, $timeout) {
                var Util;

                return Util = {
                    now: window.performance ? angular.bind(window.performance, window.performance.now) : Date.now,

                    elementRect: function (element, offsetParent) {
                        var node = element[0];
                        offsetParent = offsetParent || node.offsetParent || document.body;
                        offsetParent = offsetParent[0] || offsetParent;
                        var nodeRect = node.getBoundingClientRect();
                        var parentRect = offsetParent.getBoundingClientRect();
                        return {
                            left: nodeRect.left - parentRect.left + offsetParent.scrollLeft,
                            top: nodeRect.top - parentRect.top + offsetParent.scrollTop,
                            width: nodeRect.width,
                            height: nodeRect.height
                        };
                    },

                    fakeNgModel: function () {
                        return {
                            $fake: true,
                            $setViewValue: function (value) {
                                this.$viewValue = value;
                                this.$render(value);
                                this.$viewChangeListeners.forEach(function (cb) {
                                    cb();
                                });
                            },
                            $isEmpty: function (value) {
                                return ('' + value).length === 0;
                            },
                            $parsers: [],
                            $formatters: [],
                            $viewChangeListeners: [],
                            $render: angular.noop
                        };
                    },

                    // Returns a function, that, as long as it continues to be invoked, will not
                    // be triggered. The function will be called after it stops being called for
                    // N milliseconds.
                    // @param wait Integer value of msecs to delay (since last debounce reset); default value 10 msecs
                    // @param invokeApply should the $timeout trigger $digest() dirty checking
                    debounce: function (func, wait, scope, invokeApply) {
                        var timer;

                        return function debounced() {
                            var context = scope,
                                args = Array.prototype.slice.call(arguments);

                            $timeout.cancel(timer);
                            timer = $timeout(function () {

                                timer = undefined;
                                func.apply(context, args);

                            }, wait || 10, invokeApply);
                        };
                    },

                    // Returns a function that can only be triggered every `delay` milliseconds.
                    // In other words, the function will not be called unless it has been more
                    // than `delay` milliseconds since the last call.
                    throttle: function throttle(func, delay) {
                        var recent;
                        return function throttled() {
                            var context = this;
                            var args = arguments;
                            var now = Util.now();

                            if (!recent || (now - recent > delay)) {
                                func.apply(context, args);
                                recent = now;
                            }
                        };
                    },

                    /**
                     * nextUid, from angular.js.
                     * A consistent way of creating unique IDs in angular. The ID is a sequence of alpha numeric
                     * characters such as '012ABC'. The reason why we are not using simply a number counter is that
                     * the number string gets longer over time, and it can also overflow, where as the nextId
                     * will grow much slower, it is a string, and it will never overflow.
                     *
                     * @returns an unique alpha-numeric string
                     */
                    nextUid: function () {
                        var index = nextUniqueId.length;
                        var digit;

                        while (index) {
                            index--;
                            digit = nextUniqueId[index].charCodeAt(0);
                            if (digit == 57 /*'9'*/ ) {
                                nextUniqueId[index] = 'A';
                                return nextUniqueId.join('');
                            }
                            if (digit == 90 /*'Z'*/ ) {
                                nextUniqueId[index] = '0';
                            } else {
                                nextUniqueId[index] = String.fromCharCode(digit + 1);
                                return nextUniqueId.join('');
                            }
                        }
                        nextUniqueId.unshift('0');
                        return nextUniqueId.join('');
                    },

                    // Stop watchers and events from firing on a scope without destroying it,
                    // by disconnecting it from its parent and its siblings' linked lists.
                    disconnectScope: function disconnectScope(scope) {
                        if (!scope) return;

                        // we can't destroy the root scope or a scope that has been already destroyed
                        if (scope.$root === scope) return;
                        if (scope.$$destroyed) return;

                        var parent = scope.$parent;
                        scope.$$disconnected = true;

                        // See Scope.$destroy
                        if (parent.$$childHead === scope) parent.$$childHead = scope.$$nextSibling;
                        if (parent.$$childTail === scope) parent.$$childTail = scope.$$prevSibling;
                        if (scope.$$prevSibling) scope.$$prevSibling.$$nextSibling = scope.$$nextSibling;
                        if (scope.$$nextSibling) scope.$$nextSibling.$$prevSibling = scope.$$prevSibling;

                        scope.$$nextSibling = scope.$$prevSibling = null;

                    },

                    // Undo the effects of disconnectScope above.
                    reconnectScope: function reconnectScope(scope) {
                        if (!scope) return;

                        // we can't disconnect the root node or scope already disconnected
                        if (scope.$root === scope) return;
                        if (!scope.$$disconnected) return;

                        var child = scope;

                        var parent = child.$parent;
                        child.$$disconnected = false;
                        // See Scope.$new for this logic...
                        child.$$prevSibling = parent.$$childTail;
                        if (parent.$$childHead) {
                            parent.$$childTail.$$nextSibling = child;
                            parent.$$childTail = child;
                        } else {
                            parent.$$childHead = parent.$$childTail = child;
                        }
                    },
                    /*
                     * getClosest replicates jQuery.closest() to walk up the DOM tree until it finds a matching nodeName
                     *
                     * @param el Element to start walking the DOM from
                     * @param tagName Tag name to find closest to el, such as 'form'
                     */
                    getClosest: function getClosest(el, tagName) {
                        tagName = tagName.toUpperCase();
                        do {
                            if (el.nodeName === tagName) {
                                return el;
                            }
                        } while (el = el.parentNode);
                        return null;
                    }
                };

            }]);

        /*
         * Since removing jQuery from the demos, some code that uses `element.focus()` is broken.
         *
         * We need to add `element.focus()`, because it's testable unlike `element[0].focus`.
         *
         * TODO(ajoslin): This should be added in a better place later.
         */

        angular.element.prototype.focus = angular.element.prototype.focus || function () {
            if (this.length) {
                this[0].focus();
            }
            return this;
        };
        angular.element.prototype.blur = angular.element.prototype.blur || function () {
            if (this.length) {
                this[0].blur();
            }
            return this;
        };

    })();

    (function () {
        'use strict';

        angular.module('material.core')
            .service('$mdAria', AriaService);

        function AriaService($$rAF, $log, $window) {

            return {
                expect: expect,
                expectAsync: expectAsync,
                expectWithText: expectWithText
            };

            /**
             * Check if expected attribute has been specified on the target element or child
             * @param element
             * @param attrName
             * @param {optional} defaultValue What to set the attr to if no value is found
             */
            function expect(element, attrName, defaultValue) {
                var node = element[0];

                if (!node.hasAttribute(attrName) && !childHasAttribute(node, attrName)) {

                    defaultValue = angular.isString(defaultValue) && defaultValue.trim() || '';
                    if (defaultValue.length) {
                        element.attr(attrName, defaultValue);
                    } else {
                        //$log.warn('ARIA: Attribute "', attrName, '", required for accessibility, is missing on node:', node);
                    }

                }
            }

            function expectAsync(element, attrName, defaultValueGetter) {
                // Problem: when retrieving the element's contents synchronously to find the label,
                // the text may not be defined yet in the case of a binding.
                // There is a higher chance that a binding will be defined if we wait one frame.
                $$rAF(function () {
                    expect(element, attrName, defaultValueGetter());
                });
            }

            function expectWithText(element, attrName) {
                expectAsync(element, attrName, function () {
                    return element.text().trim();
                });
            }

            function childHasAttribute(node, attrName) {
                var hasChildren = node.hasChildNodes(),
                    hasAttr = false;

                function isHidden(el) {
                    var style = el.currentStyle ? el.currentStyle : $window.getComputedStyle(el);
                    return (style.display === 'none');
                }

                if (hasChildren) {
                    var children = node.childNodes;
                    for (var i = 0; i < children.length; i++) {
                        var child = children[i];
                        if (child.nodeType === 1 && child.hasAttribute(attrName)) {
                            if (!isHidden(child)) {
                                hasAttr = true;
                            }
                        }
                    }
                }
                return hasAttr;
            }
        }
        AriaService.$inject = ["$$rAF", "$log", "$window"];
    })();

    (function () {
        'use strict';

        angular.module('material.core')
            .service('$mdCompiler', mdCompilerService);

        function mdCompilerService($q, $http, $injector, $compile, $controller, $templateCache) {
            /* jshint validthis: true */

            /*
             * @ngdoc service
             * @name $mdCompiler
             * @module material.core
             * @description
             * The $mdCompiler service is an abstraction of angular's compiler, that allows the developer
             * to easily compile an element with a templateUrl, controller, and locals.
             *
             * @usage
             * <hljs lang="js">
             * $mdCompiler.compile({
             *   templateUrl: 'modal.html',
             *   controller: 'ModalController',
             *   locals: {
             *     modal: myModalInstance;
             *   }
             * }).then(function(compileData) {
             *   compileData.element; // modal.html's template in an element
             *   compileData.link(myScope); //attach controller & scope to element
             * });
             * </hljs>
             */

            /*
             * @ngdoc method
             * @name $mdCompiler#compile
             * @description A helper to compile an HTML template/templateUrl with a given controller,
             * locals, and scope.
             * @param {object} options An options object, with the following properties:
             *
             *    - `controller` - `{(string=|function()=}` Controller fn that should be associated with
             *      newly created scope or the name of a registered controller if passed as a string.
             *    - `controllerAs` - `{string=}` A controller alias name. If present the controller will be
             *      published to scope under the `controllerAs` name.
             *    - `template` - `{string=}` An html template as a string.
             *    - `templateUrl` - `{string=}` A path to an html template.
             *    - `transformTemplate` - `{function(template)=}` A function which transforms the template after
             *      it is loaded. It will be given the template string as a parameter, and should
             *      return a a new string representing the transformed template.
             *    - `resolve` - `{Object.<string, function>=}` - An optional map of dependencies which should
             *      be injected into the controller. If any of these dependencies are promises, the compiler
             *      will wait for them all to be resolved, or if one is rejected before the controller is
             *      instantiated `compile()` will fail..
             *      * `key` - `{string}`: a name of a dependency to be injected into the controller.
             *      * `factory` - `{string|function}`: If `string` then it is an alias for a service.
             *        Otherwise if function, then it is injected and the return value is treated as the
             *        dependency. If the result is a promise, it is resolved before its value is 
             *        injected into the controller.
             *
             * @returns {object=} promise A promise, which will be resolved with a `compileData` object.
             * `compileData` has the following properties: 
             *
             *   - `element` - `{element}`: an uncompiled element matching the provided template.
             *   - `link` - `{function(scope)}`: A link function, which, when called, will compile
             *     the element and instantiate the provided controller (if given).
             *   - `locals` - `{object}`: The locals which will be passed into the controller once `link` is
             *     called. If `bindToController` is true, they will be coppied to the ctrl instead
             *   - `bindToController` - `bool`: bind the locals to the controller, instead of passing them in
             */
            this.compile = function (options) {
                var templateUrl = options.templateUrl;
                var template = options.template || '';
                var controller = options.controller;
                var controllerAs = options.controllerAs;
                var resolve = options.resolve || {};
                var locals = options.locals || {};
                var transformTemplate = options.transformTemplate || angular.identity;
                var bindToController = options.bindToController;

                // Take resolve values and invoke them.  
                // Resolves can either be a string (value: 'MyRegisteredAngularConst'),
                // or an invokable 'factory' of sorts: (value: function ValueGetter($dependency) {})
                angular.forEach(resolve, function (value, key) {
                    if (angular.isString(value)) {
                        resolve[key] = $injector.get(value);
                    } else {
                        resolve[key] = $injector.invoke(value);
                    }
                });
                //Add the locals, which are just straight values to inject
                //eg locals: { three: 3 }, will inject three into the controller
                angular.extend(resolve, locals);

                if (templateUrl) {
                    resolve.$template = $http.get(templateUrl, {
                            cache: $templateCache
                        })
                        .then(function (response) {
                            return response.data;
                        });
                } else {
                    resolve.$template = $q.when(template);
                }

                // Wait for all the resolves to finish if they are promises
                return $q.all(resolve).then(function (locals) {

                    var template = transformTemplate(locals.$template);
                    var element = angular.element('<div>').html(template.trim()).contents();
                    var linkFn = $compile(element);

                    //Return a linking function that can be used later when the element is ready
                    return {
                        locals: locals,
                        element: element,
                        link: function link(scope) {
                            locals.$scope = scope;

                            //Instantiate controller if it exists, because we have scope
                            if (controller) {
                                var ctrl = $controller(controller, locals);
                                if (bindToController) {
                                    angular.extend(ctrl, locals);
                                }
                                //See angular-route source for this logic
                                element.data('$ngControllerController', ctrl);
                                element.children().data('$ngControllerController', ctrl);

                                if (controllerAs) {
                                    scope[controllerAs] = ctrl;
                                }
                            }

                            return linkFn(scope);
                        }
                    };
                });

            };
        }
        mdCompilerService.$inject = ["$q", "$http", "$injector", "$compile", "$controller", "$templateCache"];
    })();

    (function (jQuery) {
        'use strict';
        var HANDLERS = {};

        /* The state of the current 'pointer'
         * The pointer represents the state of the current touch.
         * It contains normalized x and y coordinates from DOM events,
         * as well as other information abstracted from the DOM.
         */
         
        var pointer, lastPointer, forceSkipClickHijack = false;

        /**
         * The position of the most recent click if that click was on a label element.
         * @type {{x: number, y: number}?}
         */
        var lastLabelClickPos = null;

        // Used to attach event listeners once when multiple ng-apps are running.
        var isInitialized = false;

        angular
          .module('material.core.gestures', [ ])
          .provider('$mdGesture', MdGestureProvider)
          .factory('$$MdGestureHandler', MdGestureHandler)
          .run( attachToDocument );

        /**
           * @ngdoc service
           * @name $mdGestureProvider
           * @module material.core.gestures
           *
           * @description
           * In some scenarios on Mobile devices (without jQuery), the click events should NOT be hijacked.
           * `$mdGestureProvider` is used to configure the Gesture module to ignore or skip click hijacking on mobile
           * devices.
           *
           * <hljs lang="js">
           *   app.config(function($mdGestureProvider) {
           *
           *     // For mobile devices without jQuery loaded, do not
           *     // intercept click events during the capture phase.
           *     $mdGestureProvider.skipClickHijack();
           *
           *   });
           * </hljs>
           *
           */
        function MdGestureProvider() { }

        MdGestureProvider.prototype = {

          // Publish access to setter to configure a variable  BEFORE the
          // $mdGesture service is instantiated...
          skipClickHijack: function() {
            return forceSkipClickHijack = true;
          },

          /**
           * $get is used to build an instance of $mdGesture
           * ngInject
           */
          $get : ["$$MdGestureHandler", "$$rAF", "$timeout", function($$MdGestureHandler, $$rAF, $timeout) {
               return new MdGesture($$MdGestureHandler, $$rAF, $timeout);
          }]
        };



        /**
         * MdGesture factory construction function
         * ngInject
         */
        function MdGesture($$MdGestureHandler, $$rAF, $timeout) {
          var userAgent = navigator.userAgent || navigator.vendor || window.opera;
          var isIos = userAgent.match(/ipad|iphone|ipod/i);
          var isAndroid = userAgent.match(/android/i);
          var hasJQuery =  (typeof window.jQuery !== 'undefined') && (angular.element === window.jQuery);

          var self = {
            handler: addHandler,
            register: register,
            // On mobile w/out jQuery, we normally intercept clicks. Should we skip that?
            isHijackingClicks: (isIos || isAndroid) && !hasJQuery && !forceSkipClickHijack
          };

          if (self.isHijackingClicks) {
            var maxClickDistance = 6;
            self.handler('click', {
              options: {
                maxDistance: maxClickDistance
              },
              onEnd: checkDistanceAndEmit('click')
            });

            self.handler('focus', {
              options: {
                maxDistance: maxClickDistance
              },
              onEnd: function(ev, pointer) {
                if (pointer.distance < this.state.options.maxDistance) {
                  if (canFocus(ev.target)) {
                    this.dispatchEvent(ev, 'focus', pointer);
                    ev.target.focus();
                  }
                }

                function canFocus(element) {
                  var focusableElements = ['INPUT', 'SELECT', 'BUTTON', 'TEXTAREA', 'VIDEO', 'AUDIO'];

                  return (element.getAttribute('tabindex') != '-1') &&
                      !element.hasAttribute('DISABLED') &&
                      (element.hasAttribute('tabindex') || element.hasAttribute('href') ||
                      (focusableElements.indexOf(element.nodeName) != -1));
                }
              }
            });

            self.handler('mouseup', {
              options: {
                maxDistance: maxClickDistance
              },
              onEnd: checkDistanceAndEmit('mouseup')
            });

            self.handler('mousedown', {
              onStart: function(ev) {
                this.dispatchEvent(ev, 'mousedown');
              }
            });
          }

          function checkDistanceAndEmit(eventName) {
            return function(ev, pointer) {
              if (pointer.distance < this.state.options.maxDistance) {
                this.dispatchEvent(ev, eventName, pointer);
              }
            };
          }

          /*
           * Register an element to listen for a handler.
           * This allows an element to override the default options for a handler.
           * Additionally, some handlers like drag and hold only dispatch events if
           * the domEvent happens inside an element that's registered to listen for these events.
           *
           * @see GestureHandler for how overriding of default options works.
           * @example $mdGesture.register(myElement, 'drag', { minDistance: 20, horziontal: false })
           */
          function register(element, handlerName, options) {
            var handler = HANDLERS[handlerName.replace(/^\$md./, '')];
            if (!handler) {
              throw new Error('Failed to register element with handler ' + handlerName + '. ' +
              'Available handlers: ' + Object.keys(HANDLERS).join(', '));
            }
            return handler.registerElement(element, options);
          }

          /*
           * add a handler to $mdGesture. see below.
           */
          function addHandler(name, definition) {
            var handler = new $$MdGestureHandler(name);
            angular.extend(handler, definition);
            HANDLERS[name] = handler;

            return self;
          }

          /*
           * Register handlers. These listen to touch/start/move events, interpret them,
           * and dispatch gesture events depending on options & conditions. These are all
           * instances of GestureHandler.
           * @see GestureHandler 
           */
          return self
            /*
             * The press handler dispatches an event on touchdown/touchend.
             * It's a simple abstraction of touch/mouse/pointer start and end.
             */
            .handler('press', {
              onStart: function (ev, pointer) {
                this.dispatchEvent(ev, '$md.pressdown');
              },
              onEnd: function (ev, pointer) {
                this.dispatchEvent(ev, '$md.pressup');
              }
            })

            /*
             * The hold handler dispatches an event if the user keeps their finger within
             * the same <maxDistance> area for <delay> ms.
             * The hold handler will only run if a parent of the touch target is registered
             * to listen for hold events through $mdGesture.register()
             */
            .handler('hold', {
              options: {
                maxDistance: 6,
                delay: 500
              },
              onCancel: function () {
                $timeout.cancel(this.state.timeout);
              },
              onStart: function (ev, pointer) {
                // For hold, require a parent to be registered with $mdGesture.register()
                // Because we prevent scroll events, this is necessary.
                if (!this.state.registeredParent) return this.cancel();

                this.state.pos = {x: pointer.x, y: pointer.y};
                this.state.timeout = $timeout(angular.bind(this, function holdDelayFn() {
                  this.dispatchEvent(ev, '$md.hold');
                  this.cancel(); //we're done!
                }), this.state.options.delay, false);
              },
              onMove: function (ev, pointer) {
                // Don't scroll while waiting for hold.
                // If we don't preventDefault touchmove events here, Android will assume we don't
                // want to listen to anymore touch events. It will start scrolling and stop sending
                // touchmove events.
                ev.preventDefault();

                // If the user moves greater than <maxDistance> pixels, stop the hold timer
                // set in onStart
                var dx = this.state.pos.x - pointer.x;
                var dy = this.state.pos.y - pointer.y;
                if (Math.sqrt(dx * dx + dy * dy) > this.options.maxDistance) {
                  this.cancel();
                }
              },
              onEnd: function () {
                this.onCancel();
              }
            })

            /*
             * The drag handler dispatches a drag event if the user holds and moves his finger greater than
             * <minDistance> px in the x or y direction, depending on options.horizontal.
             * The drag will be cancelled if the user moves his finger greater than <minDistance>*<cancelMultiplier> in
             * the perpindicular direction. Eg if the drag is horizontal and the user moves his finger <minDistance>*<cancelMultiplier>
             * pixels vertically, this handler won't consider the move part of a drag.
             */
            .handler('drag', {
              options: {
                minDistance: 6,
                horizontal: true,
                cancelMultiplier: 1.5
              },
              onStart: function (ev) {
                // For drag, require a parent to be registered with $mdGesture.register()
                if (!this.state.registeredParent) this.cancel();
              },
              onMove: function (ev, pointer) {
                var shouldStartDrag, shouldCancel;
                // Don't scroll while deciding if this touchmove qualifies as a drag event.
                // If we don't preventDefault touchmove events here, Android will assume we don't
                // want to listen to anymore touch events. It will start scrolling and stop sending
                // touchmove events.
                ev.preventDefault();

                if (!this.state.dragPointer) {
                  if (this.state.options.horizontal) {
                    shouldStartDrag = Math.abs(pointer.distanceX) > this.state.options.minDistance;
                    shouldCancel = Math.abs(pointer.distanceY) > this.state.options.minDistance * this.state.options.cancelMultiplier;
                  } else {
                    shouldStartDrag = Math.abs(pointer.distanceY) > this.state.options.minDistance;
                    shouldCancel = Math.abs(pointer.distanceX) > this.state.options.minDistance * this.state.options.cancelMultiplier;
                  }

                  if (shouldStartDrag) {
                    // Create a new pointer representing this drag, starting at this point where the drag started.
                    this.state.dragPointer = makeStartPointer(ev);
                    updatePointerState(ev, this.state.dragPointer);
                    this.dispatchEvent(ev, '$md.dragstart', this.state.dragPointer);

                  } else if (shouldCancel) {
                    this.cancel();
                  }
                } else {
                  this.dispatchDragMove(ev);
                }
              },
              // Only dispatch dragmove events every frame; any more is unnecessray
              dispatchDragMove: $$rAF.throttle(function (ev) {
                // Make sure the drag didn't stop while waiting for the next frame
                if (this.state.isRunning) {
                  updatePointerState(ev, this.state.dragPointer);
                  this.dispatchEvent(ev, '$md.drag', this.state.dragPointer);
                }
              }),
              onEnd: function (ev, pointer) {
                if (this.state.dragPointer) {
                  updatePointerState(ev, this.state.dragPointer);
                  this.dispatchEvent(ev, '$md.dragend', this.state.dragPointer);
                }
              }
            })

            /*
             * The swipe handler will dispatch a swipe event if, on the end of a touch,
             * the velocity and distance were high enough.
             * TODO: add vertical swiping with a `horizontal` option similar to the drag handler.
             */
            .handler('swipe', {
              options: {
                minVelocity: 0.65,
                minDistance: 10
              },
              onEnd: function (ev, pointer) {
                if (Math.abs(pointer.velocityX) > this.state.options.minVelocity &&
                  Math.abs(pointer.distanceX) > this.state.options.minDistance) {
                  var eventType = pointer.directionX == 'left' ? '$md.swipeleft' : '$md.swiperight';
                  this.dispatchEvent(ev, eventType);
                }
              }
            });

        }
        MdGesture.$inject = ["$$MdGestureHandler", "$$rAF", "$timeout"];

        /**
         * MdGestureHandler
         * A GestureHandler is an object which is able to dispatch custom dom events
         * based on native dom {touch,pointer,mouse}{start,move,end} events.
         *
         * A gesture will manage its lifecycle through the start,move,end, and cancel
         * functions, which are called by native dom events.
         *
         * A gesture has the concept of 'options' (eg a swipe's required velocity), which can be
         * overridden by elements registering through $mdGesture.register()
         */
        function GestureHandler (name) {
          this.name = name;
          this.state = {};
        }

        function MdGestureHandler() {
          var hasJQuery =  (typeof window.jQuery !== 'undefined') && (angular.element === window.jQuery);

          GestureHandler.prototype = {
            options: {},
            // jQuery listeners don't work with custom DOMEvents, so we have to dispatch events
            // differently when jQuery is loaded
            dispatchEvent: hasJQuery ?  jQueryDispatchEvent : nativeDispatchEvent,

            // These are overridden by the registered handler
            onStart: angular.noop,
            onMove: angular.noop,
            onEnd: angular.noop,
            onCancel: angular.noop,

            // onStart sets up a new state for the handler, which includes options from the
            // nearest registered parent element of ev.target.
            start: function (ev, pointer) {
              if (this.state.isRunning) return;
              var parentTarget = this.getNearestParent(ev.target);
              // Get the options from the nearest registered parent
              var parentTargetOptions = parentTarget && parentTarget.$mdGesture[this.name] || {};

              this.state = {
                isRunning: true,
                // Override the default options with the nearest registered parent's options
                options: angular.extend({}, this.options, parentTargetOptions),
                // Pass in the registered parent node to the state so the onStart listener can use
                registeredParent: parentTarget
              };
              this.onStart(ev, pointer);
            },
            move: function (ev, pointer) {
              if (!this.state.isRunning) return;
              this.onMove(ev, pointer);
            },
            end: function (ev, pointer) {
              if (!this.state.isRunning) return;
              this.onEnd(ev, pointer);
              this.state.isRunning = false;
            },
            cancel: function (ev, pointer) {
              this.onCancel(ev, pointer);
              this.state = {};
            },

            // Find and return the nearest parent element that has been registered to
            // listen for this handler via $mdGesture.register(element, 'handlerName').
            getNearestParent: function (node) {
              var current = node;
              while (current) {
                if ((current.$mdGesture || {})[this.name]) {
                  return current;
                }
                current = current.parentNode;
              }
              return null;
            },

            // Called from $mdGesture.register when an element reigsters itself with a handler.
            // Store the options the user gave on the DOMElement itself. These options will
            // be retrieved with getNearestParent when the handler starts.
            registerElement: function (element, options) {
              var self = this;
              element[0].$mdGesture = element[0].$mdGesture || {};
              element[0].$mdGesture[this.name] = options || {};
              element.on('$destroy', onDestroy);

              return onDestroy;

              function onDestroy() {
                delete element[0].$mdGesture[self.name];
                element.off('$destroy', onDestroy);
              }
            }
          };

          return GestureHandler;

          /*
           * Dispatch an event with jQuery
           * TODO: Make sure this sends bubbling events
           *
           * @param srcEvent the original DOM touch event that started this.
           * @param eventType the name of the custom event to send (eg 'click' or '$md.drag')
           * @param eventPointer the pointer object that matches this event.
           */
          function jQueryDispatchEvent(srcEvent, eventType, eventPointer) {
            eventPointer = eventPointer || pointer;
            var eventObj = new angular.element.Event(eventType);

            eventObj.$material = true;
            eventObj.pointer = eventPointer;
            eventObj.srcEvent = srcEvent;

            angular.extend(eventObj, {
              clientX: eventPointer.x,
              clientY: eventPointer.y,
              screenX: eventPointer.x,
              screenY: eventPointer.y,
              pageX: eventPointer.x,
              pageY: eventPointer.y,
              ctrlKey: srcEvent.ctrlKey,
              altKey: srcEvent.altKey,
              shiftKey: srcEvent.shiftKey,
              metaKey: srcEvent.metaKey
            });
            angular.element(eventPointer.target).trigger(eventObj);
          }

          /*
           * NOTE: nativeDispatchEvent is very performance sensitive.
           * @param srcEvent the original DOM touch event that started this.
           * @param eventType the name of the custom event to send (eg 'click' or '$md.drag')
           * @param eventPointer the pointer object that matches this event.
           */
          function nativeDispatchEvent(srcEvent, eventType, eventPointer) {
            eventPointer = eventPointer || pointer;
            var eventObj;

            if (eventType === 'click' || eventType == 'mouseup' || eventType == 'mousedown' ) {
              eventObj = document.createEvent('MouseEvents');
              eventObj.initMouseEvent(
                eventType, true, true, window, srcEvent.detail,
                eventPointer.x, eventPointer.y, eventPointer.x, eventPointer.y,
                srcEvent.ctrlKey, srcEvent.altKey, srcEvent.shiftKey, srcEvent.metaKey,
                srcEvent.button, srcEvent.relatedTarget || null
              );

            } else {
              eventObj = document.createEvent('CustomEvent');
              eventObj.initCustomEvent(eventType, true, true, {});
            }
            eventObj.$material = true;
            eventObj.pointer = eventPointer;
            eventObj.srcEvent = srcEvent;
            eventPointer.target.dispatchEvent(eventObj);
          }

        }

        /**
         * Attach Gestures: hook document and check shouldHijack clicks
         * ngInject
         */
        function attachToDocument( $mdGesture, $$MdGestureHandler ) {

          // Polyfill document.contains for IE11.
          // TODO: move to util
          document.contains || (document.contains = function (node) {
            return document.body.contains(node);
          });

          if (!isInitialized && $mdGesture.isHijackingClicks ) {
            /*
             * If hijack clicks is true, we preventDefault any click that wasn't
             * sent by ngMaterial. This is because on older Android & iOS, a false, or 'ghost',
             * click event will be sent ~400ms after a touchend event happens.
             * The only way to know if this click is real is to prevent any normal
             * click events, and add a flag to events sent by material so we know not to prevent those.
             * 
             * Two exceptions to click events that should be prevented are:
             *  - click events sent by the keyboard (eg form submit)
             *  - events that originate from an Ionic app
             */
            document.addEventListener('click'    , clickHijacker     , true);
            document.addEventListener('mouseup'  , mouseInputHijacker, true);
            document.addEventListener('mousedown', mouseInputHijacker, true);
            document.addEventListener('focus'    , mouseInputHijacker, true);

            isInitialized = true;
          }

          function mouseInputHijacker(ev) {
            var isKeyClick = !ev.clientX && !ev.clientY;
            if (!isKeyClick && !ev.$material && !ev.isIonicTap
              && !isInputEventFromLabelClick(ev)) {
              ev.preventDefault();
              ev.stopPropagation();
            }
          }

          function clickHijacker(ev) {
            var isKeyClick = ev.clientX === 0 && ev.clientY === 0;
            if (!isKeyClick && !ev.$material && !ev.isIonicTap
              && !isInputEventFromLabelClick(ev)) {
              ev.preventDefault();
              ev.stopPropagation();
              lastLabelClickPos = null;
            } else {
              lastLabelClickPos = null;
              if (ev.target.tagName.toLowerCase() == 'label') {
                lastLabelClickPos = {x: ev.x, y: ev.y};
              }
            }
          }


          // Listen to all events to cover all platforms.
          var START_EVENTS = 'mousedown touchstart pointerdown';
          var MOVE_EVENTS = 'mousemove touchmove pointermove';
          var END_EVENTS = 'mouseup mouseleave touchend touchcancel pointerup pointercancel';

          angular.element(document)
            .on(START_EVENTS, gestureStart)
            .on(MOVE_EVENTS, gestureMove)
            .on(END_EVENTS, gestureEnd)
            // For testing
            .on('$$mdGestureReset', function gestureClearCache () {
              lastPointer = pointer = null;
            });

          /*
           * When a DOM event happens, run all registered gesture handlers' lifecycle
           * methods which match the DOM event.
           * Eg when a 'touchstart' event happens, runHandlers('start') will call and
           * run `handler.cancel()` and `handler.start()` on all registered handlers.
           */
          function runHandlers(handlerEvent, event) {
            var handler;
            for (var name in HANDLERS) {
              handler = HANDLERS[name];
              if( handler instanceof $$MdGestureHandler ) {

                if (handlerEvent === 'start') {
                  // Run cancel to reset any handlers' state
                  handler.cancel();
                }
                handler[handlerEvent](event, pointer);

              }
            }
          }

          /*
           * gestureStart vets if a start event is legitimate (and not part of a 'ghost click' from iOS/Android)
           * If it is legitimate, we initiate the pointer state and mark the current pointer's type
           * For example, for a touchstart event, mark the current pointer as a 'touch' pointer, so mouse events
           * won't effect it.
           */
          function gestureStart(ev) {
            // If we're already touched down, abort
            if (pointer) return;

            var now = +Date.now();

            // iOS & old android bug: after a touch event, a click event is sent 350 ms later.
            // If <400ms have passed, don't allow an event of a different type than the previous event
            if (lastPointer && !typesMatch(ev, lastPointer) && (now - lastPointer.endTime < 1500)) {
              return;
            }

            pointer = makeStartPointer(ev);

            runHandlers('start', ev);
          }
          /*
           * If a move event happens of the right type, update the pointer and run all the move handlers.
           * "of the right type": if a mousemove happens but our pointer started with a touch event, do nothing.
           */
          function gestureMove(ev) {
            if (!pointer || !typesMatch(ev, pointer)) return;

            updatePointerState(ev, pointer);
            runHandlers('move', ev);
          }
          /*
           * If an end event happens of the right type, update the pointer, run endHandlers, and save the pointer as 'lastPointer'
           */
          function gestureEnd(ev) {
            if (!pointer || !typesMatch(ev, pointer)) return;

            updatePointerState(ev, pointer);
            pointer.endTime = +Date.now();

            runHandlers('end', ev);

            lastPointer = pointer;
            pointer = null;
          }

        }
        attachToDocument.$inject = ["$mdGesture", "$$MdGestureHandler"];

        // ********************
        // Module Functions
        // ********************

        /*
         * Initiate the pointer. x, y, and the pointer's type.
         */
        function makeStartPointer(ev) {
          var point = getEventPoint(ev);
          var startPointer = {
            startTime: +Date.now(),
            target: ev.target,
            // 'p' for pointer events, 'm' for mouse, 't' for touch
            type: ev.type.charAt(0)
          };
          startPointer.startX = startPointer.x = point.pageX;
          startPointer.startY = startPointer.y = point.pageY;
          return startPointer;
        }

        /*
         * return whether the pointer's type matches the event's type.
         * Eg if a touch event happens but the pointer has a mouse type, return false.
         */
        function typesMatch(ev, pointer) {
          return ev && pointer && ev.type.charAt(0) === pointer.type;
        }

        /**
         * Gets whether the given event is an input event that was caused by clicking on an
         * associated label element.
         *
         * This is necessary because the browser will, upon clicking on a label element, fire an
         * *extra* click event on its associated input (if any). mdGesture is able to flag the label
         * click as with `$material` correctly, but not the second input click.
         *
         * In order to determine whether an input event is from a label click, we compare the (x, y) for
         * the event to the (x, y) for the most recent label click (which is cleared whenever a non-label
         * click occurs). Unfortunately, there are no event properties that tie the input and the label
         * together (such as relatedTarget).
         *
         * @param {MouseEvent} event
         * @returns {boolean}
         */
        function isInputEventFromLabelClick(event) {
          return lastLabelClickPos
              && lastLabelClickPos.x == event.x
              && lastLabelClickPos.y == event.y;
        }

        /*
         * Update the given pointer based upon the given DOMEvent.
         * Distance, velocity, direction, duration, etc
         */
        function updatePointerState(ev, pointer) {
          var point = getEventPoint(ev);
          var x = pointer.x = point.pageX;
          var y = pointer.y = point.pageY;

          pointer.distanceX = x - pointer.startX;
          pointer.distanceY = y - pointer.startY;
          pointer.distance = Math.sqrt(
            pointer.distanceX * pointer.distanceX + pointer.distanceY * pointer.distanceY
          );

          pointer.directionX = pointer.distanceX > 0 ? 'right' : pointer.distanceX < 0 ? 'left' : '';
          pointer.directionY = pointer.distanceY > 0 ? 'up' : pointer.distanceY < 0 ? 'down' : '';

          pointer.duration = +Date.now() - pointer.startTime;
          pointer.velocityX = pointer.distanceX / pointer.duration;
          pointer.velocityY = pointer.distanceY / pointer.duration;
        }

        /*
         * Normalize the point where the DOM event happened whether it's touch or mouse.
         * @returns point event obj with pageX and pageY on it.
         */
        function getEventPoint(ev) {
          ev = ev.originalEvent || ev; // support jQuery events
          return (ev.touches && ev.touches[0]) ||
            (ev.changedTouches && ev.changedTouches[0]) ||
            ev;
        }

    })(window.jQuery);

    (function () {
        'use strict';

        angular.module('material.core')
            .provider('$$interimElement', InterimElementProvider);

        /*
         * @ngdoc service
         * @name $$interimElement
         * @module material.core
         *
         * @description
         *
         * Factory that contructs `$$interimElement.$service` services.
         * Used internally in material design for elements that appear on screen temporarily.
         * The service provides a promise-like API for interacting with the temporary
         * elements.
         *
         * ```js
         * app.service('$mdToast', function($$interimElement) {
         *   var $mdToast = $$interimElement(toastDefaultOptions);
         *   return $mdToast;
         * });
         * ```
         * @param {object=} defaultOptions Options used by default for the `show` method on the service.
         *
         * @returns {$$interimElement.$service}
         *
         */

        function InterimElementProvider() {
            createInterimElementProvider.$get = InterimElementFactory;
            InterimElementFactory.$inject = ["$document", "$q", "$rootScope", "$timeout", "$rootElement", "$animate", "$interpolate", "$mdCompiler"];
            return createInterimElementProvider;

            /**
             * Returns a new provider which allows configuration of a new interimElement
             * service. Allows configuration of default options & methods for options,
             * as well as configuration of 'preset' methods (eg dialog.basic(): basic is a preset method)
             */
            function createInterimElementProvider(interimFactoryName) {
                var EXPOSED_METHODS = ['onHide', 'onShow', 'onRemove'];
                var providerConfig = {
                    presets: {}
                };
                var provider = {
                    setDefaults: setDefaults,
                    addPreset: addPreset,
                    $get: factory
                };

                /**
                 * all interim elements will come with the 'build' preset
                 */
                provider.addPreset('build', {
                    methods: ['controller', 'controllerAs', 'resolve',
                        'template', 'templateUrl', 'themable', 'transformTemplate', 'parent'
                    ]
                });

                factory.$inject = ["$$interimElement", "$animate", "$injector"];
                return provider;

                /**
                 * Save the configured defaults to be used when the factory is instantiated
                 */
                function setDefaults(definition) {
                    providerConfig.optionsFactory = definition.options;
                    providerConfig.methods = (definition.methods || []).concat(EXPOSED_METHODS);
                    return provider;
                }

                /**
                 * Save the configured preset to be used when the factory is instantiated
                 */
                function addPreset(name, definition) {
                    definition = definition || {};
                    definition.methods = definition.methods || [];
                    definition.options = definition.options || function () {
                        return {};
                    };

                    if (/^cancel|hide|show$/.test(name)) {
                        throw new Error("Preset '" + name + "' in " + interimFactoryName + " is reserved!");
                    }
                    if (definition.methods.indexOf('_options') > -1) {
                        throw new Error("Method '_options' in " + interimFactoryName + " is reserved!");
                    }
                    providerConfig.presets[name] = {
                        methods: definition.methods.concat(EXPOSED_METHODS),
                        optionsFactory: definition.options,
                        argOption: definition.argOption
                    };
                    return provider;
                }

                /**
                 * Create a factory that has the given methods & defaults implementing interimElement
                 */
                /* @ngInject */
                function factory($$interimElement, $animate, $injector) {
                    var defaultMethods;
                    var defaultOptions;
                    var interimElementService = $$interimElement();

                    /*
                     * publicService is what the developer will be using.
                     * It has methods hide(), cancel(), show(), build(), and any other
                     * presets which were set during the config phase.
                     */
                    var publicService = {
                        hide: interimElementService.hide,
                        cancel: interimElementService.cancel,
                        show: showInterimElement
                    };

                    defaultMethods = providerConfig.methods || [];
                    // This must be invoked after the publicService is initialized
                    defaultOptions = invokeFactory(providerConfig.optionsFactory, {});

                    angular.forEach(providerConfig.presets, function (definition, name) {
                        var presetDefaults = invokeFactory(definition.optionsFactory, {});
                        var presetMethods = (definition.methods || []).concat(defaultMethods);

                        // Every interimElement built with a preset has a field called `$type`,
                        // which matches the name of the preset.
                        // Eg in preset 'confirm', options.$type === 'confirm'
                        angular.extend(presetDefaults, {
                            $type: name
                        });

                        // This creates a preset class which has setter methods for every
                        // method given in the `.addPreset()` function, as well as every
                        // method given in the `.setDefaults()` function.
                        //
                        // @example
                        // .setDefaults({
                        //   methods: ['hasBackdrop', 'clickOutsideToClose', 'escapeToClose', 'targetEvent'],
                        //   options: dialogDefaultOptions
                        // })
                        // .addPreset('alert', {
                        //   methods: ['title', 'ok'],
                        //   options: alertDialogOptions
                        // })
                        //
                        // Set values will be passed to the options when interimElemnt.show() is called.
                        function Preset(opts) {
                            this._options = angular.extend({}, presetDefaults, opts);
                        }
                        angular.forEach(presetMethods, function (name) {
                            Preset.prototype[name] = function (value) {
                                this._options[name] = value;
                                return this;
                            };
                        });

                        // Create shortcut method for one-linear methods
                        if (definition.argOption) {
                            var methodName = 'show' + name.charAt(0).toUpperCase() + name.slice(1);
                            publicService[methodName] = function (arg) {
                                var config = publicService[name](arg);
                                return publicService.show(config);
                            };
                        }

                        // eg $mdDialog.alert() will return a new alert preset
                        publicService[name] = function (arg) {
                            // If argOption is supplied, eg `argOption: 'content'`, then we assume
                            // if the argument is not an options object then it is the `argOption` option.
                            //
                            // @example `$mdToast.simple('hello')` // sets options.content to hello
                            //                                     // because argOption === 'content'
                            if (arguments.length && definition.argOption && !angular.isObject(arg) &&
                                !angular.isArray(arg)) {
                                return (new Preset())[definition.argOption](arg);
                            } else {
                                return new Preset(arg);
                            }

                        };
                    });

                    return publicService;

                    function showInterimElement(opts) {
                        // opts is either a preset which stores its options on an _options field,
                        // or just an object made up of options
                        if (opts && opts._options) opts = opts._options;
                        return interimElementService.show(
                            angular.extend({}, defaultOptions, opts)
                        );
                    }

                    /**
                     * Helper to call $injector.invoke with a local of the factory name for
                     * this provider.
                     * If an $mdDialog is providing options for a dialog and tries to inject
                     * $mdDialog, a circular dependency error will happen.
                     * We get around that by manually injecting $mdDialog as a local.
                     */
                    function invokeFactory(factory, defaultVal) {
                        var locals = {};
                        locals[interimFactoryName] = publicService;
                        return $injector.invoke(factory || function () {
                            return defaultVal;
                        }, {}, locals);
                    }

                }

            }

            /* @ngInject */
            function InterimElementFactory($document, $q, $rootScope, $timeout, $rootElement, $animate,
                $interpolate, $mdCompiler) {
                var startSymbol = $interpolate.startSymbol(),
                    endSymbol = $interpolate.endSymbol(),
                    usesStandardSymbols = ((startSymbol === '{{') && (endSymbol === '}}')),
                    processTemplate = usesStandardSymbols ? angular.identity : replaceInterpolationSymbols;

                return function createInterimElementService() {
                    /*
                     * @ngdoc service
                     * @name $$interimElement.$service
                     *
                     * @description
                     * A service used to control inserting and removing an element into the DOM.
                     *
                     */
                    var stack = [];
                    var service;
                    return service = {
                        show: show,
                        hide: hide,
                        cancel: cancel
                    };

                    /*
                     * @ngdoc method
                     * @name $$interimElement.$service#show
                     * @kind function
                     *
                     * @description
                     * Adds the `$interimElement` to the DOM and returns a promise that will be resolved or rejected
                     * with hide or cancel, respectively.
                     *
                     * @param {*} options is hashMap of settings
                     * @returns a Promise
                     *
                     */
                    function show(options) {
                        options.zIndex = 80 + stack.length;
                        var interimElement = new InterimElement(options);

                        stack.unshift(interimElement);
                        return interimElement.show().then(function () {
                            return interimElement.deferred.promise;
                        });
                    }

                    /*
                     * @ngdoc method
                     * @name $$interimElement.$service#hide
                     * @kind function
                     *
                     * @description
                     * Removes the `$interimElement` from the DOM and resolves the promise returned from `show`
                     *
                     * @param {*} resolveParam Data to resolve the promise with
                     * @returns a Promise that will be resolved after the element has been removed.
                     *
                     */
                    function hide(response, interimElementAt) {
                        var interimElement;
                        if (interimElementAt !== undefined) {
                            interimElement = interimElementAt;
                            stack.splice(stack.indexOf(interimElementAt), 1);
                        } else {
                            interimElement = stack.shift();
                        }
                        interimElement && interimElement.remove().then(function () {
                            interimElement.deferred.resolve(response);
                        });

                        return interimElement ? interimElement.deferred.promise : $q.when(response);
                    }

                    /*
                     * @ngdoc method
                     * @name $$interimElement.$service#cancel
                     * @kind function
                     *
                     * @description
                     * Removes the `$interimElement` from the DOM and rejects the promise returned from `show`
                     *
                     * @param {*} reason Data to reject the promise with
                     * @returns Promise that will be rejected after the element has been removed.
                     *
                     */
                    function cancel(reason, interimElementAt) {
                        var interimElement;
                        if (interimElementAt !== undefined) {
                            interimElement = interimElementAt;
                            stack.splice(stack.indexOf(interimElementAt), 1);
                        } else {
                            interimElement = stack.shift();
                        }
                        interimElement && interimElement.remove().then(function () {
                            interimElement.deferred.reject(reason);
                        });

                        return interimElement ? interimElement.deferred.promise : $q.reject(reason);
                    }


                    /*
                     * Internal Interim Element Object
                     * Used internally to manage the DOM element and related data
                     */
                    function InterimElement(options) {
                        var self;
                        var hideTimeout, element;

                        options = options || {};
                        options = angular.extend({
                            scope: options.scope || $rootScope.$new(options.isolateScope),
                            onShow: function (scope, element, options) {
                                return $animate.enter(element, options.parent);
                            },
                            onRemove: function (scope, element, options) {
                                // Element could be undefined if a new element is shown before
                                // the old one finishes compiling.
                                return element && $animate.leave(element) || $q.when();
                            }
                        }, options);

                        if (options.template) {
                            options.template = processTemplate(options.template);
                        }

                        self = {
                            options: options,
                            deferred: $q.defer(),
                            show: function () {
                                return $mdCompiler.compile(options).then(function (compileData) {
                                    angular.extend(compileData.locals, self.options);

                                    // Search for parent at insertion time, if not specified
                                    if (angular.isString(options.parent)) {
                                        options.parent = angular.element($document[0].querySelector(options.parent));
                                    } else if (!options.parent) {
                                        options.parent = $rootElement.find('body');
                                        if (!options.parent.length) options.parent = $rootElement;
                                    }

                                    element = compileData.link(options.scope);
                                    element.css('z-index', options.zIndex);

                                    var ret = options.onShow(options.scope, element, options);
                                    return $q.when(ret)
                                        .then(function () {
                                            // Issue onComplete callback when the `show()` finishes
                                            (options.onComplete || angular.noop)(options.scope, element, options);
                                            startHideTimeout();
                                        });

                                    function startHideTimeout() {
                                        if (options.hideDelay) {
                                            hideTimeout = $timeout(service.cancel, options.hideDelay);
                                        }
                                    }
                                });
                            },
                            cancelTimeout: function () {
                                if (hideTimeout) {
                                    $timeout.cancel(hideTimeout);
                                    hideTimeout = undefined;
                                }
                            },
                            remove: function () {
                                self.cancelTimeout();
                                var ret = options.onRemove(options.scope, element, options);
                                return $q.when(ret).then(function () {
                                    options.scope.$destroy();
                                });
                            }
                        };

                        options.interimElement = self;
                        options.stack = stack;

                        return self;
                    }
                };

                /*
                 * Replace `{{` and `}}` in a string (usually a template) with the actual start-/endSymbols used
                 * for interpolation. This allows pre-defined templates (for components such as dialog, toast etc)
                 * to continue to work in apps that use custom interpolation start-/endSymbols.
                 *
                 * @param {string} text The text in which to replace `{{` / `}}`
                 * @returns {string} The modified string using the actual interpolation start-/endSymbols
                 */
                function replaceInterpolationSymbols(text) {
                    if (!text || !angular.isString(text)) return text;
                    return text.replace(/\{\{/g, startSymbol).replace(/}}/g, endSymbol);
                }
            }

        }

    })();
    (function () {
        'use strict';

        angular.module('material.core')
            .provider('$$interimStackableElement', InterimElementProvider);

        /*
         * @ngdoc service
         * @name $$interimStackableElement
         * @module material.core
         *
         * @description
         *
         * Factory that contructs `$$interimStackableElement.$service` services.
         * Used internally in material design for elements that appear on screen temporarily.
         * The service provides a promise-like API for interacting with the temporary
         * elements.
         *
         * ```js
         * app.service('$mdToast', function($$interimStackableElement) {
         *   var $mdToast = $$interimStackableElement(toastDefaultOptions);
         *   return $mdToast;
         * });
         * ```
         * @param {object=} defaultOptions Options used by default for the `show` method on the service.
         *
         * @returns {$$interimStackableElement.$service}
         *
         */

        function InterimElementProvider() {
            createInterimElementProvider.$get = InterimElementFactory;
            InterimElementFactory.$inject = ["$document", "$q", "$rootScope", "$timeout", "$rootElement", "$animate", "$interpolate", "$mdCompiler"];
            return createInterimElementProvider;

            /**
             * Returns a new provider which allows configuration of a new interimElement
             * service. Allows configuration of default options & methods for options,
             * as well as configuration of 'preset' methods (eg dialog.basic(): basic is a preset method)
             */
            function createInterimElementProvider(interimFactoryName) {
                var EXPOSED_METHODS = ['onHide', 'onShow', 'onRemove'];
                var providerConfig = {
                    presets: {}
                };
                var provider = {
                    setDefaults: setDefaults,
                    addPreset: addPreset,
                    $get: factory
                };

                /**
                 * all interim elements will come with the 'build' preset
                 */
                provider.addPreset('build', {
                    methods: ['controller', 'controllerAs', 'resolve',
                        'template', 'templateUrl', 'themable', 'transformTemplate', 'parent'
                    ]
                });

                factory.$inject = ["$$interimStackableElement", "$animate", "$injector"];
                return provider;

                /**
                 * Save the configured defaults to be used when the factory is instantiated
                 */
                function setDefaults(definition) {
                    providerConfig.optionsFactory = definition.options;
                    providerConfig.methods = (definition.methods || []).concat(EXPOSED_METHODS);
                    return provider;
                }

                /**
                 * Save the configured preset to be used when the factory is instantiated
                 */
                function addPreset(name, definition) {
                    definition = definition || {};
                    definition.methods = definition.methods || [];
                    definition.options = definition.options || function () {
                        return {};
                    };

                    if (/^cancel|hide|show$/.test(name)) {
                        throw new Error("Preset '" + name + "' in " + interimFactoryName + " is reserved!");
                    }
                    if (definition.methods.indexOf('_options') > -1) {
                        throw new Error("Method '_options' in " + interimFactoryName + " is reserved!");
                    }
                    providerConfig.presets[name] = {
                        methods: definition.methods.concat(EXPOSED_METHODS),
                        optionsFactory: definition.options,
                        argOption: definition.argOption
                    };
                    return provider;
                }

                /**
                 * Create a factory that has the given methods & defaults implementing interimElement
                 */
                /* @ngInject */
                function factory($$interimStackableElement, $animate, $injector) {
                    var defaultMethods;
                    var defaultOptions;
                    var interimElementService = $$interimStackableElement();

                    /*
                     * publicService is what the developer will be using.
                     * It has methods hide(), cancel(), show(), build(), and any other
                     * presets which were set during the config phase.
                     */
                    var publicService = {
                        hide: interimElementService.hide,
                        cancel: interimElementService.cancel,
                        show: showInterimElement
                    };

                    defaultMethods = providerConfig.methods || [];
                    // This must be invoked after the publicService is initialized
                    defaultOptions = invokeFactory(providerConfig.optionsFactory, {});

                    angular.forEach(providerConfig.presets, function (definition, name) {
                        var presetDefaults = invokeFactory(definition.optionsFactory, {});
                        var presetMethods = (definition.methods || []).concat(defaultMethods);

                        // Every interimElement built with a preset has a field called `$type`,
                        // which matches the name of the preset.
                        // Eg in preset 'confirm', options.$type === 'confirm'
                        angular.extend(presetDefaults, {
                            $type: name
                        });

                        function Preset(opts) {
                            this._options = angular.extend({}, presetDefaults, opts);
                        }
                        angular.forEach(presetMethods, function (name) {
                            Preset.prototype[name] = function (value) {
                                this._options[name] = value;
                                return this;
                            };
                        });

                        // Create shortcut method for one-linear methods
                        if (definition.argOption) {
                            var methodName = 'show' + name.charAt(0).toUpperCase() + name.slice(1);
                            publicService[methodName] = function (arg) {
                                var config = publicService[name](arg);
                                return publicService.show(config);
                            };
                        }

                        // eg $mdDialog.alert() will return a new alert preset
                        publicService[name] = function (arg) {
                            // If argOption is supplied, eg `argOption: 'content'`, then we assume
                            // if the argument is not an options object then it is the `argOption` option.
                            //
                            // @example `$mdToast.simple('hello')` // sets options.content to hello
                            //                                     // because argOption === 'content'
                            if (arguments.length && definition.argOption && !angular.isObject(arg) &&
                                !angular.isArray(arg)) {
                                return (new Preset())[definition.argOption](arg);
                            } else {
                                return new Preset(arg);
                            }

                        };
                    });

                    return publicService;

                    function showInterimElement(opts) {
                        // opts is either a preset which stores its options on an _options field,
                        // or just an object made up of options
                        if (opts && opts._options) opts = opts._options;
                        return interimElementService.show(
                            angular.extend({}, defaultOptions, opts)
                        );
                    }

                    /**
                     * Helper to call $injector.invoke with a local of the factory name for
                     * this provider.
                     * If an $mdDialog is providing options for a dialog and tries to inject
                     * $mdDialog, a circular dependency error will happen.
                     * We get around that by manually injecting $mdDialog as a local.
                     */
                    function invokeFactory(factory, defaultVal) {
                        var locals = {};
                        locals[interimFactoryName] = publicService;
                        return $injector.invoke(factory || function () {
                            return defaultVal;
                        }, {}, locals);
                    }

                }

            }

            /* @ngInject */
            function InterimElementFactory($document, $q, $rootScope, $timeout, $rootElement, $animate,
                $interpolate, $mdCompiler) {
                var startSymbol = $interpolate.startSymbol(),
                    endSymbol = $interpolate.endSymbol(),
                    usesStandardSymbols = ((startSymbol === '{{') && (endSymbol === '}}')),
                    processTemplate = usesStandardSymbols ? angular.identity : replaceInterpolationSymbols;

                return function createInterimElementService() {
                    /*
                     * @ngdoc service
                     * @name $$interimStackableElement.$service
                     *
                     * @description
                     * A service used to control inserting and removing an element into the DOM.
                     *
                     */
                    var stack = [];
                    var service;
                    return service = {
                        show: show,
                        hide: hide,
                        cancel: cancel
                    };

                    /*
                     * @ngdoc method
                     * @name $$interimStackableElement.$service#show
                     * @kind function
                     *
                     * @description
                     * Adds the `$interimElement` to the DOM and returns a promise that will be resolved or rejected
                     * with hide or cancel, respectively.
                     *
                     * @param {*} options is hashMap of settings
                     * @returns a Promise
                     *
                     */
                    function show(options) {
                        options.zIndex = 80 + stack.length;
                        var interimElement = new InterimElement(options);

                        stack.unshift(interimElement);
                        return interimElement.show().then(function () {
                            return interimElement.deferred.promise;
                        });
                    }

                    /*
                     * @ngdoc method
                     * @name $$interimStackableElement.$service#hide
                     * @kind function
                     *
                     * @description
                     * Removes the `$interimElement` from the DOM and resolves the promise returned from `show`
                     *
                     * @param {*} resolveParam Data to resolve the promise with
                     * @returns a Promise that will be resolved after the element has been removed.
                     *
                     */
                    function hide(response, interimElementAt) {
                        var interimElement;
                        if (interimElementAt !== undefined) {
                            interimElement = interimElementAt;
                            stack.splice(stack.indexOf(interimElementAt), 1);
                        } else {
                            interimElement = stack.shift();
                        }
                        interimElement && interimElement.remove().then(function () {
                            interimElement.deferred.resolve(response);
                        });

                        return interimElement ? interimElement.deferred.promise : $q.when(response);
                    }

                    /*
                     * @ngdoc method
                     * @name $$interimStackableElement.$service#cancel
                     * @kind function
                     *
                     * @description
                     * Removes the `$interimElement` from the DOM and rejects the promise returned from `show`
                     *
                     * @param {*} reason Data to reject the promise with
                     * @returns Promise that will be rejected after the element has been removed.
                     *
                     */
                    function cancel(reason, interimElementAt) {
                        var interimElement;
                        if (interimElementAt !== undefined) {
                            interimElement = interimElementAt;
                            stack.splice(stack.indexOf(interimElementAt), 1);
                        } else {
                            interimElement = stack.shift();
                        }
                        interimElement && interimElement.remove().then(function () {
                            interimElement.deferred.reject(reason);
                        });

                        return interimElement ? interimElement.deferred.promise : $q.reject(reason);
                    }


                    /*
                     * Internal Interim Element Object
                     * Used internally to manage the DOM element and related data
                     */
                    function InterimElement(options) {
                        var self;
                        var hideTimeout, element;

                        options = options || {};
                        options = angular.extend({
                            scope: options.scope || $rootScope.$new(options.isolateScope),
                            onShow: function (scope, element, options) {
                                return $animate.enter(element, options.parent);
                            },
                            onRemove: function (scope, element, options) {
                                // Element could be undefined if a new element is shown before
                                // the old one finishes compiling.
                                return element && $animate.leave(element) || $q.when();
                            }
                        }, options);

                        if (options.template) {
                            options.template = processTemplate(options.template);
                        }

                        self = {
                            options: options,
                            deferred: $q.defer(),
                            show: function () {
                                return $mdCompiler.compile(options).then(function (compileData) {
                                    angular.extend(compileData.locals, self.options);

                                    // Search for parent at insertion time, if not specified
                                    if (angular.isString(options.parent)) {
                                        options.parent = angular.element($document[0].querySelector(options.parent));
                                    } else if (!options.parent) {
                                        options.parent = $rootElement.find('body');
                                        if (!options.parent.length) options.parent = $rootElement;
                                    }

                                    element = compileData.link(options.scope);
                                    element.css('z-index', options.zIndex);

                                    var ret = options.onShow(options.scope, element, options);
                                    return $q.when(ret)
                                        .then(function () {
                                            // Issue onComplete callback when the `show()` finishes
                                            (options.onComplete || angular.noop)(options.scope, element, options);
                                            startHideTimeout();
                                        });

                                    function startHideTimeout() {
                                        if (options.hideDelay) {
                                            hideTimeout = $timeout(service.cancel, options.hideDelay);
                                        }
                                    }
                                });
                            },
                            cancelTimeout: function () {
                                if (hideTimeout) {
                                    $timeout.cancel(hideTimeout);
                                    hideTimeout = undefined;
                                }
                            },
                            remove: function () {
                                self.cancelTimeout();
                                var ret = options.onRemove(options.scope, element, options);
                                return $q.when(ret).then(function () {
                                    options.scope.$destroy();
                                });
                            }
                        };

                        options.interimElement = self;
                        options.stack = stack;

                        return self;
                    }
                };

                /*
                 * Replace `{{` and `}}` in a string (usually a template) with the actual start-/endSymbols used
                 * for interpolation. This allows pre-defined templates (for components such as dialog, toast etc)
                 * to continue to work in apps that use custom interpolation start-/endSymbols.
                 *
                 * @param {string} text The text in which to replace `{{` / `}}`
                 * @returns {string} The modified string using the actual interpolation start-/endSymbols
                 */
                function replaceInterpolationSymbols(text) {
                    if (!text || !angular.isString(text)) return text;
                    return text.replace(/\{\{/g, startSymbol).replace(/}}/g, endSymbol);
                }
            }

        }

    })();
    (function () {
        'use strict';

        /**
         * @ngdoc module
         * @name material.core.componentRegistry
         *
         * @description
         * A component instance registration service.
         * Note: currently this as a private service in the SideNav component.
         */
        angular.module('material.core')
            .factory('$mdComponentRegistry', ComponentRegistry);

        /*
         * @private
         * @ngdoc factory
         * @name ComponentRegistry
         * @module material.core.componentRegistry
         *
         */
        function ComponentRegistry($log, $q) {

            var self;
            var instances = [];
            var pendings = {};

            return self = {
                /**
                 * Used to print an error when an instance for a handle isn't found.
                 */
                notFoundError: function (handle) {
                    $log.error('No instance found for handle', handle);
                },
                /**
                 * Return all registered instances as an array.
                 */
                getInstances: function () {
                    return instances;
                },

                /**
                 * Get a registered instance.
                 * @param handle the String handle to look up for a registered instance.
                 */
                get: function (handle) {
                    if (!isValidID(handle)) return null;

                    var i, j, instance;
                    for (i = 0, j = instances.length; i < j; i++) {
                        instance = instances[i];
                        if (instance.$$mdHandle === handle) {
                            return instance;
                        }
                    }
                    return null;
                },

                /**
                 * Register an instance.
                 * @param instance the instance to register
                 * @param handle the handle to identify the instance under.
                 */
                register: function (instance, handle) {
                    if (!handle) return angular.noop;

                    instance.$$mdHandle = handle;
                    instances.push(instance);
                    resolveWhen();

                    return deregister;

                    /**
                     * Remove registration for an instance
                     */
                    function deregister() {
                        var index = instances.indexOf(instance);
                        if (index !== -1) {
                            instances.splice(index, 1);
                        }
                    }

                    /**
                     * Resolve any pending promises for this instance
                     */
                    function resolveWhen() {
                        var dfd = pendings[handle];
                        if (dfd) {
                            dfd.resolve(instance);
                            delete pendings[handle];
                        }
                    }
                },

                /**
                 * Async accessor to registered component instance
                 * If not available then a promise is created to notify
                 * all listeners when the instance is registered.
                 */
                when: function (handle) {
                    if (isValidID(handle)) {
                        var deferred = $q.defer();
                        var instance = self.get(handle);

                        if (instance) {
                            deferred.resolve(instance);
                        } else {
                            pendings[handle] = deferred;
                        }

                        return deferred.promise;
                    }
                    return $q.reject("Invalid `md-component-id` value.");
                }

            };

            function isValidID(handle) {
                return handle && (handle !== "");
            }

        }
        ComponentRegistry.$inject = ["$log", "$q"];


    })();

    (function () {
        'use strict';

        function isSafari() {
            var ua = navigator.userAgent.toLowerCase(); 
            if (ua.indexOf('safari') !== -1) { 
                if (ua.indexOf('chrome') === -1) {
                  return true;
                }
            }
            return false;
        }

        angular.module('material.core')
            .factory('$mdInkRipple', InkRippleService)
            .directive('mdInkRipple', InkRippleDirective)
            .directive('mdNoInk', attrNoDirective())
            .directive('mdNoBar', attrNoDirective())
            .directive('mdNoStretch', attrNoDirective());

        function InkRippleDirective($mdInkRipple, $parse) {
            return {
                controller: angular.noop,
                link: function (scope, element, attr) {
                    if (attr.hasOwnProperty('mdInkRippleCheckbox')) {
                        $mdInkRipple.attachCheckboxBehavior(scope, element);
                    } else {
                        $mdInkRipple.attachButtonBehavior(scope, element);
                    }
                }
            };
        }
        InkRippleDirective.$inject = ["$mdInkRipple", "$parse"];

        function InkRippleService($window, $timeout, $parse) {

            return {
                attachButtonBehavior: attachButtonBehavior,
                attachCheckboxBehavior: attachCheckboxBehavior,
                attachTabBehavior: attachTabBehavior,
                attach: attach
            };

            function attachButtonBehavior(scope, element, options) {
                return attach(scope, element, angular.extend({
                    isFAB: element.hasClass('md-fab'),
                    isMenuItem: element.hasClass('md-menu-item'),
                    center: false,
                    dimBackground: true
                }, options));
            }

            function attachCheckboxBehavior(scope, element, options) {
                return attach(scope, element, angular.extend({
                    center: true,
                    dimBackground: false,
                    fitRipple: true
                }, options));
            }

            function attachTabBehavior(scope, element, options) {
                return attach(scope, element, angular.extend({
                    center: false,
                    dimBackground: true,
                    outline: true
                }, options));
            }

            function attach(scope, element, options) {
                if (element.controller('mdNoInk')) return angular.noop;

                var ignore = element.attr('md-ink-ripple-ignore');

                ignore = (ignore ? $parse(ignore)(scope) : undefined);

                options = angular.extend({
                    colorElement: element,
                    mousedown: true,
                    hover: true,
                    focus: true,
                    center: false,
                    mousedownPauseTime: 150,
                    dimBackground: false,
                    outline: false,
                    isFAB: false,
                    isMenuItem: false,
                    fitRipple: false
                }, options);

                var rippleSize,
                    controller = element.controller('mdInkRipple') || {},
                    counter = 0,
                    ripples = [],
                    states = [],
                    isActiveExpr = element.attr('md-highlight'),
                    isActive = false,
                    isHeld = false,
                    node = element[0],
                    rippleSizeSetting = element.attr('md-ripple-size');

                switch (rippleSizeSetting) {
                case 'full':
                    options.isFAB = true;
                    break;
                case 'partial':
                    options.isFAB = false;
                    break;
                }

                element.addClass('ripple-presence');

                // expose onInput for ripple testing
                if (options.mousedown) {
                    element.on('$md.pressdown', onPressDown);
                    //.on('click', onPressDown);
                }


                // Publish self-detach method if desired...
                return function detach() {
                    element.off('$md.pressdown', onPressDown);
                    //.off('$md.pressup', onPressUp);
                    //.off('click', onPressDown);
                    element.removeClass('ripple-presence');
                };


                /**
                 * Handles user input start and stop events
                 *
                 */
                // temporary fix for the safari ripple
                var k = null;

                function onPressDown(ev) {
                    if (k) {
                        clearTimeout(k);
                    }
                    k = setTimeout(function () {
                        onPressDown2(ev);
                    }, (isSafari() ? 80 : 0));
                }

                function onPressDown2(ev) {
                    if (!isRippleAllowed()) return;

                    var cls = 'ripple-animation';

                    if (ignore && ev.target) {
                        var target = $(ev.target),
                            skip = false;
                        angular.forEach(ignore, function (ig) {
                            if (target.is(ig) || target.parent().is(ig)) {
                                skip = true;
                            }
                        });
                        if (skip) {
                            return;
                        }
                    }
                    isHeld = true;
                    var worker = {};
                    worker.style = {
                        'top': '0',
                        'left': '0'
                    };
                    var ripple = angular.element('<div class="ripple-active"></div>');
                    ripple.css(worker.style);
                    if (element[0].hasAttribute('ripple-dark')) {
                        ripple.addClass('ripple-dark');
                    } else if (element[0].hasAttribute('ripple-light')) {
                        ripple.addClass('ripple-light');
                    }
                    element.append(ripple);
                    var squared = element[0].hasAttribute('md-ink-ripple-action') || element[0].hasAttribute('ripple-action');
                    if (squared) {
                        worker.style = {
                            'top': '0px',
                            'left': '0px',
                            'height': element.outerWidth() + 'px',
                            'width': element.outerWidth() + 'px'
                        };
                        cls += ' ripple-action';
                    } else if (element[0].hasAttribute('md-ink-ripple-switch')) {
                        worker.style = {
                            'top': '-14px',
                            'left': '-14px',
                            'height': '48px',
                            'width': '48px'
                        };
                    } else {
                        var parent_width = element.width();
                        var parent_height = element.height();
                        var element_position = element[0].getBoundingClientRect();
                        var parent_diagonal = 2 * (Math.round(Math.sqrt((parent_width * parent_width) + (parent_height * parent_height))));
                        if (parent_diagonal > 2000) {
                            parent_diagonal = 2000;
                        }
                        var margin = -(parent_diagonal / 2);
                        worker.style = {
                            'top': (ev.clientY - element_position.top),
                            'left': (ev.clientX - element_position.left),
                            'height': parent_diagonal,
                            'width': parent_diagonal,
                            'margin-top': margin,
                            'margin-left': margin
                        };
                    }


                    ripple.css(worker.style);

                    $timeout(function () {
                        ripple.addClass(cls);
                        ripple.oneAnimationEnd(function () {
                            ripple.remove();
                        });
                    }, 0, false);

                }

                function onPressUp(ev) {
                    isHeld = false;
                }

                /**
                 * Determines if the ripple is allowed
                 *
                 * @returns {boolean} true if the ripple is allowed, false if not
                 */
                function isRippleAllowed() {
                    var parent = node.parentNode;
                    var grandparent = parent && parent.parentNode;
                    var ancestor = grandparent && grandparent.parentNode;
                    return !isDisabled(node) && !isDisabled(parent) && !isDisabled(grandparent) && !isDisabled(ancestor);

                    function isDisabled(elem) {
                        return elem && elem.hasAttribute && elem.hasAttribute('disabled');
                    }
                }

            }
        }
        InkRippleService.$inject = ["$window", "$timeout", "$parse"];

        function attrNoDirective() {
            return function () {
                return {
                    controller: angular.noop
                };
            };
        }
    })();



}());
(function () {

    angular.module('material.components.input', [
            'material.core'
        ])
        .directive('mdInputContainer', mdInputContainerDirective)
        .directive('label', labelDirective)
        .directive('input', inputTextareaDirective)
        .directive('textarea', inputTextareaDirective)
        .directive('mdMaxlength', mdMaxlengthDirective)
        .directive('placeholder', placeholderDirective);

    function mdInputContainerDirective($parse) {
        ContainerCtrl.$inject = ["$scope", "$element", "$attrs"];
        return {
            restrict: 'E',
            link: postLink,
            controller: ContainerCtrl
        };

        function postLink(scope, element, attr) {

        }

        function ContainerCtrl($scope, $element, $attrs) {
            var self = this;

            self.isErrorGetter = $attrs.mdIsError && $parse($attrs.mdIsError);

            self.element = $element;
            self.setFocused = function (isFocused) {
                $element.toggleClass('md-input-focused', !!isFocused);
            };
            self.setHasValue = function (hasValue) {
                $element.toggleClass('md-input-has-value', !!hasValue);
            };
            self.setNoFloat = function (hasValue) {
                $element.toggleClass('md-input-no-float', !!hasValue);
            };
            self.setInvalid = function (isInvalid) {
                $element.toggleClass('md-input-invalid', !!isInvalid);
            };
            $scope.$watch(function () {
                return self.label && self.input;
            }, function (hasLabelAndInput) {
                if (hasLabelAndInput && !self.label.attr('for')) {
                    self.label.attr('for', self.input.attr('id'));
                }
            });
        }
    }
    mdInputContainerDirective.$inject = ["$parse"];

    function labelDirective() {
        return {
            restrict: 'E',
            require: '^?mdInputContainer',
            link: function (scope, element, attr, containerCtrl) {
                if (!containerCtrl) return;

                containerCtrl.label = element;
                scope.$on('$destroy', function () {
                    containerCtrl.label = null;
                });
            }
        };
    }

    function inputTextareaDirective($mdUtil, $window, $compile, $animate) {
        return {
            restrict: 'E',
            require: ['^?mdInputContainer', '?ngModel'],
            link: postLink
        };

        function postLink(scope, element, attr, ctrls) {

            var containerCtrl = ctrls[0];
            var ngModelCtrl = ctrls[1] || $mdUtil.fakeNgModel();
            var isReadonly = angular.isDefined(attr.readonly);

            if (!containerCtrl) return;
            if (containerCtrl.input) {
                throw new Error("<md-input-container> can only have *one* <input> or <textarea> child element!");
            }
            containerCtrl.input = element;

            element.addClass('md-input');
            if (!element.attr('id')) {
                element.attr('id', 'input_' + $mdUtil.nextUid());
            }

            function ngModelPipelineCheckValue(arg) {
                containerCtrl.setHasValue(!ngModelCtrl.$isEmpty(arg));
                return arg;
            }

            function inputCheckValue() {
                // An input's value counts if its length > 0,
                // or if the input's validity state says it has bad input (eg string in a number input)
                containerCtrl.setHasValue(element.val().length > 0 || (element[0].validity || {}).badInput);
            }


            var isErrorGetter = containerCtrl.isErrorGetter || function () {
                return ngModelCtrl.$invalid && (ngModelCtrl.$dirty || ngModelCtrl.$touched);
            };
            scope.$watch(isErrorGetter, containerCtrl.setInvalid);

            ngModelCtrl.$parsers.push(ngModelPipelineCheckValue);
            ngModelCtrl.$formatters.push(ngModelPipelineCheckValue);

            element.on('input', inputCheckValue);

            if (!isReadonly) {
                element
                    .on('focus', function (ev) {
                        containerCtrl.setFocused(true);
                    })
                    .on('blur', function (ev) {
                        containerCtrl.setFocused(false);
                        inputCheckValue();
                    });
            }

            scope.$on('$destroy', function () {
                containerCtrl.setFocused(false);
                containerCtrl.setHasValue(false);
                containerCtrl.input = null;
            });
        }
    }
    inputTextareaDirective.$inject = ["$mdUtil", "$window", "$compile", "$animate"];

    function mdMaxlengthDirective($animate) {
        return {
            restrict: 'A',
            require: ['ngModel', '^mdInputContainer'],
            link: postLink
        };

        function postLink(scope, element, attr, ctrls) {
            var maxlength;
            var ngModelCtrl = ctrls[0];
            var containerCtrl = ctrls[1];
            var charCountEl = angular.element('<div class="md-char-counter">');

            // Stop model from trimming. This makes it so whitespace 
            // over the maxlength still counts as invalid.
            attr.$set('ngTrim', 'false');
            containerCtrl.element.append(charCountEl);

            ngModelCtrl.$formatters.push(renderCharCount);
            ngModelCtrl.$viewChangeListeners.push(renderCharCount);
            element.on('input keydown', function () {
                renderCharCount(); //make sure it's called with no args
            });

            scope.$watch(attr.mdMaxlength, function (value) {
                maxlength = value;
                if (angular.isNumber(value) && value > 0) {
                    if (!charCountEl.parent().length) {
                        $animate.enter(charCountEl, containerCtrl.element,
                            angular.element(containerCtrl.element[0].lastElementChild));
                    }
                    renderCharCount();
                } else {
                    $animate.leave(charCountEl);
                }
            });

            ngModelCtrl.$validators['md-maxlength'] = function (modelValue, viewValue) {
                if (!angular.isNumber(maxlength) || maxlength < 0) {
                    return true;
                }
                return (modelValue || element.val() || viewValue || '').length <= maxlength;
            };

            function renderCharCount(value) {
                charCountEl.text((element.val() || value || '').length + '/' + maxlength);
                return value;
            }
        }
    }
    mdMaxlengthDirective.$inject = ["$animate"];

    function placeholderDirective() {
        return {
            restrict: 'A',
            require: '^^?mdInputContainer',
            link: postLink
        };

        function postLink(scope, element, attr, inputContainer) {
            if (!inputContainer || element[0].hasAttribute('native-placeholder')) return;

            var placeholderText = attr.placeholder;
            element.removeAttr('placeholder');
            inputContainer.element.append('<div class="md-placeholder">' + placeholderText + '</div>');
        }
    }

})();
/*!
 * Angular Material Design
 * https://github.com/angular/material
 * @license MIT
 * v0.7.1
 */
(function () {
    'use strict';


    /**
     * @ngdoc module
     * @name material.components.radioButton
     * @description radioButton module!
     */
    angular.module('material.components.radioButton', [
            'material.core'
        ])
        .directive('mdRadioGroup', mdRadioGroupDirective)
        .directive('mdRadioButton', mdRadioButtonDirective);

    function mdRadioGroupDirective($mdUtil, $mdConstant) {
        RadioGroupController.prototype = createRadioGroupControllerProto();

        return {
            restrict: 'E',
            controller: ['$element', RadioGroupController],
            require: ['mdRadioGroup', '?ngModel'],
            link: {
                pre: linkRadioGroup
            }
        };

        function linkRadioGroup(scope, element, attr, ctrls) {
 
            var rgCtrl = ctrls[0];
            var ngModelCtrl = ctrls[1] || $mdUtil.fakeNgModel();

            function keydownListener(ev) {
                switch (ev.keyCode) {
                case $mdConstant.KEY_CODE.LEFT_ARROW:
                case $mdConstant.KEY_CODE.UP_ARROW:
                    ev.preventDefault();
                    rgCtrl.selectPrevious();
                    break;

                case $mdConstant.KEY_CODE.RIGHT_ARROW:
                case $mdConstant.KEY_CODE.DOWN_ARROW:
                    ev.preventDefault();
                    rgCtrl.selectNext();
                    break;

                case $mdConstant.KEY_CODE.ENTER:
                    var form = angular.element($mdUtil.getClosest(element[0], 'form'));
                    if (form.length > 0) {
                        form.triggerHandler('submit');
                    }
                    break;
                }
            }

            rgCtrl.init(ngModelCtrl);

            element.attr({
                    'role': 'radiogroup',
                    'tabIndex': element.attr('tabindex') || '0'
                })
                .on('keydown', keydownListener);

        }

        function RadioGroupController($element) {
            this._radioButtonRenderFns = [];
            this.$element = $element;
        }

        function createRadioGroupControllerProto() {
                return {
                    init: function (ngModelCtrl) {
                        this._ngModelCtrl = ngModelCtrl;
                        this._ngModelCtrl.$render = angular.bind(this, this.render);
                    },
                    add: function (rbRender) {
                        this._radioButtonRenderFns.push(rbRender);
                    },
                    remove: function (rbRender) {
                        var index = this._radioButtonRenderFns.indexOf(rbRender);
                        if (index !== -1) {
                            this._radioButtonRenderFns.splice(index, 1);
                        }
                    },
                    render: function () {
                        this._radioButtonRenderFns.forEach(function (rbRender) {
                            rbRender();
                        });
                    },
                    setViewValue: function (value, eventType) {
                        this._ngModelCtrl.$setViewValue(value, eventType);
                        // update the other radio buttons as well
                        this.render();
                    },
                    getViewValue: function () {
                        return this._ngModelCtrl.$viewValue;
                    },
                    selectNext: function () {
                        return changeSelectedButton(this.$element, 1);
                    },
                    selectPrevious: function () {
                        return changeSelectedButton(this.$element, -1);
                    },
                    setActiveDescendant: function (radioId) {
                        this.$element.attr('aria-activedescendant', radioId);
                    }
                };
            }
            /**
             * Change the radio group's selected button by a given increment.
             * If no button is selected, select the first button.
             */
        function changeSelectedButton(parent, increment) {
            // Coerce all child radio buttons into an array, then wrap then in an iterator
            var buttons = $mdUtil.iterator(
                Array.prototype.slice.call(parent[0].querySelectorAll('md-radio-button')),
                true
            );

            if (buttons.count()) {
                var validate = function (button) {
                    // If disabled, then NOT valid
                    return !angular.element(button).attr("disabled");
                };
                var selected = parent[0].querySelector('md-radio-button.md-checked');
                var target = buttons[increment < 0 ? 'previous' : 'next'](selected, validate) || buttons.first();
                // Activate radioButton's click listener (triggerHandler won't create a real click event)
                angular.element(target).triggerHandler('click');


            }
        }

    }
    mdRadioGroupDirective.$inject = ["$mdUtil", "$mdConstant"];


    function mdRadioButtonDirective($mdAria, $mdUtil) {

        var CHECKED_CSS = 'md-checked';

        return {
            restrict: 'E',
            require: '^mdRadioGroup',
            transclude: true,
            template: '<div class="md-container list-primary-tile">' +
                '<div class="avatar-small"><div><icon class="button-square" type="radio_button_checked"></icon>' +
                '<icon class="button-square" type="radio_button_unchecked"></icon></div>' +
                '</div></div>' +
                '<div ng-transclude class="md-label"></div>',
            link: link
        };

        function link(scope, element, attr, rgCtrl) {
            var lastChecked;
            configureAria(element, scope);

            rgCtrl.add(render);
            attr.$observe('value', render);

            element
                .on('click', listener)
                .on('$destroy', function () {
                    rgCtrl.remove(render);
                });

            function listener(ev) {
                if (element[0].hasAttribute('disabled')) return;

                scope.$apply(function () {
                    rgCtrl.setViewValue(attr.value, ev && ev.type);
                });
            }

            function render() {
                    var checked = (rgCtrl.getViewValue() == attr.value);
                    if (checked === lastChecked) {
                        return;
                    }
                    lastChecked = checked;
                    element.attr('aria-checked', checked);
                    if (checked) {
                        element.addClass(CHECKED_CSS);
                        rgCtrl.setActiveDescendant(element.attr('id'));
                    } else {
                        element.removeClass(CHECKED_CSS);
                    }
                }
                /**
                 * Inject ARIA-specific attributes appropriate for each radio button
                 */
            function configureAria(element, scope) {
                scope.ariaId = buildAriaID();

                element.attr({
                    'id': scope.ariaId,
                    'role': 'radio',
                    'aria-checked': 'false'
                });

                $mdAria.expectWithText(element, 'aria-label');

                /**
                 * Build a unique ID for each radio button that will be used with aria-activedescendant.
                 * Preserve existing ID if already specified.
                 * @returns {*|string}
                 */
                function buildAriaID() {
                    return attr.id || ('radio' + "_" + $mdUtil.nextUid());
                }
            }
        }
    }
    mdRadioButtonDirective.$inject = ["$mdAria", "$mdUtil"];

})();
(function () {
    'use strict';

    angular.module('material.components.sidenav', [
            'material.core'
        ])
        .factory('$mdSidenav', SidenavService)
        .directive('mdSidenav', SidenavDirective)
        .controller('$mdSidenavController', SidenavController)
        .run(ng(function (helpers, $mdSidenav, $timeout, $q) {
            if (!helpers.sideNav) {
                helpers.sideNav = {};
            }
            helpers.sideNav.setup = function (menu, id, notRipplable) {
                if (!notRipplable) {
                    notRipplable = [];
                }
                id = id + _.uniqueId();
                menu.id = id;
                menu.notRipplable = notRipplable;
                menu.toggling = false;
                menu.close = function () {
                    return menu.toggle(undefined, 'close');
                };
                menu.open = function () {
                    return menu.toggle(undefined, 'open');
                };
                menu.toggle = function ($event, dowhat) {
                    var it = $mdSidenav(menu.id),
                        check = false,
                        defer = $q.defer(),
                        promise = defer.promise,
                        target;
                    if (menu.toggling) {
                        defer.resolve();
                        return promise;
                    }
                    if ($event && $event.target) {
                        target = $($event.target);
                        angular.forEach(menu.notRipplable, function (skip) {
                            if (target.is(skip) || target.parent().is(skip)) {
                                check = true;
                            }
                        });
                        if (check) {
                            defer.resolve();
                            return promise;
                        }
                    }
                    menu.toggling = true;
                    $timeout(function () {
                        it[dowhat || (it.isOpen() ? 'close' : 'open')]().then(function () {
                            menu.toggling = false;
                            defer.resolve();
                        });
                    });

                    return promise;
                };
            };
        }));

    function SidenavService($mdComponentRegistry, $q) {
        return function (handle) {
            var errorMsg = "SideNav '" + handle + "' is not available!";

            // Lookup the controller instance for the specified sidNav instance
            var instance = $mdComponentRegistry.get(handle);
            if (!instance) {
                $mdComponentRegistry.notFoundError(handle);
            }

            return {
                isOpen: function () {
                    return instance && instance.isOpen();
                },
                isLockedOpen: function () {
                    return instance && instance.isLockedOpen();
                },
                toggle: function () {
                    return instance ? instance.toggle() : $q.reject(errorMsg);
                },
                open: function () {
                    return instance ? instance.open() : $q.reject(errorMsg);
                },
                close: function () {
                    return instance ? instance.close() : $q.reject(errorMsg);
                }
            };
        };
    }
    SidenavService.$inject = ["$mdComponentRegistry", "$q"];

    function SidenavDirective($timeout, $animate, $parse, $mdMedia, $mdConstant, $compile, $q, $document, mdContextualMonitor) {
        return {
            restrict: 'E',
            scope: {
                isOpen: '=?mdIsOpen',
                componentID: '=?mdComponentId',
                stateChanged: '=?mdStateChanged'
            },
            controller: '$mdSidenavController',
            compile: function (element) {
                element.addClass('md-closed slide drawer out invisible');
                element.attr('tabIndex', '-1');
                return postLink;
            }
        };

        /**
         * Directive Post Link function...
         */
        function postLink(scope, element, attr, sidenavCtrl) {
            var triggeringElement = null;
            var promise = $q.when(true);
            var working = false;
            var nothing = !scope.isOpen;

            var isLockedOpenParsed = $parse(attr.mdIsLockedOpen);
            var isLocked = function () {
                return isLockedOpenParsed(scope.$parent, {
                    $media: $mdMedia
                });
            };
            var backdrop = $compile(
                '<md-backdrop class="md-sidenav-backdrop md-opaque fade">'
            )(scope);

            element.on('$destroy', sidenavCtrl.destroy);

            var initialWidth = element.css('width');
            var resize = function () {
                var tolerate = $(window).width() - 56;
                if (tolerate > initialWidth) {
                    element.css({
                        width: '',
                        'min-width': ''
                    });
                    return;
                }
                if (element.width() > tolerate) {
                    element.css({
                        width: tolerate,
                        'min-width': tolerate
                    });
                }
            };

            resize();

            resize = _.throttle(resize, 100);

            $(window).bind('resize', resize);

            scope.$watch(isLocked, updateIsLocked);
            scope.$watch('isOpen', updateIsOpen);
            scope.$on('$destroy', function () {
                $(window).off('resize', resize);
            });


            // Publish special accessor for the Controller instance
            sidenavCtrl.$toggleOpen = toggleOpen;

            /**
             * Toggle the DOM classes to indicate `locked`
             * @param isLocked
             */
            function updateIsLocked(isLocked, oldValue) {
                scope.isLockedOpen = isLocked;
                if (isLocked === oldValue) {
                    element.toggleClass('md-locked-open', !!isLocked);
                } else {
                    $animate[isLocked ? 'addClass' : 'removeClass'](element, 'md-locked-open');
                }
                backdrop.toggleClass('md-locked-open', !!isLocked);
            }

            /**
             * Toggle the SideNav view and attach/detach listeners
             * @param isOpen
             */
            function updateIsOpen(isOpen) {
                if (nothing) {
                    nothing = false;
                    return;
                }
                var parent = element.parent(),
                    promises = [];
                backdrop[isOpen ? 'on' : 'off']('click', function (ev) {
                    var that = this;
                    $timeout(function () {
                        close.apply(that, ev);
                    });
                });
                mdContextualMonitor[isOpen ? 'queue' : 'dequeue'](onKeyDown);
                if (isOpen) {
                    // Capture upon opening..
                    triggeringElement = $document[0].activeElement;
                }
                element.before(backdrop);
                var complete = function () {
                        // If we opened, and haven't closed again before the animation finished
                        if (scope.isOpen) {
                            element.focus();
                        }
                        working = false;
                        if (scope.stateChanged) {
                            scope.stateChanged(scope.isOpen);
                        }
                    },
                    backdropComplete = function () {
                        // If we opened, and haven't closed again before the animation finished
                        if (!scope.isOpen) {
                            backdrop.remove();
                        }
                    };
                if (isOpen) {
                    element.removeClass('invisible out');
                    backdrop.removeClass('out');
                    promises.push($animate.addClass(backdrop, 'in').then(backdropComplete));
                    promises.push($animate.addClass(element, 'in').then(complete));
                } else {
                    element.removeClass('in');
                    backdrop.removeClass('in');
                    promises.push($animate.addClass(backdrop, 'out').then(backdropComplete));
                    promises.push($animate.addClass(element, 'out').then(complete));
                }
                promise = $q.all(promises);
                return promise;
            }

            /**
             * Toggle the sideNav view and publish a promise to be resolved when
             * the view animation finishes.
             *
             * @param isOpen
             * @returns {*}
             */
            function toggleOpen(isOpen) {
                if (scope.isOpen == isOpen || working) {

                    return $q.when(true);

                } else {
                    working = true;
                    var deferred = $q.defer();

                    // Toggle value to force an async `updateIsOpen()` to run
                    scope.isOpen = isOpen;

                    $timeout(function () {

                        // When the current `updateIsOpen()` animation finishes
                        promise.then(function (result) {

                            if (!scope.isOpen) {
                                // reset focus to originating element (if available) upon close
                                triggeringElement && triggeringElement.focus();
                                triggeringElement = null;
                            }

                            if (isOpen) {
                                resize();
                            }

                            deferred.resolve(result);
                        });

                    }, 0, false);

                    return deferred.promise;
                }
            }

            /**
             * Auto-close sideNav when the `escape` key is pressed.
             * @param evt
             */
            function onKeyDown(ev) {
                $timeout(function () {
                    close(ev);
                });
                return true;
            }

            /**
             * With backdrop `clicks` or `escape` key-press, immediately
             * apply the CSS close transition... Then notify the controller
             * to close() and perform its own actions.
             */
            function close(ev) {
                if (ev) {
                    ev.preventDefault();
                    ev.stopPropagation();
                }
                return sidenavCtrl.close();
            }

        }
    }
    SidenavDirective.$inject = ["$timeout", "$animate", "$parse", "$mdMedia", "$mdConstant", "$compile", "$q", "$document", "mdContextualMonitor"];

    /*
     * @private
     * @ngdoc controller
     * @name SidenavController
     * @module material.components.sidenav
     *
     */
    function SidenavController($scope, $element, $attrs, $mdComponentRegistry, $q, $parse) {

        var self = this;

        // Use Default internal method until overridden by directive postLink

        self.$toggleOpen = function () {
            return $q.when($scope.isOpen);
        };
        self.isOpen = function () {
            return !!$scope.isOpen;
        };
        self.isLockedOpen = function () {
            return !!$scope.isLockedOpen;
        };
        self.open = function () {
            return self.$toggleOpen(true);
        };
        self.close = function () {
            return self.$toggleOpen(false);
        };
        self.toggle = function () {
            return self.$toggleOpen(!$scope.isOpen);
        };
        self.destroy = $mdComponentRegistry.register(self, $scope.componentID || $attrs.mdComponentId);
    }
    SidenavController.$inject = ["$scope", "$element", "$attrs", "$mdComponentRegistry", "$q", "$parse"];

}());
(function () {
    'use strict';

    angular.module('material.components.simpledialog', ['material.core'])
        .factory('mdContextualMonitor', mdContextualMonitor)
        .directive('simpleDialog', SimpleDialogDirective)
        .provider('$simpleDialog', SimpleDialogProvider);

    function mdContextualMonitor($rootElement, $mdConstant) {
        var callbacks = [],
            bound = false,
            id = 1,
            generateNextID = function () {
                id += 1;
                return id;
            },
            emptyHashery = function () {
                if (!callbacks.length && window.location.hash.length) {
                    window.location.hash = '';
                    id = 1;
                }
            },
            executeFirstInQueue = function (e) {
                var next = callbacks.pop(),
                    execute = (next && next(e));
                if (!execute && next) {
                    callbacks.push(next);
                }
                emptyHashery();
                return execute;
            };
        return {
            dequeue: function (cb) {
                var index = callbacks.indexOf(cb);
                if (index !== -1) {
                    callbacks.splice(index, 1);
                }
                emptyHashery();
            },
            queue: function (cb) {
                var hashPrefix = 'context-monitor-',
                    lastHash = window.location.hash,
                    nextId = generateNextID();
                if (!bound) {
                    $rootElement.on('keyup', function (e) {
                        if (e.keyCode !== $mdConstant.KEY_CODE.ESCAPE) {
                            return;
                        }
                        if (!executeFirstInQueue(e)) {
                            e.preventDefault();
                        }
                    });
                    $(window).bind('hashchange', function (e) {
                        var newHash = window.location.hash,
                            isBack,
                            newHashId = parseInt(newHash.substr(hashPrefix.length + 1), 10),
                            oldHashId = parseInt(lastHash.substr(hashPrefix.length + 1), 10);
                        // Do something
                        if (isNaN(newHashId) || (!isNaN(oldHashId) && (newHashId < oldHashId))) {
                            isBack = true;
                        }
                        //At the end of the func:
                        lastHash = newHash;
                        if (isBack) {
                            if (!executeFirstInQueue()) {
                                e.preventDefault();
                            }
                        }
                    });

                    bound = true;
                }
                window.location.hash = hashPrefix + nextId;
                callbacks.push(cb);
            }
        };
    }
    mdContextualMonitor.$inject = ["$rootElement", "$mdConstant"];


    function SimpleDialogDirective($$rAF) {
        return {
            restrict: 'E'
        };
    }
    SimpleDialogDirective.$inject = ["$$rAF"];

    function SimpleDialogProvider($$interimElementProvider) {

        var alertDialogMethods = ['title', 'content', 'ariaLabel', 'ok'];

        dialogDefaultOptions.$inject = ["$timeout", "$rootElement", "$compile", "$animate", "$mdAria", "$document", "$mdUtil", "$mdConstant", "$$rAF", "$q", "$simpleDialog", "mdContextualMonitor"];
        return $$interimElementProvider('$simpleDialog')
            .setDefaults({
                methods: ['disableParentScroll', 'hasBackdrop', 'clickOutsideToClose', 'popFrom'],
                options: dialogDefaultOptions
            });


        /* @ngInject */
        function dialogDefaultOptions($timeout, $rootElement, $compile, $animate, $mdAria, $document,
            $mdUtil, $mdConstant, $$rAF, $q, $simpleDialog, mdContextualMonitor) {
            return {
                hasBackdrop: true,
                isolateScope: true,
                onShow: onShow,
                onRemove: onRemove,
                clickOutsideToClose: true,
                popFrom: null,
                disableParentScroll: true,
                transformTemplate: function (template) {
                    return '<div class="simple-dialog-container">' + template + '</div>';
                }
            };

            function discoverDirective(options) {
                return 'simple-dialog';
            }

            function discoverContainerClass(container, options) {}

            // On show method for dialogs
            function onShow(scope, element, options) {
                // Incase the user provides a raw dom element, always wrap it in jqLite
                options.parent = angular.element(options.parent);

                options.popInTarget = angular.element(options.popFrom);
                var closeButton = findCloseButton(),
                    directive = discoverDirective(options),
                    dialogEl = element.find(directive);

                configureAria(dialogEl);
                options.disableScrollInfo = [];
                if (!options.disableScroll) {
                    options.disableScroll = [];
                }
                if (options.disableParentScroll) {
                    options.disableScroll.push(options.parent);
                }
                angular.forEach(options.disableScroll, function (el) {
                    options.disableScrollInfo.push({
                        old: {
                            'overflow-y': el.css('overflow-y'),
                            'overflow-x': el.css('overflow-x')
                        },
                        element: el
                    });
                    el.css('overflow', 'hidden');
                    el.css('overflow-wrap', el.css('overflow-wrap') === 'normal' ? 'break-word' : 'normal');
                });

                if (options.hasBackdrop) {
                    options.backdrop = angular.element('<md-backdrop class="simple-dialog-backdrop" style="z-index: ' + options.zIndex + '">');
                    $animate.enter(options.backdrop, options.parent);
                }

                dialogEl.css('z-index', options.zIndex + 1);

                return dialogPopIn(element, options)
                    .then(function () {
                        options.rootElementKeyupCallback = function () {
                            if (options.stack.indexOf(options.interimElement) === 0) {
                                $timeout(function () {
                                    $simpleDialog.cancel('esc', options.interimElement);
                                });
                            }
                            return true;
                        };
                        mdContextualMonitor.queue(options.rootElementKeyupCallback);
                        if (options.clickOutsideToClose) {
                            options.dialogClickOutsideCallback = function (e) {
                                // Only close if we click the flex container outside the backdrop
                                if (e.target === options.backdrop[0]) {
                                    $timeout($simpleDialog.cancel);
                                }
                            };
                            options.backdrop.on('click', options.dialogClickOutsideCallback);
                        }
                        closeButton.focus();

                    });


                function findCloseButton() {
                    //If no element with class dialog-close, try to find the last
                    //button child in md-actions and assume it is a close button
                    var closeButton = element[0].querySelector('.dialog-close');
                    if (!closeButton) {
                        var actionButtons = element[0].querySelectorAll('.md-actions button');
                        closeButton = actionButtons[actionButtons.length - 1];
                    }
                    return angular.element(closeButton);
                }

            }

            // On remove function for all dialogs
            function onRemove(scope, element, options) {
                if (options.clickOutsideToClose && options.backdrop) {
                    options.backdrop.off('click', options.dialogClickOutsideCallback);
                }
                if (options.backdrop) {
                    $animate.leave(options.backdrop);
                }
                angular.forEach(options.disableScrollInfo, function (info) {
                    info.element.css(info.old);
                    info.element.css('overflow-wrap', info.element.css('overflow-wrap') === 'normal' ? 'break-word' : 'normal');
                });
                options.disableScrollInfo = [];
                $document[0].removeEventListener('scroll', options.captureScroll, true);
                mdContextualMonitor.dequeue(options.rootElementKeyupCallback);
                return dialogPopOut(element, options).then(function () {
                    options.scope.$destroy();
                    element.remove();
                    options.popInTarget && options.popInTarget.focus();
                });

            }

            /**
             * Inject ARIA-specific attributes appropriate for Dialogs
             */
            function configureAria(element) {
                element.attr({
                    'role': 'dialog'
                });

                var dialogContent = element.find('md-content');
                if (dialogContent.length === 0) {
                    dialogContent = element;
                }
                $mdAria.expectAsync(element, 'aria-label', function () {
                    var words = dialogContent.text().split(/\s+/);
                    if (words.length > 3) {
                        words = words.slice(0, 3).concat('...');
                    }
                    return words.join(' ');
                });
            }

            function dialogPopIn(container, options) {
                discoverContainerClass(container, options);
                var dialogEl = container.find(discoverDirective(options)),
                    parentElement = options.parent,
                    promise,
                    nextPromise,
                    defer = $q.defer();
                parentElement.append(container);
                promise = defer.promise;
                nextPromise = promise.then(function () {
                    var maybeDefer = $q.defer(),
                        maybePromise = maybeDefer.promise,
                        maybePromiseOnBefore;
                    if (options.onBeforeShow) {
                        maybePromiseOnBefore = options.onBeforeShow(dialogEl, options);
                        if (maybePromiseOnBefore && maybePromiseOnBefore.then) {
                            return maybePromiseOnBefore;
                        }
                    }
                    maybeDefer.resolve();
                    return maybePromise;
                });
                defer.resolve();
                return nextPromise;
            }

            function dialogTransitionEnd(dialogEl) {
                var deferred = $q.defer();

                function finished(ev) {
                    //Make sure this transitionend didn't bubble up from a child
                    if (ev.target === dialogEl[0]) {
                        dialogEl.off($mdConstant.CSS.TRANSITIONEND, finished);
                        deferred.resolve();
                    }
                }
                dialogEl.on($mdConstant.CSS.TRANSITIONEND, finished);
                return deferred.promise;
            }

            function dialogPopOut(container, options) {
                discoverContainerClass(container, options);
                var dialogEl = container.find(discoverDirective(options)),
                    promise,
                    defer;
                if (options.onBeforeHide) {
                    options.onBeforeHide(dialogEl, options);
                }
                if (dialogEl.hasClass('fade')) {
                    defer = $q.defer();
                    dialogEl.oneAnimationEnd(function () {
                        defer.resolve();
                    });
                    dialogEl.removeClass('in').addClass('out');
                    promise = defer.promise;
                } else {
                    promise = dialogTransitionEnd(dialogEl);
                    promise.then(function () {
                        if (options.onAfterHide) {
                            options.onAfterHide(dialogEl, options);
                        }
                    });
                    dialogEl.removeClass('transition-in').addClass('transition-out');
                    setTimeout(function () {
                        dialogEl.addClass('opacity-out');
                    }, 50);
                }
                return promise;
            }

        }
    }
    SimpleDialogProvider.$inject = ["$$interimElementProvider"];

})();
(function () {
    'use strict';
    var module = angular.module('material.components.swipe', []);

    ['SwipeLeft', 'SwipeRight'].forEach(function (name) {
        var directiveName = 'md' + name;
        var eventName = '$md.' + name.toLowerCase();

        module.directive(directiveName, /*@ngInject*/ ["$parse", function ($parse) {
            return {
                restrict: 'A',
                link: postLink
            };

            function postLink(scope, element, attr) {
                var fn = $parse(attr[directiveName]);

                element.on(eventName, function (ev) {
                    scope.$apply(function () {
                        fn(scope, {
                            $event: ev
                        });
                    });
                });

            }
        }]);
    });

})();
(function () {
    'use strict';

    angular.module('material.components.textField', [
            'material.core'
        ])
        .directive('mdInputGroup', mdInputGroupDirective)
        .directive('mdInput', mdInputDirective)
        .directive('mdTextFloat', mdTextFloatDirective);


    function mdTextFloatDirective($mdUtil, $parse, $log) {
        return {
            restrict: 'E',
            replace: true,
            scope: {
                fid: '@?mdFid',
                label: '@?',
                value: '=ngModel'
            },
            compile: function (element, attr) {

                $log.warn('<md-text-float> is deprecated. Please use `<md-input-container>` and `<input>`.' +
                    'More information at http://material.angularjs.org/#/api/material.components.input/directive/mdInputContainer');

                if (angular.isUndefined(attr.mdFid)) {
                    attr.mdFid = $mdUtil.nextUid();
                }

                return {
                    pre: function (scope, element, attrs) {
                        var disabledParsed = $parse(attrs.ngDisabled);
                        scope.isDisabled = function () {
                            return disabledParsed(scope.$parent);
                        };

                        scope.inputType = attrs.type || "text";
                    }
                };
            },
            template: '<md-input-group tabindex="-1">' +
                ' <label for="{{fid}}" >{{label}}</label>' +
                ' <md-input id="{{fid}}" ng-disabled="isDisabled()" ng-model="value" type="{{inputType}}"></md-input>' +
                '</md-input-group>'
        };
    }
    mdTextFloatDirective.$inject = ["$mdUtil", "$parse", "$log"];

    function mdInputGroupDirective($log) {
        return {
            restrict: 'CE',
            controller: ['$element', function ($element) {

                $log.warn('<md-input-group> is deprecated. Please use `<md-input-container>` and `<input>`.' +
                    'More information at http://material.angularjs.org/#/api/material.components.input/directive/mdInputContainer');
                this.setFocused = function (isFocused) {
                    $element.toggleClass('md-input-focused', !!isFocused);
                };
                this.setHasValue = function (hasValue) {
                    $element.toggleClass('md-input-has-value', hasValue);
                };
            }]
        };

    }
    mdInputGroupDirective.$inject = ["$log"];

    function mdInputDirective($mdUtil, $log) {
        return {
            restrict: 'E',
            replace: true,
            template: '<input >',
            require: ['^?mdInputGroup', '?ngModel'],
            link: function (scope, element, attr, ctrls) {
                if (!ctrls[0]) return;

                $log.warn('<md-input> is deprecated. Please use `<md-input-container>` and `<input>`.' +
                    'More information at http://material.angularjs.org/#/api/material.components.input/directive/mdInputContainer');

                var inputGroupCtrl = ctrls[0];
                var ngModelCtrl = ctrls[1];

                scope.$watch(scope.isDisabled, function (isDisabled) {
                    element.attr('aria-disabled', !!isDisabled);
                    element.attr('tabindex', !!isDisabled);
                });
                element.attr('type', attr.type || element.parent().attr('type') || "text");

                // When the input value changes, check if it "has" a value, and
                // set the appropriate class on the input group
                if (ngModelCtrl) {
                    //Add a $formatter so we don't use up the render function
                    ngModelCtrl.$formatters.push(function (value) {
                        inputGroupCtrl.setHasValue(isNotEmpty(value));
                        return value;
                    });
                }

                element
                    .on('input', function () {
                        inputGroupCtrl.setHasValue(isNotEmpty());
                    })
                    .on('focus', function (e) {
                        // When the input focuses, add the focused class to the group
                        inputGroupCtrl.setFocused(true);
                    })
                    .on('blur', function (e) {
                        // When the input blurs, remove the focused class from the group
                        inputGroupCtrl.setFocused(false);
                        inputGroupCtrl.setHasValue(isNotEmpty());
                    });

                scope.$on('$destroy', function () {
                    inputGroupCtrl.setFocused(false);
                    inputGroupCtrl.setHasValue(false);
                });


                function isNotEmpty(value) {
                    value = angular.isUndefined(value) ? element.val() : value;
                    return (angular.isDefined(value) && (value !== null) &&
                        (value.toString().trim() !== ""));
                }
            }
        };
    }
    mdInputDirective.$inject = ["$mdUtil", "$log"];

})();
(function () {
    'use strict';
    angular.module('app').factory('snackbar', ng(function (GLOBAL_CONFIG) {
        var snackbar = {
            show: $.noop,
            hide: $.noop,
            showK: function (key, config) {
                var gets = GLOBAL_CONFIG.snackbar.messages[key];
                if (angular.isUndefined(gets)) {
                    gets = key;
                }
                return snackbar.show($.extend({
                    message: gets
                }, config));
            }
        };
        if (GLOBAL_CONFIG.debug) {
            window._snackbar = snackbar;
        }
        return snackbar;
    })).directive('qsnackbar', ng(function (snackbar) {
        return {
            link: function (scope, element) {
                var kill = function () {
                    snackbar.hide();
                };
                element.on('click', kill);
                scope.$on('$destroy', function () {
                    element.off('click', kill);
                });
            }
        };
    })).directive('ngClick', ng(function (snackbar) {
        return {
            restrict: 'A',
            priority: 100,
            link: function (scope, element, attr) {
                var kill = function () {
                    if (!snackbar.animating) {
                        snackbar.hide();
                    }
                };
                element.on('click', kill);
                scope.$on('$destroy', function () {
                    element.off('click', kill);
                });
            }
        };
    })).directive('snackbar', ng(function (snackbar, $timeout, $animate, $q) {
        return {
            scope: true,
            require: 'snackbar',
            templateUrl: 'core/snackbar/view.html',
            controller: ng(function ($scope) {
                var digest = function () {
                        if (!$scope.$$phase) {
                            $scope.$digest();
                        }
                    },
                    timer;
                $scope.message = '';
                $scope.size = 1;
                $scope.element = null;

                snackbar.animating = false;
                snackbar.hide = function () {
                    var defer = $q.defer();
                    $scope.element.removeClass('in');
                    if (!$scope.element.hasClass('out')) {
                        $animate.addClass($scope.element, 'out').then(function () {
                            defer.resolve();
                        });
                        digest();
                    } else {
                        defer.resolve();
                    }
                    return defer.promise;
                };
                snackbar.show = function (config) {
                    if (!angular.isObject(config)) {
                        config = {
                            message: config
                        };
                    }
                    $scope.message = config.message;
                    if (!config.hideAfter) {
                        config.hideAfter = (($scope.message.length / 16) * 1000) + 500;
                    }
                    $scope.size = config.size;
                    $scope.calculateSize = function () {
                        if (!$scope.size) {
                            return $scope.element.find('.brief').height() > 16 ? 2 : 1;
                        }
                        return $scope.size;
                    };
                    digest();
                    snackbar.animating = true;
                    return snackbar.hide().then(function () {
                        $animate.removeClass($scope.element, 'out');
                        return $animate.addClass($scope.element, 'in').then(function () {
                            snackbar.animating = false;
                            if (config.hideAfter) {
                                if (timer) {
                                    clearTimeout(timer);
                                }
                                timer = setTimeout(function () {
                                    snackbar.hide();
                                }, config.hideAfter);
                            }
                        });
                    });
                };
            }),
            link: function (scope, element, snackbarCtrl) {
                scope.element = element.find('.snackbar');
            }
        };
    }));
}());
(function () {
    'use strict';

    angular.module('material.components.toolbar', [
            'material.core',
            'material.components.content'
        ])
        .directive('mdToolbar', mdToolbarDirective).run(ng(function (helpers, GLOBAL_CONFIG) {
            if (angular.isUndefined(helpers.toolbar)) {
                helpers.toolbar = {};
            }
            $.extend(helpers.toolbar, {
                title: function (keys, separator) {
                    var splits,
                        gets = GLOBAL_CONFIG.toolbar.titles,
                        complete = [],
                        initial = gets[keys];
                    if (!separator) {
                        separator = ' / ';
                    }
                    if (angular.isDefined(initial)) {
                        return angular.isArray(initial) ? initial.join(separator) : initial;
                    }
                    if (!angular.isArray(keys)) {
                        splits = keys.split('.');
                    } else {
                        splits = keys;
                    }
                    angular.forEach(splits, function (key, i) {
                        var get = gets[key];
                        if (get === false) {
                            return;
                        }
                        complete.push(angular.isDefined(get) ? get : key);
                    });
                    if (!complete.length) {
                        return keys;
                    }
                    return complete.join(separator);
                },
                buildTitle: function (callbacks) {
                    var paths = [];
                    angular.forEach(callbacks, function (cb) {
                        paths.push(cb());
                    });
                    return helpers.toolbar.title(paths.join('.'));
                },
                makeTitle: function (word) {
                    return _.string.capitalize(_.string.camelize(word));
                }
            });
        }));

    function mdToolbarDirective($$rAF, $mdConstant, $mdUtil) {

        return {
            restrict: 'E',
            controller: angular.noop,
            link: function (scope, element, attr) {

                if (angular.isDefined(attr.mdScrollShrink)) {
                    setupScrollShrink();
                }

                function setupScrollShrink() {
                    // Current "y" position of scroll
                    var y = 0;
                    // Store the last scroll top position
                    var prevScrollTop = 0;

                    var shrinkSpeedFactor = attr.mdShrinkSpeedFactor || 0.5;

                    var toolbarHeight;
                    var contentElement;

                    var debouncedContentScroll = $$rAF.throttle(onContentScroll);
                    var debouncedUpdateHeight = $mdUtil.debounce(updateToolbarHeight, 5 * 1000);

                    // Wait for $mdContentLoaded event from mdContent directive.
                    // If the mdContent element is a sibling of our toolbar, hook it up
                    // to scroll events.
                    scope.$on('$mdContentLoaded', onMdContentLoad);

                    function onMdContentLoad($event, newContentEl) {
                        // Toolbar and content must be siblings
                        if (element.parent()[0] === newContentEl.parent()[0]) {
                            // unhook old content event listener if exists
                            if (contentElement) {
                                contentElement.off('scroll', debouncedContentScroll);
                            }

                            newContentEl.on('scroll', debouncedContentScroll);
                            newContentEl.attr('scroll-shrink', 'true');

                            contentElement = newContentEl;
                            $$rAF(updateToolbarHeight);
                        }
                    }

                    function updateToolbarHeight() {
                        toolbarHeight = element.prop('offsetHeight');
                        // Add a negative margin-top the size of the toolbar to the content el.
                        // The content will start transformed down the toolbarHeight amount,
                        // so everything looks normal.
                        //
                        // As the user scrolls down, the content will be transformed up slowly
                        // to put the content underneath where the toolbar was.
                        contentElement.css(
                            'margin-top', (-toolbarHeight * shrinkSpeedFactor) + 'px'
                        );
                        onContentScroll();
                    }

                    function onContentScroll(e) {
                        var scrollTop = e ? e.target.scrollTop : prevScrollTop;

                        debouncedUpdateHeight();

                        y = Math.min(
                            toolbarHeight / shrinkSpeedFactor,
                            Math.max(0, y + scrollTop - prevScrollTop)
                        );

                        element.css(
                            $mdConstant.CSS.TRANSFORM,
                            'translate3d(0,' + (-y * shrinkSpeedFactor) + 'px,0)'
                        );
                        contentElement.css(
                            $mdConstant.CSS.TRANSFORM,
                            'translate3d(0,' + ((toolbarHeight - y) * shrinkSpeedFactor) + 'px,0)'
                        );

                        prevScrollTop = scrollTop;
                    }

                }

            }
        };

    }
    mdToolbarDirective.$inject = ["$$rAF", "$mdConstant", "$mdUtil"];
})();
(function () {
    'use strict';
    angular.module('app').directive('actionDropdownList', function () {
        return {
            templateUrl: 'core/action/dropdown_list.html',
            transclude: true,
            replace: true
        };
    }).directive('actionDropdown', ng(function ($simpleDialog, $$rAF, $mdConstant, underscoreTemplate, $timeout, $parse, $q, helpers) {
        return {
            replace: true,
            transclude: true,
            templateUrl: 'core/action/dropdown.html',
            scope: true,
            link: function (scope, element, attrs) {
                var dropdown = {},
                    template = scope.$eval(attrs.template);
                if (!template) {
                    return;
                }

                dropdown.opened = false;
                dropdown.open = function ($event) {
                    if (dropdown.opened) {
                        return;
                    }
                    dropdown.opened = true;
                    $timeout(function () {
                        dropdown.openSimpleDialog($event);
                    });
                };
                dropdown.openSimpleDialog = function ($event) {
                    $simpleDialog.show({
                        templateUrl: template,
                        popFrom: $event.target,
                        parent: element.parents(attrs.parent),
                        onBeforeHide: function (dialogEl, options) {
                            $(window).off('resize', options.resize);
                        },
                        onBeforeShow: function (dialogEl, options) {
                            var nextDefer = $q.defer(), nextPromise = nextDefer.promise, animateSelect = function () {
                                var target = element;
                                options.resize = function () {
                                    var targetOffset = target.offset(),
                                        parent = options.parent,
                                        paddingTop = parseInt(parent.css('padding-top'), 10) || 24,
                                        paddingBottom = parseInt(parent.css('padding-bottom'), 10) || 24,
                                        newTop = targetOffset.top,
                                        newLeft = (targetOffset.left - (dialogEl.width() - target.outerWidth())) - 12,
                                        height = parent.height() - (paddingBottom + paddingTop),
                                        maxLeft = parent.width() - dialogEl.width() - 16;
                                    newTop = targetOffset.top;
                                    if (newTop < 16) {
                                        newTop = 16;
                                    }
                                    if (newLeft < 16) {
                                        newLeft = 16;
                                    }
                                    if (newLeft > maxLeft) {
                                        newLeft = maxLeft;
                                    }
                                    if (!attrs.fixedPosition) {
                                        dialogEl.css({
                                            top: newTop,
                                            left: newLeft
                                        });
                                    } else if (attrs.fixedPosition === 'toolbar') {
                                        dialogEl.css({
                                            top: '8px',
                                            left: 'auto',
                                            right: '8px'
                                        });
                                    }
                                    if (dialogEl.height() > height) {
                                        dialogEl.height(height);
                                    }
                                };
                                options.resize();
                                $(window).on('resize', options.resize);

                                $$rAF(function () {
                                    dialogEl.addClass('fade in');
                                });

                                dialogEl.oneAnimationEnd(function () {
                                    element.addClass('opacity-in');
                                    nextDefer.resolve();
                                });

                                return nextPromise;

                            };

                            $$rAF(animateSelect);

                            dialogEl.on('click', dropdown.close);
                        },
                        controller: ng(function ($scope) {
                            $scope.parent = scope;
                            $scope.$on('$destroy', function () {
                                dropdown.opened = false;
                            });
                        })
                    });
                };
                dropdown.close = function () {
                    $simpleDialog.hide();
                };
                scope.dropdown = dropdown;
            }
        };
    })).directive('actionToolbar', function () {
        return {
            transclude: true,
            replace: true,
            scope: true,
            templateUrl: 'core/action/toolbar.html',
            link: function (scope, element, attrs) {
                scope.spec = scope.$eval(attrs.spec);
            }
        };
    });
}());
/**
 * @author Jason Dobry <jason.dobry@gmail.com>
 * @file angular-cache.js
 * @version 3.1.1 - Homepage <https://github.com/jmdobry/angular-cache>
 * @copyright (c) 2013-2014 Jason Dobry <http://www.pseudobry.com>
 * @license MIT <https://github.com/jmdobry/angular-cache/blob/master/LICENSE>
 *
 * @overview angular-cache is a very useful replacement for Angular's $cacheFactory.
 */
(function e(t, n, r) {
    function s(o, u) {
        if (!n[o]) {
            if (!t[o]) {
                var a = typeof require == "function" && require;
                if (!u && a) return a(o, !0);
                if (i) return i(o, !0);
                throw new Error("Cannot find module '" + o + "'")
            }
            var f = n[o] = {
                exports: {}
            };
            t[o][0].call(f.exports, function (e) {
                var n = t[o][1][e];
                return s(n ? n : e)
            }, f, f.exports, e, t, n, r)
        }
        return n[o].exports
    }
    var i = typeof require == "function" && require;
    for (var o = 0; o < r.length; o++) s(r[o]);
    return s
})({
    1: [function (require, module, exports) {
        /**
         * @method bubbleUp
         * @param {array} heap The heap.
         * @param {function} weightFunc The weight function.
         * @param {number} n The index of the element to bubble up.
         */
        function bubbleUp(heap, weightFunc, n) {
            var element = heap[n],
                weight = weightFunc(element);
            // When at 0, an element can not go up any further.
            while (n > 0) {
                // Compute the parent element's index, and fetch it.
                var parentN = Math.floor((n + 1) / 2) - 1,
                    parent = heap[parentN];
                // If the parent has a lesser weight, things are in order and we
                // are done.
                if (weight >= weightFunc(parent)) {
                    break;
                } else {
                    heap[parentN] = element;
                    heap[n] = parent;
                    n = parentN;
                }
            }
        }

        /**
         * @method bubbleDown
         * @param {array} heap The heap.
         * @param {function} weightFunc The weight function.
         * @param {number} n The index of the element to sink down.
         */
        function bubbleDown(heap, weightFunc, n) {
            var length = heap.length,
                node = heap[n],
                nodeWeight = weightFunc(node);

            while (true) {
                var child2N = (n + 1) * 2,
                    child1N = child2N - 1;
                var swap = null;
                if (child1N < length) {
                    var child1 = heap[child1N],
                        child1Weight = weightFunc(child1);
                    // If the score is less than our node's, we need to swap.
                    if (child1Weight < nodeWeight) {
                        swap = child1N;
                    }
                }
                // Do the same checks for the other child.
                if (child2N < length) {
                    var child2 = heap[child2N],
                        child2Weight = weightFunc(child2);
                    if (child2Weight < (swap === null ? nodeWeight : weightFunc(heap[child1N]))) {
                        swap = child2N;
                    }
                }

                if (swap === null) {
                    break;
                } else {
                    heap[n] = heap[swap];
                    heap[swap] = node;
                    n = swap;
                }
            }
        }

        /**
         * @class DSBinaryHeap
         * @desc DSBinaryHeap implementation of a priority queue.
         * @param {function} weightFunc Function that returns the value that should be used for node value comparison.
         * @example
         * angular.module('app').controller(function (DSBinaryHeap) {
         *      var bHeap = new DSBinaryHeap(function (x) {
         *          return x.value;
         *      });
         * );
         */
        function DSBinaryHeap(weightFunc) {
            if (weightFunc && !angular.isFunction(weightFunc)) {
                throw new Error('DSBinaryHeap(weightFunc): weightFunc: must be a function!');
            }
            weightFunc = weightFunc || function (x) {
                return x;
            };
            this.weightFunc = weightFunc;
            this.heap = [];
        }

        /**
         * @method DSBinaryHeap.push
         * @desc Push an element into the binary heap.
         * @param {*} node The element to push into the binary heap.
         */
        DSBinaryHeap.prototype.push = function (node) {
            this.heap.push(node);
            bubbleUp(this.heap, this.weightFunc, this.heap.length - 1);
        };

        /**
         * @method DSBinaryHeap.peek
         * @desc Return, but do not remove, the minimum element in the binary heap.
         * @returns {*}
         */
        DSBinaryHeap.prototype.peek = function () {
            return this.heap[0];
        };

        /**
         * @method DSBinaryHeap.pop
         * @desc Remove and return the minimum element in the binary heap.
         * @returns {*}
         */
        DSBinaryHeap.prototype.pop = function () {
            var front = this.heap[0],
                end = this.heap.pop();
            if (this.heap.length > 0) {
                this.heap[0] = end;
                bubbleDown(this.heap, this.weightFunc, 0);
            }
            return front;
        };

        /**
         * @method DSBinaryHeap.remove
         * @desc Remove the first node in the priority queue that satisfies angular.equals comparison with
         * the given node.
         * @param {*} node The node to remove.
         * @returns {*} The removed node.
         */
        DSBinaryHeap.prototype.remove = function (node) {
            var length = this.heap.length;
            for (var i = 0; i < length; i++) {
                if (angular.equals(this.heap[i], node)) {
                    var removed = this.heap[i],
                        end = this.heap.pop();
                    if (i !== length - 1) {
                        this.heap[i] = end;
                        bubbleUp(this.heap, this.weightFunc, i);
                        bubbleDown(this.heap, this.weightFunc, i);
                    }
                    return removed;
                }
            }
            return null;
        };

        /**
         * @method DSBinaryHeap.removeAll
         * @desc Remove all nodes from this DSBinaryHeap.
         */
        DSBinaryHeap.prototype.removeAll = function () {
            this.heap = [];
        };

        /**
         * @method DSBinaryHeap.size
         * @desc Return the size of the priority queue.
         * @returns {number} The size of the priority queue.
         */
        DSBinaryHeap.prototype.size = function () {
            return this.heap.length;
        };

        /**
         * @desc Provider for the DSBinaryHeap.
         */
        function DSBinaryHeapProvider() {
            this.$get = function () {
                return DSBinaryHeap;
            };
        }

        module.exports = {
            DSBinaryHeapProvider: DSBinaryHeapProvider,
            DSBinaryHeap: DSBinaryHeap
        };

    }, {}],
    2: [function (require, module, exports) {
        /**
         * @doc method
         * @id DSCache.methods:destroy
         * @name destroy
         * @description
         * Destroy this cache and all of its data.
         *
         * ## Signature:
         * ```js
         * DSCache#destroy()
         * ```
         *
         * ## Example:
         * ```js
         * var someCache = DSCacheFactory.get('someCache');
         *
         * someCache.destroy();
         *
         * DSCacheFactory.get('someCache'); // undefined
         * someCache.put('1', 'apple'); // Error
         * ```
         */
        module.exports = function destroy() {
            clearInterval(this.$$cacheFlushIntervalId);
            clearInterval(this.$$recycleFreqId);
            this.removeAll();
            if (this.$$storage) {
                this.$$storage.removeItem(this.$$prefix + '.keys');
                this.$$storage.removeItem(this.$$prefix);
            }
            this.$$storage = null;
            this.$$data = null;
            this.$$lruHeap = null;
            this.$$expiresHeap = null;
            this.$$prefix = null;
        };

    }, {}],
    3: [function (require, module, exports) {
        var utils = require('../utils');

        /**
         * @doc method
         * @id DSCache.methods:get
         * @name get
         * @description
         * Retrieve the item with the given key.
         *
         * ## Signature:
         * ```js
         * DSCache#get(key)
         * ```
         *
         * ## Examples:
         * ```js
         * var cache = DSCacheFactory('cache');
         *
         * cache.put('1', 'apple');
         *
         * cache.get('1'); // "apple"
         * cache.get('2'); // undefined
         * ```
         *
         * ```js
         *  var options = {
         *          deleteOnExpire: 'passive',
         *          maxAge: 1000
         *      },
         *      cache = DSCacheFactory('cache', options);
         *
         *  cache.put('1', 'apple');
         *
         *  cache.get('1'); // "apple"
         *
         *  setTimeout(function () {
         *      cache.get('1'); // undefined
         *  }, 1500);
         * ```
         *
         * ```js
         *  var options = {
         *          deleteOnExpire: 'passive',
         *          maxAge: 1000
         *      },
         *      cache = DSCacheFactory('cache', options);
         *
         *  cache.put('1', 'apple');
         *
         *  cache.get('1', {
         *      onExpire: function (key, value) {
         *          console.log(key, value);
         *      }
         *  }); // "apple"
         *
         *  setTimeout(function () {
         *      cache.get('1'); // undefined
         *                      // "1" "apple" (printed to console)
         *  }, 1500);
         * ```
         *
         * ```js
         *  var options = {
         *          deleteOnExpire: 'passive',
         *          maxAge: 1000,
         *          onExpire: function (key, value, done) {
         *              console.log('global hit');
         *              if (done) {
         *                  done(key, value);
         *              }
         *          }
         *      },
         *      cache = DSCacheFactory('cache', options);
         *
         *  cache.put('1', 'apple');
         *
         *  cache.get('1', {
         *      onExpire: function (key, value) {
         *          console.log(key, value);
         *      }
         *  }); // "apple"
         *
         *  setTimeout(function () {
         *      cache.get('1'); // undefined
         *                      // "global hit" (printed to console)
         *                      // "1" "apple" (printed to console)
         *  }, 1500);
         * ```
         *
         * @param {string} key The key of the item to retrieve.
         * @param {object=} options Optional configuration. Properties:
         *
         * - `{function=}` - `onExpire` - Callback to be used if in passive `deleteOnExpire` mode and the requested item has
         * expired. If a global `onExpire` callback exists for this cache, then it will be called with three arguments: `key`,
         * `value`, and `done`, where `done` is the `onExpire` callback passed into the call to `DSCache#get(key[, options])`.
         * (See the last example above.)
         *
         * @returns {*} The item with the given key.
         */
        module.exports = function get(key, options) {
            var _this = this;

            if (angular.isArray(key)) {
                var keys = key,
                    values = [];

                angular.forEach(keys, function (key) {
                    var value = _this.get(key, options);
                    if (value !== null && value !== undefined) {
                        values.push(value);
                    }
                });

                return values;
            } else {
                key = utils.stringifyNumber(key);

                if (this.$$disabled) {
                    return;
                }
            }

            options = options || {};
            if (!angular.isString(key)) {
                throw angular.$$minErr('ng')('areq', 'Expected key to be a string! Found: {0}.', typeof key);
            } else if (options && !angular.isObject(options)) {
                throw angular.$$minErr('ng')('areq', 'Expected options to be an object! Found: {0}.', typeof options);
            } else if (options.onExpire && !angular.isFunction(options.onExpire)) {
                throw angular.$$minErr('ng')('areq', 'Expected options.onExpire to be a function! Found: {0}.', typeof options.onExpire);
            }

            var item;

            if (this.$$storage) {
                var itemJson = this.$$storage.getItem(this.$$prefix + '.data.' + key);

                if (itemJson) {
                    item = angular.fromJson(itemJson);
                } else {
                    return;
                }
            } else {
                if (!(key in this.$$data)) {
                    return;
                }

                item = this.$$data[key];
            }

            var value = item.value,
                now = new Date().getTime();

            if (this.$$storage) {
                this.$$lruHeap.remove({
                    key: key,
                    accessed: item.accessed
                });
                item.accessed = now;
                this.$$lruHeap.push({
                    key: key,
                    accessed: now
                });
            } else {
                this.$$lruHeap.remove(item);
                item.accessed = now;
                this.$$lruHeap.push(item);
            }

            if (this.$$deleteOnExpire === 'passive' && 'expires' in item && item.expires < now) {
                this.remove(key);

                if (this.$$onExpire) {
                    this.$$onExpire(key, item.value, options.onExpire);
                } else if (options.onExpire) {
                    options.onExpire(key, item.value);
                }
                value = undefined;
            } else if (this.$$storage) {
                this.$$storage.setItem(this.$$prefix + '.data.' + key, (item));
            }

            return value;
        };

    }, {
        "../utils": 21
    }],
    4: [function (require, module, exports) {
        var defaults = require('../defaults'),
            DSBinaryHeap = require('../DSBinaryHeap').DSBinaryHeap;

        /*!
         * Configure the cache to use webStorage.
         */
        function _setStorageMode(storageMode, storageImpl) {
            if (!angular.isString(storageMode)) {
                throw angular.$$minErr('ng')('areq', 'Expected storageMode to be a string! Found: {0}.', typeof storageMode);
            } else if (storageMode !== 'memory' && storageMode !== 'localStorage' && storageMode !== 'sessionStorage') {
                throw angular.$$minErr('ng')('areq', 'Expected storageMode to be "memory", "localStorage" or "sessionStorage"! Found: {0}.', storageMode);
            }

            this.$$storageMode = storageMode;

            if (storageImpl) {
                if (!angular.isObject(storageImpl)) {
                    throw angular.$$minErr('ng')('areq', 'Expected storageImpl to be an object! Found: {0}.', typeof storageImpl);
                } else if (!('setItem' in storageImpl) || typeof storageImpl.setItem !== 'function') {
                    throw angular.$$minErr('ng')('areq', 'Expected storageImpl to implement "setItem(key, value)"! Found: {0}.', typeof storageImpl.setItem);
                } else if (!('getItem' in storageImpl) || typeof storageImpl.getItem !== 'function') {
                    throw angular.$$minErr('ng')('areq', 'Expected storageImpl to implement "getItem(key)"! Found: {0}.', typeof storageImpl.getItem);
                } else if (!('removeItem' in storageImpl) || typeof storageImpl.removeItem !== 'function') {
                    throw angular.$$minErr('ng')('areq', 'Expected storageImpl to implement "removeItem(key)"! Found: {0}.', typeof storageImpl.removeItem);
                }
                this.$$storage = storageImpl;
            } else if (this.$$storageMode === 'localStorage') {
                try {
                    localStorage.setItem('angular-cache', 'angular-cache');
                    localStorage.removeItem('angular-cache');
                    this.$$storage = localStorage;
                } catch (e) {
                    delete this.$$storage;
                    this.$$storageMode = 'memory';
                }
            } else if (this.$$storageMode === 'sessionStorage') {
                try {
                    sessionStorage.setItem('angular-cache', 'angular-cache');
                    sessionStorage.removeItem('angular-cache');
                    this.$$storage = sessionStorage;
                } catch (e) {
                    delete this.$$storage;
                    this.$$storageMode = 'memory';
                }
            }
        }

        /**
         * @doc method
         * @id DSCache.methods:setOptions
         * @name setOptions
         * @description
         * Configure this cache with the given options. With this method you can configure all of this cache's settings at once.
         *
         * ## Signature:
         * ```js
         * DSCache#setOptions(cacheOptions[, strict])
         * ```
         *
         * ## Example:
         * ```js
         *  cache.setOptions({
         *      maxAge: 60000,
         *      deleteOnExpire: 'aggressive',
         *      disabled: false
         *  });
         * ```
         *
         * @param {object} cacheOptions New configuration options for the cache. Properties:
         *
         * - `{number=}` - `capacity` - Default: `Number.MAX_VALUE`
         * - `{number=}` - `maxAge` - Default: `null`
         * - `{number=}` - `deleteOnExpire` - Default: `none`
         * - `{function=}` - `onExpire` - Default: `null`
         * - `{number=}` - `cacheFlushInterval` - Default: `null`
         * - `{number=}` - `recycleFreq` - Default: `1000`
         * - `{boolean=}` - `disabled` - Default: `false`
         *
         * @param {boolean=} strict If true then any existing configuration will be reset to the defaults before
         * applying the new options, otherwise only the options specified in the options hash will be altered.
         */
        function _setOptions(cacheOptions, strict) {
            cacheOptions = cacheOptions || {};
            strict = !!strict;
            if (!angular.isObject(cacheOptions)) {
                throw angular.$$minErr('ng')('areq', 'Expected cacheOptions to be an object! Found: {0}.', typeof cacheOptions);
            }

            if ('disabled' in cacheOptions) {
                this.$$disabled = !!cacheOptions.disabled;
            } else if (strict) {
                delete this.$$disabled;
            }

            if ('capacity' in cacheOptions) {
                this.setCapacity(cacheOptions.capacity);
            } else if (strict) {
                this.setCapacity(null);
            }

            if ('deleteOnExpire' in cacheOptions) {
                this.setDeleteOnExpire(cacheOptions.deleteOnExpire);
            } else if (strict) {
                this.setDeleteOnExpire(null);
            }

            if ('maxAge' in cacheOptions) {
                this.setMaxAge(cacheOptions.maxAge);
            } else if (strict) {
                this.setMaxAge(null);
            }

            if ('recycleFreq' in cacheOptions) {
                this.setRecycleFreq(cacheOptions.recycleFreq);
            } else if (strict) {
                this.setRecycleFreq(null);
            }

            if ('cacheFlushInterval' in cacheOptions) {
                this.setCacheFlushInterval(cacheOptions.cacheFlushInterval);
            } else if (strict) {
                this.setCacheFlushInterval(null);
            }

            if ('onExpire' in cacheOptions) {
                this.setOnExpire(cacheOptions.onExpire);
            } else if (strict) {
                this.setOnExpire(null);
            }
        }

        /**
         * @doc function
         * @id DSCache
         * @name DSCache
         * @description
         * Instantiated via `DSCacheFactory(cacheId[, options])`.
         *
         * @param {string} cacheId The id of the new cache.
         * @param {object=} options Configuration options.
         */
        function DSCache(cacheId, options) {

            this.$$data = {};
            this.$$id = cacheId;
            this.$$storage = null;

            this.$$expiresHeap = new DSBinaryHeap(function (x) {
                return x.expires;
            });

            this.$$lruHeap = new DSBinaryHeap(function (x) {
                return x.accessed;
            });

            options = options || {};

            if ('storageMode' in options) {
                _setStorageMode.apply(this, [options.storageMode, options.storageImpl]);
            }
            if ('storagePrefix' in options) {
                this.$$storagePrefix = options.storagePrefix;
            }

            this.$$prefix = this.$$storagePrefix + cacheId;

            // Initialize this cache with the default and given options
            _setOptions.apply(this, [options, true]);
        }

        for (var key in defaults.defaults) {
            DSCache.prototype['$$' + key] = defaults.defaults[key];
        }

        /**
         * @doc method
         * @id DSCache.methods:setOptions
         * @name setOptions
         * @methodOf DSCache
         * @description
         * See [DSCache.setOptions](/documentation/api/angular-cache/DSCache.methods:create).
         */
        DSCache.prototype.setOptions = _setOptions;

        /**
         * @doc method
         * @id DSCache.methods:setCapacity
         * @name setCapacity
         * @methodOf DSCache
         * @description
         * See [DSCache.setCapacity](/documentation/api/angular-cache/DSCache.methods:create).
         */
        DSCache.prototype.setCapacity = require('./setCapacity');

        /**
         * @doc method
         * @id DSCache.methods:setDeleteOnExpire
         * @name setDeleteOnExpire
         * @methodOf DSCache
         * @description
         * See [DSCache.setDeleteOnExpire](/documentation/api/angular-cache/DSCache.methods:create).
         */
        DSCache.prototype.setDeleteOnExpire = require('./setDeleteOnExpire');

        /**
         * @doc method
         * @id DSCache.methods:setMaxAge
         * @name setMaxAge
         * @methodOf DSCache
         * @description
         * See [DSCache.setMaxAge](/documentation/api/angular-cache/DSCache.methods:create).
         */
        DSCache.prototype.setMaxAge = require('./setMaxAge');

        /**
         * @doc method
         * @id DSCache.methods:setRecycleFreq
         * @name setRecycleFreq
         * @methodOf DSCache
         * @description
         * See [DSCache.setRecycleFreq](/documentation/api/angular-cache/DSCache.methods:create).
         */
        DSCache.prototype.setRecycleFreq = require('./setRecycleFreq');

        /**
         * @doc method
         * @id DSCache.methods:setCacheFlushInterval
         * @name setCacheFlushInterval
         * @methodOf DSCache
         * @description
         * See [DSCache.setCacheFlushInterval](/documentation/api/angular-cache/DSCache.methods:create).
         */
        DSCache.prototype.setCacheFlushInterval = require('./setCacheFlushInterval');

        /**
         * @doc method
         * @id DSCache.methods:setOnExpire
         * @name setOnExpire
         * @methodOf DSCache
         * @description
         * See [DSCache.setOnExpire](/documentation/api/angular-cache/DSCache.methods:create).
         */
        DSCache.prototype.setOnExpire = require('./setOnExpire');

        /**
         * @doc method
         * @id DSCache.methods:put
         * @name put
         * @methodOf DSCache
         * @description
         * See [DSCache.put](/documentation/api/angular-cache/DSCache.methods:create).
         */
        DSCache.prototype.put = require('./put');

        /**
         * @doc method
         * @id DSCache.methods:get
         * @name get
         * @methodOf DSCache
         * @description
         * See [DSCache.get](/documentation/api/angular-cache/DSCache.methods:create).
         */
        DSCache.prototype.get = require('./get');

        /**
         * @doc method
         * @id DSCache.methods:remove
         * @name remove
         * @methodOf DSCache
         * @description
         * See [DSCache.remove](/documentation/api/angular-cache/DSCache.methods:create).
         */
        DSCache.prototype.remove = require('./remove');

        /**
         * @doc method
         * @id DSCache.methods:removeAll
         * @name removeAll
         * @methodOf DSCache
         * @description
         * See [DSCache.removeAll](/documentation/api/angular-cache/DSCache.methods:create).
         */
        DSCache.prototype.removeAll = require('./removeAll');

        /**
         * @doc method
         * @id DSCache.methods:removeExpired
         * @name removeExpired
         * @methodOf DSCache
         * @description
         * See [DSCache.removeExpired](/documentation/api/angular-cache/DSCache.methods:create).
         */
        DSCache.prototype.removeExpired = require('./removeExpired');

        /**
         * @doc method
         * @id DSCache.methods:destroy
         * @name destroy
         * @methodOf DSCache
         * @description
         * See [DSCache.destroy](/documentation/api/angular-cache/DSCache.methods:create).
         */
        DSCache.prototype.destroy = require('./destroy');

        /**
         * @doc method
         * @id DSCache.methods:info
         * @name info
         * @methodOf DSCache
         * @description
         * See [DSCache.info](/documentation/api/angular-cache/DSCache.methods:create).
         */
        DSCache.prototype.info = require('./info');

        /**
         * @doc method
         * @id DSCache.methods:keySet
         * @name keySet
         * @methodOf DSCache
         * @description
         * See [DSCache.keySet](/documentation/api/angular-cache/DSCache.methods:create).
         */
        DSCache.prototype.keySet = require('./keySet');

        /**
         * @doc method
         * @id DSCache.methods:keys
         * @name keys
         * @methodOf DSCache
         * @description
         * See [DSCache.keys](/documentation/api/angular-cache/DSCache.methods:create).
         */
        DSCache.prototype.keys = require('./keys');

        /**
         * @doc method
         * @id DSCache.methods:disable
         * @name disable
         * @description
         * Disable this cache. Disabling a cache does not remove any data, it just turns DSCache#get and DSCache#put into noops.
         *
         * ## Signature:
         * ```js
         * DSCache#disable()
         * ```
         *
         * ## Example:
         * ```js
         *  var cache = DSCacheFactory.get('cache');
         *
         *  cache.put('1', 'apple');
         *  cache.get('1'); // "apple"
         *  cache.info().size; // 1
         *
         *  cache.disable();
         *  cache.info().size; // 1
         *
         *  cache.get('1'); // undefined
         *  cache.put('2', 'banana'); // undefined
         *  cache.get('2'); // undefined
         *  cache.info().size; // 1
         * ```
         */
        DSCache.prototype.disable = function () {
            this.$$disabled = true;
        };

        /**
         * @doc method
         * @id DSCache.methods:enable
         * @name enable
         * @description
         * Enable this cache.
         *
         * ## Signature:
         * ```js
         * DSCache#enable()
         * ```
         *
         * ## Example:
         * ```js
         *  var options = {
         *      disabled: true
         *  };
         *  var cache = DSCacheFactory.get('cache', options);
         *
         *  cache.put('1', 'apple');
         *  cache.get('1'); // undefined
         *
         *  cache.enable();
         *
         *  cache.put('1', 'apple');
         *  cache.get('1'); // "apple"
         * ```
         */
        DSCache.prototype.enable = function () {
            delete this.$$disabled;
        };

        /**
         * @doc method
         * @id DSCache.methods:touch
         * @name touch
         * @description
         * Reset the expiry of a single item or all items in the cache.
         *
         * ## Signature:
         * ```js
         * DSCache#touch(key)
         * ```
         *
         * ## Example:
         * ```js
         *  cache.touch('1'); // touch one item
         *
         *  cache.touch(); // touch all items
         * ```
         *
         * @param {string=} key The key of the item to touch.
         */
        DSCache.prototype.touch = function (key) {
            if (key) {
                var _this = this;
                var val = this.get(key, {
                    onExpire: function (k, v) {
                        _this.put(k, v);
                    }
                });
                if (val) {
                    this.put(key, val);
                }
            } else {
                var keys = this.keys();
                for (var i = 0; i < keys.length; i++) {
                    this.touch(keys[i]);
                }
            }
        };

        module.exports = DSCache;

    }, {
        "../DSBinaryHeap": 1,
        "../defaults": 19,
        "./destroy": 2,
        "./get": 3,
        "./info": 5,
        "./keySet": 6,
        "./keys": 7,
        "./put": 8,
        "./remove": 9,
        "./removeAll": 10,
        "./removeExpired": 11,
        "./setCacheFlushInterval": 12,
        "./setCapacity": 13,
        "./setDeleteOnExpire": 14,
        "./setMaxAge": 15,
        "./setOnExpire": 16,
        "./setRecycleFreq": 17
    }],
    5: [function (require, module, exports) {
        /**
         * @doc method
         * @id DSCache.methods:info
         * @name info
         * @description
         * Return the status of this cache, or if `key` is provided return the status of the item with that key.
         *
         * ## Signature:
         * ```js
         * DSCache#info([key])
         * ```
         *
         * ## Example:
         * ```js
         * var cache = DSCacheFactory('cache');
         *
         * cache.put('1', 'apple');
         * cache.put('2', 'banana');
         *
         * cache.info();    //  {
         *                  //      id: 'cache',
         *                  //      capacity: Number.MAX_VALUE,
         *                  //      maxAge: Number.MAX_VALUE,
         *                  //      deleteOnExpire: 'none',
         *                  //      onExpire: null,
         *                  //      cacheFlushInterval: null,
         *                  //      recycleFreq: 1000,
         *                  //      storageMode: 'memory',
         *                  //      storageImpl: null,
         *                  //      disabled: false,
         *                  //      size: 2
         *                  //  }
         *
         * cache.info('1'); //  {
         *                  //      created: 1234567890,
         *                  //      accessed: 1234567890,
         *                  //      expires: Number.MAX_VALUE,
         *                  //      isExpired: false
         *                  //  }
         *
         * cache.info('3'); // undefined
         * ```
         *
         * @param {string=} key The key of the item whose status is to be retrieved.
         * @returns {object} The status of this cache or of the item with the given key.
         */
        module.exports = function info(key) {
            if (key) {
                var item;
                if (this.$$storage) {
                    var itemJson = this.$$storage.getItem(this.$$prefix + '.data.' + key);

                    if (itemJson) {
                        item = angular.fromJson(itemJson);
                        return {
                            created: item.created,
                            accessed: item.accessed,
                            expires: item.expires,
                            isExpired: (new Date().getTime() - item.created) > this.$$maxAge
                        };
                    } else {
                        return undefined;
                    }
                } else {
                    if (key in this.$$data) {
                        item = this.$$data[key];

                        return {
                            created: item.created,
                            accessed: item.accessed,
                            expires: item.expires,
                            isExpired: (new Date().getTime() - item.created) > this.$$maxAge
                        };
                    } else {
                        return undefined;
                    }
                }
            } else {
                return {
                    id: this.$$id,
                    capacity: this.$$capacity,
                    maxAge: this.$$maxAge,
                    deleteOnExpire: this.$$deleteOnExpire,
                    onExpire: this.$$onExpire,
                    cacheFlushInterval: this.$$cacheFlushInterval,
                    recycleFreq: this.$$recycleFreq,
                    storageMode: this.$$storageMode,
                    storageImpl: this.$$storage,
                    disabled: this.$$disabled,
                    size: this.$$lruHeap && this.$$lruHeap.size() || 0
                };
            }
        };

    }, {}],
    6: [function (require, module, exports) {
        var utils = require('../utils');

        /**
         * @doc method
         * @id DSCache.methods:keySet
         * @name keySet
         * @description
         * Return an object of the keys in this cache.
         *
         * ## Signature:
         * ```js
         * DSCache#keySet()
         * ```
         *
         * ## Example:
         * ```js
         * var cache = DSCacheFactory('cache');
         *
         * cache.put('1', 'apple');
         * cache.put('2', 'banana');
         *
         * cache.keys(); // { "1": "1", "2": "2" }
         * ```
         *
         * @returns {object} An object of the keys in this cache.
         */
        module.exports = function keySet() {
            if (this.$$storage) {
                var keysJson = this.$$storage.getItem(this.$$prefix + '.keys'),
                    kSet = {};

                if (keysJson) {
                    var keys = angular.fromJson(keysJson);

                    for (var i = 0; i < keys.length; i++) {
                        kSet[keys[i]] = keys[i];
                    }
                }
                return kSet;
            } else {
                return utils.keySet(this.$$data);
            }
        };

    }, {
        "../utils": 21
    }],
    7: [function (require, module, exports) {
        var utils = require('../utils');

        /**
         * @doc method
         * @id DSCache.methods:keys
         * @name keys
         * @description
         * Return an array of the keys in this cache.
         *
         * ## Signature:
         * ```js
         * DSCache#keys()
         * ```
         *
         * ## Example:
         * ```js
         * var cache = DSCacheFactory('cache');
         *
         * cache.put('1', 'apple');
         * cache.put('2', 'banana');
         *
         * cache.keys(); // [ "1", "2" ]
         * ```
         *
         * @returns {Array} An array of the keys in this cache.
         */
        module.exports = function keys() {
            if (this.$$storage) {
                var keysJson = this.$$storage.getItem(this.$$prefix + '.keys');

                if (keysJson) {
                    return angular.fromJson(keysJson);
                } else {
                    return [];
                }
            } else {
                return utils.keys(this.$$data);
            }
        };

    }, {
        "../utils": 21
    }],
    8: [function (require, module, exports) {
        var utils = require('../utils');

        /**
         * @doc method
         * @id DSCache.methods:put
         * @name put
         * @description
         * Insert a value into the cache under the given key.
         *
         * ## Signature:
         * ```js
         * DSCache#put(key, value)
         * ```
         *
         * ## Example:
         * ```js
         * var cache = DSCacheFactory('cache');
         *
         * cache.put('1', 'apple');
         * cache.put('2', 3);
         * cache.put('3', { stuff: 'more stuff' });
         *
         * cache.get('1'); // "apple"
         * cache.get('2'); // 3
         * cache.get('3'); // { stuff: 'more stuff' }
         * cache.get('4'); // undefined
         * ```
         *
         * ## Throws:
         * - `Error` - `key` must be a string.
         *
         * @param {string} key The key under which to store the given value.
         * @param {*} value The value to store.
         * @returns {*} The newly stored item.
         */
        module.exports = function put(key, value) {
            var _this = this;
            if (this.$$disabled || value === null || value === undefined) {
                return;
            }
            if (value && value.then && false) {
                value.then(function (v) {
                    if (angular.isObject(v) && 'status' in v && 'data' in v) {
                        _this.put(key, [v.status, v.data, v.headers(), v.statusText]);
                    } else {
                        _this.put(key, v);
                    }
                });
                return;
            }
            key = utils.stringifyNumber(key);

            if (!angular.isString(key)) {
                throw angular.$$minErr('ng')('areq', 'Expected key to be a string! Found: {0}.', typeof key);
            }

            var now = new Date().getTime(),
                item = {
                    key: key,
                    value: value,
                    created: now,
                    accessed: now
                };

            item.expires = item.created + this.$$maxAge;

            if (this.$$storage) {
                var keysJson = this.$$storage.getItem(this.$$prefix + '.keys'),
                    keys = keysJson ? angular.fromJson(keysJson) : [],
                    itemJson = this.$$storage.getItem(this.$$prefix + '.data.' + key);

                // Remove existing
                if (itemJson) {
                    this.remove(key);
                }
                // Add to expires heap
                this.$$expiresHeap.push({
                    key: key,
                    expires: item.expires
                });
                // Add to lru heap
                this.$$lruHeap.push({
                    key: key,
                    accessed: item.accessed
                });
                // Set item
                this.$$storage.setItem(this.$$prefix + '.data.' + key, (item));
                var exists = false;
                for (var i = 0; i < keys.length; i++) {
                    if (keys[i] === key) {
                        exists = true;
                        break;
                    }
                }
                if (!exists) {
                    keys.push(key);
                }
                this.$$storage.setItem(this.$$prefix + '.keys', (keys));
            } else {
                // Remove existing
                if (this.$$data[key]) {
                    this.remove(key);
                }
                // Add to expires heap
                this.$$expiresHeap.push(item);
                // Add to lru heap
                this.$$lruHeap.push(item);
                // Set item
                this.$$data[key] = item;
            }

            // Handle exceeded capacity
            if (this.$$lruHeap.size() > this.$$capacity) {
                this.remove(this.$$lruHeap.peek().key);
            }

            return value;
        };

    }, {
        "../utils": 21
    }],
    9: [function (require, module, exports) {
        /**
         * @doc method
         * @id DSCache.methods:remove
         * @name remove
         * @description
         * Remove the item with the given key.
         *
         * ## Signature:
         * ```js
         * DSCache#remove(key)
         * ```
         *
         * ## Example:
         * ```js
         * var cache = DSCacheFactory('cache');
         *
         * cache.put('1', 'apple');
         *
         * cache.get('1'); // "apple"
         *
         * cache.remove('1'); // "apple"
         *
         * cache.get('1'); // undefined
         * ```
         *
         * @param {string} key The key of the item to remove.
         * @returns {*} The removed item if an item was removed.
         */
        module.exports = function remove(key) {
            if (this.$$storage) {
                var itemJson = this.$$storage.getItem(this.$$prefix + '.data.' + key);

                if (itemJson) {
                    var item = angular.fromJson(itemJson);
                    this.$$lruHeap.remove({
                        key: key,
                        accessed: item.accessed
                    });
                    this.$$expiresHeap.remove({
                        key: key,
                        expires: item.expires
                    });
                    this.$$storage.removeItem(this.$$prefix + '.data.' + key);
                    var keysJson = this.$$storage.getItem(this.$$prefix + '.keys'),
                        keys = keysJson ? angular.fromJson(keysJson) : [],
                        index = keys.indexOf(key);

                    if (index >= 0) {
                        keys.splice(index, 1);
                    }
                    this.$$storage.setItem(this.$$prefix + '.keys', (keys));
                    return item.value;
                }
            } else {
                var value = this.$$data[key] ? this.$$data[key].value : undefined;
                this.$$lruHeap.remove(this.$$data[key]);
                this.$$expiresHeap.remove(this.$$data[key]);
                this.$$data[key] = null;
                delete this.$$data[key];
                return value;
            }
        };

    }, {}],
    10: [function (require, module, exports) {
        /**
         * @doc method
         * @id DSCache.methods:removeAll
         * @name removeAll
         * @description
         * Remove all items from this cache.
         *
         * ## Signature:
         * ```js
         * DSCache#removeAll()
         * ```
         *
         * ## Example:
         * ```js
         * var cache = DSCacheFactory('cache');
         *
         * cache.put('1', 'apple');
         * cache.put('2', 'banana');
         * cache.info().size; // 2
         *
         * cache.get('1'); // "apple"
         * cache.get('2'); // "banana"
         *
         * cache.removeAll();
         * cache.info().size; // 0
         *
         * cache.get('1'); // undefined
         * cache.get('2'); // undefined
         * ```
         */
        module.exports = function removeAll() {
            if (this.$$storage) {
                this.$$lruHeap.removeAll();
                this.$$expiresHeap.removeAll();
                var keysJson = this.$$storage.getItem(this.$$prefix + '.keys');

                if (keysJson) {
                    var keys = angular.fromJson(keysJson);

                    for (var i = 0; i < keys.length; i++) {
                        this.remove(keys[i]);
                    }
                }
                this.$$storage.setItem(this.$$prefix + '.keys', ([]));
            } else {
                this.$$lruHeap.removeAll();
                this.$$expiresHeap.removeAll();
                for (var key in this.$$data) {
                    this.$$data[key] = null;
                }
                this.$$data = {};
            }
        };

    }, {}],
    11: [function (require, module, exports) {
        /**
         * @doc method
         * @id DSCache.methods:removeExpired
         * @name removeExpired
         * @description
         * Remove and return all expired items from the cache.
         *
         * ## Signature:
         * ```js
         * DSCache#removeExpired()
         * ```
         *
         * ## Example:
         * ```js
         *  var options = {
         *          maxAge: 1000
         *      },
         *      // deleteOnExpire defaults to "none"
         *      cache = DSCacheFactory('cache', options);
         *
         *  cache.put('1', 'apple');
         *  cache.put('2', 'banana');
         *
         *  setTimeout(function () {
         *      cache.put('3', 'orange');
         *
         *      cache.info().size; // 3
         *      cache.info('1').isExpired; // true
         *      cache.info('2').isExpired; // true
         *      cache.info('3').isExpired; // false
         *
         *      cache.removeExpired(); // { "1": "apple", "2": "banana" }
         *
         *      cache.info().size; // 1
         *      cache.get('1'); // undefined
         *      cache.get('2'); // undefined
         *      cache.info('3').isExpired; // false
         *  }, 1500);
         * ```
         *
         * @returns {object} The removed items, if any.
         */
        module.exports = function removeExpired() {
            var now = new Date().getTime(),
                expired = {},
                key,
                expiredItem;

            while ((expiredItem = this.$$expiresHeap.peek()) && expiredItem.expires < now) {
                expired[expiredItem.key] = expiredItem.value ? expiredItem.value : null;
                this.$$expiresHeap.pop();
            }

            if (this.$$storage) {
                for (key in expired) {
                    var itemJson = this.$$storage.getItem(this.$$prefix + '.data.' + key);
                    if (itemJson) {
                        expired[key] = angular.fromJson(itemJson).value;
                        this.remove(key);
                    }
                }
            } else {
                for (key in expired) {
                    this.remove(key);
                }
            }

            if (this.$$onExpire) {
                for (key in expired) {
                    this.$$onExpire(key, expired[key]);
                }
            }

            return expired;
        };

    }, {}],
    12: [function (require, module, exports) {
        /**
         * @doc method
         * @id DSCache.methods:setCacheFlushInterval
         * @name setCacheFlushInterval
         * @description
         * Set the `cacheFlushInterval` setting for this cache. If set, this setting will cause this cache to periodically
         * clear itself.
         *
         * ## Signature:
         * ```js
         * DSCache#setCacheFlushInterval(cacheFlushInterval)
         * ```
         *
         * ## Example:
         * ```js
         *  var cache = DSCacheFactory('cache');
         *
         *  cache.put('1', 'apple');
         *  cache.put('2', 'banana');
         *
         *  cache.info().size; // 2
         *  cache.setCacheFlushInterval(60000);
         *
         *  setTimeout(function () {
         *      cache.info().size; // 0
         *  }, 90000);
         * ```
         *
         * ## Throws:
         * - `Error` - `cacheFlushInterval` must be `null` or a number greater than zero.
         *
         * @param {number|null} cacheFlushInterval The new cacheFlushInterval for this cache in milliseconds. If
         * `cacheFlushInterval` is `null` then `cacheFlushInterval` for this cache will be reset to the default (`null`).
         */
        module.exports = function setCacheFlushInterval(cacheFlushInterval) {
            if (cacheFlushInterval === null) {
                delete this.$$cacheFlushInterval;
            } else if (!angular.isNumber(cacheFlushInterval)) {
                throw angular.$$minErr('ng')('areq', 'Expected cacheFlushInterval to be a number! Found: {0}.', typeof cacheFlushInterval);
            } else if (cacheFlushInterval < 0) {
                throw angular.$$minErr('ng')('areq', 'Expected cacheFlushInterval to be greater than zero! Found: {0}.', cacheFlushInterval);
            } else if (cacheFlushInterval !== this.$$cacheFlushInterval) {
                this.$$cacheFlushInterval = cacheFlushInterval;
                clearInterval(this.$$cacheFlushIntervalId);
                (function (_this) {
                    _this.$$cacheFlushIntervalId = setInterval(function () {
                        _this.removeAll();
                    }, _this.$$cacheFlushInterval);
                })(this);
            }
        };

    }, {}],
    13: [function (require, module, exports) {
        /**
         * @doc method
         * @id DSCache.methods:setCapacity
         * @name setCapacity
         * @description
         * Set the capacity for this cache.
         *
         * ## Signature:
         * ```js
         * DSCache#setCapacity(capacity)
         * ```
         *
         * ## Example:
         * ```js
         * var smallCache = DSCacheFactory('smallCache', { capacity: 2 });
         *
         * smallCache.info().size; // 0
         *
         * smallCache.put('1', 'apple');
         * smallCache.put('2', 'banana');
         *
         * smallCache.info().size; // 2
         *
         * // Least-recently used items are removed
         * // when the cache's new capacity exceeds
         * // its size
         * smallCache.setCapacity(1);
         *
         * smallCache.get('1'); // undefined
         * smallCache.info().size; // 1
         * ```
         *
         * ## Throws:
         * - `Error` - `capacity` must be `null` or a number greater than zero.
         *
         * @param {number|null} capacity The new capacity for this cache. If `capacity` is `null` then the capacity for this cache
         * will be reset to the default (`Number.MAX_VALUE`).
         * @returns {object} Key-value pairs of any items removed because this cache's size exceeds the new capacity.
         */
        module.exports = function setCapacity(capacity) {
            if (capacity === null) {
                delete this.$$capacity;
            } else if (!angular.isNumber(capacity)) {
                throw angular.$$minErr('ng')('areq', 'Expected capacity to be a number! Found: {0}.', typeof capacity);
            } else if (capacity < 0) {
                throw angular.$$minErr('ng')('areq', 'Expected capacity to be greater than zero! Found: {0}.', capacity);
            } else {
                this.$$capacity = capacity;
            }
            var removed = {};
            while (this.$$lruHeap.size() > this.$$capacity) {
                removed[this.$$lruHeap.peek().key] = this.remove(this.$$lruHeap.peek().key);
            }
            return removed;
        };

    }, {}],
    14: [function (require, module, exports) {
        /**
         * @doc method
         * @id DSCache.methods:setDeleteOnExpire
         * @name setDeleteOnExpire
         * @description
         * Set the behavior for this cache for when items expire. This setting determines what this cache will do when one of
         * its items expires.
         *
         * ## Possible Values:
         * - `"none"` - Do nothing when items expire.
         * - `"passive"` - Do nothing when items expire, but if an expired item is requested, remove it from the cache and return `undefined`.
         * - `"aggressive"` - Scan for expired items on the interval specified by the `recycleFreq` setting for this cache (defaults
         * to `1000ms`) and actively remove any expired items.
         *
         * ## Signature:
         * ```js
         * DSCache#setDeleteOnExpire(deleteOnExpire)
         * ```
         *
         * ## Example:
         * ```js
         * var cache = DSCacheFactory('cache');
         *
         * cache.put('1', 'apple');
         *
         * // Wait a few seconds
         *
         * cache.get('1'); // "apple"
         *
         * cache.setDeleteOnExpire('aggressive');
         *
         * // Wait a few seconds
         *
         * cache.get('1'); // undefined
         * ```
         *
         * ## Throws:
         * - `Error` - `deleteOnExpire` must be `null`, `"none"`, `"passive"` or `"aggressive"`.
         *
         * @param {string|null} deleteOnExpire The new deleteOnExpire for this cache. If `deleteOnExpire` is `null` then
         * `deleteOnExpire` for this cache will be reset to the default (`"none"`).
         */
        module.exports = function setDeleteOnExpire(deleteOnExpire) {
            if (deleteOnExpire === null) {
                delete this.$$deleteOnExpire;
            } else if (!angular.isString(deleteOnExpire)) {
                throw angular.$$minErr('ng')('areq', 'Expected deleteOnExpire to be a string! Found: {0}.', typeof deleteOnExpire);
            } else if (deleteOnExpire !== 'none' && deleteOnExpire !== 'passive' && deleteOnExpire !== 'aggressive') {
                throw angular.$$minErr('ng')('areq', 'Expected deleteOnExpire to be "none", "passive" or "aggressive"! Found: {0}.', deleteOnExpire);
            } else {
                this.$$deleteOnExpire = deleteOnExpire;
            }
            this.setRecycleFreq(this.$$recycleFreq);
        };

    }, {}],
    15: [function (require, module, exports) {
        var utils = require('../utils');

        /**
         * @doc method
         * @id DSCache.methods:setMaxAge
         * @name setMaxAge
         * @description
         * Set the `maxAge` setting for this cache. This setting specifies how long items can be in the cache before they expire.
         *
         * ## Signature:
         * ```js
         * DSCache#setMaxAge(maxAge)
         * ```
         *
         * ## Example:
         * ```js
         *  var cache = DSCacheFactory('cache', { deleteOnExpire: 'aggressive' });
         *
         *  // This won't expire for a long time
         *  cache.put('1', 'apple');
         *
         *  setTimeout(function () {
         *      // 'apple' will be removed because it
         *      // has already been in the cache longer
         *      // than the new maxAge
         *      var removed = cache.setMaxAge(1000);
         *
         *      removed; // {
         *               //     '1': 'apple'
         *               // }
         *  }, 1500);
         * ```
         *
         * ## Throws:
         * - `Error` - `maxAge must be `null` or a number greater than zero.
         *
         * @param {number} maxAge The new maxAge for this cache in milliseconds. If `maxAge` is `null` then `maxAge` for this
         * cache will be reset to the default (`Number.MAX_VALUE`);
         * @returns {object} Key-value pairs of any items aggressively removed because they are expired according to the new
         * `maxAge`. Items are only removed if the `deleteOnExpire` setting for this cache is set to `"aggressive"`.
         */
        module.exports = function setMaxAge(maxAge) {
            if (maxAge === null) {
                delete this.$$maxAge;
            } else if (!angular.isNumber(maxAge)) {
                throw angular.$$minErr('ng')('areq', 'Expected maxAge to be a number! Found: {0}.', typeof maxAge);
            } else if (maxAge < 0) {
                throw angular.$$minErr('ng')('areq', 'Expected maxAge to be greater than zero! Found: {0}.', maxAge);
            } else {
                this.$$maxAge = maxAge;
            }
            var i, keys, key;

            this.$$expiresHeap.removeAll();

            if (this.$$storage) {
                var keysJson = this.$$storage.getItem(this.$$prefix + '.keys');

                keys = keysJson ? angular.fromJson(keysJson) : [];

                for (i = 0; i < keys.length; i++) {
                    key = keys[i];
                    var itemJson = this.$$storage.getItem(this.$$prefix + '.data.' + key);

                    if (itemJson) {
                        var item = angular.fromJson(itemJson);
                        if (this.$$maxAge === Number.MAX_VALUE) {
                            item.expires = Number.MAX_VALUE;
                        } else {
                            item.expires = item.created + this.$$maxAge;
                        }
                        this.$$expiresHeap.push({
                            key: key,
                            expires: item.expires
                        });
                    }
                }
            } else {
                keys = utils.keys(this.$$data);

                for (i = 0; i < keys.length; i++) {
                    key = keys[i];
                    if (this.$$maxAge === Number.MAX_VALUE) {
                        this.$$data[key].expires = Number.MAX_VALUE;
                    } else {
                        this.$$data[key].expires = this.$$data[key].created + this.$$maxAge;
                    }
                    this.$$expiresHeap.push(this.$$data[key]);
                }
            }
            if (this.$$deleteOnExpire === 'aggressive') {
                return this.removeExpired();
            } else {
                return {};
            }
        };

    }, {
        "../utils": 21
    }],
    16: [function (require, module, exports) {
        /**
         * @doc method
         * @id DSCache.methods:setOnExpire
         * @name setOnExpire
         * @description
         * Set the global `onExpire` callback for this cache.
         *
         * ## Signature:
         * ```js
         * DSCache#setOnExpire(onExpire)
         * ```
         *
         * ## Examples:
         * ```js
         *  var options = {
         *      onExpire: function (key, value) {
         *          window.lastExpiredItem = key;
         *      },
         *      maxAge: 1000,
         *      deleteOnExpire: 'aggressive'
         *  };
         *  var cache = DSCacheFactory('cache', options);
         *
         *  cache.put('1', 'apple');
         *
         *  setTimeout(function () {
         *      window.lastExpiredItem; // '1'
         *  }, 1500);
         * ```
         *
         * ## Throws:
         * - `Error` - `cacheFlushInterval` must be `null` or a number greater than zero.
         *
         * @param {function|null} onExpire The new onExpire callback for this cache. If `onExpire` is `null` then the onExpire
         * callback for this cache will be removed.
         */
        module.exports = function setOnExpire(onExpire) {
            if (onExpire === null) {
                delete this.$$onExpire;
            } else if (!angular.isFunction(onExpire)) {
                throw angular.$$minErr('ng')('areq', 'Expected onExpire to be a function! Found: {0}.', typeof onExpire);
            } else {
                this.$$onExpire = onExpire;
            }
        };

    }, {}],
    17: [function (require, module, exports) {
        /**
         * @doc method
         * @id DSCache.methods:setRecycleFreq
         * @name setRecycleFreq
         * @description
         * Set the `recycleFreq` setting for this cache. This setting determines how often this cache will scan for expired
         * items. The cache will only scan for expired items if the `deleteOnExpire` setting for this cache is set to
         * `"aggressive"`.
         *
         * ## Signature:
         * ```js
         * DSCache#setRecycleFreq(recycleFreq)
         * ```
         *
         * ## Example:
         * ```js
         *  var options = {
         *      deleteOnExpire: 'aggressive',
         *      maxAge: 1000
         *  };
         *  var cache = DSCacheFactory('cache', options);
         *
         *  cache.put('1', 'apple');
         *
         *  setTimeout(function () {
         *
         *      cache.get('1'); // undefined
         *      cache.setRecycleFreq(60000);
         *
         *      // This expires after 1 second, but the cache
         *      // only checks every 60 seconds now
         *      cache.put('1', 'apple');
         *
         *      setTimeout(function () {
         *          // expired, but won't be removed
         *          // until the next check
         *          cache.get('1'); // "apple"
         *          cache.info('1').isExpired; // true
         *      }, 1500);
         *  }, 1500);
         * ```
         *
         * ## Throws:
         * - `Error` - `recycleFreq` must be `null` or a number greater than zero.
         *
         * @param {number} recycleFreq The new recycleFreq for this cache in milliseconds. If `recycleFreq` is `null` then
         * `recycleFreq` for this cache will be reset to the default (`1000` milliseconds).
         */
        module.exports = function setRecycleFreq(recycleFreq) {
            if (recycleFreq === null) {
                delete this.$$recycleFreq;
            } else if (!angular.isNumber(recycleFreq)) {
                throw angular.$$minErr('ng')('areq', 'Expected recycleFreq to be a number! Found: {0}.', typeof recycleFreq);
            } else if (recycleFreq < 0) {
                throw angular.$$minErr('ng')('areq', 'Expected recycleFreq to be greater than zero! Found: {0}.', recycleFreq);
            } else {
                this.$$recycleFreq = recycleFreq;
            }
            clearInterval(this.$$recycleFreqId);
            if (this.$$deleteOnExpire === 'aggressive') {
                (function (_this) {
                    _this.$$recycleFreqId = setInterval(function () {
                        _this.removeExpired();
                    }, _this.$$recycleFreq);
                })(this);
            } else {
                delete this.$$recycleFreqId;
            }
        };

    }, {}],
    18: [function (require, module, exports) {
        var defaults = require('../defaults'),
            DSCache = require('../DSCache'),
            version = '3.1.1';

        /**
         * @doc function
         * @id DSCacheFactoryProvider
         * @name DSCacheFactoryProvider
         */
        function DSCacheFactoryProvider() {

            var config = new defaults.Config();

            this.version = version;

            /**
             * @doc method
             * @id DSCacheFactoryProvider.methods:setCacheDefaults
             * @name setCacheDefaults
             * @desc Set the default configuration for all caches created by $angularCacheFactory.
             * @param {object} options Default configuration options for each new cache.
             */
            this.setCacheDefaults = function (options) {
                options = options || {};

                if (!angular.isObject(options)) {
                    throw angular.$$minErr('ng')('areq', 'Expected options to be an object! Found: {0}.', typeof options);
                }

                for (var key in defaults.defaults) {
                    if (key in options) {
                        config[key] = options[key];
                    }
                }
                if ('disabled' in options) {
                    config.$$disabled = !!options.disabled;
                }
            };

            this.$get = function () {
                var caches = {};

                /*!
                 * @method _keys
                 * @desc Returns an array of the keys of the given collection.
                 * @param {object} collection The collection from which to get the keys.
                 * @returns {array} An array of the keys of the given collection.
                 */
                function _keys(collection) {
                    var keys = [],
                        key;
                    for (key in collection) {
                        if (collection.hasOwnProperty(key)) {
                            keys.push(key);
                        }
                    }
                    return keys;
                }

                function createCache(cacheId, options) {
                    if (cacheId in caches) {
                        throw angular.$$minErr('$cacheFactory')('iid', "CacheId '{0}' is already taken!", cacheId);
                    } else if (!angular.isString(cacheId)) {
                        throw angular.$$minErr('ng')('areq', 'Expected cacheId to be a string! Found: {0}.', typeof cacheId);
                    }

                    caches[cacheId] = new DSCache(cacheId, angular.extend({}, config, options));
                    caches[cacheId].destroy = function () {
                        this.constructor.prototype.destroy.call(this);
                        delete caches[this.$$id];
                    };
                    return caches[cacheId];
                }

                /**
                 * @doc function
                 * @id DSCacheFactory
                 * @name DSCacheFactory
                 * @description
                 * Factory function that produces instances of `DSCache`.
                 *
                 * @param {string} cacheId The id of the new cache.
                 * @param {object} options Configuration options. Properties:
                 *
                 * - `{number=}` - `capacity` - Default: `Number.MAX_VALUE`
                 * - `{number=}` - `maxAge` - Default: `null`
                 * - `{number=}` - `deleteOnExpire` - Default: `none`
                 * - `{function=}` - `onExpire` - Default: `null`
                 * - `{number=}` - `cacheFlushInterval` - Default: `null`
                 * - `{number=}` - `recycleFreq` - Default: `1000`
                 * - `{number=}` - `deleteOnExpire` - Default: `null`
                 * - `{string=}` - `storageMode` - Default: `'none`
                 * - `{object=}` - `storageImpl` - Default: `null`
                 * - `{boolean=}` - `disabled` - Default: `false`
                 * - `{string=}` - `storagePrefix` - Default: `"angular-cache.caches."`
                 *
                 * @returns {DSCache} New instance of DSCache.
                 */
                function DSCacheFactory(cacheId, options) {
                    return createCache(cacheId, options);
                }

                /**
                 * @doc method
                 * @id DSCacheFactory.methods:createCache
                 * @name createCache
                 * @description
                 * Factory function that produces instances of `DSCache`.
                 *
                 * @param {string} cacheId The id of the new cache.
                 * @param {object} options Configuration options. Properties:
                 *
                 * - `{number=}` - `capacity` - Default: `Number.MAX_VALUE`
                 * - `{number=}` - `maxAge` - Default: `null`
                 * - `{number=}` - `deleteOnExpire` - Default: `none`
                 * - `{function=}` - `onExpire` - Default: `null`
                 * - `{number=}` - `cacheFlushInterval` - Default: `null`
                 * - `{number=}` - `recycleFreq` - Default: `1000`
                 * - `{number=}` - `deleteOnExpire` - Default: `null`
                 * - `{string=}` - `storageMode` - Default: `'none`
                 * - `{object=}` - `storageImpl` - Default: `null`
                 * - `{boolean=}` - `disabled` - Default: `false`
                 * - `{string=}` - `storagePrefix` - Default: `"angular-cache.caches."`
                 *
                 * @returns {DSCache} New instance of DSCache.
                 */
                DSCacheFactory.createCache = createCache;

                DSCacheFactory.version = version;

                /**
                 * @doc method
                 * @id DSCacheFactory.methods:info
                 * @name info
                 * @description
                 * Return the status of `DSCacheFactory`.
                 * @returns {object} The status of `DSCacheFactory`.
                 */
                DSCacheFactory.info = function () {
                    var keys = _keys(caches);
                    var info = {
                        size: keys.length,
                        caches: {}
                    };
                    for (var i = 0; i < keys.length; i++) {
                        var key = keys[i];
                        info.caches[key] = caches[key].info();
                    }
                    var c = info.cacheDefaults = angular.extend({}, config);
                    for (var option in defaults.defaults) {
                        if (!(option in c)) {
                            c[option] = config['$$' + option];
                        }
                    }
                    return info;
                };

                /**
                 * @doc method
                 * @id DSCacheFactory.methods:get
                 * @name get
                 * @description
                 * Return the cache with the given `cacheId`.
                 * @param {string} cacheId The id of the desired cache.
                 * @returns {DSCache} The cache with the specified `cacheId`.
                 */
                DSCacheFactory.get = function (cacheId) {
                    if (!angular.isString(cacheId)) {
                        throw angular.$$minErr('ng')('areq', 'Expected cacheId to be a string! Found: {0}.', typeof cacheId);
                    }
                    return caches[cacheId];
                };

                /**
                 * @doc method
                 * @id DSCacheFactory.methods:keySet
                 * @name keySet
                 * @description
                 * Return an object containing the `cacheId` of each cache.
                 * @returns {object} An object containing the `cacheId` of each cache.
                 */
                DSCacheFactory.keySet = function () {
                    var cacheIds = {},
                        cacheId;
                    for (cacheId in caches) {
                        if (caches.hasOwnProperty(cacheId)) {
                            cacheIds[cacheId] = cacheId;
                        }
                    }
                    return cacheIds;
                };

                /**
                 * @doc method
                 * @id DSCacheFactory.methods:keys
                 * @name keys
                 * @description
                 * Return an array containing the `cacheId` of each cache.
                 * @returns {array} An array containing the `cacheId` of each cache.
                 */
                DSCacheFactory.keys = function () {
                    return _keys(caches);
                };

                /**
                 * @doc method
                 * @id DSCacheFactory.methods:destroyAll
                 * @name destroyAll
                 * @description
                 * Destroy all caches.
                 *
                 * ## Signature:
                 * ```js
                 * DSCacheFactory.destroyAll()
                 * ```
                 *
                 * ## Example:
                 * ```js
                 * var newCache = DSCacheFactory('newCache');
                 * var otherCache = DSCacheFactory('otherCache');
                 *
                 * newCache.info().size; // 0
                 * otherCache.info().size; // 0
                 *
                 * newCache.put('1', 'apple');
                 * newCache.put('2', 'banana');
                 * otherCache.put('abcd', 'horse');
                 *
                 * newCache.info().size; // 2
                 * otherCache.info().size; // 1
                 *
                 * DSCacheFactory.destroyAll();
                 *
                 * newCache.info().size; // Error thrown
                 * otherCache.info().size; // Error thrown
                 *
                 * DSCacheFactory.get('newCache'); // undefined
                 * DSCacheFactory.get('otherCache'); // undefined
                 * ```
                 */
                DSCacheFactory.destroyAll = function () {
                    for (var cacheId in caches) {
                        caches[cacheId].destroy();
                    }
                    caches = {};
                };

                /**
                 * @doc method
                 * @id DSCacheFactory.methods:clearAll
                 * @name clearAll
                 * @description
                 * Clear the contents of all caches.
                 *
                 * ## Signature:
                 * ```js
                 * DSCacheFactory.clearAll()
                 * ```
                 *
                 * ## Example:
                 * ```js
                 * var newCache = DSCacheFactory('newCache');
                 * var otherCache = DSCacheFactory('otherCache');
                 *
                 * newCache.info().size; // 0
                 * otherCache.info().size; // 0
                 *
                 * newCache.put('1', 'apple');
                 * newCache.put('2', 'banana');
                 * otherCache.put('abcd', 'horse');
                 *
                 * newCache.info().size; // 2
                 * otherCache.info().size; // 1
                 *
                 * DSCacheFactory.clearAll();
                 *
                 * newCache.info().size; // 0
                 * otherCache.info().size; // 0
                 * ```
                 */
                DSCacheFactory.clearAll = function () {
                    for (var cacheId in caches) {
                        caches[cacheId].removeAll();
                    }
                };

                /**
                 * @doc method
                 * @id DSCacheFactory.methods:enableAll
                 * @name enableAll
                 * @description
                 * Enable any disabled caches.
                 *
                 * ## Signature:
                 * ```js
                 * DSCacheFactory.enableAll()
                 * ```
                 *
                 * ## Example:
                 * ```js
                 * var newCache = DSCacheFactory('newCache', { disabled: true });
                 * var otherCache = DSCacheFactory('otherCache', { disabled: true });
                 *
                 * newCache.info().disabled; // true
                 * otherCache.info().disabled; // true
                 *
                 * DSCacheFactory.enableAll();
                 *
                 * newCache.info().disabled; // false
                 * otherCache.info().disabled; // false
                 * ```
                 */
                DSCacheFactory.enableAll = function () {
                    for (var cacheId in caches) {
                        caches[cacheId].$$disabled = false;
                    }
                };

                /**
                 * @doc method
                 * @id DSCacheFactory.methods:disableAll
                 * @name disableAll
                 * @description
                 * Disable all caches.
                 *
                 * ## Signature:
                 * ```js
                 * DSCacheFactory.disableAll()
                 * ```
                 *
                 * ## Example:
                 * ```js
                 * var newCache = DSCacheFactory('newCache');
                 * var otherCache = DSCacheFactory('otherCache');
                 *
                 * newCache.info().disabled; // false
                 * otherCache.info().disabled; // false
                 *
                 * DSCacheFactory.disableAll();
                 *
                 * newCache.info().disabled; // true
                 * otherCache.info().disabled; // true
                 * ```
                 */
                DSCacheFactory.disableAll = function () {
                    for (var cacheId in caches) {
                        caches[cacheId].$$disabled = true;
                    }
                };

                return DSCacheFactory;
            };
        }

        module.exports = DSCacheFactoryProvider;

    }, {
        "../DSCache": 4,
        "../defaults": 19
    }],
    19: [function (require, module, exports) {
        var defaults = {
            /**
             * @doc overview
             * @id capacity
             * @name capacity
             * @description
             * __Default:__ `Number.MAX_VALUE`
             *
             * This option limits the capacity of a cache. With a maximum capacity set, a cache operates as an LRU cache,
             * deleting the least-recently-used item when the cache exceeds capacity.
             *
             * This option is dynamically configurable. Must be a number (milliseconds) greater than zero.
             *
             * ### Where can it be used?
             * - `DSCacheFactoryProvider.setCacheDefaults(options)`
             * - `DSCacheFactory(cacheId[, options])`
             * - `DSCache.setCapacity(capacity)`
             * - `DSCache.setOptions(options[, strict])`
             */
            capacity: Number.MAX_VALUE,

            /**
             * @doc overview
             * @id maxAge
             * @name maxAge
             * @description
             * __Default:__ `Number.MAX_VALUE`
             *
             * This option determines how long an item is in a cache before the item expires.. With `maxAge` set, items are
             * marked as expired when their time in a cache exceeds `maxAge`. A cache's behavior when an item expires is
             * determined by the [deleteOnExpire](/documentation/api/angular-cache/deleteOnExpire) option.
             *
             * This option is dynamically configurable. Must be a number (milliseconds) greater than zero.
             *
             * ### Where can it be used?
             * - `DSCacheFactoryProvider.setCacheDefaults(options)`
             * - `DSCacheFactory(cacheId[, options])`
             * - `DSCache.setMaxAge(maxAge)`
             * - `DSCache.setOptions(options[, strict])`
             */
            maxAge: Number.MAX_VALUE,

            /**
             * @doc overview
             * @id deleteOnExpire
             * @name deleteOnExpire
             * @description
             * __Default:__ `"none"`
             *
             * This option determines how long an item is in a cache before the item expires.. With `maxAge` set, items are
             * marked as expired when their time in a cache exceeds `maxAge`. A cache's behavior when an item expires is
             * determined by the [deleteOnExpire](/documentation/api/angular-cache/deleteOnExpire) option.
             *
             * This option is dynamically configurable. Must be `"none"`, `"passive"` or `"aggressive"`.
             *
             * #### "none"
             * A cache will do nothing when its items expire.
             *
             * #### "passive"
             * A cache will do nothing when its items expire. If an expired item is request it is removed from the cache and
             * `undefined` is returned.
             *
             * #### "aggressive"
             * A cache will periodically scan for expired items and actively remove them from the cache if any are found. The
             * frequency of the scan is determined by the [recycleFreq](/documentation/api/angular-cache/recycleFreq) option.
             *
             * ### Where can it be used?
             * - `DSCacheFactoryProvider.setCacheDefaults(options)`
             * - `DSCacheFactory(cacheId[, options])`
             * - `DSCache.setRecycleFreq(recycleFreq)`
             * - `DSCache.setOptions(options[, strict])`
             */
            deleteOnExpire: 'none',

            /**
             * @doc overview
             * @id onExpire
             * @name onExpire
             * @description
             * __Default:__ `"none"`
             *
             * This option is a callback function which will be executed whenever an expired item is removed from a cache by
             * either requesting an expired item while the cache is in `"passive"` `deleteOnExpire` mode, or when an expired
             * item is actively removed when the cache is in `"aggressive"` `deleteOnExpire` mode.
             *
             * This option is dynamically configurable. Must be a function. Will be passed the `key` and `value` of the expired
             * item. Will be passed a third `done` argument (if in `"passive"` `deleteOnExpire` mode) which is the `onExpire`
             * argument passed to [DSCache#get(key[, options])](/documentation/api/angular-cache/DSCache.methods:get).
             *
             * ### Where can it be used?
             * - `DSCacheFactoryProvider.setCacheDefaults(options)`
             * - `DSCacheFactory(cacheId[, options])`
             * - `DSCache.setOnExpire(onExpire)`
             * - `DSCache.setOptions(options[, strict])`
             */
            onExpire: null,

            /**
             * @doc overview
             * @id cacheFlushInterval
             * @name cacheFlushInterval
             * @description
             * __Default:__ `null`
             *
             * This option, if set, will cause a cache to periodically clear itself of all data.
             *
             * This option is dynamically configurable. Must be a number (milliseconds) greater than zero.
             *
             * ### Where can it be used?
             * - `DSCacheFactoryProvider.setCacheDefaults(options)`
             * - `DSCacheFactory(cacheId[, options])`
             * - `DSCache.setCacheFlushInterval(cacheFlushInterval)`
             * - `DSCache.setOptions(options[, strict])`
             */
            cacheFlushInterval: null,

            /**
             * @doc overview
             * @id recycleFreq
             * @name recycleFreq
             * @description
             * __Default:__ `1000`
             *
             * This option determines how often a cache will scan for expired items when in `"aggressive"` `deleteOnExpire`
             * mode.
             *
             * This option is dynamically configurable. Must be a number (milliseconds) greater than zero.
             *
             * ### Where can it be used?
             * - `DSCacheFactoryProvider.setCacheDefaults(options)`
             * - `DSCacheFactory(cacheId[, options])`
             * - `DSCache.setRecycleFreq(recycleFreq)`
             * - `DSCache.setOptions(options[, strict])`
             */
            recycleFreq: 1000,

            /**
             * @doc overview
             * @id storageMode
             * @name storageMode
             * @description
             * __Default:__ `"memory"`
             *
             * This option determines the storage mode for a cache.
             *
             * #### "memory"
             * All data will be held in memory.
             *
             * #### "localStorage"
             * Data will be held in `localStorage`, if available (or
             * [storageImpl](/documentation/api/angular-cache/storageImpl) is provided).
             *
             * #### "sessionStorage"
             * Data will be held in `sessionStorage`, if available (or
             * [storageImpl](/documentation/api/angular-cache/storageImpl) is provided).
             *
             * This option is NOT dynamically configurable. Must be `"memory"`, `"localStorage"` or `"sessionStorage"`.
             *
             * ### Where can it be used?
             * - `DSCacheFactoryProvider.setCacheDefaults(options)`
             * - `DSCacheFactory(cacheId[, options])`
             */
            storageMode: 'memory',

            /**
             * @doc overview
             * @id storageImpl
             * @name storageImpl
             * @description
             * __Default:__ `null`
             *
             * This option is available if you want to provide a custom `localStorage` or `sessionStorage` implementation.
             *
             * This option is NOT dynamically configurable. Must be an object that implements `setItem(key, value)`,
             * `getItem(key)` and `removeItem(key)`.
             *
             * ### Where can it be used?
             * - `DSCacheFactoryProvider.setCacheDefaults(options)`
             * - `DSCacheFactory(cacheId[, options])`
             */
            storageImpl: null,

            /**
             * @doc overview
             * @id disabled
             * @name disabled
             * @description
             * __Default:__ `false`
             *
             * This option disables or enables cache.
             *
             * This option is dynamically configurable. Must be `true` or `false`.
             *
             * ### Where can it be used?
             * - `DSCacheFactoryProvider.setCacheDefaults(options)`
             * - `DSCacheFactory(cacheId[, options])`
             * - `DSCache.setOptions(options[, strict])`
             *
             * or just use [DSCache#disable()](/documentation/api/angular-cache/DSCache.methods:disable) or
             * [DSCache#enable()](/documentation/api/angular-cache/DSCache.methods:enable).
             */
            disabled: false,

            /**
             * @doc overview
             * @id storagePrefix
             * @name storagePrefix
             * @description
             * __Default:__ `"angular-cache.caches."`
             *
             * This option determines the namespace for a cache when `storageMode` is `"localStorage"` or `"sessionStorage"`.
             * Setting this value to something like `"ac."` will save space when using WebStorage.
             *
             * This option is NOT dynamically configurable. Must be a string.
             *
             * ### Where can it be used?
             * - `DSCacheFactoryProvider.setCacheDefaults(options)`
             * - `DSCacheFactory(cacheId[, options])`
             */
            storagePrefix: 'angular-cache.caches.'
        };

        function Config() {}

        for (var option in defaults) {
            Config.prototype['$$' + option] = defaults[option];
        }

        module.exports = {
            Config: Config,
            defaults: defaults
        };

    }, {}],
    20: [function (require, module, exports) {
        (function (window, angular, undefined) {
            'use strict';

            angular.$$minErr = angular.$$minErr || function minErr(module) {
                return function () {
                    var code = arguments[0],
                        prefix = '[' + (module ? module + ':' : '') + code + '] ',
                        template = arguments[1],
                        templateArgs = arguments,
                        stringify = function (obj) {
                            if (typeof obj === 'function') {
                                return obj.toString().replace(/ \{[\s\S]*$/, '');
                            } else if (typeof obj === 'undefined') {
                                return 'undefined';
                            } else if (typeof obj !== 'string') {
                                return JSON.stringify(obj);
                            }
                            return obj;
                        },
                        message, i;

                    message = prefix + template.replace(/\{\d+\}/g, function (match) {
                        var index = +match.slice(1, -1),
                            arg;

                        if (index + 2 < templateArgs.length) {
                            arg = templateArgs[index + 2];
                            if (typeof arg === 'function') {
                                return arg.toString().replace(/ ?\{[\s\S]*$/, '');
                            } else if (typeof arg === 'undefined') {
                                return 'undefined';
                            } else if (typeof arg !== 'string') {
                                return angular.toJson(arg);
                            }
                            return arg;
                        }
                        return match;
                    });

                    message = message + '\nhttp://errors.angularjs.org/' + angular.version.full + '/' +
                        (module ? module + '/' : '') + code;
                    for (i = 2; i < arguments.length; i++) {
                        message = message + (i == 2 ? '?' : '&') + 'p' + (i - 2) + '=' +
                            encodeURIComponent(stringify(arguments[i]));
                    }

                    return new Error(message);
                };
            };


            angular.module('app')
                .provider('DSBinaryHeap', require('./DSBinaryHeap').DSBinaryHeapProvider);

            /**
             * @doc overview
             * @id angular-cache
             * @name Overview
             * @description
             * __Version:__ 3.1.1
             *
             * ## Install
             *
             * #### Bower
             * ```text
             * bower install angular-cache
             * ```
             *
             * Load `dist/angular-cache.js` or `dist/angular-cache.min.js` onto your web page after Angular.js.
             *
             * #### Npm
             * ```text
             * npm install angular-cache
             * ```
             *
             * Load `dist/angular-cache.js` or `dist/angular-cache.min.js` onto your web page after Angular.js. Angular-cache is
             * also consumable by Browserify and you should be able to `require('angular-cache')`. The `main` file is `src/index.js`.
             *
             * #### Manual download
             * Download angular-cache.3.1.1.js from the [Releases](https://github.com/jmdobry/angular-cache/releases)
             * section of the angular-cache GitHub project.
             *
             * ## Load into Angular
             * Your Angular app must depend on the module `"angular-data.DSCacheFactory"` in order to use angular-cache. Loading
             * angular-cache into your app allows you to inject the following:
             *
             * - `DSCacheFactory`
             * - `DSBinaryHeap`
             *
             * [DSCacheFactory](/documentation/api/api/DSCacheFactory) is a factory function that produces instances of
             * [DSCache](/documentation/api/api/DSCache), which is API compatible with caches produced by Angular's
             * [$cacheFactory](http://docs.angularjs.org/api/ng/service/$cacheFactory).
             *
             * [DSBinaryHeap](/documentation/api/api/DSBinaryHeap) is a priority queue implemented as a Binary Heap.
             *
             * Angular-cache is a dependency of [angular-data](/documentation/api/api/angular-data) and must be loaded before
             * angular-data if you are using angular-data.
             */
            angular.module('app')
                .provider('DSCacheFactory', require('./DSCacheFactory'));

        })(window, window.angular);

    }, {
        "./DSBinaryHeap": 1,
        "./DSCacheFactory": 18
    }],
    21: [function (require, module, exports) {
        module.exports = {
            /*!
             * Stringify a number.
             */
            stringifyNumber: function (number) {
                if (number && angular.isNumber(number)) {
                    return number.toString();
                }
                return number;
            },

            /*!
             * Return a hash of the keys in the given collection.
             */
            keySet: function (collection) {
                var keySet = {},
                    key;
                for (key in collection) {
                    if (collection.hasOwnProperty(key)) {
                        keySet[key] = key;
                    }
                }
                return keySet;
            },

            /*!
             * Return an array of the keys in the given collection
             */
            keys: function (collection) {
                var keys = [],
                    key;
                for (key in collection) {
                    if (collection.hasOwnProperty(key)) {
                        keys.push(key);
                    }
                }
                return keys;
            }
        };

    }, {}]
}, {}, [20]);
(function () {
    'use strict';

    angular.module('app')
        .service('dateParser', ['$locale', 'orderByFilter', function ($locale, orderByFilter) {

            this.parsers = {};

            var formatCodeToRegex = {
                'yyyy': {
                    regex: '\\d{4}',
                    apply: function (value) {
                        this.year = +value;
                    }
                },
                'yy': {
                    regex: '\\d{2}',
                    apply: function (value) {
                        this.year = +value + 2000;
                    }
                },
                'y': {
                    regex: '\\d{1,4}',
                    apply: function (value) {
                        this.year = +value;
                    }
                },
                'MMMM': {
                    regex: $locale.DATETIME_FORMATS.MONTH.join('|'),
                    apply: function (value) {
                        this.month = $locale.DATETIME_FORMATS.MONTH.indexOf(value);
                    }
                },
                'MMM': {
                    regex: $locale.DATETIME_FORMATS.SHORTMONTH.join('|'),
                    apply: function (value) {
                        this.month = $locale.DATETIME_FORMATS.SHORTMONTH.indexOf(value);
                    }
                },
                'MM': {
                    regex: '0[1-9]|1[0-2]',
                    apply: function (value) {
                        this.month = value - 1;
                    }
                },
                'M': {
                    regex: '[1-9]|1[0-2]',
                    apply: function (value) {
                        this.month = value - 1;
                    }
                },
                'dd': {
                    regex: '[0-2][0-9]{1}|3[0-1]{1}',
                    apply: function (value) {
                        this.date = +value;
                    }
                },
                'd': {
                    regex: '[1-2]?[0-9]{1}|3[0-1]{1}',
                    apply: function (value) {
                        this.date = +value;
                    }
                },
                'EEEE': {
                    regex: $locale.DATETIME_FORMATS.DAY.join('|')
                },
                'EEE': {
                    regex: $locale.DATETIME_FORMATS.SHORTDAY.join('|')
                }
            };

            function createParser(format) {
                var map = [],
                    regex = format.split('');

                angular.forEach(formatCodeToRegex, function (data, code) {
                    var index = format.indexOf(code);

                    if (index > -1) {
                        format = format.split('');

                        regex[index] = '(' + data.regex + ')';
                        format[index] = '$'; // Custom symbol to define consumed part of format
                        for (var i = index + 1, n = index + code.length; i < n; i++) {
                            regex[i] = '';
                            format[i] = '$';
                        }
                        format = format.join('');

                        map.push({
                            index: index,
                            apply: data.apply
                        });
                    }
                });

                return {
                    regex: new RegExp('^' + regex.join('') + '$'),
                    map: orderByFilter(map, 'index')
                };
            }

            this.parse = function (input, format) {
                if (!angular.isString(input) || !format) {
                    return input;
                }

                format = $locale.DATETIME_FORMATS[format] || format;

                if (!this.parsers[format]) {
                    this.parsers[format] = createParser(format);
                }

                var parser = this.parsers[format],
                    regex = parser.regex,
                    map = parser.map,
                    results = input.match(regex);

                if (results && results.length) {
                    var fields = {
                            year: 1900,
                            month: 0,
                            date: 1,
                            hours: 0
                        },
                        dt;

                    for (var i = 1, n = results.length; i < n; i++) {
                        var mapper = map[i - 1];
                        if (mapper.apply) {
                            mapper.apply.call(fields, results[i]);
                        }
                    }

                    if (isValid(fields.year, fields.month, fields.date)) {
                        dt = new Date(fields.year, fields.month, fields.date, fields.hours);
                    }

                    return dt;
                }
            };

            // Check if date is valid for specific month (and year for February).
            // Month: 0 = Jan, 1 = Feb, etc
            function isValid(year, month, date) {
                if (month === 1 && date > 28) {
                    return date === 29 && ((year % 4 === 0 && year % 100 !== 0) || year % 400 === 0);
                }

                if (month === 3 || month === 5 || month === 8 || month === 10) {
                    return date < 31;
                }

                return true;
            }
        }])
        .directive('renderModelAsHours', function () {
            return {
                require: 'ngModel',
                link: function (scope, element, attrs, ngModel) {
                    ngModel.$render = function () {
                        var parse = parseInt(ngModel.$modelValue, 10);
                        if (isNaN(parse)) {
                            element.val(ngModel.$modelValue);
                            return;
                        }
                        if (parse < 10) {
                            parse = '0' + parse;
                        }
                        element.val(parse);
                    };
                }
            };
        })
        .directive('timeDatePicker', [
            '$filter', '$sce', '$rootScope', '$parse',
            function ($filter, $sce, $rootScope, $parse) {
                var _dateFilter;
                _dateFilter = $filter('date');
                return {
                    restrict: 'AE',
                    replace: true,
                    scope: {
                        _modelValue: '=ngModel'
                    },
                    require: 'ngModel',
                    templateUrl: 'core/datetime/input.html',
                    link: function (scope, element, attrs, ngModel) {
                        var cancelFn, saveFn;
                        attrs.$observe('defaultMode', function (val) {
                            return scope._mode = val != null ? val : 'date';
                        });
                        attrs.$observe('displayMode', function (val) {
                            return scope._displayMode = val;
                        });
                        attrs.$observe('orientation', function (val) {
                            return scope._verticalMode = val === 'true';
                        });
                        attrs.$observe('displayTwentyfour', function (val) {
                            return scope._hours24 = (val != null) && val;
                        });
                        attrs.$observe('mindate', function (val) {
                            if ((val != null) && angular.isDate(val)) {
                                return scope.restrictions.mindate = val;
                            }
                        });
                        attrs.$observe('maxdate', function (val) {
                            if ((val != null) && angular.isDate(val)) {
                                return scope.restrictions.maxdate = val;
                            }
                        });
                        ngModel.$render = function () {
                            return scope.setDate(ngModel.$modelValue);
                        };
                        saveFn = $parse(attrs.onSave);
                        cancelFn = $parse(attrs.onCancel);
                        scope.save = function () {
                            scope._modelValue = scope.date;
                            ngModel.$setDirty();
                            return saveFn(scope.$parent, {
                                $value: scope.date
                            });
                        };
                        return scope.cancel = function () {
                            cancelFn(scope.$parent, {});
                            return ngModel.$render();
                        };
                    },
                    controller: [
                        '$scope',
                        function (scope) {
                            var i;
                            scope.restrictions = {
                                mindate: void 0,
                                maxdate: void 0
                            };
                            scope.setDate = function (newVal) {
                                scope.date = newVal != null ? new Date(newVal) : new Date();
                                scope.calendar._year = scope.date.getFullYear();
                                scope.calendar._month = scope.date.getMonth();
                                scope.clock._minutes = scope.date.getMinutes();
                                scope.clock._hours = scope._hours24 ? scope.date.getHours() : scope.date.getHours() % 12;
                                if (!scope._hours24 && scope.clock._hours === 0) {
                                    return scope.clock._hours = 12;
                                }
                            };
                            scope.display = {
                                fullTitle: function () {
                                    return _dateFilter(scope.date, 'EEEE d MMMM yyyy, h:mm a');
                                },
                                title: function () {
                                    if (scope._mode === 'date') {
                                        return _dateFilter(scope.date, (scope._displayMode === 'date' ? 'EEEE' : 'EEEE h:mm a'));
                                    } else {
                                        return _dateFilter(scope.date, 'MMMM d yyyy');
                                    }
                                },
                                "super": function () {
                                    if (scope._mode === 'date') {
                                        return _dateFilter(scope.date, 'MMM');
                                    } else {
                                        return '';
                                    }
                                },
                                main: function () {
                                    return $sce.trustAsHtml(scope._mode === 'date' ? _dateFilter(scope.date, 'd') : "" + (_dateFilter(scope.date, 'h:mm')) + "<small>" + (_dateFilter(scope.date, 'a')) + "</small>");
                                },
                                sub: function () {
                                    if (scope._mode === 'date') {
                                        return _dateFilter(scope.date, 'yyyy');
                                    } else {
                                        return _dateFilter(scope.date, 'HH:mm');
                                    }
                                }
                            };
                            scope.calendar = {
                                _month: 0,
                                _year: 0,
                                _months: (function () {
                                    var _i, _results;
                                    _results = [];
                                    for (i = _i = 0; _i <= 11; i = ++_i) {
                                        _results.push(_dateFilter(new Date(0, i), 'MMMM'));
                                    }
                                    return _results;
                                })(),
                                offsetMargin: function () {
                                    return new Date(this._year, this._month).getDay();
                                },
                                isVisible: function (d) {
                                    return new Date(this._year, this._month, d).getMonth() === this._month;
                                },
                                "class": function (d) {
                                    if ((scope.date != null) && new Date(this._year, this._month, d).getTime() === new Date(scope.date.getTime()).setHours(0, 0, 0, 0)) {
                                        return "selected";
                                    } else if (new Date(this._year, this._month, d).getTime() === new Date().setHours(0, 0, 0, 0)) {
                                        return "today";
                                    } else {
                                        return "";
                                    }
                                },
                                select: function (d) {
                                    var sets = scope.date.setFullYear(this._year, this._month, d);
                                    scope.save();
                                    return sets;
                                },
                                monthChange: function () {
                                    if ((this._year == null) || isNaN(this._year)) {
                                        this._year = new Date().getFullYear();
                                    }
                                    scope.date.setFullYear(this._year, this._month);
                                    if (scope.date.getMonth() !== this._month) {
                                        return scope.date.setDate(0);
                                    }
                                },
                                _incMonth: function (months) {
                                    this._month += months;
                                    while (this._month < 0 || this._month > 11) {
                                        if (this._month < 0) {
                                            this._month += 12;
                                            this._year--;
                                        } else {
                                            this._month -= 12;
                                            this._year++;
                                        }
                                    }
                                    return this.monthChange();
                                }
                            };
                            scope.clock = {
                                _minutes: 0,
                                _hours: 0,
                                _incHours: function (inc) {
                                    this._hours = scope._hours24 ? Math.max(0, Math.min(23, this._hours + inc)) : Math.max(1, Math.min(12, this._hours + inc));
                                    if (isNaN(this._hours)) {
                                        return this._hours = 0;
                                    }
                                },
                                _incMinutes: function (inc) {
                                    this._minutes = Math.max(0, Math.min(59, this._minutes + inc));
                                    if (isNaN(this._minutes)) {
                                        return this._minutes = 0;
                                    }
                                },
                                setAM: function (b) {
                                    if (b == null) {
                                        b = !this.isAM();
                                    }
                                    if (b && !this.isAM()) {
                                        return scope.date.setHours(scope.date.getHours() - 12);
                                    } else if (!b && this.isAM()) {
                                        return scope.date.setHours(scope.date.getHours() + 12);
                                    }
                                },
                                isAM: function () {
                                    return scope.date.getHours() < 12;
                                }
                            };
                            scope.$watch('clock._minutes', function (val, oldVal) {
                                if ((val != null) && val !== scope.date.getMinutes() && !isNaN(val) && (0 <= val && val <= 59)) {
                                    var sets = scope.date.setMinutes(val);
                                    sets = scope.date.setSeconds(0);
                                    scope.save();
                                    return sets;
                                }
                            });
                            scope.$watch('clock._hours', function (val) {
                                if ((val != null) && !isNaN(val)) {
                                    if (!scope._hours24) {
                                        if (val === 24) {
                                            val = 12;
                                        } else if (val === 12) {
                                            val = 0;
                                        } else if (!scope.clock.isAM()) {
                                            val += 12;
                                        }
                                    }
                                    if (val !== scope.date.getHours()) {
                                        var sets = scope.date.setHours(val);
                                        scope.save();
                                        return sets;
                                    }
                                }
                            });
                            scope.setNow = function () {
                                return scope.setDate();
                            };
                            scope._mode = 'date';
                            scope.modeClass = function () {
                                if (scope._displayMode != null) {
                                    scope._mode = scope._displayMode;
                                }
                                return "" + ((scope._verticalMode != null) && scope._verticalMode ? 'vertical ' : '') + (scope._displayMode === 'full' ? 'full-mode' : scope._displayMode === 'time' ? 'time-only' : scope._displayMode === 'date' ? 'date-only' : scope._mode === 'date' ? 'date-mode' : 'time-mode');
                            };
                            scope.modeSwitch = function () {
                                var _ref;
                                return scope._mode = (_ref = scope._displayMode) != null ? _ref : scope._mode === 'date' ? 'time' : 'date';
                            };
                            return scope.modeSwitchText = function () {
                                if (scope._mode === 'date') {
                                    return 'Clock';
                                } else {
                                    return 'Calendar';
                                }
                            };
                        }
                    ]
                };
            }
        ]).directive('timeDatePickerDialog', ng(function ($modal, dateFilter, dateParser, GLOBAL_CONFIG, $$rAF) {
            return {
                require: ['ngModel', '^form'],
                link: function (scope, element, attrs, ctrls) {
                    var ngModel = ctrls[0],
                        form = ctrls[1],
                        open = false;
                    ngModel.$render = function () {
                        element.val(dateFilter(ngModel.$modelValue, GLOBAL_CONFIG.date.format));
                    };

                    element.on('click focus', function (event) {
                        event.preventDefault();
                        if (open) {
                            return;
                        }
                        open = true;

                        $$rAF(function () {
                            $modal.open({
                                windowClass: 'modal-medium datepicker-pop',
                                popFrom: false,
                                inDirection: false,
                                outDirection: false,
                                fullScreen: false,
                                cantCloseWithBackdrop: true,
                                templateUrl: 'core/datetime/popup.html',
                                controller: ng(function ($scope) {
                                    $scope.date = ngModel.$modelValue;
                                    var $close = $scope.$close;
                                    $scope.$close = function () {
                                        $close();
                                    };
                                    $scope.select = function () {
                                        ngModel.$setViewValue($scope.date);
                                        ngModel.$render();
                                        $scope.$close();
                                    };

                                    $scope.$on('$destroy', function () {
                                        open = false;
                                    });
                                })
                            });
                        });
                    });

                    ngModel.$parsers.unshift(function parseDate(viewValue) {
                        if (!viewValue) {
                            ngModel.$setValidity('date', true);
                            return null;
                        } else if (angular.isDate(viewValue) && !isNaN(viewValue)) {
                            ngModel.$setValidity('date', true);
                            return viewValue;
                        } else if (angular.isString(viewValue)) {
                            var date = dateParser.parse(viewValue, dateFormat) || new Date(viewValue);
                            if (isNaN(date)) {
                                ngModel.$setValidity('date', false);
                                return undefined;
                            } else {
                                ngModel.$setValidity('date', true);
                                return date;
                            }
                        } else {
                            ngModel.$setValidity('date', false);
                            return undefined;
                        }
                    });
                }

            };
        }));
}());
(function () {
    'use strict';
    angular.module('app')
        .directive('repeatedText', ng(function (helpers) {
            return {
                require: 'ngModel',
                link: function (scope, element, attrs, ctrl) {

                    var worker = function (value, what) {

                            var test = false;

                            try {
                                if (what === 'list') {
                                    value = helpers.splitLines(value);
                                    value = _.uniq(value);
                                }
                                if (what === 'str') {
                                    if (angular.isArray(value)) {
                                        value = value.join('\n');
                                    }
                                }
                                test = true;

                            } catch (ignore) {}

                            ctrl.$setValidity('invalid', test);

                            return value;
                        },
                        parser = function (value) {
                            return worker(value, 'list');
                        },
                        formatter = function (value) {
                            return worker(value, 'str');
                        };

                    ctrl.$parsers.push(parser);
                    ctrl.$formatters.push(formatter);
                }
            };
        })).directive('checkNumeric', function () {
            return {
                require: ['ngModel', '^form'],
                link: function (scope, element, attrs, ctrls) {
                    var checkNumeric = function (value) {
                            var valid = !isNaN(parseInt(value, 10));
                            if (!valid) {
                                valid = !isNaN(parseFloat(value, 10));
                            }
                            return valid;
                        },
                        required = element.attr('required') === 'required';
                    ctrls[0].$parsers.unshift(function (value) {
                        var valid = checkNumeric(value),
                            out;
                        if (!required && (!valid || angular.isUndefined(value) || !value.length || !value.replace(/[^0-9+.]/g, ''))) {
                            valid = true;
                        }
                        ctrls[0].$setValidity('checkNumeric', valid);
                        // if it's valid, return the value to the model, 
                        // otherwise return undefined.
                        if (angular.isDefined(value)) {
                            out = value.replace(/[^0-9+.]/g, '');
                            if (out !== value) {
                                ctrls[0].$setViewValue(out);
                                ctrls[0].$render();
                            }
                            return out;
                        }

                        return valid ? value : undefined;
                    });
                }
            };
        }).constant('msdElasticConfig', {
            append: ''
        }).directive('msdElastic', [
            '$timeout', '$window', 'msdElasticConfig',
            function ($timeout, $window, config) {
                return {
                    require: 'ngModel',
                    restrict: 'A, C',
                    link: function (scope, element, attrs, ngModel) {

                        // cache a reference to the DOM element
                        var ta = element[0],
                            $ta = element;

                        // ensure the element is a textarea, and browser is capable
                        if (ta.nodeName !== 'TEXTAREA' || !$window.getComputedStyle) {
                            return;
                        }

                        // set these properties before measuring dimensions
                        $ta.css({
                            'overflow': 'hidden',
                            'overflow-y': 'hidden',
                            'word-wrap': 'break-word'
                        });

                        // force text reflow
                        var text = ta.value;
                        ta.value = '';
                        ta.value = text;

                        var append = attrs.msdElastic ? attrs.msdElastic.replace(/\\n/g, '\n') : config.append,
                            $win = angular.element($window),
                            mirrorInitStyle = 'position: absolute; top: -999px; right: auto; bottom: auto;' +
                            'left: 0; overflow: hidden; -webkit-box-sizing: content-box;' +
                            '-moz-box-sizing: content-box; box-sizing: content-box;' +
                            'min-height: 0 !important; height: 0 !important; padding: 0;' +
                            'word-wrap: break-word; border: 0;',
                            $mirror = angular.element('<textarea aria-hidden="true" tabindex="-1" ' +
                                'style="' + mirrorInitStyle + '"/>').data('elastic', true),
                            mirror = $mirror[0],
                            taStyle = getComputedStyle(ta),
                            resize = taStyle.getPropertyValue('resize'),
                            borderBox = taStyle.getPropertyValue('box-sizing') === 'border-box' ||
                            taStyle.getPropertyValue('-moz-box-sizing') === 'border-box' ||
                            taStyle.getPropertyValue('-webkit-box-sizing') === 'border-box',
                            boxOuter = !borderBox ? {
                                width: 0,
                                height: 0
                            } : {
                                width: parseInt(taStyle.getPropertyValue('border-right-width'), 10) +
                                    parseInt(taStyle.getPropertyValue('padding-right'), 10) +
                                    parseInt(taStyle.getPropertyValue('padding-left'), 10) +
                                    parseInt(taStyle.getPropertyValue('border-left-width'), 10),
                                height: parseInt(taStyle.getPropertyValue('border-top-width'), 10) +
                                    parseInt(taStyle.getPropertyValue('padding-top'), 10) +
                                    parseInt(taStyle.getPropertyValue('padding-bottom'), 10) +
                                    parseInt(taStyle.getPropertyValue('border-bottom-width'), 10)
                            },
                            minHeightValue = parseInt(taStyle.getPropertyValue('min-height'), 10),
                            heightValue = parseInt(taStyle.getPropertyValue('height'), 10),
                            minHeight = Math.max(minHeightValue, heightValue) - boxOuter.height,
                            maxHeight = parseInt(taStyle.getPropertyValue('max-height'), 10),
                            mirrored,
                            active,
                            copyStyle = ['font-family',
                                'font-size',
                                'font-weight',
                                'font-style',
                                'letter-spacing',
                                'line-height',
                                'text-transform',
                                'word-spacing',
                                'text-indent'
                            ];

                        // exit if elastic already applied (or is the mirror element)
                        if ($ta.data('elastic')) {
                            return;
                        }

                        // Opera returns max-height of -1 if not set
                        maxHeight = maxHeight && maxHeight > 0 ? maxHeight : 9e4;

                        // append mirror to the DOM
                        if (mirror.parentNode !== document.body) {
                            angular.element(document.body).append(mirror);
                        }

                        // set resize and apply elastic
                        $ta.css({
                            'resize': (resize === 'none' || resize === 'vertical') ? 'none' : 'horizontal'
                        }).data('elastic', true);

                        /*
                         * methods
                         */

                        function initMirror() {
                            var mirrorStyle = mirrorInitStyle;

                            mirrored = ta;
                            // copy the essential styles from the textarea to the mirror
                            taStyle = getComputedStyle(ta);
                            angular.forEach(copyStyle, function (val) {
                                mirrorStyle += val + ':' + taStyle.getPropertyValue(val) + ';';
                            });
                            mirror.setAttribute('style', mirrorStyle);
                        }

                        function adjust() {
                            var taHeight,
                                taComputedStyleWidth,
                                mirrorHeight,
                                width,
                                overflow;

                            if (mirrored !== ta) {
                                initMirror();
                            }

                            // active flag prevents actions in function from calling adjust again
                            if (!active) {
                                active = true;

                                mirror.value = ta.value + append; // optional whitespace to improve animation
                                mirror.style.overflowY = ta.style.overflowY;

                                taHeight = ta.style.height === '' ? 'auto' : parseInt(ta.style.height, 10);

                                taComputedStyleWidth = getComputedStyle(ta).getPropertyValue('width');

                                // ensure getComputedStyle has returned a readable 'used value' pixel width
                                if (taComputedStyleWidth.substr(taComputedStyleWidth.length - 2, 2) === 'px') {
                                    // update mirror width in case the textarea width has changed
                                    width = parseInt(taComputedStyleWidth, 10) - boxOuter.width;
                                    mirror.style.width = width + 'px';
                                }

                                mirrorHeight = mirror.scrollHeight;

                                if (mirrorHeight > maxHeight) {
                                    mirrorHeight = maxHeight;
                                    overflow = 'scroll';
                                } else if (mirrorHeight < minHeight) {
                                    mirrorHeight = minHeight;
                                }
                                mirrorHeight += boxOuter.height;
                                ta.style.overflowY = overflow || 'hidden';

                                if (taHeight !== mirrorHeight) {
                                    ta.style.height = mirrorHeight + 'px';
                                    scope.$emit('elastic:resize', $ta);
                                }

                                // small delay to prevent an infinite loop
                                $timeout(function () {
                                    active = false;
                                }, 1, false);

                            }
                        }

                        function forceAdjust() {
                            active = false;
                            adjust();
                        }

                        /*
                         * initialise
                         */

                        // listen
                        if ('onpropertychange' in ta && 'oninput' in ta) {
                            // IE9
                            ta['oninput'] = ta.onkeyup = adjust;
                        } else {
                            ta['oninput'] = adjust;
                        }

                        $win.bind('resize', forceAdjust);

                        scope.$watch(function () {
                            return ngModel.$modelValue;
                        }, function (newValue) {
                            forceAdjust();
                        });

                        scope.$on('elastic:adjust', function () {
                            initMirror();
                            forceAdjust();
                        });

                        $timeout(adjust);

                        /*
                         * destroy
                         */

                        scope.$on('$destroy', function () {
                            $mirror.remove();
                            $win.unbind('resize', forceAdjust);
                        });
                    }
                };
            }
        ]).run(ng(function (formInputTypes, GLOBAL_CONFIG, helpers) {
            $.extend(formInputTypes, {
                _SelectBox: function (info) {

                    if (!angular.isDefined(info.config.ui.specifics.searchEnabled)) {
                        if (info.config.choices.length < 10) {
                            info.config.ui.specifics.searchEnabled = false;
                        } else {
                            info.config.ui.specifics.searchEnabled = true;
                        }
                    }

                    if (info.config.choices.length && (info.config.ui.specifics && info.config.ui.specifics.translatedChoices !== false)) {
                        info.config.ui.specifics.translatedChoices = [];
                        angular.forEach(info.config.choices, function (value) {
                            // @todo this might cause problems when config.choices = some other list is applied trough the lifecycle
                            // the choices will not be re-parsed to translatedChoices
                            // this code will only run upon directive initilization
                            var hasit = helpers.getProperty(GLOBAL_CONFIG.fields.translateChoices, [info.config._maker_, info.config.code_name, value]);
                            if (angular.isUndefined(hasit)) {
                                hasit = value;
                            }
                            info.config.ui.specifics.translatedChoices.push({
                                key: value,
                                name: hasit
                            });
                        });
                    }

                    return 'select';
                },
                SuperStringProperty: function (info) {
                    var config = info.config;


                    if (config.ui.attrs.type === undefined) {
                        config.ui.attrs.type = 'text';
                    }

                    if (config.choices) {
                        if (config.repeated) {
                            return this._SuperStringRepeated(info);
                        }
                        if (info.config.ui.attrs['repeated-text'] !== undefined) {
                            delete info.config.ui.attrs['repeated-text'];
                        }
                        return this._SelectBox(info);
                    }

                    if (config.repeated) {
                        config.ui.attrs['repeated-text'] = '';
                        return this.SuperTextProperty(info);
                    }

                    return 'string';
                },
                SuperFloatProperty: function (info) {
                    var config = info.config;

                    if (config.choices) {
                        return this._SelectBox(info);
                    }
                    config.ui.attrs['check-numeric'] = '';
                    return this.SuperStringProperty(info);
                },
                SuperIntegerProperty: function (info) {
                    var config = info.config;

                    if (config.choices) {
                        return this._SelectBox(info);
                    }

                    config.ui.attrs['check-numeric'] = '';

                    return this.SuperFloatProperty(info);
                },
                SuperDecimalProperty: function (info) {
                    var config = info.config;
                    if (config.choices) {
                        return this._SelectBox(info);
                    }
                    config.ui.attrs['check-numeric'] = '';
                    return this.SuperFloatProperty(info);
                },
                _SuperStringRepeated: function (info) {
                    var select = {};
                    info.config.ui.specifics.select = select;
                    info.config._groupable = true;
                    return 'select_multiple';
                },
                SuperTextProperty: function (info) {
                    if (info.config.repeated) {
                        info.config.ui.attrs['repeated-text'] = '';
                    }
                    if (info.config.ui.specifics.autoGrow === undefined || info.config.ui.specifics.autoGrow) {
                        info.config.ui.attrs['msd-elastic'] = '';
                    }
                    return 'text';
                }
            });
        }));
}());
(function () {
    'use strict';
    angular.module('app')
        .filter('humanized', ng(function ($filter) {
            return function (str) {
                var inflector = $filter('inflector'),
                    human = inflector(str, 'humanize');
                human = human.toLowerCase();
                return _.string.capitalize(human);
            };
        }))
        .run(ng(function (helpers, modals, $modal, GLOBAL_CONFIG, snackbar) {
            if (!helpers.fields) {
                helpers.fields = {};
            }
            if (!helpers.form) {
                helpers.form = {};
            }
            $.extend(helpers.fields, {
                isFieldset: function (field) {
                    return (field.is_structured || ((_.string.contains(field.type, 'KeyProperty')) && field.repeated) || field.ui.fieldset);
                },
                sorter: function (prev, next) {
                    var p1 = parseInt(prev.name, 10),
                        p2 = parseInt(next.name, 10);
                    if (isNaN(p1)) {
                        p1 = 999999;
                    }
                    if (isNaN(p2)) {
                        p2 = 999999;
                    }
                    return p1 - p2;
                },
                applyGlobalConfig: function (config) {
                    if (angular.isUndefined(config.ui.help) && angular.isDefined(GLOBAL_CONFIG.fields.help[config._maker_])) {
                        config.ui.help = GLOBAL_CONFIG.fields.help[config._maker_][config.code_name];
                    }

                    if (angular.isUndefined(config.ui.emptyHelp) && angular.isDefined(GLOBAL_CONFIG.fields.emptyHelp[config._maker_])) {
                        config.ui.emptyHelp = GLOBAL_CONFIG.fields.emptyHelp[config._maker_][config.code_name];
                    }

                    if (angular.isUndefined(config.ui.label) && angular.isDefined(GLOBAL_CONFIG.fields.label[config._maker_])) {
                        config.ui.label = GLOBAL_CONFIG.fields.label[config._maker_][config.code_name];
                    }
                },
                utils: {
                    attrs: function (config) {
                        var defaults = this.defaultAttrs(config),
                            extra = this.extraAttrs(config),
                            attrs = [];

                        angular.extend(defaults, extra);

                        angular.forEach(defaults, function (value, key) {
                            attrs.push(key + (value ? '="' + value + '"' : ''));
                        });

                        return attrs.join(' ');
                    },
                    defaultAttrs: function (config) {
                        var attrs = {},
                            writableCompiled;
                        if (config.max_size) {
                            attrs['ng-maxlength'] = 'config.max_size';
                        }

                        if (config.ui.pattern !== undefined) {
                            attrs['ng-pattern'] = config.pattern;
                        }

                        if (angular.isString(config.required)) {
                            attrs['ng-required'] = config.required;
                        } else {
                            attrs['ng-required'] = 'config.required';
                        }
                        attrs['ng-model'] = config.ui.args;
                        attrs.placeholder = config.ui.placeholder;

                        if (!angular.isArray(config.ui.writable)) {
                            attrs['ng-disabled'] = '!' + config.ui.writable;
                            config.ui.writableCompiled = config.ui.writable;
                        } else {
                            writableCompiled = config.ui.model + '.ui.rule.field' + $.map(config.ui.writable,
                                function (item) {
                                    return "['" + helpers.addslashes(item) + "']";
                                }).join('') + '.writable';

                            attrs['ng-disabled'] = '!' + writableCompiled;

                            config.ui.writableCompiled = writableCompiled;
                        }

                        if (attrs.readonly) {
                            delete attrs['ng-disabled'];
                        }

                        return attrs;
                    },
                    extraAttrs: function (config) {
                        return config.ui.attrs;
                    },
                    label: function (config) {
                        var use = '{{config.ui.label}}';
                        if (config.ui.label === undefined) {
                            use = '{{config.ui.autoLabel|humanized}}';
                        }
                        return use;
                    }
                }
            });
            $.extend(helpers.form, {
                wakeUp: function (form, dirty) {
                    var happend = false;
                    angular.forEach(form, function (formElement) {
                        if (angular.isObject(formElement) && formElement.hasOwnProperty('$valid') && !formElement.$valid && angular.isFunction(formElement.$setViewValue)) {
                            formElement.$setViewValue(formElement.$viewValue !== undefined ? formElement.$viewValue : '');
                            formElement.$setDirty();
                            formElement.$setTouched();
                            if (dirty) {
                                form.$setDirty();
                            }

                            happend = true;
                        }
                    });

                    return happend;
                },
                setDirty: function () {
                    if (this.container && this.container.form) {
                        this.container.form.$setDirty();
                    }
                },
                setPristine: function () {
                    if (this.container && this.container.form) {
                        this.container.form.$setPristine();
                    }
                },
                validate: function () {
                    var form = this.container.form;
                    if (!form.$valid) {
                        helpers.form.wakeUp(form);
                        this.$broadcast('invalidForm');
                        snackbar.showK('actionFailedCheckForm');
                        return false;
                    }
                    return true;
                },
                leave: function (cb) {
                    var form = this.container.form;
                    if (form.$pristine) {
                        return cb();
                    }
                    modals.confirm('discard', cb);
                }
            });
        }))
        .directive('formBuilder', ng(function ($compile, underscoreTemplate, modelsMeta) {
            return {
                restrict: 'A',
                require: '^form',
                templateUrl: 'core/fields/builder.html',
                scope: true,
                transclude: true,
                controller: ng(function ($scope, $element, $attrs) {
                    $scope.configurations = $scope.$eval($attrs.formBuilder);
                })
            };
        }))
        .directive('formInput', ng(function ($compile, underscoreTemplate,
            formInputTypes, helpers, GLOBAL_CONFIG) {

            var types = formInputTypes,
                utils = helpers.fields.utils;

            return {
                restrict: 'A',
                require: '^form',
                scope: true,
                transclude: true,
                link: function (scope, element, attrs, ctrl) {

                    var run = function () {
                        var supplied_config = scope.$eval(attrs.formInput),
                            name,
                            label = null,
                            config,
                            tpl,
                            template,
                            info,
                            constructor;

                        if (!angular.isObject(supplied_config)) {
                            console.warn('Config provided is not object for element: ', element);
                            return;
                        }

                        name = supplied_config.code_name;

                        // use backend defined label if was provided, otherwise the label will be humanized
                        if (supplied_config.verbose_name !== null && supplied_config.verbose_name !== undefined) {
                            label = supplied_config.verbose_name;
                        } else {
                            label = name;
                        }

                        if (!name) {
                            console.error('Your field config', supplied_config, 'has no name defined defined. element: ', element);
                            return;
                        }

                        config = {
                            ui: { // root config for entire config, upper structure is ndb property definition
                                args: 'args.' + name,
                                parentArgs: 'args',
                                rootScope: 'rootScope', // pointer to rootScope that should be considered
                                model: 'entity',
                                autoLabel: label,
                                directiveScope: function () {
                                    return scope;
                                },
                                specifics: {}, // used for property specific configurations
                                systemName: name,
                                name: name,
                                form: {
                                    root: ctrl,
                                    field: function () {
                                        return this.root[config.ui.name];
                                    },
                                    hasErrors: function () {
                                        if (!this.field()) {
                                            return false;
                                        }
                                        return Object.keys(this.field().$error).length;
                                    },
                                    messages: function () {
                                        if (!this.field()) {
                                            return false;
                                        }
                                        return ((this.field().$dirty && this.hasErrors()) ? this.field().$error : false) || config.ui;
                                    },
                                    shouldShowMessages: function () {
                                        if (config.ui.hideMessages) {
                                            return false;
                                        }
                                        return true;
                                    }
                                },
                                writable: [name],
                                path: undefined,
                                realPath: undefined,
                                attrs: {}
                            }
                        };
                        helpers.mergeDeep(supplied_config, config);
                        config = supplied_config;

                        if (angular.isFunction(config.ui.init)) {
                            constructor = config.ui.init;
                            config.ui.init = undefined;
                        }

                        if (!config.ui.init) {
                            config.ui.init = {
                                callbacks: [],
                                add: function (name, callback) {
                                    var theObj = null;
                                    angular.forEach(this.callbacks, function (obj, i) {
                                        if (angular.isDefined(obj[name])) {
                                            theObj = obj;
                                        }
                                    });
                                    if (theObj !== null) {
                                        theObj[name] = callback;
                                    } else {
                                        theObj = {};
                                        theObj[name] = callback;
                                        this.callbacks.push(theObj);
                                    }
                                }
                            };
                        }

                        if (constructor) {
                            config.ui.init.add('init', constructor);
                        }

                        if (!angular.isDefined(config.ui.path)) {
                            config.ui.path = [name];
                        }

                        if (angular.isArray(config.ui.writable)) {
                            config.ui.writable = angular.copy(config.ui.path);
                        }

                        if (!angular.isDefined(config.ui.realPath)) {
                            config.ui.realPath = [name];
                        }

                        helpers.fields.applyGlobalConfig(config);

                        if (types[config.type] !== undefined) {
                            // reference main locals to type builder
                            info = {
                                config: config,
                                element: element,
                                scope: scope,
                                attrs: attrs
                            };
                            tpl = types[config.type](info);

                            // compiled variables for the template
                            config.ui.compiled = {
                                attrs: utils.attrs(config),
                                label: utils.label(config)
                            };
                            angular.forEach(config.ui.init.callbacks, function (obj) {
                                angular.forEach(obj, function (callback) {
                                    callback(info);
                                });
                            });

                            if (config.ui.render === false) {
                                return;
                            }

                            template = underscoreTemplate.get(angular.isDefined(config.ui.template) ? config.ui.template : 'core/fields/' + tpl + '.html')({
                                config: config
                            });

                            scope.config = config;
                            element.html(template);
                            $compile(element.contents())(scope);

                        } else {
                            /* console.warn('Field type: ' + config.type +
                                ' is not supported.'); */
                        }

                        scope.$on('$destroy', function () {
                            config.ui.directiveScope = undefined;
                            config.ui.form = undefined;
                        });

                    };

                    run();

                }

            };
        })).directive('compatibilityMaker', ng(function (modelsUtil) {
            return {
                restrict: 'A',
                link: function (scope, element, attrs, ctrl) {
                    var fn = function () {
                        var newval = scope.$eval(attrs.compatibilityMaker),
                            stringified = modelsUtil.argumentsToJson(newval);
                        element.val(stringified);
                    };
                    scope.$watch(attrs.compatibilityMaker, fn);
                    scope.$on('ngUploadSubmit', fn);

                }
            };
        })).factory('formInputTypes', ng(function () {

            var formInputTypes = {};

            return formInputTypes;

        })).directive('fastNgChange', ng(function ($parse, $mdUtil) {
            return {
                priority: 1,
                link: function (scope, element, attrs) {
                    var fn = $parse(attrs.fastNgChange),
                        prev = element.val(),
                        change = $mdUtil.debounce(function (ev) {
                            var cval = element.val();
                            if (prev !== cval) {
                                prev = cval;
                                fn(scope, {
                                    $event: ev
                                });
                            }
                        }, 100, scope, true);
                    element.on('change keydown', change);
                    scope.$on('$destroy', function () {
                        element.off('change keydown', change);
                    });
                }
            };
        })).directive('fastNgModel', ng(function ($parse, $mdUtil) {
            return {
                priority: -1,
                link: function (scope, element, attrs) {
                    var model = $parse(attrs.fastNgModel),
                        change = $mdUtil.debounce(function (ev) {
                            model.assign(scope, element.val());
                        }, 100, scope, true);
                    element.on('keyup', change);
                    scope.$on('$destroy', function () {
                        element.off('keyup', change);
                    });
                }
            };
        }));
}());
(function () {
    'use strict';
    angular.module('app')
        .directive('validFile', function () {
            return {
                require: 'ngModel',
                link: function (scope, el, attrs, ngModel) {
                    el.bind('change', function () {
                        scope.$apply(function () {
                            ngModel.$setViewValue(el.val());
                            ngModel.$render();
                        });
                    });
                }
            };
        })
        .directive('jsonOnly', function () {
            return {
                require: 'ngModel',
                link: function (scope, element, attrs, ctrl) {
                    var worker = function (value, what) {
                            var test = false;
                            try {
                                value = angular[what](value);
                                test = true;
                            } catch (ignore) {}

                            ctrl.$setValidity('jsonOnly', test);

                            return value;
                        },
                        parser = function (value) {
                            return worker(value, 'fromJson');
                        },
                        formatter = function (value) {
                            return worker(value, 'toJson');
                        };

                    ctrl.$parsers.push(parser);
                    ctrl.$formatters.push(formatter);
                }
            };
        })
        .directive('generateUploadUrl', ng(function (endpoint, $rootScope) {
            return {
                restrict: 'A',
                require: '^form',
                link: function (scope, element, attrs, ctrl) {

                    var that = element,
                        form = that.parents('form:first'),
                        change = function () {

                            if (!that.val()) {
                                return false;
                            }

                            endpoint.post('blob_upload_url', '11', {
                                upload_url: endpoint.url
                            }).then(function (response) {
                                form.attr('action', response.data.upload_url);
                                ctrl.$setDirty();
                            });
                        },
                        reset = function ($event, content) {
                            form.attr('action', endpoint.url);
                            that.val('');
                        };

                    if (!form.length) {
                        console.error('Directive generateUploadUrl demands explicit <form> tag');
                        return false;
                    }

                    $(element).on('change', change);

                    scope.$on('$destroy', function () {
                        $(element).off('change', change);
                    });

                    scope.$on('ngUploadComplete', reset);
                    scope.$on('ngUploadCompleteError', change);
                }
            };
        })).directive('submitIfFiles', ng(function ($parse, helpers) {
            return {
                require: '^form',
                link: function (scope, element, attrs, ctrl) {
                    var form = element.parents('form:first'),
                        files,
                        submit = $parse(attrs.submitIfFiles),
                        complete = $parse(attrs.submitIfFilesNoComplete),
                        check = $parse(attrs.submitIf),
                        nativeSubmit = $parse(attrs.submitNative),
                        execute,
                        click = function () {
                            var promise,
                                isNative,
                                thingsHappened = helpers.form.wakeUp(ctrl, true);
                            if (thingsHappened) {
                                if (!scope.$$phase) {
                                    scope.$apply();
                                }
                            }
                            if (check && !check(scope)) {
                                return false;
                            }
                            isNative = nativeSubmit(scope);
                            files = form.find('input[type="file"]');
                            execute = false;
                            if (files.length) {
                                files.each(function () {
                                    if ($(this).val()) {
                                        execute = true;
                                        return false;
                                    }
                                });
                            }
                            if (isNative) {
                                if (execute) {
                                    form.trigger('submit');
                                    return false;
                                }
                            }
                            promise = submit(scope, {
                                dontShowMessage: execute
                            });
                            if (promise && angular.isObject(promise) && promise.then) {
                                promise.then(function () {
                                    if (execute) {
                                        form.trigger('submit');
                                        return false;
                                    }
                                    complete(scope);
                                });
                            }

                            scope.$apply();
                        };

                    element.on('click', click);
                    scope.$on('$destroy', function () {
                        element.off('click', click);
                    });

                }
            };
        })).directive('submitIfValid', ng(function ($parse) {
            return {
                require: '^form',
                link: function (scope, element, attrs, ctrl) {
                    var form = element.parents('form:first'),
                        check = $parse(attrs.submitIfValid),
                        click = function (e) {
                            if (check(scope)) {
                                form.submit();
                            }
                            return e.preventDefault();
                        };

                    element.on('click', click);
                    scope.$on('$destroy', function () {
                        element.off('click', click);
                    });

                }
            };
        })).directive('showNumberOfSelectedFiles', function () {
            return {
                restrict: 'A',
                link: function (scope, element, attrs) {
                    var root = element.parents('.fake-button:first'),
                        target = root.find(attrs.showNumberOfSelectedFiles),
                        totalText = target.text(),
                        change = function () {
                            setTimeout(function () {
                                var files = element.prop('files');
                                if (files && files.length) {
                                    target.css('display', 'inline');
                                    target.text(totalText.replace(':total', files.length));
                                } else {
                                    target.hide();
                                }
                            }, 200);

                        };
                    element.bind('change', change);
                    change();
                    scope.$on('ngUploadComplete', change);
                    scope.$on('ngUploadCompleteError', change);
                    scope.$on('$destroy', function () {
                        element.unbind('change', change);
                    });
                }
            };
        }).run(ng(function (formInputTypes, underscoreTemplate, $timeout, $parse,
            endpoint, modelsMeta, models, $q, $filter, $modal, helpers,
            errorHandling, modals, GLOBAL_CONFIG, snackbar) {

            $.extend(formInputTypes, {
                SuperBooleanProperty: function (info) {
                    info.config.required = false;
                    if (!info.config.ui.specifics || angular.isUndefined(info.config.ui.specifics.type)) {
                        info.config.ui.specifics.type = 'checkbox';
                    }
                    return 'boolean';
                },
                SuperVirtualKeyProperty: function (info) {
                    return this.SuperKeyProperty(info);
                },
                _SuperKeyPropertyRepeated: function (info) {
                    var select = {};
                    info.config.ui.specifics.select = select;
                    return 'select_multiple';
                },
                SuperKeyProperty: function (info) {
                    if (info.config.searchable === false) {
                        return this.SuperStringProperty(info);
                    }
                    var config = info.config,
                        template = 'select_async',
                        defaults = {
                            cache: {
                                query: {
                                    '24': true,
                                    '12': true,
                                    '13': true
                                },
                                type: {
                                    '12': 'local',
                                    '17': 'local',
                                    'default': 'memory'
                                }
                            },
                            finder: {
                                '24': true
                            },
                            grouping: {},
                            view: {
                                'default': function (result) {
                                    if (!result) {
                                        return '';
                                    }
                                    return result.name;
                                }
                            },
                            init: {
                                '13': function (info) {
                                    info.scope.$watch(info.config.ui.parentArgs +
                                        '.country',
                                        function (neww, old) {
                                            if (neww !== old) {
                                                var args = info.scope.$eval(info.config.ui.parentArgs);
                                                args.region = null;
                                                info.config.ui.specifics.initial(); // refresh results
                                            }
                                        });
                                }
                            },
                            queryFilter: {
                                '24': function (term, searchArguments) {
                                    var searchDefaults = angular.copy(searchArguments.search['default']),
                                        args = {
                                            search: searchDefaults
                                        };
                                    if (term) {
                                        args.search.filters.push({
                                            field: 'name',
                                            operator: '==',
                                            value: term
                                        });
                                    }
                                    return args;
                                },
                                '17': function (term, searchArguments) {
                                    var searchDefaults = {
                                            search: {
                                                filters: [{
                                                    value: true,
                                                    field: 'active',
                                                    operator: '=='
                                                }],
                                                orders: [{
                                                    field: 'name',
                                                    operator: 'asc'
                                                }],
                                            }
                                        },
                                        argument = searchDefaults.search;

                                    if (config.code_name === 'uom') {
                                        argument.filters.unshift({
                                            value: 'Currency',
                                            field: 'measurement',
                                            operator: '!='
                                        });

                                        argument.orders = [{
                                            field: 'measurement',
                                            operator: 'asc'
                                        }, {
                                            field: 'key',
                                            operator: 'asc'
                                        }];
                                    }

                                    if (config.code_name === 'currency') {
                                        argument.filters.push({
                                            value: 'Currency',
                                            field: 'measurement',
                                            operator: '=='
                                        });
                                    }

                                    return searchDefaults;

                                },
                                '13': function (term, searchArguments) {
                                    var args = info.scope.$eval(info.config.ui.parentArgs);
                                    if ((args && args.country)) {
                                        return {
                                            search: {
                                                ancestor: args.country,
                                                filters: [{
                                                    value: true,
                                                    field: 'active',
                                                    operator: '=='
                                                }],
                                                orders: [{
                                                    field: 'name',
                                                    operator: 'asc'
                                                }],
                                            }
                                        };
                                    }
                                    return false;
                                }
                            }
                        },
                        init,
                        model = models[config.kind],
                        search = {},
                        args,
                        opts = {},
                        override = config.ui.specifics.override || {},
                        repackMemory = function () {
                            config.ui.specifics._mapEntities = {};
                            angular.forEach(config.ui.specifics.entities, function (val) {
                                config.ui.specifics._mapEntities[val.key] = 1;
                            });
                        },
                        actionArguments = (config.kind ? modelsMeta.getActionArguments(config.kind, 'search') : {}),
                        response = function (response) {
                            config.ui.specifics.entities = response.data.entities;
                            repackMemory();
                            return config.ui.specifics.entities;
                        },
                        findArgs,
                        finder,
                        initialDefer = $q.defer(),
                        initialPromise = initialDefer.promise;

                    if (config.repeated) {
                        config.ui.fieldset = true;
                    }

                    config.ui.specifics.view = function (result) {
                        var fn = defaults.view[config.kind];
                        if (!fn) {
                            fn = defaults.view['default'];
                        }
                        if (override.view) {
                            fn = override.view;
                        }
                        return fn(result);
                    };
                    init = defaults.init[config.kind];
                    if (override.init) {
                        init = override.init;
                    }
                    if (angular.isDefined(init)) {
                        init(info);
                    }
                    $.extend(search, config.ui.specifics.search);
                    config.ui.specifics.search = search;

                    if (angular.isFunction(config.ui.specifics.entities)) {
                        config.ui.specifics.getEntities = config.ui.specifics.entities;
                        config.ui.specifics.entities = config.ui.specifics.entities();
                    }

                    if (angular.isUndefined(config.ui.specifics.entities)) {
                        config.ui.specifics.entities = [];
                    }


                    if (angular.isUndefined(config.ui.specifics.grouping)) {
                        config.ui.specifics.grouping = defaults.grouping[config.kind];
                    }

                    repackMemory();

                    finder = defaults.finder[config.kind];
                    if (override.finder) {
                        finder = override.finder;
                    }

                    config.ui.specifics.search.ready = initialPromise;

                    if (model && !config.ui.specifics.getEntities) {
                        if (model.actions.search) {
                            opts.cache = defaults.cache.query[config.kind];
                            opts.cacheType = defaults.cache.type[config.kind] || defaults.cache.type['default'];
                            if (override.cache && angular.isDefined(override.cache.query)) {
                                opts.cache = override.cache.query;
                            }
                            if (override.cache && angular.isDefined(override.cache.type)) {
                                opts.cacheType = override.cache.type;
                            }
                            config.ui.specifics.initial = function () {
                                args = defaults.queryFilter[config.kind];
                                if (override.queryFilter) {
                                    args = override.queryFilter;
                                }
                                if (!args) {
                                    args = actionArguments.search['default'];
                                } else {
                                    findArgs = args;
                                    args = findArgs(null, actionArguments);
                                    if (finder) {
                                        config.ui.specifics.search.find = function (term) {
                                            return model.actions.search(findArgs(term, actionArguments), opts).then(function (response) {
                                                var entities = response.data.entities;
                                                angular.forEach(entities, function (ent) {
                                                    if (angular.isUndefined(config.ui.specifics._mapEntities[ent.key])) {
                                                        config.ui.specifics._mapEntities[ent.key] = 1;
                                                        config.ui.specifics.entities.push(ent);
                                                    }
                                                });
                                            });
                                        };
                                    }
                                    config.ui.specifics.search.missing = function (id) {
                                        if (id === null || id === undefined || !id.length) {
                                            return;
                                        }
                                        var selectedIsArray = angular.isArray(id);
                                        model.actions.search({
                                            search: {
                                                keys: (selectedIsArray ? id : [id])
                                            }
                                        }, {
                                            cache: true
                                        }).then(function (response) {
                                            var fetchedEntities = response.data.entities;
                                            if (!selectedIsArray) {
                                                if (angular.isUndefined(config.ui.specifics._mapEntities[id])) {
                                                    config.ui.specifics._mapEntities[id] = 1;
                                                    config.ui.specifics.entities.unshift(response.data.entities[0]);
                                                }
                                            } else {
                                                angular.forEach(fetchedEntities, function (ent) {
                                                    if (angular.isUndefined(config.ui.specifics._mapEntities[ent.key])) {
                                                        config.ui.specifics._mapEntities[ent.key] = 1;
                                                        config.ui.specifics.entities.push(ent);
                                                    }
                                                });
                                            }
                                        });
                                    };
                                }
                                return model.actions.search(args, opts).then(response);
                            };
                            config.ui.specifics.initial().then(function () {
                                initialDefer.resolve();
                            });
                        }
                    }
                    info.scope.$on('$destroy', function () {
                        config.ui.specifics.entities = [];
                        config.ui.specifics._mapEntities = {};
                    });
                    config.ui.specifics.async = true;
                    if (config.repeated) {
                        template = this._SuperKeyPropertyRepeated(info);
                    }
                    (function () {
                        var select = config.ui.specifics.select || config.ui.specifics.search;
                        if (info.config.kind === '24') {
                            select.init = function (select, scope, element, attrs, ctrls) {
                                var splitout = function (entities) {
                                    angular.forEach(entities, function (ent) {
                                        ent.leafname = _.last(ent.name.split(' / '));
                                    });
                                };
                                select.afterClose = function () {
                                    select.product_categories.resetToTop();
                                };
                                select.openTemplate = 'core/select/product_categories.html';
                                select.windowClass = 'category-modal';
                                select.product_categories = {
                                    children: [],
                                    mapped: {},
                                    top: [],
                                    isLeaf: function (item) {
                                        return $.inArray('visible', item.state) !== -1;
                                    },
                                    resetToTop: function () {
                                        select.product_categories.children = [];
                                        select.product_categories.mapped = {};
                                    },
                                    next: function (item) {
                                        var newFilter = {
                                            search: {
                                                options: {limit: 1000},
                                                orders: [{
                                                    operator: 'asc',
                                                    field: 'name'
                                                }],
                                                filters: [{
                                                    value: 'indexable',
                                                    operator: '==',
                                                    field: 'state'
                                                }, {
                                                    value: 'None',
                                                    operator: '==',
                                                    field: 'parent_record'
                                                }]
                                            }
                                        };
                                        newFilter.search.filters[1].value = item.key;
                                        models['24'].actions.search(newFilter).then(function (response) {
                                            var entities = response.data.entities,
                                                child = {
                                                    item: item
                                                },
                                                existing = select.product_categories.mapped[item.key];
                                            splitout(entities);
                                            if (existing) {
                                                child = existing;
                                            }
                                            child.visible = true;
                                            if (entities.length) {
                                                child.items = entities;
                                                select.product_categories.children.push(child);
                                                select.product_categories.mapped[item.key] = child;
                                            } else {
                                                select.select(item);
                                                select.product_categories.resetToTop();
                                            }
                                        });
                                    },
                                    prev: function (child) {
                                        var children = select.product_categories.children,
                                            reset = false;
                                        angular.forEach(children, function (value, index) {
                                            if (value === child) {
                                                value.visible = false;
                                                if (index === 0) {
                                                    reset = true;
                                                }
                                            }
                                        });
                                        if (reset) {
                                            // select.product_categories.resetToTop();
                                        }
                                    }
                                };

                                models['24'].actions.search({
                                    search: {
                                        options: {limit: 1000},
                                        orders: [{
                                            operator: 'asc',
                                            field: 'name'
                                        }],
                                        filters: [{
                                            value: 'indexable',
                                            operator: '==',
                                            field: 'state'
                                        }, {
                                            value: 'None',
                                            operator: '==',
                                            field: 'parent_record'
                                        }]
                                    }
                                }).then(function (response) {
                                    var entities = response.data.entities;
                                    splitout(entities);
                                    select.product_categories.top = entities;
                                });
                            };
                        }
                    }());
                    return template;
                },
                SuperJsonProperty: function (info) {
                    info.config.ui.attrs['json-only'] = '';
                    return this.SuperTextProperty(info);
                },
                SuperDateTimeProperty: function (info) {
                    info.config.ui.attrs['time-date-picker-dialog'] = '';
                    info.config.ui.attrs.readonly = 'true';
                    return 'datetime';
                }
            });

        }));
}());
(function () {
    'use strict';
    angular.module('app')
        .run(ng(function (helpers, modals, $modal, GLOBAL_CONFIG) {
            $.extend(modals, {
                fields: {
                    remote: function (scope, field, config) {
                        $modal.open({
                            scope: scope,
                            templateUrl: 'core/models/manage.html',
                            controller: ng(function ($scope) {
                                var save = scope.save,
                                    complete = scope.complete,
                                    getTitle,
                                    initial = true;
                                getTitle = function () {
                                    return 'view' + helpers.toolbar.makeTitle(field.code_name);
                                };
                                field._title_.push(getTitle);
                                $scope.dialog = {
                                    templateBodyUrl: 'core/models/manage_body_default.html',
                                    toolbar: {}
                                };
                                $scope.parentContainer = $scope.container;
                                $scope.container = {};
                                $scope.close = angular.bind($scope, helpers.form.leave, function () {
                                    $scope.formSetPristine();
                                    $scope.$close();
                                });
                                $scope.formSetDirty = angular.bind($scope, helpers.form.setDirty);
                                $scope.formSetPristine = angular.bind($scope, helpers.form.setPristine);
                                $scope.formBuilder = {
                                    '0': [field]
                                };
                                $scope.layouts = {
                                    groups: [{
                                        label: false
                                    }]
                                };
                                $scope.$on('itemDelete', function () {
                                    $scope.formSetDirty();
                                });
                                $scope.$watch('parentContainer.form.$dirty', function (neww, old) {
                                    if (initial) {
                                        initial = false;
                                        return;
                                    }
                                    if (neww) {
                                        $scope.formSetDirty();
                                    } else {
                                        $scope.formSetPristine();
                                    }
                                });

                                $scope.$watch('entity.id', function () {
                                    $scope.dialog.toolbar.title = helpers.toolbar.buildTitle(field._title_);
                                });

                                $scope.save = function (dontShowMessage) {
                                    var maybePromise = save.call(scope, dontShowMessage);
                                    if (maybePromise) {
                                        maybePromise.then($scope.formSetPristine);
                                    }
                                    return maybePromise;
                                };

                                $scope.complete = function (response) {
                                    complete.call(scope, response);
                                    $scope.formSetPristine();
                                };

                                $scope.$on('$destroy', function () {
                                    if (angular.isArray(field.ui.specifics.parentArgs)) {
                                        field.ui.specifics.parentArgs.empty();
                                    }
                                    field._title_.remove(getTitle);
                                });
                            })
                        });
                    }
                }
            });
        })).run(ng(function (formInputTypes, underscoreTemplate, $timeout, $parse,
            endpoint, modelsMeta, models, $q, $filter, $modal, helpers,
            errorHandling, modals, GLOBAL_CONFIG, snackbar) {

            $.extend(formInputTypes, {
                SuperLocalStructuredProperty: function (info) {
                    var config = info.config,
                        fields = [],
                        newFields = [],
                        modelFields = config.modelclass,
                        defaultFields = _.toArray(modelFields),
                        noSpecifics = !angular.isDefined(config.ui.specifics),
                        newSort = [],
                        defaults,
                        defaultSortable,
                        findWhereByLayoutConfig,
                        buildPaths,
                        rootArgs,
                        rootFormSetDirty = helpers.callable(info.scope.formSetDirty),
                        list = {
                            secondary: true,
                            perLine: 1,
                            clickable: true,
                            calculate: function (ent, p) {
                                return parseInt(p, 10) === parseInt(this.perLine, 10);
                            }
                        };
                    config.ui.fieldset = true;

                    if (!config.ui.specifics.toolbar) {
                        config.ui.specifics.toolbar = {};
                    }

                    if (!config.ui.specifics.remoteOpts) {
                        config.ui.specifics.remoteOpts = {};
                    }

                    config.ui.specifics.sortMode = true;
                    defaultFields = defaultFields.sort(helpers.fields.sorter);

                    if (noSpecifics || !config.ui.specifics.fields) {
                        config.ui.specifics.fields = defaultFields;
                        if (config.ui.specifics.sortFields) {
                            angular.forEach(config.ui.specifics.sortFields, function (key) {
                                newSort.push(_.findWhere(config.ui.specifics.fields, {
                                    code_name: key
                                }));
                            });

                            config.ui.specifics.fields = newSort;
                        }
                    }

                    if (!noSpecifics && config.ui.specifics.excludeFields) {
                        angular.forEach(config.ui.specifics.fields, function (field, i) {
                            if ($.inArray(field.code_name, config.ui.specifics.excludeFields) === -1) {
                                newFields.push(field);
                            }
                        });
                        config.ui.specifics.fields = newFields;
                    }

                    defaults = {
                        fields: fields,
                        addNewText: 'Add',
                        addText: '{{config.ui.specifics.addNewText}}'
                    };

                    if (config.ui.specifics.listConfig) {
                        $.extend(list, config.ui.specifics.listConfig);
                    }

                    config.ui.specifics.listConfig = list;

                    // merge defaults into the
                    angular.forEach(defaults, function (value, key) {
                        if (config.ui.specifics[key] === undefined) {
                            config.ui.specifics[key] = value;
                        }
                    });

                    config.ui.specifics.parentArgs = info.scope.$eval(config.ui.args);
                    config.ui.specifics.entity = info.scope.$eval(config.ui.model);
                    config.ui.specifics.rootScope = info.scope.$eval(config.ui.rootScope);

                    if (!config.ui.specifics.sortableOptions) {
                        config.ui.specifics.sortableOptions = {};
                    }

                    defaultSortable = {
                        disabled: false,
                        start: function (e, ui) {
                            info.scope.$broadcast('itemOrderStarted');
                        },
                        axis: false,
                        containment: false,
                        whatSortMeans: function () {
                            modals.alert('howToSort');
                        },
                        handle: '.sort-handle',
                        tolerance: 'pointer',
                        helper: 'clone',
                        sort: function (e, ui) {
                            var deleteMode,
                                division,
                                helperWidth = ui.helper.width(),
                                itemScope = ui.item.scope(),
                                item = itemScope.$eval(ui.item.attr('current-item'));
                            division = ui.offset.left + helperWidth;
                            if (division < (helperWidth / 2)) {
                                deleteMode = true;
                            }
                            if (item) {
                                if (deleteMode) {
                                    ui.helper.addClass('about-to-delete');
                                    item._state = 'deleted';
                                } else {
                                    ui.helper.removeClass('about-to-delete');
                                    item._state = null;
                                }
                            }
                            info.scope.$broadcast('itemOrderSorting');
                        },
                        stop: function (e, ui) {
                            var dirty;
                            angular.forEach(config.ui.specifics.parentArgs,
                                function (ent, i) {
                                    i = ((config.ui.specifics.parentArgs.length - 1) - i);
                                    if (ent._state === 'deleted' || ent._sequence !== i) {
                                        dirty = true;
                                    }
                                    ent._sequence = i;
                                    ent.ui.access[ent.ui.access.length - 1] = i;
                                });
                            if (dirty) {
                                info.scope.formSetDirty();
                            }
                            info.scope.$broadcast('itemOrderChanged');
                            info.scope.$apply();
                        }
                    };
                    if (config.ui.specifics.setupSortableOptions) {
                        config.ui.specifics.sortableOptions = config.ui.specifics.setupSortableOptions();
                    }
                    // add default sorting config
                    $.extend(defaultSortable, config.ui.specifics.sortableOptions);
                    config.ui.specifics.sortableOptions = defaultSortable;
                    // disables sorting if the field is not writable
                    // writableCompiled is as-is specification
                    config.ui.init.add('checkDisabledStateForSortable', function () {
                        var fieldIsWritable = $parse(config.ui.writableCompiled + '');
                        config.ui.specifics.sortableOptions.disabled = !fieldIsWritable(info.scope);
                    });
                    // watches list of arguments args != new
                    info.scope.$watch(config.ui.args, function (neww, old) {
                        if (neww !== old) {
                            config.ui.specifics.parentArgs = neww;
                        }
                    });

                    buildPaths = function () {
                        // builds form fields
                        // it appends needed paths depending on hierarchy depth
                        config.ui.specifics.formBuilder = [];
                        angular.forEach(config.ui.specifics.fields, function (field) {
                            var copyWritable = angular.copy(config.ui.writable);

                            if (angular.isArray(copyWritable)) {
                                copyWritable.push((field.ui.writableName ? field.ui.writableName : field.code_name));
                            }

                            field.ui.path = [];
                            field.ui.path.extend(config.ui.path);
                            field.ui.path.push(field.code_name);
                            field.ui.realPath = [];
                            field.ui.realPath.extend(config.ui.realPath);
                            field.ui.realPath.push(field.code_name);
                            if (!angular.isDefined(field.ui.name)) {
                                field.ui.name = config.ui.name + '.' + field.code_name;
                            }
                            field.ui.writable = copyWritable;
                            config.ui.specifics.formBuilder.push(field);
                        });
                    };

                    buildPaths();

                    if (angular.isUndefined(config.ui.specifics.toolbar.titleAdd)) {
                        config.ui.specifics.toolbar.titleAdd = 'add' + helpers.toolbar.makeTitle(config.code_name);
                    }
                    if (angular.isUndefined(config.ui.specifics.toolbar.titleEdit)) {
                        config.ui.specifics.toolbar.titleEdit = 'edit' + helpers.toolbar.makeTitle(config.code_name);
                    }

                    if (config.ui.specifics.remote) {
                        // construct reference to root arguments
                        rootArgs = (config.ui.specifics.getRootArgs ? config.ui.specifics.getRootArgs() : config.ui.specifics.rootScope.args);
                        // assign "load more" logic
                        if (config.repeated && rootArgs.id && info.scope.args.id) {

                            config.ui.specifics.reader = models[rootArgs.action_model].reader({
                                kind: rootArgs.action_model,
                                key: rootArgs.key,
                                args: rootArgs,
                                access: config.ui.realPath,
                                complete: function (items) {
                                    config.ui.specifics.parentArgs.extend(items);
                                }
                            });
                            // apply direct reader settings if any
                            if (angular.isDefined(config.ui.specifics.readerSettings)) {
                                config.ui.specifics.reader.state(config.ui.specifics.readerSettings);
                            }

                            if ((angular.isUndefined(config.ui.specifics.remoteAutoload) || config.ui.specifics.remoteAutoload)) {
                                if (angular.isArray(config.ui.specifics.parentArgs)) {
                                    config.ui.specifics.parentArgs.empty();
                                }
                                $timeout(function () {
                                    config.ui.specifics.reader.load();
                                }, 100, false);
                            }

                        }
                    }

                    if (!config.repeated && config.ui.specifics.modal !== true) {

                        config.ui.specifics.SingularCtrl = ng(function ($scope) {
                            $scope.args = config.ui.specifics.parentArgs;
                            info.scope.$watchCollection(config.ui.args, function (neww, old) {
                                $.extend($scope.args, neww);
                            });
                            config.ui.specifics.getScope = function () {
                                return $scope;
                            };
                            var getTitle = function () {
                                return config.ui.specifics.toolbar.titleEdit;
                            };
                            config._title_.push(getTitle);
                            angular.forEach(config.ui.specifics.fields, function (field) {
                                field._title_ = config._title_.concat();
                            });
                            $scope.$on('$destroy', function () {
                                config._title_.remove(getTitle);
                                config.ui.specifics.getScope = undefined;
                            });
                        });

                    } else {

                        config.ui.specifics.remove = function (arg) {
                            arg._state = 'deleted';
                            info.scope.$emit('itemDelete', arg);
                            info.scope.$broadcast('itemDelete', arg);
                            rootFormSetDirty();
                        };

                        // generic manage dialog that handles editing of remote and local structured properties
                        config.ui.specifics.manage = function (arg, defaultArgs, modalSettings) {

                            buildPaths(); // force path rebuild

                            modalSettings = helpers.alwaysObject(modalSettings);

                            $modal.open({
                                popFrom: (modalSettings && modalSettings.target ? helpers.clicks.realEventTarget(modalSettings.target) : undefined),
                                template: underscoreTemplate.get(config.ui.specifics.templateUrl || 'core/fields/manage_structured.html')({
                                    config: config
                                }),
                                inDirection: modalSettings.inDirection,
                                outDirection: modalSettings.outDirection,
                                controller: ng(function ($scope, modelsUtil) {
                                    var length = (config.ui.specifics.modal ? 0 : config.ui.specifics.parentArgs.length),
                                        formBuilder = {
                                            '0': []
                                        },
                                        fieldsMap = {},
                                        groupBysIndx = [],
                                        groupBysMap = {},
                                        getTitle,
                                        getResult = function (response, access) {
                                            var accessPath = [],
                                                value,
                                                isNewAndRepeated = ($scope.isNew && config.repeated);
                                            angular.forEach(access, function (path, i) {
                                                var parse = parseInt(path, 10);
                                                if (!isNaN(parse)) {
                                                    path = 0;
                                                }
                                                accessPath.push(path);
                                            });
                                            if (isNewAndRepeated) {
                                                accessPath.pop();
                                            }
                                            value = helpers.getProperty(response.data.entity, accessPath);
                                            if (isNewAndRepeated && value.length) {
                                                value = _.findWhere(value, {
                                                    _state: 'created'
                                                });
                                            }

                                            return value;
                                        };

                                    angular.forEach(config.ui.specifics.formBuilder, function (value) {
                                        fieldsMap[value.code_name] = value;
                                    });

                                    config.ui.specifics.getScope = function () {
                                        return $scope;
                                    };

                                    $scope.isNew = false;

                                    $scope.rootFormSetDirty = rootFormSetDirty;
                                    $scope.formSetDirty = angular.bind($scope, helpers.form.setDirty);
                                    $scope.formSetPristine = angular.bind($scope, helpers.form.setPristine);

                                    $scope.response = null;
                                    $scope.config = config;
                                    if (!arg) {
                                        arg = {
                                            kind: config.modelclass_kind,
                                            _sequence: length
                                        };
                                        modelsUtil.normalize(arg, config.modelclass,
                                            config.ui.specifics.entity, config.code_name,
                                            length);
                                        if (angular.isDefined(defaultArgs)) {
                                            $.extend(arg, defaultArgs);
                                        }
                                        $scope.isNew = true;
                                    } else if (!config.ui.specifics.modal && arg.ui) {
                                        length = _.last(arg.ui.access);
                                    }


                                    if (angular.isDefined(arg.ui)) {
                                        arg.ui.access = angular.copy(config.ui.realPath);
                                        if (!config.ui.specifics.modal) {
                                            arg.ui.access.push(length);
                                        }
                                    }

                                    $scope.layouts = {
                                        groups: [{
                                            label: false
                                        }]
                                    };

                                    $scope.formBuilder = formBuilder;
                                    $scope.container = {
                                        action: endpoint.url
                                    };
                                    $scope.args = angular.copy(arg);
                                    $scope.parentArgs = config.ui.specifics.parentArgs;
                                    $scope.rootScope = config.ui.specifics.rootScope;
                                    $scope.entity = config.ui.specifics.entity;
                                    if (config.ui.specifics.remote) {
                                        $scope.close = angular.bind($scope, helpers.form.leave, function () {
                                            $scope.$close();
                                            if (config.ui.specifics.afterClose) {
                                                config.ui.specifics.afterClose($scope);
                                            }
                                        });

                                    } else {
                                        $.extend(config.ui.specifics.toolbar, {
                                            leftIcon: 'arrow_back',
                                            hideSave: true
                                        });
                                        $scope.close = function () {
                                            if (!$scope.container.form.$dirty) {
                                                return $scope.$close();
                                            }
                                            var save = $scope.save();
                                            if (save) {
                                                save.then(function () {
                                                    $scope._close_ = undefined;
                                                    $scope.$close();
                                                });
                                            } else {
                                                modals.confirm('discardWithFieldsRequired', $scope.$close);
                                            }
                                        };

                                        $scope._close_ = $scope.close;
                                    }

                                    $scope.validateForm = angular.bind($scope, helpers.form.validate);
                                    $scope.$on('$destroy', function () {
                                        config.ui.specifics.getScope = undefined;
                                    });
                                    if (config.ui.specifics.layoutConfig) {
                                        delete formBuilder['0'];
                                        $scope.layouts = {
                                            groups: []
                                        };
                                        angular.forEach(config.ui.specifics.layoutConfig, function (value, key) {
                                            var firstField = fieldsMap[value.fields[0]];
                                            $scope.layouts.groups.push({label: value.label || (firstField.label || $filter('humanized')(firstField.code_name))});
                                        });
                                    }
                                    findWhereByLayoutConfig = function (field) {
                                        var layout = config.ui.specifics.layoutConfig,
                                            needle,
                                            i;
                                        for (i = layout.length - 1; i >= 0; i--) {
                                            if ($.inArray(field.code_name, layout[i].fields) !== -1) {
                                                needle = i;
                                                break;
                                            }
                                        }
                                        return needle;
                                    };
                                    angular.forEach(config.ui.specifics.formBuilder, function (field) {
                                        var gr, group, next;
                                        helpers.fields.applyGlobalConfig(field);
                                        if (!field.ui.initialRealPath) {
                                            field.ui.initialRealPath = angular.copy(field.ui.realPath);
                                        } else {
                                            field.ui.realPath = angular.copy(field.ui.initialRealPath);
                                        }
                                        field.ui.realPath.pop();
                                        if (!config.ui.specifics.modal) {
                                            field.ui.realPath.push(length);
                                        }
                                        field.ui.realPath.push(field.code_name);
                                        if (field.ui.groupBy) {
                                            field.ui.hideMessages = true;
                                            if (!groupBysMap[field.ui.groupBy]) {
                                                gr = {
                                                    ui: {
                                                        group: {
                                                            help: field.ui.groupHelp,
                                                            label: field.ui.groupLabel,
                                                            name: field.ui.groupBy,
                                                            fields: [],
                                                            messages: function () {
                                                                var messages = {
                                                                    help: true
                                                                };
                                                                angular.forEach(gr.ui.group.fields, function (field) {
                                                                    if (field.ui.form.hasErrors() && field.ui.form.field().$dirty) {
                                                                        messages = field.ui.form.messages();
                                                                    }
                                                                });
                                                                return messages;
                                                            },
                                                            shouldShowMessages: function () {
                                                                return true;
                                                            }
                                                        }
                                                    }
                                                };
                                                groupBysMap[field.ui.groupBy] = gr;
                                                groupBysIndx.push(field.ui.groupBy);
                                                if (config.ui.specifics.layoutConfig) {
                                                    next = findWhereByLayoutConfig(field);
                                                    if (!angular.isDefined(formBuilder[next])) {
                                                        formBuilder[next] = [];
                                                    }
                                                    formBuilder[next].push(gr);
                                                } else {
                                                    formBuilder['0'].push(gr);
                                                }
                                            }
                                            groupBysMap[field.ui.groupBy].ui.group.fields.push(field);
                                            return;
                                        }
                                        if (config.ui.specifics.layoutConfig) {
                                            next = findWhereByLayoutConfig(field);
                                            if (!angular.isDefined(formBuilder[next])) {
                                                formBuilder[next] = [];
                                            }
                                            formBuilder[next].push(field);
                                            // this is manual layout config, skip this part
                                            return;
                                        }
                                        if (helpers.fields.isFieldset(field) && formInputTypes[field.type]) {
                                            group = {
                                                label: field.ui.label || $filter('humanized')(field.code_name)
                                            };
                                            if (_.string.contains(field.type, 'Remote')) {
                                                group.include = 'core/misc/action.html';
                                                group.action = function () {
                                                    var test = true;
                                                    if (field.ui.specifics.canOpen) {
                                                        test = field.ui.specifics.canOpen();
                                                    }
                                                    if (test) {
                                                        modals.fields.remote($scope, field);
                                                    }
                                                };
                                            }
                                            $scope.layouts.groups.push(group);

                                            next = $scope.layouts.groups.length - 1;

                                            if (!angular.isDefined(formBuilder[next])) {
                                                formBuilder[next] = [];
                                            }
                                            formBuilder[next].push(field);
                                        } else {
                                            formBuilder['0'].push(field);
                                        }
                                    });

                                    if (config.ui.specifics.remote) {

                                        // reference to args that get sent
                                        $scope.rootArgs = rootArgs;
                                        $scope.setAction = function (action) {
                                            // internal helper to set the action to be executed
                                            $scope.sendRootArgs.action_id = action;
                                        };
                                        // copy of root args used for packing the customized arguments
                                        $scope.sendRootArgs = {};
                                        $scope.save = function (dontShowMessage) {
                                            if (!$scope.validateForm()) { // check if the form is valid
                                                return false;
                                            }
                                            var promise,
                                                prepare = function () {
                                                    var readArgs = {},
                                                        readRootArgs = $scope.rootArgs,
                                                        readRootArgsAsList,
                                                        parentArgsPath = $scope.args.ui.access,
                                                        fieldList,
                                                        traceDeep,
                                                        lastPart = [];
                                                    // set this args as single item in array
                                                    // delete all remote structured property from rpc data
                                                    readRootArgs = angular.copy(readRootArgs);
                                                    helpers.setProperty(readRootArgs, parentArgsPath, $scope.args);
                                                    if (config.ui.additionalRealPaths) {
                                                        angular.forEach(config.ui.additionalRealPaths, function (path) {
                                                            helpers.setProperty(readRootArgs, path, $scope.args);
                                                        });
                                                    }
                                                    $scope.sendRootArgs = readRootArgs;
                                                    angular.forEach($scope.rootScope.config.fields, function (field) {
                                                        if (_.string.contains(field.type, 'RemoteStructured') && field.code_name !== $scope.args.ui.access[0]) {
                                                            delete readRootArgs[field.code_name];
                                                        }
                                                    });
                                                    readRootArgs.read_arguments = readArgs;
                                                    angular.forEach(parentArgsPath, function (part, i) {
                                                        // parseInt can produce inconsistent stuff like 10_foo makes 10, so we must avoid names of
                                                        // properties in datastore that begin with an number
                                                        if (!angular.isDefined(readArgs[part]) && isNaN(parseInt(part, 10))) {
                                                            readArgs[part] = {
                                                                config: {}
                                                            };
                                                            readArgs = readArgs[part];
                                                            lastPart.push(part);
                                                        }
                                                        // produce read path for the rpc
                                                        readRootArgs = readRootArgs[part];
                                                        if (angular.isArray(readRootArgs)) {
                                                            readRootArgsAsList = readRootArgs;
                                                        } else {
                                                            var extraReadPath = lastPart.join('.'),
                                                                extraRead,
                                                                extraReadClone;
                                                            if (config.ui.specifics.remoteOpts.read && config.ui.specifics.remoteOpts.read[extraReadPath]) {
                                                                extraRead = config.ui.specifics.remoteOpts.read[extraReadPath];
                                                            }
                                                            if (angular.isDefined(readRootArgsAsList)) {
                                                                extraReadClone = readRootArgsAsList.concat();
                                                                readRootArgsAsList.empty();
                                                                readRootArgsAsList.push(readRootArgs);
                                                                if (extraRead) {
                                                                    extraRead(extraReadClone, readRootArgsAsList);
                                                                }
                                                                extraReadClone = null;

                                                                readRootArgsAsList = undefined;
                                                            }
                                                            if (readRootArgs.key !== null && angular.isDefined(readRootArgs.key)) {
                                                                if (!angular.isDefined(readArgs.config.keys)) {
                                                                    readArgs.config.keys = [];
                                                                }
                                                                readArgs.config.keys.push(readRootArgs.key);

                                                            }
                                                        }
                                                    });

                                                    traceDeep = function (readRootArgs, readArgs) {
                                                        if (readRootArgs && readRootArgs.key) {
                                                            fieldList = modelsMeta.getFields(readRootArgs.kind);
                                                            angular.forEach(fieldList, function (field) {
                                                                if (field.is_structured && _.string.contains(field.type, 'RemoteStructured')) {
                                                                    var keys = [],
                                                                        newReadArgs = {
                                                                            config: {
                                                                                keys: keys
                                                                            }
                                                                        };
                                                                    if (field.repeated) {
                                                                        angular.forEach(readRootArgs[field.code_name], function (ent) {
                                                                            if (ent.key) {
                                                                                keys.push(ent.key);
                                                                                traceDeep(ent, newReadArgs);
                                                                            }
                                                                        });
                                                                    }
                                                                    readArgs[field.code_name] = newReadArgs;
                                                                }
                                                            });
                                                        } else if (angular.isArray(readRootArgs)) {
                                                            angular.forEach(readRootArgs, function (readRootArg) {
                                                                traceDeep(readRootArg, readArgs);
                                                            });
                                                        }
                                                    };

                                                    traceDeep(readRootArgs, readArgs);
                                                };

                                            prepare();
                                            if (config.ui.specifics.beforeSave) {
                                                config.ui.specifics.beforeSave($scope);
                                            }
                                            // create rpc from root args's action model and action id
                                            promise = models[$scope.sendRootArgs.action_model].actions[$scope.sendRootArgs.action_id]($scope.sendRootArgs);
                                            promise.then(function (response) {
                                                $scope.response = response;
                                                var keepAccess = angular.copy($scope.args.ui.access),
                                                    // set zero-in access path, example _images.0.pricetags.0._product.0._instances.0
                                                    value;
                                                if (config.ui.specifics.remoteOpts.response) {
                                                    value = config.ui.specifics.remoteOpts.response(response);
                                                } else {
                                                    value = getResult(response, keepAccess);
                                                }
                                                $.extend($scope.args, value); // modify current args
                                                $scope.args.ui.access = keepAccess; // reference back original access path
                                                if ($scope.isNew) {
                                                    if (config.repeated) {
                                                        $scope.parentArgs.unshift($scope.args); // preappend arg if they are new
                                                    }
                                                    $scope.isNew = false;
                                                }
                                                $.extend(arg, $scope.args); // modify provided args, usually come from the parent's scope
                                                // re-run prepare to ensure proper paths for complete hook
                                                prepare();
                                                if (angular.isDefined(config.ui.specifics.afterSave)) {
                                                    config.ui.specifics.afterSave($scope);
                                                }
                                                $scope.formSetPristine();
                                                if (!dontShowMessage) {
                                                    snackbar.showK('changesSaved');
                                                }

                                            }, function (response) {
                                                if (angular.isDefined(config.ui.specifics.afterSaveError)) {
                                                    config.ui.specifics.afterSaveError($scope, response);
                                                }
                                            });

                                            return promise;
                                        };

                                        $scope.complete = function (response) {
                                            $scope.response = response;
                                            var keepAccess = angular.copy($scope.args.ui.access),
                                                value = getResult(response, keepAccess);

                                            $.extend($scope.args, value);
                                            $scope.args.ui.access = keepAccess;
                                            if (angular.isDefined(config.ui.specifics.afterComplete)) {
                                                config.ui.specifics.afterComplete($scope);
                                            }
                                            $scope.formSetPristine();

                                            snackbar.showK('changesSaved');
                                        };

                                        $scope.noComplete = function () {
                                            // fired when the scope.complete() does not get fired i.e. when no files were sent for upload
                                            if (angular.isDefined(config.ui.specifics.noComplete)) {
                                                config.ui.specifics.noComplete($scope);
                                            }
                                            $scope.formSetPristine();
                                        };

                                        $scope.completeError = function (response) {
                                            // fired when it failed to send http-form-data rpc
                                            if (angular.isDefined(config.ui.specifics.afterCompleteError)) {
                                                config.ui.specifics.afterCompleteError($scope, response);
                                            }
                                            $scope.formSetPristine();
                                        };


                                    } else {


                                        $scope.save = function () {
                                            if (!$scope.validateForm()) { // check if the form is valid
                                                return false;
                                            }
                                            if ($scope.container.form.$dirty) {
                                                $scope.rootFormSetDirty();
                                            }
                                            var promise = null,
                                                saveCompleteDefer = $q.defer(),
                                                saveCompletePromise = saveCompleteDefer.promise,
                                                complete = function () {
                                                    var completePromise = null,
                                                        total = 0;

                                                    if (config.repeated) {
                                                        if ($scope.isNew) {
                                                            $scope.parentArgs.unshift($scope.args);
                                                            $scope.isNew = false;
                                                            total = $scope.parentArgs.length - 1;
                                                            angular.forEach($scope.parentArgs, function (item, i) {
                                                                i = total - i;
                                                                item._sequence = i;
                                                                item.sequence = i;
                                                            });
                                                        } else {
                                                            $.extend(arg, $scope.args);
                                                        }
                                                    }

                                                    if (angular.isFunction(config.ui.specifics.afterSave)) {
                                                        completePromise = config.ui.specifics.afterSave($scope, info);
                                                    }

                                                    if (completePromise && completePromise.then) {
                                                        completePromise.then(function () {
                                                            $scope.formSetPristine();
                                                            saveCompleteDefer.resolve();
                                                            if (config.closeAfterSave) {
                                                                $scope.close();
                                                            }
                                                        });
                                                    } else {
                                                        $scope.formSetPristine();
                                                        saveCompleteDefer.resolve();
                                                        if (config.closeAfterSave) {
                                                            $scope.close();
                                                        }
                                                    }

                                                };

                                            if (angular.isFunction(config.ui.specifics.beforeSave)) {
                                                promise = config.ui.specifics.beforeSave($scope, info);
                                            }

                                            if (promise && promise.then) {
                                                promise.then(complete);

                                            } else {
                                                complete();
                                            }
                                            return saveCompletePromise;

                                        };
                                    }

                                    // construct direct scope
                                    if (config.ui.specifics.scope) {
                                        $.extend($scope, config.ui.specifics.scope);
                                    }

                                    // call constructor
                                    if (angular.isFunction(config.ui.specifics.init)) {
                                        config.ui.specifics.init($scope);
                                    }

                                    getTitle = function () {
                                        return config.ui.specifics.toolbar['title' + ($scope.isNew ? 'Add' : 'Edit')];
                                    };

                                    config._title_.push(getTitle);

                                    $scope.$watch('isNew', function () {
                                        config.ui.specifics.toolbar.title = helpers.toolbar.buildTitle(config._title_);
                                    });

                                    angular.forEach(config.ui.specifics.fields, function (field) {
                                        field._title_ = config._title_.concat();
                                    });

                                    $scope.$on('$destroy', function () {
                                        config._title_.remove(getTitle);
                                        config.ui.specifics.remoteOpts = {};
                                        config.ui.additionalRealPaths = null;
                                    });

                                })
                            });
                        };

                        if (angular.isUndefined(config.ui.specifics.create)) {
                            config.ui.specifics.create = config.ui.specifics.manage;
                        }

                        info.scope.$on('$destroy', function () {
                            config.ui.specifics.create = undefined;
                            config.ui.specifics.sortableOptions = {};
                        });

                    }

                    return 'structured_' + (config.repeated ? 'repeated' : 'single');
                },
                _RemoteStructuredPropery: function (info) {
                    var config = info.config;
                    config.ui.specifics.remote = true;
                },
                SuperStructuredProperty: function (info) {
                    return this.SuperLocalStructuredProperty(info);
                },
                SuperRemoteStructuredProperty: function (info) {
                    this._RemoteStructuredPropery(info);
                    var ret = this.SuperLocalStructuredProperty(info);
                    return ret;
                },
                SuperImageLocalStructuredProperty: function (info) {
                    this.SuperLocalStructuredProperty(info);
                    if (!info.config.ui.specifics.displayImageConfig) {
                        info.config.ui.specifics.displayImageConfig = {
                            size: 360
                        };
                    }
                    if (!info.config.ui.specifics.sortableOptions) {
                        info.config.ui.specifics.sortableOptions = {};
                    }
                    $.extend(info.config.ui.specifics.sortableOptions, {
                        axis: false,
                        containment: false
                    });
                    return 'image';
                },
                SuperImageStructuredProperty: function (info) {
                    if (!info.config.ui.specifics.sortableOptions) {
                        info.config.ui.specifics.sortableOptions = {};
                    }
                    $.extend(info.config.ui.specifics.sortableOptions, {
                        axis: false,
                        containment: false
                    });
                    return this.SuperImageLocalStructuredProperty(info);
                },
                SuperImageRemoteStructuredProperty: function (info) {
                    this._RemoteStructuredPropery(info);
                    var ret = this.SuperImageLocalStructuredProperty(info);
                    return ret;
                }
            });

        }));
}());
(function () {
    'use strict';
    angular.module('app').run(ng(function (helpers) {
        helpers.grid = {
            calculate: function (canvas_width, max_width, min_width, margin) {
                var loop = max_width - min_width,
                    values = [],
                    i,
                    cover_width,
                    cover_count_raw,
                    cover_count,
                    cover_width_rounded,
                    sides;
                for (i = 0; i < loop; i++) {
                    cover_width = max_width - i;
                    cover_count_raw = canvas_width / cover_width;
                    cover_count = Math.floor(cover_count_raw);
                    cover_width = canvas_width / cover_count;
                    if (cover_width > max_width) {
                        cover_count = cover_count + 1;
                        cover_width = canvas_width / cover_count;
                        if (cover_width < min_width) {
                            cover_count = cover_count - 1;
                            cover_width = max_width;
                        }
                    }
                    cover_width_rounded = Math.floor(cover_width);
                    sides = Math.floor((canvas_width % (cover_width_rounded * cover_count)) / 2);
                    cover_width_rounded = cover_width_rounded - (margin * 2);
                    values = [cover_width_rounded, cover_count, sides];
                    if (cover_count_raw > 4 || cover_count === 1) {
                        break;
                    }
                }
                return values;
            }
        };
        helpers.gridStacked = {
            getHeight: function (images, width, margin) {
                margin = (margin * 2);
                width -= images.length * margin;
                var h = 0;
                angular.forEach(images, function (image) {
                    h += image.proportion;
                });
                // Math.floor
                return (width / h);
            },
            setHeight: function (images, height) {

                angular.forEach(images, function (image) {
                    image.width = (height * image.proportion);
                    image.height = height;
                });

            },
            resize: function (images, width) {
                this.setHeight(images, this.getHeight(images, width));
            },
            calculate: function (size, images, max_height, margin) {
                var n = 0,
                    providedImages = images,
                    i,
                    slice,
                    h; // reference entire array
                w: while (images.length > 0) {
                    for (i = 1; i < images.length + 1; ++i) {
                        slice = images.slice(0, i);
                        h = this.getHeight(slice, size, margin);
                        if (h < max_height) {
                            this.setHeight(slice, h);
                            n++;
                            images = images.slice(i);
                            continue w;
                        }
                    }
                    this.setHeight(slice, Math.min(max_height, h));
                    n++;
                    break;
                }
                return providedImages;
            }

        };
    })).directive('gridStacked', ng(function (helpers, $timeout) {

        return {
            link: function (scope, element, attrs) {
                var resize = function () {
                    var originalCanvas = 0,
                        run = function (check) {
                            var canvas = element.width(),
                                images = [],
                                margin = 1;
                            if (!canvas || (check && originalCanvas === canvas)) {
                                return; // do not measure if canvas is falsy or if the original canvas is the same as the current one
                            }
                            angular.forEach(scope.$eval(attrs.gridStacked), function (image) {
                                if (image._state !== 'deleted') {
                                    images.push(angular.copy(image));
                                }
                            });
                            helpers.gridStacked.calculate(canvas, images, 240, margin);
                            element.find('.grid-item').filter(function () {
                                return $(this).css('display') !== 'none';
                            }).each(function (i) {
                                if (!angular.isDefined(images[i])) {
                                    return;
                                }
                                $(this).css({
                                    width: images[i].width,
                                    height: images[i].height
                                }).addClass('visible');
                                $(this).find('img').css({
                                    height: images[i].height
                                });
                            });
                        };
                    run();
                    setTimeout(function () {
                        run(true);
                    }, 50);
                };

                resize = _.throttle(resize, 100);

                scope.$on('modalResize', resize);
                scope.$on('itemOrderChanged', resize);
                scope.$on('itemOrderSorting', resize);
                scope.$on('ngRepeatEnd', resize);

                scope.$on('itemDelete', function () {
                    $timeout(resize, 0, false);
                });
                scope.$watch(attrs.gridStacked + '.length', function () {
                    $timeout(resize, 0, false);
                });

            }
        };
    })).directive('gridGenerator', ng(function (GLOBAL_CONFIG, helpers, $timeout) {
        return {
            link: function (scope, element, attrs) {

                var config = scope.$eval(attrs.gridGenerator) || {},
                    margin = config.margin || 0,
                    maxWidth = config.maxWidth || GLOBAL_CONFIG.grid.maxWidth,
                    minWidth = config.minWidth || GLOBAL_CONFIG.grid.minWidth,
                    maxHeight = config.maxHeight || GLOBAL_CONFIG.grid.maxHeight,
                    fixedHeight = config.fixedHeight,
                    square = (angular.isDefined(config.square) ? config.square : true),
                    resize = function () {
                        element = $(element);
                        if (!element.length) {
                            return;
                        }
                        var wrapper = element,
                            canvasWidth = wrapper.width(),
                            values;
                        if (canvasWidth) {
                            values = helpers.grid.calculate(canvasWidth,
                                maxWidth, minWidth, margin);

                            if (wrapper.css('paddingLeft') !== values[2] || wrapper.css('paddingRight') !== values[2]) {
                                wrapper.css({
                                    paddingRight: values[2],
                                    paddingLeft: values[2]
                                });
                            }

                            wrapper.find('.grid-item').filter(function () {
                                return $(this).css('display') !== 'none';
                            }).each(function () {
                                var box, newHeight = fixedHeight ? fixedHeight : helpers.newHeightByWidth(maxWidth, maxHeight, values[0]);
                                if (values[0] !== $(this).width() || $(this).height() !== newHeight) {
                                    box = $(this).width(values[0]);
                                    if (square) {
                                        box.height(values[0]);
                                    } else {
                                        $(this).height(newHeight);
                                    }
                                }

                                $(this).addClass('visible');

                            });

                        }
                    };

                resize = _.throttle(resize, 100);

                $(window).bind('resize', resize);
                scope.$on('ngRepeatEnd', resize);
                scope.$on('itemDelete', resize);
                scope.$watch(attrs.gridGeneratorItems + '.length', resize);
                scope.$on('$destroy', function () {
                    $(window).off('resize', resize);
                });

            }
        };
    })).directive('gridScale', ng(function (helpers, $timeout, GLOBAL_CONFIG) {
        return {
            controller: ng(function ($scope, $element) {
                var that = this,
                    tracker = 0;
                that.items = [];
                that.config = {};
                that.columns = 1;
                that.calc = [];
                that.getColumns = function () {
                    var calc = helpers.grid.calculate($element.width(), that.config.maxWidth, that.config.minWidth, that.config.margin);
                    that.columns = calc[1];
                    that.calc = calc;
                };
                that.add = function (item) {
                    tracker += 1;
                    that.items.push(item);
                    that.calculate(item);
                    if (tracker === that.columns) {
                        tracker = 0;
                        //that.resize(true);
                    }
                };
                that.remove = function (item) {
                    that.items.remove(item);
                    that.resize();
                };
                that.calculate = function (item) {
                    if (that.columns < 2 && $element.width() > that.config.maxWidth) {
                        item.css('width', 'calc((100%) - ' + (that.config.margin * 2) + 'px)');
                        $element.css({
                            marginLeft: that.calc[2],
                            marginRight: that.calc[2]
                        });
                        return;
                    }
                    $element.css({
                        marginLeft: '',
                        marginRight: ''
                    });
                    item.css('width', 'calc((' + (100 / that.columns) + '%) - ' + (that.config.margin * 2) + 'px)');
                };
                that.resize = function (doAll) {
                    that.getColumns();
                    angular.forEach(that.items, function (item) {
                        that.calculate(item);
                        if (doAll) {
                            if (that.config.square) {
                                //item.height(item.width());
                            } else {
                                //item.height(helpers.newHeightByWidth(that.config.maxWidth, that.config.maxHeight, item.width()));
                            }
                        }
                    });
                };

                that.resize = _.throttle(that.resize, 100);

                $(window).on('resize', that.resize);

                $scope.$on('$destroy', function () {
                    $(window).off('resize', that.resize);
                });
            }),
            link: function (scope, element, attrs, ctrl) {
                $.extend(ctrl.config, GLOBAL_CONFIG.grid, scope.$eval(attrs.gridScale) || {});
                ctrl.getColumns();
            }
        };
    })).directive('gridScaleItem', ng(function (helpers) {
        return {
            require: '^gridScale',
            link: function (scope, element, attrs, gridScaleCtrl) {
                var appear = function () {
                    element.addClass('visible');
                }, config = scope.$eval(attrs.gridScaleItem) || {};
                gridScaleCtrl.add(element);
                if (config.image) {
                    scope.$on('displayImageLoaded', appear);
                } else {
                    setTimeout(appear, 50);
                }
                scope.$on('$destroy', function () {
                    gridScaleCtrl.remove(element);
                });
            }
        };
    }));
}());
(function () {
    'use strict';
    angular.module('app')
        .run(ng(function (helpers, $mdConstant) {
            $.extend(helpers, {
                clicks: {
                    realEventTarget: function (target) {
                        var theTarget = $(target),
                            parentTarget = theTarget.parents('.grid-item:first'),
                            cardParent = theTarget.parents('.card:first');
                        if (!theTarget.hasClass('grid-item') && parentTarget.length) {
                            target = parentTarget.get(0);
                        }

                        if (cardParent.length) {
                            target = cardParent.get(0);
                        }

                        return target;
                    }
                },
                closestLargestNumber: function (arr, closestTo) {
                    var closest = Math.max.apply(null, arr),
                        i = 0; //Get the highest number in arr in case it match nothing.

                    for (i = 0; i < arr.length; i++) { //Loop the array
                        if (arr[i] > closestTo && arr[i] < closest) {
                            closest = arr[i];
                        } //Check if it's higher than your number, but lower than your closest value
                    }
                    return closest; // return the value
                },
                newWidthByHeight: function (original_width, original_height, new_height) {
                    var ratio;
                    original_width = parseInt(original_width, 10);
                    original_height = parseInt(original_height, 10);
                    new_height = parseInt(new_height, 10);
                    ratio = new_height / original_height;
                    return (original_width * ratio);
                },
                newHeightByWidth: function (original_width, original_height, new_width) {
                    var ratio;
                    original_width = parseInt(original_width, 10);
                    original_height = parseInt(original_height, 10);
                    new_width = parseInt(new_width, 10);
                    ratio = new_width / original_width; // get ratio for scaling image
                    return (original_height * ratio);
                },
                url: {
                    abs: function (part) {
                        return window.location.protocol + '//' + window.location.host + '/' + part;
                    },
                    urlsafe: function (str) {
                        return window.btoa(str).replace('=', '-');
                    },
                    urlunsafe: function (str) {
                        return window.atob(str.replace('-', '='));
                    },
                    jsonFromUrlsafe: function (str) {
                        return angular.fromJson(helpers.url.urlunsafe(str));
                    },
                    jsonToUrlsafe: function (str) {
                        return helpers.url.urlsafe(angular.toJson(str));
                    }
                }
            });

            var animationEnd = function (which, cb) {
                return $(this).on($mdConstant.CSS.ANIMATIONEND, function kill(e) {
                    if (e.target === this) {
                        cb.call(this, e);
                        if (which === 'one') {
                            $(this).off($mdConstant.CSS.ANIMATIONEND, kill);
                        }
                    }
                });
            };

            $.fn.oneAnimationEnd = function (cb) {
                return animationEnd.call(this, 'one', cb);
            };

            $.fn.onAnimationEnd = function (cb) {
                return animationEnd.call(this, 'on', cb);
            };

        }))
        .directive('fillEmptySpace', function () {
            return {
                link: function (scope, element, attrs) {
                    var scroller = element.parents('.overflow-y:first'), resize;
                    if (!scroller.length) {
                        scroller = element.parents('.overflow-auto-y:first');
                    }
                    resize = function () {
                        var height = element.height(),
                            scrollHeight = scroller.height(),
                            lastLi = element.find('.list:last'),
                            lastLiHeight = lastLi.outerHeight();
                        if (scrollHeight > height) {
                            lastLi.css('min-height', lastLiHeight + (scrollHeight - height));
                        }

                    };
                    resize = _.throttle(resize, 100);
                    scope.$on('modalResize', resize);
                }
            };
        })
        .directive('helpRender', function () {
            return {
                scope: {
                    help: '=helpRender'
                },
                templateUrl: 'core/misc/help_render.html',
                link: function (scope, element, attrs) {
                    scope.isTemplate = function () {
                        return !angular.isArray(scope.help);
                    };
                }
            };
        })
        .directive('displayImage', ng(function (GLOBAL_CONFIG) {
            return {
                scope: {
                    image: '=displayImage',
                    config: '=displayImageConfig'
                },
                link: function (scope, element, attrs) {

                    if (!scope.config) {
                        scope.config = {};
                    }

                    if (!angular.isDefined(scope.config.size)) {
                        scope.config.size = 240;
                    }

                    var fn = function (nv, ov) {
                        if (nv !== ov) {
                            var img = element,
                                done = function () {
                                    img.css('visibility', 'inherit');
                                    scope.$emit('displayImageLoaded', img);
                                },
                                error = function () {
                                    var defaultImage = scope.config.defaultImage;
                                    if (!defaultImage) {
                                        defaultImage = 'defaultImage';
                                    }
                                    img.attr('src', GLOBAL_CONFIG[defaultImage]);
                                    done();
                                };

                            if (scope.image && scope.image.serving_url) {
                                img.on('load', done)
                                    .on('error', error)
                                    .attr('src', scope.image.serving_url + (scope.config.size === true ? '' : '=s' + scope.config.size));
                            } else {
                                setTimeout(function () {
                                    error();
                                    done();
                                }, 50);
                            }
                        }
                    };

                    scope.$watch('image.serving_url', fn);

                    fn(true, false);

                }
            };
        })).directive('loading', ng(function ($parse) {
            return {
                link: function (scope, element, attrs) {

                    if (angular.isDefined(attrs.loading)) {
                        scope.$watch(attrs.loading, function ngBooleanAttrWatchAction(value) {
                            if (value) {
                                element.attr('disabled', 'disabled');
                            } else {
                                element.removeAttr('disabled');
                            }
                        });
                    }

                    var disable = function (e) {
                            e.stopImmediatePropagation();
                            e.preventDefault();
                            return false;
                        },
                        disabledInitially = angular.isDefined(attrs.loading) ? $parse(attrs.loading) : function () {
                            return false;
                        };

                    scope.$on('disableUI', function ($event, neww) {

                        if (disabledInitially(scope)) {
                            return;
                        }
                        if (neww === true) {
                            element.attr('disabled', 'disabled');
                            element.on('click', disable);
                        } else {
                            element.removeAttr('disabled');
                            element.off('click', disable);
                        }

                    });
                }
            };
        })).directive('onNgRepeatEnd', ng(function ($timeout) {
            return {
                restrict: 'A',
                link: function (scope, element, attr) {
                    if (scope.$last === true) {
                        scope.$evalAsync(function () {
                            scope.$emit('ngRepeatEnd');
                        });
                    }
                }
            };
        })).directive('defaultFieldDisplay', ng(function ($compile) {
            return {
                scope: {
                    val: '=defaultFieldDisplay'
                },
                templateUrl: 'buyer/address_display.html',
                controller: ng(function ($scope) {
                    $scope.notEmpty = function (val) {
                        return angular.isString(val) || angular.isNumber(val);
                    };

                })
            };
        })).directive('draggableClick', ng(function ($parse, helpers) {
            return {
                restrict: 'A',
                link: function (scope, element, attrs) {
                    var callback = $parse(attrs.draggableClick),
                        click = function (event, tap) {
                            if (element.hasClass('dragged') && !tap) {
                                element.removeClass('dragged');
                                return;
                            }
                            scope.$apply(function () {
                                callback(scope, {
                                    $event: event
                                });
                            });
                        };
                    element.on('click', click);
                    scope.$on('$destroy', function () {
                        element.off('click', click);
                    });
                }
            };
        })).directive('loadMoreButton', ng(function () {
            return {
                restrict: 'A',
                templateUrl: 'core/misc/load_more_button.html',
                scope: {
                    config: '=loadMoreButton'
                }
            };
        })).directive('autoloadOnVerticalScrollEnd', ng(function ($timeout) {
            return {
                restrict: 'A',
                link: function (scope, element, attrs) {
                    var config,
                        listen,
                        loadMore,
                        steady,
                        intervalid,
                        waitinterval = false,
                        loaded = false,
                        steadyOpts,
                        maybeMore,
                        timeoutid,
                        run;
                    config = scope.$eval(attrs.autoloadOnVerticalScrollEnd);

                    run = function () {
                        listen = (function () {
                            var listener = config.listen;
                            if (!listener) {
                                listener = element.parents('.ui-view-wrapper:first');
                                if (listener.length) {
                                    return listener;
                                }
                                listener = element.parents('md-content[md-scroll-y]:first');
                                if (element.hasClass('overflow-y') || element.hasClass('overflow-auto-y')) {
                                    listener = element;
                                } else {
                                    if (!listener.length) {
                                        listener = element.parents('.overflow-y:first');
                                    }
                                    if (!listener.length) {
                                        listener = element.parents('.overflow-auto-y:first');
                                    }
                                }
                            } else {
                                listener = $(config.listen || window);
                            }
                            return listener;
                        }());


                        maybeMore = function () {
                            timeoutid = $timeout(function () {
                                var listenNode = listen.get(0),
                                    listenScrollHeight = listenNode.scrollHeight,
                                    viewport = $(window).height() - 56,
                                    maybe = config.reverse ? true : listenNode ? (viewport >= listenScrollHeight) : false,
                                    promise;
                                if (!listen.length || !listenNode) {
                                    return;
                                }
                                if (maybe) {
                                    promise = loadMore({}, angular.noop);
                                    if (promise) {
                                        promise.then(function () {
                                            waitinterval = false;
                                            if (!config.reverse) {
                                                maybeMore();
                                            }
                                        });
                                    }
                                } else {
                                    waitinterval = false;
                                }

                            }, 1000, false);

                        };

                        intervalid = setInterval(function () {
                            if (waitinterval) {
                                return true;
                            }
                            waitinterval = true;
                            maybeMore();
                        }, 2000);

                        loadMore = function (values, done) {
                            if (!config.loader) {
                                return;
                            }
                            var promise = config.loader.load();
                            if (!promise) {
                                done();
                                return false;
                            }
                            promise.then(function () {
                                done();
                            });

                            return promise;
                        };
                        steadyOpts = {
                            conditions: {
                                'max-bottom': config.bottom || 40
                            },
                            scrollElement: listen.get(0),
                            throttle: 100,
                            handler: loadMore
                        };
                        if (config.reverse) {
                            delete steadyOpts.conditions;
                        }
                        steady = new Steady(steadyOpts);
                        if (config.reverse) {
                            steady.addTracker('checkTop', function () {
                                return listen.scrollTop() < 100;
                            });
                            steady.addCondition('checkTop', true);
                        }
                        scope.$on('$destroy', function () {
                            steady.stop();
                            steady = undefined;
                            clearInterval(intervalid);
                            $timeout.cancel(timeoutid);
                        });

                        maybeMore();
                    };

                    scope.$watch(function () {
                        return attrs.autoloadOnVerticalScrollEnd && config && config.loader;
                    }, function (old, neww) {
                        if (loaded || !attrs.autoloadOnVerticalScrollEnd || !config || !config.loader) {
                            return;
                        }
                        loaded = true;
                        run();
                    });

                }
            };
        })).directive('resizeChart', ng(function (helpers) {
            return {
                priority: 100,
                link: function (scope, element, attrs) {

                    var resize = function () {
                        var width = $(element).width(),
                            newHeight = helpers.newHeightByWidth(640, 260, width);
                        $(element).height(newHeight);
                    };

                    resize();

                    scope.$on('modalResize', resize);
                }
            };
        })).directive('listButton', function () {
            return {
                templateUrl: 'core/misc/list_button.html',
                transclude: true,
                replace: true
            };
        }).directive('mdInkRippleList', ng(function ($mdInkRipple) {
            return {
                link: function (scope, element, attrs) {
                    $mdInkRipple.attach(scope, element, {
                        dimBackground: true,
                        multiplier: 0.1,
                        moveToCenter: false
                    });
                }
            };
        })).directive('mdInkRippleAction', ng(function ($mdInkRipple) {
            return {
                link: function (scope, element, attrs) {
                    $mdInkRipple.attachButtonBehavior(scope, element, {
                        dimBackground: false
                    });
                }
            };
        })).directive('mdInkRippleFit', ng(function ($mdInkRipple) {
            return {
                link: function (scope, element, attrs) {
                    $mdInkRipple.attachButtonBehavior(scope, element, {
                        dimBackground: false,
                        fitRipple: true,
                        moveToCenter: false
                    });
                }
            };
        })).directive('icon', ng(function ($mdInkRipple) {
            return {
                templateUrl: 'core/misc/icon.html',
                replace: true,
                transclude: true,
                scope: true,
                link: function (scope, element, attrs) {
                    scope.icon = attrs.type;
                    scope.color = attrs.color || 'normal';
                }
            };
        })).directive('contentListView', function () {
            return {
                scope: {
                    val: '=contentListView'
                },
                templateUrl: 'core/misc/content_list_view.html'
            };
        }).directive('sidenavItem', ng(function ($timeout, $mdSidenav) {
            return {
                templateUrl: 'core/misc/sidenav_item.html',
                transclude: true,
                replace: true
            };
        })).filter('labelize', ng(function (GLOBAL_CONFIG, $log) {
            return function (key, group) {
                if (angular.isUndefined(group)) {
                    group = 'default';
                }
                var getGroup = GLOBAL_CONFIG.labels[group],
                    get;
                if (angular.isUndefined(getGroup)) {
                    $log.warn('Group is not defined: ' + group);
                    return key;
                }
                get = getGroup[key];
                if (angular.isDefined(get)) {
                    return get;
                }
                $log.warn('Path for label not found: ' + group + '.' + key);
                return key;
            };
        })).filter('propsFilter', function () {
            return function (items, props) {
                var out = [];

                if (angular.isArray(items)) {
                    items.forEach(function (item) {
                        var itemMatches = false,
                            keys = Object.keys(props),
                            i,
                            prop,
                            text;
                        for (i = 0; i < keys.length; i++) {
                            prop = keys[i];
                            text = props[prop].toLowerCase();
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
        }).filter('capitalize', function () {
            return function (obj) {
                return _.str.capitalize(obj);
            };
        }).filter('output', ng(function (modelsMeta, outputTypes, $cacheFactory) {

            var types = outputTypes,
                cacheFields = $cacheFactory('cacheFields'),
                getFields = function (kind) {
                    if (!cacheFields.get(kind)) {
                        cacheFields.put(kind, modelsMeta.getFields(kind));
                    }
                    return cacheFields.get(kind);
                };

            return function (obj, key, args) {

                var input = obj[key],
                    fields,
                    field,
                    format;

                if (obj.kind) {
                    fields = getFields(obj.kind);
                    field = fields[key];

                    if (angular.isDefined(field)) {
                        format = types[field.type];
                        if (angular.isDefined(format)) {
                            return format(input, field);
                        }
                        // this is more generic approach to structured objects
                        if (input && typeof input === 'object' && input.hasOwnProperty('name')) {
                            return input.name;
                        }
                    }

                }

                return input;

            };

        })).filter('escape', function () {
            return function (val) {
                if (!val) {
                    return val;
                }
                return _.escape(val);
            };
        }).filter('autobr', ng(function (helpers) {
            return function (data) {
                if (!data) {
                    return data;
                }
                return data.replace(/\n\r?/g, '<br />');
            };

        })).filter('formatCurrency', ['$injector', '$locale', function ($injector, $locale) {
            var $filter = $injector.get('$filter'),
                numberFilter = $filter('number'),
                formats = $locale.NUMBER_FORMATS;
            formats.DEFAULT_PRECISION = angular.isUndefined(formats.DEFAULT_PRECISION) ? 2 : formats.DEFAULT_PRECISION;
            return function (amount, currency) {
                amount = parseFloat(amount, 10);
                if (!angular.isNumber(amount) || isNaN(amount)) {
                    return '';
                }
                /*
                {
                  "name": "US Dollar",
                  "code": "USD",
                  "id": "usd",
                  "_state": null,
                  "negative_separate_by_space": false,
                  "measurement": "Currency",
                  "thousands_separator": ",",
                  "positive_sign": "None",
                  "numeric_code": "840",
                  "positive_sign_position": 1,
                  "rate": null,
                  "digits": 2,
                  "key": "ahdkZXZ-dW5pdmVyc2FsLXRyYWlsLTYwOHILCxICMTciA3VzZAw",
                  "parent": {},
                  "kind": "17",
                  "_next_read_arguments": {},
                  "active": true,
                  "rounding": "0.01",
                  "symbol": "$",
                  "negative_currency_symbol_precedes": true,
                  "grouping": [
                    3,
                    3,
                    0
                  ],
                  "decimal_separator": ".",
                  "positive_separate_by_space": false,
                  "namespace": "",
                  "negative_sign": "-",
                  "factor": null,
                  "_sequence": null,
                  "positive_currency_symbol_precedes": true,
                  "negative_sign_position": 1
                }

                s = '<' + number + '>';
                symb = currency.symbol;
                smb = currency.symbol
                if (smb) {
                    precedes = (isNegative && currency.negative_currency_symbol_precedes || currency.positive_currency_symbol_precedes)
                    separated = (isNegative && currency.negative_separate_by_space || currency.positive_separate_by_space)

                    if (precedes) {
                        s = smb + (separated ? ' ' : '') + s
                    }
                    else {
                        s = s + (separated ? ' ' : '') + smb
                    }
                }

                sign_pos = isNegative && currency.negative_sign_position || currency.positive_sign_position;
                sign = isNegative && currency.negative_sign || currency.positive_sign;

                if (sign_pos == 0) {
                    s = '(' + s + ')'
                }
                else if (sign_pos == 1) {
                    s = sign + s
                }
                else if (sign_pos == 2) {
                    s = s + sign
                }
                else if (sign_pos == 3) {
                    s = s.replace('<', sign)
                }
                else if (sign_pos == 4) {
                    s = s.replace('>', sign)
                }
                else {
                    # the default if nothing specified;
                    # this should be the most fitting sign position
                    s = sign + s
                }

                s = s.replace('<', '').replace('>', '')


                @classmethod
                def currency(cls, lang, val, currency, symbol=True, grouping=False):
                    """
                    Formats val according to the currency settings in lang.
                    """
                    # Code from currency in locale.py
                    if not lang:
                        lang = cls(
                            decimal_point=cls.default_decimal_point(),
                            thousands_sep=cls.default_thousands_sep(),
                            grouping=cls.default_grouping(),
                            )

                    # check for illegal values
                    digits = currency.digits
                    if digits == 127:
                        raise ValueError("Currency formatting is not possible using "
                                         "the 'C' locale.")

                    s = cls.format(lang, '%.%if' % digits, abs(val), grouping,
                            monetary=currency)
                    # '<' and '>' are markers if the sign must be inserted
                    # between symbol and value
                    s = '<' + s + '>'

                    if symbol:
                        smb = currency.symbol
                        precedes = (val < 0 and currency.n_cs_precedes
                            or currency.p_cs_precedes)
                        separated = (val < 0 and currency.n_sep_by_space
                            or currency.p_sep_by_space)

                        if precedes:
                            s = smb + (separated and ' ' or '') + s
                        else:
                            s = s + (separated and ' ' or '') + smb

                    sign_pos = val < 0 and currency.n_sign_posn or currency.p_sign_posn
                    sign = val < 0 and currency.negative_sign or currency.positive_sign

                    if sign_pos == 0:
                        s = '(' + s + ')'
                    elif sign_pos == 1:
                        s = sign + s
                    elif sign_pos == 2:
                        s = s + sign
                    elif sign_pos == 3:
                        s = s.replace('<', sign)
                    elif sign_pos == 4:
                        s = s.replace('>', sign)
                    else:
                        # the default if nothing specified;
                        # this should be the most fitting sign position
                        s = sign + s

                    return s.replace('<', '').replace('>', '')


                 */
                var isNegative = amount < 0,
                    number,
                    s,
                    smb,
                    precedes,
                    separated,
                    sign_pos,
                    sign;

                amount = Math.abs(amount);
                number = numberFilter(amount, currency.digits);

                s = '<' + number + '>';
                smb = currency.symbol;
                if (smb) {
                    precedes = (isNegative && currency.negative_currency_symbol_precedes || currency.positive_currency_symbol_precedes);
                    separated = (isNegative && currency.negative_separate_by_space || currency.positive_separate_by_space);

                    if (precedes) {
                        s = smb + (separated ? ' ' : '') + s;
                    } else {
                        s = s + (separated ? ' ' : '') + smb;
                    }
                }

                sign_pos = isNegative && currency.negative_sign_position || currency.positive_sign_position;
                sign = isNegative && currency.negative_sign || currency.positive_sign;
                if (!sign) {
                    sign = '';
                }

                if (sign_pos === 0) {
                    s = '(' + s + ')';
                } else if (sign_pos === 1) {
                    s = sign + s;
                } else if (sign_pos === 2) {
                    s = s + sign;
                } else if (sign_pos === 3) {
                    s = s.replace('<', sign);
                } else if (sign_pos === 4) {
                    s = s.replace('>', sign);
                } else {
                    s = sign + s;
                }

                s = s.replace('<', '').replace('>', '');

                return s;
            };
        }]).filter('substr', function () {
            return function (str) {
                if (angular.isString(str)) {
                    return String.prototype.substr.apply(str, Array.prototype.slice.call(arguments, 1));
                }
                return str;
            };

        }).filter('nl2br', function () {
            return function (input) {
                if (input !== void 0) {
                    return input.replace(/\n/g, '<br />');
                }
            };
        }).filter('highlight', function () {
            function escapeRegexp(queryToEscape) {
                return queryToEscape.replace(/([.?*+^$[\]\\(){}|-])/g, '\\$1');
            }

            return function (matchItem, query) {
                return query && matchItem ? matchItem.replace(new RegExp(escapeRegexp(query), 'gi'), '<span class="ui-select-highlight">$&</span>') : matchItem;
            };
        }).factory('outputTypes', ng(function (dateFilter, GLOBAL_CONFIG, modelsMeta) {
            var outputTypes = {
                SuperDateTimeProperty: function (input, field) {
                    var date = new Date(input),
                        now = new Date(),
                        thisyear = now.getYear() === date.getYear(),
                        thismonth = false,
                        today = false,
                        tz = ' UTC+1:00',
                        format = GLOBAL_CONFIG.date.format;
                    // for reference https://docs.angularjs.org/api/ng/filter/date
                    if (!thisyear) {
                        format = 'd MMM yyyy, HH:mm';
                    }
                    if (thisyear) {
                        thismonth = true;
                        format = 'd MMM, HH:mm';
                    }
                    if (thismonth && thisyear && date.getDay() === now.getDay()) {
                        today = true;
                        format = 'HH:mm';
                    }
                    return dateFilter(date, format);
                }
            };
            return outputTypes;
        })).factory('searchBuilder', ng(function (modelsMeta, GLOBAL_CONFIG) {
            var create = function () {
                var make = {
                    kind: null,
                    hide: false,
                    filters: {},
                    indexes: [],
                    indexID: null,
                    fields: {
                        indexID: {
                            type: 'SuperStringProperty',
                            choices: [],
                            code_name: 'indexID',
                            required: true,
                            ui: {
                                args: 'search.indexID',
                                label: GLOBAL_CONFIG.fields.label.search.indexID,
                                specifics: {
                                    translatedChoices: false
                                },
                                writable: true,
                                attrs: {
                                    'ng-change': 'search.makeFilters()'
                                }
                            }
                        },
                        ancestor: {
                            type: 'SuperStringProperty',
                            code_name: 'ancestor',
                            required: 'search.indexes[search.indexID].ancestor',
                            ui: {
                                args: 'search.send.ancestor',
                                label: GLOBAL_CONFIG.fields.label.search.ancestor,
                                writable: true
                            }
                        },
                        filters: [],
                        orders: []
                    },
                    mapIndexes: function (obj) {
                        angular.forEach(obj, function (o, i) {
                            o._index = i;
                        });
                    },
                    formatSearchFilter: function (input) {
                        var filters, out = '';
                        if (!input || !angular.isObject(input)) {
                            return input;
                        }
                        if (input.ancestor && !input.filters) {
                            out += 'Ancestor and ';
                        }

                        if (input.filters) {
                            out += 'Filter by ';
                            if (input.ancestor) {
                                out += 'ancestor and ';
                            }
                            filters = $.map(input.filters, function (filter) {
                                return filter[0];
                            });

                            out += filters.join(" and ");

                            if (input.orders) {
                                out += ' and ';
                            }
                        }

                        if (input.orders) {
                            out += ' order by ' + $.map(input.orders, function (value) {
                                return value[0];
                            }).join(', ');
                        }

                        return out;
                    },
                    resetFilters: function () {
                        this.send.filters = [];
                        this.send.orders = [];
                        delete this.send.ancestor;
                    },
                    changeKindUI: function () {
                        this.changeKind();
                        this.setSearch(this.kind, undefined);
                        this.makeFilters();
                    },
                    changeKind: function () {

                        var searchActionArguments = modelsMeta.getActionArguments(this.kind, 'search'),
                            searchField,
                            cfg,
                            that = this;

                        if (searchActionArguments) {
                            try {
                                searchField = searchActionArguments.search;
                                this.default_send = searchField['default'];
                            } catch (ignore) {}

                            if (!searchField) {
                                this.hide = true;
                                searchField = {};
                            } else {
                                this.hide = false;
                            }

                            cfg = searchField.cfg;
                            this.cfg = cfg;
                            this.send.kind = this.kind;
                            this.filters = cfg.filters || {};
                            this.indexes = cfg.indexes || [];
                            this.indexID = null;
                            this.mapIndexes(cfg.indexes);
                            that.fields.indexID.choices = [];
                            angular.forEach(cfg.indexes, function (index) {
                                var choice = {
                                    key: index._index,
                                    name: that.formatSearchFilter(index)
                                };
                                that.fields.indexID.choices.push(choice);
                            });

                        }

                    },
                    changeOrderBy: function (e) {
                        e.field = this.indexes[this.indexID].orders[e._index][0];
                    },
                    makeFilters: function (reset) {
                        var that = this,
                            indx,
                            field,
                            operator;
                        if (!angular.isDefined(reset)) {
                            reset = true;
                        }

                        if (reset) {
                            this.resetFilters();
                        }
                        that.fields.filters = [];
                        that.fields.orders = [];

                        indx = that.indexes[that.indexID];


                        angular.forEach(indx.filters, function (filter, i) {
                            field = that.filters[filter[0]];
                            field.required = 'search.indexID != null && search.send.filters.length';
                            field.code_name = 'filter_' + filter[0];
                            field.ui = {
                                args: 'search.send.filters[\'' + i + '\'].value',
                                writable: true
                            };

                            if (reset) {
                                that.send.filters.push({
                                    field: filter[0],
                                    operator: filter[1][0],
                                    value: (field['default'] ? field['default'] : ''),
                                    _index: i
                                });
                            }

                            operator = {
                                type: 'SuperStringProperty',
                                choices: filter[1],
                                code_name: 'op_' + i,
                                required: field.required,
                                ui: {
                                    label: GLOBAL_CONFIG.fields.label.search.operator,
                                    writable: true,
                                    args: 'search.send.filters[\'' + i + '\'].operator'
                                }
                            };
                            that.fields.filters.push([operator, field]);
                        });

                        angular.forEach(indx.orders, function (order, i) {

                            if (reset) {
                                that.send.orders.push({
                                    field: order[0],
                                    operator: order[1][0],
                                    _index: i,
                                });
                            }

                            field = {
                                type: 'SuperStringProperty',
                                choices: order[1],
                                code_name: 'order_by_' + order[0],
                                required: 'search.indexID != null && search.send.filters.length',
                                ui: {
                                    writable: true,
                                    args: 'search.send.orders[\'' + i + '\'].operator'
                                }
                            };

                            that.fields.orders.push(field);
                        });

                        if (!indx.orders) {
                            that.send.orders = [];
                        }

                    },
                    discoverIndexID: function () {
                        var that = this,
                            filters = this.send.filters,
                            ancestor = this.send.ancestor,
                            orders = this.send.orders;

                        angular.forEach(this.indexes, function (index, indexID) {

                            if ((ancestor && !index.ancestor) || (!ancestor && index.ancestor)) {
                                return;
                            }

                            var got_filters = true,
                                matchCount = 0,
                                orderMatchCount = 0;

                            if (index.filters) {
                                got_filters = false;
                                if (filters && filters.length) {
                                    angular.forEach(index.filters, function (filter) {
                                        var gets = _.findWhere(filters, {
                                            field: filter[0]
                                        });
                                        if (gets && $.inArray(gets.operator, filter[1]) !== -1) {
                                            matchCount += 1;
                                        }
                                    });

                                    if (filters.length === matchCount && index.filters.length === filters.length) {
                                        got_filters = true;
                                        that.indexID = indexID;
                                    }
                                }

                            }


                            angular.forEach(index.orders, function (order, oi) {

                                var gets = _.findWhere(orders, {
                                    field: order[0]
                                });

                                if (got_filters && gets && $.inArray(gets.operator, order[1]) !== -1) {
                                    orderMatchCount += 1;
                                    gets._index = oi;
                                }
                            });

                            if (got_filters && index.orders && orderMatchCount === orders.length && index.orders.length === orders.length) {
                                that.indexID = indexID;
                            }

                        });

                    },
                    setSearch: function (kind, search) {

                        if (kind === undefined || kind === null) {
                            this.hide = true;
                            return;
                        }

                        if (this.kind !== kind) {
                            this.kind = kind;
                            this.changeKind();
                            this.resetFilters();
                        }

                        var searchActionArguments = modelsMeta.getActionArguments(this.kind, 'search'),
                            searchArgument = null;
                        if (searchActionArguments) {
                            try {
                                searchArgument = searchActionArguments.search;
                            } catch (ignore) {}

                            if (searchArgument) {
                                if (search === undefined && searchArgument['default']) {
                                    this.send = searchArgument['default'];
                                } else if (search) {
                                    this.send = search;
                                }

                                this.discoverIndexID();
                                this.makeFilters(false);
                            }

                        } else {
                            this.hide = true;
                        }

                    },
                    doSearch: function () {
                        throw new Error('Not implemented');
                    },
                    submitSearch: function () {
                        this.doSearch();
                    },
                    send: {
                        filters: [],
                        orders: [],
                    }
                };
                return make;
            };
            return {
                create: create
            };
        })).factory('channelApi', ng(function (GLOBAL_CONFIG) {
            // low level channel api
            var channelApi = {
                instances: {},
                create: function (token) {
                    if (!channelApi.instances[token]) {
                        var instance;
                        instance = {
                            callbacks: {},
                            events: {},
                            signals: [],
                            socket: null,
                            afterOnclose: [],
                            onclose: function (cb) {
                                this.afterOnclose.unshift(cb);
                            },
                            channel: new goog.appengine.Channel(token),
                            open: function (config) {
                                var that = this;
                                angular.forEach(config, function (callback, type) {
                                    that[type](callback);
                                });
                                if (that.socket !== null) {
                                    return that;
                                }
                                that.socket = that.channel.open(that.events);
                                console.log('socket.open', that.socket);
                                that.socket.onclose = function () {
                                    angular.forEach(that.afterOnclose, function (cb) {
                                        cb();
                                    });
                                };
                                return that;
                            },
                            destroy: function () {
                                delete channelApi.instances[token];
                            },
                            queue: function (type, cb) {
                                var id = this.signals.length;
                                this.signals.push(id);
                                this.callbacks[type].push([cb, id]);
                            },
                            dispatch: function (type, args) {
                                var that = this,
                                    terminate = [];
                                angular.forEach(this.callbacks[type], function (data) {
                                    if ($.inArray(data[1], that.signals) === -1) {
                                        terminate.push(data);
                                        return;
                                    }
                                    args = _.toArray(args);
                                    args.push(function () {
                                        that.signals.remove(data[1]);
                                    });
                                    data[0].apply(that.socket, args);
                                });

                                if (terminate) {
                                    angular.forEach(terminate, function (data) {
                                        that.callbacks[type].remove(data);
                                    });
                                    terminate = [];
                                }
                                if (!that.signals.length) {
                                    that.socket.close();
                                }
                            }
                        };
                        angular.forEach(['onopen', 'onmessage', 'onerror'], function (type) {
                            instance.callbacks[type] = [];
                            instance[type] = function (cb) {
                                this.queue(type, cb);
                            };
                            instance.events[type] = function () {
                                instance.dispatch(type, arguments);
                            };
                        });

                        instance.afterOnclose.push(function () {
                            instance.destroy();
                        });
                        channelApi.instances[token] = instance;
                    }
                    return channelApi.instances[token];
                }
            };

            if (GLOBAL_CONFIG.debug) {
                window._channelApi = channelApi;
            }
            return channelApi;
        })).factory('channelNotifications', ng(function (channelApi, snackbar) {
            var channelNotifications = {
                instances: {},
                create: function (token, callback) {
                    var out;
                    out = channelApi.create(token);
                    //channelNotifications.instances[token] = out;
                    out.open({
                        onmessage: function (message, destroy) {
                            destroy();
                            if (angular.isObject(message) && message.data) {
                                try {
                                    var response = angular.fromJson(message.data);
                                    if (callback) {
                                        callback(response);
                                    } else {
                                        snackbar.show(response.body);
                                    }
                                } catch (ignore) {
                                    console.warn('channel callback could not execute, got error', ignore, 'with data', message);
                                }
                            } else {
                                console.warn('channel returned no parsable data, got', message);
                            }
                        }
                    });
                    return out;
                }
            };
            return channelNotifications;
        })).directive('collapse', ['$animate', function ($animate) {

            return {
                link: function (scope, element, attrs) {
                    function expand() {
                        element.removeClass('collapse').addClass('collapsing');
                        $animate.addClass(element, 'in', {
                            to: {
                                height: element[0].scrollHeight + 'px'
                            }
                        }).then(expandDone);
                    }

                    function expandDone() {
                        element.removeClass('collapsing');
                        element.css({
                            height: 'auto'
                        });
                    }

                    function collapse() {
                        element
                        // IMPORTANT: The height must be set before adding "collapsing" class.
                        // Otherwise, the browser attempts to animate from height 0 (in
                        // collapsing class) to the given height here.
                            .css({
                                height: element[0].scrollHeight + 'px'
                            })
                            // initially all panel collapse have the collapse class, this removal
                            // prevents the animation from jumping to collapsed state
                            .removeClass('collapse')
                            .addClass('collapsing');

                        $animate.removeClass(element, 'in', {
                            to: {
                                height: '0'
                            }
                        }).then(collapseDone);
                    }

                    function collapseDone() {
                        element.css({
                            height: '0'
                        }); // Required so that collapse works when animation is disabled
                        element.removeClass('collapsing');
                        element.addClass('collapse');
                    }

                    scope.$watch(attrs.collapse, function (shouldCollapse) {
                        if (shouldCollapse) {
                            collapse();
                        } else {
                            expand();
                        }
                    });
                }
            };
        }]);
}());
(function () {
    'use strict';

    var getClickElement = function (options) {
            var clickElement = options.popFrom;
            return (clickElement ? $(clickElement) : clickElement);
        },
        getPositionOverClickElement = function (clickElement, element) {
            var clickRect = clickElement[0].getBoundingClientRect(),
                modalRect = element[0].getBoundingClientRect(),

                initial_width = clickElement.width(),
                initial_height = clickElement.height(),
                final_width = element.width(),
                final_height = element.height(),

                width_divider = final_width / initial_width,
                initial_width_scale = 1 / width_divider,

                height_divider = final_height / initial_height,
                initial_height_scale = 1 / height_divider,

                left = (-modalRect.left + clickRect.left + clickRect.width / 2 - modalRect.width / 2),
                top = (-modalRect.top + clickRect.top + clickRect.height / 2 - modalRect.height / 2);

            return {
                top: top,
                left: left,
                scale: {
                    x: initial_width_scale,
                    y: initial_height_scale
                }
            };

        };

    angular.module('app').factory('$$stackedMap', function () {
        return {
            createNew: function () {
                var stack = [];

                return {
                    add: function (key, value) {
                        stack.push({
                            key: key,
                            value: value
                        });
                    },
                    get: function (key) {
                        var i;
                        for (i = 0; i < stack.length; i++) {
                            if (key === stack[i].key) {
                                return stack[i];
                            }
                        }
                    },
                    keys: function () {
                        var keys = [],
                            i;
                        for (i = 0; i < stack.length; i++) {
                            keys.push(stack[i].key);
                        }
                        return keys;
                    },
                    top: function () {
                        return stack[stack.length - 1];
                    },
                    remove: function (key) {
                        var idx = -1,
                            i;
                        for (i = 0; i < stack.length; i++) {
                            if (key === stack[i].key) {
                                idx = i;
                                break;
                            }
                        }
                        return stack.splice(idx, 1)[0];
                    },
                    removeTop: function () {
                        return stack.splice(stack.length - 1, 1)[0];
                    },
                    length: function () {
                        return stack.length;
                    }
                };
            }
        };
    }).directive('modalBackdrop', ['$timeout', function ($timeout) {
        return {
            restrict: 'EA',
            replace: true,
            templateUrl: 'core/modal/backdrop.html',
            link: function (scope, element, attrs) {
                scope.backdropClass = attrs.backdropClass || '';
                $timeout(function () {
                    element.addClass('in');
                }, 0, false);
            }
        };
    }]).directive('modalWindow', ['$modalStack', '$timeout', '$$rAF', '$mdConstant', '$q', '$animate', 'animationGenerator', '$rootScope',
        function ($modalStack, $timeout, $$rAF, $mdConstant, $q, $animate, animationGenerator, $rootScope) {
            return {
                restrict: 'EA',
                scope: {
                    index: '@',
                    animate: '=',
                    modalOptions: '='
                },
                replace: true,
                transclude: true,
                templateUrl: function (tElement, tAttrs) {
                    return tAttrs.templateUrl || 'core/modal/window.html';
                },
                link: function (scope, element, attrs) {
                    $rootScope.$broadcast('disableUI', true);
                    var clickElement = getClickElement(scope.modalOptions),
                        ready;
                    element.addClass(!scope.modalOptions.fullScreen ? 'modal-medium' : ''); // add class for confirmation dialog
                    if (attrs.windowClass) {
                        element.addClass(attrs.windowClass);
                    }
                    scope.size = attrs.size;
                    scope.$isRendered = true;
                    // Observe function will be called on next digest cycle after compilation, ensuring that the DOM is ready.
                    // In order to use this way of finding whether DOM is ready, we need to observe a scope property used in modal's template.
                    ready = function () {
                        var where = scope.modalOptions.inDirection,
                            isSlide = (where && !clickElement),
                            isFromClick = clickElement,
                            isFade = (!isSlide && !isFromClick),
                            isConfirmation = !scope.modalOptions.fullScreen,
                            cb,
                            modal,
                            spec,
                            iwidth,
                            iheight,
                            animator;
                        if (isSlide) {
                            cb = function () {
                                element.addClass(where + ' slide drawer visible in');
                            };
                        } else if (isConfirmation) {
                            modal = element.find('.modal-dialog');
                            iwidth = modal.width();
                            iheight = modal.height();
                            scope.modalOptions.resize = _.throttle(function () {
                                var wwidth = $(window).width() - 40 * 2,
                                    wheight = $(window).height() - 24 * 2,
                                    maxHeight,
                                    maxWidth,
                                    cwidth = modal.width(),
                                    cheight = modal.height(),
                                    overHeight = iheight >= wheight,
                                    overWidth = iwidth >= wwidth;
                                if (overHeight || (cheight < wheight && overHeight)) {
                                    maxHeight = wheight;
                                } else {
                                    maxHeight = '';
                                }
                                if (overWidth || (cwidth < wwidth && overWidth)) {
                                    maxWidth = wwidth;
                                } else {
                                    maxWidth = '';
                                }
                                modal.css('max-height', maxHeight);
                                modal.css('max-width', maxWidth);
                            }, 100);
                            scope.modalOptions.resize();
                            $(window).on('resize', scope.modalOptions.resize);
                        }

                        if (clickElement) {
                            spec = getPositionOverClickElement(clickElement, element);
                            animator = animationGenerator.single('pop-in',
                                '0% {top: ' + spec.top + 'px; left: ' + spec.left + 'px; ' + $mdConstant.RAW_CSS.TRANSFORM + ': scale(' + spec.scale.x + ', ' + spec.scale.y + '); }' +
                                '1% { opacity:1; }' +
                                '75% { top: 0px; left: 0px;}' +
                                '100% { top: 0px; left: 0px; ' + $mdConstant.RAW_CSS.TRANSFORM + ': scale(1, 1);opacity:1;}');
                            cb = function () {
                                element.addClass('pop ' + animator.className).data('animator', animator);
                                $$rAF(function () {
                                    clickElement.css('opacity', 0); // separate frame for opacity
                                });
                            };
                        } else if (isFade) {
                            cb = function () {
                                element.addClass('fade in');
                            };
                        }

                        element.oneAnimationEnd(function () {
                            element.addClass('visible');
                            $(window).triggerHandler('modal.visible', [element]);
                            scope.modalOptions.opened = true;
                            scope.$apply();
                            $rootScope.$broadcast('disableUI', false);
                        });

                        $(window).triggerHandler('modal.open', [element]);

                        $$rAF(cb);

                    };
                    attrs.$observe('modalRender', function (value) {
                        if (value === 'true') {
                            $timeout(ready, 50, false);
                        }
                    });

                    scope.backdropClose = function ($event) {
                        if (scope.modalOptions.cantCloseWithBackdrop) {
                            return;
                        }
                        if ($event.target === $event.currentTarget) {
                            scope.$parent.close();
                        }
                    };
                }
            };
        }
    ]).directive('modalTransclude', function () {
        return {
            link: function ($scope, $element, $attrs, controller, $transclude) {
                $transclude($scope.$parent, function (clone) {
                    $element.empty();
                    $element.append(clone);
                });
            }
        };
    }).factory('$modalStack', ['$timeout', '$document', '$compile', '$rootScope', '$$stackedMap', 'mdContextualMonitor',
        '$mdConstant', '$q', 'animationGenerator', '$animate', '$$rAF',
        function ($timeout, $document, $compile, $rootScope, $$stackedMap, mdContextualMonitor, $mdConstant, $q, animationGenerator, $animate, $$rAF) {

            var OPENED_MODAL_CLASS = 'modal-open',
                openedWindows = $$stackedMap.createNew(),
                $modalStack = {};

            function backdropIndex() {
                return openedWindows.length() - 1;
            }

            function removeAfterAnimate(domEl, scope, done) {
                var clickElement = getClickElement(scope.modalOptions),
                    spec,
                    demise,
                    animator,
                    inclass = 'in',
                    outclass = 'out',
                    popin = domEl.data('animator');

                if (clickElement && popin) {
                    spec = getPositionOverClickElement(clickElement, domEl);
                    animator = animationGenerator.single('pop-out',
                        '0% { opacity:1;top: 0px; left: 0px; ' + $mdConstant.RAW_CSS.TRANSFORM + ': scale(1, 1);}' +
                        '75% { top: 0px; left: 0px;}' +
                        '100% { opacity:1;top: ' + spec.top + 'px; left: ' + spec.left + 'px; ' + $mdConstant.RAW_CSS.TRANSFORM + ': scale(' + spec.scale.x + ', ' + spec.scale.y + '); }');

                    outclass = animator.className;
                    inclass = popin.className;
                }

                $$rAF(function () {
                    domEl.removeClass(inclass).addClass(outclass);
                });

                demise = function (e) {
                    domEl.remove();
                    if (done) {
                        done();
                    }
                    if (clickElement) {
                        clickElement.css('opacity', 1);
                    }

                    domEl = undefined;

                    if (popin) {
                        popin.destroy();
                    }

                    if (animator) {
                        animator.destroy();
                    }
                };

                domEl.oneAnimationEnd(demise);

                setTimeout(function () {
                    if (domEl) {
                        demise();
                    }
                }, 600);

            }

            function removeModalWindow(modalInstance, defer) {

                var body = $document.find('body').eq(0),
                    modalWindow = openedWindows.get(modalInstance).value,
                    backdropDomEl = modalWindow.backdropDomEl,
                    backdropScope = modalWindow.backdropScope;

                //clean up the stack
                openedWindows.remove(modalInstance);

                //remove window DOM element
                backdropDomEl.removeClass('in').addClass('out').oneAnimationEnd(function () {
                    backdropDomEl.remove();
                    backdropScope.$destroy();
                    modalWindow.backdropScope = undefined;
                    modalWindow.backdropDomEl = undefined;
                });
                removeAfterAnimate(modalWindow.modalDomEl, modalWindow.modalScope, function () {
                    modalWindow.modalScope.$destroy();
                    body.toggleClass(OPENED_MODAL_CLASS, openedWindows.length() > 0);
                    $(window).triggerHandler('modal.close');
                    defer.resolve();
                });
            }

            $modalStack.open = function (modalInstance, modal) {

                var backdropDomEl,
                    backdropScope,
                    body,
                    config = {
                        deferred: modal.deferred,
                        modalScope: modal.scope,
                        backdrop: modal.backdrop
                    },
                    currBackdropIndex,
                    angularBackgroundDomEl,
                    modalDomEl,
                    angularDomEl;

                openedWindows.add(modalInstance, config);

                modal.scope.modalOptions = {
                    inDirection: modal.inDirection,
                    outDirection: modal.outDirection,
                    cantCloseWithBackdrop: modal.cantCloseWithBackdrop,
                    popFrom: modal.popFrom,
                    fullScreen: modal.fullScreen,
                    noEscape: modal.noEscape,
                    opened: false
                };

                body = $document.find('body').eq(0);
                currBackdropIndex = backdropIndex();

                backdropScope = $rootScope.$new(true);
                backdropScope.index = currBackdropIndex;
                angularBackgroundDomEl = angular.element('<div class="opaque" modal-backdrop></div>');
                angularBackgroundDomEl.attr('backdrop-class', modal.backdropClass);
                backdropDomEl = $compile(angularBackgroundDomEl)(backdropScope);
                body.append(backdropDomEl);

                config.backdropDomEl = backdropDomEl;
                config.backdropScope = backdropScope;

                angularDomEl = angular.element('<div modal-window></div>');

                angularDomEl.attr({
                    'template-url': modal.windowTemplateUrl,
                    'window-class': modal.windowClass,
                    size: modal.size,
                    index: openedWindows.length() - 1,
                    'modal-options': 'modalOptions',
                    animate: 'animate',
                    exiting: 'exiting'
                }).html(modal.content);

                modalDomEl = $compile(angularDomEl)(modal.scope);
                openedWindows.top().value.modalDomEl = modalDomEl;
                body.append(modalDomEl);
                body.addClass(OPENED_MODAL_CLASS);

                if (!modal.noEscape) {
                    modalInstance.esc = function (e) {
                        var modalWindow = openedWindows.get(modalInstance);
                        if (e) {
                            e.preventDefault();
                        }
                        if (modalWindow && modalWindow.value && modalWindow.value.modalScope && modalWindow.value.modalScope._close_) {
                            return modalWindow.value.modalScope._close_();
                        }

                        $rootScope.$apply(function () {
                            if (modalWindow && modalWindow.value && modalWindow.value.modalScope) {
                                return modalWindow.value.modalScope.close();
                            }
                            $modalStack.dismiss(modalInstance, 'escape key press');
                        });

                        return true;
                    };
                    mdContextualMonitor.queue(modalInstance.esc);
                }

            };

            $modalStack._dequeue = function (modalWindow, modalInstance) {

                if (modalWindow && modalWindow.value) {
                    if (!modalWindow.value.modalScope.modalOptions.noEscape) {
                        mdContextualMonitor.dequeue(modalInstance.esc);
                    }
                    if (modalWindow.value.modalScope.modalOptions.resize) {
                        $(window).off('resize', modalWindow.value.modalScope.modalOptions.resize);
                    }
                }
            };

            $modalStack.close = function (modalInstance, result, what) {
                if (!what) {
                    what = 'resolve';
                }
                var modalWindow = openedWindows.get(modalInstance),
                    defer = $q.defer();
                $modalStack._dequeue(modalWindow, modalInstance);
                if (modalWindow) {
                    modalWindow.value.deferred[what](result);
                    removeModalWindow(modalInstance, defer);
                } else {
                    defer.resolve();
                }
                return defer.promise;
            };

            $modalStack.dismiss = function (modalInstance, reason) {
                return $modalStack.close(modalInstance, reason, 'reject');
            };

            $modalStack.dismissAll = function (reason) {
                var topModal = this.getTop();
                while (topModal) {
                    this.dismiss(topModal.key, reason);
                    topModal = this.getTop();
                }
            };

            $modalStack.getTop = function () {
                return openedWindows.top();
            };

            return $modalStack;
        }
    ]).provider('$modal', function () {

        var $modalProvider = {
            options: {
                backdrop: false, //can be also false or 'static'
                inDirection: 'right',
                outDirection: 'right',
                fullScreen: true
            },
            $get: ['$injector', '$rootScope', '$q', '$http', '$templateCache', '$controller', '$modalStack',
                function ($injector, $rootScope, $q, $http, $templateCache, $controller, $modalStack) {

                    var $modal = {};

                    function getTemplatePromise(options) {
                        return options.template ? $q.when(options.template) :
                            $http.get(angular.isFunction(options.templateUrl) ? (options.templateUrl)() : options.templateUrl, {
                                cache: $templateCache
                            }).then(function (result) {
                                return result.data;
                            });
                    }

                    function getResolvePromises(resolves) {
                        var promisesArr = [];
                        angular.forEach(resolves, function (value) {
                            if (angular.isFunction(value) || angular.isArray(value)) {
                                promisesArr.push($q.when($injector.invoke(value)));
                            }
                        });
                        return promisesArr;
                    }

                    $modal.open = function (modalOptions) {

                        var modalResultDeferred = $q.defer();
                        var modalOpenedDeferred = $q.defer();

                        //prepare an instance of a modal to be injected into controllers and returned to a caller
                        var modalInstance = {
                            result: modalResultDeferred.promise,
                            opened: modalOpenedDeferred.promise,
                            close: function (result) {
                                return $modalStack.close(modalInstance, result);
                            },
                            dismiss: function (reason) {
                                return $modalStack.dismiss(modalInstance, reason);
                            }
                        };

                        //merge and clean up options
                        modalOptions = $.extend({}, $modalProvider.options, modalOptions);
                        modalOptions.resolve = modalOptions.resolve || {};

                        //verify options
                        if (!modalOptions.template && !modalOptions.templateUrl) {
                            throw new Error('One of template or templateUrl options is required.');
                        }

                        var templateAndResolvePromise =
                            $q.all([getTemplatePromise(modalOptions)].concat(getResolvePromises(modalOptions.resolve)));


                        templateAndResolvePromise.then(function resolveSuccess(tplAndVars) {

                            var modalScope = (modalOptions.scope || $rootScope).$new();
                            modalScope.$close = modalInstance.close;
                            modalScope.close = modalScope.$close;
                            modalScope.$dismiss = modalInstance.dismiss;

                            var ctrlInstance, ctrlLocals = {};
                            var resolveIter = 1;

                            if (modalOptions.controller) {
                                ctrlLocals.$scope = modalScope;
                                ctrlLocals.$modalInstance = modalInstance;
                                angular.forEach(modalOptions.resolve, function (value, key) {
                                    ctrlLocals[key] = tplAndVars[resolveIter++];
                                });

                                ctrlInstance = $controller(modalOptions.controller, ctrlLocals);
                                if (modalOptions.controllerAs) {
                                    modalScope[modalOptions.controllerAs] = ctrlInstance;
                                }
                            }

                            $modalStack.open(modalInstance, {
                                scope: modalScope,
                                deferred: modalResultDeferred,
                                content: tplAndVars[0],
                                backdrop: modalOptions.backdrop,
                                backdropClass: modalOptions.backdropClass,
                                windowClass: modalOptions.windowClass,
                                windowTemplateUrl: modalOptions.windowTemplateUrl,
                                cantCloseWithBackdrop: modalOptions.cantCloseWithBackdrop,
                                size: modalOptions.size,
                                inDirection: modalOptions.inDirection,
                                outDirection: modalOptions.outDirection,
                                fullScreen: modalOptions.fullScreen,
                                popFrom: modalOptions.popFrom,
                                noEscape: modalOptions.noEscape
                            });

                        }, function resolveError(reason) {
                            modalResultDeferred.reject(reason);
                        });

                        templateAndResolvePromise.then(function () {
                            modalOpenedDeferred.resolve(true);
                        }, function () {
                            modalOpenedDeferred.reject(false);
                        });

                        return modalInstance;
                    };

                    return $modal;
                }
            ]
        };

        return $modalProvider;
    }).directive('fitInModal', function () {
        return {
            link: function (scope, element, attrs) {
                var time,
                    fn = function (e) {
                        if (time) {
                            clearTimeout(time);
                        }
                        time = setTimeout(function () {
                            var modal = $(element).parents('.modal:first'),
                                modalDialog = modal.find('.modal-dialog:first'),
                                height = (modal.hasClass('modal-medium') ? (parseInt((modalDialog.css('max-height').indexOf('%') === -1 ? modalDialog.css('max-height') : 0), 10) || modalDialog.height()) : $(window).height());

                            modalDialog.find('.fixed-height, .min-height, .max-height').each(function () {
                                var newHeight = height,
                                    footer = modalDialog.find('.md-actions'),
                                    toolbar = modalDialog.find('md-toolbar'),
                                    css = 'height';
                                if (footer.length) {
                                    newHeight -= footer.outerHeight();
                                }
                                if (toolbar.length) {
                                    newHeight -= toolbar.outerHeight();
                                }
                                if ($(this).hasClass('min-height')) {
                                    css = 'min-height';
                                }
                                if ($(this).hasClass('max-height')) {
                                    css = 'max-height';
                                }
                                $(this).css(css, newHeight);
                            });
                            scope.$broadcast('modalResize');
                        }, 50);
                    };

                fn = _.throttle(fn, 100);

                $(window).bind('resize modal.open', fn);
                scope.$on('$destroy', function () {
                    $(window).unbind('resize modal.open', fn);
                });
            }
        };
    }).factory('modals', ng(function ($modal, $q, helpers, GLOBAL_CONFIG) {

        var modals = {
            alert: function (key, callbackOrConfig, messageOrConfig) {
                return modals.confirm(key, callbackOrConfig, messageOrConfig, true);
            },
            confirm: function (key, callbackOrConfig, messageOrConfig, alert) {
                var theConfig = {
                        message: key + ' missing config, see core/config/config.js'
                    },
                    config;

                if (angular.isFunction(callbackOrConfig)) {
                    config = {
                        confirm: callbackOrConfig
                    };
                } else if (angular.isObject(callbackOrConfig)) {
                    config = callbackOrConfig;
                }
                if (angular.isDefined(messageOrConfig)) {
                    if (!angular.isObject(messageOrConfig)) {
                        config.message = messageOrConfig;
                    } else {
                        config = messageOrConfig;
                    }
                }
                config = helpers.alwaysObject(config);
                helpers.extendDeep(theConfig, config, GLOBAL_CONFIG.modals[!alert ? 'confirmations' : 'alerts'][key]);
                theConfig.noSecondary = alert;
                theConfig.confirm = function () {
                    var that = this;
                    if (config.noAutoDismiss) {
                        return config.confirm.call(that);
                    }
                    this.dismiss().then(function () {
                        if (angular.isFunction(config.confirm)) {
                            config.confirm.call(that);
                        }
                    });
                };
                return this.create(theConfig, theConfig.modal);
            },
            create: function (extraConfig, modalConfig) {
                var config = {
                        message: ''
                    },
                    defaultModalConfig;
                helpers.extendDeep(config, extraConfig);
                defaultModalConfig = {
                    fullScreen: false,
                    inDirection: false,
                    outDirection: false,
                    cantCloseWithBackdrop: true,
                    templateUrl: 'core/misc/confirm.html',
                    controller: ng(function ($scope) {
                        var callback = (angular.isFunction(extraConfig) ? extraConfig : (extraConfig.ok || null));
                        config.dismiss = function () {
                            var close = $scope.$close();
                            close.then(function () {
                                if (callback) {
                                    callback.call($scope);
                                }
                            });
                            return close;
                        };

                        if (!angular.isObject(extraConfig)) {
                            extraConfig = {};
                        }

                        if (config.message && !config.messages) {
                            config.messages = [config.message];
                        }

                        $scope.config = config;
                        $.extend($scope, config.scope);
                        config.scope = undefined;
                    })
                };
                $.extend(defaultModalConfig, modalConfig);
                return $modal.open(defaultModalConfig);
            }
        };
        if (GLOBAL_CONFIG.debug) {
            window._modals = modals;
        }
        return modals;
    }));

}());
(function () {
    'use strict';
    angular.module('app')
        .run(ng(function (modals, helpers, models, $modal, modelsMeta, snackbar) {
            if (!modals.models) {
                modals.models = {};
            }
            modals.models.sudo = function (entity, config) {
                var defaults = {
                    fullScreen: false,
                    popFrom: false,
                    inDirection: false,
                    outDirection: false,
                    templateUrl: null,
                    cantCloseWithBackdrop: true,
                    controller: ng(function ($scope) {
                        var sudoFields = modelsMeta.getActionArguments(entity.kind, 'sudo');
                        $scope.args = {};
                        $scope.fields = sudoFields;
                        angular.forEach($scope.fields, function (field) {
                            $.extend(field.ui, {
                                writable: true,
                                label: false,
                                attrs: {
                                    'native-placeholder': '',
                                    'class': 'full-width'
                                }
                            });
                            $scope.args[field.code_name] = entity[field.code_name];
                        });

                        $scope.fields.message.ui.placeholder = 'Write a message to the user!';
                        $scope.fields.note.ui.placeholder = 'Write a note to the admins!';
                        $scope.validateForm = angular.bind($scope, helpers.form.validate);

                        $scope.container = {};
                        $scope.config = {};

                        $scope.config.scroll = true;

                        $scope.config.dismiss = function () {
                            return $scope.$close();
                        };

                        $scope.config.text = {
                            primary: 'Ok'
                        };

                        $scope.config.confirm = function () {
                            if ($scope.validateForm()) {
                                var promise = models[entity.kind].actions.sudo($scope.args);
                                promise.then(function (response) {
                                    if (config.onConfirm) {
                                        config.onConfirm(response.data.entity);
                                    }
                                    $scope.config.dismiss();
                                    snackbar.showK('administered');
                                });
                            } else {
                                helpers.form.wakeUp($scope.container.form);
                            }
                        };
                    })
                };
                $.extend(defaults, config);
                $modal.open(defaults);
            };

            if (!helpers.models) {
                helpers.models = {};
            }
            $.extend(helpers.models, {
                isEntityListEmpty: function (entities, also) {
                    var empty = (!entities || entities.length === 0),
                        emptyFactory;
                    if (!empty) {
                        emptyFactory = 0;
                        angular.forEach(entities, function (value) {
                            var maybe = false;
                            if (also) {
                                maybe = $.inArray(value._state, also) !== -1;
                            }
                            if (value._state === 'deleted' || maybe) {
                                emptyFactory += 1;
                            }
                        });
                        empty = (emptyFactory === entities.length);
                    }
                    return empty;
                }
            });
        }))
        .value('modelsInfo', {})
        .value('currentAccount', {}).factory('modelsMeta', ng(function ($injector, GLOBAL_CONFIG) {
            var modelsMeta = {},
                standardize = function (fields, maker) {
                    angular.forEach(fields, function (field, field_key) {
                        if (field.ui === undefined) {
                            field.ui = {};
                        }
                        if (field.code_name === null) {
                            field.code_name = field_key;
                        }

                        field._maker_ = maker;
                        if (field.modelclass !== undefined) {
                            standardize(field.modelclass, field.modelclass_kind);
                        }
                    });

                };

            modelsMeta.friendlyActionName = function (kind, action_key) {

                var info = this.get(kind),
                    actions,
                    friendlyName;
                if (info === undefined) {
                    return undefined;
                }

                actions = info.actions;

                angular.forEach(actions, function (action) {
                    if (action.key === action_key) {
                        friendlyName = action.id;
                    }
                });

                return friendlyName;
            };

            modelsMeta.getFields = function (kind_id) {
                if (!angular.isDefined(kind_id)) {
                    console.error('provided kind id is not acceptable, got: ' +
                        kind_id);
                    return undefined;
                }
                var info = this.get(kind_id),
                    fields;
                if (!angular.isDefined(info)) {
                    console.error('could not find meta info for kind ' + kind_id);
                    return undefined;
                }

                fields = angular.copy(info.fields);

                standardize(fields, kind_id);

                return fields;
            };

            modelsMeta.getDefaultActionArguments = function (kind, action) {
                var getAction = this.getActionArguments(kind, action),
                    defaultArgs = {};

                angular.forEach(getAction['arguments'], function (arg) {
                    if (arg['default'] !== null) {
                        defaultArgs[arg.code_name] = arg['default'];
                    }

                });

                return defaultArgs;
            };

            modelsMeta.getActionArguments = function (kind_id, action) {
                var info = this.get(kind_id),
                    getAction,
                    actionArguments = {},
                    fields;
                if (!angular.isDefined(info)) {
                    return undefined;
                }
                if (angular.isDefined(action)) {
                    getAction = info.mapped_actions[action];
                    if (!angular.isDefined(getAction)) {
                        console.error('action ' + action + ' not found for kind ' + kind_id);
                        return undefined;
                    }
                    fields = angular.copy(getAction['arguments']);

                    standardize(fields, kind_id + '-' + action);
                    return fields;
                }

                angular.forEach(info.mapped_actions, function (action) {
                    fields = angular.copy(action['arguments']);
                    standardize(fields, kind_id + '-' + action.id);
                    actionArguments[action.id] = fields;
                });

                return actionArguments;

            };

            modelsMeta.getActions = function (kind_id) {
                var info = this.get(kind_id),
                    actions;
                if (!angular.isDefined(info)) {
                    return undefined;
                }
                actions = info.mapped_actions;
                angular.forEach(actions, function (action) {
                    standardize(action['arguments'], kind_id + '-' + action.id);
                });

                return actions;
            };

            modelsMeta.getName = function (kind_id) {
                var info = this.get(kind_id);
                if (!angular.isDefined(info)) {
                    console.error('model name not found for kind ' + kind_id);
                    return undefined;
                }
                return info.name;
            };

            modelsMeta.get = function (kind_id) {

                var modelsInfo = $injector.get('modelsInfo'),
                    kind = modelsInfo[kind_id],
                    fields = {},
                    actions = {},
                    data;

                if (kind === undefined) {
                    console.error('no info for kind ' + kind_id);
                    return undefined;
                }

                angular.forEach(kind, function (value, key) {
                    if (key !== '_actions' && key !== '__name__') {
                        fields[key] = value;
                    }
                });

                angular.forEach(kind._actions, function (action) {
                    actions[action.id] = action;
                });

                data = {
                    actions: kind._actions,
                    mapped_actions: actions,
                    fields: fields,
                    name: kind.__name__
                };

                return data;
            };
            if (GLOBAL_CONFIG.debug) {
                window._modelsMeta = modelsMeta;
            }

            return modelsMeta;

        })).factory('ruleEngine', ng(function (modelsMeta) {

            var ruleEngine = {
                run: function (entity) {
                    var actions = {},
                        inputs = {},
                        kindInfo = modelsMeta.get(entity.kind),
                        actionPermissions = entity._action_permissions,
                        fieldPermissions = entity._field_permissions,
                        ruleActions = kindInfo.actions,
                        config = {
                            action: actions,
                            input: inputs,
                            field: fieldPermissions
                        },
                        actionTranslate = function (actionName) {
                            return actionPermissions[ruleActions[actionName].id];
                        },
                        executable = function (actionName) {
                            var gets = actionTranslate(actionName);
                            return gets.executable;
                        };
                    if (actionPermissions === undefined) {
                        return undefined;
                        // if the permissions are not present, there is no rule engine here...
                    }
                    angular.forEach(ruleActions, function (value, key) {

                        if (!config.action[value.id]) {
                            config.action[value.id] = {};
                        }
                        config.action[value.id].executable = executable(key);

                        angular.forEach(value.arguments, function (argumentValue) {
                            var argument_key = argumentValue.code_name;
                            if (!config.input[value.id]) {
                                config.input[value.id] = {};
                            }
                            config.input[value.id][argument_key] = argumentValue;
                        });

                    });

                    return config;
                }
            };

            return ruleEngine;
        })).factory('modelsUtil', ng(function (modelsMeta, ruleEngine, GLOBAL_CONFIG) {
            // Service used for normalizing entity data that gets retrieved from datastore
            var modelsUtil = {
                normalizeMultiple: function (entities) {
                    angular.forEach(entities, function (entity) {
                        modelsUtil.normalize(entity);
                    });
                },
                argumentsToJson: function (entity, pretty) {
                    var ignore = ['_field_permissions', '_next_read_arguments', '_read_arguments', '_action_permissions', 'ui'];
                    return JSON.stringify(entity,
                        function (key, value) {
                            var val = value,
                                newval;

                            if (angular.isObject(value) && value.ui) {
                                newval = {};
                                angular.forEach(value, function (v, k) {
                                    if ($.inArray(k, ignore) === -1) {
                                        newval[k] = v;
                                    }
                                });
                                val = newval;
                            }

                            if (typeof key === 'string' && key.charAt(0) === '$') {
                                val = undefined;
                            } else if (value && value.document && value.location && value.alert && value.setInterval) {
                                val = '$WINDOW';
                            } else if (value && document === value) {
                                val = '$DOCUMENT';
                            } else if (value && value.$evalAsync && value.$watch) {
                                val = '$SCOPE';
                            }

                            return val;
                        }, pretty ? '  ' : null);
                },
                normalize: function (entity, fields, parent, subentity_field_key, subentity_position, noui) {
                    if (entity.ui && entity.ui.normalized) {
                        return;
                    }

                    if (fields === undefined) {
                        fields = modelsMeta.getFields(entity.kind);
                    }

                    if (noui === undefined) {

                        entity.ui = {};
                        entity.ui.normalized = true;
                        entity.ui.access = [];
                        if (subentity_field_key) {
                            entity.ui.access.extend(parent.ui.access);
                            entity.ui.access.push(subentity_field_key);
                            if (subentity_position !== undefined) {
                                entity.ui.access.push(subentity_position);
                            }

                        }
                        /// ui must be now reserved keyword in datastore and we use it for making ui related functions
                        if (parent === undefined) {
                            entity.ui.rule = ruleEngine.run(entity);
                        }

                    }

                    angular.forEach(fields, function (field) {
                        var defaults = field['default'],
                            value = entity[field.code_name];
                        if (field.type === 'SuperDateTimeProperty' && !defaults) {
                            defaults = new Date();

                        }
                        if (field.repeated && !angular.isArray(defaults)) {
                            defaults = [];
                        }

                        if ((value === undefined || value === null)) {
                            if ((defaults !== null && defaults !== undefined)) {
                                entity[field.code_name] = defaults;
                            }
                        }

                        if (field.type === 'SuperDateTimeProperty' && angular.isString(value)) {
                            entity[field.code_name] = new Date(value);
                        }

                        if (field.is_structured) {
                            if (field.repeated) {
                                angular.forEach(value, function (subentity, i) {
                                    modelsUtil.normalize(subentity, field.modelclass,
                                        entity, field.code_name, i);
                                });
                            } else {

                                if ((value === undefined || value === null)) {
                                    if (field.required) {
                                        value = {
                                            kind: field.modelclass_kind
                                        };
                                        entity[field.code_name] = value;
                                    }
                                }

                                if (!(value === undefined || value === null)) {
                                    modelsUtil.normalize(value, field.modelclass, entity,
                                        field.code_name, undefined, noui);
                                }

                            }
                        }

                    });

                }
            };

            if (GLOBAL_CONFIG.debug) {
                window._modelsUtil = modelsUtil;
            }
            return modelsUtil;
        })).factory('modelsEditor', ng(function ($modal, endpoint, $q, helpers,
            modelsUtil, errorHandling, models, modelsMeta, $timeout, $filter, formInputTypes, recordBrowser, snackbar) {

            var modelsEditor = {
                create: function (config) {

                    var defaultConfig = {
                            showClose: true,
                            closeAfterSave: false,
                            action: 'update',
                            templateBodyUrl: 'core/models/manage_body_default.html',
                            scope: {},
                            fields: [],
                            init: angular.noop,
                            getScope: null,
                            defaultInit: angular.noop,
                            defaultArgumentLoader: function ($scope) {
                                var entityCopy = angular.copy($scope.entity),
                                    actionArguments = modelsMeta.getActionArguments($scope.config.kind, $scope.config.action),
                                    args = {};

                                angular.forEach(actionArguments, function (arg) {
                                    var val = entityCopy[arg.code_name];
                                    // default is only acceptable if its not null or undefined
                                    if (val === undefined && (arg['default'] !== null &&
                                            arg['default'] !== undefined)) {
                                        val = arg['default'];
                                    }
                                    if (val !== undefined) {
                                        // arg can never be "undefined"
                                        args[arg.code_name] = val;
                                    }

                                });
                                if ($scope.entity.key) {
                                    args.key = entityCopy.key;
                                }
                                if ($scope.entity.id) {
                                    args.id = entityCopy.id;
                                }
                                args.ui = entityCopy.ui;
                                // every entity has _read_arguments when retrieved from database
                                // argument loader will attach that to its next rpc
                                // to ensure that entity that has been fetched from database
                                // gets the same read arguments for next rpc
                                if (entityCopy._read_arguments) {
                                    args.read_arguments = entityCopy._read_arguments;
                                }

                                // attaches next read arguments to args too, needed for paging
                                if (entityCopy._next_read_arguments) {
                                    args._next_read_arguments = entityCopy._next_read_arguments;
                                }

                                // attach extra data to args
                                $.extend(args, $scope.withArgs);

                                // attach which action and model should be used in rpc from the config
                                args.action_id = $scope.config.action;
                                args.action_model = $scope.config.kind;
                                return args;
                            },
                            argumentLoader: function ($scope) {
                                return this.defaultArgumentLoader($scope);
                            },
                            defaultPrepareReadArguments: function ($scope) {
                                // it will scan entire args and populate read arguments
                                if (!angular.isObject($scope.args.read_arguments)) {
                                    $scope.args.read_arguments = {};
                                }
                                var readArgs = $scope.args.read_arguments,
                                    parser = function (arg, key, readArgs) {
                                        if (angular.isArray(arg)) {
                                            var path = readArgs[key];
                                            if (!path) {
                                                path = {
                                                    config: {}
                                                };
                                            }

                                            if (!path.config) {
                                                path.config = {};
                                            }

                                            if (arg && angular.isObject(arg[0])) {
                                                path.config.keys = $.map(arg, function (ent) {
                                                    return ent.key;
                                                });
                                            }

                                            readArgs[key] = path;
                                        }
                                    };
                                angular.forEach($scope.args, function (arg, key) {
                                    parser(arg, key, readArgs);
                                });
                            },
                            prepareReadArguments: function ($scope) {
                                this.defaultPrepareReadArguments($scope);
                            }
                        },
                        actionArguments,
                        modelsEditorInstance;

                    // recurse the config adding only what is supplied by the `new_config`
                    helpers.mergeDeep(config, defaultConfig);

                    // load all field specs from the arguments that are going to be used based on action and model provided
                    if (!angular.isDefined(config.fields) && angular.isDefined(config.kind) && angular.isDefined(config.action)) {
                        config.fields = [];
                        actionArguments = modelsMeta.getActionArguments(config.kind, config.action);
                        angular.forEach(actionArguments, function (field) {
                            if (angular.isDefined(config.excludeFields) && $.inArray(field.code_name, config.excludeFields) !== -1) {
                                return;
                            }
                            config.fields.push(field);
                        });

                    }
                    // map out the fields to key-value dict
                    config.keyedFields = {};
                    angular.forEach(config.fields, function (field) {
                        config.keyedFields[field.code_name] = field;
                    });

                    modelsEditorInstance = {
                        config: config,
                        read: function (entity, args, httpConfig) {
                            if (args === undefined) {
                                args = {
                                    key: entity.key
                                };
                            }
                            var that = this;
                            return models[config.kind].actions.read(args, httpConfig).then(function (response) {
                                $.extend(entity, response.data.entity);
                                return that.open(entity, args);
                            });
                        },
                        prepare: function (entity, args, httpConfig) {
                            var that = this;
                            return models[config.kind].actions.prepare(args, httpConfig).then(function (response) {
                                $.extend(entity, response.data.entity);
                                return that.open(entity, args);
                            });
                        },
                        open: function (entity, args) {
                            var opener = $modal,
                                fn = 'open',
                                defer = $q.defer(),
                                completePromise = defer.promise,
                                ctrl;
                            ctrl = function ($scope) {
                                var inflector = $filter('inflector'),
                                    field,
                                    done = {},
                                    rootTitle,
                                    madeHistory = false,
                                    makeHistory = function () {
                                        if (madeHistory || !$scope.entity.id) {
                                            return false;
                                        }
                                        if (!angular.isDefined($scope.historyConfig)) {
                                            $scope.historyConfig = false;
                                        }
                                        if ($scope.historyConfig === true) {
                                            $scope.historyConfig = {
                                                kind: config.kind,
                                                key: $scope.entity.key
                                            };
                                        } else {
                                            if ($scope.historyConfig === false) {
                                                return false;
                                            }
                                        }
                                        madeHistory = true;
                                        var rule = $scope.args.ui.rule.field._records;
                                        $scope.historyConfig.key = $scope.entity.key;
                                        if (rule && rule.visible) {
                                            $scope.layouts.groups.push(recordBrowser.attach($scope.historyConfig));
                                        }
                                    },
                                    editTitle = 'edit' + config.kind,
                                    addTitle = 'add' + config.kind;
                                config.getScope = function () {
                                    return $scope;
                                };
                                modelsUtil.normalize(entity);

                                if (!config.toolbar) {
                                    config.toolbar = {};
                                }

                                if (angular.isUndefined(config.toolbar.titleEdit)) {
                                    config.toolbar.titleEdit = editTitle;
                                }

                                if (angular.isUndefined(config.toolbar.titleAdd)) {
                                    config.toolbar.titleAdd = addTitle;
                                }

                                $scope.container = {
                                    action: endpoint.url
                                };
                                $scope.withArgs = args;
                                $scope.config = config;
                                $scope.dialog = {
                                    toolbar: config.toolbar,
                                    templateBodyUrl: config.templateBodyUrl
                                };
                                $scope.entity = entity;
                                $scope.args = config.argumentLoader($scope);
                                $scope.rootScope = $scope;

                                $scope.formSetPristine = angular.bind($scope, helpers.form.setPristine);
                                $scope.formSetDirty = angular.bind($scope, helpers.form.setDirty);
                                $scope.validateForm = angular.bind($scope, helpers.form.validate);

                                $scope.setAction = function (action) {
                                    $scope.args.action_id = action;
                                    config.action = action;
                                };

                                $scope.save = function (dontShowMessage) {
                                    if (!$scope.validateForm()) {
                                        return false;
                                    }
                                    config.prepareReadArguments($scope);
                                    var promise = models[config.kind].actions[$scope.args.action_id]($scope.args);

                                    promise.then(function (response) {
                                        $.extend($scope.entity, response.data.entity);
                                        var new_args = config.argumentLoader($scope);
                                        $.extend($scope.args, new_args);
                                        makeHistory();
                                        if (angular.isDefined(config.afterSave)) {
                                            config.afterSave($scope);
                                        }
                                        $scope.formSetPristine();
                                        if (!dontShowMessage) {
                                            snackbar.showK('changesSaved');
                                        }
                                    }, function (response) {
                                        // here handle error...
                                        if (angular.isDefined(config.afterSaveError)) {
                                            config.afterSaveError($scope, response);
                                        }
                                    });

                                    return promise;
                                };

                                $scope.complete = function (response) {
                                    $.extend($scope.entity, response.data.entity);
                                    var newArgs = config.argumentLoader($scope);
                                    $.extend($scope.args, newArgs);
                                    makeHistory();
                                    if (angular.isDefined(config.afterComplete)) {
                                        config.afterComplete($scope);
                                    }
                                    if (config.closeAfterSave) {
                                        $timeout(function () {
                                            $scope.close();
                                        });
                                    }
                                    $scope.formSetPristine();
                                    snackbar.showK('changesSaved');

                                };

                                $scope.noComplete = function () {
                                    if (angular.isDefined(config.noComplete)) {
                                        config.noComplete($scope);
                                    }
                                };

                                $scope.completeError = function (response) {
                                    if (angular.isDefined(config.afterCompleteError)) {
                                        config.afterCompleteError($scope, response);
                                    }
                                };

                                $scope.close = angular.bind($scope, helpers.form.leave, function () {
                                    $scope._close_ = undefined;
                                    var promise = $scope.$close();
                                    if (config.afterClose) {
                                        config.afterClose($scope);
                                    }
                                    return promise;
                                });

                                $scope._close_ = $scope.close;

                                rootTitle = function () {
                                    var toolbar = $scope.dialog.toolbar,
                                        out;
                                    if ($scope.entity.id) {
                                        if (angular.isDefined(toolbar.titleEdit)) {
                                            toolbar.title = helpers.toolbar.title(toolbar.titleEdit);
                                        }
                                        out = toolbar.titleEdit;
                                    } else {
                                        if (angular.isDefined(toolbar.titleAdd)) {
                                            toolbar.title = helpers.toolbar.title(toolbar.titleAdd);
                                        }
                                        out = toolbar.titleAdd;
                                    }
                                    return out;
                                };
                                config._title_ = [rootTitle];
                                $scope.$watch('entity.id', rootTitle);

                                angular.forEach(config.fields, function (field) {
                                    field._title_ = config._title_.concat();
                                });

                                if (angular.isDefined(config.scope)) {
                                    $.extend($scope, config.scope);
                                }

                                $scope.formBuilder = {
                                    '0': []
                                };

                                // if no accordions are defined, use the auto accordion builder
                                if (!angular.isDefined($scope.layouts)) {
                                    $scope.layouts = {
                                        groups: [{
                                            label: false
                                        }]
                                    };

                                    angular.forEach(config.fields, function (field) {
                                        if (field.is_structured && formInputTypes[field.type]) {
                                            if (!field.ui.initialLabel) {
                                                field.ui.initialLabel = field.ui.label;
                                            }
                                            $scope.layouts.groups.push({
                                                label: $filter('humanized')((field.ui.initialLabel || field.code_name))
                                            });

                                            field.ui.label = false;

                                            var next = $scope.layouts.groups.length - 1;

                                            if (!angular.isDefined($scope.formBuilder[next])) {
                                                $scope.formBuilder[next] = [];
                                                $scope.formBuilder[next].push(field);
                                            }

                                            $scope.layouts.groups[0].disabled = false;
                                        } else {
                                            $scope.formBuilder['0'].push(field);
                                        }
                                    });


                                } else {
                                    angular.forEach($scope.layouts.groups, function (group, i) {
                                        $scope.formBuilder[i] = [];
                                        if (!angular.isDefined(group.fields)) {
                                            var wait = false;
                                            angular.forEach(config.fields, function (field) {
                                                if (wait) {
                                                    return;
                                                }
                                                if (!done[field.code_name]) {
                                                    done[field.code_name] = 1;
                                                    if (field.is_structured) {
                                                        wait = true;
                                                    }

                                                    $scope.formBuilder[i].push(field);
                                                }
                                            });
                                        } else {
                                            angular.forEach(group.fields, function (field_key) {
                                                if (!done[field_key]) {
                                                    field = config.keyedFields[field_key];
                                                    $scope.formBuilder[i].push(field);
                                                    done[field_key] = 1;
                                                }
                                            });
                                        }
                                    });
                                }

                                $scope.$watch('dialog.toolbar.title', function (neww) {
                                    if (angular.isObject($scope.historyConfig)) {
                                        $scope.historyConfig.title = neww;
                                    }
                                });

                                // call config constructor, needed for posible after variable setup configurations
                                config.defaultInit($scope);
                                config.init($scope);
                                makeHistory();

                                $scope.$on('$destroy', function () {
                                    config.getScope = undefined;
                                });

                                defer.resolve($scope);
                            };

                            ctrl.$inject = ['$scope'];

                            opener[fn]($.extend({
                                templateUrl: 'core/models/manage.html',
                                controller: ctrl
                            }, config.modalConfig));

                            return completePromise;
                        }
                    };

                    return modelsEditorInstance;

                }
            };

            return modelsEditor;

        })).factory('modelsConfig', function () {
            // depency config loader
            var callbacks = [];
            return function (callback) {
                if (callback === true) {
                    return callbacks;
                }
                callbacks.push(callback);
            };
        }).factory('models', ng(function (endpoint, modelsMeta, $injector, modelsConfig, helpers, $q, GLOBAL_CONFIG) {
            // models depency should never be included directly or indirectly, because its depency on modelsMeta
            var models = {}, // all model instances
                modelCreate = function (kind) {
                    // creates a new service based on kind
                    // it will map every action into function which can be called in this way: models['12'].actions.search() etc.
                    var config = {},
                        service = {
                            kind: kind,
                            actions: {},
                            getCacheKey: function (key) {
                                return this.kind + '_' + key;
                            },
                            removeCache: function (key) {
                                return endpoint.removeCache(this.getCacheKey(key));
                            },
                            getCache: function (key) {
                                return endpoint.getCache(this.getCacheKey(key));
                            },
                            get: function (key) {
                                if (angular.isDefined(this.actions.search)) {
                                    return this.actions.search({
                                        search: {
                                            keys: [key]
                                        }
                                    });
                                }

                                console.error('get() relies on actions.search action. use actions.read() instead.');
                            },
                            paginate: function (config) {
                                var that = this,
                                    theConfig = {
                                        args: {
                                            search: {}
                                        },
                                        config: {}
                                    },
                                    searchAction = modelsMeta.getActionArguments(config.kind, 'search'),
                                    paginate = {
                                        loading: false,
                                        more: null,
                                        cursor: null,
                                        args: theConfig.args,
                                        load: function () {
                                            var promise;
                                            if (this.loading || this.more === false) {
                                                return false;
                                            }
                                            if (!theConfig.args.search.options) {
                                                theConfig.args.search.options = {};
                                            }
                                            theConfig.args.search.options.start_cursor = this.cursor;
                                            this.loading = true;
                                            promise = that.actions[theConfig.action ? theConfig.action : 'search'](theConfig.args, theConfig.config);
                                            promise.then(function (response) {
                                                if (response.data.errors) {
                                                    paginate.more = false;
                                                    return config.complete.call(this, response);
                                                }
                                                paginate.more = response.data.more;
                                                paginate.cursor = response.data.cursor;
                                                if (angular.isFunction(config.complete)) {
                                                    return config.complete.call(this, response);
                                                }
                                                return response;
                                            })['finally'](function () {
                                                paginate.loading = false;
                                            });
                                            return promise;
                                        }
                                    };
                                theConfig.args.search = searchAction.search['default'];
                                if (angular.isDefined(config.args)) {
                                    helpers.merge(config.args, theConfig.args);
                                    $.extend(theConfig, config);
                                }
                                return paginate;
                            },
                            reader: function (config) {
                                // reader instance that internally tracks the reader next read arguments.
                                // params provided are config, access, and callback
                                // and path to the structure that the reader will inject/read data
                                if (!angular.isArray(config.access)) {
                                    console.error('path must be array, ' + typeof config.access + ' given');
                                    return;
                                }

                                var fields,
                                    model = this,
                                    canLoadMore = function (nextReadArguments) {
                                        return helpers.getProperty(nextReadArguments, fields.join('.') + '.config.more');
                                    },
                                    init = function (access) {
                                        fields = [];
                                        angular.forEach(access, function (path) {
                                            if (isNaN(parseInt(path, 10))) {
                                                fields.push(path);
                                            }
                                        });
                                    },
                                    reader,
                                    readArgs,
                                    readRootArgs;

                                if (angular.isUndefined(config.next)) {
                                    readArgs = {};
                                    readRootArgs = config.args;
                                    config.next = readArgs;
                                    angular.forEach(config.access, function (part, i) {
                                        // parseInt can produce inconsistent stuff like 10_foo makes 10, so we must avoid names of
                                        // properties in datastore that begin with an number, which we do not
                                        if (!angular.isDefined(readArgs[part]) && isNaN(parseInt(part, 10))) {
                                            readArgs[part] = {
                                                config: {}
                                            };
                                            readArgs = readArgs[part];
                                        }
                                        // produce read path for the rpc
                                        readRootArgs = readRootArgs[part];
                                        if (angular.isUndefined(readRootArgs)) {
                                            return;
                                        }
                                        if (readRootArgs.key !== null && angular.isDefined(readRootArgs.key)) {
                                            if (!angular.isDefined(readArgs.config.keys)) {
                                                readArgs.config.keys = [];
                                            }
                                            readArgs.config.keys.push(readRootArgs.key);
                                        }
                                    });
                                }

                                // fields are now _images, pricetags, _product, _instances
                                init(config.access);

                                reader = {
                                    next: null,
                                    loading: false,
                                    access: config.access,
                                    more: canLoadMore(config.next),
                                    config: config,
                                    loaded: false,
                                    previous: null,
                                    state: function (config) {
                                        this.next = config.next;
                                        if (angular.isDefined(config.access)) {
                                            this.access = config.access;
                                            init(this.access);
                                        }
                                        if (angular.isDefined(config.more)) {
                                            this.more = config.more;
                                        } else {
                                            this.more = canLoadMore(this.next);
                                        }
                                    },
                                    setNextReadArguments: function (nextReadArguments) {
                                        this.next = nextReadArguments;
                                        this.more = canLoadMore(this.next);
                                    },
                                    setAccess: function (access) {
                                        this.access = access;
                                        init(access);
                                        this.more = canLoadMore(this.next);
                                    },
                                    load: function (loadConfig) {
                                        loadConfig = helpers.alwaysObject(loadConfig);
                                        if (angular.isUndefined(loadConfig.runLast) && (this.more === false || this.loading)) {
                                            return false;
                                        }
                                        var that = this,
                                            next = that.next,
                                            promise,
                                            oldNext,
                                            readArgsRpc;

                                        if (!next) {
                                            next = angular.copy(config.next);
                                        }

                                        if (!this.more) {
                                            oldNext = next;
                                            angular.forEach(fields, function (value, key) {
                                                if (angular.isUndefined(next[value])) {
                                                    next[value] = {};
                                                } else {
                                                    next = next[value];
                                                }
                                            });
                                            next = oldNext;
                                        }

                                        if (!loadConfig.hideLoading) {
                                            this.loading = true;
                                        }
                                        readArgsRpc = {
                                            key: config.key,
                                            read_arguments: next
                                        };

                                        if (loadConfig.runLast) {
                                            readArgsRpc = reader.previous || readArgsRpc;
                                        }

                                        promise = (config.read ? config.read(next) : (config.kind ? models[config.kind] : model).actions.read(readArgsRpc, loadConfig.rpcOptions));

                                        reader.previous = readArgsRpc;

                                        promise['finally'](function () {
                                            reader.loading = false;
                                            reader.loaded = true;
                                            if (loadConfig.runLastFinally) {
                                                loadConfig.runLastFinally();
                                            }
                                        });

                                        return promise.then(function (response) {
                                            if (response.data.errors) {
                                                that.more = false;
                                                return response;
                                            }
                                            var getAccess = [],
                                                items,
                                                loadedNext;
                                            angular.forEach(that.access, function (part) {
                                                if (!isNaN(parseInt(part, 10))) {
                                                    part = 0;
                                                }
                                                getAccess.push(part);
                                            });
                                            items = helpers.getProperty(response.data.entity, getAccess);

                                            if (loadConfig.runLast) {
                                                loadConfig.runLast(items);
                                                return response;
                                            }

                                            if (angular.isFunction(config.complete)) {
                                                config.complete(items);
                                            }

                                            loadedNext = response.data.entity._next_read_arguments;
                                            that.more = canLoadMore(loadedNext);

                                            if (that.more) {
                                                that.next = loadedNext;
                                            }

                                            return response;
                                        });
                                    }
                                };

                                return reader;

                            }
                        };

                    service.config = config;
                    angular.forEach(modelsMeta.getActions(kind), function (action, action_key) {
                        service.actions[action_key] = function (args, overrideConfig) {
                            var defaultArgs = modelsMeta.getDefaultActionArguments(kind, action_key),
                                defaults = angular.copy(config),
                                cache_key;

                            $.extend(defaultArgs, args);
                            if (angular.isDefined(overrideConfig)) {
                                if (overrideConfig.merge) {
                                    $.extend(defaults, overrideConfig);
                                } else {
                                    defaults = overrideConfig;
                                }
                            }

                            cache_key = config.cache;
                            if (angular.isDefined(defaults) && defaults.cache) {
                                cache_key = defaults.cache;
                            }
                            if (cache_key === true) {
                                // btoa is base64encode built-in, if cache key is true then the cache key will be autogenerated
                                cache_key = kind + '_' + action_key + '_' + window.btoa(angular.toJson(defaultArgs));
                            }
                            if (!angular.isDefined(cache_key) || cache_key === false) {
                                return endpoint.post(action_key, kind, defaultArgs, defaults);
                            }
                            delete defaults.cache;
                            return endpoint.cached(cache_key, action_key, kind, defaultArgs, defaults);

                        };
                    });
                    return service;
                };

            models.initialized = false;
            models.init = function () {
                if (models.initialized === true) {
                    return;
                }

                var modelsInfo = $injector.get('modelsInfo'),
                    callbacks;

                if (!angular.isDefined(modelsInfo['0'])) {
                    return;
                }

                angular.forEach(modelsInfo, function (meta, kind) {
                    models[kind] = modelCreate(kind);
                });

                callbacks = modelsConfig(true);
                angular.forEach(callbacks, function (callback) {
                    callback(models);
                });

                models.initialized = true;
            };

            if (GLOBAL_CONFIG.debug) {
                window._models = models;
            }

            return models;

        }));
}());
(function () {
    'use strict';
    angular.module('app')
        .factory('recordBrowser', ng(function (models, GLOBAL_CONFIG, $modal) {
            return {
                attach: function (config) {
                    return {
                        label: GLOBAL_CONFIG.subheaders.history,
                        include: 'core/misc/action.html',
                        action: function () {
                            $modal.open({
                                templateUrl: 'core/models/manage.html',
                                controller: ng(function ($scope) {
                                    $scope.dialog = {
                                        templateBodyUrl: 'core/record/list.html',
                                        toolbar: {
                                            hideSave: true,
                                            leftIcon: 'arrow_back',
                                            title: config.title + ' / History'
                                        }
                                    };
                                    var defaultReaderOpts = {
                                            access: ['_records'],
                                            key: config.key,
                                            next: {
                                                _records: {
                                                    config: {
                                                        more: true,
                                                        search: {
                                                            orders: [{
                                                                field: 'logged',
                                                                operator: 'desc'
                                                            }]
                                                        }
                                                    }
                                                }
                                            },
                                            complete: function (records) {
                                                $scope.history.records.extend(records);
                                            }
                                        };

                                    $.extend(defaultReaderOpts, config.reader);

                                    $scope.history = {
                                        records: [],
                                        reader: models[config.kind].reader(defaultReaderOpts),
                                        view: function (record) {
                                            $modal.open({
                                                templateUrl: 'core/models/manage.html',
                                                controller: ng(function ($scope) {
                                                    $scope.record = record;
                                                    $scope.dialog = {};
                                                    $scope.dialog.templateBodyUrl = 'core/record/view_body.html';
                                                    $scope.dialog.toolbar = {
                                                        hideSave: true,
                                                        leftIcon: 'arrow_back',
                                                        title: config.title + ' / History / Log Entry'
                                                    };
                                                })
                                            });
                                        }
                                    };

                                    $scope.history.reader.load();
                                })
                            });

                        }
                    };
                }
            };
        }));
}());(function () {
    'use strict';
    angular.module('app')
        .directive('selectInputMultiple', ng(function ($timeout, underscoreTemplate, $modal) {
            return {
                require: ['ngModel', '^?form'],
                link: function (scope, element, attrs, ctrls) {
                    var ngModel = ctrls[0],
                        formCtrl = ctrls[1],
                        grouping = scope.$eval(attrs.grouping),
                        items = scope.$eval(attrs.items),
                        view = scope.$eval(attrs.view),
                        listView = scope.$eval(attrs.listView),
                        search = scope.$eval(attrs.search),
                        select = scope.$eval(attrs.select),
                        init = (select && select.init ? select.init : null);

                    select.getHash = function (item) {
                        return (angular.isObject(item) ? item.key : item);
                    };
                    select.search = search;
                    select.anyItems = 0;
                    select.async = true;
                    select.loading = false;
                    select.multiple = true;
                    select.items = [];
                    select.find = function (value) {
                        if (value === null) {
                            return undefined;
                        }
                        var active,
                            missing,
                            get = function (val) {
                                var i,
                                    found;
                                if (!angular.isObject(select.items[0])) {
                                    i = select.items.indexOf(val);
                                    if (i !== -1) {
                                        found = select.items[i];
                                    }
                                } else {
                                    found = _.findWhere(select.items, {
                                        key: val
                                    });
                                }
                                return found;
                            };
                        if (select.multiple) {
                            missing = [];
                            active = [];
                            if (value && value.length) {
                                angular.forEach(value, function (val) {
                                    var gets = get(val);
                                    if (angular.isUndefined(gets)) {
                                        missing.push(val);
                                    } else {
                                        active.push(gets);
                                    }
                                });
                            }
                        } else {
                            active = get(value);
                            if (angular.isUndefined(active)) {
                                missing = value;
                            }
                        }
                        if (angular.isDefined(missing) && missing.length && select.search && select.search.ready) {
                            select.search.ready.then(function () {
                                if (select.search.missing) {
                                    select.search.missing(missing);
                                }
                            });
                        }
                        return active;
                    };
                    select.getActive = function () {
                        select.item = select.find(ngModel.$modelValue);
                        return select.item;
                    };
                    select.setItems = function (items) {
                        select.items = items;
                        select.collectActive();
                        if (grouping) {
                            select.grouping = grouping(select.items);
                        }
                        select.anyItems = items.length;
                    };
                    select.isSelected = function (item) {
                        var hash = select.getHash(item);
                        if (select.multiple) {
                            return $.inArray(hash, ngModel.$modelValue) !== -1;
                        }
                        return ngModel.$modelValue === hash;
                    };
                    select.remove = function (item) {
                        select.select(item);
                    };
                    select.anySelected = function () {
                        var any = true;
                        angular.forEach(select.multipleSelection, function (value) {
                            if (!any) {
                                any = value;
                            }
                        });
                        return any;
                    };
                    select.multipleSelection = {};
                    select.multipleSelect = function (item, nocheck) {
                        var hash = select.getHash(item),
                            hasIt = nocheck ? select.multipleSelection[hash] : !select.multipleSelection[hash],
                            already = ngModel.$modelValue || [],
                            selected = $.inArray(hash, ngModel.$modelValue) !== -1;
                        select.multipleSelection[hash] = hasIt;
                        if (!angular.isArray(select.item)) {
                            select.item = already;
                        }
                        if (hasIt) {
                            if (!selected) {
                                already.push(hash);
                                select.item.push(item);
                            }
                        } else {
                            if (selected) {
                                already.remove(hash);
                                select.item.remove(item);
                            }
                        }
                        ngModel.$setViewValue(already);
                        formCtrl.$setDirty();
                        select.close();
                    };

                    select.commitMultipleSelect = function (item) {
                        $timeout(function () {
                            select.multipleSelect(item, true);
                        }, 100);
                    };

                    select.collectActive = function () {
                        angular.forEach(select.items, function (item) {
                            var hash = select.getHash(item);
                            if (angular.isUndefined(select.multipleSelection[hash]) && $.inArray(hash, ngModel.$modelValue) !== -1) {
                                select.multipleSelection[hash] = true;
                            }
                        });
                    };

                    select.isChecked = function (item) {
                        return select.multipleSelection[select.getHash(item)];
                    };
                    select.select = function (item) {
                        select.multipleSelect(item);
                    };
                    select.close = angular.noop;
                    select.opened = false;
                    select.open = function ($event) {
                        if (select.opened) {
                            return;
                        }
                        select.opened = true;
                        $timeout(function () {
                            select.openSimpleDialog($event);
                        });
                    };
                    select.openSimpleDialog = function ($event) {
                        if (element.attr('disabled')) {
                            return;
                        }
                        if (select.search) {
                            select.search.query = {};
                        }
                        var attachTo = element.parents('.modal:first').find('.modal-dialog:first'),
                            choices;

                        if (!attachTo.length) {
                            attachTo = element.parents('body:first');
                        }

                        choices = underscoreTemplate.get(select.openTemplate || 'core/select/choices.html')({
                            select: select
                        });
                        $modal.open({
                            template: underscoreTemplate.get('core/select/single.html')().replace('{{content}}', choices),
                            targetEvent: $event,
                            parent: attachTo,
                            inDirection: false,
                            windowClass: 'modal-medium-simple ' + (select.windowClass || ''),
                            outDirection: false,
                            fullScreen: false,
                            backdrop: true,
                            controller: ng(function ($scope) {
                                $scope.select = select;
                                $scope.$on('$destroy', function () {
                                    select.opened = false;
                                    select.close = angular.noop;
                                });
                                $scope.close = function () {
                                    $scope.$close().then(select.afterClose || angular.noop);
                                };
                                select.close = function () {
                                    $scope.close();
                                };
                            })
                        });
                    };
                    if (!view) {
                        view = function (item) {
                            return angular.isObject(item) ? item.name : item;
                        };
                    }
                    select.view = view;
                    select.listView = listView || view;
                    ngModel.$formatters.push(function (value) {
                        select.collectActive();
                        select.item = select.find(value);
                        return value;
                    });
                    if (grouping) {
                        select.hasGrouping = true;
                        select.grouping = [];
                    }
                    select.setItems(items);
                    scope.$watchGroup([attrs.items + '.length', attrs.items], function (neww, old) {
                        if (neww[0] !== old[0] || neww[1] !== old[1]) {
                            select.setItems(scope.$eval(attrs.items));
                            select.getActive();
                            if (select.opened) {
                                $timeout(function () {
                                    $(window).triggerHandler('resize');
                                }, 0, false);
                            }
                        }
                    });

                    if (init) {
                        init(select, scope, element, attrs, ctrls);
                    }

                }
            };
        }))
        .directive('selectInput', ng(function ($simpleDialog, $$rAF, $mdConstant, underscoreTemplate, $timeout, $parse, helpers, $q, $modal) {
            return {
                replace: true,
                transclude: true,
                require: ['ngModel', '^?mdInputContainer', '^?form'],
                templateUrl: 'core/select/input.html',
                scope: true,
                link: function (scope, element, attrs, ctrls) {
                    var ngModel = ctrls[0],
                        containerCtrl = ctrls[1],
                        formCtrl = ctrls[2],
                        items = scope.$eval(attrs.items),
                        view = scope.$eval(attrs.view),
                        search = scope.$eval(attrs.search),
                        init = (search && search.init ? search.init : null),
                        multiple = scope.$eval(attrs.multiple),
                        async = scope.$eval(attrs.async),
                        grouping = scope.$eval(attrs.grouping),
                        listView = scope.$eval(attrs.listView),
                        placeholder = attrs.placeholder,
                        select = {},
                        timeout,
                        ngModelPipelineCheckValue,
                        dontOpen = false;
                    containerCtrl.input = element;
                    ngModelPipelineCheckValue = function (arg) {
                        var s = !ngModel.$isEmpty(arg);
                        if (angular.isArray(arg)) {
                            s = arg.length !== 0;
                        }
                        containerCtrl.setHasValue(s);
                        return arg;
                    };
                    scope.$watch(function () {
                        return ngModel.$invalid && ngModel.$touched;
                    }, containerCtrl.setInvalid);

                    ngModel.$parsers.push(ngModelPipelineCheckValue);
                    ngModel.$formatters.push(ngModelPipelineCheckValue);

                    element.on('keyup', function (ev) {
                        if (ev.keyCode === $mdConstant.KEY_CODE.ENTER) {
                            select.open();
                        }
                    }).on('click', function (ev) {
                        if (!dontOpen) {
                            select.open();
                        }
                        dontOpen = false;

                        ev.preventDefault();
                    }).on('blur', function (ev) {
                        containerCtrl.setFocused(false);
                    });
                    scope.$on('$destroy', function () {
                        containerCtrl.setFocused(false);
                        containerCtrl.setHasValue(false);
                        containerCtrl.input = null;
                    });
                    select.getHash = function (item) {
                        return (angular.isObject(item) ? item.key : item);
                    };
                    select.async = async;
                    select.placeholder = placeholder;
                    select.loading = false;
                    select.multiple = multiple;
                    select.items = [];
                    select.find = function (value) {
                        if (value === null) {
                            return undefined;
                        }
                        var active,
                            missing,
                            get = function (val) {
                                var i,
                                    found;
                                if (!angular.isObject(select.items[0])) {
                                    i = select.items.indexOf(val);
                                    if (i !== -1) {
                                        found = select.items[i];
                                    }
                                } else {
                                    found = _.findWhere(select.items, {
                                        key: val
                                    });
                                }
                                return found;
                            };
                        if (select.multiple) {
                            missing = [];
                            active = [];
                            if (value && value.length) {
                                angular.forEach(value, function (val) {
                                    var gets = get(val);
                                    if (angular.isUndefined(gets)) {
                                        missing.push(val);
                                    } else {
                                        active.push(gets);
                                    }
                                });
                            }
                        } else {
                            active = get(value);
                            if (angular.isUndefined(active)) {
                                missing = value;
                            }
                        }
                        if (angular.isDefined(missing) && missing.length && select.search && select.search.ready) {
                            select.search.ready.then(function () {
                                if (select.search.missing) {
                                    select.search.missing(missing);
                                }
                            });
                        }
                        return active;
                    };
                    select.getActive = function () {
                        select.item = select.find(ngModel.$modelValue);
                        return select.item;
                    };
                    select.setItems = function (items) {
                        select.items = items;
                        select.collectActive();
                        if (grouping) {
                            select.grouping = grouping(select.items);
                        }
                    };
                    select.isSelected = function (item) {
                        var hash = select.getHash(item);
                        if (select.multiple) {
                            return $.inArray(hash, ngModel.$modelValue) !== -1;
                        }
                        return ngModel.$modelValue === hash;
                    };
                    select.anyUnselected = function () {
                        return true;
                    };
                    select.anySelected = function () {
                        return true;
                    };
                    select.multipleSelection = {};
                    select.multipleSelect = function (item) {
                        var hash = select.getHash(item),
                            hasIt = !select.multipleSelection[hash],
                            already = ngModel.$modelValue || [],
                            selected = $.inArray(hash, ngModel.$modelValue) !== -1;
                        select.multipleSelection[hash] = hasIt;
                        if (select.multiple) {
                            return;
                        }
                        if (!angular.isArray(select.item)) {
                            select.item = already;
                        }
                        if (hasIt) {
                            if (!selected) {
                                already.push(hash);
                                select.item.push(item);
                            }
                        } else {
                            if (selected) {
                                already.remove(hash);
                                select.item.remove(item);
                            }
                        }
                        ngModel.$setViewValue(already);
                        formCtrl.$setDirty();
                        ngModelPipelineCheckValue(already);
                    };

                    select.completeMultiSelection = function () {
                        var selected = [],
                            founds = [];
                        angular.forEach(select.items, function (item) {
                            var hash = select.getHash(item);
                            if (select.multipleSelection[hash]) {
                                selected.push(hash);
                                founds.push(item);
                            }
                        });
                        ngModel.$setViewValue(selected);
                        formCtrl.$setDirty();
                        ngModelPipelineCheckValue(selected);
                        select.item = founds;
                        select.close();
                    };


                    select.collectActive = function () {
                        angular.forEach(select.items, function (item) {
                            var hash = select.getHash(item);
                            if (angular.isUndefined(select.multipleSelection[hash]) && $.inArray(hash, ngModel.$modelValue) !== -1) {
                                select.multipleSelection[hash] = true;
                            }
                        });
                    };

                    select.isChecked = function (item) {
                        return false;
                    };
                    select.select = function (item) {
                        var val = select.getHash(item);
                        ngModel.$setViewValue(val);
                        select.item = item;
                        select.close();
                    };
                    select.close = angular.noop;
                    select.opened = false;
                    select.open = function ($event) {
                        if (select.opened) {
                            return;
                        }
                        select.opened = true;
                        $timeout(function () {
                            select.openSimpleDialog($event);
                        });
                    };
                    select.openSimpleDialog = function ($event) {
                        if (element.attr('disabled')) {
                            return;
                        }
                        if (select.search) {
                            select.search.query = {};
                        }
                        select.multipleSelection = {};
                        select.collectActive();

                        var attachTo = element.parents('.modal:first').find('.modal-dialog:first'),
                            choices,
                            root;

                        if (!attachTo.length) {
                            attachTo = element.parents('body:first');
                        }

                        choices = underscoreTemplate.get(select.openTemplate || 'core/select/choices.html')({
                            select: select
                        });
                        root = choices;
                        if (select.multiple || async) {
                            root = underscoreTemplate.get('core/select/single.html')().replace('{{content}}', choices);
                            $event = undefined;
                        }

                        (select.multiple || async ? $modal.open : $simpleDialog.show)({
                            template: root,
                            popFrom: ($event ? $event.target : undefined),
                            targetEvent: $event,
                            parent: attachTo,
                            inDirection: false,
                            windowClass: 'modal-medium-simple ' + (select.windowClass ? select.windowClass : ''),
                            outDirection: false,
                            fullScreen: false,
                            backdrop: true,
                            disableScroll: [element.parents('md-content:first'), element.parents('.fixed-height:first')],
                            onBeforeHide: function (dialogEl, options) {
                                $(window).off('resize', options.resize);
                            },
                            onBeforeShow: function (dialogEl, options) {
                                var nextDefer = $q.defer(),
                                    nextPromise = nextDefer.promise,
                                    nextActive = false,
                                    firstTabbable = dialogEl.find('[tabindex="2"]'),
                                    animateSelect = function () {
                                        var target = element.parents('md-input-container:first');
                                        options.resize = function () {
                                            var targetOffset = target.offset(),
                                                elementOffset = element.offset(),
                                                parent = options.parent,
                                                parentOffset = parent.offset(),
                                                paddingTop = async ? 24 : 16,
                                                paddingBottom = async ? 24 : 16,
                                                parentHeight = options.parent.height(),
                                                scrollElement = dialogEl.find('md-content'),
                                                maxTop,
                                                activeOffset,
                                                active = dialogEl.find('.list-row-is-active'),
                                                toolbar = attachTo.find('md-toolbar'),
                                                toolbarHeight = 0,
                                                newTop,
                                                totalHeight,
                                                wrapAround,
                                                wrapAroundOffset,
                                                nextActive,
                                                innerHeight;
                                            if (active.length) {
                                                activeOffset = active.offset();
                                                wrapAroundOffset = activeOffset;
                                                wrapAround = active;
                                            } else {
                                                wrapAroundOffset = firstTabbable.offset();
                                                wrapAround = firstTabbable;
                                            }
                                            if (toolbar.length) {
                                                toolbarHeight = toolbar.height();
                                            }
                                            maxTop = parentOffset.top + paddingTop + toolbarHeight;
                                            innerHeight = parentHeight - (paddingBottom + paddingTop + toolbarHeight);
                                            dialogEl.width(target.width());
                                            if ((dialogEl.height() > parentHeight) || (scrollElement.prop('scrollHeight') > parentHeight) || (dialogEl.height() > innerHeight)) {
                                                dialogEl.css({
                                                    top: maxTop,
                                                    left: elementOffset.left
                                                }).height(innerHeight);
                                            } else {
                                                dialogEl.css(elementOffset);
                                                if (active.length) {
                                                    // position the selection at center of active item
                                                    newTop = elementOffset.top - activeOffset.top + (active.height() / 5);
                                                } else {
                                                    // position the div at the center if no item is selected
                                                    newTop = (targetOffset.top) - (dialogEl.height() / 2) + paddingTop;
                                                }
                                                if (newTop > maxTop) {
                                                    totalHeight = newTop + dialogEl.height();
                                                    if (totalHeight + 24 > parentHeight) {
                                                        newTop = newTop - (totalHeight - (parentHeight - 24));
                                                        if (newTop < maxTop) {
                                                            newTop = maxTop;
                                                        }
                                                    }
                                                    dialogEl.css('top', newTop);
                                                } else {
                                                    dialogEl.css('top', maxTop);
                                                }
                                            }
                                            if (active.length && !select.multiple) {
                                                scrollElement.scrollTop(scrollElement.scrollTop() - scrollElement.offset().top + active.offset().top);
                                            }

                                            if (wrapAroundOffset) {
                                                dialogEl.css($mdConstant.CSS.TRANSFORMORIGIN, (wrapAroundOffset.left + target.width() / 2) + 'px ' + (wrapAroundOffset.top + active.height() / 2 - scrollElement.scrollTop()) + 'px 0px');
                                            }
                                        };
                                        options.resize();
                                        $(window).on('resize', function () {
                                            setTimeout(options.resize, 100);
                                        });

                                        dialogEl.oneAnimationEnd(function (ev) {
                                            nextDefer.resolve();
                                            nextActive = dialogEl.find('.list-row-is-active:first');
                                            if (!nextActive.length) {
                                                nextActive = firstTabbable;
                                            }
                                            if (select.search) {
                                                setTimeout(function () {
                                                    dialogEl.find('input[type="search"]').focus();
                                                }, 100);
                                            } else {
                                                nextActive.focus();
                                            }
                                            dialogEl.addClass('opacity-in');
                                        }).on('keyup', function (ev) {
                                            if (!nextActive) {
                                                return;
                                            }
                                            var original = nextActive,
                                                doFocus = false,
                                                indx = -1;
                                            if (ev.keyCode === $mdConstant.KEY_CODE.DOWN_ARROW) {
                                                nextActive = nextActive.next();
                                                doFocus = true;
                                            } else if (ev.keyCode === $mdConstant.KEY_CODE.UP_ARROW) {
                                                nextActive = nextActive.prev();
                                                doFocus = true;
                                            } else if (ev.keyCode === $mdConstant.KEY_CODE.ENTER) {
                                                nextActive = dialogEl.find('.simple-dialog-option:focus');
                                                if (!nextActive.length) {
                                                    nextActive = dialogEl.find('.list-row-is-active:first');
                                                }
                                                if (nextActive.length) {
                                                    indx = $parse(nextActive.attr('item'))(nextActive.scope());
                                                } else {
                                                    indx = select.items[0];
                                                }
                                                if (indx) {
                                                    select.select(indx);
                                                }
                                            }
                                            if (!nextActive.length && doFocus) {
                                                nextActive = original;
                                            }
                                            if (doFocus) {
                                                nextActive.focus();
                                            }
                                        });

                                        $$rAF(function () {
                                            dialogEl.addClass('fade in');
                                            dontOpen = false;
                                        });


                                    };

                                $$rAF(animateSelect);

                                return nextPromise;
                            },
                            controller: ng(function ($scope) {
                                select.close = function () {
                                    if (select.multiple || select.async) {
                                        $scope.close();
                                    } else {
                                        $simpleDialog.hide();
                                    }
                                };
                                $scope.close = function () {
                                    $scope.$close().then(select.afterClose || angular.noop);
                                };
                                $scope.select = select;
                                $scope.$on('$destroy', function () {
                                    select.opened = false;
                                    containerCtrl.setFocused(false);
                                    //dontOpen = true;
                                    element.focus();
                                });
                            })
                        });
                    };
                    if (!view) {
                        view = function (item) {
                            return angular.isObject(item) ? item.name : item;
                        };
                    }
                    select.view = view;
                    select.listView = listView || view;
                    ngModel.$formatters.push(function (value) {
                        select.item = select.find(value);
                        return value;
                    });

                    select.isFilterMatch = function (item) {
                        if (!search) {
                            return true;
                        }
                        var toFilter,
                            term = select.getFindTerm(),
                            match,
                            maybe = select.search.query;
                        if (select.search.filterProp) {
                            maybe = maybe[select.search.filterProp];
                        }
                        if (!maybe || maybe.length < 1) {
                            return true;
                        }
                        if (select.search.filterProp) {
                            toFilter = item[select.search.filterProp];
                        } else {
                            toFilter = item;
                        }
                        match = toFilter.toString().toLowerCase().indexOf(term) !== -1;
                        return match;
                    };

                    select.getFindTerm = function () {
                        return $parse(select.search.filterProp)(select.search.query);
                    };

                    if (search) {
                        select.search = {
                            query: {},
                            delay: 200,
                            enabled: false,
                            doFind: function () {
                                var term = select.getFindTerm();
                                if (timeout) {
                                    clearTimeout(timeout);
                                }
                                if (select.search.find) {
                                    timeout = setTimeout(function () {
                                        select.search.find(term);
                                    }, select.search.delay);
                                }

                                $timeout(function () {
                                    $(window).triggerHandler('resize');
                                }, 0, false);
                            }
                        };
                        $.extend(select.search, search);
                        select.search.filterProp = (select.search.filterProp ? select.search.filterProp : 'name');
                        if (!select.search.model) {
                            select.search.model = 'select.search.query' + ('.' + select.search.filterProp);
                        }
                    }
                    if (grouping) {
                        select.hasGrouping = true;
                        select.grouping = [];
                    }
                    select.setItems(items);
                    scope.$watchGroup([attrs.items + '.length', attrs.items], function (neww, old) {
                        if (neww[0] !== old[0] || neww[1] !== old[1]) {
                            select.setItems(scope.$eval(attrs.items));
                            select.getActive();
                            if (select.opened) {
                                $timeout(function () {
                                    $(window).triggerHandler('resize');
                                }, 0, false);
                            }
                        }
                    });

                    scope.select = select;

                    if (init) {
                        init(select, scope, element, attrs, ctrls);
                    }

                }
            };
        }));
}());
(function () {
    'use strict';
    angular.module('app').directive('imageSlider', ng(function ($timeout, $parse) {
        return {
            restrict: 'A',
            link: function (scope, element, attrs) {
                var callback = $parse(attrs.imageSliderLoadMore),
                    parent = element.parent('.image-slider-outer:first'),
                    steadyScroll,
                    anyMore = true,
                    tryToLoadSteady = function (values, done) {
                        if (!anyMore) {
                            return false;
                        }
                        anyMore = false;
                        callback(scope, {
                            callback: function (response, state) {
                                done();
                                anyMore = state;
                            }
                        });
                    },
                    measure = function () {
                        var tw = 0,
                            notDisplayNone = function () {
                                return $(this).css('display') !== 'none';
                            };
                        element.find('.image-slider-item').filter(notDisplayNone).each(function () {
                            tw += $(this).width();
                        });

                        element.width(Math.ceil(tw) + element.find('.vertical-loader').filter(notDisplayNone).width());
                    },
                    resize = function () {
                        var height = parent.parents('.fixed-height:first').height(),
                            bar = parent.parents('.modal:first').find('.new-pricetag-bar');
                        if (bar.length) {
                            height -= bar.outerHeight();
                        }
                        if (height) {
                            parent.height(height);
                            scope.$broadcast('imageSliderResized', height);
                        }
                    };

                resize();
                resize = _.throttle(resize, 100);
                scope.$on('modalResize', resize);
                scope.$on('reMeasureImageSlider', function () {
                    resize();
                    measure();
                });

                scope.$on('readyImageSlider', function () {
                    resize();
                    measure();
                    steadyScroll = new Steady({
                        throttle: 100,
                        scrollElement: parent.get(0),
                        handler: tryToLoadSteady
                    });

                    steadyScroll.addTracker('checkLeft', function () {
                        if (!callback) {
                            return;
                        }
                        var p = parent.get(0),
                            maxscroll,
                            sense;
                        if (!p) {
                            steadyScroll.stop();
                            return;
                        }
                        maxscroll = p.scrollWidth - p.clientWidth;
                        sense = maxscroll - parent.scrollLeft();
                        if (sense < 300) {
                            return true;
                        }
                        return false;
                    });

                    steadyScroll.addCondition('checkLeft', true);
                    parent.data('steady', steadyScroll);
                });

                scope.$on('$destroy', function () {
                    if (steadyScroll) {
                        steadyScroll.stop();
                        parent.data('steady', undefined);
                    }
                });
            }
        };
    })).directive('sliderImage', ng(function ($timeout, helpers, GLOBAL_CONFIG) {
        return {
            restrict: 'A',
            link: function (scope, element, attrs) {
                var image = scope.$eval(attrs.sliderImage),
                    run = function () {
                        var bar = element.parents('.modal:first').find('.new-pricetag-bar'),
                            newHeight = element.parents('.fixed-height:first').innerHeight() - window.SCROLLBAR_WIDTH - (bar.length ? bar.outerHeight() : 0),
                            newWidth = Math.ceil(newHeight * image.proportion),
                            imageSize = helpers.closestLargestNumber(GLOBAL_CONFIG.imageSizes, newHeight),
                            originalNewHeight = newHeight,
                            reactingElement = element.parents('.image-slider-item:first');
                        newWidth = helpers.newWidthByHeight(newWidth, originalNewHeight, newHeight);
                        element.bind('load', function () {
                            scope.$broadcast('readySingleImageSlider', reactingElement);
                        }).attr('src', image.serving_url + '=s' + imageSize)
                            .width(newWidth)
                            .height(newHeight);

                        reactingElement
                            .width(newWidth)
                            .height(newHeight);
                    },
                    resize = function () {
                        run();
                        scope.$emit('reMeasureImageSlider');
                    };

                $timeout(function () {
                    run();
                    if (scope.$last) {
                        scope.$emit('readyImageSlider');
                    }
                });
                scope.$on('modalResize', resize);
                scope.$on('itemDelete', function () {
                    $timeout(resize);
                });

            }
        };
    }));
}());
﻿(function () {
    'use strict';
    angular.module('app').factory('social', ng(function ($modal, GLOBAL_CONFIG) {
        var social = {
            share: function (meta, embed, link) {
                $modal.open({
                    templateUrl: 'core/social/share.html',
                    controller: ng(function ($scope) {
                        $scope.socials = [{
                            name: 'Facebook',
                            key: 'facebook',
                            command: 'https://www.facebook.com/sharer.php?s=100&p[url]={p[url]}&p[images][0]={p[images][0]}&p[title]={p[title]}&p[summary]={p[summary]}',
                            require: ['href']
                        }, {
                            name: 'Twitter',
                            key: 'twitter',
                            command: 'https://twitter.com/intent/tweet?text={text}&url={url}',
                            require: ['url', 'text']
                        }, {
                            name: 'Pinterest',
                            key: 'pinterest',
                            command: 'https://www.pinterest.com/pin/create/button/?url={url}&media={media}&description={description}',
                            require: ['url', 'media', 'description']
                        }, {
                            name: 'Reddit',
                            key: 'reddit',
                            command: 'https://www.reddit.com/submit?url={url}&title={title}',
                            require: ['url', 'title']
                        }, {
                            name: 'Linkedin',
                            key: 'linkedin',
                            command: 'https://www.linkedin.com/shareArticle?url={url}&title={title}',
                            require: ['url', 'title']
                        }, {
                            name: 'Google+',
                            icon: 'googleplus',
                            key: 'googleplus',
                            command: 'https://plus.google.com/share?url={url}',
                            require: ['url']
                        }, {
                            name: 'Tumblr',
                            key: 'tumblr',
                            command: 'https://www.tumblr.com/share/link?url={url}&name={name}&description={description}',
                            require: ['url', 'name', 'description']
                        }];

                        $scope.getIcon = function (soc) {
                            return '/client/dist/static/social/' + (soc.icon || soc.name.toLowerCase()) + '.png';
                        };

                        $scope.share = function (soc) {
                            var w = $(window).width() / 1.3,
                                h = $(window).height() / 1.3,
                                left = (screen.width / 2) - (w / 2),
                                top = (screen.height / 2) - (h / 2),
                                cmd = soc.command,
                                popup;
                            angular.forEach(soc.require, function (key) {
                                var hasit = meta[soc.key][key];
                                if (angular.isUndefined(hasit)) {
                                    cmd = cmd.replace('&' + key + '={' + key + '}', '');
                                    cmd = cmd.replace('?' + key + '={' + key + '}', '');
                                } else {
                                    cmd = cmd.replace('{' + key + '}', encodeURIComponent(meta[soc.key][key]));
                                }
                            });
                            popup = window.open(cmd, 'Share to ' + soc.name, 'toolbar=no, location=no, directories=no, status=no, menubar=no, scrollbars=1, resizable=no, copyhistory=no, width=' + w + ', height=' + h + ', top=' + top + ', left=' + left);
                            popup.focus();
                            return popup;
                        };

                        $scope.container = {};

                        if (angular.isUndefined(link)) {
                            link = {
                                src: meta.googleplus.url
                            };
                        }

                        $scope.link = {
                            enabled: link,
                            values: {
                                url: (angular.isObject(link) ? link.src : link)
                            },
                            fields: [{
                                type: 'SuperTextProperty',
                                code_name: 'url',
                                ui: {
                                    label: false,
                                    writable: true,
                                    args: 'link.values.url',
                                    parentArgs: 'link.values',
                                    attrs: {
                                        readonly: 'true',
                                        onclick: 'this.select()'
                                    }
                                }

                            }]
                        };

                        $scope.embed = {
                            enabled: embed,
                            values: {
                                width: '100%',
                                height: '100%',
                                code: ''
                            },
                            setCode: function () {
                                if (!embed) {
                                    return '';
                                }
                                var values = $scope.embed.values;
                                values.code = '<iframe width="' + values.width + '" height="' + values.height + '" src="' + embed.src + '" frameborder="0" allowfullscreen></iframe>';
                                return values.code;
                            },
                            fields: [{
                                type: 'SuperStringProperty',
                                code_name: 'width',
                                required: true,
                                ui: {
                                    writable: true,
                                    args: 'embed.values.width',
                                    parentArgs: 'embed.values',
                                    attrs: {
                                        'ng-change': 'embed.setCode()'
                                    }
                                }

                            }, {
                                type: 'SuperStringProperty',
                                code_name: 'height',
                                required: true,
                                ui: {
                                    writable: true,
                                    args: 'embed.values.height',
                                    parentArgs: 'embed.values',
                                    attrs: {
                                        'ng-change': 'embed.setCode()'
                                    }
                                }

                            }, {
                                type: 'SuperTextProperty',
                                code_name: 'code',
                                ui: {
                                    writable: true,
                                    args: 'embed.values.code',
                                    parentArgs: 'embed.values',
                                    attrs: {
                                        readonly: 'true',
                                        onclick: 'this.select()'
                                    }
                                }

                            }]
                        };

                        $scope.embed.setCode();
                    })
                });
            }
        };
        if (GLOBAL_CONFIG.debug) {
            window._social = social;
        }
        return social;
    }));

}());
// Version (see package.json)
// AngularJS simple file upload directive
// this directive uses an iframe as a target
// to enable the uploading of files without
// losing focus in the ng-app.
//
// <div ng-app="app">
//   <div ng-controller="mainCtrl">
//    <form ng-attr-action="/uploads"
//      ng-upload="completed(content)">
//      ng-upload-loading="loading()"
//      <input type="file" name="avatar"></input>
//      <input type="submit" value="Upload"
//         ng-disabled="$isUploading"></input>
//    </form>
//  </div>
// </div>
//
//  angular.module('app', ['ngUpload'])
//    .controller('mainController', function($scope) {
//      $scope.loading = function() {
//        console.log('loading...');
//      }
//      $scope.completed = function(content) {
//        console.log(content);
//      };
//  });
//
angular.module('app')
    .directive('uploadSubmit', ["$parse", function ($parse) {
        // Utility function to get the closest parent element with a given tag
        function getParentNodeByTagName(element, tagName) {
            element = angular.element(element);
            var parent = element.parent();
            tagName = tagName.toLowerCase();

            if (parent && parent[0].tagName.toLowerCase() === tagName) {
                return parent;
            } else {
                return !parent ? null : getParentNodeByTagName(parent, tagName);
            }
        }
        return {
            restrict: 'AC',
            link: function (scope, element, attrs) {
                element.bind('click', function ($event) {
                    // prevent default behavior of click
                    if ($event) {
                        $event.preventDefault();
                        $event.stopPropagation();
                    }

                    if (element.attr('disabled')) {
                        return;
                    }
                    var form = getParentNodeByTagName(element, 'form');
                    form.triggerHandler('submit');
                    form[0].submit();
                });
            }
        };
    }])
    .directive('ngUpload', ["$log", "$parse", "$document", "$rootScope", "errorHandling", "modelsUtil",
        function ($log, $parse, $document, $rootScope, errorHandling, modelsUtil) {
            var iframeID = 1;
            // Utility function to get meta tag with a given name attribute
            function getMetaTagWithName(name) {
                var head = $document.find('head');
                var match;

                angular.forEach(head.find('meta'), function (element) {
                    if (element.getAttribute('name') === name) {
                        match = element;
                    }
                });

                return angular.element(match);
            }

            return {
                require: 'form',
                restrict: 'AC',
                link: function (scope, element, attrs, ctrl) {
                    // Give each directive instance a new id
                    iframeID++;

                    var formController = ctrl;

                    function setLoadingState(state) {
                        scope.$isUploading = state;
                    }

                    var options = {};
                    // Options (just 1 for now)
                    // Each option should be prefixed with 'upload-options-' or 'uploadOptions'
                    // {
                    //    // add the Rails CSRF hidden input to form
                    //    enableRailsCsrf: bool
                    // }
                    var fn = attrs.ngUpload ? $parse(attrs.ngUpload) : angular.noop;
                    var errorFn = attrs.ngUploadError ? $parse(attrs.ngUploadError) : angular.noop;
                    var loading = attrs.ngUploadLoading ? $parse(attrs.ngUploadLoading) : null;
                    var opts = scope.$eval(attrs.ngUploadOptions) || {};
                    var normalize = (angular.isDefined(opts.normalize) ? opts.normalize : true);

                    if (attrs.hasOwnProperty("uploadOptionsConvertHidden")) {
                        // Allow blank or true
                        options.convertHidden = attrs.uploadOptionsConvertHidden != "false";
                    }

                    if (attrs.hasOwnProperty("uploadOptionsEnableRailsCsrf")) {
                        // allow for blank or true
                        options.enableRailsCsrf = attrs.uploadOptionsEnableRailsCsrf != "false";
                    }

                    if (attrs.hasOwnProperty("uploadOptionsBeforeSubmit")) {
                        options.beforeSubmit = $parse(attrs.uploadOptionsBeforeSubmit);
                    }

                    element.attr({
                        'target': 'upload-iframe-' + iframeID,
                        'method': 'post',
                        'enctype': 'multipart/form-data',
                        'encoding': 'multipart/form-data'
                    });

                    var config = {
                        url: element.attr('action')
                    };

                    var iframe = angular.element(
                        '<iframe name="upload-iframe-' + iframeID + '" ' +
                        'border="0" width="0" height="0" ' +
                        'style="width:0px;height:0px;border:none;display:none">'
                    );

                    // If enabled, add csrf hidden input to form
                    if (options.enableRailsCsrf) {
                        var input = angular.element("<input />");
                        input.attr("class", "upload-csrf-token");
                        input.attr("type", "hidden");
                        input.attr("name", getMetaTagWithName('csrf-param').attr('content'));
                        input.val(getMetaTagWithName('csrf-token').attr('content'));

                        element.append(input);
                    }
                    element.after(iframe);

                    setLoadingState(false);
                    // Start upload
                    element.bind('submit', function uploadStart() {
                        // if form is invalid don't submit (e.g. keypress 13)
                        if (formController && formController.$invalid) return false;
                        // perform check before submit file
                        if (options.beforeSubmit && options.beforeSubmit(scope, {}) == false) return false;

                        // bind load after submit to prevent initial load triggering uploadEnd
                        iframe.bind('load', uploadEnd);

                        // If convertHidden option is enabled, set the value of hidden fields to the eval of the ng-model
                        if (options.convertHidden) {
                            angular.forEach(element.find('input'), function (el) {
                                var _el = angular.element(el);
                                if (_el.attr('ng-model') &&
                                    _el.attr('type') &&
                                    _el.attr('type') == 'hidden') {
                                    _el.attr('value', scope.$eval(_el.attr('ng-model')));
                                }
                            });
                        }

                        if (!scope.$$phase) {
                            scope.$apply(function () {
                                if (loading) loading(scope);
                                setLoadingState(true);
                            });
                        } else {
                            if (loading) loading(scope);
                            setLoadingState(true);
                        }

                        scope.$broadcast('ngUploadSubmit');
                        $rootScope.$broadcast('disableUI', true);

                    });

                    // Finish upload
                    function uploadEnd() {
                        // unbind load after uploadEnd to prevent another load triggering uploadEnd
                        iframe.unbind('load');
                        if (!scope.$$phase) {
                            scope.$apply(function () {
                                setLoadingState(false);
                            });
                        } else {
                            setLoadingState(false);
                        }
                        // Get iframe body contents
                        var bodyContent = (iframe[0].contentDocument ||
                            iframe[0].contentWindow.document).body;
                        var content;
                        try {
                            content = angular.fromJson(bodyContent.innerText || bodyContent.textContent);
                        } catch (e) {
                            // Fall back to html if json parse failed
                            content = bodyContent.innerHTML;
                            $log.warn('Response is not valid JSON');
                        }

                        var response = {
                                content: {
                                    data: content
                                }
                            },
                            noErrors = (content && angular.isObject(content) && !content.errors);
                        // if outside a digest cycle, execute the upload response function in the active scope
                        // else execute the upload response function in the current digest
                        if (normalize && noErrors) {
                            if (angular.isDefined(content.entities)) {
                                modelsUtil.normalizeMultiple(content.entities);
                            } else if (angular.isDefined(content.entity)) {
                                modelsUtil.normalize(content.entity);
                            }
                        }
                        if (noErrors) {
                            if (!scope.$$phase) {
                                scope.$apply(function () {
                                    fn(scope, response);
                                });
                            } else {
                                fn(scope, response);
                            }
                        } else {
                            if (!scope.$$phase) {
                                scope.$apply(function () {
                                    errorFn(scope, response);
                                });
                            } else {
                                errorFn(scope, response);
                            }
                        }
                        $rootScope.$broadcast('disableUI', false);

                        if (noErrors) {
                            scope.$broadcast('ngUploadComplete', content);
                        } else {
                            errorHandling.snackbar(content.errors);
                            scope.$broadcast('ngUploadCompleteError', content);
                        }


                    }
                }
            };
        }
    ]);
(function () {
    'use strict';
    angular.module('app').run(ng(function (helpers) {
        helpers.responsive = {
            isTouch: function () {
                return Modernizr.touch;
            },
            isMobile: function () {
                return $('#is-mobile').css('visibility') === 'visible';
            },
            isTablet: function () {
                return $('#is-tablet').css('visibility') === 'visible';
            },
            isDesktop: function () {
                return !this.isMobile();
            },
            isLandscape: function () {
                return $('#is-landscape').css('visibility') === 'visible';
            },
            isPortrait: function () {
                return !this.isLandscape();
            }
        };
    }));
}());
(function () {
    'use strict';
    // code for account
    angular.module('app').constant('LOGIN_PROVIDERS', [{
            name: 'Google',
            id: 1
        }, {
            name: 'Facebook',
            id: 2
        }, {
            name: 'Twitter',
            id: 3
        }, {
            name: 'Pinterest',
            id: 4
        }])
        .factory('mappedLoginProviders', ng(function (LOGIN_PROVIDERS) {
            var mappedLoginProviders = {};
            angular.forEach(LOGIN_PROVIDERS, function (value) {
                mappedLoginProviders[value.id] = value;
            });
            return mappedLoginProviders;
        }))
        .controller('LoginProviderConnectedController', ng(function ($scope, snackbar, currentAccount, models) {
            models['11'].manageModal(currentAccount, {
                fromRedirect: true
            }).then(function () {
                snackbar.showK('identityConnected');
            });
        }))
        .controller('AccountLoginStatusController', ng(function ($scope, $location, $state, snackbar) {
            var data = $location.search(),
                errors;
            if (data.success) {
                $state.go('home');
            } else {
                if (data.errors) {
                    errors = angular.fromJson(data.errors);
                    if (errors && errors.action_denied) {
                        snackbar.showK('accessDenied');
                    }
                }
            }
        })).controller('LoginLinksController', ng(function ($scope, endpoint, currentAccount, models) {

            $scope.authorization_urls = {};
            if (currentAccount._is_guest === undefined || currentAccount._is_guest) {
                models['11'].actions.login({
                    login_method: '1'
                }).then(function (response) {
                    $scope.authorization_urls = response.data.authorization_urls;
                });
            }

            $scope.login = function (type) {
                endpoint.removeCache('currentAccount');
                window.location.replace($scope.authorization_urls[type]);
            };

        })).controller('AccountManagementController', ng(function ($scope, currentAccount, models, modelsUtil) {

            $scope.settings = function () {
                models['11'].manageModal(currentAccount);
            };
            $scope.logout = function () {
                models['11'].logout(currentAccount.key);
            };
        })).filter('formatLoginProivider', ng(function (mappedLoginProviders) {
            return function (value) {
                var splits = value.split('-'),
                    out = '';
                if (splits && splits[1]) {
                    out = mappedLoginProviders[splits[1]].name;
                }
                return out;
            };
        })).run(ng(function (modelsConfig, channelApi, channelNotifications, currentAccount, $http, $state, endpoint, $window, modelsEditor, GLOBAL_CONFIG, modelsMeta, modelsUtil, $modal, helpers, modals, $q, mappedLoginProviders, LOGIN_PROVIDERS, snackbar) {

            var getProvider = function (ident) {
                return ident.identity.split('-')[1];
            };
            modelsConfig(function (models) {

                $.extend(models['11'], {
                    channel: function () {
                        var promise = this.actions.create_channel(undefined, {
                            cache: 'accountChannel',
                            cacheType: 'memory'
                        });
                        return promise.then(function (response) {
                            var token = response.data.token;
                            return {
                                token: token,
                                channel: channelApi.create(token)
                            };
                        });
                    },
                    channelNotifications: function (config) {
                        config = helpers.alwaysObject(config);
                        var promise = this.channel();
                        return promise.then(function (response) {
                            var token = response.token;
                            return {
                                token: token,
                                channel: channelNotifications.create(token, config.callback)
                            };
                        });
                    },
                    adminManageModal: function (account, extraConfig) {
                        return this.manageModal(account, extraConfig);
                    },
                    login: function (redirect_to) {
                        if (!redirect_to) {
                            redirect_to = '';
                        }
                        $modal.open({
                            templateUrl: 'account/login.html',
                            inDirection: false,
                            windowClass: 'modal-medium-simple',
                            outDirection: false,
                            fullScreen: false,
                            backdrop: true,
                            controller: ng(function ($scope) {
                                $scope.socials = [{
                                    name: 'Facebook',
                                    key: '2'
                                }, {
                                    name: 'Twitter',
                                    key: '3'
                                }, {
                                    name: 'Pinterest',
                                    key: '4'
                                }, {
                                    name: 'Reddit',
                                    key: '5'
                                }, {
                                    name: 'Linkedin',
                                    key: '6'
                                }, {
                                    name: 'Google+',
                                    icon: 'googleplus',
                                    key: '1'
                                }, {
                                    name: 'Tumblr',
                                    key: '7'
                                }];

                                $scope.getIcon = function (soc) {
                                    return '/client/dist/static/social/' + (soc.icon || soc.name.toLowerCase()) + '.png';
                                };

                                $scope.login = function (soc) {
                                    $http.post($state.href('login', {
                                        provider: soc.key
                                    }), {
                                        action_id: 'login',
                                        action_model: '11',
                                        redirect_to: redirect_to
                                    }).then(function (response) {
                                        var data = response.data;
                                        if (data && !data.errors && data.authorization_url) {
                                            window.location.href = data.authorization_url;
                                        } else {
                                            modals.alert('failedGeneratingAuthorizaitonUrl');
                                        }
                                    });
                                };
                            })
                        });
                    },
                    manageModal: function (account, extraConfig) {
                        extraConfig = helpers.alwaysObject(extraConfig);
                        var config = {
                            kind: this.kind,
                            templateBodyUrl: 'account/manage_body.html',
                            toolbar: {
                                titleEdit: 'account.settings',
                                hideSave: true
                            },
                            modalConfig: {
                                popFrom: extraConfig.popFrom,
                                inDirection: false,
                                outDirection: false
                            },
                            init: function ($scope) {
                                var entity = $scope.entity,
                                    close,
                                    updateFields = ['state', 'ui.rule', 'created', 'updated'],
                                    updateState = function (newArgs) {
                                        angular.forEach(['args', 'entity'], function (p) {
                                            helpers.update($scope[p], newArgs, updateFields);
                                        });
                                    },
                                    recompute = function () {
                                        var missing = Object.keys(mappedLoginProviders);
                                        $scope.identities = $scope.entity.identities.concat();
                                        angular.forEach($scope.identities, function (value) {
                                            var id = getProvider(value);
                                            if (missing[id]) {
                                                delete missing[id];
                                            }
                                        });
                                        angular.forEach(LOGIN_PROVIDERS, function (value) {
                                            if (missing[value.id]) {
                                                $scope.identities.push({
                                                    identity: '0-' + value.id,
                                                    associated: false
                                                });
                                            }
                                        });
                                    };
                                recompute();

                                if (entity.ui.rule.action.sudo.executable) {
                                    config.toolbar.templateActionsUrl = 'account/manage_actions.html';
                                }

                                $scope.args.disassociate = [];
                                $scope.maybeDisconnect = function (identity) {
                                    if (identity.email && identity.associated === undefined) {
                                        modals.confirm('disconnectSignInMethod', function () {
                                            $scope.args.disassociate.push(identity.identity);
                                            $scope.save().then(function () {
                                                recompute();
                                                snackbar.showK('identityDisconnected');
                                            });
                                        });
                                    } else {
                                        modals.confirm('connectSignInMethod', function () {
                                            var redirect_to = $state.href('loginProviderConnected', {
                                                provider: getProvider(identity)
                                            });
                                            $http.post($state.href('login', {
                                                provider: getProvider(identity)
                                            }), {
                                                action_id: 'login',
                                                action_model: '11',
                                                redirect_to: redirect_to
                                            }).then(function (response) {
                                                var data = response.data;
                                                if (data && !data.errors && data.authorization_url) {
                                                    window.location.href = data.authorization_url;
                                                } else {
                                                    modals.alert('failedGeneratingAuthorizaitonUrl');
                                                }
                                            });
                                        });
                                    }
                                };

                                $scope.actions.sudo = function () {
                                    modals.models.sudo(entity, {
                                        templateUrl: 'account/administer.html',
                                        onConfirm: updateState
                                    });
                                };
                            },
                            afterClose: function () {
                                if (extraConfig.fromRedirect) {
                                    $state.go('home');
                                }
                            },
                            scope: {
                                historyConfig: true,
                                isAssociated: function (ident) {
                                    return $.inArray(ident.identity, this.args.disassociate) === -1;
                                },
                                setPrimary: function (ident) {
                                    this.container.form.$setDirty();
                                    this.args.primary_identity = ident.identity;
                                },
                                disassociate: function (ident) {
                                    this.container.form.$setDirty();
                                    if (this.isAssociated(ident)) {
                                        this.args.disassociate.push(ident.identity);
                                    } else {
                                        this.args.disassociate.remove(ident.identity);
                                    }
                                },
                                actions: {},
                                layouts: {
                                    groups: [{
                                        label: false
                                    }, {
                                        label: GLOBAL_CONFIG.subheaders.loginMethods
                                    }]
                                }
                            }
                        };

                        return modelsEditor.create(config).read(account, {
                            key: account.key
                        });

                    },
                    logout: function (accountKey) {
                        var that = this;
                        that.actions.logout({
                            key: accountKey
                        }).then(function (response) {
                            endpoint.removeCache();
                            $.extend(currentAccount, response.data.entity);
                            $state.go('home');
                        });

                    }
                });

            });

        }));

}());
(function () {
    'use strict';
    angular.module('app')
        .controller('BuyerManagementController', ng(function ($scope, endpoint, currentAccount, models) {

            $scope.settings = function () {
                models['19'].manageModal(currentAccount.key, undefined, {
                    inDirection: false,
                    outDirection: false
                });
            };

            $scope.manageCollection = function () {
                models['18'].manageModal(currentAccount.key, {
                    inDirection: false,
                    outDirection: false
                });
            };

        })).controller('BuyOrdersController', ng(function ($scope, $timeout, modals, snackbar, modelsEditor, GLOBAL_CONFIG, modelsMeta, helpers, models, modelsUtil, $state) {

            var carts = $state.current.name === 'buy-carts',
                isOrderPaymentCanceled = $state.current.name === 'order-payment-canceled',
                isOrderPaymentSuccess = $state.current.name === 'order-payment-success',
                wait = null,
                loaded = false,
                tick = null,
                gorder,
                maxTries = 10,
                scheduleTick = function () {
                    if (!$state.params.key) {
                        return;
                    }
                    if (tick) {
                        $timeout.cancel(tick);
                    }
                    tick = $timeout(function () {
                        models['34'].actions.read({
                            key: $state.params.key
                        }, {disableUI: false}).then(function (response) {
                            if (gorder) {
                                helpers.update(gorder, response.data.entity, ['state', 'updated', 'payment_status', 'feedback_adjustment', 'feedback', 'ui']);
                            }
                            if (response.data.entity.state === 'completed') {
                                snackbar.showK('orderPaymentSuccessProgress' + response.data.entity.state);
                            } else {
                                scheduleTick();
                            }
                        }, function () {
                            maxTries += 1;
                            if (maxTries < 10) { // if it fails 10 rpcs then obv something wrong, abort
                                scheduleTick();
                            }
                        }); // schedule tick if error, and if entity state did not change from cart.
                    }, 2000);
                },
                viewOpts = {
                    inDirection: false,
                    outDirection: false,
                    afterClose: function () {
                        $state.go('buy-carts');
                    }
                },
                viewThen = function (order) {
                    gorder = order;
                    if (isOrderPaymentCanceled) {
                        snackbar.showK('orderPaymentSuccessProgresscanceled');
                    } else {
                        snackbar.showK('orderPaymentSuccessProgress');
                        scheduleTick();
                    }
                },
                maybeOpenOrder = function () {
                    if (loaded) {
                        return;
                    }
                    if (wait) {
                        clearTimeout(wait);
                    }
                    wait = setTimeout(function () {
                        var find = {
                            key: $state.params.key
                        }, order = _.findWhere($scope.search.results, find);
                        loaded = true;
                        if (order) {
                            return $scope.view(order, false);
                        }
                        models['34'].manageModal(find, undefined, undefined, viewOpts).then(viewThen);
                    }, 300);

                };

            if (isOrderPaymentCanceled || isOrderPaymentSuccess) {
                carts = true;
            }


            $scope.setPageToolbarTitle('buyer.' + (carts ? 'carts' : 'orders'));

            $scope.listHelp = (carts ? GLOBAL_CONFIG.emptyHelp.cartBuyerList : GLOBAL_CONFIG.emptyHelp.orderBuyerList);

            $scope.search = {
                results: [],
                pagination: {},
                loaded: false
            };

            $scope.scrollEnd = {loader: false};

            $scope.view = function (order, $event) {
                models['19'].current().then(function (response) {
                    return response.data.entity;
                }).then(function (buyer) {
                    var opts = {
                        cartMode: carts,
                        popFrom: ($event ? helpers.clicks.realEventTarget($event.target) : false)
                    }, viewPromise, directView = $event === false;
                    if (directView) {
                        $.extend(opts, viewOpts);
                    }
                    viewPromise = models['34'].manageModal(order, order._seller, buyer, opts);
                    if (viewPromise && directView) {
                        viewPromise.then(viewThen);
                    }
                });
            };

            models['19'].current().then(function (response) {
                var buyerEntity = response.data.entity;
                $scope.search.pagination = models['34'].paginate({
                    kind: '34',
                    args: {
                        search: {
                            ancestor: buyerEntity.key,
                            filters: [{field: 'state', operator: 'IN', value: (carts ? ['cart', 'checkout'] : ['completed', 'canceled'])}],
                            orders: [{field: 'updated', operator: 'desc'}, {field: 'key', operator: 'asc'}]
                        }
                    },
                    config: {
                        ignoreErrors: true
                    },
                    complete: function (response) {
                        var errors = response.data.errors;
                        if (errors) {
                            if (errors.buyer) {
                                snackbar.showK('noBuyer');
                            }
                        } else {
                            $scope.search.results.extend(response.data.entities);
                        }

                        if (isOrderPaymentCanceled || isOrderPaymentSuccess) {
                            maybeOpenOrder();
                        }

                        $scope.search.loaded = true;
                    }
                });
                $scope.scrollEnd.loader = $scope.search.pagination;
                $scope.search.pagination.load();
            });
        })).directive('buyerAddressListView', function () {
            return {
                scope: {
                    val: '=buyerAddressListView'
                },
                templateUrl: 'buyer/address_list_view.html',
                controller: ng(function ($scope) {
                    $scope.notEmpty = function (val) {
                        return angular.isString(val) || angular.isNumber(val);
                    };
                })
            };
        }).run(ng(function ($window, modelsEditor, modelsMeta, $q, modelsConfig, currentAccount, endpoint) {

            modelsConfig(function (models) {

                $.extend(models['19'], {
                    current: function (args) {
                        if (!args) {
                            args = {};
                        }
                        args.account = currentAccount.key;
                        return this.actions.read(args, {
                            cache: this.getCacheKey('current'),
                            cacheType: 'memory'
                        });
                    },
                    manageModalFieldsOrder: ['country', 'region', 'city', 'postal_code', 'street', 'name'],
                    manageModal: function (accountKey, afterSave, modalConfig) {
                        if (!modalConfig) {
                            modalConfig = {};
                        }
                        var fields = modelsMeta.getActionArguments(this.kind, 'update'),
                            that = this,
                            config;
                        $.extend(fields.addresses.ui, {
                            label: false,
                            specifics: {
                                listView: 'buyer-address-list-view',
                                listConfig: {
                                    perLine: 3
                                },
                                sortFields: that.manageModalFieldsOrder,
                                beforeSave: function ($scope, info) {
                                    var promises = [],
                                        updatedAddress = $scope.args,
                                        promise;
                                    if (updatedAddress.region && (!updatedAddress._region || (updatedAddress.region !== updatedAddress._region.key))) {
                                        promise = models['13'].get(updatedAddress.region);
                                        promise.then(function (response) {
                                            if (response.data.entities.length) {
                                                updatedAddress._region = response.data.entities[0];
                                            }
                                        });
                                        promises.push(promise);
                                    }

                                    if (updatedAddress.country && (!updatedAddress._country || (updatedAddress.country !== updatedAddress._country.key))) {
                                        promise = models['12'].actions.search(undefined, {
                                            cache: true
                                        });
                                        promise.then(function (response) {
                                            if (response.data.entities.length) {
                                                var country = _.findWhere(response.data.entities, {
                                                    key: updatedAddress.country
                                                });
                                                if (angular.isDefined(country)) {
                                                    updatedAddress._country = country;
                                                }

                                            }

                                        });

                                        promises.push(promise);
                                    }
                                    if (promises.length) {
                                        return $q.all(promises);
                                    }

                                    return false;
                                }
                            }
                        });
                        config = {
                            fields: _.toArray(fields),
                            kind: this.kind,
                            action: 'update',
                            modalConfig: modalConfig,
                            afterSave: function () {
                                endpoint.removeCache(that.getCacheKey('current'));
                                if (angular.isDefined(afterSave)) {
                                    afterSave();
                                }
                            },
                            scope: {
                                layouts: {
                                    groups: [{label: false, fields: ['addresses']}]
                                }
                            },
                            toolbar: {
                                titleEdit: 'buyer.viewAddresses'
                            },
                            excludeFields: ['account', 'read_arguments'],
                            argumentLoader: function ($scope) {
                                var args = this.defaultArgumentLoader($scope);
                                args.account = accountKey;
                                return args;
                            }
                        };

                        modelsEditor.create(config).read({}, {
                            account: accountKey
                        });
                    }
                });

            });

        }));
}());(function () {
    'use strict';
    angular.module('app').directive('trackIfProductView', ng(function ($timeout) {
        return {
            restrict: 'A',
            link: function (scope, element, attrs) {
                var fired;
                scope.$watch(attrs.trackIfProductView, function (neww, old) {
                    if (fired) {
                        return;
                    }
                    if (angular.isObject(neww)) {
                        $timeout(function () {
                            element.find('[data-pricetag-id="' + neww.image + '-' + neww.id + '"]').click();
                            fired = true;
                        }, 100);
                    }
                });
            }
        };
    })).directive('catalogNewPricetag', ng(function ($parse) {
        return {
            restrict: 'A',
            link: function (scope, element, attrs) {
                var callback = $parse(attrs.catalogNewPricetag);
                element.on('click', function (event) {
                    var offset = element.offset(),
                        x = event.pageX - offset.left,
                        y = event.pageY - offset.top,
                        parent = element.parents('.image-slider-item:first'),
                        width = parent.width(),
                        height = parent.height();

                    scope.$apply(function () {
                        callback(scope, {
                            config: {
                                position_left: x,
                                position_top: y,
                                image_width: width,
                                image_height: height
                            }
                        });
                    });
                });
            }
        };
    })).controller('CatalogViewController', ng(function ($scope, $state, models) {
        $scope.site.toolbar.hidden = true;
        models['31'].viewModal($state.params.key, {
            popFrom: undefined,
            inDirection: false,
            outDirection: false,
            afterClose: function () {
                $state.go('home');
            }
        });

    })).controller('CatalogProductAddToCartController', ng(function ($scope, $state, helpers, models) {
        var embed = $state.current.name === 'embed-catalog-product-add-to-cart';
        $scope.site.toolbar.hidden = true;
        models['31'].viewModal($state.params.key, {
            popFrom: undefined,
            inDirection: false,
            outDirection: false,
            hideClose: embed,
            noEscape: embed,
            afterClose: embed ? undefined : function () {
                $state.go('home');
            },
            variantSignatureAsDicts: helpers.url.jsonFromUrlsafe($state.params.variant),
            autoAddToCartQuantity: $state.params.quantity,
            loadProduct: {
                image: $state.params.image_id,
                id: $state.params.pricetag_id
            }
        });

    })).controller('CatalogProductViewController', ng(function ($scope, $state, models) {
        $scope.site.toolbar.hidden = true;
        models['31'].viewModal($state.params.key, {
            popFrom: undefined,
            inDirection: false,
            outDirection: false,
            afterClose: function () {
                $state.go('home');
            },
            loadProduct: {
                image: $state.params.image_id,
                id: $state.params.pricetag_id
            }
        });

    })).controller('CatalogOrderViewController', ng(function ($scope, $state, models) {
        var embed = $state.current.name === 'embed-catalog-order-view';
        $scope.site.toolbar.hidden = true;
        models['31'].viewModal($state.params.key, {
            popFrom: undefined,
            inDirection: false,
            outDirection: false,
            openCart: true,
            hideClose: embed,
            noEscape: embed
        });

    })).controller('EmbedCatalogViewController', ng(function ($scope, $state, models) {
        $scope.site.toolbar.hidden = true;
        models['31'].viewModal($state.params.key, {
            popFrom: undefined,
            inDirection: false,
            outDirection: false,
            noEscape: true,
            hideClose: true
        });

    })).controller('EmbedCatalogProductViewController', ng(function ($scope, $state, models) {
        $scope.site.toolbar.hidden = true;
        models['31'].viewModal($state.params.key, {
            popFrom: undefined,
            hideClose: true,
            noEscape: true,
            noEscapeOnProduct: true,
            inDirection: false,
            outDirection: false,
            loadProduct: {
                image: $state.params.image_id,
                id: $state.params.pricetag_id
            }
        });

    })).directive('catalogPricetagPosition', ng(function ($timeout, models) { // directives that are not used anywhere else other than this context are defined in their own context
        return {
            link: function (scope, element, attr) {

                var pricetag = scope.$eval(attr.catalogPricetagPosition),
                    resize = function (justElement) {
                        var pa = $(element).parents('.image-slider-item:first'),
                            sizes,
                            containerh = pa.height(),
                            pricetagHeight = 36;
                        sizes = models['31'].calculatePricetagPosition(
                            pricetag.position_top,
                            pricetag.position_left,
                            pricetag.image_width,
                            pricetag.image_height,
                            pa.width(),
                            containerh
                        );

                        if (sizes[0] < 0) {
                            sizes[0] = 0;
                        } else {
                            if (sizes[0] > containerh - pricetagHeight) {
                                sizes[0] = containerh - pricetagHeight;
                            }
                        }

                        pricetag._position_top = sizes[0];
                        pricetag._position_left = sizes[1];

                        $(element).css({
                            top: pricetag._position_top,
                            left: pricetag._position_left,
                            visibility: 'visible'
                        });
                    },
                    track = [];
                resize = _.throttle(resize, 100);
                $timeout(resize, 0, false);
                scope.$on('modalResize', resize);
                scope.$on('resizePricetags', function (event, tpricetag) {
                    if (tpricetag) {
                        if (tpricetag.key === pricetag.key) {
                            pricetag.position_top = tpricetag.position_top;
                            pricetag.position_left = tpricetag.position_left;
                            resize();
                        }
                    } else {
                        resize();
                    }
                });
                angular.forEach(['state', 'key', 'position_left', 'position_top', '_position_left', '_position_top'], function (value) {
                    track.push(attr.catalogPricetagPosition + '.' + value);
                });
                scope.$watch(function () {
                    return true;
                }, resize);
            }
        };
    })).directive('productInstanceCardView', ng(function ($compile) {
        return {
            scope: {
                val: '=productInstanceCardView'
            },
            templateUrl: 'catalog/product/product_instance_card_view.html',
            link: function (scope) {
                scope.showVariantLabel = function (variant) {
                    return variant.split(':')[0];
                };
                scope.showVariantValue = function (variant) {
                    var splitOpen = variant.split(':');
                    return splitOpen.slice(1, splitOpen.length).join(':');
                };
            }
        };
    })).run(ng(function (modelsEditor, modelsMeta, modelsConfig, currentAccount, $modal, modals, helpers, $q, GLOBAL_CONFIG, $mdSidenav, $timeout, $state, snackbar, social) {

        modelsConfig(function (models) {
            var doNotRipple = ['.catalog-close-button', '.catalog-pricetag', '.catalog-pricetag-link'],
                recomputeRealPath = function (field1, level) {
                    if (!level) {
                        level = 0;
                    }
                    var field2 = field1.modelclass;
                    angular.forEach(field2, function (value) {
                        if (value.ui.realPath) {
                            var con = field1.ui.realPath.concat();
                            con.push(value.code_name);
                            value.ui.realPath = con;
                            value.ui.initialRealPath = con;
                            if (value.modelclass) {
                                recomputeRealPath(value, level + 1);
                            }
                        }
                    });
                };
            $.extend(models['31'], {
                formatPublicSearchResults: function (results) {
                    angular.forEach(results, function (result) {
                        result._cover = {
                            serving_url: result.cover,
                            proportion: result.cover_proportion
                        };
                        result._seller_logo = {
                            serving_url: result.seller_logo,
                            proportion: 2.4
                        };
                    });
                },
                calculatePricetagPosition: function (ihp, ivp, iiw, iih, ciw, cih) {
                    /*  
                    ihp - Initial Horizontal Price Tag Position 
                    ivp - Initial Vertical Price Tag Position 
                    iiw - Initial Image Width  
                    iih - Initial Image Height  

                    ciw - Current Image Width  
                    cih - Current Image Height  
                    chp - Current Horizontal Price Tag Position  
                    cvp - Current Vertical Price Tag Position  
                    */
                    var chp = (ihp / iiw) * ciw,
                        cvp = (ivp / iih) * cih;
                    return [chp, cvp];
                },
                previewModal: function (key, config) {
                    config = helpers.alwaysObject(config);
                    config.hideAddToCart = true;
                    return this.viewModal(key, config);
                },
                viewProductModal: function (catalogKey, imageKey, pricetagKey, variantSignatureAsDicts, config) {
                    var readArguments = {
                        _seller: {},
                        _images: {
                            config: {
                                keys: [imageKey]
                            },
                            pricetags: {
                                config: {
                                    keys: [pricetagKey]
                                },
                                _product: {
                                    _category: {}
                                }
                            }
                        }
                    };
                    config = helpers.alwaysObject(config);
                    this.actions.read({
                        key: catalogKey,
                        read_arguments: readArguments
                    }).then(function (response) {
                        var catalog = response.data.entity,
                            fakeScope = (function () {
                                var $scope = {};
                                $scope.product = catalog._images[0].pricetags[0]._product;
                                $scope.originalProduct = angular.copy($scope.product);
                                $scope.catalog = catalog;
                                $scope.variants = [];
                                $scope.variantSelection = [];
                                $scope.hideAddToCart = false;
                                $scope.hideClose = config ? config.hideClose : false;
                                $scope.currentVariation = [];
                                angular.forEach($scope.product.variants, function (v, i) {

                                    $scope.variants.push({
                                        name: v.name,
                                        options: v.options,
                                        option: (variantSignatureAsDicts ? variantSignatureAsDicts[i][v.name] : v.options[0]),
                                        description: v.description,
                                        allow_custom_value: v.allow_custom_value
                                    });

                                    $scope.variantSelection.push({
                                        type: 'SuperStringProperty',
                                        choices: (v.allow_custom_value ? null : v.options),
                                        code_name: 'option_' + i,
                                        ui: {
                                            //help: v.description,
                                            label: (v.allow_custom_value ? false : v.name),
                                            writable: true,
                                            attrs: {
                                                'ng-change': 'delayedChangeVariation()'
                                            },
                                            args: 'variants[' + i + '].option'
                                        }
                                    });

                                });

                                $scope.changeVariationPromise = function () {
                                    var buildVariantSignature = [],
                                        skip = false,
                                        promise;

                                    $scope.currentVariation.splice(0, $scope.currentVariation.length);

                                    angular.forEach($scope.variants, function (v) {
                                        var d = {};
                                        if (v.option === null) {
                                            skip = true;
                                        }
                                        if ( /*!v.allow_custom_value*/ 1) {
                                            buildVariantSignature.push(v.name + ': ' + v.option);
                                            d[v.name] = v.option;
                                            $scope.currentVariation.push(d);
                                        }
                                    });

                                    if (skip) {
                                        promise = $q.defer().promise;
                                        promise.resolve();
                                        return promise;
                                    }
                                    // rpc to check the instance
                                    return models['31'].actions.read({
                                        key: this.catalog.key,
                                        // 4 rpcs
                                        read_arguments: {
                                            _images: {
                                                config: {
                                                    keys: [imageKey]
                                                },
                                                pricetags: {
                                                    config: {
                                                        keys: [pricetagKey]
                                                    },
                                                    _product: {
                                                        _instances: {
                                                            config: {
                                                                search: {
                                                                    filters: [{
                                                                        field: 'variant_options',
                                                                        operator: 'ALL_IN',
                                                                        value: buildVariantSignature
                                                                    }]
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    });
                                };

                                return $scope;
                            }());
                        $modal.open({
                            resolve: {
                                productInstanceResponse: function () {
                                    return fakeScope.changeVariationPromise().then(function (response) {
                                        return response;
                                    });
                                }
                            },
                            templateUrl: 'catalog/product/view.html',
                            windowClass: 'no-overflow',
                            popFrom: config.popFrom,
                            noEscape: config.noEscape,
                            controller: ng(function ($scope, productInstanceResponse) {
                                var loadProductInstance, sellerKey, shareWatch, timer;
                                $scope.variantMenu = {};
                                $scope.productMenu = {};
                                helpers.sideNav.setup($scope.productMenu, 'right_product_sidenav', doNotRipple);
                                helpers.sideNav.setup($scope.variantMenu, 'right_variantMenu_sidenav', doNotRipple);

                                $.extend($scope, fakeScope);

                                shareWatch = function () {
                                    if (!$scope.product) {
                                        $scope.socialMeta = {};
                                        return;
                                    }
                                    var productUrl = $state.href('catalog-product-view', {
                                            key: $scope.catalog.key,
                                            image_id: $scope.catalog._images[0].id,
                                            pricetag_id: $scope.catalog._images[0].pricetags[0].id
                                        }, {
                                            absolute: true
                                        }),
                                        image = function (size) {
                                            if ($scope.product.images && $scope.product.images.length) {
                                                return $scope.product.images[0].serving_url + '=s' + (size || '600');
                                            }
                                            return undefined;
                                        };
                                    $scope.socialMeta = {
                                        facebook: {
                                            'p[url]': productUrl,
                                            'p[images][0]': image(600),
                                            'p[title]': $scope.product.name
                                        },
                                        twitter: {
                                            url: productUrl,
                                            text: 'Product - ' + $scope.product.name
                                        },
                                        pinterest: {
                                            url: productUrl,
                                            media: image(600),
                                            description: 'Share on pinterest'
                                        },
                                        googleplus: {
                                            url: productUrl
                                        },
                                        reddit: {
                                            url: productUrl,
                                            title: $scope.product.name
                                        },
                                        linkedin: {
                                            url: productUrl,
                                            title: $scope.product.name
                                        },
                                        tumblr: {
                                            url: productUrl,
                                            name: $scope.product.name
                                        }
                                    };
                                };

                                $scope.displayShare = function () {
                                    return social.share($scope.socialMeta, false);
                                };

                                $scope.variantChooser = {};

                                $scope.setupVariantChooser = function (variant, indice) {
                                    variant.indice = indice;
                                    $scope.variantChooser = variant;
                                    $scope.variantMenu.open();
                                };

                                $scope.completeVariantChooser = function (option) {
                                    $scope.variantChooser.option = option;
                                    $scope.variantMenu.close();
                                    $scope.changeVariation();
                                };

                                $scope.resetVariation = function () {
                                    $scope.resetVariantProduct();
                                    $scope.variationApplied = false;
                                    angular.forEach($scope.variants, function (v) {
                                        v.option = null;
                                    });
                                };
                                $scope.resetVariantProduct = function () {
                                    $.extend($scope.product, $scope.originalProduct);
                                    $scope.productInstance = null;
                                };
                                $scope.variationApplied = false;
                                $scope.viewContent = function (content) {
                                    $modal.open({
                                        templateUrl: 'core/misc/content_view.html',
                                        controller: ng(function ($scope) {
                                            $scope.markDown = true;
                                            $scope.content = content;
                                        })
                                    });
                                };
                                $scope.canAddToCart = true;
                                $scope.hasThisProduct = false;
                                $scope.disableUpdateCart = false;
                                $scope.productQuantity = 0;

                                sellerKey = $scope.catalog._seller.key;
                                $scope.cartProductQuantity = function () {
                                    $scope.productQuantity = 0;
                                    $scope.hasThisProduct = false;
                                    $scope.disableUpdateCart = false;
                                    if (!currentAccount._is_guest) {
                                        models['34'].current(sellerKey).then(function (response) {
                                            var order = response.data.entity;
                                            if (order.id) {
                                                angular.forEach(order._lines, function (line) {
                                                    if (line.product._reference.parent.id === $scope.product.parent.id && line.product._reference.id === $scope.product.id && angular.toJson($scope.currentVariation) === angular.toJson(line.product.variant_signature)) {
                                                        $scope.productQuantity = parseInt(line.product.quantity, 10);
                                                        if ($scope.productQuantity > 0) {
                                                            $scope.hasThisProduct = true;
                                                            $scope.disableUpdateCart = true;
                                                        }
                                                    }
                                                });
                                                $scope.canAddToCart = order.ui.rule.action.update_line.executable;
                                            } else {
                                                $scope.canAddToCart = true;
                                            }

                                            if (!$scope.productQuantity) {
                                                $scope.productQuantity = 1;
                                            }

                                        });
                                    } else {
                                        $scope.productQuantity = 1;
                                    }
                                };

                                loadProductInstance = function (response) {
                                    var product,
                                        productInstance,
                                        toUpdate = ['images', 'code', 'unit_price', 'weight', 'volume',
                                            'description', 'contents', 'availability'
                                        ];
                                    try {
                                        product = response.data.entity._images[0].pricetags[0]._product;
                                    } catch (ignore) {}

                                    if (product) {
                                        productInstance = product._instances[0];
                                    }
                                    $scope.resetVariantProduct();
                                    if (productInstance) {
                                        $scope.productInstance = productInstance;
                                        angular.forEach(toUpdate, function (field) {
                                            var next = productInstance[field];
                                            if (next !== null && next.length && next !== undefined) {
                                                $scope.product[field] = next;
                                            }
                                        });
                                    }
                                    $scope.variationApplied = true;
                                };

                                $scope.delayedChangeVariation = function () {
                                    if (timer) {
                                        $timeout.cancel(timer);
                                    }
                                    timer = $timeout(function () {
                                        timer = null;
                                        $scope.changeVariation();
                                    }, 500, false);
                                };

                                $scope.changeVariation = function () {
                                    // rpc to check the instance
                                    $scope.changeVariationPromise()
                                        .then(loadProductInstance)
                                        .then($scope.cartProductQuantity);
                                };

                                loadProductInstance(productInstanceResponse);

                                $scope.cartProductQuantity();

                                $scope.increaseQuantity = function () {
                                    $scope.disableUpdateCart = false;
                                    $scope.productQuantity = parseInt($scope.productQuantity, 10) + 1;
                                };

                                $scope.decreaseQuantity = function () {
                                    if (parseInt($scope.productQuantity, 10) === 0) {
                                        return;
                                    }
                                    $scope.disableUpdateCart = false;
                                    $scope.productQuantity = parseInt($scope.productQuantity, 10) - 1;
                                };

                                $scope.changedQuantity = function () {
                                    $scope.disableUpdateCart = false;
                                };

                                $scope.addToCart = function () {
                                    if (currentAccount._is_guest) {
                                        models['11'].login($state.href((config.hideCloseCatalog ? 'embed-' : '') + 'catalog-product-add-to-cart', {
                                            key: $scope.catalog.key,
                                            image_id: $scope.catalog._images[0].id,
                                            pricetag_id: $scope.catalog._images[0].pricetags[0].id,
                                            variant: helpers.url.jsonToUrlsafe($scope.currentVariation),
                                            quantity: $scope.productQuantity
                                        }));
                                        return;
                                    }
                                    if (config.autoAddToCart) {
                                        $scope.productQuantity = config.autoAddToCartQuantity;
                                    }
                                    if (!$scope.hasThisProduct && $scope.productQuantity < 1) {
                                        $scope.container.form.$setDirty();
                                        var productQuantityField = $scope.container.form.productQuantity;
                                        productQuantityField.$setViewValue(productQuantityField.$viewValue !== undefined ? productQuantityField.$viewValue : '');
                                        productQuantityField.$setDirty();
                                        productQuantityField.$setValidity('required', false);
                                        return;
                                    }
                                    models['19'].current().then(function (response) {
                                        return models['34'].actions.update_line({
                                            buyer: response.data.entity.key,
                                            product: $scope.product.key,
                                            image: imageKey,
                                            quantity: $scope.productQuantity,
                                            variant_signature: $scope.currentVariation
                                        });
                                    }).then(function (response) {
                                        if (config.events && config.events.addToCart) {
                                            config.events.addToCart.call(this, response);
                                        }
                                        if (models['34'].getCache('current' + sellerKey)) {
                                            models['34'].current(sellerKey).then(function (cached) {
                                                $.extend(cached.data.entity, response.data.entity);
                                            });
                                        }

                                        if ($scope.productQuantity < 1) {
                                            $scope.hasThisProduct = false;
                                            $scope.productQuantity = 1;
                                        } else {
                                            $scope.hasThisProduct = true;
                                            $scope.disableUpdateCart = true;
                                        }

                                        snackbar.showK('cartUpdated');
                                    });
                                };

                                if (config.autoAddToCart) {
                                    $timeout(function () {
                                        $scope.addToCart();
                                        config.autoAddToCart = false;
                                    });
                                }

                                $scope.close = function () {
                                    $scope.$close().then(function () {
                                        if (config.afterClose) {
                                            config.afterClose();
                                        }
                                    });
                                };


                                $scope.$watch('product.id', function (neww, old) {
                                    shareWatch();
                                });

                            })
                        });
                    });
                },
                viewModal: function (key, config) {
                    var that = this;
                    that.actions.read({
                        key: key,
                        // 5 rpcs
                        read_arguments: {
                            _seller: {
                                _content: {},
                                _feedback: {}
                            },
                            _images: {
                                pricetags: {}
                            }
                        }
                    }).then(function (response) {
                        var entity = response.data.entity;
                        if (!entity._images.length) {
                            snackbar.showK('noImagesInCatalog');
                            return;
                        }
                        $modal.open({
                            templateUrl: 'catalog/view.html',
                            windowClass: 'no-overflow',
                            popFrom: config.popFrom,
                            inDirection: config.inDirection,
                            outDirection: config.outDirection,
                            noEscape: config.noEscape,
                            controller: ng(function ($scope) {
                                $scope.catalogMenu = {};
                                helpers.sideNav.setup($scope.catalogMenu, 'right_catalog_sidenav', doNotRipple);
                                $scope.catalog = entity;
                                $scope.catalog.action_model = '31';
                                $scope.logoImageConfig = {
                                    size: 560
                                };
                                var imagesReader,
                                    accessImages,
                                    loadProduct,
                                    catalogUrl = $state.href('catalog-view', {
                                        key: $scope.catalog.key
                                    }, {
                                        absolute: true
                                    }),
                                    embedCatalogUrl = $state.href('embed-catalog-view', {
                                        key: $scope.catalog.key
                                    }, {
                                        absolute: true
                                    });
                                accessImages = angular.copy($scope.catalog.ui.access);
                                accessImages.push('_images');

                                imagesReader = models['31'].reader({
                                    key: $scope.catalog.key,
                                    next: {
                                        _images: $scope.catalog._next_read_arguments._images
                                    },
                                    access: accessImages,
                                    complete: function (items) {
                                        $scope.catalog._images.extend(items);
                                    }
                                });

                                $scope.imagesReader = imagesReader;
                                imagesReader.showLoaderAlways = true;

                                $scope.socialMeta = {
                                    facebook: {
                                        'p[url]': catalogUrl,
                                        'p[images][0]': $scope.catalog._images[0].serving_url + '=s600',
                                        'p[title]': $scope.catalog.name
                                    },
                                    twitter: {
                                        url: catalogUrl,
                                        text: 'Catalog - ' + $scope.catalog.name
                                    },
                                    pinterest: {
                                        url: catalogUrl,
                                        media: $scope.catalog._images[0].serving_url + '=s600',
                                        description: 'Share on pinterest'
                                    },
                                    googleplus: {
                                        url: catalogUrl
                                    },
                                    reddit: {
                                        url: catalogUrl,
                                        title: $scope.catalog.name
                                    },
                                    linkedin: {
                                        url: catalogUrl,
                                        title: $scope.catalog.name
                                    },
                                    tumblr: {
                                        url: catalogUrl,
                                        name: $scope.catalog.name
                                    }
                                };

                                $scope.displayShare = function () {
                                    return social.share($scope.socialMeta, {
                                        src: embedCatalogUrl
                                    });
                                };

                                $scope.hideClose = config.hideClose;

                                $scope.loadMoreImages = function (callback) {
                                    var promise = imagesReader.load();
                                    if (promise) {
                                        promise.then(function () {
                                            callback.call(this, response, imagesReader.more);
                                        });
                                    } else {
                                        callback.call(this, undefined, imagesReader.more);
                                    }
                                };

                                $scope.displayCart = function () {
                                    if (currentAccount._is_guest) {
                                        models['11'].login($state.href((config.hideClose ? 'embed-' : '') + 'catalog-order-view', {
                                            key: $scope.catalog.key
                                        }));
                                        return;
                                    }
                                    models['19'].current().then(function (response) {
                                        models['34'].manageModal(undefined, $scope.catalog._seller, response.data.entity, {
                                            cartMode: true
                                        });
                                    });
                                };

                                if (config.openCart) {
                                    $timeout(function () {
                                        $scope.displayCart();
                                    });
                                }

                                // cache current user's cart
                                if (!currentAccount._is_guest) {
                                    models['34'].current($scope.catalog._seller.key);
                                }

                                $scope.viewProduct = function (image, pricetag, $event) {
                                    var target = $event.target,
                                        theTarget = $(target).parents('.catalog-pricetag:first');
                                    if (theTarget.length) {
                                        target = theTarget.get(0);
                                    }
                                    that.viewProductModal($scope.catalog.key, image.key, pricetag.key, config.variantSignatureAsDicts, {
                                        popFrom: target,
                                        hideClose: config.hideCloseOnProduct,
                                        hideCloseCatalog: config.hideClose,
                                        noEscapeCatalog: config.noEscape,
                                        noEscape: config.noEscapeOnProduct,
                                        autoAddToCart: config.variantSignatureAsDicts ? true : false,
                                        autoAddToCartQuantity: config.autoAddToCartQuantity,
                                        afterClose: config.afterCloseProduct
                                    });

                                    config.variantSignatureAsDicts = null;
                                };

                                $scope.openSellerDetails = function () {
                                    $scope.sellerDetails.menu.open();
                                };

                                $scope.maybeLoadProduct = null;

                                if (config.loadProduct) {
                                    loadProduct = function () {
                                        angular.forEach($scope.catalog._images, function (image) {
                                            if (image.id.toString() === config.loadProduct.image.toString()) {
                                                $scope.maybeLoadProduct = config.loadProduct;
                                            }
                                        });
                                        if (!$scope.maybeLoadProduct) {
                                            //return;
                                            var promise = imagesReader.load();
                                            if (promise) {
                                                promise.then(loadProduct);
                                            }
                                        }
                                    };

                                    loadProduct();
                                }

                                $scope.sellerDetails = models['23'].makeSellerDetails($scope.catalog._seller);

                                $scope.close = function () {
                                    $scope.$close().then(function () {
                                        if (config.afterClose) {
                                            config.afterClose();
                                        }
                                    });
                                };
                            })
                        });
                    });
                },
                adminManageModal: function (account, extraConfig) {
                    return this.manageModal(account, undefined, extraConfig);
                },
                manageModal: function (catalog, callback, modalConfig) { // modal dialog for managing the catalog

                    modalConfig = helpers.alwaysObject(modalConfig);

                    var fields = modelsMeta.getActionArguments('31', 'update'),
                        isNew = !angular.isDefined(catalog),
                        afterSave = function ($scope) {
                            $scope.setAction('catalog_upload_images');
                            $scope.dialog.toolbar.templateActionsUrl = 'catalog/manage_actions.html';
                            callback($scope.entity);
                        },
                        afterComplete = function ($scope) {
                            $scope.setAction('update');
                            callback($scope.entity);
                        },
                        noComplete = function ($scope) {
                            afterComplete($scope);
                        },
                        config = {
                            kind: this.kind,
                            action: (isNew ? 'create' : 'update'),
                            modalConfig: modalConfig,
                            fields: _.toArray(fields),
                            toolbar: {
                                templateActionsUrl: (isNew ? false : 'catalog/manage_actions.html'),
                                titleEdit: 'edit31',
                                titleAdd: 'add31'
                            },
                            afterSave: afterSave,
                            afterSaveError: afterSave,
                            afterComplete: afterComplete,
                            afterCompleteError: afterComplete,
                            init: function ($scope) {

                                $.extend(fields._images.ui, {
                                    label: false,
                                    specifics: {
                                        setupSortableOptions: function () {
                                            return {
                                                stop: function () {
                                                    if (fields._images.ui.specifics.parentArgs.length) {
                                                        var total = fields._images.ui.specifics.parentArgs[0].sequence,
                                                            dirty,
                                                            scope = fields._images.ui.directiveScope();
                                                        angular.forEach(fields._images.ui.specifics.parentArgs,
                                                            function (ent, i) {
                                                                i = (total - i);
                                                                if (ent.sequence !== i || ent._state === 'deleted') {
                                                                    dirty = true;
                                                                }
                                                                ent.sequence = i;
                                                                ent.ui.access[ent.ui.access.length - 1] = i;
                                                            });

                                                        if (dirty) {
                                                            scope.formSetDirty();
                                                        }
                                                        scope.$broadcast('itemOrderChanged');
                                                        scope.$apply();

                                                    }
                                                }
                                            };
                                        }
                                    }
                                });

                                var updateFields = ['state', 'ui.rule', 'created', 'updated'],
                                    updateState = function (newArgs) {
                                        angular.forEach(['args', 'entity'], function (p) {
                                            helpers.update($scope[p], newArgs, updateFields);
                                        });
                                    };

                                $scope.actions = {
                                    publish: function () {
                                        modals.confirm('publishCatalog',
                                            function () {
                                                models['31'].actions.publish({
                                                    key: $scope.entity.key
                                                }).then(function (response) {
                                                    snackbar.showK('catalogPublished');
                                                    updateState(response.data.entity);
                                                });
                                            });
                                    },
                                    discontinue: function () {
                                        modals.confirm('discontinueCatalog',
                                            function () {
                                                models['31'].actions.discontinue({
                                                    key: $scope.entity.key
                                                }).then(function (response) {
                                                    snackbar.showK('catalogDiscontinued');
                                                    updateState(response.data.entity);
                                                });
                                            });
                                    },
                                    duplicate: function () {
                                        modals.confirm('duplicateCatalog',
                                            function () {
                                                models['11'].channelNotifications({
                                                    callback: function (response) {
                                                        models['31'].actions.read({
                                                            key: response.catalog_key,
                                                            read_arguments: {
                                                                cover: {}
                                                            }
                                                        }).then(function (response) {
                                                            snackbar.showK('catalogDuplicated');
                                                            callback(response.data.entity);
                                                        });
                                                    }
                                                }).then(function (response) {
                                                    models['31'].actions.catalog_duplicate({
                                                        key: $scope.entity.key,
                                                        channel: response.token
                                                    });
                                                });
                                            });
                                    },
                                    sudo: function () {
                                        modals.models.sudo($scope.entity, {
                                            templateUrl: 'catalog/administer.html',
                                            onConfirm: updateState
                                        });
                                    }
                                };
                            },
                            noComplete: noComplete,
                            scope: {
                                historyConfig: true,
                                addProducts: function () {
                                    var parentScope = this;
                                    $modal.open({
                                        templateUrl: 'core/models/manage.html',
                                        windowClass: 'no-overflow',
                                        controller: ng(function ($scope, $timeout) {
                                            var accessImages = angular.copy(parentScope.args.ui.access),
                                                imagesReader,
                                                setupCurrentPricetag,
                                                variantOptions,
                                                addNewPricetag,
                                                removePricetag,
                                                getTitle = function () {
                                                    return 'viewProducts';
                                                };
                                            accessImages.push(fields._images.code_name);
                                            $scope.rootScope = parentScope.rootScope; // pass the rootScope
                                            $scope.config = parentScope.rootScope.config;
                                            $scope.entity = parentScope.entity;
                                            $scope.args = angular.copy(parentScope.args);
                                            $scope.dialog = {
                                                templateBodyUrl: 'catalog/manage_products.html',
                                                toolbar: {
                                                    hideSave: true
                                                }
                                            };
                                            $scope.imagesLoaded = false;
                                            $scope.container = {};
                                            $scope.formSetPristine = angular.bind($scope, helpers.form.setPristine);
                                            $scope.formSetDirty = angular.bind($scope, helpers.form.setDirty);
                                            $scope.validateForm = angular.bind($scope, helpers.form.validate);
                                            $scope.fieldProduct = fields._images.modelclass.pricetags.modelclass._product;
                                            $scope.args._images = [];
                                            $scope.config._title_.push(getTitle);
                                            $scope.$on('$destroy', function () {
                                                $scope.config._title_.remove(getTitle);
                                                fields._images._title_.remove(getTitle);
                                                fields._images.modelclass.pricetags._title_.remove(getTitle);
                                                fields._images.modelclass.pricetags.modelclass._product._title_.remove(getTitle);
                                            });
                                            fields._images._title_ = $scope.config._title_.concat();
                                            fields._images.modelclass.pricetags._title_ = fields._images._title_.concat();
                                            $scope.fieldProduct._title_ = fields._images._title_.concat();
                                            $scope.dialog.toolbar.title = helpers.toolbar.buildTitle($scope.config._title_);

                                            $scope.trackPricetags = function (pricetag) {
                                                if (pricetag.key) {
                                                    return pricetag.key;
                                                }
                                                return 'new' + _.uniqueId();
                                            };

                                            imagesReader = models['31'].reader({
                                                key: $scope.args.key,
                                                next: {
                                                    _images: {}
                                                },
                                                access: accessImages,
                                                complete: function (items) {
                                                    $scope.args._images.extend(items);
                                                    $timeout(function () {
                                                        $scope.imagesLoaded = true;
                                                    }, 300);
                                                }
                                            });
                                            variantOptions = $scope.fieldProduct.modelclass._instances.modelclass.variant_options;
                                            if (!variantOptions.ui.specifics) {
                                                variantOptions.ui.specifics = {};
                                            }
                                            variantOptions.ui.specifics.checkboxes = true;
                                            variantOptions.ui.fieldset = true;
                                            if (!variantOptions.ui.specifics) {
                                                variantOptions.ui.specifics = {};
                                            }
                                            variantOptions.ui.specifics.listView = function (item) {
                                                return angular.isObject(item) ? item.full : item;
                                            };
                                            variantOptions.ui.specifics.grouping = function (items) {
                                                var list = [],
                                                    map = {};
                                                angular.forEach(items, function (value) {
                                                    var split = value.split(': '),
                                                        obj = map[split[0]];
                                                    if (!obj) {
                                                        obj = {
                                                            label: split[0],
                                                            items: []
                                                        };
                                                        map[split[0]] = obj;
                                                        list.push(obj);
                                                    }

                                                    obj.items.push({
                                                        name: split[1],
                                                        key: value,
                                                        full: value
                                                    });
                                                });
                                                return list;
                                            };

                                            addNewPricetag = function (image, pricetag) {
                                                image.pricetags.push(pricetag);
                                                var existing = _.findWhere($scope.rootScope.args._images, {
                                                    key: image.key
                                                });
                                                if (!existing) {
                                                    return;
                                                }
                                                existing.pricetags.push(pricetag);
                                            };

                                            removePricetag = function (image, pricetag) {
                                                if (angular.isDefined(pricetag._destroy)) {
                                                    pricetag._destroy();
                                                }
                                                image.pricetags.remove(pricetag);
                                                var existing = _.findWhere($scope.rootScope.args._images, {
                                                    key: image.key
                                                });
                                                if (!existing) {
                                                    return;
                                                }
                                                existing.pricetags.iremove(function (ipricetag) {
                                                    return ipricetag.key === pricetag.key;
                                                });
                                            };

                                            imagesReader.load();

                                            $scope.onStart = function (event, ui, image, pricetag) {
                                                $(ui.helper).addClass('dragged');
                                                $(ui.helper).find('a').addClass('dragged');
                                                if (angular.isUndefined(pricetag._image)) {
                                                    pricetag._image = $scope.args._images.indexOf(image);
                                                }
                                            };

                                            $scope.onDrag = function (event, ui, image, pricetag) {};

                                            $scope.droppableOptions = {
                                                accept: '.catalog-new-pricetag',
                                                tolerance: 'pointer'
                                            };

                                            $scope.draggableOptions = {
                                                containment: '.image-slider-outer',
                                                distance: 10
                                            };

                                            $scope.onStop = function (event, ui, image, pricetag) {
                                                setTimeout(function () {
                                                    $(ui.helper).removeClass('dragged');
                                                    $(ui.helper).find('a').removeClass('dragged');
                                                }, 350);
                                                if (pricetag._state === 'deleted') {
                                                    return;
                                                }

                                                var target = $(event.target).parents('.image-slider-item:first'),
                                                    pricetagElement = $(event.target),
                                                    left = parseFloat(pricetagElement.css('left'), 10),
                                                    width = pricetagElement.width(),
                                                    targetWidth = target.width(),
                                                    tolerance = targetWidth - (width + left),
                                                    i = $scope.args._images.indexOf(image),
                                                    cwidth = 0,
                                                    pwidth = 0,
                                                    next,
                                                    extract;
                                                extract = function (what) {
                                                    var newImage,
                                                        exists,
                                                        newParent,
                                                        newPricetag,
                                                        newPositionLeft,
                                                        ocw = 0,
                                                        currentTop = parseFloat($(ui.helper).css('top'), 10);
                                                    next = target;
                                                    cwidth = what ? targetWidth : 0;
                                                    while (true) {
                                                        if (what) {
                                                            i += 1;
                                                            next = next.next();
                                                            cwidth += next.width();
                                                            if (cwidth > left) {
                                                                newParent = next;
                                                                newImage = $scope.args._images[i];
                                                                newPositionLeft = left - (pwidth || targetWidth);
                                                                break;
                                                            }
                                                            if (i > 10000) {
                                                                break;
                                                            }

                                                            pwidth = cwidth;
                                                        } else {
                                                            i -= 1;
                                                            next = next.prev();
                                                            ocw += next.width();
                                                            cwidth -= next.width();
                                                            if (cwidth < left) {
                                                                newParent = next;
                                                                newImage = $scope.args._images[i];
                                                                newPositionLeft = ocw + left;
                                                                break;
                                                            }
                                                            if (i < 0) {
                                                                break;
                                                            }
                                                        }
                                                    }
                                                    if (newImage) {
                                                        pricetag._state = 'deleted';
                                                        pricetagElement.addClass('ng-hide');
                                                        exists = _.findWhere(newImage.pricetags, {
                                                            key: pricetag.key
                                                        });
                                                        if (exists) {
                                                            pricetag = exists;
                                                        }
                                                        pricetag.image_width = newParent.width();
                                                        pricetag.image_height = newParent.height();
                                                        pricetag.position_left = newPositionLeft;
                                                        pricetag.position_top = currentTop;
                                                        pricetag._position_left = newPositionLeft;
                                                        pricetag._position_top = currentTop;
                                                        if (angular.isUndefined(exists)) {
                                                            newPricetag = angular.copy(pricetag);
                                                            newPricetag._state = null;
                                                            newPricetag._must_save = true;
                                                            if (angular.isUndefined(pricetag._image)) {
                                                                newPricetag._image = i;
                                                            }
                                                            addNewPricetag(newImage, newPricetag);
                                                        } else {
                                                            exists._state = null;
                                                        }
                                                    }
                                                };

                                                pricetag.position_top = ui.position.top;
                                                pricetag.position_left = ui.position.left;
                                                pricetag.image_width = target.width();
                                                pricetag.image_height = target.height();
                                                pricetag._position_top = pricetag.position_top;
                                                pricetag._position_left = pricetag.position_left;

                                                $scope.formSetDirty();

                                                if ((tolerance + width) < 3.3) {
                                                    //console.log('must go to next image');
                                                    extract(true);
                                                } else if (left < -8.5) {
                                                    //console.log('must go to the previous image');
                                                    extract();
                                                } else {
                                                    //console.log('stays');
                                                }

                                                if (!$scope.$$phase) {
                                                    $scope.$apply();
                                                }
                                                $scope.sync();
                                                $scope.$broadcast('resizePricetags', pricetag);

                                            };

                                            $scope.onDrop = function (event, ui, image) {
                                                var target_drop = $(event.target),
                                                    posi = target_drop.offset(),
                                                    posi2 = ui.offset,
                                                    rtop = posi2.top - posi.top + 6,
                                                    rleft = posi2.left - posi.left + 4,
                                                    vdom = $('<div style="visibility:hidden;"></div>'),
                                                    newPricetagConfig = {
                                                        position_top: rtop,
                                                        position_left: rleft,
                                                        _image: $scope.args._images.indexOf(image),
                                                        image_width: target_drop.width(),
                                                        image_height: target_drop.height()
                                                    };
                                                vdom.css({
                                                    top: rtop,
                                                    position: 'absolute',
                                                    left: rleft,
                                                    width: ui.draggable.width(),
                                                    height: ui.draggable.height()
                                                });
                                                vdom.appendTo(target_drop);
                                                newPricetagConfig._destroy = function () {
                                                    $timeout(function () {
                                                        vdom.remove();
                                                    }, 2000, false);
                                                };
                                                $scope.createProduct(image, newPricetagConfig, vdom);
                                            };

                                            $scope.imagesReader = imagesReader;

                                            imagesReader.showLoaderAlways = true;

                                            $scope.loadMoreImages = function (callback) {
                                                var promise = imagesReader.load();
                                                if (promise) {
                                                    promise.then(function (response) {
                                                        callback.call(this, response, imagesReader.more);
                                                    });
                                                } else {
                                                    callback.call(this, undefined, imagesReader.more);
                                                }
                                            };

                                            setupCurrentPricetag = function (image, pricetag) {
                                                $scope.image = image;
                                                $scope.pricetag = pricetag;
                                            };

                                            $scope.loadingManageProduct = false;
                                            $scope.manageProduct = function (image, pricetag, $event) {
                                                if (pricetag._must_save) {
                                                    clearTimeout($scope.syncID);
                                                    return $scope.save(true).then(function () {
                                                        image = _.findWhere($scope.args._images, {
                                                            key: image.key
                                                        });
                                                        pricetag = _.findWhere(image.pricetags, {
                                                            key: pricetag.key
                                                        });
                                                        return $scope.realManageProduct(image, pricetag, $event);
                                                    });
                                                }
                                                return $scope.realManageProduct(image, pricetag, $event);
                                            };

                                            $scope.realManageProduct = function (image, pricetag, $event) {
                                                if ($scope.loadingManageProduct) {
                                                    return;
                                                }
                                                $scope.loadingManageProduct = true;
                                                setupCurrentPricetag(image, pricetag);
                                                // perform read catalog.images.0.pricetags.0._product
                                                models['31'].actions.read({
                                                    key: $scope.entity.key,
                                                    read_arguments: {
                                                        _images: {
                                                            config: {
                                                                keys: [image.key]
                                                            },
                                                            pricetags: {
                                                                config: {
                                                                    keys: [pricetag.key],
                                                                },
                                                                _product: {}
                                                            }
                                                        }
                                                    }
                                                }).then(function (response) {
                                                    var responseEntity = response.data.entity,
                                                        ii = $scope.args._images.indexOf(image),
                                                        product = responseEntity._images[0].pricetags[0]._product,
                                                        oldPricetagIndex = _.findIndex(image.pricetags, function (ipricetag) {
                                                            return ipricetag.key === pricetag.key;
                                                        }),
                                                        realPath = ['_images', ii, 'pricetags', oldPricetagIndex, '_product'];
                                                    if (!$scope.fieldProduct.ui.specifics.toolbar) {
                                                        $scope.fieldProduct.ui.specifics.toolbar = {};
                                                    }
                                                    $scope.fieldProduct.ui.specifics.toolbar.templateActionsUrl = 'catalog/product/manage_actions.html';
                                                    pricetag._product = product;
                                                    product.ui.access = realPath; // override normalizeEntity auto generated path
                                                    $scope.fieldProduct.ui.realPath = realPath; // set same path
                                                    recomputeRealPath($scope.fieldProduct);
                                                    $scope.fieldProduct.ui.specifics.manage(product, undefined, $event); // fire up modal dialog

                                                })['finally'](function () {
                                                    $scope.loadingManageProduct = false;
                                                });
                                            };

                                            $scope.howToDrag = function ($event) {
                                                modals.alert('howToDropPricetag');
                                            };

                                            $scope.createProduct = function (image, config, target) {
                                                var ii = $scope.args._images.indexOf(image),
                                                    newPricetag = {
                                                        _sequence: image.pricetags.length,
                                                        image_height: config.image_height,
                                                        image_width: config.image_width,
                                                        position_left: config.position_left,
                                                        position_top: config.position_top,
                                                        _position_left: config.position_left,
                                                        _position_top: config.position_top,
                                                        value: {},
                                                        _destroy: config._destroy,
                                                        _product: {},
                                                        ui: {
                                                            access: ['_images', ii, 'pricetags', image.pricetags.length]
                                                        }
                                                    };
                                                addNewPricetag(image, newPricetag); // append new pricetag to image
                                                setupCurrentPricetag(image, newPricetag); // set current
                                                $scope.fieldProduct.ui.specifics.toolbar.templateActionsUrl = false;
                                                $scope.fieldProduct.ui.realPath = ['_images', ii, 'pricetags', image.pricetags.length - 1, '_product']; // set correct pathing for the new product
                                                recomputeRealPath($scope.fieldProduct);
                                                $scope.fieldProduct.ui.specifics.create(undefined, undefined, {
                                                    target: target
                                                });
                                            };

                                            $.extend($scope.fieldProduct.ui, {
                                                args: 'pricetag._product',
                                                parentArgs: 'pricetag',
                                                path: ['_images', 'pricetags', '_product'],
                                                render: false,
                                                label: false,
                                                specifics: {
                                                    remoteAutoload: false,
                                                    modal: true,
                                                    removeConfirm: function (arg, close) {
                                                        modals.confirm('removePricetagConfirm', function () {
                                                            $scope.pricetag._state = 'deleted';
                                                            $scope.save().then(close);
                                                        });
                                                    },
                                                    beforeSave: function (fieldScope) {
                                                        fieldScope.setAction('update');
                                                        // before saving entity, set the name and unit price for the pricetag.
                                                        var findPricetag = _.last(fieldScope.sendRootArgs._images[0].pricetags);
                                                        findPricetag.value = {
                                                            name: fieldScope.args.name,
                                                            price: fieldScope.args.unit_price
                                                        };
                                                    },
                                                    templateFooterUrl: 'catalog/product/manage_footer.html',
                                                    getRootArgs: function () {
                                                        // root args is data that gets sent with rpc
                                                        return $scope.args;
                                                    },
                                                    afterClose: function (fieldProductScope) {
                                                        // after close hook
                                                        $scope.pricetag._product = null;
                                                        if (!fieldProductScope.args.key) {
                                                            removePricetag($scope.image, $scope.pricetag); // remove the pricetag if we did not commit the product
                                                        }
                                                    },
                                                    afterSave: function (fieldScope) {
                                                        // after save hook
                                                        fieldScope.setAction('product_upload_images');
                                                        var updatedPricetag = fieldScope.response.data.entity._images[0].pricetags[0];
                                                        $scope.fieldProduct.ui.specifics.toolbar.templateActionsUrl = 'catalog/product/manage_actions.html';
                                                        $.extend($scope.pricetag, updatedPricetag); // after save, always update the live pricetag, because there is no way that field scope can access this scope
                                                    },
                                                    afterComplete: function (fieldScope) {
                                                        // after complete hook
                                                        fieldScope.setAction('update');
                                                    },
                                                    noComplete: function (fieldScope) {
                                                        // hook for no complete event - complete event only fires if there are images to be uploaded
                                                        fieldScope.setAction('update');
                                                    },
                                                    duplicate: function () {
                                                        modals.confirm('duplicateCatalogPricetag',
                                                            function () {
                                                                models['11'].channelNotifications({
                                                                    callback: function (response) {
                                                                        models['31'].actions.read({
                                                                            key: response.catalog_key,
                                                                            read_arguments: {
                                                                                _images: {
                                                                                    config: {
                                                                                        keys: [response.image_key]
                                                                                    },
                                                                                    pricetags: {
                                                                                        config: {
                                                                                            keys: [response.pricetag_key]
                                                                                        }
                                                                                    }
                                                                                }
                                                                            }
                                                                        }).then(function (response2) {

                                                                            var image = _.findWhere($scope.args._images, {
                                                                                key: response.image_key
                                                                            });
                                                                            if (image) {
                                                                                angular.forEach(response2.data.entity._images[0].pricetags, function (value, key) {
                                                                                    if (!_.findWhere(image.pricetags, {
                                                                                            key: response.pricetag_key
                                                                                        })) {
                                                                                        image.pricetags.push(value);
                                                                                    }
                                                                                });
                                                                            }
                                                                            snackbar.showK('productDuplicated');
                                                                        });
                                                                    }
                                                                }).then(function (response) {
                                                                    models['31'].actions.catalog_pricetag_duplicate({
                                                                        key: $scope.entity.key,
                                                                        channel: response.token,
                                                                        read_arguments: {
                                                                            _images: {
                                                                                config: {
                                                                                    keys: [$scope.image.key]
                                                                                },
                                                                                pricetags: {
                                                                                    config: {
                                                                                        keys: [$scope.pricetag.key]
                                                                                    }
                                                                                }
                                                                            }
                                                                        }
                                                                    });
                                                                });
                                                            });
                                                    }
                                                }
                                            });

                                            $.extend($scope.fieldProduct.modelclass.images.ui, {
                                                name: 'images'
                                            });

                                            $.extend($scope.fieldProduct.modelclass._instances.modelclass.images.ui, {
                                                name: 'images'
                                            });

                                            $scope.fieldProduct.modelclass.category.ui.specifics = {
                                                search: {
                                                    enabled: true
                                                }
                                            };


                                            $.extend($scope.fieldProduct.modelclass._instances.ui, {
                                                label: GLOBAL_CONFIG.subheaders.productInstances,
                                                path: ['_images', 'pricetags'],
                                                specifics: {
                                                    layoutConfig: [{
                                                        label: GLOBAL_CONFIG.fields.label['28'].variant_options,
                                                        fields: ["variant_options"]
                                                    }, {
                                                        label: 'Details',
                                                        fields: ["code", "description", "unit_price", "availability", "weight", "volume"]
                                                    }, {
                                                        fields: ["images"]
                                                    }, {
                                                        fields: ["contents"]
                                                    }],
                                                    cards: true,
                                                    cardView: 'product-instance-card-view',
                                                    getRootArgs: function () {
                                                        return $scope.args;
                                                    },
                                                    beforeSave: function (fieldScope) {
                                                        fieldScope.setAction('update');
                                                    },
                                                    afterSave: function (fieldScope) {
                                                        fieldScope.setAction('product_instance_upload_images');
                                                    },
                                                    afterComplete: function (fieldScope) {
                                                        fieldScope.setAction('update');
                                                    },
                                                    noComplete: function (fieldScope) {
                                                        fieldScope.setAction('update');
                                                    },
                                                    setupSortableOptions: function () {
                                                        return {
                                                            forcePlaceholderSize: true,
                                                            stop: function () {
                                                                var field = $scope.fieldProduct.modelclass._instances,
                                                                    total,
                                                                    dirty,
                                                                    scope = field.ui.directiveScope();
                                                                if (field.ui.specifics.parentArgs.length) {
                                                                    total = field.ui.specifics.parentArgs[0].sequence;
                                                                    angular.forEach(field.ui.specifics.parentArgs,
                                                                        function (ent, i) {
                                                                            i = (total - i);
                                                                            if (ent.sequence !== i || ent._state === 'deleted') {
                                                                                dirty = true;
                                                                            }
                                                                            ent.sequence = i;
                                                                            ent.ui.access[ent.ui.access.length - 1] = i;
                                                                        });
                                                                    if (dirty) {
                                                                        scope.formSetDirty();
                                                                    }
                                                                    scope.$broadcast('itemOrderChanged');
                                                                    scope.$apply();
                                                                }
                                                            }
                                                        };
                                                    },
                                                    canOpen: function () {
                                                        var currentFieldScope = $scope.fieldProduct.ui.specifics.getScope(),
                                                            currentArgs = currentFieldScope.args;
                                                        if (!currentArgs.id) {
                                                            snackbar.showK('saveProductFirst');
                                                            return false;
                                                        }
                                                        if (!currentArgs.variants.length) {
                                                            snackbar.showK('createVariantsFirst');
                                                            return false;
                                                        }
                                                        return true;
                                                    },
                                                    init: function () {
                                                        var currentFieldScope = $scope.fieldProduct.ui.specifics.getScope(),
                                                            currentArgs = currentFieldScope.args,
                                                            choices = [];

                                                        angular.forEach(currentArgs.variants, function (variant) {
                                                            if (variant.allow_custom_value) {
                                                                return;
                                                            }
                                                            angular.forEach(variant.options, function (variantOpt) {
                                                                choices.push(variant.name + ': ' + variantOpt);
                                                            });
                                                        });

                                                        variantOptions.choices = choices;
                                                    },
                                                    excludeFields: ['created', 'sequence']
                                                }
                                            });

                                            $.extend($scope.fieldProduct.modelclass.contents.ui, {
                                                specifics: {}
                                            });

                                            $.extend($scope.fieldProduct.modelclass.images.ui, {
                                                name: 'images',
                                                specifics: {}
                                            });

                                            $.extend($scope.fieldProduct.modelclass.variants.ui, {
                                                specifics: {}
                                            });

                                            if (!$scope.fieldProduct.modelclass.uom.ui.specifics) {
                                                $scope.fieldProduct.modelclass.uom.ui.specifics = {};
                                            }

                                            $scope.fieldProduct.modelclass.uom.ui.specifics.grouping = function (items) {
                                                var grouped = [],
                                                    current;
                                                angular.forEach(items, function (item) {
                                                    if (current && current.label !== item.measurement) {
                                                        current = null;
                                                    }
                                                    if (!current) {
                                                        current = {
                                                            label: item.measurement,
                                                            items: []
                                                        };
                                                        grouped.push(current);
                                                    }

                                                    current.items.push(item);
                                                });

                                                return grouped;
                                            };

                                            $scope.loadingSave = false;

                                            $scope.save = function (hideSnackbar) {
                                                var promise;
                                                if ($scope.loadingSave) {
                                                    return;
                                                }
                                                $scope.rootScope.config.prepareReadArguments($scope);
                                                $scope.loadingSave = true;
                                                promise = models['31'].actions[$scope.args.action_id]($scope.args);
                                                promise.then(function (response) {
                                                    $.extend($scope.entity, response.data.entity);
                                                    var newArgs = $scope.rootScope.config.argumentLoader($scope);
                                                    $.extend(parentScope.args, angular.copy(newArgs));
                                                    $.extend($scope.args, angular.copy(newArgs));
                                                    $scope.formSetPristine();
                                                    if (!hideSnackbar) {
                                                        snackbar.showK('changesSaved');
                                                    }
                                                })['finally'](function () {
                                                    $scope.loadingSave = false;
                                                });
                                                return promise;
                                            };

                                            $scope.syncID = null;
                                            $scope.sync = function (hideSnackbar) {
                                                var defer = $q.defer(),
                                                    promise = defer.promise;
                                                clearTimeout($scope.syncID);
                                                $scope.syncID = setTimeout(function () {
                                                    $scope.save(hideSnackbar).then(function (response) {
                                                        defer.resolve(response);
                                                        return response;
                                                    });
                                                }, 1000);
                                                return promise;
                                            };
                                        })
                                    });

                                },
                                layouts: {
                                    groups: [{
                                        label: false,
                                        fields: ['name', 'discontinue_date'],
                                    }, {
                                        label: GLOBAL_CONFIG.subheaders.catalogImages,
                                        include: 'core/misc/action.html',
                                        action: function () {
                                            var scope = config.getScope();
                                            helpers.form.wakeUp(scope.container.form);
                                            if (!scope.container.form.$valid) {
                                                snackbar.showK('provideProperValues');
                                                return;
                                            }
                                            modals.fields.remote(config.getScope(), fields._images);
                                        }
                                    }, {
                                        label: GLOBAL_CONFIG.subheaders.catalogProducts,
                                        include: 'core/misc/action.html',
                                        action: function () {
                                            var scope = config.getScope();

                                            if (!scope.entity.cover) {
                                                snackbar.showK('uploadImagesFirst');
                                                return;
                                            }
                                            config.getScope().addProducts();
                                        }
                                    }]
                                }
                            }
                        };

                    if (isNew) {
                        // get current seller
                        models['23'].current().then(function (response) {
                            modelsEditor.create(config).prepare({}, {
                                seller: response.data.entity.key
                            }, {
                                handleError: GLOBAL_CONFIG.backendErrorHandling.sellerProfileNotFound
                            });
                        });

                    } else {
                        modelsEditor.create(config).read(catalog, {
                            key: catalog.key
                        });

                    }

                }
            });

        });
    }));
}());
(function () {
    'use strict';
    angular.module('app').run(ng(function (modelsConfig, endpoint, $state, modals, currentAccount, modelsMeta, GLOBAL_CONFIG, modelsEditor, helpers, $timeout, snackbar) {
        modelsConfig(function (models) {
            var read_arguments = {
                _sellers: {
                    _content: {},
                    _feedback: {}
                }
            };

            $.extend(models['18'], {
                current: function (args) {
                    if (!args) {
                        args = {};
                    }
                    args.account = currentAccount.key;
                    return this.actions.read(args, {
                        cache: this.getCacheKey('current'),
                        cacheType: 'memory'
                    });
                },
                manageModal: function (accountKey, modalConfig) {
                    if (!modalConfig) {
                        modalConfig = {};
                    }
                    var fields = modelsMeta.getActionArguments(this.kind, 'update'),
                        config;
                    config = {
                        kind: this.kind,
                        action: 'update',
                        fields: _.toArray(fields),
                        toolbar: {
                            hideSave: true,
                            titleEdit: 'buyer.edit18'
                        },
                        modalConfig: modalConfig,
                        templateBodyUrl: 'collection/manage_body.html',
                        excludeFields: ['account', 'read_arguments'],
                        init: function ($scope) {
                            $scope.$watch('args.notify', function (neww, old) {
                                if (neww !== old) {
                                    $scope.save().then(function () {
                                        snackbar.showK('changesSaved');
                                        $scope.entity._sellers.iremove(function (seller) {
                                            return $.inArray(seller.key, $scope.entity.sellers) === -1;
                                        });
                                        models['18'].current().then(function (response) {
                                            $.extend(response.data.entity, $scope.entity);
                                        });
                                    });
                                }
                            });

                            $scope.collectionDrag = {
                                options: {
                                    disabled: false,
                                    handle: '.sort-handle',
                                    distance: 10,
                                    stop: function (e, ui) {
                                        $scope.$apply();
                                    }
                                },
                                whatSortMeans: function () {
                                    modals.alert('howToDeleteDragging');
                                },
                                onStart: function (e, ui, seller) {
                                    $(ui.helper).find('.sort-handle').addClass('dragged');
                                },
                                onDrag: function (e, ui, seller) {
                                    var deleteMode,
                                        division,
                                        helperWidth = ui.helper.width();
                                    division = ui.offset.left + helperWidth;
                                    if (division < (helperWidth / 2)) {
                                        deleteMode = true;
                                    }
                                    if (seller) {
                                        if (deleteMode) {
                                            ui.helper.addClass('about-to-delete');
                                        } else {
                                            ui.helper.removeClass('about-to-delete');
                                        }
                                    }
                                },
                                onStop: function (e, ui, seller) {
                                    if (ui.helper.hasClass('about-to-delete')) {
                                        ui.helper.animate({
                                            left: (ui.helper.width() * 2) * -1
                                        }, function () {
                                            $timeout(function () {
                                                $scope.remove(seller);
                                            });
                                        });
                                    } else {
                                        ui.helper.animate(ui.originalPosition, function () {
                                            ui.helper.attr('style', '');
                                        });
                                    }
                                }
                            };
                        },
                        scope: {
                            remove: function (seller) {
                                var scope = this,
                                    sellers;
                                scope.args.sellers.remove(seller.key);
                                scope.entity._sellers.remove(seller);
                                sellers = scope.entity._sellers.concat();
                                scope.save().then(function () {
                                    snackbar.showK('changesSaved');
                                    scope.entity._sellers = sellers;
                                    models['23'].decrementGlobalSellerStack(seller.key, scope.args.notify);
                                    models['18'].current().then(function (response) {
                                        var collection = response.data.entity;
                                        collection.sellers.remove(seller.key);
                                        return collection;
                                    });
                                });
                            },
                            view: function (seller, $event) {
                                models['23'].viewProfileModal(seller.parent.key, {
                                    popFrom: helpers.clicks.realEventTarget($event.target),
                                    inDirection: false,
                                    sellerDetails: {
                                        removedOrAdded: function (updatedCollection, inCollection) {
                                            if (!inCollection) {
                                                seller._state = 'deleted';
                                            } else {
                                                seller._state = null;
                                            }
                                        }
                                    },
                                    outDirection: false
                                });
                            },
                            layouts: {
                                groups: [{
                                    label: false
                                }, {
                                    label: GLOBAL_CONFIG.subheaders.collectionSeller
                                }]
                            }
                        }
                    };

                    modelsEditor.create(config).read({}, {
                        account: accountKey,
                        read_arguments: read_arguments
                    });

                }
            });

        });
    }));
}());(function () {
    'use strict';
    angular.module('app')
        .controller('RootController', ng(function ($scope, $mdSidenav, $timeout) {}))
        .directive('closeMasterMenu', ng(function ($mdSidenav, $timeout, $parse) {
            return {
                link: function (scope, element, attrs) {
                    var callback = $parse(attrs.closeMasterMenu);
                    element.on('click', function () {
                        scope.site.toolbar.menu.close().then(function () {
                            if (callback) {
                                if (scope.$$phase) {
                                    callback(scope, {
                                        $event: event
                                    });
                                } else {
                                    scope.$apply(function () {
                                        callback(scope, {
                                            $event: event
                                        });
                                    });
                                }
                            }
                        });
                    });
                }
            };
        }))
        .directive('homeSplash', ng(function ($animate) {
            return {
                restrict: 'A',
                link: function (scope, element, attrs) {
                    element.addClass('fade out').oneAnimationEnd(function () {
                        element.addClass('ng-hide');
                    });
                }
            };
        }))
        .controller('LoginLinksController', ng(function ($scope, models) {
            $scope.login = function () {
                models['11'].login();
            };
        }))
        .run(ng(function ($rootScope, GLOBAL_CONFIG, currentAccount, helpers) {
            $rootScope.site = {
                title: '',
                toolbar: {
                    hideRight: true,
                    hideLeft: false,
                    title: '',
                    menu: {}
                }
            };
            $rootScope.currentAccount = currentAccount;
            $rootScope.GLOBAL_CONFIG = GLOBAL_CONFIG;
            $rootScope.JSON = JSON;
            $rootScope.helpers = helpers;
            $rootScope.setPageTitle = function (title, notToolbarTitle) {
                $rootScope.site.title = helpers.toolbar.title(title);
                if (!notToolbarTitle) {
                    $rootScope.site.toolbar.title = $rootScope.site.title;
                }
            };
            $rootScope.setPageToolbarTitle = function (title, notPageTitle) {
                $rootScope.site.toolbar.title = helpers.toolbar.title(title);
                if (!notPageTitle) {
                    $rootScope.site.title = $rootScope.site.toolbar.title;
                }
            };

            $rootScope.$on('$stateChangeStart', function () {
                $rootScope.site.toolbar.hideRight = true;
                $rootScope.site.toolbar.actionRight = undefined;
                $rootScope.site.toolbar.hidden = false;
            });

            helpers.sideNav.setup($rootScope.site.toolbar.menu, 'left');
        }))
        .controller('AboutController', ng(function ($scope) {
            $scope.socials = [{
                name: 'Facebook',
                key: 'facebook',
                command: 'https://www.facebook.com/fbpage'
            }, {
                name: 'Twitter',
                key: 'twitter',
                command: 'https://twitter.com/twitteracc'
            }, {
                name: 'Pinterest',
                key: 'pinterest',
                command: 'https://www.pinterest.com/pinterestacc'
            }, {
                name: 'Reddit',
                key: 'reddit',
                command: 'https://www.reddit.com/subreddit'
            }, {
                name: 'Linkedin',
                key: 'linkedin',
                command: 'https://www.linkedin.com/profile'
            }, {
                name: 'Google+',
                icon: 'googleplus',
                command: 'https://plus.google.com/pageid',
            }, {
                name: 'Tumblr',
                key: 'tumblr',
                command: 'https://www.tumblr.com/profile'
            }];

            $scope.share = function (soc) {
                return soc.command;
            };

            $scope.getIcon = function (soc) {
                return '/client/dist/static/social/' + (soc.icon || soc.name.toLowerCase()) + '.png';
            };

            $scope.setPageToolbarTitle('about');

        }))
        .controller('HomePageController', ng(function ($scope, models, modals, $state, $stateParams, helpers, $q, modelsMeta) {
            var args = {
                    search: {}
                },
                defer = $q.defer(),
                promise = defer.promise;

            $scope.setPageToolbarTitle('home');
            $scope.sellerDetails = false;
            $scope.viewProfile = function (key, $event) {
                models['23'].viewProfileModal(key, {
                    popFrom: $event.target
                });
            };
            $scope.view = function (key, $event) {
                models['31'].viewModal(key, {
                    popFrom: helpers.clicks.realEventTarget($event.target)
                });
            };

            if ($stateParams.key) {
                $scope.sellerMode = true;
                $scope.setPageToolbarTitle('sellerProfile');
                args.search.filters = [{
                    field: 'seller_account_key',
                    operator: 'IN',
                    value: $stateParams.key
                }];
                models['23'].actions.read({
                    account: $stateParams.key,
                    read_arguments: {
                        _feedback: {},
                        _content: {}
                    }
                }).then(function (response) {
                    $scope.sellerDetails = models['23'].makeSellerDetails(response.data.entity);
                });

                $scope.site.toolbar.hideRight = false;
                $scope.site.toolbar.actionRight = function () {
                    $scope.sellerDetails.menu.open();
                };
            }
            if ($state.current.name === 'following') {
                promise = models['18'].current();
                promise.then(function (response) {
                    var sids = response.data.entity.sellers;
                    args.search.filters = [{
                        field: 'ancestor',
                        operator: 'IN',
                        value: sids.length ? sids : ['nothing']
                    }];
                });
            } else {
                defer.resolve();
            }
            $scope.search = {
                results: [],
                pagination: models['31'].paginate({
                    kind: '31',
                    args: args,
                    config: {
                        normalizeEntity: false
                    },
                    action: 'public_search',
                    complete: function (response) {
                        var results = response.data.entities;
                        models['31'].formatPublicSearchResults(results);
                        $scope.search.results.extend(results);
                    }
                })
            };
            $scope.scrollEnd = {
                loader: false
            };
            $scope.scrollEnd.loader = $scope.search.pagination;
            promise.then(function () {
                $scope.search.pagination.load();
            });


        }));

}());
(function () {
    'use strict';
    angular.module('app').run(ng(function (modelsConfig, modelsMeta) {
        modelsConfig(function (models) {
            models['12'].config.cache = true;
            models['12'].getSubdivisions = function (countryKey, overrideConfig) {
                var subdivisionModel = models['13'],
                    defaultArgs = modelsMeta.getDefaultActionArguments(subdivisionModel.kind, 'search');
                defaultArgs.ancestor = countryKey;
                return subdivisionModel.search(defaultArgs, overrideConfig);
            };

        });

    }));
}());(function () {
    'use strict';
    angular.module('app')
        .controller('OrderViewController', ng(function ($scope, models, currentAccount, $state) {

            var entity = false;

            models['34'].manageModal({
                key: $state.params.key
            }, undefined, undefined, {
                inDirection: false,
                outDirection: false,
                afterClose: function () {
                    if (!entity) {
                        return;
                    }
                    if (entity.parent.parent.key === currentAccount.key) {
                        // this is buyer
                        $state.go('buy-orders');
                    } else {
                        // this is seller
                        $state.go('sell-orders');
                    }
                }
            }).then(function (response) {
                entity = response;
            });

        }))
        .directive('alwaysScrollToBottom', ng(function ($timeout) {
            return {
                link: function (scope, element, attrs) {
                    var cb = function () {
                        element.scrollTop(element[0].scrollHeight);
                    };

                    scope.$watchGroup(scope.$eval(attrs.alwaysScrollToBottom), function (neww, old) {
                        if (neww !== old) {
                            $timeout(cb, 100, 0);
                        }
                    });
                }
            };
        })).filter('displayTaxes', ng(function () {
            return function (value) {
                var formatted = '';
                if (value) {
                    formatted = $.map(value, function (item) {
                        return item.name;
                    }).join(', ');
                }
                return formatted;
            };
        })).run(ng(function (modelsMeta, modelsConfig, $modal, modals, snackbar, $state, helpers, endpoint, $q, $filter, currentAccount, $mdSidenav, $timeout) {
            modelsConfig(function (models) {
                $.extend(models['34'], {
                    current: function (sellerKey) {
                        var that = this;
                        return models['19'].current().then(function (response) {
                            var buyer = response.data.entity;
                            return that.actions.view_order({
                                buyer: buyer.key,
                                seller: sellerKey
                            }, {
                                cache: that.getCacheKey('current' + sellerKey),
                                cacheType: 'memory'
                            });
                        });
                    },
                    adminManageModal: function (order, extraConfig) {
                        extraConfig = helpers.alwaysObject(extraConfig);
                        return this.manageModal(order, order._seller, undefined, $.extend({
                            sellerMode: true
                        }, extraConfig));
                    },
                    manageModal: function (order, seller, buyer, config) {
                        config = helpers.alwaysObject(config);
                        var args, that = this,
                            cartMode = config.cartMode,
                            sellerMode = config.sellerMode,
                            openDefer = $q.defer(),
                            openPromise = openDefer.promise,
                            rpc = {};
                        if (!cartMode) {
                            args = {
                                key: order.key,
                                read_arguments: {
                                    _lines: {
                                        config: {
                                            limit: 0
                                        }
                                    },
                                    _seller: {
                                        _feedback: {},
                                        _content: {}
                                    },
                                    _messages: {
                                        _agent: {}
                                    }
                                }
                            };
                        } else {
                            args = {
                                buyer: buyer.key,
                                seller: seller.key,
                                read_arguments: {
                                    _seller: {
                                        _feedback: {},
                                        _content: {}
                                    },
                                    _messages: {
                                        _agent: {}
                                    }
                                }
                            };
                        }

                        models['34'].actions[cartMode ? 'view_order' : 'read'](args, rpc).then(function (response) {
                            seller = response.data.entity._seller;
                            var modalOpen = {
                                templateUrl: 'order/view.html',
                                controller: ng(function ($scope) {
                                    var locals = {
                                        customPlaceholder: null,
                                        updateLiveEntity: function (response) {
                                            var messages = $scope.order._messages;
                                            $.extend($scope.order, response.data.entity);
                                            $scope.order._messages = messages;
                                        },
                                        reactOnStateChange: function (response) {
                                            helpers.update($scope.order, response.data.entity, ['state', 'feedback_adjustment', 'feedback', 'ui']);
                                            locals.reactOnUpdate();
                                        },
                                        reactOnUpdate: function (skipCache) {
                                            if (order) {
                                                $.extend(order, $scope.order);
                                            }
                                            if (!skipCache && that.getCache('current' + seller.key)) {
                                                that.current(seller.key).then(function (response) {
                                                    $.extend(response.data.entity, $scope.order);
                                                });
                                            }
                                        },
                                        logMessageAction: modelsMeta.getActionArguments('34', 'log_message'),
                                        orderUpdateFields: modelsMeta.getActionArguments('34', 'update'),
                                        billingAddressFields: [],
                                        shippingAddressFields: [],
                                        sorter: function (field, prev) {
                                            var indx = models['19'].manageModalFieldsOrder.indexOf(field.code_name),
                                                b = models['19'].manageModalFieldsOrder.indexOf(prev.code_name);
                                            if (indx === -1) {
                                                indx = 99999;
                                            }
                                            return indx - b;
                                        }
                                    };

                                    angular.forEach(locals.orderUpdateFields.shipping_address.modelclass, function (value) {
                                        $.extend(value.ui, {
                                            args: 'addresses.shipping.' + value.code_name,
                                            parentArgs: 'addresses.shipping',
                                            writable: true,
                                            name: 'supplier_' + value.code_name
                                        });
                                        value.required = (value.required ? '!addresses.sameAsBilling' : false);
                                        locals.shippingAddressFields.push(value);
                                    });

                                    angular.forEach(locals.orderUpdateFields.billing_address.modelclass, function (value) {
                                        $.extend(value.ui, {
                                            args: 'addresses.billing.' + value.code_name,
                                            parentArgs: 'addresses.billing',
                                            writable: true,
                                            name: 'supplier_' + value.code_name
                                        });
                                        locals.billingAddressFields.push(value);
                                    });

                                    locals.billingAddressFields.sort(locals.sorter);
                                    locals.shippingAddressFields.sort(locals.sorter);

                                    $.extend(locals.logMessageAction.message.ui, {
                                        label: false,
                                        args: 'messages.draft.message',
                                        parentArgs: 'messages.draft',
                                        writable: 'order.ui.rule.action.log_message.executable || !order.id',
                                        placeholder: 'Type a message here',
                                        attrs: {
                                            'native-placeholder': '',
                                            'class': 'primary',
                                            'min-length': '1'
                                        }
                                    });

                                    $scope.dialog = {
                                        toolbar: {
                                            templateRight: 'order/toolbar_actions.html'
                                        }
                                    };

                                    $scope.$watch('order.state', function (neww, old) {
                                        var title = 'Cart';
                                        if (neww === 'completed') {
                                            title = 'Order';
                                        }
                                        $scope.dialog.toolbar.title = title;
                                    });

                                    $scope.today = new Date();

                                    $scope.stage = {
                                        checkout: null,
                                        current: 1,
                                        out: [],
                                        canShowPay: function () {
                                            return $scope.order.state === 'checkout';
                                        },
                                        isOut: function (indx) {
                                            return $.inArray(indx, $scope.stage.out) !== -1;
                                        },
                                        toCheckout: function () {
                                            $scope.stage.out.push(1);
                                            $scope.stage.current = 2;
                                        },
                                        toDeliveryMethod: function () {
                                            var valid = $scope.addresses.form.billing.$valid,
                                                addressing = {
                                                    billing_address: $scope.addresses.billing
                                                };
                                            if (!$scope.addresses.sameAsBilling) {
                                                valid = valid && $scope.addresses.form.shipping.$valid;
                                                addressing.shipping_address = $scope.addresses.shipping;
                                            } else {
                                                addressing.shipping_address = $scope.addresses.billing;
                                            }
                                            if (valid) {
                                                $scope.cmd.order.update(addressing).then(function (response) {
                                                    if (response.data.errors) {
                                                        return;
                                                    }
                                                    $scope.stage.out.push(2);
                                                    $scope.stage.current = 3;
                                                });
                                            } else {
                                                helpers.form.wakeUp($scope.addresses.form.billing);
                                                if (!$scope.addresses.sameAsBilling) {
                                                    helpers.form.wakeUp($scope.addresses.form.shipping);
                                                }
                                            }
                                        },
                                        toReviewOrder: function () {
                                            modals.confirm('toCheckout', function () {
                                                if ($scope.carrier.form.$valid) {
                                                    // state = 'checkout' is needed here
                                                    $scope.cmd.order.update({
                                                        carrier: $scope.carrier.selected,
                                                        state: 'checkout'
                                                    }).then(function () {
                                                        $scope.stage.out.push(3);
                                                        $scope.stage.current = 4;
                                                    });
                                                } else {
                                                    helpers.form.wakeUp($scope.carrier.form);
                                                }
                                            });
                                        },
                                        complete: function () {
                                            $scope.stage.out = [];
                                            $scope.stage.current = 1;
                                        }
                                    };
                                    $scope.logoImageConfig = {
                                        size: 280
                                    };
                                    $scope.cmd = {};
                                    $scope.container = {};
                                    $scope.cartMode = cartMode;
                                    $scope.sellerMode = sellerMode;
                                    $scope.order = response.data.entity;
                                    $scope.seller = seller;
                                    $scope.currentAccount = currentAccount;
                                    $scope.addresses = {
                                        sameAsBilling: true,
                                        form: {},
                                        shipping: {},
                                        billing: {},
                                        browse: function (type) {
                                            var parentScope = $scope;
                                            models['19'].current().then(function (response) {
                                                $modal.open({
                                                    inDirection: false,
                                                    windowClass: 'modal-medium-simple',
                                                    outDirection: false,
                                                    fullScreen: false,
                                                    backdrop: true,
                                                    templateUrl: 'order/browse_addresses.html',
                                                    controller: ng(function ($scope) {
                                                        $scope.addresses = response.data.entity.addresses;
                                                        $scope.select = function (ent) {
                                                            var doit = function () {
                                                                angular.forEach(ent, function (value, key) {
                                                                    parentScope.addresses[type][key] = value;
                                                                });
                                                            };
                                                            doit();
                                                            $scope.$close().then(function () {
                                                                $timeout(doit, 100); // fix for region
                                                            }); // scope apply
                                                        };
                                                        $scope.manage = function () {
                                                            models['19'].manageModal(response.data.entity.parent.key, function () {
                                                                models['19'].current().then(function (response) {
                                                                    $scope.addresses = response.data.entity.addresses;
                                                                });
                                                            }, {
                                                                inDirection: false,
                                                                outDirection: false
                                                            });
                                                        };
                                                    })
                                                });
                                            });
                                        },
                                        fields: {
                                            shipping: locals.shippingAddressFields,
                                            billing: locals.billingAddressFields,
                                            sameAsBilling: {
                                                type: 'SuperBooleanProperty',
                                                code_name: 'sameAsBilling',
                                                ui: {
                                                    writable: true,
                                                    parentArgs: 'addresses',
                                                    args: 'addresses.sameAsBilling',
                                                    specifics: {
                                                        type: 'checkbox'
                                                    }
                                                }
                                            }
                                        }
                                    };

                                    $scope.payment = {
                                        method: $scope.order.payment_method
                                    };

                                    $scope.carrier = {
                                        selected: $scope.order.carrier ? $scope.order.carrier.reference : null,
                                        available: (response.data.carriers || []),
                                        form: null
                                    };

                                    $scope.format = {
                                        variantLabel: function (variant) {
                                            return Object.keys(variant)[0];
                                        },
                                        variantValue: function (variant) {
                                            return variant[$scope.format.variantLabel(variant)];
                                        }
                                    };

                                    if ($scope.order._messages && $scope.order._messages.length) {
                                        $scope.order._messages.reverse();
                                    }

                                    $scope.messages = {
                                        reader: $scope.order.id ? models['34'].reader({
                                            key: $scope.order.key,
                                            next: {
                                                _messages: angular.copy($scope.order._next_read_arguments._messages)
                                            },
                                            access: ['_messages'],
                                            complete: function (items) {
                                                $scope.order._messages.prepend(items);
                                            }
                                        }) : {},
                                        toggling: false,
                                        open: false,
                                        stateChanged: function (state) {
                                            $scope.messages.sync.toggle(state);
                                        },
                                        sync: {
                                            timer: null,
                                            active: false,
                                            stop: function () {
                                                this.active = false;
                                                this.loading = false;
                                                clearTimeout(this.timer);
                                            },
                                            start: function () {
                                                if (!$scope.order.id || !$scope.order._lines.length) {
                                                    return;
                                                }
                                                this.active = true;
                                                this.run();
                                            },
                                            toggle: function (what) {
                                                if (what) {
                                                    this.start();
                                                } else {
                                                    this.stop();
                                                }
                                            },
                                            loading: false,
                                            run: function () {
                                                var sync = this;
                                                if (this.loading || !this.active) {
                                                    return;
                                                }
                                                clearTimeout(this.timer);
                                                this.loading = true;
                                                this.timer = setTimeout(function () {
                                                    models['34'].actions.read({
                                                        key: $scope.order.key,
                                                        read_arguments: {
                                                            _messages: {
                                                                _agent: {}
                                                            }
                                                        }
                                                    }, {
                                                        disableUI: false
                                                    }).then(function (response) {
                                                        var map = {},
                                                            changed = false,
                                                            items = response.data.entity._messages;
                                                        angular.forEach($scope.order._messages, function (value, key) {
                                                            map[value.key] = 1;
                                                        });
                                                        angular.forEach(items, function (value) {
                                                            if (!map[value.key]) {
                                                                $scope.order._messages.push(value);
                                                                changed = true;
                                                            }
                                                        });
                                                        if (changed) {
                                                            $scope.messages.forceReflow();
                                                        }
                                                    })['finally'](function () {
                                                        sync.loading = false;
                                                        sync.timer = null;
                                                        sync.run();
                                                    });
                                                }, 2000);
                                            },
                                        },
                                        draft: {
                                            message: null,
                                            key: $scope.order.key
                                        },
                                        field: locals.logMessageAction.message,
                                        nav: function () {
                                            return $mdSidenav($scope.messages.sidebarID);
                                        },
                                        sent: false,
                                        send: function (action) {
                                            return models['34'].actions[action]($scope.messages.draft).then(function (response) {
                                                $scope.messages.draft.message = '';
                                                $scope.messages.forceReflow();
                                                $scope.order._messages.push(response.data.entity._messages[0]);
                                                locals.reactOnStateChange(response);
                                                return response;
                                            });
                                        },
                                        forceReflow: function () {
                                            $scope.messages.sent = !$scope.messages.sent;
                                        },
                                        sidebarID: 'messages' + _.uniqueId(),
                                        logMessage: function () {
                                            if (!$scope.order._lines.length) {
                                                snackbar.showK('messangerDisabledWhenEmpty');
                                                return;
                                            }
                                            if ($scope.container.messages.$valid) {
                                                return this.send('log_message').then(function (response) {
                                                    $scope.container.messages.$setSubmitted(true);
                                                    $scope.container.messages.$setPristine(true);
                                                    return response;
                                                });
                                            }
                                            helpers.form.wakeUp($scope.container.messages);
                                        },
                                        close: function () {
                                            return $scope.message.toggle(true);
                                        },
                                        toggle: function (close) {
                                            if (!$scope.order._lines.length) {
                                                snackbar.showK('messangerDisabledWhenEmpty');
                                            }
                                            if ($scope.messages.toggling) {
                                                return;
                                            }
                                            var it = $scope.messages.nav(),
                                                isOpen = it.isOpen();
                                            $scope.messages.toggling = true;
                                            if (close === true) {
                                                isOpen = true;
                                            }
                                            $timeout(function () {
                                                it[isOpen ? 'close' : 'open']().then(function () {
                                                    $scope.messages.toggling = false;
                                                    $scope.messages.open = !isOpen;
                                                });
                                            });
                                        }
                                    };

                                    $scope.feedback = {
                                        canShowButton: function () {
                                            var maybe = false;
                                            angular.forEach(['leave_feedback', 'review_feedback', 'sudo_feedback'], function (k) {
                                                if (!maybe) {
                                                    maybe = $scope.order.ui.rule.action[k].executable;
                                                }
                                            });
                                            return maybe;
                                        },
                                        isBuyer: function () {
                                            return $scope.order.ui.rule.action.leave_feedback.executable || $scope.order.ui.rule.action.sudo_feedback.executable;
                                        },
                                        showAction: function () {
                                            var parentScope = $scope,
                                                leaveFeedbackArgs = modelsMeta.getActionArguments('34', 'leave_feedback');
                                            $.extend(leaveFeedbackArgs.message.ui, {
                                                writable: true,
                                                parentArgs: 'feedback',
                                                args: 'feedback.message',
                                                label: false,
                                                placeholder: 'Please, write a comment here. Comments appear in the messages feed.',
                                                attrs: {
                                                    'native-placeholder': '',
                                                    'class': 'full-width'
                                                }
                                            });
                                            if ($scope.feedback.isBuyer()) {
                                                $modal.open({
                                                    fullScreen: false,
                                                    inDirection: false,
                                                    outDirection: false,
                                                    cantCloseWithBackdrop: true,
                                                    templateUrl: 'order/leave_feedback.html',
                                                    controller: ng(function ($scope) {
                                                        $scope.config = {};
                                                        $scope.feedback = {
                                                            form: null,
                                                            messageField: leaveFeedbackArgs.message,
                                                            message: '',
                                                            choice: 'neutral',
                                                            choices: [{
                                                                key: 'positive'
                                                            }, {
                                                                key: 'negative'
                                                            }, {
                                                                key: 'neutral'
                                                            }]
                                                        };
                                                        $scope.config.dismiss = function () {
                                                            return $scope.$close();
                                                        };

                                                        $scope.config.text = {
                                                            primary: 'Ok'
                                                        };

                                                        $scope.config.confirm = function () {
                                                            if ($scope.feedback.form.$valid) {
                                                                models['34'].actions[parentScope.order.ui.rule.action.leave_feedback.executable ? 'leave_feedback' : 'sudo_feedback']({
                                                                    key: parentScope.order.key,
                                                                    message: $scope.feedback.message,
                                                                    feedback: $scope.feedback.choice
                                                                }).then(function (response) {
                                                                    parentScope.order._messages.push(response.data.entity._messages[0]);
                                                                    locals.reactOnStateChange(response);
                                                                    $scope.config.dismiss();
                                                                    snackbar.showK('feedbackLeft');
                                                                });
                                                            } else {
                                                                helpers.form.wakeUp($scope.feedback.form);
                                                            }
                                                        };
                                                    })
                                                });
                                            } else {
                                                $modal.open({
                                                    fullScreen: false,
                                                    inDirection: false,
                                                    outDirection: false,
                                                    cantCloseWithBackdrop: true,
                                                    templateUrl: 'order/seller_feedback.html',
                                                    controller: ng(function ($scope) {
                                                        $scope.config = {};
                                                        $scope.feedback = {
                                                            form: null,
                                                            messageField: leaveFeedbackArgs.message,
                                                            message: '',
                                                            choice: 'review_feedback',
                                                            choices: [{
                                                                key: 'review_feedback',
                                                                name: 'Ask the buyer to review feedback'
                                                            }, {
                                                                key: 'report_feedback',
                                                                name: 'Ask the admin to intervene'
                                                            }]
                                                        };
                                                        $scope.config.dismiss = function () {
                                                            return $scope.$close();
                                                        };

                                                        $scope.config.text = {
                                                            primary: 'Ok'
                                                        };

                                                        $scope.order = parentScope.order;

                                                        $scope.config.confirm = function () {
                                                            if ($scope.feedback.form.$valid) {
                                                                models['34'].actions[$scope.feedback.choice]({
                                                                    key: parentScope.order.key,
                                                                    message: $scope.feedback.message
                                                                }).then(function (response) {
                                                                    parentScope.order._messages.push(response.data.entity._messages[0]);
                                                                    locals.reactOnStateChange(response);
                                                                    $scope.config.dismiss();
                                                                    snackbar.showK('feedback' + ($scope.feedback.choice === 'report_feedback' ? 'Reported' : 'Reviewed'));
                                                                });
                                                            } else {
                                                                helpers.form.wakeUp($scope.feedback.form);
                                                            }
                                                        };
                                                    })
                                                });
                                            }
                                        }
                                    };

                                    $scope.cmd.order = {
                                        update: function (extra) {
                                            var data = {
                                                key: $scope.order.key,
                                                payment_method: $scope.payment.method,
                                                _lines: $scope.order._lines
                                            };
                                            $.extend(data, extra);
                                            return models['34'].actions.update(data, {
                                                ignoreErrors: true
                                            }).then(function (response) {
                                                var errors = response.data.errors;
                                                if (errors) {
                                                    if (errors.plugin_error && $.inArray('invalid_address', errors.plugin_error) !== -1) {
                                                        snackbar.showK('sellerProhibtsAddress');
                                                    }
                                                    return response;
                                                }
                                                locals.updateLiveEntity(response);
                                                locals.reactOnUpdate();
                                                $scope.carrier.available = response.data.carriers;
                                                $scope.carrier.selected = response.data.entity.carrier ? response.data.entity.carrier.reference : null;
                                                return response;
                                            });
                                        },
                                        cancel: function () {
                                            if ($scope.order.state === 'checkout') {
                                                modals.confirm('cancelOrder', function () {
                                                    models['34'].actions.cancel({
                                                        key: $scope.order.key
                                                    }).then(function (response) {
                                                        locals.updateLiveEntity(response);
                                                        locals.reactOnUpdate(true);
                                                        models['34'].removeCache('current' + seller.key);
                                                        $scope.close();
                                                    });
                                                });
                                            }
                                        }
                                    };

                                    $scope.cmd.line = {
                                        view: function (line, $event) {
                                            var path = line.product._reference;
                                            models['31'].viewProductModal(path.parent.parent.parent.key,
                                                path.parent.parent.key, path.pricetag.key,
                                                line.product.variant_signature, {
                                                    popFrom: helpers.clicks.realEventTarget($event.target),
                                                    events: {
                                                        addToCart: locals.updateLiveEntity
                                                    }
                                                });
                                        },
                                        remove: function (line) {
                                            line.quantity = 0;
                                            line._state = 'deleted';
                                        }
                                    };

                                    $scope.cmd.seller = {
                                        view: function () {
                                            $scope.sellerDetails.menu.open();
                                        }
                                    };

                                    $scope.sellerDetails = models['23'].makeSellerDetails($scope.seller);

                                    $scope.lineDrag = {
                                        options: {
                                            disabled: false,
                                            axis: 'x',
                                            handle: '.sort-handle',
                                            distance: 10,
                                            stop: function (e, ui) {
                                                $scope.$apply();
                                            }
                                        },
                                        whatSortMeans: function () {
                                            modals.alert('howToDeleteDragging');
                                        },
                                        onStart: function (e, ui, line) {
                                            $(ui.helper).find('.sort-handle').addClass('dragged');
                                        },
                                        onDrag: function (e, ui, line) {
                                            var deleteMode,
                                                division,
                                                helperWidth = ui.helper.width();
                                            division = ui.offset.left + helperWidth;
                                            if (division < (helperWidth / 2)) {
                                                deleteMode = true;
                                            }
                                            if (line) {
                                                if (deleteMode) {
                                                    ui.helper.addClass('about-to-delete');
                                                } else {
                                                    ui.helper.removeClass('about-to-delete');
                                                }
                                            }
                                        },
                                        onStop: function (e, ui, line) {
                                            if (ui.helper.hasClass('about-to-delete')) {
                                                ui.helper.animate({
                                                    left: (ui.helper.width() * 2) * -1
                                                }, function () {
                                                    $timeout(function () {
                                                        $scope.cmd.line.remove(line);
                                                        $scope.cmd.order.update().then(function () {
                                                            snackbar.showK('cartUpdated');
                                                        });
                                                    });
                                                });
                                            } else {
                                                ui.helper.animate(ui.originalPosition, function () {
                                                    ui.helper.attr('style', '');
                                                });
                                            }
                                        }
                                    };

                                    (function () {
                                        if ($scope.order.state === 'checkout' || $scope.order.state === 'canceled' || $scope.order.state === 'completed') {
                                            $scope.stage.out.extend([1, 2, 3]);
                                            $scope.stage.current = 4;
                                            $scope.stage.checkout = 1;
                                        }
                                    }());


                                    $scope.close = function () {
                                        $scope.$close().then(config.afterClose || angular.noop);
                                    };


                                    $scope.notifyUrl = $state.href('paypal-ipn', {}, {
                                        absolute: true
                                    });

                                    $scope.completePath = $state.href('order-payment-success', {
                                        key: $scope.order.key
                                    }, {
                                        absolute: true
                                    });

                                    $scope.cancelPath = $state.href('order-payment-canceled', {
                                        key: $scope.order.key
                                    }, {
                                        absolute: true
                                    });

                                    $scope.$on('$destroy', function () {
                                        $scope.messages.sync.stop();
                                    });

                                    openDefer.resolve($scope.order);

                                })
                            };

                            $.extend(modalOpen, config);

                            $modal.open(modalOpen);


                        });

                        return openPromise;

                    }
                });

            });


        }));
}());
(function () {
    'use strict';
    var notEmpty = function (val) {
        return angular.isString(val) || angular.isNumber(val);
    };
    angular.module('app').controller('SellerInfo', ng(function ($scope, $state, $stateParams, models) {
        $scope.site.toolbar.hidden = true;
        models['23'].viewProfileModal($stateParams.key, {
            inDirection: false,
            outDirection: false,
            afterClose: function () {
                $state.go('home');
            }
        });
    })).controller('SellerEmbedInfo', ng(function ($scope, $stateParams, models) {
        $scope.site.toolbar.hidden = true;
        models['23'].viewProfileModal($stateParams.key, {
            hideClose: true,
            inDirection: false,
            outDirection: false
        });
    })).directive('addressRuleLocationListView', function () {
        return {
            scope: {
                val: '=addressRuleLocationListView'
            },
            templateUrl: 'seller/address_rule_location_list_view.html',
            controller: ng(function ($scope) {
                $scope.notEmpty = notEmpty;
                $scope.postalCodes = function (postalCodes) {
                    return postalCodes.join(', ');
                };

            })
        };
    }).directive('defaultLineListView', function () {
        return {
            scope: {
                val: '=defaultLineListView'
            },
            templateUrl: 'seller/default_line_list_view.html'
        };
    }).directive('carrierLineRuleListView', function () {
        return {
            scope: {
                val: '=carrierLineRuleListView'
            },
            templateUrl: 'seller/carrier_line_rule_list_view.html',
            controller: ng(function ($scope) {
                $scope.notEmpty = notEmpty;

            })
        };
    }).controller('SellerManagementController', ng(function ($scope, endpoint, currentAccount, models) {

        $scope.settings = function () {
            models['23'].manageModal(currentAccount.key);
        };

    })).controller('SellCatalogsController', ng(function ($scope, modals, helpers, currentAccount, modelsEditor, modelsMeta, snackbar, models, modelsUtil, $rootScope) {

        $scope.setPageToolbarTitle('seller.catalogs');

        var newEntity = function (entity) {
            if (!entity.key) {
                return;
            }
            if (!_.findWhere($scope.search.results, {
                    key: entity.key
                })) {
                $scope.search.results.unshift(entity);
            }
        };

        $scope.create = function ($event) {
            models['31'].manageModal(undefined, newEntity, {
                popFrom: helpers.clicks.realEventTarget($event.target)
            });
        };

        $scope.preview = function (key, $event) {
            models['31'].previewModal(key, {
                popFrom: helpers.clicks.realEventTarget($event.target)
            });
        };

        $scope.manage = function (entity, $event) {
            models['31'].manageModal(entity, newEntity, {
                popFrom: helpers.clicks.realEventTarget($event.target)
            });
        };

        $scope.search = {
            results: [],
            pagination: {},
            loaded: false
        };

        $scope.scrollEnd = {
            loader: false
        };

        models['23'].current().then(function (response) {
            var sellerEntity = response.data.entity;
            $scope.search.pagination = models['31'].paginate({
                kind: '31',
                args: {
                    search: {
                        ancestor: sellerEntity.key
                    }
                },
                config: {
                    ignoreErrors: true
                },
                complete: function (response) {
                    var errors = response.data.errors;
                    if (!errors) {
                        $scope.search.results.extend(response.data.entities);
                    }
                    $scope.search.loaded = true;
                }
            });
            $scope.scrollEnd.loader = $scope.search.pagination;
            $scope.search.pagination.load();
        });

    })).controller('SellOrdersController', ng(function ($scope, modals, modelsEditor, snackbar, helpers, currentAccount, GLOBAL_CONFIG, modelsMeta, models, modelsUtil, $state) {

        var carts = $state.current.name === 'sell-carts';

        $scope.setPageToolbarTitle('seller.' + (carts ? 'carts' : 'orders'));

        $scope.listHelp = (carts ? GLOBAL_CONFIG.emptyHelp.cartSellerList : GLOBAL_CONFIG.emptyHelp.orderSellerList);


        $scope.search = {
            results: [],
            pagination: {},
            loaded: false
        };

        $scope.scrollEnd = {
            loader: false
        };

        $scope.view = function (order, $event) {
            models['34'].manageModal(order, order._seller, undefined, {
                sellerMode: carts,
                popFrom: helpers.clicks.realEventTarget($event.target)
            });
        };

        models['23'].current().then(function (response) {
            var sellerEntity = response.data.entity;
            $scope.search.pagination = models['34'].paginate({
                kind: '34',
                args: {
                    search: {
                        filters: [{
                            field: 'seller_reference',
                            operator: '==',
                            value: sellerEntity.key
                        }],
                        orders: [{
                            field: 'updated',
                            operator: 'desc'
                        }]
                    }
                },
                config: {
                    ignoreErrors: true
                },
                complete: function (response) {
                    var errors = response.data.errors;
                    if (!errors) {
                        $scope.search.results.extend(response.data.entities);
                    }

                    $scope.search.loaded = true;
                }
            });
            $scope.scrollEnd.loader = $scope.search.pagination;
            $scope.search.pagination.load();
        });
    })).run(ng(function (modelsConfig, modelsMeta,
        modelsEditor, formInputTypes, underscoreTemplate, $state, $stateParams, $modal, modals, social, helpers, $q, $timeout, currentAccount, $filter, dateFilter, GLOBAL_CONFIG, snackbar) {

        var pluginName = function (kind) {
            var find = GLOBAL_CONFIG.fields.translateChoices.rules.kind[kind];
            return angular.isDefined(find) ? find : kind;
        };

        modelsConfig(function (models) {
            formInputTypes.SuperPluginStorageProperty = function (info) {
                //info.config.repeated = true;
                //return this.SuperLocalStructuredProperty(info);
                var config = info.config,
                    kinds = config.kinds,
                    rootFormSetDirty = helpers.callable(info.scope.formSetDirty),
                    lineSpec = function () {
                        return {
                            listView: 'default-line-list-view',
                            listConfig: {
                                perLine: 2
                            }
                        };
                    },
                    exclusionSpec = function () {
                        return {
                            ui: {
                                specifics: {
                                    type: 'radio',
                                    trueLabel: GLOBAL_CONFIG.fields.radioLabel.pluginLocation.trueLabel,
                                    falseLabel: GLOBAL_CONFIG.fields.radioLabel.pluginLocation.falseLabel
                                }
                            }
                        };
                    },
                    groupBy = function (what, label, help) {
                        return {
                            ui: {
                                groupBy: what,
                                groupHelp: help,
                                groupLabel: label,
                                label: false
                            }
                        };
                    },
                    locationSpec = function () {
                        return {
                            listView: 'address-rule-location-list-view',
                            sortFields: ['country', 'region', 'postal_codes'],
                            listConfig: {
                                calculate: function (ent, i) {
                                    var lines = 0;
                                    angular.forEach(['country', 'region', 'postal_codes'], function (k) {
                                        var maybe = ent[k];
                                        if (maybe && maybe.length) {
                                            lines += 1;
                                        }
                                    });
                                    return lines === i;
                                }
                            },
                            beforeSave: function ($scope, info) {
                                var promises = [],
                                    updatedAddress = $scope.args,
                                    promise;

                                if (updatedAddress.region && (!updatedAddress._region || (updatedAddress.region !== updatedAddress._region.key))) {
                                    promise = models['13'].get(updatedAddress.region);
                                    promise.then(function (response) {
                                        if (response.data.entities.length) {
                                            updatedAddress._region = response.data.entities[0];
                                        }
                                    });
                                    promises.push(promise);
                                }

                                if (updatedAddress.country && ((!updatedAddress._country) || (updatedAddress.country !== updatedAddress._country.key))) {
                                    promise = models['12'].actions.search(undefined, {
                                        cache: true
                                    });
                                    promise.then(function (response) {
                                        if (response.data.entities.length) {
                                            var country = _.findWhere(response.data.entities, {
                                                key: updatedAddress.country
                                            });
                                            if (angular.isDefined(country)) {
                                                updatedAddress._country = country;
                                            }

                                        }

                                    });
                                    promises.push(promise);
                                }

                                if (promises.length) {
                                    return $q.all(promises);
                                }
                                return false;

                            }
                        };
                    },
                    defaultSpecifics = {
                        aboutPlugins: function () {
                            $modal.open({
                                templateUrl: 'core/models/manage.html',
                                controller: ng(function ($scope) {
                                    $scope.dialog = {
                                        templateBodyUrl: 'seller/help/plugins.html',
                                        toolbar: {
                                            hideSave: true,
                                            leftIcon: 'arrow_back',
                                            title: helpers.toolbar.title('seller.settings.aboutRules')
                                        }
                                    };
                                })
                            });
                        },
                        setupSortableOptions: function () {
                            return {
                                disabled: false,
                                start: function (e, ui) {
                                    info.scope.$broadcast('itemOrderStarted');
                                },
                                axis: false,
                                containment: false,
                                whatSortMeans: function () {
                                    modals.alert('howToSort');
                                },
                                handle: '.sort-handle',
                                tolerance: 'pointer',
                                helper: 'clone',
                                sort: function (e, ui) {
                                    var deleteMode,
                                        division,
                                        helperWidth = ui.helper.width(),
                                        itemScope = ui.item.scope(),
                                        item = itemScope.$eval(ui.item.attr('current-item'));
                                    division = ui.offset.left + helperWidth;
                                    if (division < (helperWidth / 2)) {
                                        deleteMode = true;
                                    }
                                    if (item) {
                                        if (deleteMode) {
                                            ui.helper.addClass('about-to-delete');
                                            item._state = 'deleted';
                                            info.scope.formSetDirty();
                                        } else {
                                            ui.helper.removeClass('about-to-delete');
                                            item._state = null;
                                        }
                                    }
                                    info.scope.$broadcast('itemOrderSorting');
                                },
                                stop: function (e, ui) {
                                    var dirty;
                                    angular.forEach(config.ui.specifics.parentArgs,
                                        function (ent, i) {
                                            i = ((config.ui.specifics.parentArgs.length - 1) - i);
                                            if (ent._sequence !== i || ent._state === 'deleted') {
                                                dirty = true;
                                            }
                                            ent._sequence = i;
                                            if (ent.ui) {
                                                ent.ui.access[ent.ui.access.length - 1] = i;
                                            }
                                        });
                                    if (dirty) {
                                        info.scope.formSetDirty();
                                    }
                                    info.scope.$broadcast('itemOrderChanged');
                                    info.scope.$apply();
                                }
                            };
                        },
                        pluginFieldOverrides: {
                            '113': {
                                lines: {
                                    ui: {
                                        specifics: lineSpec()
                                    },
                                    modelclass: {
                                        prices: {
                                            ui: {
                                                specifics: {
                                                    toolbar: {
                                                        titleEdit: 'editPrice',
                                                        titleAdd: 'addPrice'
                                                    },
                                                    listView: 'carrier-line-rule-list-view',
                                                    listConfig: {
                                                        perLine: 2
                                                    }
                                                }
                                            },
                                            modelclass: {
                                                condition_type: groupBy('conditional', GLOBAL_CONFIG.fields.label['111-update'].condition_type, GLOBAL_CONFIG.fields.help['111-update'].condition_type),
                                                condition_operator: groupBy('conditional'),
                                                condition_value: groupBy('conditional'),
                                                price_type: groupBy('price', GLOBAL_CONFIG.fields.label['111-update'].price_type, GLOBAL_CONFIG.fields.help['111-update'].price_type),
                                                price_operator: helpers.extendDeep(groupBy('price'), {
                                                    ui: {
                                                        active: 'args.price_type !== \'fixed\''
                                                    }
                                                }),
                                                price_value: groupBy('price')
                                            }
                                        },
                                        exclusion: exclusionSpec(),
                                        locations: {
                                            ui: {
                                                specifics: locationSpec()
                                            }
                                        }
                                    }
                                }
                            },
                            '107': {
                                exclusion: exclusionSpec(),
                                locations: {
                                    ui: {
                                        specifics: locationSpec()
                                    }
                                }
                            },
                            '126': {
                                lines: {
                                    ui: {
                                        specifics: lineSpec()
                                    },
                                    modelclass: {
                                        product_categories: {
                                            ui: {
                                                specifics: {
                                                    search: {
                                                        enabled: true
                                                    }
                                                }
                                            }
                                        },
                                        condition_type: groupBy('conditional', GLOBAL_CONFIG.fields.label['124-update'].condition_type, GLOBAL_CONFIG.fields.help['124-update'].condition_type),
                                        condition_operator: groupBy('conditional'),
                                        condition_value: groupBy('conditional')
                                    }
                                }
                            },
                            '109': {
                                product_categories: {
                                    ui: {
                                        specifics: {
                                            search: {
                                                enabled: true
                                            }
                                        }
                                    }
                                },
                                carriers: {
                                    ui: {
                                        specifics: {
                                            checkboxes: true,
                                            entities: function () {
                                                if (!config.ui.specifics.parentArgs) {
                                                    return [];
                                                }
                                                return $.map(config.ui.specifics.parentArgs,
                                                    function (item) {
                                                        if (item.active && item.kind === '113') {
                                                            return {
                                                                key: item.key,
                                                                name: item.name
                                                            };

                                                        }

                                                    });
                                            }
                                        }
                                    }
                                },
                                exclusion: exclusionSpec(),
                                locations: {
                                    ui: {
                                        specifics: locationSpec()
                                    }
                                }
                            }
                        },
                        showType: pluginName,
                        kind: undefined,
                        selectKinds: {
                            type: 'SuperStringProperty',
                            _maker_: 'rules',
                            choices: kinds,
                            required: true,
                            ui: {
                                args: 'info.kind',
                                label: GLOBAL_CONFIG.fields.label.plugins.kind,
                                attrs: {
                                    'ng-change': 'setNewArg()'
                                },
                                writable: true,
                            },
                            code_name: 'kind'
                        },
                        remove: function (arg) {
                            arg._state = 'deleted';
                            info.scope.$emit('itemDelete', arg);
                            info.scope.$broadcast('itemDelete', arg);
                            rootFormSetDirty();
                        },
                        create: function () {
                            return this.manage();
                        },
                        manage: function (arg) {

                            if (!angular.isDefined(config.ui.specifics.templateUrl)) {
                                config.ui.specifics.templateUrl = 'core/fields/manage_structured.html';
                            }

                            $modal.open({
                                template: underscoreTemplate.get(config.ui.specifics.templateUrl)({
                                    config: config
                                }),
                                controller: ng(function ($scope, modelsUtil) {
                                    var getTitle,
                                        resetFormBuilder = function () {
                                            $scope.layouts = {
                                                groups: [{
                                                    label: false
                                                }]
                                            };
                                            $scope.formBuilder = {
                                                '0': [config.ui.specifics.selectKinds]
                                            };
                                        },
                                        getPluginFieldOverrides = function (kind_id, field) {
                                            var gets = defaultSpecifics.pluginFieldOverrides[kind_id];
                                            if (angular.isDefined(gets) && angular.isDefined(gets[field])) {
                                                return angular.copy(gets[field]);
                                            }
                                            return {};
                                        };
                                    config.ui.specifics.toolbar = {
                                        leftIcon: 'arrow_back',
                                        hideSave: true
                                    };
                                    if (angular.isUndefined(config.ui.specifics.toolbar.titleAdd)) {
                                        config.ui.specifics.toolbar.titleAdd = 'add' + helpers.toolbar.makeTitle(config.code_name);
                                    }
                                    if (angular.isUndefined(config.ui.specifics.toolbar.titleEdit)) {
                                        config.ui.specifics.toolbar.titleEdit = 'edit' + helpers.toolbar.makeTitle(config.code_name);
                                    }
                                    getTitle = function () {
                                        return config.ui.specifics.toolbar['title' + ($scope.isNew ? 'Add' : 'Edit')];
                                    };
                                    config._title_.push(getTitle);
                                    $scope.isNew = false;
                                    if (!arg) {
                                        arg = {};
                                        $scope.isNew = true;
                                    } else {
                                        modelsUtil.normalize(arg, undefined, config.ui.specifics.entity, config.code_name,
                                            config.ui.specifics.parentArgs.length);
                                    }
                                    $scope.info = {
                                        build: true
                                    };
                                    $scope.config = config;
                                    $scope.setNewArg = function () {
                                        if ($scope.info.kind !== 0 && $scope.args.kind !== $scope.info.kind) {
                                            arg = {
                                                kind: $scope.info.kind
                                            };
                                            modelsUtil.normalize(arg, undefined, config.ui.specifics.entity, config.code_name,
                                                config.ui.specifics.parentArgs.length, false);
                                            $scope.isNew = true;

                                            $scope.args = arg;
                                            $scope.getFormBuilder();
                                            $scope.info.build = false;

                                            $timeout(function () {
                                                $scope.info.build = true;
                                                $scope.$apply();
                                            }, 100);

                                        }
                                    };

                                    resetFormBuilder();

                                    $scope.getFormBuilder = function () {
                                        resetFormBuilder();
                                        var kind = $scope.info.kind,
                                            fields = modelsMeta.getFields(kind),
                                            realTotal = 0,
                                            found = false;
                                        fields = _.toArray(fields);
                                        fields.sort(helpers.fields.sorter);
                                        config.ui.specifics.fields = fields;
                                        angular.forEach(fields, function (field) {
                                            helpers.fields.applyGlobalConfig(field);
                                            field._title_ = config._title_.concat();
                                            field.ui.name = 'plugin.' + field.code_name;
                                            field.ui.writable = true;
                                            var extra = getPluginFieldOverrides(kind, field.code_name),
                                                next;
                                            if (extra) {
                                                helpers.extendDeep(field, extra);
                                            }
                                            if (helpers.fields.isFieldset(field) && formInputTypes[field.type]) {
                                                $scope.layouts.groups.push({
                                                    label: field.ui.label || $filter('humanized')(field.code_name),
                                                    disabled: false,
                                                    open: false
                                                });

                                                field.ui.label = false;
                                                next = $scope.layouts.groups.length - 1;

                                                if (!angular.isDefined($scope.formBuilder[next])) {
                                                    $scope.formBuilder[next] = [];
                                                    $scope.formBuilder[next].push(field);
                                                }
                                                $scope.layouts.groups[0].disabled = false;
                                            } else {
                                                $scope.formBuilder['0'].push(field);
                                            }
                                        });

                                        angular.forEach($scope.layouts.groups, function (group, i) {
                                            if ($scope.formBuilder[i].length) {
                                                realTotal += 1;
                                            }
                                            if (found !== false) {
                                                return;
                                            }
                                            if ($scope.formBuilder[i].length) {
                                                group.open = true;
                                                found = group;
                                            } else {
                                                group.open = false;
                                            }
                                        });

                                        if (realTotal === 1) {
                                            found.disabled = true;
                                        }

                                    };

                                    $scope.container = {};
                                    $scope.args = angular.copy(arg);
                                    // entity.addreses.0.address
                                    $scope.parentArgs = config.ui.specifics.parentArgs;
                                    // entity.addresses
                                    $scope.entity = config.ui.specifics.entity;
                                    $scope.rootFormSetDirty = rootFormSetDirty;
                                    $scope.formSetDirty = angular.bind($scope, helpers.form.setDirty);
                                    $scope.formSetPristine = angular.bind($scope, helpers.form.setPristine);
                                    $scope.validateForm = angular.bind($scope, helpers.form.validate);


                                    if ($scope.args && $scope.args.kind) {
                                        $scope.info.kind = $scope.args.kind;
                                        $scope.getFormBuilder();

                                    }
                                    $scope.close = function () {
                                        if (!$scope.container.form.$dirty) {
                                            return $scope.$close();
                                        }
                                        var save = $scope.save();
                                        if (save) {
                                            save.then(function () {
                                                $scope._close_ = undefined;
                                                $scope.$close();
                                            });
                                        } else {
                                            modals.confirm('discardWithFieldsRequired', $scope.$close);
                                        }
                                    };

                                    $scope._close_ = $scope.close;

                                    $scope.save = function () {
                                        var promise,
                                            complete,
                                            saveCompleteDefer = $q.defer(),
                                            saveCompletePromise = saveCompleteDefer.promise;
                                        if (!$scope.validateForm() || !$scope.info.kind) {
                                            return;
                                        }

                                        if (angular.isFunction(config.ui.specifics.beforeSave)) {
                                            promise = config.ui.specifics.beforeSave($scope, info);
                                        }

                                        complete = function () {
                                            var newPromise = null,
                                                total = 0;
                                            if ($scope.isNew) {
                                                $scope.parentArgs.unshift($scope.args);
                                                $scope.isNew = false;
                                                total = $scope.parentArgs.length;
                                                angular.forEach($scope.parentArgs, function (item, i) {
                                                    i = total - i;
                                                    item._sequence = i;
                                                });
                                            } else {
                                                $.extend(arg, $scope.args);
                                            }

                                            if (angular.isFunction(config.ui.specifics.afterSave)) {
                                                newPromise = config.ui.specifics.afterSave($scope, info);
                                            }

                                            if (newPromise && newPromise.then) {
                                                newPromise.then(function () {
                                                    saveCompleteDefer.resolve();
                                                });
                                            } else {
                                                saveCompleteDefer.resolve();
                                            }

                                        };

                                        if ($scope.container.form.$dirty) {
                                            rootFormSetDirty();
                                        }
                                        if (promise && promise.then) {
                                            promise.then(complete);

                                        } else {
                                            complete();

                                        }

                                        $scope.isNew = false;

                                        return saveCompletePromise;

                                    };
                                    $scope.$on('$destroy', function () {
                                        config._title_.remove(getTitle);
                                        config.ui.specifics.getScope = undefined;
                                    });

                                    $scope.$watch('isNew', function () {
                                        config.ui.specifics.toolbar.title = helpers.toolbar.buildTitle(config._title_);
                                    });

                                })
                            });
                        }
                    };

                config.ui.specifics.parentArgs = info.scope.$eval(config.ui.args);
                config.ui.specifics.entity = info.scope.$eval(config.ui.model);

                info.scope.$watch(config.ui.args, function (neww, old) {
                    if (neww !== old) {
                        config.ui.specifics.parentArgs = neww;
                    }
                });

                angular.forEach(defaultSpecifics, function (v, k) {
                    if (config.ui.specifics[k] === undefined) {
                        config.ui.specifics[k] = v;
                    }
                });

                if (config.ui.specifics.setupSortableOptions) {
                    config.ui.specifics.sortableOptions = config.ui.specifics.setupSortableOptions();
                }

                return 'plugins';
            };
        });


        modelsConfig(function (models) {
            var read_arguments = {
                    _content: {
                        documents: {}
                    },
                    _plugin_group: {}
                },
                globalSellerStack = {};

            $.extend(models['23'], {
                decrementGlobalSellerStack: function (key, notified) {
                    var gss = globalSellerStack[key];
                    if (gss) {
                        gss.follower_count -= 1;
                        gss.inCollection = false;
                        if (notified) {
                            gss.notified_followers_count -= 1;
                        }
                    }
                },
                makeSellerDetails: function (seller, config) {
                    config = helpers.alwaysObject(config);
                    var removedOrAdded = config.removedOrAdded;
                    return (function ($scope) {
                        var chartData,
                            sellerUrl = $state.href('seller-info', {
                                key: seller.parent.key
                            }, {
                                absolute: true
                            }),
                            embedSellerUrl = $state.href('embed-seller-info', {
                                key: seller.parent.key
                            }, {
                                absolute: true
                            }),
                            sellerLogo = seller.logo.serving_url;
                        $scope.seller = seller;
                        if (!globalSellerStack[seller.key]) {
                            globalSellerStack[seller.key] = {
                                follower_count: seller._follower_count,
                                notified_followers_count: seller._notified_followers_count
                            };
                        }
                        $scope.globalSellerStack = globalSellerStack[seller.key];
                        $scope.menu = {};
                        $scope.globalSellerStack.inCollection = false;
                        if (!currentAccount._is_guest) {
                            $scope.loadedCollection = models['18'].current().then(function (response) {
                                var collection = response.data.entity;
                                if ($.inArray($scope.seller.key, collection.sellers) !== -1) {
                                    $scope.globalSellerStack.inCollection = true;
                                }
                                return collection;
                            });
                        }

                        helpers.sideNav.setup($scope.menu, 'right_seller_details');

                        chartData = [];

                        if ($scope.seller._feedback) {

                            angular.forEach($scope.seller._feedback.feedbacks, function (feedback) {
                                feedback.positive_count = _.random(0, 100);
                                feedback.negative_count = _.random(0, 100);
                                feedback.neutral_count = _.random(0, 100);
                                chartData.push({
                                    c: [{
                                        v: dateFilter(feedback.date, 'MMM')
                                    }, {
                                        v: feedback.positive_count
                                    }, {
                                        v: feedback.negative_count
                                    }, {
                                        v: feedback.neutral_count
                                    }]
                                });

                            });

                            $scope.chartConfig = {
                                type: "ColumnChart",
                                data: {
                                    cols: [{
                                        id: "months",
                                        label: "Months",
                                        type: "string"
                                    }, {
                                        id: "positive",
                                        label: "Positive",
                                        type: "number"
                                    }, {
                                        id: "negative",
                                        label: "Negative",
                                        type: "number"
                                    }, {
                                        id: "neutral",
                                        label: "Neutral",
                                        type: "number"
                                    }],
                                    rows: chartData
                                },
                                options: {
                                    colors: ['green', 'red', 'gray'],
                                    series: {
                                        0: {
                                            axis: 'positive'
                                        },
                                        1: {
                                            axis: 'negative'
                                        },
                                        3: {
                                            axis: 'neutral'
                                        }
                                    },
                                    axes: {
                                        y: {
                                            positive: {
                                                label: 'Positive'
                                            },
                                            negative: {
                                                label: 'Negative',
                                                side: 'right'
                                            },
                                            neutral: {
                                                label: 'Neutral',
                                                side: 'right'
                                            }
                                        }
                                    }
                                }
                            };

                            $scope.socialMeta = {
                                facebook: {
                                    'p[url]': sellerUrl,
                                    'p[images][0]': sellerLogo,
                                    'p[title]': $scope.seller.name
                                },
                                twitter: {
                                    url: sellerUrl,
                                    text: $scope.seller.name
                                },
                                pinterest: {
                                    url: sellerUrl,
                                    media: sellerLogo,
                                    description: $scope.seller.name
                                },
                                googleplus: {
                                    url: sellerUrl
                                },
                                reddit: {
                                    url: sellerUrl,
                                    title: $scope.seller.name
                                },
                                linkedin: {
                                    url: sellerUrl,
                                    title: $scope.seller.name
                                },
                                tumblr: {
                                    url: sellerUrl,
                                    name: $scope.seller.name
                                }
                            };

                            $scope.displayShare = function () {
                                return social.share($scope.socialMeta, {
                                    src: embedSellerUrl
                                });
                            };


                            $scope.feedbackStats = (function () {
                                var positive_count = 0,
                                    neutral_count = 0,
                                    negative_count = 0,
                                    positive_average,
                                    negative_average,
                                    neutral_average,
                                    score,
                                    values = [];

                                positive_average = parseFloat((positive_count / (positive_count + negative_count)) * 100).toFixed(1);
                                negative_average = parseFloat((negative_count / (negative_count + positive_count)) * 100).toFixed(1);
                                neutral_average = parseFloat((neutral_count / (neutral_count + negative_count + positive_count)) * 100).toFixed(1);

                                if ((positive_count - negative_count) > 0) {
                                    score = positive_count - negative_count;
                                } else {
                                    score = 0;
                                }
                                values[0] = isNaN(positive_count) ? 0 : positive_count;
                                values[1] = isNaN(neutral_count) ? 0 : neutral_count;
                                values[2] = isNaN(negative_count) ? 0 : negative_count;
                                values[3] = isNaN(positive_average) ? 0 : positive_average;
                                values[4] = isNaN(negative_average) ? 0 : negative_average;
                                values[5] = isNaN(neutral_average) ? 0 : neutral_average;
                                values[6] = score;
                                return values;
                            }());

                        }


                        $scope.viewContent = function (content) {
                            $modal.open({
                                templateUrl: 'core/misc/content_view.html',
                                controller: ng(function ($scope) {
                                    $scope.plainText = true;
                                    $scope.content = content;
                                })
                            });
                        };

                        $scope.toggleCollection = function () {
                            if (currentAccount._is_guest) {
                                models['11'].login($state.href('home')); // must redirect to actual follow button >_>
                                return;
                            }
                            $scope.loadedCollection.then(function (collection) {
                                var loadedCollection = collection,
                                    removed = false;
                                if (!$scope.globalSellerStack.inCollection) {
                                    removed = true;
                                    loadedCollection.sellers.remove($scope.seller.key);
                                } else {
                                    loadedCollection.sellers.unshift($scope.seller.key);
                                }
                                models['18'].actions.update({
                                    account: currentAccount.key,
                                    sellers: loadedCollection.sellers,
                                    notify: loadedCollection.notify
                                }).then(function (newResponse) {
                                    var updatedCollection = newResponse.data.entity;
                                    if (removed) {
                                        $scope.globalSellerStack.follower_count -= 1;
                                    } else {
                                        $scope.globalSellerStack.follower_count += 1;
                                    }
                                    // update cache
                                    $.extend(loadedCollection, updatedCollection);
                                    if (angular.isFunction(removedOrAdded)) {
                                        removedOrAdded(updatedCollection, $scope.globalSellerStack.inCollection);
                                    }
                                });
                            });
                        };

                        return $scope;
                    }({}));
                },
                current: function (args) {
                    if (!args) {
                        args = {};
                    }
                    args.account = currentAccount.key;
                    return this.actions.read(args, {
                        cache: 'currentSeller',
                        cacheType: 'memory'
                    });
                },
                viewProfileModal: function (accountKey, config) {
                    config = helpers.alwaysObject(config);
                    $modal.open({
                        templateUrl: 'seller/profile.html',
                        popFrom: config.popFrom,
                        inDirection: config.inDirection,
                        outDirection: config.outDirection,
                        noEscape: config.noEscape,
                        resolve: {
                            seller: function () {
                                return models['23'].actions.read({
                                    account: accountKey,
                                    read_arguments: {
                                        _feedback: {},
                                        _content: {}
                                    }
                                }).then(function (response) {
                                    return response.data.entity;
                                });
                            }
                        },
                        controller: ng(function ($scope, seller) {
                            $scope.view = function (key, $event) {
                                models['31'].viewModal(key, {
                                    popFrom: helpers.clicks.realEventTarget($event.target)
                                });
                            };
                            $scope.hideClose = config.hideClose;
                            $scope.seller = seller;
                            $scope.sellerDetails = models['23'].makeSellerDetails($scope.seller, config.sellerDetails);
                            $scope.search = {
                                results: [],
                                pagination: models['31'].paginate({
                                    kind: '31',
                                    args: {
                                        search: {
                                            filters: [{
                                                field: 'seller_account_key',
                                                operator: 'IN',
                                                value: accountKey
                                            }]
                                        }
                                    },
                                    config: {
                                        normalizeEntity: false
                                    },
                                    action: 'public_search',
                                    complete: function (response) {
                                        var results = response.data.entities;
                                        models['31'].formatPublicSearchResults(results);
                                        $scope.search.results.extend(results);
                                    }
                                })
                            };
                            $scope.scrollEnd = {
                                loader: $scope.search.pagination
                            };
                            $scope.search.pagination.load();
                            $scope.close = function () {
                                $scope.$close().then(config.afterClose || angular.noop);
                            };

                        })
                    });
                },
                manageModal: function (accountKey) {
                    var fields = modelsMeta.getActionArguments(this.kind, 'update'),
                        config;
                    fields._content.ui.label = false;
                    $.extend(fields._content.modelclass.documents.ui, {
                        label: false,
                        specifics: {
                            listView: 'content-list-view',
                            listConfig: {
                                perLine: 1
                            }
                        }
                    });
                    $.extend(fields._plugin_group.modelclass.plugins.ui, {
                        label: false
                    });

                    fields.logo.ui.specifics = {
                        displayImageConfig: {
                            size: 240,
                            defaultImage: 'defaultLogo'
                        }
                    };
                    fields._plugin_group.ui.label = false;
                    config = {
                        kind: this.kind,
                        action: 'update',
                        fields: _.toArray(fields),
                        toolbar: {
                            submitNative: true,
                            titleEdit: 'seller.settings'
                        },
                        modalConfig: {
                            inDirection: false,
                            outDirection: false
                        },
                        excludeFields: ['account', 'read_arguments'],
                        argumentLoader: function ($scope) {
                            var args = this.defaultArgumentLoader($scope);
                            args.account = accountKey;
                            if (args._content === null) {
                                args._content = {
                                    kind: '21',
                                    documents: []
                                };
                            }
                            args.read_arguments = read_arguments;
                            return args;
                        },
                        scope: {
                            layouts: {
                                groups: [{
                                    label: false,
                                    fields: ['name', 'logo'],
                                }, {
                                    label: GLOBAL_CONFIG.subheaders.sellerContents,
                                    fields: ['_content']
                                }, {
                                    label: GLOBAL_CONFIG.subheaders.sellerPlugins,
                                    fields: ['_plugin_group'],
                                }]
                            }
                        }
                    };

                    modelsEditor.create(config).read({}, {
                        account: accountKey,
                        read_arguments: read_arguments
                    });

                }
            });

        });

    }));

}());
(function () {
    'use strict';
    angular.module('app')
        .controller('AdminListController', ng(function ($scope, models, $stateParams, GLOBAL_CONFIG, searchBuilder, $state, helpers) {

            var kind = $stateParams.kind,
                query = null,
                args = {},
                getMaybeTemplate = GLOBAL_CONFIG.admin.listViewDirective[kind];

            try {
                query = helpers.url.jsonFromUrlsafe($stateParams.query);
                args = query;
            } catch (ignore) {}

            $scope.config = {
                titles: GLOBAL_CONFIG.admin.listTitles,
                kind: kind
            };

            $scope.maybeTemplate = (getMaybeTemplate === true ? 'admin/list_view/' + kind + '.html' : getMaybeTemplate);

            $scope.setPageToolbarTitle('admin.' + $scope.config.titles[kind]);

            $scope.manage = function (entity, $event) {
                models[kind].adminManageModal(entity, {
                    popFrom: helpers.clicks.realEventTarget($event.target)
                });
            };
            $scope.search = searchBuilder.create();
            $.extend($scope.search, {
                doSearch: function () {
                    $state.go('admin-list', {
                        kind: this.kind,
                        query: helpers.url.jsonToUrlsafe({
                            search : this.send
                        })
                    });
                },
                results: [],
                pagination: models[kind].paginate({
                    args: args,
                    kind: kind,
                    complete: function (response) {
                        $scope.search.results.extend(response.data.entities);
                    }
                })
            });

            $scope.search.kind = kind;
            if (!query) {
                query = $scope.search.pagination.args;
            }
            $scope.search.changeKindUI();
            if (query) {
                $scope.search.setSearch(kind, query.search);
            }
            $scope.scrollEnd = {loader: $scope.search.pagination};
            $scope.search.pagination.load();


        }));
}());(function () {
    'use strict';
    angular.module('app').config(ng(function ($stateProvider, GLOBAL_CONFIG) {

        $stateProvider
            .state('home', {
                url: '/',
                templateUrl: 'home/index.html',
                controller: 'HomePageController'
            })
            .state('following', {
                url: '/following',
                templateUrl: 'home/index.html',
                controller: 'HomePageController'
            })
            .state('seller-info', {
                url: '/seller/:key',
                controller: 'SellerInfo',
                template: ''
            })
            .state('embed-seller-info', {
                url: '/embed/seller/:key',
                controller: 'SellerEmbedInfo',
                template: ''
            })
            .state('catalog-view', {
                url: '/catalog/:key',
                controller: 'CatalogViewController',
                template: ''
            })
            .state('catalog-product-add-to-cart', {
                url: '/catalog/:key/product-add-to-cart/:image_id/:pricetag_id/:variant/:quantity',
                controller: 'CatalogProductAddToCartController',
                template: ''
            })
            .state('embed-catalog-product-add-to-cart', {
                url: '/embed/catalog/:key/product-add-to-cart/:image_id/:pricetag_id/:variant/:quantity',
                controller: 'CatalogProductAddToCartController',
                template: ''
            })
            .state('catalog-order-view', {
                url: '/catalog/:key/order/view',
                controller: 'CatalogOrderViewController',
                template: ''
            })
            .state('embed-catalog-order-view', {
                url: '/embed/catalog/:key/order/view',
                controller: 'CatalogOrderViewController',
                template: ''
            })
            .state('catalog-product-view', {
                url: '/catalog/:key/product/:image_id/:pricetag_id',
                controller: 'CatalogProductViewController',
                template: ''
            })
            .state('embed-catalog-view', {
                url: '/embed/catalog/:key',
                controller: 'EmbedCatalogViewController',
                template: ''
            })
            .state('embed-seller-view', {
                url: '/embed/seller/:key',
                controller: 'EmbedSellerViewController',
                template: ''
            })
            .state('embed-catalog-product-view', {
                url: '/embed/catalog/:key/product/:image_id/:pricetag_id',
                controller: 'EmbedCatalogProductViewController',
                template: ''
            })
            .state('sell-catalogs', {
                url: '/sell/catalogs',
                controller: 'SellCatalogsController',
                templateUrl: 'catalog/list.html'
            })
            .state('sell-orders', {
                url: '/sell/orders',
                controller: 'SellOrdersController',
                templateUrl: 'order/list.html'
            })
            .state('sell-carts', {
                url: '/sell/carts',
                controller: 'SellOrdersController',
                templateUrl: 'order/list.html'
            })
            .state('buy-orders', {
                url: '/buy/orders',
                controller: 'BuyOrdersController',
                templateUrl: 'order/list.html'
            })
            .state('buy-carts', {
                url: '/buy/carts',
                controller: 'BuyOrdersController',
                templateUrl: 'buyer/carts.html'
            })
            .state('login', {
                url: '/api/account/login/:provider',
                template: ''
            })
            .state('loginProviderConnected', {
                url: '/login_provider_connected/:provider',
                controller: 'LoginProviderConnectedController',
                template: ''
            })
            .state('order-payment-canceled', {
                url: '/order/payment/canceled/:key',
                controller: 'BuyOrdersController',
                templateUrl: 'buyer/carts.html'
            })
            .state('order-payment-success', {
                url: '/order/payment/success/:key',
                controller: 'BuyOrdersController',
                templateUrl: 'buyer/carts.html'
            })
            .state('order-view', {
                url: '/order/:key',
                controller: 'OrderViewController',
                template: ''
            })
            .state('login-status', {
                url: '/login/status',
                template: '',
                controller: 'AccountLoginStatusController'
            })
            .state('paypal-ipn', {
                url: '/api/order/complete/paypal',
                template: '',
            })
            .state('about', {
                url: '/about',
                controller: 'AboutController',
                templateUrl: 'home/about.html',
            })
            .state('tos', {
                url: '/tos',
                title: 'tos',
                templateUrl: 'home/tos.html',
            })
            .state('acceptable_use_policy', {
                url: '/acceptable_use_policy',
                title: 'acceptable_use_policy',
                templateUrl: 'home/acceptable_use_policy.html',
            })
            .state('privacy_policy', {
                url: '/privacy_policy',
                title: 'privacy_policy',
                templateUrl: 'home/privacy_policy.html',
            })
            .state('copyright_policy', {
                url: '/copyright_policy',
                title: 'copyright_policy',
                templateUrl: 'home/copyright_policy.html',
            })
            .state('admin-list', {
                url: '/admin/list/:kind/:query',
                templateUrl: function ($stateParams) {

                    var defaults = 'admin/list.html',
                        config;

                    if ($stateParams.kind !== undefined) {
                        config = GLOBAL_CONFIG.admin.listTemplates[$stateParams.kind];
                        if (config && config.templateUrl) {
                            defaults = config.templateUrl;
                        }
                    }

                    return defaults;
                },
                controller: 'AdminListController'
            });

    })).run(ng(function ($rootScope, modelsInfo, $state, endpoint, models, currentAccount, GLOBAL_CONFIG, modelsUtil) {
        $rootScope.$on('$stateChangeSuccess',
            function (event, toState, toParams, fromState, fromParams) {
                if (toState.title) {
                    $rootScope.setPageToolbarTitle(toState.title);
                }
                if (window.ga) {
                    window.ga('send', 'pageview', $state.href(toState, toParams));
                }
            });
        $.extend(modelsInfo, window.MODELS_META);
        $.extend(currentAccount, window.CURRENT_ACCOUNT);
        modelsUtil.normalize(currentAccount);
        models.init();
        if (!GLOBAL_CONFIG.debug) {
            delete window.MODELS_META;
            delete window.CURRENT_ACCOUNT;
        }
    }));
}());