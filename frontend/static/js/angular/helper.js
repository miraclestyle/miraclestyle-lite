/**
 * These are global scope helper functions and additional hacks
 */
function calculate_grider(all_canvas, max_w, min_w, margin){
 
  var loop = max_w - min_w;
  if (margin == undefined) margin = 0;
  	 
  var canvas_width = all_canvas;
  var values = [];
  
  for (var i=0;i<loop;i++){
    var cover_width_raw = (max_w + 1)-i;
    var cover_count_raw = canvas_width/cover_width_raw;
    var cover_count = Math.floor(cover_count_raw);
    var cover_width = (canvas_width/cover_count);
    if (cover_width>max_w){
      cover_count = cover_count+1;
      cover_width = (canvas_width/cover_count);
      if (cover_width<min_w){
        cover_width = max_w;
        cover_count = cover_count-1;
      }
    }
    cover_width = cover_width - margin;
    var rounded = Math.floor(cover_width);
    var sides = (cover_width - rounded) * cover_count;
    
    values[0] = rounded;
    values[1] = sides;
    values[2] = cover_width;
    values[3] = cover_count;
    if (cover_count_raw>4||cover_count==1){
      break;
    }
  }
  return values;
};

KINDS.friendlyActionName = function(kind, action_key)
{
 
	var info = this.get(kind);
	if (info == undefined) return undefined;
	var actions = info['actions'];
	var ra = null;
	
	angular.forEach(actions, function (action) {
		if (action['key'] == action_key)
		{
			ra = action['id'];
		}
	});
 
 
	return ra;
};

if (!'console' in window)
{
	window.console = {'log' : $.noop};
}
else
{
	if (!'log' in window.console)
	{
		window.console.log = $.noop;
	}
}

KINDS.get = function (kind_id)
{
  
   var kind = this.info[kind_id];
   if (kind == undefined) return undefined;
   var fields = {};
   
   angular.forEach(kind, function (value, key) {
   		if (key != '_actions')
   		{
   			fields[key] = value;
   		}
   });
   
   var actions = {};
   
   angular.forEach(kind['_actions'], function (action) {
   	  actions[action.id] = action;
   });
   
   var data = {
   	  'actions' : kind['_actions'],
   	  'mapped_actions' : actions,
   	  'fields' : fields,
   };
 
   return data;
};


function always_object(obj)
{
	if (!angular.isObject(obj))
	{
		return {};
	}
	
	return obj;
};

function use_init(key, fun)
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
	return '/frontend/static/js/lib/angular/template/' + file;
}
function logic_template(file)
{
	return '/frontend/static/js/angular/component/template/' + file;
}
 

function update()
{ 
 
    /**
     * Updates a dict(s) based on last argument provided in argument list. e.g.
     * update(dict1, dict2, dict3, dict_to_update_others)
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

Array.prototype.extend = function (other_array) {
    var that = this;
    angular.forEach(other_array, function(v) {that.push(v);});
};

function new_width_by_height(original_width, original_height, new_height)
{
	original_width = parseInt(original_width);
	original_height = parseInt(original_height);
	new_height = parseInt(new_height);
  
    var ratio = new_height / original_height; // get ratio for scaling image
    var new_width = (original_width * ratio);
 
    return (new_width);
 
};

function new_height_by_width(original_width, original_height, new_width)
{
	original_width = parseInt(original_width);
	original_height = parseInt(original_height);
	new_width = parseInt(new_width);
	
    var ratio = new_width / original_width; // get ratio for scaling image
    var new_height = (original_height * ratio);
    
    return (new_height);
};


	
function calculate_pricetag_position(ihp, ivp, iiw, iih, ciw, cih){
 
 
	  /*  
	  ihp - Initial Horizontal Price Tag Position 
	  ivp - Initial Vertical Price Tag Position 
	  iiw - Initial Image Width  
	  iih - Initial Image Height  
	  
	  ciw - Current Image Width  
	  cih - Current Image Height  
	  chp - Current Horizontal Price Tag Position  
	  cvp - Current Vertical Price Tag Position  
	  */
	 
	  var chp = (ihp/iiw)*ciw;
	  var cvp = (ivp/iih)*cih;
	  return [chp, cvp];
};
	 

FRIENDLY_KIND_NAMES = {
    "0": "Record",
    "1": "Action",
    "2": "PluginGroup",
    "3": "Permission",
    "4": "ActionPermission",
    "5": "FieldPermission",
    "6": "Role",
    "7": "GlobalRole",
    "8": "Image",
    "9": "AccountSession",
    "10": "AccountIdentity",
    "11": "Account",
    "12": "Country",
    "13": "CountrySubdivision",
    "14": "Address",
    "15": "Location",
    "16": "UOM",
    "17": "Unit",
    "18": "Collection",
    "19": "Buyer",
    "20": "SellerContentDocument",
    "21": "SellerContent",
    "22": "SellerPluginContainer",
    "23": "Seller",
    "24": "CatalogProductCategory",
    "25": "CatalogProductContent",
    "26": "CatalogProductVariant",
    "27": "CatalogProductInstance",
    "28": "CatalogProduct",
    "29": "CatalogPricetag",
    "30": "CatalogImage",
    "31": "Catalog",
    "32": "OrderLineTax",
    "33": "OrderLine",
    "34": "Order",
    "35": "OrderMessage",
    "36": "SellerFeedbackStats",
    "37": "SellerFeedback",
    "86": "Context",
    "87": "Set",
    "88": "Read",
    "89": "Write",
    "90": "Delete",
    "91": "Duplicate",
    "92": "UploadImages",
    "93": "RulePrepare",
    "94": "RuleExec",
    "95": "Search",
    "97": "CallbackExec",
    "98": "BlobURL",
    "99": "OrderInit",
    "101": "ProductToOrderLine",
    "104": "OrderLineFormat",
    "105": "OrderFormat",
    "106": "Location",
    "107": "AddressRule",
    "108": "PayPalPayment",
    "109": "Tax",
    "111": "CarrierLineRule",
    "112": "CarrierLine",
    "113": "Carrier",
    "114": "PluginExec"
};