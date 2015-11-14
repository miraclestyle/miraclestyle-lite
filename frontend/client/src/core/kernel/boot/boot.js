if (!window.ng) {
    window.ng = function (fn) {
        return fn;
    };
}

window.isChromeApp = window.chrome && chrome.app && chrome.app.runtime;
window._chromeLocalStorage = null;
window.getLocalStorage = function () {
    if (!window.isChromeApp) {
        return window.localStorage;
    }
    if (window.isChromeApp) {
        if (!window._chromeLocalStorage) {
            window._chromeLocalStorage = {
                _data       : {},
                setItem     : function(id, val) { return this._data[id] = String(val); },
                getItem     : function(id) { return this._data.hasOwnProperty(id) ? this._data[id] : undefined; },
                removeItem  : function(id) { return delete this._data[id]; },
                clear       : function() { return this._data = {}; }
            };
        }
        return window._chromeLocalStorage;
    }
};

function Steady(opts) {
    if (!opts) throw new Error('missing options');
    if (!opts.handler) throw new Error('missing handler parameter');


    this.scrollElement = opts.scrollElement || window;
    this.conditions = opts.conditions || {};
    this.handler = opts.handler;
    this.values = {};
    this.tracked = {};
    this.success = false;
    this.throttleVal = opts.throttle || 100;
    this.processing = false;
    this.stopped = false;


    this._parse();

    if ('pageYOffset' in this.scrollElement) {
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


Steady.prototype.addCondition = function (name, value) {
    this.conditions[name] = value;
    this._parse();
};
Steady.prototype.removeCondition = function (name) {
    delete this.conditions[name];
    this._parse();
};
Steady.prototype.addTracker = function (name, fn) {
    this.tracked[name] = {
        cb: fn,
        name: name
    };
};

Steady.prototype._addBottom = function () {
    this.addTracker('bottom', function (scrollable) {
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

Steady.prototype._addTop = function () {
    this.addTracker('top', function (scrollable) {
        return scrollable.pageYOffset;
    });
};

Steady.prototype._addBottomEl = function () {
    var self = this;
    this.addTracker('bottom', function (scrollable) {
        var height = Math.max(
            scrollable.scrollHeight,
            scrollable.offsetHeight
        );
        return height - (scrollable.scrollTop + scrollable.offsetHeight);
    });
};

Steady.prototype._addTopEl = function () {
    this.addTracker('top', function (scrollable) {
        return scrollable.scrollTop;
    });
};

Steady.prototype._addScrollLeft = function () {
    var self = this;
    this.addTracker('scrollLeft', function (scrollable) {
        return scrollable.scrollLeft;
    });
};

Steady.prototype._addWidth = function () {
    this.addTracker('width', function (scrollable) {
        return scrollable.innerWidth;
    });
};


Steady.prototype._parse = function () {
    this._parsed = {};
    this._wantedTrackers = [];
    this._parsedMax = {};
    this._parsedMin = {};

    for (var condition in this.conditions) {
        if (!this.conditions.hasOwnProperty(condition)) continue;

        var operator = condition.substr(0, 4);

        switch (operator) {
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

Steady.prototype._check = function () {
    var results = [];

    for (var name in this.values) {
        if (this._parsed.hasOwnProperty(name)) {
            results.push(this._parsed[name] == this.values[name]);
        }
        if (this._parsedMin.hasOwnProperty(name)) {
            results.push(this._parsedMin[name] <= this.values[name]);
        }

        if (this._parsedMax.hasOwnProperty(name)) {
            results.push(this._parsedMax[name] >= this.values[name]);
        }
    }

    if (results.length && results.indexOf(false) == -1) {
        this.processing = true;

        var cb = this._done.bind(this);
        window.requestAnimationFrame(this.handler.bind(this, this.values, cb));
    }
};

Steady.prototype._done = function () {
    this.processing = false;
};

Steady.prototype._onScroll = function () {
    this._onScrollHandler = this._throttledHandler();
    this.scrollElement.addEventListener('scroll', this._onScrollHandler, false);
};

Steady.prototype._throttledHandler = function () {
    var self = this;
    return this.throttle(function (e) {

        if (!self._wantedTrackers.length || self.processing) return;

        for (var i = 0; i < self._wantedTrackers.length; i++) {

            if (!self.tracked[self._wantedTrackers[i]]) continue;

            self.values[self._wantedTrackers[i]] = self.tracked[self._wantedTrackers[i]].cb(self.scrollElement || window);
        }

        window.requestAnimationFrame(self._check.bind(self));
    }, this.throttleVal);
};

Steady.prototype.stop = function () {
    if (!this.stopped) {
        this.scrollElement.removeEventListener('scroll', this._onScrollHandler, false);
        this.stopped = true;
    }
};

Steady.prototype.resume = function () {
    if (this.stopped)
        this._onScroll();
    this.stopped = false;
};


// i use it to avoid calling the onscroll function many times.
Steady.prototype.throttle = function (fn, delay) {
    var timer;
    var isFirstTime = true;
    return function () {
        var context = this;
        var args = arguments;

        if (isFirstTime) {
            fn.apply(context, args);
            isFirstTime = false;
            return;
        }

        if (timer) return;

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
    Array.prototype.indexOf = function (searchElement, fromIndex) {

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

        for (var i = 0, l = this.length; i < l; i++) {
            // Check if we have nested arrays
            if (this[i] instanceof Array && array[i] instanceof Array) {
                // recurse into the nested arrays
                if (!this[i].equals(array[i])) {
                    return false;
                }
            } else if (this[i] !== array[i]) {
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

    var host = (window.isChromeApp ? 'https://x-arcanum-801.appspot.com' : window.location.protocol + '//' + window.location.host),
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
                'material.components.toolbar'
            ], // this will be changed accordingly
            api: {
                endpoint: {
                    path: host + '/api/endpoint'
                },
                modelsMeta: host + '/api/model_meta'
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
            misc: {
                text: {}
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
            defaultImage: '/client/dist/static/240x240_placeholder.png',
            defaultLogo: '/client/dist/static/720x300_placeholder.png',
            defaultCatalogCover: '/client/dist/static/240x240_placeholder.png',
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
                menu: [{
                    name: 'Accounts',
                    kind: 11
                }, {
                    name: 'Catalogs',
                    kind: 31
                }, {
                    name: 'Orders',
                    kind: '34'
                }], // admin paths shown in the menu
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
        .config(ng(function ($httpProvider, $locationProvider, $compileProvider) {
            $httpProvider.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';
            $locationProvider.hashPrefix('!');
            $locationProvider.html5Mode(!window.isChromeApp);
            if (window.isChromeApp) {
                $compileProvider.aHrefSanitizationWhitelist(/^\s*(https?|ftp|mailto|chrome-extension):/);
            }
        }));
    angular.module('app', GLOBAL_CONFIG.modules);

}());

$(function () {
    'use strict';
    var container = $('<div>').css({
            height: 1,
            overflow: 'scroll'
        }).appendTo('body'),
        child = $('<div>').css({
            height: 2
        }).appendTo(container);
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
        var failure = function (response) {
                if (response.status === -1) {
                    return; // this is canceled request
                }
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
            var d1 = response[0].data,
                d2 = response[1].data;
            window.MODELS_META = d1;
            window.CURRENT_ACCOUNT = d2.entity;
            if ((d1 && d1.errors) || (d2 && d2.errors)) {
                failure();
            } else {
                angular.bootstrap(document, ['app'], {
                    strictDi: false
                });
            }
        }, failure);

    });
}());
