/*global angular, window, console, jQuery, $, document*/
'use strict';
angular.module('app').config(function(datepickerConfig) {
  datepickerConfig.showWeeks = false;
}).directive('mainMenuToggler', function($rootScope) {

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
}).directive('toggle', function() {
  return {
    scope : {
      ngModel : '='
    },
    link : function(scope, element, attrs, controller) {

      var toggle = attrs.toggle;
      if (!toggle)
        toggle = 'Yes/No';
      var splits = toggle.split('/');

      var init = function() {
        if (scope.ngModel) {
          element.text(splits[0]);
        } else {
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

      scope.$on('$destroy', function() {
        element.off('click', handler);
      });
    }
  };
}).directive('jsonOnly', function() {
  return {
    require : 'ngModel',
    link : function(scope, element, attrs, ctrl) {
      var worker = function(value, what) {
        
        var test = false;
     
        try {
          value = angular[what](value);
          test = true;

        } catch(e) { }

        ctrl.$setValidity('jsonOnly', test);
  
        return value;
      };
      var parser = function(value) {
         return worker(value, 'fromJson');
      };
      var formatter = function(value) {
         return worker(value, 'toJson');
      };
      
      ctrl.$parsers.push(parser);
      ctrl.$formatters.push(formatter);
    }
  };
})
.directive('repeatedText', function() {
  return {
    require : 'ngModel',
    link : function(scope, element, attrs, ctrl) {
      
      var worker = function(value, what) {
        
        var test = false;
     
        try {
          if (what == 'list')
          {
            value = value.match(/[^\r\n]+/g);
          }
          test = true;

        } catch(e) { }

        ctrl.$setValidity('repeatedText', test);
  
        return value;
      };
      var parser = function(value) {
         return worker(value, 'list');
      };
      var formatter = function(value) {
         return worker(value, 'str');
      };
    
      ctrl.$parsers.push(parser);
      ctrl.$formatters.push(formatter);
    }
  };
})
.directive('uploadOnSelect', function(endpoint, $rootScope) {
  return {
    restrict: 'A',
    require: '^form',
    link : function(scope, element, attrs, ctrl) {
      
      var that = element, form = that.parents('form:first');
        
      if (!form.length) {
        console.error('Directive upload-on-select demands explicit <form> tag in \
         order to perform regular html form submission');
        return false;
      }
      
      var click = function ()
      {
          // stop the click if the form is invalid and schedule it for when the
          // submission is complete to start the file dialog
          // ...
      };
      
      var change = function() {
 
        if (!that.val())
          return false;
  
        var options = scope.$eval(attrs.uploadOnSelect);
        
        if (ctrl.$valid)
        {
          endpoint.post('blob_upload_url', '11', {
            'upload_url' : endpoint.url
          }).then(function(response) {
                form.attr('action', response.data.upload_url).trigger('submit');
               // triggers angular ng-upload
          });
        
        }
          
      };

      $(element).on('change', change);

      scope.$on('$destroy', function() {
        $(element).off('change', change).off('click', click);
        
      });
      
      scope.$on('ngUploadComplete', function ($event, content) {
         form.attr('action', endpoint.url);
         scope.$emit('ngUploadCompleteImageUpload', content);
      });
    }
  };
}).directive('formBuilder', function($compile, underscoreTemplate, modelMeta) {
  /**
   * Main builder. It will construct a form based on a list of configuration params:
   * [
   * {
   *    ... field data
   *
   *    ui : {... user defined dictionary }
   * }
   * ]
   *
   */

  return {
    restrict: 'A',
    require : '^form',
    templateUrl : 'form/builder.html',
    controller : function($scope, $element, $attrs) {
      $scope.configurations = $scope.$eval($attrs.formBuilder);
    }
  };
}).directive('formInput', function($compile, underscoreTemplate, endpoint, modelMeta, $filter, $modal, helpers, $parse, errorHandling) {

  var inflector = $filter('inflector'), internal_config = {
    search : {
      cache_results : {
        'default' : true
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
      if (config.ui.attrs.type === undefined) {
        config.ui.attrs.type = 'text';
      }
      
      if (config.choices) {
        return 'select';
      }
      
      if (info.config.repeated)
      {
        info.config.ui.attrs['repeated-text'] = '';
        return 'text';
      }
      
      return 'string';
    },
    'SuperFloatProperty' : function(info) {
      var config = info.config;

      if (config.choices) {
        return 'select';
      }

      if (config.ui.attrs.type === undefined) {
        config.ui.attrs.type = 'number';
      }
      return types.SuperStringProperty(info);
    },
    'SuperIntegerProperty' : function(info) {
      var config = info.config;

      if (config.choices) {
        return 'select';
      }

      if (config.ui.attrs.type === undefined) {
        config.ui.attrs.type = 'number';
      }
      return types.SuperStringProperty(info);
    },
    'SuperDecimalProperty' : function(info) {
      var config = info.config;
      if (config.choices) {
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
      var propsFilter = internal_config.search.propsFilter_results[config.kind];
      if (!propsFilter) {
        propsFilter = internal_config.search.propsFilter_results['default'];
      }
      config.ui.specifics.propsFilter = propsFilter;

      if (!config.ui.specifics.view) {
        config.ui.specifics.view = function(result) {
          var fn = internal_config.search.view[config.kind];
          if (!fn) {
            fn = internal_config.search.view['default'];
          }

          return fn(result);
        };
      }

      if (!config.ui.specifics.search) {

        var kindinfo = modelMeta.get(config.kind), cache_hit, cache_key = 'search_results_' + config.kind, should_cache = false, search_command, action_search = kindinfo.mapped_actions.search, skip_search_command = false;

        if (action_search !== undefined) {
          var cache_option = internal_config.search.cache_results[config.kind];
          if (cache_option !== undefined) {
            should_cache = cache_key;
          }
          else
          {
            should_cache = internal_config.search_cache_results['default'];
          }

          search_command = function(term) {
            var params = action_search['arguments'].search['default'], fn = internal_config.search.queryfilter[config.kind], args = {};
            if (angular.isFunction(fn)) {
              args = fn(term, config, action_search.search);
            } else {
              args = {
                search : params
              };
            }
            endpoint.post('search', config.kind, args, {
              cache : should_cache
            }).then(function(response) {
              config.ui.specifics.entities = response.data.entities;
            });
          };

          if (config.ui.specifics.entities === undefined) {
            search_command();
          }

        } else {
          console.error('No search action found in kind: ' + config.kind);
        }

        if (should_cache === false) {
          config.ui.specifics.search = function(term) {
            search_command(term);
          };
        }

      }

      return 'select_async';
    },

    'SuperLocalStructuredProperty' : function(info) {
      var config = info.config;
      var defaults = {
        fields : $.map(Object.keys(config.modelclass), function(item) {

          return {
            'key' : item,
            'generated' : true,
            'label' : inflector(item, 'humanize')
          };

        }),
        add_new_text : 'Add',
        add_text : '{{config.ui.specifics.add_new_text}}',
        show : function(val, field) {
          return val[field];
        },
        remove : function(entity) {
          entity._state = 'deleted';
        },
        manage : function(entity) {
          $modal.open({
            template : underscoreTemplate.get('underscore/form/modal/structured.html')({
              config : config
            }),
            controller : function($scope, $modalInstance, Entity) {
              var is_new = false, parentEntity;

              $scope.config = config;
              if (!entity) {
                entity = {
                  kind : config.modelclass_kind
                };
                var length = config.ui.specifics.entities.length;
                Entity.normalize(entity, config.modelclass, 
                                config.ui.specifics.entity, info.config.ui.name,
                                 length);
                is_new = true;
              }

              $scope.entity = angular.copy(entity);
              $scope.parentEntity = config.ui.specifics.entities;

              $scope.cancel = function() {
                $modalInstance.dismiss('cancel');
              };

              $scope.save = function() {
                
                console.log($scope.entity, $scope.entity.ui.root_access());

                if (config.repeated) {
                  if (is_new) {
                    $scope.parentEntity.push($scope.entity);
                  } else {
                    helpers.update(entity, $scope.entity);
                  }

                }

                $scope.cancel();
              };

            }
          });
        }
      };

      defaults.formBuilder = [];
      angular.forEach(defaults.fields, function(field) {
        defaults.formBuilder.push(config.modelclass[field.key]);
      });

      config.ui.specifics.entities = info.scope.$eval(config.ui.model);
      config.ui.specifics.entity = info.scope.$eval(config.ui.parent_model);

      angular.forEach(defaults, function(value, key) {
        if (config.ui.specifics[key] === undefined) {
          config.ui.specifics[key] = value;
        }
      });

      return 'structured';
    },
    'SuperStructuredProperty' : function(info) {
      return types.SuperLocalStructuredProperty(info);
    },
    'SuperRemoteStructuredProperty' : function(info) {
      // remote structured is missing here... @todo
      return types.SuperLocalStructuredProperty(info);
    },
    'SuperImageLocalStructuredProperty' : function(info) {
      info.scope.$on('ngUploadCompleteImageUpload', function ($event, content) {
         if (!content || content.errors)
         {
           errorHandling.modal(content.errors);
         }
         else
         {
           var path = info.scope.entity.root_access().split('.');
           path.splice(path.length-1, 1);
           var getter = $parse(path.join('.')),
               setter = getter.assign;
           
           var list = getter(info.scope.entity.root());
           var new_entities = getter(content.entity);
           list.push(new_entities);
         }
         
      });
      return 'image';
    },
    'SuperTextProperty' : function(info) {
      if (info.config.repeated)
      {
        info.config.ui.attrs['repeated-text'] = '';
      }
      return 'text';
    },
    'SuperJsonProperty' : function(info) {
      info.config.ui.attrs['json-only'] = '';
      return types.SuperTextProperty(info);
    },
    'SuperDateTimeProperty' : function(info) {
      return 'datetime';
    }
  }, utils = {
    attrs : function(config) {
      var defaults = utils.default_attrs(config), extra = utils.extra_attrs(config), attrs = [];

      angular.extend(defaults, extra);

      angular.forEach(defaults, function(value, key) {
        attrs.push(key + ( value ? '="' + value + '"' : ''));
      });

      return attrs.join(' ');
    },
    default_attrs : function(config) {
      var attrs = {};
      if (config.max_size) {
        attrs['ng-maxlength'] = 'config.max_size';
      }

      if (config.ui.pattern !== undefined) {
        attrs['ng-pattern'] = config.pattern;
      }

      attrs['ng-required'] = 'config.required';
      attrs['ng-model'] = config.ui.model;

      if (config.ui.writable) {
        attrs['ng-disabled'] = '!' + config.ui.writable;
      }

      return attrs;
    },
    extra_attrs : function(config) {
      return config.ui.attrs;
    },
    label : function(config) {
      var use = '{{config.ui.label}}';
      if (config.label === undefined) {
        use = '{{config.ui.auto_label|inflector:humanize}}';
      }
      return use;
    }
  };

  return {
    restrict: 'A',
    require : '^form',
    link : function(scope, element, attrs, ctrl) {
     
      var supplied_config = scope.$eval(attrs.formInput), name = (supplied_config.code_name !== undefined ? supplied_config.code_name : (supplied_config.ui ? supplied_config.ui.name : undefined));

      if (!name) {
        console.error('Your field config', supplied_config, 'has no name defined defined.');
        return;
      }
      var config = {
        ui : {
          model : 'entity.' + name,
          parent_model : 'entity',
          auto_label : name,
          specifics : {},
          name : name,
          writable : 'true',
          attrs : {}
        }
      }, type = types[supplied_config.type];

      $.extend(true, config, supplied_config);
      // recursive set

      // auto rule engine
      if (scope.entity !== undefined && scope.entity.ui !== undefined && scope.entity.ui.rule !== undefined) {
        config.ui.writable = 'entity.ui.rule.field[\' ' + config.name + ' \'].writable';
      }

      if (type) {
        // reference main locals to type builder
        var tpl = type({
          config : config,
          element : element,
          scope : scope,
          attrs : attrs
        });

        // compiled variables for the template
        config.ui.compiled = {
          attrs : utils.attrs(config),
          label : utils.label(config)
        };

        var template = underscoreTemplate.get('underscore/form/' + tpl + '.html')({
          config : config
        });

        scope.config = config;

        element.html(template);
 
        $compile(element.contents())(scope);
        
       
      } else {
        console.error('Field type: ' + config.type + ' is not supported');
      }

    }
  };
});
