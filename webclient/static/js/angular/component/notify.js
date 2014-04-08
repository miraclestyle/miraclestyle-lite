MainApp.factory('Notify', ['$rootScope', 'Endpoint', 'EntityEditor', 'Title', '$modal',

    function ($rootScope, Endpoint, EntityEditor, Title, $modal) {
    	
    	var actions = {};
    	
    	angular.forEach(KINDS.info, function (value, key) {
    		
    		 if (key in FRIENDLY_KIND_NAMES)
    		 {
    		 	angular.forEach(value._actions, function (action, action_name) {
	    		 	 actions[action.key] = FRIENDLY_KIND_NAMES[key] + '.' + action_name;
	    		 });
    		 }
    		 
    	});
    	  
        var scope = {
         	'modes' : [{'name' : 'Mail', 'kind' : 58}, {'name' : 'Http', 'kind' : 59}],
         	'actions' : actions,
         	'changeKind' : function ()
         	{
         		var that = this;
         		Endpoint.post('prepare', this.options['kind'], this.entity).success(function (data) {
         			update(that.entity, data.entity);
         			update(that.live_entity, data.entity);
         			that.rule.update(data.entity);
         			
         			that.roles = data.roles;
			        that.users = data.users;
         		});
         	},
    	};
    	
        return {
 
            create: function (domain_key, complete) {
              
               return EntityEditor.create({
                	 'kind' : '61',
                	 'entity' : {},
                	 'scope' : scope,
                	 'handle' : function (data)
			         {
			            this.entity['domain'] = domain_key;
			             
			         },
                	 'complete' : complete,
                	 'templateUrl' : logic_template('notify/manage.html'),
                	 'args' : {
                	 	'domain' : domain_key,
                	 }
                });
                
            },
            remove : function (entity, complete)
            {
               
               return EntityEditor.remove({
               	  'kind' : entity['kind'],
               	  'entity' : entity,
               	  'complete' : complete,
               });
         
            },
            update: function (entity, complete)
            {
             
                return EntityEditor.update({
                	 'kind' : entity['kind'],
                	 'entity' : entity,
                	 'scope' : scope,
                	 'handle' : function (data)
			         {
			            this.roles = data['roles'];
			            this.users = data['users'];
			         },
                	 'complete' : complete,
                	 'templateUrl' : logic_template('notify/manage.html'),
                	 'args' : {
                	 	'key' : entity['key'],
                	 }
                });
            }

        };

    }
]);