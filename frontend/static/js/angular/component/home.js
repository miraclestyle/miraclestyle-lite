MainApp
.directive('homepageGrid', ['MAX_GRID_WIDTH', 'MIN_GRID_WIDTH', function(MAX_GRID_WIDTH, MIN_GRID_WIDTH) {
	return {
		link : function (scope, element, attr)
		{
			if (scope.$last)
			{
				
			
			 var resize = function ()
			 {
			 
			 	var wrapper = $(element).parents('.grid-wrapper'); 
				var canvas_width = wrapper.width();
				var calc = calculate_grider(canvas_width, MAX_GRID_WIDTH, MIN_GRID_WIDTH);
				/*
				    values[0] = rounded;
				    values[1] = sides;
				    values[2] = cover_width;
				    values[3] = cover_count;
				 * */
				 
				var r = calc[1] / 2;
				wrapper.css({
					marginRight : r,
					marginLeft : r,
				});
				
				var item = wrapper.find('.grid-item');
				wrapper.find('.grid-item').each(function () {
				    var catalog = $(this).scope().catalog;
				    item.width(calc[0]).height(calc[0]/(parseInt(catalog.cover.proportion)));
				});
				
				
			 	
			 };
			 
			 resize();
			 
			 $(window).bind('resize', resize);
			 
			 scope.$on('$destroy', function () {
			 	$(window).unbind('resize', resize);
			 });
			 
			 
			
			}
		 
		}
	};
}])
.controller('HomePage', ['$scope', 'Title', 'Endpoint', '$modal', 'EntityEditor',
    function ($scope, Title, Endpoint, $modal, EntityEditor) {
    
    $scope.catalogs = [];
    
    Endpoint.post('public_search', '31', {'search' : {'filters' : [], 'kind' : '31', 'orders' : [{"field": 'created',"operator": 'desc'}]}}).success(function (data) {
    	$scope.catalogs = data.entities;
    });
     
    $scope.viewCatalog = function (catalog)
    {
        Endpoint.post('read', '31', {
            'key' : catalog.key,
            'read_arguments' : {
                '_images' : {},
            },
        }).success(function (data) {
            
            var modalInstance = $modal.open({
                                templateUrl: logic_template('home/view_catalog.html'),
                                controller: function ($scope, $modalInstance, RuleEngine, $timeout) {
                                    
                                    var $parentScope = $scope;
                                    $scope.entity = data.entity;
                                    $scope.rule = RuleEngine.factory(data.entity);
                                     
                                    $scope.viewProduct = function(pricetag)
                                    { 
                                        Endpoint.post('read', '31', {
                                            'key' : catalog.key,
                                            'read_arguments' : {
                                                '_products' : {
                                                    'config' : {
                                                        'keys' : [pricetag.product],
                                                    },
                                                    '_product_category' : {},
                                                    '_weight_uom' : {},
                                                    '_volume_uom' : {},
                                                    '_instances' : {
                                                        '_product_category' : {},
                                                        '_weight_uom' : {},
                                                        '_volume_uom' : {},
                                                    },
                                                },
                                            },
                                        }).success(function (data) {
                                             
                                            $modal.open({
                                                templateUrl: logic_template('home/view_product.html'),
                                                controller: function ($scope, $modalInstance, RuleEngine, $timeout) {
                                                    
                                                    $scope.rule = RuleEngine.factory(data.entity);
                                                    $scope.entity = data.entity;
                                                    $scope.child = _.findWhere($scope.entity._products, {key : pricetag.product});
                                                    $scope.current_variant = null;
                                                    $scope.product_key = $scope.child.key;
                                                    
                                                    $scope.original_child = angular.copy($scope.child);
                                                    
                                                    $scope.variant_combo = {};
                                                    
                                                    angular.forEach($scope.child.variants, function (v) {
                                                        $scope.variant_combo[v.name] = null;
                                                    });
                                                    
                                                    $scope.addToCart = function ()
                                                    {
                                                        Endpoint.post('read', '19', {
                                                            'account': current_account.key
                                                        }).success(function (buyer) {
                                                            
                                                            Endpoint.post('add_to_cart', '34', {
                                                                'buyer': buyer.entity.key,
                                                                'product': $scope.product_key,
                                                                'variant_signature': $scope.current_variant,
                                                            }).success(function (data) {
                                                                console.log(data);
                                                            });
                                                            
                                                            
                                                        });
                                                    };
                                                    
                                                    $scope.changeProductView = function ()
                                                    {
                                                        var packer = [];
                                                        
                                                        angular.forEach($scope.variant_combo, function (v, k) {
                                                             var d = {};
                                                             d[k] = v;
                                                             packer.push(d);
                                                        });
                                                        angular.forEach($scope.child._instances, function (instance) {
                                                            if (JSON.stringify(instance.variant_signature) == JSON.stringify(packer))
                                                            {
                                                                $scope.current_variant = packer;
                                                                angular.forEach(instance, function (v, k) {
                                                                   if (typeof v != undefined)
                                                                   {
                                                                       $scope.child[k] = v;
                                                                   } 
                                                                });
                                                            }
                                                            else
                                                            {
                                                                update($scope.child, $scope.original_child);
                                                            }
                                                        
                                                        });
                                                    };
                                                    
                                                    
                                                    
                                                    $scope.cancel = function () {
                                                        $modalInstance.dismiss();
                                                    };
                                                }
                                            });
                                        
                                         });
                                    };
                                    
                                    $scope.getMoreImages = function () {
                                 
                                             var that = this;
                                             
                                             if (!that.entity._next_read_arguments._images.config.more) return false;
                         
                                             EntityEditor.read_entity_partial(that.entity, {
                                                  '_images' : that.entity._next_read_arguments._images,
                                             }, function (data) {
                         
                                                    if (data.entity && data.entity._images)
                                                    {
                                                        that.entity._images.extend(data.entity._images);
                                                    }
                                             });
                                              
                                    };

                                    $scope.cancel = function () {
                                        $modalInstance.dismiss();
                                    };
                                }
               });
        });  
    };
    
}])
.run(['$rootScope',
     function ($rootScope) {
	
		$rootScope.toggleMainMenu = function (hide)
		{
			var mm = $('#main-menu');
			
			if (mm.is(':visible') || hide)
			{
				mm.stop().animate({
					height : '0px'
				}, 400, function () {
					$(this).hide();
				});
			}
			else
			{
				mm.show();
				mm.stop().animate({
					height : ($(window).height() - $('#top-bar').height()) + 'px',
				}, 400, function () {
					
				});
			}		
		};
  
}]);