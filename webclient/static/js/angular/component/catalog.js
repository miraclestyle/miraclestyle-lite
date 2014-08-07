MainApp
    .directive('catalogPricetagPosition', function ($timeout) { // directives that are not used anywhere else other than this context are defined in their own context
        return {
            priority: -513,
            link: function (scope, element, attr) {
  
                var resize = function () {
                    var pa = $(element).parents('.catalog-image-scroll:first');

                    var sizes = calculate_pricetag_position(
                        scope.pricetag.position_top,
                        scope.pricetag.position_left,
                        scope.pricetag.image_width,
                        scope.pricetag.image_height,
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
                    
                    var that = $(element);

                    var resize = function () {
                         
                        var h = that.parents('.modal-body').height();

                        var master = that.parents('.overflow-master:first');

                        var w = 0;

                        master.find('.catalog-image-scroll').each(function () {
                            var img = $(this).find('.img');
                            img.height(h);
                            w += img.width();
                        });

                        master.width(Math.ceil(w));
                    };
                    
                    that.parents('.overflow-master:first').find('.catalog-image-scroll .img').load(resize);

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
    .factory('Catalog', ['$rootScope', 'Endpoint', 'EntityEditor', 'Title', '$modal', 'Confirm', '$timeout',

        function ($rootScope, Endpoint, EntityEditor, Title, $modal, Confirm, $timeout) {

            var kind = '35';
            
 
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
					
					if (data.entity && data.entity._images)
					{
					    this.entity._images.extend(data.entity._images);
					}
					
                },
                'removeImage': function (image) {
                	image._state = 'deleted';
                },
                'getMoreImages': function () {
		 
					 var that = this;
					 
					 that.entity._next_read_arguments._images.config['order'] = that.entity._read_arguments._images.config['order'];
					 
	 
					 EntityEditor.read_entity_partial(that.entity, {
					      '_images' : that.entity._next_read_arguments._images,
					 }, function (data) {
 
                            if (data.entity && data.entity._images)
                            {
                                that.entity._images.extend(data.entity._images);
                            }
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
									    
									    EntityEditor.read_entity_partial(that.entity, {
                                              '_products' : that.entity._next_read_arguments._products,
                                         }, function (data) {
                     
                                                if (data.entity && data.entity._products)
                                                {
                                                    that.entity._products.extend(data.entity._products);
                                                }
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
											             var that = this;
											              
											             that.uploadConfig = $parentScope.uploadConfig;
											              
                                                         that.sortableOptions = {
                                                            'forcePlaceholderSize': true,
                                                            'placeholder': 'image-image image-image-placeholder grid-item',
                                                            'stop': function (event, ui) {
                                                                 angular.forEach(that.child.images, function (o, i) {
                                                                     o._sequence = i;
                                                                 });
                                                             }
                                                         }; 
											            
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
                                    	    
                                    	    EntityEditor.update(update_cfg);
                                    	      
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

                                        pricetag['position_top'] = posi2.top - posi.top;
                                        pricetag['position_left'] = posi2.left - posi.left;
                                        pricetag['image_width'] = target_drop.width();
                                        pricetag['image_height'] = target_drop.height();
                                        
                                        pricetag._position_top = pricetag.position_top;
                                        pricetag._position_left = pricetag.position_left;
 
                                        pricetag['product_template'] = pricetag['_key'];
                                        pricetag['value'] = pricetag['unit_price'];

                                    };

                                    $scope.onStop = function (event, ui, pricetag) {
                                        
                                         var target = $(event.target).parents('.catalog-image-scroll:first');
                                        
                                        pricetag['position_top'] = ui.position.top;
                                        pricetag['position_left'] = ui.position.left;
                                        pricetag['image_width'] = target.width();
                                        pricetag['image_height'] = target.height();
                                        
                                        pricetag._position_top = pricetag.position_top;
                                        pricetag._position_left = pricetag.position_left;
 
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
                         
                        EntityEditor.read_entity_partial($parentScope.entity, {
                               '_products' : {
                                   '_instances' : {},
                               },
                         }, function (data) {
                                  
                                if (data.entity && data.entity._products)
                                {
                                    $parentScope.entity._products = data.entity._products;
                                }
                                
                                handle();
                         });
  
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

                                                EntityEditor.update_entity($parentScope, data, ['_images', '_products']);

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
                    	this._do_user_admin(this.entity, 'catalog_duplicate');
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
                    
                    var that = this;

                    this.sortableOptions = {
                        'forcePlaceholderSize': true,
                        'placeholder': 'image-image image-image-placeholder grid-item',
                        'stop': function (event, ui) {
  							 angular.forEach(that.entity._images, function (o, i) {
  							     o.sequence = i;
  							 });
                        }
                    };

                },
                'templateUrl': logic_template('catalog/manage.html'),
              };
            
            };
            
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
                         if (!this.child.images) this.child.images = [];
                         
                         if (data.entity && data.entity._products)
                         {
                             var images = _.findWhere(data.entity._products, {key : this.child.key}).images;
                             this.child.images.extend(images);
                         }
                         
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
                     'getMoreProductInstances' : function (singular)
                      { 
                     
                         var that = this;
                         
                         var read_args = that.entity._read_arguments;
                         var new_read_args = {
                             '_products' : {
                                 'config' : read_args['_products']['config'],
                                 '_instances' : (!singular ? that.entity._next_read_arguments._products._instances : that.entity._read_arguments._products._instances),
                             }
                         };
                         
                         var cf = new_read_args['_products']['config'];
                         
                         if (!cf)
                         {
                             cf = {'keys' : []};
                             new_read_args['_products']['config'] = cf;
                         }
                         else
                         {
                             if (!cf['keys']) cf['keys'] = [];
                              
                         }
                         
                         cf['keys'].push(that.child.key);
                         
                     
                         EntityEditor.read_entity_partial(that.entity, new_read_args, function (data) {
                     
                                if (data.entity && data.entity._products)
                                {
                                    var new_prod = _.findWhere(data.entity._products, {key : that.child.key});
                                    if (new_prod)
                                    {
                                        that.child._instances.extend(new_prod._instances);
                                    }
                                }
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
                                    if (!prod._instances) prod._instances = [];
                                    prod._instances.push(this.child);
                                 },
                                 'handle' : function (data)
                                 {
                                     var that = this;
                                     
                                     that.uploadConfig = $parentScope.uploadConfig;
                                      
                                     that.sortableOptions = {
                                        'forcePlaceholderSize': true,
                                        'placeholder': 'image-image image-image-placeholder grid-item',
                                        'stop': function (event, ui) {
                                             angular.forEach(that.child.images, function (o, i) {
                                                 o._sequence = i;
                                             });
                                         }
                                     }; 
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
                                        
                                            if (JSON.stringify(inst.variant_signature) == JSON.stringify(variant_signature))
                                            {
                                                $parentScope.manageInstance(inst);
                                                
                                                manage = true;
                                            }
                                         });
                                         
                                         if (!manage)
                                         {
                                            $parentScope.manageInstance({'variant_signature' : variant_signature}, 1);
                                         }
                                         
                                         $scope.cancel();
                                           
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
    
                                                    EntityEditor.update_entity($parentScope, data, ['_images', '_products']);
    
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
                            var that = this;
                            Confirm.sure(null, null, {
                                message : 'Are you sure you want to proceed with this action?',
                                callbacks : {
                                    Yes : function () {
                                
                                         Endpoint.post('product_duplicate', that.entity.kind, {
                                             key : that.entity.key,
                                             product : that.child.key,
                                             read_arguments : that.entity._read_arguments
                                         }).success(function (data) {
                                            if (data['entity'])
                                            {
                                                var modal = Confirm.notice('Duplication process started, you will be notified when its done.');
                                                
                                                $timeout(function () {
                                                        try
                                                        {
                                                            modal.dismiss();
                                                            
                                                        }catch(e) {}
                                                        
                                                    }, 1500);
                                                
                                            }
                                        });
                                    },
                         
                                },
                             
                            });
                        },
                      
                };
             
            };
            
            var catalog_read_arguments = {
                            	'_images' : {
                            	    'config' : {
                            	        'order' : {
                            	            'field' : 'sequence',
                            	            'direction' : 'asc',
                            	        },
                            	    }
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
                                   'action' : 'prepare',
                                   'kind' : kind,
                                   'args' : {
                                      'domain' : this.entity.namespace,
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