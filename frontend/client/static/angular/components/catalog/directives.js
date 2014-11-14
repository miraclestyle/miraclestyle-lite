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
        element.find('.item').each(function () {
          tw += $(this).width();
        });
   
        element.width(Math.ceil(tw));
      };
      
      scope.$on('reMeasureCatalogSlider', function () {
        measure();
      });
  
      scope.$on('readyCatalogSlider', function () {
        
          measure();
          
          parent.kinetic({
            y:false,
            cursor: false,
            maxvelocity: 60,
            moved: tryToLoad,
            stopped: tryToLoad
          });
        
      });
    }
  }
}).directive('catalogSliderImage', function ($timeout) {
  return {
    restrict: 'A',
    link: function (scope, element, attrs) {
      
      var image = scope.$eval(attrs.catalogSliderImage);
      
      var run = function () {
         var newHeight = element.parents('.fitter:first').height(),
          newWidth = newHeight * image.proportion;
 
          element.attr('src', image.serving_url + '=s' + newHeight) // @todo the height range needs to be calculated here
             .width(newWidth)
             .height(newHeight);
             
             element.parents('.item:first')
              .width(newWidth)
              .height(newHeight);
      };
      
      $timeout(function () {
        run();
        if (scope.$last)
        {
          scope.$emit('readyCatalogSlider');
        }
      });
  
     
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