var alwaysObject = function (obj)
{
	if (!angular.isObject(obj))
	{
		return {};
	}
	
	return obj;
};

var useInit = function (key, fun)
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

var handleFewDatatypes = function (response)
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
function logic_template(active_component, file)
{
	return '/webclient/static/js/angular/component/' + active_component + '/template/' + file;
}

function update(d1, d2)
{
	angular.forEach(d2, function (value, key) {
		d1[key] = value;
	});
	
	return d1;
}

