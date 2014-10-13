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
}]).directive('formBuilder', ['$compile', 'UnderscoreTemplate', 'ModelMeta',
function($compile, UnderscoreTemplate, ModelMeta) {
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
   */

  return {
    templateUrl : 'form/builder.html',
    controller : function($scope, $element, $attrs) {
      $scope.configurations = $scope.$eval($attrs.formBuilder);
    }
  };
}]).directive('formInput', ['$compile', 'UnderscoreTemplate', 'Endpoint', 'ModelMeta', 'GeneralLocalCache',
function($compile, UnderscoreTemplate, Endpoint, ModelMeta, GeneralLocalCache) {

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
      
      if (config.field.choices) {
        return 'select';
      }
      
      if (config.attrs.type === undefined) {
        config.attrs.type = 'number';
      }
      return types.SuperStringProperty(config);
    },
    'SuperIntegerProperty' : function(config) {
      
      if (config.field.choices) {
        return 'select';
      }
      
      if (config.attrs.type === undefined) {
        config.attrs.type = 'number';
      }
      return types.SuperStringProperty(config);
    },
    'SuperDecimalProperty' : function(config) {
      if (config.field.choices) {
        return 'select';
      }
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

        var kindinfo = ModelMeta.get(config.field.kind), cache_hit, cache_key = 'search_results_' + config.field.kind, 
            should_cache = false, search_command, action_search = kindinfo.mapped_actions.search, skip_search_command = false;

        if (action_search !== undefined) {
          if (internal_config.search.cache_results[config.field.kind]) {
            should_cache = true;
          }

          if (config.specifics.entities === undefined) {
            config.specifics.entities = [];
          }
        
          if (should_cache) { // @todo rework auto-cache mechanism
            cache_hit = GeneralLocalCache.get(cache_key);
            if (cache_hit !== undefined) {
              config.specifics.entities = angular.fromJson(cache_hit);
              skip_search_command = true;
            }
          }

          search_command = function (term)
          { 
            var params = action_search['arguments'].search['default'],
                fn = internal_config.search.queryfilter[config.field.kind],
                args = {};
            if (angular.isFunction(fn)) {
              args = fn(term, config, action_search.search);
            } else {
              args = {
                search : params
              };
            }
            Endpoint.post('search', config.field.kind, args, {
              cache : should_cache
            }).success(function(response) {
              config.specifics.entities = response.entities;
              if (should_cache) {
                GeneralLocalCache.put(cache_key, angular.toJson(config.specifics.entities));
              }
            });
          };
          
          if (!skip_search_command)
          {
             search_command();
          }
         

        } else {
          console.error('No search action found in kind: ' + config.field.kind);
        }
        
        if (!should_cache)
        {
          config.specifics.search = function(term) {
            search_command(term);
          };
        }
        
      }
 
      return 'select_async';
    },
    
    'SuperLocalStructuredProperty' : function (config)
    {
      var defaults = {
        fields : $.map(Object.keys(config.field.modelclass), function (item) {
            return {'key': item, 'label' : item};
        }),
        add_new_text : 'Add',
        add_text : '{{config.specifics.add_new_text}}',
        show : function (val, field)
        {
            return val[field];
        }
      };
      
      angular.forEach(defaults, function (value, key) {
        if (config.specifics[key] === undefined)
        {
          config.specifics[key] = value;
        }
      });
  
      return 'structured';
    }
  }, utils = {
    attrs : function(config) {
      var defaults = this.default_attrs(config), extra = this.extra_attrs(config), attrs = [];

      angular.extend(defaults, extra);

      angular.forEach(defaults, function(value, key) {
        attrs.push(key + ( value ? '="' + value + '"' : ''));
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
      
        var tpl = type(config);
        
        config.compiled = {
          attrs : utils.attrs(config),
          label : utils.label(config)
        };
         
        var template = _.template(UnderscoreTemplate.get('underscore/form/' + tpl + '.html'))({
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
