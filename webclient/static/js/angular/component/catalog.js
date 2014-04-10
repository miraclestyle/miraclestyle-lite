MainApp.factory('Catalog', ['$rootScope', 'Endpoint', 'EntityEditor', 'Title', '$modal',

    function ($rootScope, Endpoint, EntityEditor, Title, $modal) {
    	  
        var scope = {
        	 'menu' : {
        	 	'isOpen' : true,
        	 },
        	 'form_info' : {
        	 	'action' : Endpoint.url
        	 },
        	 'completed' : function (data)
        	 {
        	 	update(this.entity, data['entity']);
        	 },
        	 'addFiles' : function ($event)
        	 {
        	 	  var that = this;
      
        	 	  Endpoint.post('upload_images', '35', {'upload_url' : Endpoint.url}).success(function (data) {
        	 	  	   that.form_info.action = data.upload_url;
        	 	  	   
        	 	  	   $('form[name="manage_catalog"]').attr('action', that.form_info.action).trigger('submit'); // hack
        	 	  	  
        	 	  });
        	 }
    	};
    	
        return {
 
            create: function (domain_key, complete) {
             
            	  
               return EntityEditor.create({
                	 'kind' : '35',
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
               	  'kind' : '35',
               	  'entity' : entity,
               	  'complete' : complete,
               });
         
            },
            update: function (entity, complete)
            {
             
                return EntityEditor.update({
                	 'kind' : '35',
                	 'entity' : entity,
                	 'scope' : scope,
                	 'handle' : function (data)
			         {
 						 
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