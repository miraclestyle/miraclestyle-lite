MainApp.config(['$stateProvider',
    function ($stateProvider) {

        var resolve_menu = ['Nav', '$stateParams',
            function (Nav, $stateParams) {
                return Nav.build_menu($stateParams['domain_key']);
            }
        ];

        $stateProvider.state('home', {
            url: '/',
            templateUrl: logic_template('home/index.html'),
            controller: 'HomePage'
        })
            .state('login', {
                url: '/login/:provider',
                controller: 'LoginPage',
            })
            .state('apps', {
                url: '/apps',
                templateUrl: logic_template('app/apps.html'),
                controller: 'AppList',
                resolve: {
                    apps: ['App', '$rootScope',
                        function (App, $rootScope) {

                            return App.search({
                                'key': $rootScope.current_user.key
                            }).then(function (output) {
                                return output.data;
                            });
                        }
                    ]
                }
            })
            .state('app_view', {
                url: '/app/:domain_key',
                template: '',
                controller: 'AppView',
                resolve: {
                    menu: resolve_menu,
                }
            })
            .state('app_view_search', {
                url: '/app/:domain_key/search/:kind/:query',
                templateUrl: function (stateParams) {

                    var defaults = logic_template('app/search.html');

                    if(stateParams['kind'] != undefined) {
                        var config = SEARCH_KIND_CONFIG[stateParams['kind']];
                        if(config && config['templateUrl']) {
                            defaults = config['templateUrl'];
                        }

                    }

                    return defaults;
                },
                controller: 'AppSearch',
                resolve: {
                    menu: resolve_menu,
                    search: ['Endpoint', '$stateParams', '$rootScope',
                        function (Endpoint, $stateParams, $rootScope) {

                            var query = JSON.parse($stateParams['query']);

                            if(!angular.isObject(query)) query = {};

                            query['domain'] = $stateParams['domain_key'];

                            $rootScope.search.setSearch($stateParams['kind'], query['search']);

                            return Endpoint.post('search', $stateParams['kind'], query).then(function (output) {
                                return output.data;
                            });

                        }
                    ]
                }
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

                            return Endpoint.post('search', $stateParams['kind'], query).then(function (output) {
                                return output.data;
                            });
                        }
                    ]
                }
            });

    }
]);