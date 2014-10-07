app.config(['$stateProvider',
function($stateProvider) {

    var default_resolves = {
        current_account : ['Endpoint', '$rootScope',
        function(Endpoint, $rootScope) {

            Endpoint.current_account().then(function(response) {
      
                var account = response.data;
                $rootScope.current_account = account;
                return account;
            });

        }],
        kinds : ['Endpoint', '$rootScope',
        function(Endpoint, $rootScope) {

      
            return Endpoint.meta().then(function(response) {
                
                var kinds = response.data;
                $rootScope.kinds = kinds;
                return kinds;
            });
        }]

    };

    $stateProvider.state('home', {
        url : '/',
        templateUrl : 'home/index.html',
        controller : 'HomePage'
    }).state('login', {
        url : '/login/:provider',
        controller : 'LoginPage',
    }).state('sell-catalogs', {
        url : '/sell/catalogs',
        controller : 'SellCatalogs',
        templateUrl : 'catalog/list.html',
    }).state('admin_search', {
        url : '/admin/search/:kind/:query',
        templateUrl : function(stateParams) {

            var defaults = 'admin/search.html';

            if (stateParams['kind'] != undefined) {
                var config = ADMIN_SEARCH_KIND_CONFIG[stateParams['kind']];
                if (config && config['templateUrl']) {
                    defaults = config['templateUrl'];
                }
            }

            return defaults;
        },
        controller : 'AdminSearch',
        resolve : {}
    });

}]); 