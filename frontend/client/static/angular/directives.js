/*global angular, window, console, jQuery, $, document*/
'use strict';
angular.module('app').directive('mainMenuToggler', function($rootScope) {

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
})
.directive('toggle', function() {
    return {
        scope: {
            ngModel: '='
        },
        link: function(scope, element, attrs, controller) {
          
          var toggle = attrs.toggle;
          if (!toggle) toggle = 'Yes/No';
          var splits = toggle.split('/');
 
          var init = function ()
          {
            if (scope.ngModel)
            {
              element.text(splits[0]);
            }
            else
            {
              element.text(splits[1]);
            }
          };
          
          init();
          
           var handler = function() {
                scope.$apply(function() {
                    scope.ngModel = !scope.ngModel;
                    init();
                });
            };
            
            element.bind('click', handler);
            
            scope.$on('$destroy', function () {
              element.off('click', handler);
            });
        }
    };
})
.directive('formBuilder', function($compile, UnderscoreTemplate, ModelMeta) {
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
}).directive('formInput',
function($compile, UnderscoreTemplate, Endpoint, ModelMeta, $filter, $modal, Helpers) {

  var inflector = $filter('inflector'), internal_config = {
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
    'SuperStringProperty' : function(info) {
      var config = info.config;
      if (config.attrs.type === undefined) {
        config.attrs.type = 'text';
      }
      if (config.field.choices) {
        return 'select';
      }
      return 'string';
    },
    'SuperFloatProperty' : function(info) {
      var config = info.config;

      if (config.field.choices) {
        return 'select';
      }

      if (config.attrs.type === undefined) {
        config.attrs.type = 'number';
      }
      return types.SuperStringProperty(info);
    },
    'SuperIntegerProperty' : function(info) {
      var config = info.config;

      if (config.field.choices) {
        return 'select';
      }

      if (config.attrs.type === undefined) {
        config.attrs.type = 'number';
      }
      return types.SuperStringProperty(info);
    },
    'SuperDecimalProperty' : function(info) {
      var config = info.config;
      if (config.field.choices) {
        return 'select';
      }
      return types.SuperFloatProperty(info);
    },
    'SuperBooleanProperty' : function(info) {
      var config = info.config;
      return 'boolean';
    },
    'SuperKeyProperty' : function(info) {
      var config = info.config;
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
            should_cache = false, search_command, 
            action_search = kindinfo.mapped_actions.search, skip_search_command = false;

        if (action_search !== undefined) {
          if (internal_config.search.cache_results[config.field.kind]) {
            should_cache = cache_key;
          }

        
          search_command = function(term) {
            var params = action_search['arguments'].search['default'], fn = internal_config.search.queryfilter[config.field.kind], args = {};
            if (angular.isFunction(fn)) {
              args = fn(term, config, action_search.search);
            } else {
              args = {
                search : params
              };
            }
            Endpoint.post('search', config.field.kind, args, {
              cache : should_cache
            }).then(function(response) {
              config.specifics.entities = response.data.entities;
            });
          };

          if (config.specifics.entities === undefined) {
            search_command();
          }

        } else {
          console.error('No search action found in kind: ' + config.field.kind);
        }

        if (should_cache === false) {
          config.specifics.search = function(term) {
            search_command(term);
          };
        }

      }

      return 'select_async';
    },
    
    'SuperStructuredProperty' : function(info)
    {
       return types.SuperLocalStructuredProperty(info);
    },
    'SuperLocalStructuredProperty' : function(info) {
      var config = info.config;
      var defaults = {
        fields : $.map(Object.keys(config.field.modelclass), function(item) {

          return {
            'key' : item,
            'generated' : true,
            'label' : inflector(item, 'humanize')
          };
          
        }),
        add_new_text : 'Add',
        add_text : '{{config.specifics.add_new_text}}',
        show : function(val, field) {
          return val[field];
        },
        remove : function (entity)
        {
          entity._state = 'deleted';
        },
        manage : function (entity)
        {
          $modal.open({
            template : UnderscoreTemplate.get('underscore/form/modal/structured.html')({
              config : config
            }),
            controller : function ($scope, $modalInstance, Entity)
            {
                var is_new = false, parentEntity;
                
                $scope.config = config;
                if (!entity) 
                {
                  entity = {kind : config.field.modelclass_kind};
                  Entity.normalize(entity);
                  is_new = true;
                }
                console.log(entity);
                $scope.entity = angular.copy(entity);
                $scope.parentEntity = config.specifics.entities;
                 
                $scope.cancel = function ()
                {
                    $modalInstance.dismiss('cancel');
                };
                
                $scope.save = function ()
                {
                    
                   if (config.field.repeated)
                   {
                     if (is_new)
                     {
                        $scope.parentEntity.push($scope.entity);
                     }
                     else
                     {
                        Helpers.update(entity, $scope.entity);
                     }
                  
                     
                   }
                 
                   $scope.cancel();
                };
                
            }
          });
        }
      };
      
      defaults.formBuilder = [];
      angular.forEach(defaults.fields, function (field) {
        defaults.formBuilder.push({
          field : config.field.modelclass[field.key],
          name : field.key,
          label : field.label
        });
      });
      
      config.specifics.entities = info.scope.$eval(config.model);
 
       
      angular.forEach(defaults, function(value, key) {
        if (config.specifics[key] === undefined) {
          config.specifics[key] = value;
        }
      });

      return 'structured';
    },
    'SuperRemoteStructuredProperty' : function(info)
    {
      return types.SuperLocalStructuredProperty(info);
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
        attrs['ng-disabled'] = '!' + config.writable;
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

      var supplied_config = scope.$eval(attrs.formInput),
          name = (supplied_config.name !== undefined ? supplied_config.name : supplied_config.field.code_name);
      if (name === undefined)
      {
        console.error('Your field config', supplied_config, 'has no `name` defined.');
        return;
      }    
      var config = {
        model : 'entity.' + name,
        auto_label : name,
        form : 'main',
        specifics : {},
        name : name,
        writable : 'true',
        attrs : {}
      }, type = types[supplied_config.field.type];

      angular.extend(config, supplied_config);

      if (scope.entity !== undefined && scope.entity.ui !== undefined && scope.entity.ui.rule !== undefined) {
        config.writable = 'entity.ui.rule.field[\' ' + config.name + ' \'].writable';
      }

      if (type) {

        var tpl = type({
          config : config,
          element : element,
          scope : scope,
          attrs : attrs
        });

        config.compiled = {
          attrs : utils.attrs(config),
          label : utils.label(config)
        };

        var template = UnderscoreTemplate.get('underscore/form/' + tpl + '.html')({
          config : config
        });

        scope.config = config;

        element.html($compile(template)(scope));
      } else {
        console.error('Field type: ' + config.field.type + ' is not supported');
      }

    }
  };
});