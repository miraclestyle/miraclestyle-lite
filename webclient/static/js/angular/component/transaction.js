MainApp.factory('Journal', ['$rootScope', 'Endpoint', 'EntityEditor', 'Title', '$modal', 'Confirm', '$timeout',

        function ($rootScope, Endpoint, EntityEditor, Title, $modal, Confirm, $timeout) {

            var kind = '49';
             
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
                        this.entity.entry_fields.remove(field);
                    },
                    'removeLineField': function (field) {
                        this.entity.line_fields.remove(field);
                    },
                    
                    'manageEntryField': function (field) {
                       
                    },
                    
                    'manageLineField': function (field) {
                       
                    },
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
                        
                    };
                    
                    this.managePluginGroup = function (plugin_group)
                    {
                        
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

                                                EntityEditor.update_entity($parentScope, data, ['_images', '_products']);

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
                    
                    this.duplicate = function()
                    {
                        this._do_user_admin(this.entity, 'duplicate');
                    };

                    this.activate = function () {
                        this._do_user_admin(this.entity, 'activate');
                    };

                    this.decommission = function () {
                        this._do_user_admin(this.entity, 'decommission');
                    };

                    this.remove = function () {
                        this._do_user_admin(this.entity, 'delete');
                    };
                    
                    this.sudo = function ()
                    {
                        this._do_user_admin(this.entity, 'sudo');
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
                        'templateUrl': logic_template('catalog/manage.html'),
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
                     'entity' : {
                        'domain' : domain_key,
                     },
                     'scope' : scope,
                     'handle' : function (data)
                     {
                     },
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