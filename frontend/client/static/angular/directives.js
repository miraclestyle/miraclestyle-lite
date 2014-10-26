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
.directive('generateUploadUrl', function(endpoint, $rootScope) {
  return {
    restrict: 'A',
    require: '^form',
    link : function(scope, element, attrs, ctrl) {
      
      var that = element, form = that.parents('form:first'), autoSubmit = scope.$eval(attrs.generateUploadUrl);
        
      if (!form.length) {
        console.error('Directive upload-on-select demands explicit <form> tag in \
         order to perform regular html form submission');
        return false;
      }
      
      var click = function (e)
      {
          // stop the click if the form is invalid and schedule it for when the
          // submission is complete to start the file dialog
          // ...
          
          if (!ctrl.$valid && autoSubmit)
          {
            return e.preventDefault();
          }
      };
      
      var change = function() {
 
        if (!that.val())
          return false;
 
        if ((!ctrl.$valid && autoSubmit) || !autoSubmit)
        {
          endpoint.post('blob_upload_url', '11', {
            upload_url : endpoint.url
          }).then(function(response) {
                form.attr('action', response.data.upload_url);
                
                scope.$emit('prepareTheBody');
                
                if (autoSubmit)
                {
                  form.submit();
                }
          });
        
        }
          
      };
   
      $(element).on('click', click)
                .on('change', change);

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
.directive('formInput', function($compile, underscoreTemplate, endpoint, modelMeta, $q, $filter, $modal, helpers, $parse, errorHandling) {

  var inflector = $filter('inflector'), internalConfig = {
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

        var action_search = modelMeta.getActionArguments(config.kind, 'search'), cache_hit, cache_key = 'search_results_' + config.kind, should_cache = false, search_command, skip_search_command = false;

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
            var params = action_search.search['default'], fn = internalConfig.search.queryfilter[config.kind], args = {};
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
      var config = info.config, fields = [], beforeSave, modelFields, defaultFields, noSpecifics, afterSave, listFields = [];
     
      beforeSave = config.ui.specifics.beforeSave;
      afterSave = config.ui.specifics.afterSave;
      noSpecifics = !angular.isDefined(config.ui.specifics);
      modelFields = modelMeta.getModelFields(config.modelclass_kind);
      
      defaultFields = _.toArray(modelFields);
      defaultFields = defaultFields.sort(function (prev, next) {
        return parseInt(prev.name) - parseInt(next.name);
      });
      
      if (noSpecifics || !config.ui.specifics.fields)
      { 
        config.ui.specifics.fields = defaultFields;
      }
      
      if (noSpecifics || !config.ui.specifics.listFields)
      {
     
        angular.forEach(defaultFields, function (field) {
          if (!noSpecifics && (config.ui.specifics.excludeListFields && $.inArray(field.code_name, config.ui.specifics.excludeListFields) !== -1))
          {
            return;
          }
          
          listFields.push({
              key : field.code_name,
              generated : true,
              label : (field.ui && field.ui.label ? field.ui.label : inflector(field.code_name, 'humanize'))
            });
        });
  
        if (!noSpecifics && angular.isDefined(config.ui.specifics.onlyListFields))
        {
            var newListFields = [];
            angular.forEach(config.ui.specifics.onlyListFields, function (key) {
              var find = _.findWhere(listFields, {key : key});
              if (find)
              {
                newListFields.push(find);
              }
            });
            
            listFields = newListFields;
        }
        
      }
 
      var defaults = {
        listFields : listFields,
        fields : fields,
        addNewText : 'Add',
        addText : '{{config.ui.specifics.addNewText}}'
      };
  
      // merge defaults into the 
      angular.forEach(defaults, function(value, key) {
        if (config.ui.specifics[key] === undefined) {
          config.ui.specifics[key] = value;
        }
      });
      
      config.ui.specifics.parentArgs = info.scope.$eval(config.ui.args);
      config.ui.specifics.entity = info.scope.$eval(config.ui.model);
 
      
      config.ui.specifics.formBuilder = [];
      angular.forEach(config.ui.specifics.fields, function(field) {
        var copyWritable = angular.copy(config.ui.writable);
        copyWritable.push((field.ui.writableName ? field.ui.writableName : field.code_name));
        field.ui.formName = copyWritable.join('_');
        field.ui.writable = copyWritable;
        config.ui.specifics.formBuilder.push(field);
      });
      
      if (!config.repeated)
      {
        config.ui.specifics.SingularCtrl = function ($scope)
        { 
          $scope.args = config.ui.specifics.parentArgs;
        };
        
      }
      else
      {
        
        if (config.ui.specifics.remove === undefined)
        {
          config.ui.specifics.remove = function(arg) {
            arg._state = 'deleted';
          };
        }
        
        if (config.ui.specifics.manage === undefined)
        {  
          config.ui.specifics.manage = function(arg) {
     
            $modal.open({
              template : underscoreTemplate.get(config.ui.specifics.templateUrl ? config.ui.specifics.templateUrl : 'underscore/form/modal/structured.html')({
                config : config
              }),
              controller : function($scope, $modalInstance, entityUtil) {
                var is_new = false;
  
                $scope.config = config;
                if (!arg) {
                  arg = {
                    kind : config.modelclass_kind
                  };
                  var length = config.ui.specifics.parentArgs.length;
                  entityUtil.normalize(arg, config.modelclass, 
                                  config.ui.specifics.entity, config.code_name,
                                   length, false);
                  is_new = true;
                }
                $scope.container = {};
                $scope.args = angular.copy(arg); // entity.addreses.0.address
                $scope.parentArgs = config.ui.specifics.parentArgs; // entity.addresses
                $scope.entity = config.ui.specifics.entity;
   
                $scope.cancel = function() {
                  $modalInstance.dismiss('cancel');
                };
  
                $scope.save = function() {
                  
                  if (!$scope.container.form.$valid)
                  {
                    errorHandling.modal({
                      required : ['field']
                    });
                    return;
                  }
                  var promise = null;
                  if (angular.isFunction(config.ui.specifics.beforeSave))
                  {
                    promise = config.ui.specifics.beforeSave($scope, info);
                  }
                  
                  var complete = function ()
                  {
                    var promise = null;
                    
                    if (config.repeated) {
                      if (is_new) {
                        $scope.parentArgs.push($scope.args);
                      } else {
                        helpers.update(arg, $scope.args);
                      }
                    }
                     
                    if (angular.isFunction(config.ui.specifics.afterSave))
                    {
                      promise = config.ui.specifics.afterSave($scope, info);
                    }
                    
                    if (promise && promise.then)
                    {
                      promise.then(function () {
                        $scope.cancel();
                      });
                    }
                    else
                    {
                      $scope.cancel();
                    }
     
                  };
                  
                  if (promise && promise.then)
                  {
                    promise.then(complete);
                  }
                  else
                  {
                    complete();
                  }
                    
                };
  
              }
            });
          };
            
        }
      }
    
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
           if (info.config.repeated)
           {
             
             var path = info.scope.entity.root_access().split('.');
             path.splice(path.length-1, 1);
             var getter = $parse(path.join('.')),
                 setter = getter.assign;
             
             var list = getter(info.scope.entity.root());
             var new_entities = getter(content.entity);
             list.push(new_entities);
             
           }
           
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

      if (!angular.isArray(config.ui.writable)) {
        attrs['ng-disabled'] = '!' + config.ui.writable;
      }
      else
      {
        var writableCompiled = config.ui.model + '.ui.rule.field' + $.map(config.ui.writable, function (item) {
          return "['" + helpers.addslashes(item) + "']";
        }).join('') + '.writable';
        
        attrs['ng-disabled'] = '!' + writableCompiled;
        
        config.ui.writableCompiled = writableCompiled;
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
    scope : true,
    transclude : true,
    link : function(scope, element, attrs, ctrl) {
 
      var supplied_config = scope.$eval(attrs.formInput), name = supplied_config.code_name, label = null;
 
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
          formName : name,
          writable : [name],
          attrs : {}
        }
      };

      $.extend(true, config, supplied_config);
      
      if (config.ui.writableName !== undefined)
      {
        config.ui.writable = [config.ui.writableName];
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
}).directive('compatibilityMaker', function () {
  return {
    restrict : 'A',
    require : 'ngModel',
    link : function (scope, element, attrs, ngModelCtrl)
    { 
         var fn = function (newval, oldval) {
           if (newval === true)
           { 
             var newval = scope.$eval(attrs.compatibilityMaker),
                 stringify = JSON.stringify(newval);
             scope.json_body = stringify;
           }
         };
         
         scope.$watch('$isUploading', fn);
         scope.$on('prepareTheBody', function () {
           fn(true);
         });
    }
  }
})
.directive('fitInDialog', function () {
  return {
    link : function (scope, element, attrs)
    {
      var fn = function () {
 
          var modal_dialog = $(element).parents('.modal-dialog:first');
          
          var height = $(window).height();
          
          height -= parseInt(modal_dialog.css('margin-top')) + parseInt(modal_dialog.css('margin-bottom'));
          height -= 2;
          
          var modal_footer = modal_dialog.find('.modal-footer');
          
          if (modal_footer.length)
             height -= modal_footer.outerHeight()+3;
          
          modal_dialog.find('.modal-body.scrollable').height(height);
  
      };
      
      $(window).bind('resize modal.open', fn);
      scope.$on('$destroy', function () {
        $(window).unbind('resize modal.open', fn);
      });
    }
  }
})
.directive('displayImage', function () {
    return {
      scope : {
        image : '=displayImage'
      },
      link : function (scope, element, attrs)
      { 
         var fn = function (nv, ov) {
           
           if (nv !== ov)
           {
               var load = function ()
             {
                $(element).html($(this));
             };
             
             $('<img />').on('load', load).attr('src', scope.image.serving_url);
           }
           
           
         };
         
         scope.$watch('image.serving_url', fn);
         
         fn(true, false)
         
         
      }
    };
});
