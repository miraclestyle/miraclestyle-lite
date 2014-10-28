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
      
      var resize = function ()
      {
        var mm = $('#main-menu'), visible = mm.is(':visible');
        
        if (visible)
        { 
          mm.stop().animate({
            height : ($(window).height() - $('#top-bar').height())
          }, 400);
          
        }
        
      };

      element.on('click', click);
      $(window).on('resize', resize);

      scope.$on('$destroy', function() {
        element.off('click', click);
        $(window).off('resize', resize);
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
    link : function(scope, element, attrs) {

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
  
      
      var change = function() {
 
        if (!that.val())
        {
          return false;
        } 
        
        endpoint.post('blob_upload_url', '11', {
            upload_url : endpoint.url
          }).then(function(response) {
             form.attr('action', response.data.upload_url);
          });
          
      };
   
      $(element).on('change', change);

      scope.$on('$destroy', function() {
        $(element).off('change', change);
      });
      
      scope.$on('ngUploadComplete', function ($event, content) {
         form.attr('action', endpoint.url);
         that.val('');
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
.directive('formInput', function($compile, underscoreTemplate, formInputTypes, helpers) {

  var types = formInputTypes, utils = {
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
        config.ui.writableCompiled = config.ui.writable;
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
      if (config.ui.label === undefined) {
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
 
      var run = function (){
 
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
        
        if (config.ui.writableName !== undefined && angular.isArray(config.ui.writable))
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
      
      };
      
      run();

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
                 stringified = JSON.stringify(newval);
             scope.json_body = stringified;
           }
         };
         
         scope.$watch('$isUploading', fn);
         scope.$on('stringifyData', function () {
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
