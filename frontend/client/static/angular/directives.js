/*global angular, window, console, jQuery, $, document*/
angular.module('app').directive('mainMenuToggler', ['$rootScope',
function($rootScope) {

  return {
    link : function(scope, element) {
      var click = function(e, cmd) {
        var mm = $('#main-menu'), visible = mm.is(':visible');

        if ((visible || cmd === 1) && cmd !== 2) {
          mm.stop().animate({
            height : 0
          }, 400, function() {
            $(this).hide();
          });
        } else if (!visible || cmd === 2) {
          mm.height(0).show();
          mm.stop().animate({
            height : ($(window).height() - $('#top-bar').height())
          }, 400);
        }
        if (e) {
          e.preventDefault();
        }

      };

      element.on('click', click);

      scope.$on('$destroy', function() {
        element.off('click', click);
      });

      $rootScope.$on('hide_menu', function() {
        click(null, 1);
      });

      $rootScope.$on('show_menu', function() {
        click(null, 2);
      });

    }
  };
}]).directive('formBuilder', ['$compile', 'UnderscoreTemplate', 'Kinds',
function($compile, UnderscoreTemplate, Kinds) {
  /**
   * Main builder. It will construct a form based on a list of configuration params:
   * [
   * {
   *    'type' : instance of property from backend,
   *    'model' : 'optional, e.g. "name",
   *    ...
   * }
   * ]
   *
   *
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

  return {
    templateUrl : 'form/builder.html',
    controller : function($scope, $element, $attrs) {
      $scope.configurations = $scope.$eval($attrs.formBuilder);
    }
  };
}]).directive('formInput', ['$compile', 'UnderscoreTemplate', 'Endpoint', 'Kinds', 'GeneralLocalCache',
function($compile, UnderscoreTemplate, Endpoint, Kinds, GeneralLocalCache) {

  var internal_config = {
    search : {
      cache_results : {
        '12' : true
      },
      propsFilter_results : {
        'default' : '{name: $select.search}',
        '12' : '{name: $select.search, code: $select.search}'
      },
      view : {
        'default' : function(result) {
          if (result === undefined) {
            return '';
          }
          return result.name;
        }
      },
      queryfilter : {

      }
    }
  }, types = {
    'SuperStringProperty' : function(config) {
      if (config.attrs.type === undefined) {
        config.attrs.type = 'text';
      }
      if (config.field.choices) {
        return 'select';
      }
      return 'string';
    },
    'SuperFloatProperty' : function(config) {
      if (config.attrs.type === undefined) {
        config.attrs.type = 'number';
      }
      return types.SuperStringProperty(config);
    },
    'SuperIntegerProperty' : function(config) {
      if (config.attrs.type === undefined) {
        config.attrs.type = 'number';
      }
      return types.SuperStringProperty(config);
    },
    'SuperDecimalProperty' : function(config) {
      return types.SuperFloatProperty(config);
    },
    'SuperKeyProperty' : function(config) {
      var propsFilter = internal_config.search.propsFilter_results[config.field.kind];
      if (!propsFilter) {
        propsFilter = internal_config.search.propsFilter_results['default'];
      }
      config.specifics.propsFilter = propsFilter;

      if (!config.specifics.view) {
        config.specifics.view = function(result) {
          var fn = internal_config.search.view[config.field.kind];
          if (!fn) {
            fn = internal_config.search.view['default'];
          }

          return fn(result);
        };
      }

      if (!config.specifics.search) {
        config.specifics.search = function(term) {

          Kinds.then(function(kinds) {
            var kindinfo = kinds.get(config.field.kind), cache_hit, cache_key = 'search_results_' + config.field.kind, args, fn, should_cache = false, params = {}, action_search = kindinfo.mapped_actions.search;
            if (action_search !== undefined) {
              if (internal_config.search.cache_results[config.field.kind]) {
                should_cache = true;
              }

              if (config.specifics.entities === undefined) {
                config.specifics.entities = [];
              }
              args = {};
              params = action_search['arguments'].search['default'];
              fn = internal_config.search.queryfilter[config.field.kind];
              if (angular.isFunction(fn)) {
                args = fn(config, action_search.search);
              }
              else
              {
                args = {
                  search : params
                };
              }
              
              if (should_cache)
              {
                cache_hit = GeneralLocalCache.get(cache_key);
                if (cache_hit !== undefined)
                {
                    config.specifics.entities = angular.fromJson(cache_hit);
                    return;
                }
               
              }
              
              Endpoint.post('search', config.field.kind, args, {
                cache : should_cache
              }).success(function(response) {
                config.specifics.entities = response.entities;
                if (should_cache)
                {
                    console.log(GeneralLocalCache);
                    GeneralLocalCache.put(cache_key, angular.toJson(config.specifics.entities));
                }
              });
              
            } else {
              console.error('No search action found in kind: ' + config.field.kind);
            }

          });

        };
      }
      return 'select_async';
    }
  }, utils = {
    attrs : function(config) {
      var defaults = this.default_attrs(config), extra = this.extra_attrs(config), attrs = [];

      angular.extend(defaults, extra);

      angular.forEach(defaults, function(value, key) {
        attrs.push(key + (value ? '="' + value + '"' : ''));
      });

      return attrs.join(' ');
    },
    default_attrs : function(config) {
      var attrs = {};
      if (config.field.max_size) {
        attrs['ng-maxlength'] = 'config.field.max_size';
      }

      if (config.pattern !== undefined) {
        attrs['ng-pattern'] = config.pattern;
      }

      attrs['ng-required'] = 'config.field.required';
      attrs['ng-model'] = config.model;

      if (config.writable) {
        attrs['ng-disabled'] = config.writable;
      }

      return attrs;
    },
    extra_attrs : function(config) {
      return config.attrs;
    },
    label : function(config) {
      var use = '{{config.label}}';
      if (config.label === undefined) {
        use = '{{config.auto_label|inflector:humanize}}';
      }
      return use;
    }
  };

  return {
    link : function(scope, element, attrs) {

      var supplied_config = scope.$eval(attrs.formInput), config = {
        model : 'entity.' + supplied_config.name,
        auto_label : supplied_config.name,
        form : 'main',
        specifics : {},
        attrs : {}
      }, type = types[supplied_config.field.type];

      angular.extend(config, supplied_config);

      if (scope.rule !== undefined) {
        defaults.writable = '!rule.field[\' ' + config.name + ' \'].writable';
      }

      if (type) {

        config.compiled = {
          attrs : utils.attrs(config),
          label : utils.label(config)
        };

        var template = _.template(UnderscoreTemplate.get('underscore/form/' + type(config) + '.html'))({
          config : config
        });

        scope.config = config;

        element.html($compile(template)(scope));
      } else {
        console.error('Field type: ' + config.field.type + ' is not supported');
      }

    }
  };
}]);
