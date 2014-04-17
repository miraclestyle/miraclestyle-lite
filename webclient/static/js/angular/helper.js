KINDS._friendlyActionName = {};
KINDS.friendlyActionName = function(kind, action_key)
{
	/*
	var match = kind + '.' + action_key;
	
	if (match in this._friendlyActionName)
	{
		return this._friendlyActionName[match];
	}*/
	
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
	
	/*
	this._friendlyActionName[match] = ra;
	*/
	return ra;
};

//KINDS._get = {};
KINDS.get = function (kind_id)
{
   /*
   if (kind_id in this._get)
   {
 
   	  return this._get[kind_id];
   }*/
	
   var kind = this.info[kind_id];
   var fields = {};
   
   angular.forEach(kind, function (value, key) {
   		if (key != '_actions')
   		{
   			fields[key] = value;
   		}
   });
   
   var data = {
   	  'actions' : kind['_actions'],
   	  'fields' : fields,
   };
   /*
   this._get[kind_id] = data;
   */
   return data;
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
 
    /**
     * Updates a dict(s) based on last argument provided in argument list
     */
    
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

Array.prototype.remove = function (val)
{
	var index = this.indexOf(val);
  	this.splice(index,1);  
  	
  	return this;
};

Array.prototype.contains = function (value, all)
{
	if (angular.isArray(value))
	{
		var matches = [];
		
		angular.forEach(value, function (v) {
			matches.push((this.indexOf(value) > -1));
		});
		
		if (all)
		{
			return _.all(matches);
		}
		else
		{
			return _.some(matches);
		}
	}
	return this.indexOf(value) > -1;
};


Array.prototype.compare = function (array) {
    // if the other array is a falsy value, return
    if (!array)
        return false;

    // compare lengths - can save a lot of time
    if (this.length != array.length)
        return false;

    for (var i = 0, l=this.length; i < l; i++) {
        // Check if we have nested arrays
        if (this[i] instanceof Array && array[i] instanceof Array) {
            // recurse into the nested arrays
            if (!this[i].compare(array[i]))
                return false;
        }
        else if (this[i] != array[i]) {
            // Warning - two different object instances will never be equal: {x:20} != {x:20}
            return false;
        }
    }
    return true;
};

var new_width_by_height = function (original_width, original_height, new_height)
{
	original_width = parseInt(original_width);
	original_height = parseInt(original_height);
	new_height = parseInt(new_height);
  
    var ratio = new_height / original_height; // get ratio for scaling image
    var new_width = (original_width * ratio);
 
    return (new_width);
 
};

var new_height_by_width = function (original_width, original_height, new_width)
{
	original_width = parseInt(original_width);
	original_height = parseInt(original_height);
	new_width = parseInt(new_width);
	
    var ratio = new_width / original_width; // get ratio for scaling image
    var new_height = (original_height * ratio);
    
    return (new_height);
};
