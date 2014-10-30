MainApp.factory('Seller', ['$rootScope', 'Endpoint', 'EntityEditor', 'Title', '$modal', 'Confirm',

    function ($rootScope, Endpoint, EntityEditor, Title, $modal, Confirm) {
        
        var plugins_container = '22';
        
        function make_scope()
        {
  
            return {
                'form_info' : {
                    'action' : Endpoint.url,
                },
                'accordions': {'general': true},
                'completed' : function (data) {
                    EntityEditor.update_entity(this, data);
                },
      
                'removeContent' : function (content) {
                      content._state = 'deleted';
         
                 },
                'manageContent' : function (content) {
                            
                            var $parentScope = this;
                             
                            var modalInstance = $modal.open({
                                    templateUrl: logic_template('seller/manage_content.html'),
                                    controller: function ($scope, $modalInstance, RuleEngine) {
             
                                        $scope.content = angular.copy(content ? content : {});
                                  
                                        var new_content = content ? false : true;
                         
                                        $scope.save = function () {
                       
                                             if (new_content)
                                             {
                                                if (!$parentScope.entity._content) $parentScope.entity._content = {};
                                                if (!$parentScope.entity._content.documents) $parentScope.entity._content.documents = [];
                                                $parentScope.entity._content.documents.push($scope.content);
                                             }
                                             else
                                             {
                                                update(content, $scope.content);
                                             }
                                             
                                             $scope.cancel();
                                        };
            
                                        $scope.cancel = function () {
                                            $modalInstance.dismiss('cancel');
                                        };
            
                                    }
                                });
                            
                 },
                      
                'managePlugin' : function (plg)
                {
                    var $parentScope = this;
                     
                    var modalInstance = $modal.open({
                            templateUrl: logic_template('seller/manage_plugin.html'),
                            controller: function ($scope, $modalInstance, RuleEngine) {
                                 
                                $scope.plugin = angular.copy(plg ? plg : {});
                                $scope.fields = {};
                                
                                var new_content = plg ? false : true;
                                
                                $scope.is_new = new_content;
                                
                                var info = KINDS.get(plugins_container);
                                
                                $scope.kinds = info.fields['plugins']['kinds'];
                                
                                var thing = $parentScope.entity;
                        
                                $scope.collectVitalData = function ()
                                {
                                     var info = KINDS.get($scope.plugin.kind);
                                     $scope.fields = info.fields;
                                     
                                };
                                
                                if ($scope.plugin.kind) $scope.collectVitalData();
                                
                                 
        
                                $scope.save = function () {
               
                                     if (new_content)
                                     {
                                        
                                        if (!thing['_plugin_group']['plugins'])
                                        {
                                           thing['_plugin_group']['plugins'] = [];
                                            
                                        }
                                        
                                        thing['_plugin_group']['plugins'].push($scope.plugin);
                                     }
                                     else
                                     {
                                        update(plg, $scope.plugin);
                                     }
                                     
                                     $scope.cancel();
                                };
    
                                $scope.cancel = function () {
                                    $modalInstance.dismiss('cancel');
                                };
    
                            }
                        });
                },
                'removePlugin' : function (plg)
                {
                    if (this.entity._plugin_group.plugins)
                    {
                        this.entity._plugin_group.plugins.remove(plg);
                    }
                },
      
            };
        
                  
        };
 
     
        return {
 
            update: function (account)
            {
                var that = this;
                var read_arguments = {
                                 '_plugin_group': {},
                                 '_content': {},
                                 '_feedback': {},
                                 
                         };
 
                return EntityEditor.update({
                         'kind': '23',
                         'entity': {},
                         'scope': make_scope(),
                         'handle': function ()
                         {
                             var that = this;
                             this.createUploadUrlOnSelectOptions = {
                                     'complete' : function (data)
                                     {
                                            that.form_info.action = data.upload_url;
                                     }
                            };
                            
                            this.history.args.account = account.key;
                            
                            this.entity.read_arguments = read_arguments;
                               
                               
                         },
                         'templateUrl': logic_template('seller/manage.html'),
                         'args': {
                             'account': account.key,
                             'read_arguments': read_arguments,
                         }
                });
            }

        };

    }
]).directive('spitField', ['$rootScope', '$compile',
  function ($rootScope, $compile) {
      
    function compile_attrs(data)
    {
        var compiled = [];
        angular.forEach(data, function (v, k) {
           compiled.push('"'+ k +'"="'+v+'"'); 
        });
        return compiled.join(" ");
    }
    
    return {
        replace: true,
        link : function (scope, element, attrs)
        { 
            var config = scope.$eval(attrs.spitField);
             
            var fields = scope[config.fields];
         
            var data = scope[config.model];
            
            function update_inner_scope()
            {
                fields = scope[config.fields];
                  
                data = scope[config.model];
                 
                angular.forEach(fields, function (c, k) {
                  
                    if (c.modelclass)
                    { 
                        if (!data[k])
                        {
                            if (c.repeated)
                            {
                                data[k] = [];
                            }
                            else
                            {
                                data[k] = {};
                            }
                        }
                    }
                    else
                    {
                        if (c.repeated)
                        {
                            if (!data[k])
                            {
                                data[k] = [];
                            }
                        }
                    }
                    
                });
                
                 
            }
            
            scope.$watch(
              // This function returns the value being watched. It is called for each turn of the $digest loop
              function() { return scope[config.fields]; },
              function(newValue, oldValue) {
       
                if ( newValue !== oldValue ) {
 
                   var fs = scope[config.fields];
                   angular.forEach(data, function (v, k) {
                       if (!fs[k] && k != 'kind')
                       {
                           delete data[k];
                       }
                   });
                   
                   angular.forEach(fs, function (v, k) {
                       if (!data[k])
                       {
                           data[k] = v['default'];
                       }
                   });
                   
                   update_inner_scope();
                   
                   $(element).addClass('json-editor').jsonEditor(data, {change: function (data) {
                        update(scope[config.model], data);
                        scope.$apply();
                    }});
                }
              }
            );
            
            update_inner_scope();
    
            $(element).addClass('json-editor').jsonEditor(data, {change: function (data) {
                    update(scope[config.model], data);
                    scope.$apply();
                    
                }})
                .on('jsoneditor.finalAdd', function (event, opt, json, root, path) {
                         
                }).on('jsoneditor.afterAdd', function afterAdd(event, opt, json, root, path) {
                         
                        var spath = path.split('.');
                        var find = fields;
              
                        if (spath.length > 1)
                        {
                            angular.forEach(spath, function (v) {
                                
                                var thing = v;
                   
                                if (isNaN(parseInt(thing)))
                                { 
                                    
                                    if (!find[thing])
                                    {
                                        if (find.modelclass)
                                        {
                                            find = find.modelclass;
                                        }
                                        
                                    }
                                    
                                    find = find[thing];
                               
                                    
                                }
                                 
                                
                            });
                           
                        }
                        else if (spath.length > 0)
                        {
                            find = fields[path];
                        }
            
                        
                        function modelclassprocess(path, find, json)
                        {
                        
                            if (find)
                            {
                                if (!find.modelclass)
                                {
                                    if (find.repeated)
                                    {
                                        if ((json.length-1) < 0)
                                        {
                                            json.push(d);
                                        }
                                        else
                                        {
                                            json[json.length-1] = find['default'];
                                        }
                                        
                                    }
                                    else
                                    {
                                        json[path] = find['default'];
                                    }
                                }
                                else
                                { 
                                    var d = {};
                                    
                                    angular.forEach(find.modelclass, function (v, k) {
                                        var zz = v['default'];
                                        if (v.modelclass)
                                        {
                                            if (v.repeated)
                                            {
                                                zz = [];
                                            }
                                            else
                                            {
                                                zz = {};
                                            }
                                        }
                                         
                                        d[k] = zz;
                                        
                                        if (v.modelclass)
                                        {
                                            //modelclassprocess(path + '.' + k, v, d[k]);
                                        }
                                    });
                                    
                                    if (find.repeated)
                                    {
                                        if ((json.length-1) < 0)
                                        {
                                            json.push(d);
                                        }
                                        else
                                        {
                                            json[json.length-1] = d;
                                        }
                                        
                                    }
                                    else
                                    {
                                        json[path] = d;
                                    }
                                    
                                }
                            
                            
                           }
                        }
                        
                        modelclassprocess(path, find, json);
                        
                        
                });
        }
    };
}])
.run(['$rootScope', 'Seller', 'Endpoint',
    function ($rootScope, Seller, Endpoint) {
  
    $rootScope.manageSeller = function ()
    {
        Seller.update($rootScope.current_account);
    };
     
}]);