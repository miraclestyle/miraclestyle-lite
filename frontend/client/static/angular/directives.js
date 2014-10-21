/*global angular, window, console, jQuery, $, document*/
'use strict';
angular.module('app').config(function(datepickerConfig) {
  datepickerConfig.showWeeks = false;
})
.directive('mainMenuToggler', function($rootScope) {

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
})
.directive('formElementWrapper', function () {
  return {
    restrict: 'EA',
    transclude: true,
    scope : true,
    templateUrl: 'misc/form_wrapper.html',
    link : function(scope, element, attrs) {
      scope.label = attrs.label;
    }
  };
})
.directive('formInput', function($compile, underscoreTemplate, endpoint, modelMeta, $filter, $modal, helpers, $parse, errorHandling) {

  var inflector = $filter('inflector'), internalConfig = {
    structured : {
      '14' : {
        onlyListFields : ['name', '_country', '_region', 'address', 'default_billing', 'default_shipping'],
        excludeManageFields : ['_country', '_region'],
      }      
    },
    search : {
      cache_results : {
        'default' : true,
        '13' : false
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
        '13' : function (term, info, search_action)
        {
          var args = info.scope.$eval(info.config.ui.parentArgs);
          if ((args && args.country))
          {
        
            return {
              search : {
                 ancestor : args.country,
                 filters : [{
                   value : true,
                   field : 'active',
                   operator : '=='
                 }],
                 orders : [{field: 'name', operator: 'asc'}],
              }
            };
          }
          
          return false;
          
        }
      }
    }
  }, types = {
    Custom : function (info)
    {
      if (info.config.init !== undefined)
      info.config.init(info);
      
      return info.config.template;
    },
    SuperStringProperty : function(info) {
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
    SuperFloatProperty : function(info) {
      var config = info.config;

      if (config.choices) {
        return 'select';
      }

      if (config.ui.attrs.type === undefined) {
        config.ui.attrs.type = 'number';
      }
      return this.SuperStringProperty(info);
    },
    SuperIntegerProperty : function(info) {
      var config = info.config;

      if (config.choices) {
        return 'select';
      }

      if (config.ui.attrs.type === undefined) {
        config.ui.attrs.type = 'number';
      }
      return this.SuperStringProperty(info);
    },
    SuperDecimalProperty : function(info) {
      var config = info.config;
      if (config.choices) {
        return 'select';
      }
      return this.SuperFloatProperty(info);
    },
    SuperBooleanProperty : function(info) {
      var config = info.config;
      return 'boolean';
    },
    SuperKeyProperty : function(info) {
      var config = info.config;
      var propsFilter = internalConfig.search.propsFilter_results[config.kind];
      if (!propsFilter) {
        propsFilter = internalConfig.search.propsFilter_results['default'];
      }
      config.ui.specifics.propsFilter = propsFilter;

      if (!config.ui.specifics.view) {
        config.ui.specifics.view = function(result) {
          var fn = internalConfig.search.view[config.kind];
          if (!fn) {
            fn = internalConfig.search.view['default'];
          }

          return fn(result);
        };
      }

      if (!config.ui.specifics.search) {

        var kindinfo = modelMeta.get(config.kind), cache_hit, cache_key = 'search_results_' + config.kind, should_cache = false, search_command, action_search = kindinfo.mapped_actions.search, skip_search_command = false;

        if (action_search !== undefined) {
          var cache_option = internalConfig.search.cache_results[config.kind];
          if (cache_option !== undefined && cache_option != false) {
            if (angular.isFunction(cache_option))
            {
              cache_key = cache_key + cache_option(info);
            }
            should_cache = cache_key;
          }
          else if (cache_option != false)
          {
            should_cache = internalConfig.search.cache_results['default'];
            if (should_cache === true)
            {
              should_cache = cache_key;
            }
          }
   
          search_command = function(term) {
            var params = action_search['arguments'].search['default'], fn = internalConfig.search.queryfilter[config.kind], args = {};
            if (angular.isFunction(fn)) {
              args = fn(term, info, action_search);
            } else {
              args = {
                search : params
              };
            }
            if (args === false)
            {
              return false;
            }
            endpoint.post('search', config.kind, args, {
              cache : should_cache
            }).then(function(response) {
              config.ui.specifics.entities = response.data.entities;
            });
          };

          if (config.ui.specifics.entities === undefined && should_cache !== false) {
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

    SuperLocalStructuredProperty : function(info) {
      var config = info.config, manageFields = [], sortedFields = [], listFields = [];
      
      if (!info.config.ui.specifics.sortedFields)
      {
        angular.forEach(config.modelclass, function (prop) {
          sortedFields.push(prop);
        });
        
        sortedFields.sort(function (a, b) {
          return parseInt(a.name) - parseInt(b.name);
        });
        
      }
      else
      {
        sortedFields = info.config.ui.specifics.sortedFields;
      }
      
      if (!info.config.ui.specifics.listFields)
      {
  
        angular.forEach(sortedFields, function (item) {
          listFields.push({
              key : item.code_name,
              generated : true,
              label : (item.ui && item.ui.label ? item.ui.label : inflector(item.code_name, 'humanize'))
            });
        });
        
      }
      else
      {
        listFields = info.config.ui.specifics.listFields; 
      }
      
      if (!info.config.ui.specifics.manageFields)
      {
        manageFields = sortedFields;
      }
      else
      {
        manageFields = info.config.ui.specifics.manageFields;
      }
      
      var extraConfig = internalConfig.structured[info.config.modelclass_kind];
      var newListFields = [];
      
      if (extraConfig && extraConfig.onlyListFields)
      { 
         angular.forEach(extraConfig.onlyListFields, function (field) {
       
             var item = _.findWhere(listFields, {key : field});
             
             if (item)
             {
               newListFields.push(item);
             }
              
        });
        
        listFields = newListFields;
        
      }
      else
      {
        
        angular.forEach(listFields, function (item, i) {
          if (extraConfig)
          { 
             if (extraConfig.excludeListFields && $.inArray(item.key, extraConfig.excludeListFields) !== -1)
             {
               return;
             }
     
          }
          
          newListFields.push(item);
           
        });
        
        listFields = newListFields;
        
      }
      
      
      if (extraConfig && extraConfig.sortListFields)
      {
        var newListFields = [];
        angular.forEach(extraConfig.sortListFields, function (field) {
          var item = _.findWhere(listFields, {key : field});
          if (item)
          {
            newListFields.push(item);
          }
        });
        
        listFields = newListFields;
      }
   
      var defaults = {
        listFields : listFields,
        sortedFields : sortedFields,
        manageFields : manageFields,
        addNewText : 'Add',
        addText : '{{config.ui.specifics.addNewText}}',
        remove : function(entity) {
          entity._state = 'deleted';
        },
        manage : function(entity) {
          $modal.open({
            template : underscoreTemplate.get('underscore/form/modal/structured.html')({
              config : config
            }),
            controller : function($scope, $modalInstance, entityUtil) {
              var is_new = false;

              $scope.config = config;
              if (!entity) {
                entity = {
                  kind : config.modelclass_kind
                };
                var length = config.ui.specifics.parentArgs.length;
                entityUtil.normalize(entity, config.modelclass, 
                                config.ui.specifics.entity, info.config.ui.name,
                                 length);
                is_new = true;
              }
        
              $scope.args = angular.copy(entity); // entity.addreses.0.address
              $scope.parentArgs = config.ui.specifics.parentArgs; // entity.addresses
              $scope.entity = config.ui.specifics.args; // entity
 
              $scope.cancel = function() {
                $modalInstance.dismiss('cancel');
              };

              $scope.save = function() {
  

                if (config.repeated) {
                  if (is_new) {
                    $scope.parentArgs.push($scope.args);
                  } else {
                    helpers.update(entity, $scope.args);
                  }
                }

                $scope.cancel();
              };

            }
          });
        }
      };
      
      if (extraConfig && extraConfig.sortManageFields)
      {
        var newManageFields = [];
        angular.forEach(extraConfig.sortManageFields, function (field) {
          var item = _.findWhere(manageFields, {code_name : field});
          if (item)
          {
            newManageFields.push(item);
          }
        });
        
        manageFields = newManageFields;
      }

      defaults.formBuilder = [];
      angular.forEach(manageFields, function(field) {
        if (extraConfig)
        {
          if (extraConfig.excludeManageFields
            && $.inArray(field.code_name, extraConfig.excludeManageFields) !== -1)
            {
              return;
            }
            
          if (extraConfig.onlyManageFields
            && $.inArray(field.code_name, extraConfig.onlyManageFields) === -1)
            {
               return;
            }
         
        }
        defaults.formBuilder.push(field);
      });
      
      

      config.ui.specifics.parentArgs = info.scope.$eval(config.ui.args);
      config.ui.specifics.entity = info.scope.$eval(config.ui.model);
      
      // merge defaults into the 
      angular.forEach(defaults, function(value, key) {
        if (config.ui.specifics[key] === undefined) {
          config.ui.specifics[key] = value;
        }
      });
    
      return 'structured';
    },
    SuperStructuredProperty : function(info) {
      return this.SuperLocalStructuredProperty(info);
    },
    SuperRemoteStructuredProperty : function(info) {
      // remote structured is missing here... @todo
      return this.SuperLocalStructuredProperty(info);
    },
    SuperImageLocalStructuredProperty : function(info) {
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
    SuperTextProperty : function(info) {
      if (info.config.repeated)
      {
        info.config.ui.attrs['repeated-text'] = '';
      }
      return 'text';
    },
    SuperJsonProperty : function(info) {
      info.config.ui.attrs['json-only'] = '';
      return this.SuperTextProperty(info);
    },
    SuperDateTimeProperty : function(info) {
      return 'datetime';
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
      if (config.max_size) {
        attrs['ng-maxlength'] = 'config.max_size';
      }

      if (config.ui.pattern !== undefined) {
        attrs['ng-pattern'] = config.pattern;
      }

      attrs['ng-required'] = 'config.required';
      attrs['ng-model'] = config.ui.args;

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
        use = '{{config.ui.autoLabel|inflector:humanize}}';
      }
      return use;
    }
  };

  return {
    restrict: 'A',
    require : '^form',
    link : function(scope, element, attrs, ctrl) {
     
      var supplied_config = scope.$eval(attrs.formInput), name = null, label = null;
      
      // discover the system name of the property
      if (supplied_config.ui && supplied_config.ui.name !== undefined)
      {
        name = supplied_config.ui.name;
      }
      else if (supplied_config.code_name !== undefined && supplied_config.code_name !== null)
      {
        name = supplied_config.code_name;
      }
      
      // use backend defined label if was provided, otherwise the label will be humanized
      if (supplied_config.verbose_name !== null && supplied_config.verbose_name !== undefined)
      {
        label = supplied_config.verbose_name;
      }
      else
      {
        label = name;
      }
      
      
      if (!name) {
        console.error('Your field config', supplied_config, 'has no name defined defined.');
        return;
      }
      
      var config = {
        ui : { // root config for entire config, upper structure is ndb property definition
          args : 'args.' + name,
          parentArgs : 'args',
          model : 'entity',
          autoLabel : label,
          specifics : {}, // used for property specific configurations
          name : name,
          writable : 'true',
          attrs : {}
        }
      };

      $.extend(true, config, supplied_config);
      // recursive set
      
      var parent = scope.$eval(config.ui.model);

      // auto rule engine
      if (parent !== undefined && parent.ui !== undefined && parent.ui.rule !== undefined) {
        config.ui.writable =  config.ui.model + '.ui.rule.field[\'' + (config.ui.writableName ? config.ui.writableName : config.ui.name) + '\'].writable';
      }

      if (types[supplied_config.type] !== undefined) {
        // reference main locals to type builder
        var tpl = types[supplied_config.type]({
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

        var template = underscoreTemplate.get(config.type != 'Custom' ? 'underscore/form/' + tpl + '.html' : config.template)({
          config : config
        });

        scope.config = config;

        element.html(template);
 
        $compile(element.contents())(scope);
        
       
      } else {
        console.error('Field type: ' + config.type + ' is not supported yet.');
      }

    }
  };
});
