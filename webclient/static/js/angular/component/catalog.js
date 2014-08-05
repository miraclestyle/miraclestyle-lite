MainApp
    .directive('catalogPricetagPosition', function ($timeout) { // directives that are not used anywhere else other than this context are defined in their own context
        return {
            priority: -513,
            link: function (scope, element, attr) {
                /*  
				  ihp - Initial Horizontal Price Tag Position 
				  ivp - Initial Vertical Price Tag Position 
				  iiw - Initial Image Width  
				  iih - Initial Image Height  
				  
				  ciw - Current Image Width  
				  cih - Current Image Height  
				  chp - Current Horizontal Price Tag Position  
				  cvp - Current Vertical Price Tag Position  
				  */

                var resize = function () {
                    var pa = $(element).parents('.catalog-image-scroll:first');

                    var sizes = calculate_pricetag_position(
                        scope.pricetag.position_top,
                        scope.pricetag.position_left,
                        scope.$parent.catalog_image.width,
                        scope.$parent.catalog_image.height,
                        pa.width(),
                        pa.height()
                    );

                    scope.pricetag._position_top = sizes[0];
                    scope.pricetag._position_left = sizes[1];

                    $(element).css({
                        top: scope.pricetag._position_top,
                        left: scope.pricetag._position_left,
                    }); // reposition the perspective based on the db results
                };

                $timeout(resize);

                $(window).on('resize', resize);

                scope.$on('$destroy', function () {
                    $(window).off('resize', resize);
                });
            }
        };
    })
    .directive('loadInfiniteCatalogImages', function () {
        return {
            link: function (scope, element, attr) {
                var scroll = function () {
                    var left = $(element).scrollLeft(),
                        el = $(element).get(0);

                    var maxscroll = el.scrollWidth - el.clientWidth;

                    var sense = maxscroll - left;

                    if(sense < 200) {
                        scope.getMoreImages();
                    }
                };

                $(element).on('scroll', scroll);

                scope.$on('$destroy', function () {
                    $(element).off('scroll', scroll);
                });

            }
        };
    })
    .directive('catalogSlider', function ($timeout) {
        return {
            restrict: 'A',
            priority: -515,
            link: function (scope, element, attr) {

                if(scope.$last === true) {

                    var resize = function () {
                        var that = $(element);

                        var h = that.parents('.modal-body').height();

                        var master = that.parents('.overflow-master:first');

                        var w = 0;

                        master.find('.catalog-image-scroll').each(function () {
                            var img = $(this).find('.img');
                            img.height(h);
                            var cw = $(this).data('width'),
                                ch = $(this).data('height');

                            var neww = new_width_by_height(cw, ch, h);

                            img.width(neww);
                            $(this).width(neww);

                            w += neww;


                        });

                        master.width(Math.ceil(w));
                    };

                    $timeout(function () {
                        resize();
                    });

                    $(window).resize(resize);

                    scope.$on('$destroy', function () {
                        $(window).unbind('resize', resize);
                    });

                }
            }
        };
    })
    .factory('Catalog', ['$rootScope', 'Endpoint', 'EntityEditor', 'Title', '$modal', 'Confirm',

        function ($rootScope, Endpoint, EntityEditor, Title, $modal, Confirm) {

            var kind = '35';
            
            var make_product_scope = function ()
	    	{
	    
		       return {
		        	 'form_info' : {'action' : Endpoint.url},
		        	 'accordions' : {
		        	 	'general' : true,
		        	 },
		        	 'gridConfig' : function (scope)
		              {
		            		return {
		            			margin : 10
		            		};
		             },
		        	 'completed' : function (data)
		        	 { 
		        	 	// append new images
		        	 	console.log(this, data);
		        	 },
 
		            'removeImage' : function (image)
		        	 {
		        	 	image._state = 'deleted';
		       
		        	 },
		        	 'removeContent' : function (content) {
		        	 	content._state = 'deleted';
	 
		        	 },
		        	 'removeVariant' : function (variant)
		        	 {
		        	 	variant._state = 'deleted';
		        	  
		        	 },
		        	 'getMoreProductInstances' : function ()
                      { 
                     
						 var that = this;
						 
						 var out = get_property_options(that.entity, '_products', 1);
		 
						 if (!out._instances.more) return false;
						 
						 out.config.keys = $.map(that.entity._products, function (prod) {
						     return prod.key;
						 });
						 
						 Endpoint.post('read', '35', {'key' : $parentScope.entity.key,
						  							  'read_arguments' : {'_products' : out}
						  							 }).success(function (data) {
					 
								angular.forEach(data.entity._products, function (prod) {
								   var the_prod = _.findWhere(that.entity._products, {key : prod.key});
								   if (the_prod)
								   {
								       the_prod._instances.extend(prod._instances);
								   } 
								});
								
								update(get_property_options(that.entity, '_products'), get_property_options(data.entity, '_products'));
						  });
                     },
		        	 'manageContent' : function (content) { 
		        	 	
		        	 	var $parentScope = this;
		        	 	 
		        	 	var modalInstance = $modal.open({
		                        templateUrl: logic_template('catalog/product/manage_content.html'),
		                        controller: function ($scope, $modalInstance, RuleEngine) {
		 
		                            $scope.content = angular.copy(content ? content : {});
		                      
		                            var new_content = content ? false : true;
		             
		                            $scope.save = function () {
		           
		                                 if (new_content)
		                                 {
		                                 	$parentScope.child.contents.push($scope.content);
		                                 }
		                                 else
		                                 {
		                                 	update(content, $scope.content);
		                                 }
		                                 
		                                 $scope.cancel();
		                            };
		
		                            $scope.cancel = function () {
		                                $modalInstance.dismiss('cancel');
		                            };
		
		                        }
		                    });
		        	 	
		        	  },
		        	 'manageVariant' : function (variant) {
		        	 	
		        	 	var $parentScope = this;
		       
		        	 	var modalInstance = $modal.open({
		                        templateUrl: logic_template('catalog/product/manage_variant.html'),
		                        controller: function ($scope, $modalInstance, RuleEngine) {
		 
		                            $scope.variant = angular.copy(variant ? variant : {});
		          
		                            if ($scope.variant && ('options' in $scope.variant))
		                            {
		                            	$scope.variant._options = $scope.variant.options.join("\n");
		                            }
		                   
		                            var new_variant = variant ? false : true;
		                   
		                            $scope.save = function () {
		                            	
		                            	 if (!this.variant._options) this.variant._options = '';
		                            	 
		                            	 this.variant.options = this.variant._options.split("\n");
		                            	  
		                                 if (new_variant)
		                                 {
		                                 	$parentScope.child.variants.push(this.variant);
		                                 }
		                                 else
		                                 {
		                                 	update(variant, this.variant);
		                                 }
		                                 
		                                 $scope.cancel();
		                            };
		
		                            $scope.cancel = function () {
		                                $modalInstance.dismiss('cancel');
		                            };
		
		                        }
		                    });
		        	 	
		        	  },
		        	  'removeInstance' : function (instance)
		        	  {
		        	  	  instance._state = 'deleted';
		        	  },
	 
		        	  'manageInstance' : function (instance, create)
		        	  {
		        	  	    var $parentScope = this;
		        
		        	  	    var find_child = function(child, entity)
		        	  	    {
		        	  	    	var new_product = _.findWhere(entity._products, {key : $parentScope.child.key});
		        	  	    	var new_instance = _.findWhere(new_product._instances, {key : child.key});
		        	  	    	return new_instance;
		        	  	    };
		        	  	    
		        	  	    var complete_upload = function (data) {
		                	 	var images = find_child(this.child, data.entity).images;
		                	 	
		                	 	if (images)
		                	 	{
		                	 		this.child.images = images;
		                	 	}
				             };
				              
		        	  	     var cfg = {
			                	 'kind' : kind,
			                	 'close' : false,
			                	 'parentScope' : $parentScope,
			                	 'scope' : angular.extend(make_product_scope(), {
			                	 	'completed' : complete_upload,
			                	 }),
			                	 'update_child' : function (data) {
							        var find = {key : $parentScope.child.key};
			        	  	    	var new_product = _.findWhere(data.entity._products, find);
			        	  	    	var found = _.last(new_product._instances);
			        	  	    	update(this.child, found);
			        	  	    	
			        	  	    	$parentScope.child._instances = new_product._instances;
							      },
			                	 'get_child' : function ()
			                	 {
			                	 	var prod = _.findWhere(this.entity._products, {key : $parentScope.child.key});
			                	 	this.child = instance;
			                	 	prod._instances.push(this.child);
			                	 },
			                	 'handle' : function (data)
						         {
						             this.uploadConfig = $parentScope.uploadConfig;
						         },
			                    'templateUrl' : logic_template('catalog/product/manage_instance.html'),
			                  };
			                  
			                  var update_cfg = {};
			                  update_cfg['close'] = true;
			        		  update_cfg['get_child'] = function ()
			        		  {
			        		  	  this.child = find_child(instance, this.entity);        	 	 
			        		  };
			        		  update_cfg['update_child'] = function (data)
			        		  {
			        		  	  var find = {key : $parentScope.child.key};
			        		  	  update(this.child, find_child(this.child, data.entity));
			        		  	  var new_product = _.findWhere(data.entity._products, find);
			        		  	  $parentScope.child._instances = new_product._instances;
			        		  };
			               
			                  if (create) {
			                  	
	           					cfg['options_after_update'] = update_cfg;
	           					
			        		  	EntityEditor.create(cfg);
			        		  	
			        		  }
			        		  else
			        		  {
			        		  	update(cfg, update_cfg);
			        		  	EntityEditor.update(cfg);
			        		  }
		        	   
		        	  },
		        	  'newInstance' : function ()
		        	  {
		        	  	
						var $parentScope = this;
		        	 	 
		        	 	var modalInstance = $modal.open({
		                        templateUrl: logic_template('catalog/product/create_instance.html'),
		                        controller: function ($scope, $modalInstance, RuleEngine) {
		  							
		  							$scope.variants = [];
		  				 
		  							angular.forEach($parentScope.child.variants, function (v) {
		 
		  								$scope.variants.push({
		  									'name' : v.name,
		  									'options' : v.options,
		  									'option' : null,
		  								});
		  							});
		  							
		                            $scope.save = function () {
		                            	 
		                            	 var variant_signature = [];
		                            	 angular.forEach($scope.variants, function (v) {
		                            	 	var d = {};
		                            	 	d[v.name] = v.option;
		                            	 	variant_signature.push(d);
		                            	 });
		                            	 
		                            	 var manage = false;
		                            	 
		                            	 angular.forEach($parentScope.child._instances, function (inst) {
		                            	 	if (inst.variant_signature == variant_signature)
		                            	 	{
		                            	 		$parentScope.manageInstance(inst);
		                            	 		
		                            	 		manage = true;
		                            	 	}
		                            	 });
		                            	 
		                            	 if (!manage)
		                            	 {
		                            	 	$parentScope.manageInstance({'variant_signature' : variant_signature}, 1);
		                            	 }
		                            	   
		                            };
		
		                            $scope.cancel = function () {
		                                $modalInstance.dismiss('cancel');
		                            };
		
		                        }
		                    });
		        	  }, 
		        	 _do_user_admin : function (entity, action) {
		        	 	
		        	 	    var $parentScope = this;
	
	                        var handle = function () {
	
	                            var modalInstance = $modal.open({
	                                templateUrl: logic_template('catalog/product/user_admin.html'),
	                                windowClass: 'modal-medium',
	                                controller: function ($scope, $modalInstance, RuleEngine, $timeout) {
	                               
	                                    $scope.rule = $parentScope.rule;
	                                    $scope.action = action;
	                                    $scope.log = {
	                                        'message': '',
	                                        'key': $parentScope.entity.key,
	                                        'state' : $parentScope.entity.state,
	                                        'note' : '',
	                                    };
	
	                                    $scope.save = function () {
	
	                                        Endpoint.post(action, $parentScope.entity.kind, $scope.log)
	                                            .success(function (data) {
	
	                                                EntityEditor.update_entity($parentScope, data, ['_images']);
	
	                                                $scope.cancel();
	
	                                            });
	
	                                    };
	
	                                    $scope.cancel = function () {
	                                        $modalInstance.dismiss();
	                                    };
	                                }
	                            });
	
	                        };
	
	                        handle();
	
	                    },
	                    
	                    duplicate : function()
	                    {
	                    	this._do_user_admin(this.entity, 'duplicate');
	                    },
		      		  
		    	};
	    	 
	    	};

            var make_scope = function ()
            {
            	return {
            	'accordions' : {
            		'general' : true,
            		'products' : false,
            		'embed' : false,
            	},
            	'gridConfig' : function (scope)
            	{
            		scope.$watch('accordions.products', function (new_value, old) {
            			if (new_value)
            			{
            				$(window).trigger('gridinit');
            			}
            			
            		});
            		
            		return {
            			margin : 10
            		};
            	},
                'datepickOptions': {
                   'showWeeks': false,
                },
                'form_info': {
                    'action': Endpoint.url
                },
                'completed': function (data) {
					 
					if (!this.entity._images) this.entity._images = [];
					this.entity._images.extend(data.entity._images);
                },
                'removeImage': function (image) {
                	image._state = 'deleted';
                },
                'getMoreImages': function () {
		 
					 var that = this;
					 
					 var config = get_property_options(that.entity, '_images');
					 
					 if (!config.more) return false;
					 
					 Endpoint.post('read', '35', {'key' : that.entity.key,
					  								'read_arguments' : {'_images' : {
					  									'config' : config,
					  			   }}}).success(function (data) {
					  		 
							that.entity._images.extend(data.entity._images);
							update(get_property_options(that.entity, '_images'), get_property_options(data.entity, '_images'))
					  });
					 
					 
                },
             
            };
            
            };
			
			var make_update_scope = function (){
				
                return {
                	
                
                'kind': kind,
                'scope': make_scope(),
                'handle': function (data) {
                	
                    var $parentScope = this;
                    
                    $parentScope.uploadConfig = {
                       'action' : 'prepare',
                       'kind' : kind,
			           'args' : {
			              'domain' : $parentScope.entity.namespace,
			           }
			        };
 
                    this.addProducts = function () {
                    	
                        var handle = function () {

                            var modalInstance = $modal.open({
                                templateUrl: logic_template('catalog/products.html'),
                                controller: function ($scope, $modalInstance, RuleEngine, $timeout) {
                                	
                                	$scope.getMoreProducts = function ()
                                	{ 
											 var that = this;
											 
											 var config = get_property_options(that.entity, '_products');
											 
											 if (!config.more) return false;
											 
											 Endpoint.post('read', '35', {'key' : $parentScope.entity.key,
											  								'read_arguments' : {'_products' : {
											  									'config' : config,
											  			   }}}).success(function (data) {
											  		 
													that.entity._products.extend(data.entity._products);
													update(get_property_options(that.entity, '_products'), get_property_options(data.entity, '_products'));
											  });
                                	};
 
                                    $scope.manageProduct = function (product) {
                                    	
                                    	var find_child = function(child, entity)
					        	  	    { 
					        	  	    	return _.findWhere(entity._products, {key : child.key});
					        	  	    };
                                    	
                                    	var complete_upload = function (data) {
					              
					                	 	this.child.images = find_child(this.child, data.entity).images;
							             };
							             
							             var update_child = function(data)
							             {
							             	update(this.child, find_child(this.child, data.entity));
							             };
							             
							             var update_cfg = {
								                	 'kind' : kind,
								                	 'scope' : angular.extend(make_product_scope(), {
								                	 	'completed' : complete_upload,
								                	 }),
								                	 'update_child' : update_child,
								                	 'parentScope' : $scope,
								                	 'get_child' : function ()
								                	 {
								                	 	var that = this;
								                	 	this.child = find_child(product, this.entity);
								                	 },
								                	 'handle' : function (data)
											         {
											             this.uploadConfig = $parentScope.uploadConfig;
											         },
								                	 'templateUrl' : logic_template('catalog/product/manage.html')
								                };
                                      
                                    	 if (!product)
                                    	 {
                                    	 	return EntityEditor.create({
							               		 'close' : false,
							                	 'kind' : kind,
							                	 'parentScope' : $scope,
							                	 'scope' : angular.extend(make_product_scope(), {
								                	'completed' : complete_upload,
								                 }),
							                	 'get_child' : function ()
							                	 {
							                	 	this.child = {};
							                	 	this.entity._products.push(this.child);
							                	 },
							                	 'update_child' : function (data) {
							                	 	
							                	 	var found = _.last(data.entity._products);
							        	  	    	 
							                	 	update(this.child, found);
							                	 },
							                	 'handle' : function (data)
										         {
										             this.uploadConfig = $parentScope.uploadConfig;
										         },
										         'options_after_update' : update_cfg,
							                	 'templateUrl' : logic_template('catalog/product/manage.html'),
							                });
                                    	 }
                                    	 else
                                    	 {
                                    	 	return EntityEditor.update(update_cfg);
                                    	 }
                                         
                                    };
                                    
                                    $scope.getMoreImages = $parentScope.getMoreImages;
                                   
                                    $scope.rule = $parentScope.rule;
                                    $scope.live_entity = $parentScope.entity;
                                    $scope.entity = angular.copy($scope.live_entity);
 
                                    $scope.onDrop = function (event, ui, catalog_image) {
                                        var pricetags = catalog_image.pricetags;
                                        var pricetag = pricetags[pricetags.length - 1];
                                        var target_drop = $(event.target);

                                        var posi = target_drop.offset();
                                        var posi2 = ui.offset;

                                        if('key' in pricetag) {
                                            pricetag['_key'] = pricetag['key'];

                                            delete pricetag['key'];
                                        }

                                        pricetag['_position_top'] = posi2.top - posi.top;
                                        pricetag['_position_left'] = posi2.left - posi.left;

                                        var sizes = calculate_pricetag_position(
                                            pricetag['_position_top'],
                                            pricetag['_position_left'],
                                            target_drop.width(),
                                            target_drop.height(),
                                            catalog_image.width,
                                            catalog_image.height
                                        ); // reverse the position perspective

                                        pricetag['position_top'] = sizes[0];
                                        pricetag['position_left'] = sizes[1];

                                        pricetag['product_template'] = pricetag['_key'];
                                        pricetag['value'] = pricetag['unit_price'];

                                    };

                                    $scope.onStop = function (event, ui, pricetag) {
                                        pricetag['_position_top'] = ui.position.top;
                                        pricetag['_position_left'] = ui.position.left;

                                        var target = $(event.target).parents('.catalog-image-scroll:first');

                                        var sizes = calculate_pricetag_position(
                                            pricetag['_position_top'],
                                            pricetag['_position_left'],
                                            target.width(),
                                            target.height(),
                                            target.data('width'),
                                            target.data('height')
                                        ); // reverse the position perspective

                                        pricetag['position_top'] = sizes[0];
                                        pricetag['position_left'] = sizes[1];
                                    };

                                    

                                    $scope.save = function () {
                     
                                        update($scope.live_entity, $scope.entity);
                           
                                        $scope.cancel();

                                    };

                                    $scope.cancel = function () {
                                        $modalInstance.dismiss();
                                    };
                                }
                            });

                        };
                         
                        handle();
  
                    };

                    this._do_user_admin = function (entity, action) {

                        var handle = function () {

                            var modalInstance = $modal.open({
                                templateUrl: logic_template('catalog/user_admin.html'),
                                windowClass: 'modal-medium',
                                controller: function ($scope, $modalInstance, RuleEngine, $timeout) {
                              

                                    $scope.rule = $parentScope.rule;
                                    $scope.action = action;
                                    $scope.log = {
                                        'message': '',
                                        'key': $parentScope.entity.key,
                                        'state' : $parentScope.entity.state,
                                        'note' : '',
                                    };

                                    $scope.save = function () {

                                        Endpoint.post(action, $parentScope.entity.kind, $scope.log)
                                            .success(function (data) {

                                                EntityEditor.update_entity($parentScope, data, ['_images']);

                                                $scope.cancel();

                                            });

                                    };

                                    $scope.cancel = function () {
                                        $modalInstance.dismiss();
                                    };
                                }
                            });

                        };

                        handle();

                    };
                    
                    this.duplicate = function()
                    {
                    	this._do_user_admin(this.entity, 'duplicate');
                    };

                    this.publish = function () {
                        this._do_user_admin(this.entity, 'publish');
                    };

                    this.discontinue = function () {
                        this._do_user_admin(this.entity, 'discontinue');
                    };

                    this.lock = function () {
                        this._do_user_admin(this.entity, 'lock');
                    };
                    
                    this.sudo = function ()
                    {
                    	this._do_user_admin(this.entity, 'sudo');
                    };

                    this.sortableOptions = {
                        'forcePlaceholderSize': true,
                        'placeholder': 'image-image image-image-placeholder grid-item',
                        'stop': function (e, u) {
  							 
                        }
                    };

                },
                'templateUrl': logic_template('catalog/manage.html'),
            };
            
            };
            
            var catalog_read_arguments = {
                            	'_images' : {},
                            	'_products' : {
                            		'_instances' : {
                            		},
                            	},
                           };
             
            return {

                create: function (domain_key, complete) {
                    return EntityEditor.create({
                        'kind': kind,
                        'entity': {},
                        'scope': make_scope(),
                        'close': false,
                        'handle': function (data) {
                        	this.entity.domain = this.entity.namespace;
                            this.uploadConfig = {
					           'args' : {
					              'domain' : this.entity.domain,
					              }
					        };
                        },
                        'complete': complete,
                        'options_after_update': make_update_scope(),
                        'templateUrl': logic_template('catalog/manage.html'),
                        'args': {
                            'domain': domain_key,
                            'read_arguments' : catalog_read_arguments,
                        }
                    });

                },
                update: function (entity, complete) {
                    return EntityEditor.update(angular.extend({
                        'entity': entity,
                        'complete': complete,
                        'args': {
                            'key': entity.key,
                            'read_arguments' : catalog_read_arguments,
                        }
                    }, make_update_scope()));
                }

            };

        }
    ]);