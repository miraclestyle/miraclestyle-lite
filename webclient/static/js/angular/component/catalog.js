MainApp.factory('Catalog', ['$rootScope', 'Endpoint', 'EntityEditor', 'Title', '$modal', 'Confirm',

    function ($rootScope, Endpoint, EntityEditor, Title, $modal, Confirm) {
    	
    	
    	var kind = '35';
    	  
        var scope = {
        	 'datepickOptions' : {
        	 	'showWeeks' : false,
        	 	
        	 },
        	 'sortableOptions' : {
        	 	'update' : function (e, u)
        	 	 {
        	 	 	console.log(e, u);
        	 	 }
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
        	 'publish' : function ()
        	 {
        	 	 var that = this;
        	 	 
        	 	 Confirm.sure(function () {
        	 	 	Endpoint.post('publish', kind, that.entity).success(function (data)
	        	 	{
	        	 	    EntityEditor.update_entity(that, data);	
	        	 	});
        	 	 });
        	 	
        	 },
        	 'discontinue' : function ()
        	 {
        	 	 var that = this;
        	 	 
        	 	 Confirm.sure(function () {
        	 	 	Endpoint.post('discontinue', kind, that.entity).success(function (data)
	        	 	{
	        	 	    EntityEditor.update_entity(that, data);	
	        	 	});
        	 	 });
        	 	
        	 },
        	 
        	 
             'lock' : function ()
        	 {
        	 	 var that = this;
        	 	 
        	 	 Confirm.sure(function () {
        	 	 	Endpoint.post('lock', kind, that.entity).success(function (data)
	        	 	{
	        	 	    EntityEditor.update_entity(that, data);	
	        	 	});
        	 	 });
        	 	
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