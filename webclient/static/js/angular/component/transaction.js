MainApp.directive('outputconfig', ['$rootScope', function ($rootScope) {
    return {
        link : function (scope, element, attr)
        {
            console.log(scope.config, scope.field, element);
        } 
    };
}])
.factory('Journal', ['$rootScope', 'Endpoint', 'EntityEditor', 'Title', '$modal', 'Confirm', '$timeout',

        function ($rootScope, Endpoint, EntityEditor, Title, $modal, Confirm, $timeout) {

            var kind = '49';
            var action_kind = '84';
            var plugin_group_kind = '85';
             
            var make_scope = function ()
            {
                return {
                    'accordions' : {
                        'general' : true,
                        'actions' : false,
                        'plugin_groups' : false,
                    },
                    'gridConfig' : function (scope)
                    {
                        return {
                            margin : 10
                        };
                    },
                    'removeEntryField': function (field) {
               
                        var that = this;
                        angular.forEach(this.entity.entry_fields, function (v, k) {
                           if (v == arg)
                           {
                               delete that.entity.entry_fields[k];
                           } 
                        });
                    },
                    'removeLineField': function (field) {
                        var that = this;
                        angular.forEach(that.entity.line_fields, function (v, k) {
                           if (v == arg)
                           {
                               delete that.entity.line_fields[k];
                           } 
                        });
                    },
                     
                    'manageField': function (field, thing, config, what) {
                        var $parentScope = this;
                         
                        var modalInstance = $modal.open({
                                templateUrl: logic_template('transaction/manage_field.html'),
                                controller: function ($scope, $modalInstance, RuleEngine) {
                                     
                                    $scope.field = angular.copy(field ? field : {});
                
                                    var new_content = field ? false : true;
                                    
                                    $scope.the_field = null;
                                     
                                    $scope.config = config;
                                    
                                    $scope.getTheField = function ()
                                    {
                                       angular.forEach(config, function (field) {
                                          if (field[0].type == $scope.field.type)
                                          {
                                              var copied_field = angular.copy(field[0]);
                                              
                                              angular.forEach(['code_name', 'type', 'is_structured'], function (bogus) {
                                                 if (bogus in copied_field)
                                                 {
                                                     delete copied_field[bogus]; 
                                                 }
                                                 
                                              });
                                              
                                              $scope.the_field = copied_field;
                                              var requireds = {};
                                              if (field[2])
                                              {
                                                  angular.forEach(field, function (k) {
                                                     requireds[k] = true; 
                                                  });
                                              }
                                              else
                                              {
                                                  angular.forEach($scope.the_field, function (v, k) {
                                                     requireds[k] = true; 
                                                  });
                                              }
                                              
                                              $scope.required_fields = requireds;
                                          } 
                                       });
                                    };
                                    
                                    if ($scope.field.type) $scope.getTheField();
            
                                    $scope.save = function () {
                   
                                         if (new_content)
                                         {
                                            
                                            if (!thing[what])
                                            {
                                               thing[what] = {};
                                            }
                                            
                                            thing[what][$scope.field.name] = $scope.field;
                                            
                                         }
                                         else
                                         {
                                            update(field, $scope.field);
                                         }
                                         
                                         $scope.cancel();
                                    };
        
                                    $scope.cancel = function () {
                                        $modalInstance.dismiss('cancel');
                                    };
        
                                }
                            });
                    },
                    
                    'manageEntryField': function (field) {
                       var info = KINDS.get(kind);
                       var config = info['mapped_actions'][this.action]['arguments']['entry_fields']['cfg'];
                       this.manageField(field, this.entity, config, 'entry_fields');
                    },
                    
                    'manageLineField': function (field) {
                       var info = KINDS.get(kind);
                       var config = info['mapped_actions'][this.action]['arguments']['line_fields']['cfg'];
                       this.manageField(field, this.entity, config, 'line_fields');
                    }
               };
            };
            
            var make_action_scope = function ()
            {
                var outer_scope = make_scope();
                return {
                    'manageField' : outer_scope.manageField,
                    'manageArgument' : function (arg)
                    {
                        var info = KINDS.get(action_kind);
                        var config = info.fields['arguments']['cfg'];
                        return this.manageField(arg, this.child, config, 'arguments');
                    },
                    
                    'removeArgument' : function (arg)
                    {
                        
                        var that = this;
                        angular.forEach(this.child.arguments, function (v, k) {
                           if (v == arg)
                           {
                               delete that.child.arguments[k];
                           } 
                        });
                    }
                };
            };
            
            var make_plugin_group_scope = function ()
            {
                return {
                    'managePlugin' : function (plg)
                    {
                        var $parentScope = this;
                         
                        var modalInstance = $modal.open({
                                templateUrl: logic_template('transaction/journal/manage_plugin_group_plugin.html'),
                                controller: function ($scope, $modalInstance, RuleEngine) {
                                     
                                    $scope.plugin = angular.copy(plg ? plg : {});
                                    $scope.fields = {};
                                    
                                    var new_content = plg ? false : true;
                                    
                                    var info = KINDS.get(plugin_group_kind);
                                    
                                    $scope.kinds = info.fields['plugins']['kinds'];
                                    
                                    var thing = $parentScope.child;
                                    var what = 'plugins';
                                    
                                    $scope.collectVitalData = function ()
                                    {
                                         var info = KINDS.get($scope.plugin.kind);
                                         $scope.fields = info.fields;
                                         
                                    };
                                    
                                    if ($scope.plugin.kind) $scope.collectVitalData();
            
                                    $scope.save = function () {
                   
                                         if (new_content)
                                         {
                                            
                                            if (!thing[what])
                                            {
                                               thing[what] = [];
                                                
                                            }
                                            
                                            thing[what].push($scope.plugin);
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
                        plg._state = 'deleted';
                    }
                };
            };
            
            var make_update_scope = function (){
                
                return {
                     
                'kind': kind,
                'scope': make_scope(),
                'handle': function (data) {
                    
                    var $parentScope = this;
         
                    this.manageAction = function(action)
                    {
                         var find_child = function(child, entity)
                        { 
                            return _.findWhere(entity._transaction_actions, {key : child.key});
                        };
                         
                         var update_child = function(data)
                         {
                            update(this.child, find_child(this.child, data.entity));
                         };
                         
                         var update_cfg = {
                             'kind' : kind,
                             'scope' : make_action_scope(),
                             'update_child' : update_child,
                             'parentScope' : $parentScope,
                             'get_child' : function ()
                             {
                                var that = this;
                                this.child = find_child(action, this.entity);
                             },
                             'templateUrl' : logic_template('transaction/journal/manage_action.html')
                        };
                      
                         if (!action)
                         {
                            return EntityEditor.create({
                                 'close' : false,
                                 'kind' : kind,
                                 'parentScope' : $parentScope,
                                 'scope' : make_action_scope(),
                                 'get_child' : function ()
                                 {
                                    this.child = {};
                                    this.entity._transaction_actions.push(this.child);
                                 },
                                 'update_child' : function (data) {
                                    
                                    var found = _.last(data.entity._transaction_actions);
                                     
                                    update(this.child, found);
                                 },
                                 'options_after_update' : update_cfg,
                                 'templateUrl' : logic_template('transaction/journal/manage_action.html'),
                            });
                         }
                         else
                         {
                            EntityEditor.update(update_cfg);
                         }
                    };
                    
                    this.managePluginGroup = function (plugin_group)
                    {
                         var find_child = function(child, entity)
                        { 
                            return _.findWhere(entity._transaction_plugin_groups, {key : child.key});
                        };
                         
                         var update_child = function(data)
                         {
                            update(this.child, find_child(this.child, data.entity));
                         };
                         
                         var actions = {};
                         
                         angular.forEach($parentScope.entity._transaction_actions, function (a) {
                            actions[a.key] = a.name; 
                         });
                         
             
                         var update_cfg = {
                             'kind' : kind,
                             'scope' : $.extend(make_plugin_group_scope(), {'actions' : actions}),
                             'update_child' : update_child,
                             'parentScope' : $parentScope,
                             'get_child' : function ()
                             {
                                var that = this;
                                this.child = find_child(plugin_group, this.entity);
                             },
                             'templateUrl' : logic_template('transaction/journal/manage_plugin_group.html')
                        };
                      
                         if (!plugin_group)
                         {
                            return EntityEditor.create({
                                 'close' : false,
                                 'kind' : kind,
                                 'parentScope' : $parentScope,
                                 'scope' : $.extend(make_plugin_group_scope(), {'actions' : actions}),
                                 'get_child' : function ()
                                 {
                                    this.child = {};
                                    this.entity._transaction_plugin_groups.push(this.child);
                                 },
                                 'update_child' : function (data) {
                                    
                                    var found = _.last(data.entity._transaction_plugin_groups);
                                     
                                    update(this.child, found);
                                 },
                                 'options_after_update' : update_cfg,
                                 'templateUrl' : logic_template('transaction/journal/manage_plugin_group.html'),
                            });
                         }
                         else
                         {
                            EntityEditor.update(update_cfg);
                         }
                    };

                    this._do_user_admin = function (entity, action) {

                        var handle = function () {

                            var modalInstance = $modal.open({
                                templateUrl: logic_template('transaction/journal/user_admin.html'),
                                windowClass: 'modal-medium',
                                controller: function ($scope, $modalInstance, RuleEngine, $timeout) {
                               
                                    $scope.rule = $parentScope.rule;
                                    $scope.action = action;
                                    $scope.log = {
                                        'message': '',
                                        'key': $parentScope.entity.key,
                                        'state' : $parentScope.entity.state,
                                        'note' : '',
                                    };

                                    $scope.save = function () {

                                        Endpoint.post(action, $parentScope.entity.kind, $scope.log)
                                            .success(function (data) {

                                                EntityEditor.update_entity($parentScope, data, ['_transaciton_actions', '_transaction_plugin_groups']);

                                                $scope.cancel();

                                            });

                                    };

                                    $scope.cancel = function () {
                                        $modalInstance.dismiss();
                                    };
                                }
                            });

                        };

                        handle();

                    };
 

                    this.activate = function () {
                        this._do_user_admin(this.entity, 'activate');
                    };

                    this.decommission = function () {
                        this._do_user_admin(this.entity, 'decommission');
                    };
  
                    this.sortableOptions = {
                        'forcePlaceholderSize': true,
                        'placeholder': 'image-image image-image-placeholder grid-item'
                    };

                },
                'templateUrl': logic_template('transaction/journal/manage.html'),
              };
            
            };
 
            
            var read_arguments = {
                 '_transaction_actions' : {},
                 '_transaction_plugin_groups' : {},
            };
    
            return {
                
                remove : function (entity, complete)
                {
                   
                   return EntityEditor.remove({
                      'kind' : kind,
                      'entity' : entity,
                      'complete' : complete,
                   });
             
                },

                create: function (domain_key, complete) {
                    return EntityEditor.create({
                        'kind': kind,
                        'entity': {},
                        'scope': make_scope(),
                        'close': false,
                        'handle': function (data) {
                            this.entity.domain = this.entity.namespace;
                            this.uploadConfig = {
                                   'action' : 'prepare',
                                   'kind' : kind,
                                   'args' : {
                                      'domain' : this.entity.namespace,
                                   }
                                };
                                 
                        },
                        'complete': complete,
                        'options_after_update': make_update_scope(),
                        'templateUrl': logic_template('transaction/journal/manage.html'),
                        'args': {
                            'domain': domain_key,
                            'read_arguments' : read_arguments,
                        }
                    });

                },
                update: function (entity, complete) {
                    return EntityEditor.update(angular.extend({
                        'entity': entity,
                        'complete': complete,
                        'args': {
                            'key': entity.key,
                            'read_arguments' : read_arguments,
                        }
                    }, make_update_scope()));
                }

            };

        }
    ]).factory('Category', ['$rootScope', 'Endpoint', 'EntityEditor', 'Title', '$modal',

    function ($rootScope, Endpoint, EntityEditor, Title, $modal) {
          
        var scope = {
 
        };
        
        return {
            create: function (domain_key, complete) {
              
               return EntityEditor.create({
                     'kind' : '47',
                     'entity' : {'domain' : domain_key},
                     'scope' : scope,
                     'complete' : complete,
                     'templateUrl' : logic_template('transaction/category/manage.html'),
                     'args' : {
                        'domain' : domain_key,
                     }
                });
                
            },
            remove : function (entity, complete)
            {
               
               return EntityEditor.remove({
                  'kind' : '47',
                  'entity' : entity,
                  'complete' : complete,
               });
         
            },
            update: function (entity, complete)
            {
                
 
                return EntityEditor.update({
                     'kind' : '47',
                     'entity' : entity,
                     'scope' : scope,
                     'complete' : complete,
                     'templateUrl' : logic_template('transaction/category/manage.html'),
                     'args' : {
                        'key' : entity.key,
                     }
                });
            }

        };

    }
]);