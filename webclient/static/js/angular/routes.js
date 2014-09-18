MainApp.config(['$stateProvider',
    function ($stateProvider) {
  
        $stateProvider.state('home', {
            url: '/',
            templateUrl: logic_template('home/index.html'),
            controller: 'HomePage'
        }).state('login', {
            url: '/login/:provider',
            controller: 'LoginPage',
          })
          .state('admin_search', {
            url: '/admin/search/:kind/:query',
            templateUrl: function (stateParams) {

                var defaults = logic_template('admin/search.html');

                if(stateParams['kind'] != undefined) {
                    var config = ADMIN_SEARCH_KIND_CONFIG[stateParams['kind']];
                    if(config && config['templateUrl']) {
                        defaults = config['templateUrl'];
                    }
                }

                return defaults;
            },
            controller: 'AdminSearch',
            resolve: {
                search: ['Endpoint', '$stateParams', '$rootScope',
                    function (Endpoint, $stateParams, $rootScope) {

                        var query = JSON.parse($stateParams['query']);

                        if(!angular.isObject(query)) query = {};
                        
                        $rootScope.search.setSearch($stateParams['kind'], query['search']);
                        $rootScope.search.the_query = query;

                        return Endpoint.post('search', $stateParams['kind'], query).then(function (output) {
                            return output.data;
                        });
                    }
                ]
            }
        });

    }
]);