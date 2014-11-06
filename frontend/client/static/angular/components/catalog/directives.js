angular.module('app').directive('gridGenerator', function (GLOBAL_CONFIG, helpers) {
  return {
    scope: {
      image: '=gridGeneratorImage'
    },
    link: function (scope, element, attrs) {
  
        var config = scope.$eval(attrs.gridGenerator) || {},
            margin = config.margin || 0,
            maxWidth = config.maxWidth || GLOBAL_CONFIG.gridMaxWidth,
            minWidth = config.minWidth || GLOBAL_CONFIG.gridMinWidth,
            square = config.square || true,
            timeout = null,
            resize = function () {
              if (timeout)
              {
                clearTimeout(timeout);
              }
              timeout = setTimeout(function () { 
                element = $(element);
                if (!element.length)
                {
                  return;
                }
                var wrapper = element.parents('.grid-wrapper:first'),
                    canvasWidth = wrapper.outerWidth(true);
                if (canvasWidth)
                { 
                  var values = helpers.calculateGrid(canvasWidth, maxWidth, minWidth, margin);
                  wrapper.css({
                    paddingRight: values[2],
                    paddingLeft: values[2]
                  });
                     
                  element.each(function () {
                       var box = $(this).width(values[0]);
                       if (square) {
                         box.height(values[0]);
                         var img = box.find('img');
                         if (scope.image) { 
                           img.removeClass('horizontal vertical');
                           if (scope.image.proportion > 1)
                           {
                             img.addClass('horizontal');
                           }
                           else
                           {
                             img.addClass('vertical');
                           } 
                         }
                          
                       }
                       
                     });
                    
                  
                }
              
              }, 150);
            };
            
            resize();
        
            $(window).bind('resize', resize);
            
            scope.$on('accordionStateChanged', function () {
              resize();
            });
            
            scope.$on('$destroy', function () {
              $(window).off('resize', resize);
            });
             
    }
  };
});