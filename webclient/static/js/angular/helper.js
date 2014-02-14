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

