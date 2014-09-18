MainApp.factory('Seller', ['$rootScope', 'Endpoint', 'EntityEditor', 'Title', '$modal', 'Confirm',

    function ($rootScope, Endpoint, EntityEditor, Title, $modal, Confirm) {
        
        
        var scope = {
            'form_info' : {
                'action' : Endpoint.url,
            }
        };
     
        return {
            create: function (account, complete)
            {
                var that = this;
  
                return EntityEditor.create({
                     'kind' : '23',
                     'entity' : {},
                     'scope' : scope,
                     'complete' : complete,
                     'templateUrl' : logic_template('seller/create.html'),
                     'args' : {
                        'account' : account['key'],
                     }
                });
            },
            update: function (entity, complete)
            {
                var that = this;
  
                return EntityEditor.create({
                     'kind' : '23',
                     'entity' : entity,
                     'scope' : scope,
                     'complete' : complete,
                     'templateUrl' : logic_template('seller/update.html'),
                     'args' : {
                        'key' : entity['key'],
                     }
                });
            }

        };

    }
]).run(['$rootScope', 'Seller', 'BuyerCollection',
    function ($rootScope, Seller, BuyerCollection) {
  
    $rootScope.manageSeller = function ()
    {
        Seller.update($rootScope.current_account);
    };
     
}]);