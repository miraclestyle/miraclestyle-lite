angular.module('app').directive('catalogSlider', function ($timeout) {
  return {
    restrict: 'A',
    link: function (scope, element, attrs) {
      var images = scope.$eval(attrs.catalogSlider),
          loading = null,
          callback = scope.$eval(attrs.catalogSliderLoadMore),
          parent = element.parent('.catalog-slider-outer:first'),
          tryToLoad = function (settings) {
              var p = parent.get(0), 
                  maxscroll = p.scrollWidth - p.clientWidth;
                  sense = maxscroll - parent.scrollLeft(); 
              if (sense < 300 && !loading) { 
                loading = setTimeout(function () {
                  callback(function () {
                    loading = null;
                  });
                }, 200);
                
               }
          };
          
      var measure = function () {
        var tw = 0;
        var items = element.find('.item').each(function () {
          tw += element.width();
        });
        
        element.width(tw);
      };
      
      scope.$on('reMeasureCatalogSlider', function () {
        measure();
      });
  
      scope.$on('readyCatalogSlider', function () {
        
        $timeout(function () {
           
          measure();
          
          parent.kinetic({
            y:false,
            cursor: false,
            maxvelocity: 60,
            moved: tryToLoad,
            stopped: tryToLoad
          });
           
        });
        
      });
    }
  }
}).directive('catalogSliderImage', function ($timeout) {
  return {
    restrict: 'A',
    link: function (scope, element, attrs) {
      
      var run = function () {
         var image = scope.$eval(attrs.catalogSliderImage),
          height = element.parents('.fitter:first').height();
          
          element.attr('src', image.serving_url + '=s' + height)
             .width(height * image.proportion)
             .height(height);
             
             element.parents('.item:first')
              .width(height * image.proportion)
              .height(height);
      };
      
      $timeout(run);
  
      if (scope.$last)
      {
        scope.$emit('readyCatalogSlider');
      }
      
      var resize = function () {
        run();
        scope.$emit('reMeasureCatalogSlider');
      };
      
      $(window).bind('resize', resize);
      
      scope.$on('$destroy', function () {
        $(window).off('resize', resize);
      });
      
    }
  };
});