MainApp.factory('Catalog', ['$rootScope', 'Endpoint', 'EntityEditor', 'Title', '$modal', 'Confirm',

    function ($rootScope, Endpoint, EntityEditor, Title, $modal, Confirm) {
    	
    	
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
        	 	update(this.entity, data['entity']);
        	 },
        	 'removeCatalogImage' : function (catalog_image)
        	 {
        	 	this.entity._images.remove(catalog_image);
        	 },
        	 'addFiles' : function ()
        	 {
        	 	  var that = this;
         
        	 	  Endpoint.post('upload_images', kind, {'upload_url' : Endpoint.url}).success(function (data) {
        	 	  	   that.form_info.action = data.upload_url;
        	 	  	   
        	 	  	   $('form[name="manage_catalog"]').attr('action', that.form_info.action).trigger('submit'); // hack
        	 	  	  
        	 	  });
        	 }
    	};
    	
        return {
 
            create: function (domain_key, complete) {
              
               return EntityEditor.create({
                	 'kind' : kind,
                	 'entity' : {},
                	 'scope' : scope,
                	 'handle' : function (data)
			         {
			            this.entity['domain'] = domain_key;
			         },
                	 'complete' : complete,
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
             
                return EntityEditor.update({
                	 'kind' : kind,
                	 'entity' : entity,
                	 'scope' : scope,
                	 'handle' : function (data)
			         { 
			         	var that = this;
			         	 
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
			        	 	'placeholder' : 'catalog-image catalog-image-placeholder',
			        	 	'stop' : function (e, u)
			        	 	 {
			        	 	 	 
			        	 	 	 angular.forEach(that.entity._images, function (value, i) {
			        	 	 	 	 value.sequence = i;
			        	 	 	 });
			        	 	  
			        	 	 }
			        	};
 						 
			         },
                	 'complete' : complete,
                	 'templateUrl' : logic_template('catalog/manage.html'),
                	 'args' : {
                	 	'key' : entity['key'],
                	 }
                });
            }

        };

    }
]);