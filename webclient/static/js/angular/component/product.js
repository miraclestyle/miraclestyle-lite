MainApp.factory('Product', ['$rootScope', 'Endpoint', 'EntityEditor', 'Title', '$modal',

    function ($rootScope, Endpoint, EntityEditor, Title, $modal) {
    	
    	
    	var kind = '38';
    	  
        var scope = {
        	  
        	 'completed' : function (data)
        	 {
        	 	EntityEditor.update_entity(this, data['entity']);
        	 },
            'removeImage' : function (image)
        	 {
        	 	this.entity._images.remove(image);
        	 },
        	 'addFiles' : function ()
        	 {
        	 	  var that = this;
         
        	 	  Endpoint.post('upload_images', kind, {'upload_url' : Endpoint.url}).success(function (data) {
        	 	  	   that.form_info.action = data.upload_url;
        	 	  	   
        	 	  	   $('form[name="manage_product"]').attr('action', that.form_info.action).trigger('submit'); // hack
        	 	  	  
        	 	  });
        	 }
    	};
    	
        return {
 
            create: function (catalog_key, complete) {
              
               return EntityEditor.create({
                	 'kind' : kind,
                	 'entity' : {},
                	 'scope' : scope,
                	 'handle' : function (data)
			         {
			            this.categories = data['categories'];
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