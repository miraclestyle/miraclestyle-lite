MainApp.factory('Product', ['$rootScope', 'Endpoint', 'EntityEditor', 'Title', '$modal',

    function ($rootScope, Endpoint, EntityEditor, Title, $modal) {
    	
    	
    	var kind = '38';
    	  
        var scope = {
        	 'form_info' : {'action' : Endpoint.url},
        	  
        	 'completed' : function (data)
        	 {
        	 	EntityEditor.update_entity(this, data);
        	 },
            'removeImage' : function (image)
        	 {
        	 	this.entity._images.remove(image);
        	 },
        	 'removeContent' : function (content) {
        	 	this.entity._contents.remove(content);
        	 },
        	 'removeVariant' : function (variant)
        	 {
        	 	this.entity._variants.remove(variant);
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
                                 	that.entity._contents.push($scope.content);
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
                                 	that.entity._variants.push(this.variant);
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
        	 'addFiles' : function ()
        	 {
        	 	  var that = this;
         
        	 	  Endpoint.post('upload_images', kind, {'upload_url' : Endpoint.url, 'key' : that.entity.key}).success(function (data) {
        	 	  	   that.form_info.action = data.upload_url;
        	 	  	   
        	 	  	   $('form[name="manage_product"]').attr('action', that.form_info.action).trigger('submit'); // hack
        	 	  	  
        	 	  });
        	 }
    	};
    	
        return {
 
            create: function (catalog_key, complete) {
              
               return EntityEditor.create({
               		 'close' : false,
                	 'kind' : kind,
                	 'entity' : {},
                	 'scope' : scope,
                	 'handle' : function (data)
			         {
			            this.categories = data['categories'];
			            this.units = data['units'];
			            this.entity['catalog'] = catalog_key;
			         },
                	 'complete' : complete,
                	 'templateUrl' : logic_template('product/manage.html'),
                	 'args' : {
                	 	'catalog' : catalog_key,
                	 }
                });
                
            },
            update: function (entity, complete)
            {
             
                return EntityEditor.update({
                	 'kind' : kind,
                	 'entity' : entity,
                	 'scope' : scope,
                	 'handle' : function (data)
			         {
			            this.categories = data['categories'];
			            this.units = data['units'];
			            
			            this.update_mode = true;
			         },
                	 'complete' : complete,
                	 'templateUrl' : logic_template('product/manage.html'),
                	 'args' : {
                	 	'key' : entity['key'],
                	 }
                });
            }

        };

    }
]);