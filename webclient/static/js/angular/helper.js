KINDS.friendlyActionName = function(kind, action_key)
{
	var info = this.get(kind);
	var actions = info['actions'];
	var ra = null;
	
	for (var action_name in actions)
	{
		 
		if (action_name == undefined) continue;
		
 		if (actions[action_name]['key'] == action_key)
		{
			ra = action_name;
			break;
		}
	}
	
	return ra;
};
KINDS.get = function (kind_id)
{
   var kind = this.info[kind_id];
   var fields = {};
   
   angular.forEach(kind, function (value, key) {
   		if (key != '_actions')
   		{
   			fields[key] = value;
   		}
   });
   
   return {
   	  'actions' : kind['_actions'],
   	  'fields' : fields,
   };
};

FRIENDLY_KIND_NAMES = {
    "60": "DomainRole", 
    "61": "Template", 
    "62": "Widget", 
    "24": "SupportRequest", 
    "46": "CompanyContent", 
    "44": "Company", 
    "42": "Variant", 
    "43": "Content", 
    "40": "InventoryLog", 
    "41": "InventoryAdjustment", 
    "0": "User", 
    "5": "Record", 
    "6": "Domain", 
    "9": "Address", 
    "8": "DomainUser", 
    "10": "Collection", 
    "39": "Instance", 
    "38": "Template", 
    "14": "Content", 
    "17": "ProductCategory", 
    "57": "Configuration", 
    "56": "Action", 
    "36": "CatalogImage", 
    "35": "Catalog", 
    "34": "CatalogPricetag"
};

var always_object = function (obj)
{
	if (!angular.isObject(obj))
	{
		return {};
	}
	
	return obj;
};

var use_init = function (key, fun)
{
	
	if ('initdata' in window && initdata[key])
	{
		var initdata2 = {};
		
		angular.copy(initdata, initdata2);
		 
		delete initdata;
	 
		return initdata2;
		
	}
	else
	{
	    var call = fun;
	    
	    if (angular.isFunction(fun))
	    {
	    	call = fun();
	    }
		 
		return call;
	}
	
};

var handle_data_types = function (response)
{
 
  	 	var formatter = {'created' : Date, 'updated' : Date, 'logged' : Date};
  	 	 
  	 	var do_format = function (entity) {
  	 				
			if (angular.isObject(entity))
			{
				var _recursive = function (entity) {
					
					angular.forEach(entity, function (value, key) {
						if (key in formatter)
						{
							if (angular.isObject(value))
							{
								_recursive(value);
							}
							else
							{
								entity[key] = new formatter[key](value);
							}
							
							
						}
					 
					});
				
				};
				
				_recursive(entity);
			}
			
  	 	};
  	 	// this is probably just temporary because we will need more robust transformer
  	 	if (angular.isObject(response))
  	 	{
 
  	 		if ('entities' in response)
  	 		{ 
  	 			angular.forEach(response.entities, do_format);
 
  	 		}
  	 		
  	 		if ('entity' in response)
  	 		{ 
  	 			do_format(response.entity);
 
  	 		}
  	 		 
  	 	}
  	 	 
  	 	return response;
};

function ui_template(file)
{
	return '/webclient/static/js/lib/angular/template/' + file;
}
function logic_template(file)
{
	return '/webclient/static/js/angular/component/template/' + file;
}

function update()
{ 
 
	var objects = [];
	angular.forEach(arguments, function (value) {
		objects.push(value);
	});
 
	var target = objects.pop();
	
	angular.forEach(objects, function (obj) {
		angular.forEach(target, function (new_value, key) {
			 obj[key] = new_value;
	     });
	});
  
	return objects;
}

function resolve_defaults(defaults, options)
{
	options = always_object(options);
	
	angular.forEach(defaults, function (value, key) {
		if ( ! (key in options))
		{
			options[key] = value;
		}
	});
	
	return options;
}

