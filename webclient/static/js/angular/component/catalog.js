MainApp.factory('Catalog', ['$rootScope', 'Endpoint', 'EntityEditor', 'Title', 'Product', '$modal', 'Confirm',

    function ($rootScope, Endpoint, EntityEditor, Title, Product, $modal, Confirm) {
    	
    	
    	var kind = '35';
    	  
        var scope = {
        	 'datepickOptions' : {
        	 	'showWeeks' : false,
        	 },
        	 'form_info' : {
        	 	'action' : Endpoint.url
        	 },
        	 'completed' : function (data)
        	 {
        	 	this.entity._images.extend(data['entity']['_images']);
        	 	this.entity.start_images = this.entity._images.length;
        	 },
        	 'removeImage' : function (image)
        	 {
        	 	this.entity._images.remove(image);
        	 },
        	 'getImages': function ()
        	 {	
        	 	var that = this;
        	 	
        	 	if (that.entity.more_images && !that.entity.loading_new)
        	 	{
        	 
        	 	
        	 	that.entity.start_images = that.entity._images.length;
        	 	
        	 	that.entity.loading_new = true;
        	 	
        	 	Endpoint.post('read', kind, that.entity).then(function (response) {
        	 		var data = response.data;
        	 		that.entity._images.extend(data['entity']['_images']);
        	 		that.entity.more_images = data['more_images'];
        	 		that.entity.loading_new = false;
        	 	});
        	 	
        	 			
        	 	}
        	 },
      
    	};
    	 
    	var update_options = {
    	 'kind' : kind,
    	 'scope' : scope,
    	 'handle' : function (data)
         { 
         	var that = this;
    
         	this.entity.more_images = data['more_images'];
         	
         	this.addProducts = function ()
         	{
         		var handle = function (data) {

                    var modalInstance = $modal.open({
                        templateUrl: logic_template('catalog/products.html'),
                        //windowClass: 'modal-medium',
                        controller: function ($scope, $modalInstance, RuleEngine, $timeout) {
                        	
                        	$scope.products = data['entities'];
                        	
                        	$scope.updateProduct = function (product)
				        	 {
				        	 	Product.update(product, function (product_updated) {
				        	 		update(product, product_updated);
				        	 	});
				        	 };

                            $scope.rule = that.rule;
                            $scope.live_entity = that.entity;
                            $scope.entity = angular.copy(that.entity);
                            
                            $scope.getImages = function ()
				            {
				        	 	if ($scope.entity.more_images && !$scope.entity.loading_new)
				        	 	{ 
					        	 	$scope.entity.start_images = $scope.entity._images.length;
					        	 	
					        	 	$scope.entity.loading_new = true;
					        	 	
					        	 	Endpoint.post('read', $scope.entity.kind, $scope.entity).then(function (response) {
					        	 		var data = response.data;
					        	 		$scope.entity._images.extend(data['entity']['_images']);
					        	 		$scope.entity.more_images = data['more_images'];
					        	 		$scope.entity.loading_new = false;
					        	 	});
				        	 	 
				        	 	}
				        	};
                            
                            $scope.onDrop = function (event, ui, catalog_image)
                            {
                            	 var pricetags = catalog_image.pricetags;
                            	 var pricetag = pricetags[pricetags.length-1];
                            	 
                            	 var posi = $(event.target).offset();
                            	 var posi2 = ui.offset;
                            	 
                            	 if ('key' in pricetag)
                            	 {
                            	 	pricetag['_key'] = pricetag['key'];
                            	 	
                            	 	delete pricetag['key'];
                            	 }
                            	  
                            	 pricetag['_position_top'] = posi2.top - posi.top;
                            	 pricetag['_position_left'] = posi2.left - posi.left;
                            	 
                            	 var sizes = calculate_pricetag_position
                            	 (
                            	 	pricetag['_position_top'],
                            	 	pricetag['_position_left'],
                            	 	$(event.target).width(),
                            	 	$(event.target).height(),
                            	 	catalog_image.width,
                            	 	catalog_image.height
                            	 ); // reverse the position perspective
                      
                            	 pricetag['position_top'] = sizes[0];
                            	 pricetag['position_left'] = sizes[1];
                            	 
                            	 pricetag['product_template'] = pricetag['_key'];
                            	 pricetag['value'] = pricetag['unit_price'];
                            	 
                            	  
                            };
                            
                            $scope.onStop = function (event, ui, pricetag)
                            {
                            	 pricetag['_position_top'] = ui.position.top;
                            	 pricetag['_position_left'] = ui.position.left;
                            	 
                            	 var target = $(event.target).parents('.catalog-image-scroll:first');
                            	  
                            	 var sizes = calculate_pricetag_position
                            	 (
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
                            
                            $scope.addProduct = function ()
                            {
                            	 Product.create(that.entity['key'], function (new_entity) {
                            	 	  if (this.action == 'create')
                            	 	  {
                            	 	  	 $scope.products.push(new_entity);
                            	 	  }
                            	 	  else
                            	 	  {
                            	 	  	  angular.forEach($scope.products, function (p) {
                            	 	  	  	  if (p.key == new_entity.key)
                            	 	  	  	  {
                            	 	  	  	  	 update(p, new_entity);
                            	 	  	  	  }
                            	 	  	  });
                            	 	  }
                            	 	  
                            	 });
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
                
                Endpoint.post('search', '38', {'catalog' : that.entity['key']}).success(handle);
 
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
                            };

                            $scope.save = function () {

                                Endpoint.post(action, that.entity['kind'], $scope.log)
                                    .success(function (data) {
                                    	 
                                    	EntityEditor.update_entity(that, data);
                              
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

            this.publish = function () {
                this._do_user_admin(this.entity, 'publish');
            };

            this.discontinue = function () {
                this._do_user_admin(this.entity, 'discontinue');
            };
            
            this.lock = function () {
                this._do_user_admin(this.entity, 'lock');
            };
         	 
         	this.sortableOptions = {
        	 	'forcePlaceholderSize' : true,
        	 	'placeholder' : 'image-image image-image-placeholder',
        	 	'stop' : function (e, u)
        	 	 { 
        	 	  
        	 	 }
        	};
			 
         },
    	 'templateUrl' : logic_template('catalog/manage.html'),
    	 
        };
    	
        return {
 
            create: function (domain_key, complete) {
              
               return EntityEditor.create({
                	 'kind' : kind,
                	 'entity' : {},
                	 'scope' : scope,
                	 'close' : false,
                	 'handle' : function (data)
			         {
			            this.entity['domain'] = domain_key;
			         },
                	 'complete' : complete,
                	 'options_after_update' : update_options,
                	 'templateUrl' : logic_template('catalog/manage.html'),
                	 'args' : {
                	 	'domain' : domain_key,
                	 }
                });
                
            },
            remove : function (entity, complete)
            { 
               return EntityEditor.remove({
               	  'kind' : kind,
               	  'entity' : entity,
               	  'complete' : complete,
               });
         
            },
            update: function (entity, complete)
            { 
                return EntityEditor.update(angular.extend({'entity' : entity, 
                'complete' : complete,
                'args' : {
		    	 	'key' : entity['key'],
		    	 }}, update_options));
            }

        };

    }
]);