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
                        scope.getImages();
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
    .factory('Catalog', ['$rootScope', 'Endpoint', 'EntityEditor', 'Title', 'Product', '$modal', 'Confirm',

        function ($rootScope, Endpoint, EntityEditor, Title, Product, $modal, Confirm) {

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
		        	 'manageContent' : function (content) { 
		        	 	
		        	 	var that = this;
		        	 	 
		        	 	var modalInstance = $modal.open({
		                        templateUrl: logic_template('product/manage_content.html'),
		                        controller: function ($scope, $modalInstance, RuleEngine) {
		 
		                            $scope.content = angular.copy(content ? content : {});
		                      
		                            var new_content = content ? false : true;
		             
		                            $scope.save = function () {
		           
		                                 if (new_content)
		                                 {
		                                 	that.entity.contents.push($scope.content);
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
		        	 	
		        	 	var that = this;
		        	 	 
		        	 	var modalInstance = $modal.open({
		                        templateUrl: logic_template('product/manage_variant.html'),
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
		                                 	that.entity.variants.push(this.variant);
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
		        	  	
		        	  	  var that = this;
		        	  	  
		        	  	  instance._state = 'deleted';
		        	  },
	 
		        	  'manageInstance' : function (instance, create)
		        	  {
		        	  	    var that = this;
		        	  	    
		        	  	    if (!instance) instance = {'images' : [], 'contents' : []};
		          
		        	  	    var cfg = {
			                	 'kind' : kind,
			                	 'close' : false,
			                	 'entity' : instance,
			                	 'data' : {'entity' : instance},
			                	 'scope' : angular.extend(make_product_scope(), {}),
			                	 'handle' : function (data)
						         { 
	  
						         },
			                	 'templateUrl' : logic_template('product/manage_instance.html'),
			               };
			               
			               if (create) {
	          
			        		  	cfg['args'] = create;
			        		  	cfg['complete'] = function (entity)
			        		  	{
			        		  		angular.forEach(that.entity._instances, function (e) {
			        		  			if (e.key == entity.key)
			        		  			{
			        		  				 create = false;
			        		  			}
			        		  		});
			        		  		
			        		  	    if (create)
			        		  	    {
			        		  	    	that.entity._instances.push(entity);
			        		  	    }
			        		  		
			        		  	};
			        		  	
			        		  	EntityEditor.create(cfg);
			        		  }
			        		  else
			        		  {
			        		  	cfg['close'] = true;
			        		  	EntityEditor.update(cfg);
			        		  }
		        	   
		        	  },
		        	  'newInstance' : function ()
		        	  {
		        	  	
						var that = this;
		        	 	 
		        	 	var modalInstance = $modal.open({
		                        templateUrl: logic_template('product/create_instance.html'),
		                        controller: function ($scope, $modalInstance, RuleEngine) {
		  							
		  							$scope.variants = [];
		  				 
		  							angular.forEach(that.entity.variants, function (v) {
		 
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
		                            	 
		                            	 
		                            	 //@todo fetch the dialog
		                            	 
		                            	 console.log(variant_signature);
		                            	   
		                            };
		
		                            $scope.cancel = function () {
		                                $modalInstance.dismiss('cancel');
		                            };
		
		                        }
		                    });
		        	  }, 
		        	 _do_user_admin : function (entity, action) {
		        	 	
		        	 	    var that = this;
	
	                        var handle = function () {
	
	                            var modalInstance = $modal.open({
	                                templateUrl: logic_template('product/user_admin.html'),
	                                windowClass: 'modal-medium',
	                                controller: function ($scope, $modalInstance, RuleEngine, $timeout) {
	                               
	                                    $scope.rule = that.rule;
	                                    $scope.action = action;
	                                    $scope.log = {
	                                        'message': '',
	                                        'key': that.entity['key'],
	                                        'state' : that.entity['state'],
	                                        'note' : '',
	                                    };
	
	                                    $scope.save = function () {
	
	                                        Endpoint.post(action, that.entity['kind'], $scope.log)
	                                            .success(function (data) {
	
	                                                EntityEditor.update_entity(that, data, ['_images']);
	
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
                    
					// @todo complete upload logic
                },
                'removeImage': function (image) {
                	image._state = 'deleted';
                },
                'getImages': function () {
                    var that = this;
					 // @todo missing logic for get more images
                },
             
            };
            
            };
			
			var make_update_scope = function (){
				
                return {
                	
                'kind': kind,
                'scope': make_scope(),
                'handle': function (data) {
                	
                    var that = this;
                    
                    this.uploadConfig = {
			           'args' : {
			              'domain' : this.entity.namespace,
			           }
			        };
 
                    this.addProducts = function () {
                    	
                        var handle = function () {

                            var modalInstance = $modal.open({
                                templateUrl: logic_template('catalog/products.html'),
                                //windowClass: 'modal-medium',
                                controller: function ($scope, $modalInstance, RuleEngine, $timeout) {
 
                                    $scope.manageProduct = function (product) {
                                    	 
                                    	 if (!product)
                                    	 {
                                    	 	return EntityEditor.create({
							               		 'close' : false,
							                	 'kind' : kind,
							                	 'entity' : {},
							                	 'scope' : make_product_scope(),
							                	 'handle' : function (data)
										         {
										             
										         },
							                	 'complete' : function (entity) {
							                	 	
							                	 },
							                	 'templateUrl' : logic_template('product/manage.html'),
							                	 'args' : {
							                	 	'domain' : that.entity.namespace,
							                	 }
							                });
                                    	 }
                                    	 else
                                    	 {
                                    	 	return EntityEditor.update({
								                	 'kind' : kind,
								                	 'entity' : product,
								                	 'scope' : make_scope(),
								                	 'data' : {'entity' : product},
								                	 'handle' : function (data)
											         {
											             
											         },
								                	 'complete' : function (data)
								                	 {
								                	 	// @todo
								                	 	
								                	 	console.log(data); 
								                	 	
								                	 },
								                	 'templateUrl' : logic_template('product/manage.html')
								                });
                                    	 }
                                         
                                    };
                                   
                                    $scope.rule = that.rule;
                                    $scope.live_entity = that.entity;
                                    $scope.entity = angular.copy(that.entity);
 
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
                                    	
                                    	console.log($scope.entity);

                                        update($scope.live_entity, $scope.entity);
                                        
                                        console.log(that, that.live_entity, $scope.live_entity);

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
                              

                                    $scope.rule = that.rule;
                                    $scope.action = action;
                                    $scope.log = {
                                        'message': '',
                                        'key': that.entity['key'],
                                        'state' : that.entity['state'],
                                        'note' : '',
                                    };

                                    $scope.save = function () {

                                        Endpoint.post(action, that.entity['kind'], $scope.log)
                                            .success(function (data) {

                                                EntityEditor.update_entity(that, data, ['_images']);

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
                        }
                    });

                },
                update: function (entity, complete) {
                    return EntityEditor.update(angular.extend({
                        'entity': entity,
                        'complete': complete,
                        'args': {
                            'key': entity['key'],
                            'read_arguments' : {
                            	'_images' : {},
                            	'_products' : {
                            		'_instances' : {},
                            	},
                            },
                        }
                    }, make_update_scope()));
                }

            };

        }
    ]);