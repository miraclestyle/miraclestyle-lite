MainApp.factory('Seller', ['$rootScope', 'Endpoint', 'EntityEditor', 'Title', '$modal', 'Confirm',

    function ($rootScope, Endpoint, EntityEditor, Title, $modal, Confirm) {
        
        var plugins_container = '22';
        
        var scope = {
            'form_info' : {
                'action' : Endpoint.url,
            },
            'accordions': {'general': true},
            'completed' : function (data) {
                EntityEditor.update_entity(this, data);
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
 
     
        return {
 
            update: function (account)
            {
                var that = this;
                var read_arguments = {
                                 '_plugin_group': {},
                                 '_contents': {},
                                 '_feedback': {},
                                 
                         };
 
                return EntityEditor.update({
                         'kind': '23',
                         'entity': {},
                         'scope': scope,
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
]).run(['$rootScope', 'Seller', 'Endpoint',
    function ($rootScope, Seller, Endpoint) {
  
    $rootScope.manageSeller = function ()
    {
        Seller.update($rootScope.current_account);
    };
     
}]);