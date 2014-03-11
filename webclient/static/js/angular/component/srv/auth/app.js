SEARCH_KIND_FIELDS = {
    '62': [{
        'label': 'Name',
        'key': 'name'
    }, {
        'label': 'Active',
        'key': 'active'
    }]
};

SEARCH_KIND_TITLE = {
    '62': 'Widgets',
};

SEARCH_KIND_ADD_NEW = {
    '62': 'Add New',
};

MainApp.factory('App', ['$rootScope', '$http', '$location', '$modal', 'Endpoint', 'Title',

    function ($rootScope, $http, $location, $modal, Endpoint, Title) {

        return {
            get_menu: function (params) {

                if(!$rootScope.nav['menu']) {
                    return Endpoint.post('build_menu', '62', {
                        'domain': params['app_id']
                    }).then(function (output) {
                        update($rootScope.nav, output.data);
                        Title.set(['My Apps', $rootScope.nav.domain.name]);
                        return output.data;
                    });
                } else {
                    Title.set(['My Apps', $rootScope.nav.domain.name]);
                    return $rootScope.nav;
                }

            },
            search: function (args, config) {
                return Endpoint.post('apps', '0', args, config);
            },
            sudo_search: function (args, config) {
                return Endpoint.post('sudo_search', '6', args, config);
            },
            create: function () {
                var that = this;

                var handle = function (data) {

                    var modalInstance = $modal.open({
                        templateUrl: logic_template('srv/auth', 'app_create.html'),
                        controller: function ($scope, $modalInstance, RuleEngine, Confirm) {

                            $scope.rule = RuleEngine.factory(data['entity']);
                            $scope.app = {};
                            $scope.step = 1;
                            $scope.upload_url = data.upload_url;


                            $scope.nextStep = function (which_step) {
                                $scope.step = which_step;
                            };

                            $scope.completed = function (data) {
                                if(data['entity']) {

                                    Confirm.notice('Your app is now in process of creation, you will recieve an e-mail as soon as the application is created.',
                                        function () {
                                            $scope.cancel();
                                        });
                                } else {

                                    Confirm.notice('An error occurred, please try again.', function () {
                                        Endpoint.post('prepare', '6', {
                                            'upload_url': Endpoint.url
                                        }).success(function (data) {

                                            $scope.upload_url = data.upload_url;
                                        });
                                    });

                                }

                            };

                            $scope.cancel = function () {
                                $modalInstance.dismiss('cancel');
                            };

                        }
                    });

                };

                Endpoint.post('prepare', '6', {
                    'upload_url': Endpoint.url
                }).success(handle);

            },
            update: function (app) {
                var that = this;

                var handle = function (data) {

                    var modalInstance = $modal.open({
                        templateUrl: logic_template('srv/auth', 'app_update.html'),
                        controller: function ($scope, $modalInstance, RuleEngine) {

                            update(app, data['entity']);

                            $scope.rule = RuleEngine.factory(data['entity']);

                            $scope.app = app;
                            $scope.history = {
                                'model': '6',
                                'args': {
                                    'key': app['key'],
                                }
                            };

                            $parentScope = $scope;

                            $scope.sudo = function () {
                                var handle = function () {

                                    var modalInstance = $modal.open({
                                        templateUrl: logic_template('admin', 'sudo.html'),
                                        windowClass: 'modal-medium',
                                        controller: function ($scope, $modalInstance, RuleEngine) {

                                            $scope.rule = $parentScope.rule;
                                            $scope.log = {
                                                'message': '',
                                                'note': '',
                                                'state': app['state'],
                                                'key': app['key'],
                                            };

                                            $scope.save = function () {

                                                Endpoint.post('sudo', '6', $scope.log)
                                                    .success(function (data) {

                                                        update(app, data['entity']);

                                                        $scope.rule.update(data['entity']);

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

                            $scope._do_user_admin = function (app, action) {

                                var handle = function () {

                                    var modalInstance = $modal.open({
                                        templateUrl: logic_template('srv/auth', 'app_user_admin.html'),
                                        windowClass: 'modal-medium',
                                        controller: function ($scope, $modalInstance, RuleEngine, $timeout) {

                                            $scope.rule = $parentScope.rule;
                                            $scope.action = action;
                                            $scope.log = {
                                                'message': '',
                                                'key': app['key'],
                                            };

                                            $scope.save = function () {

                                                Endpoint.post(action, 'srv.auth.Domain', $scope.log)
                                                    .success(function (data) {

                                                        update(app, data['entity']);

                                                        $scope.rule.update(data['entity']);

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

                            $scope.suspend = function () {
                                this._do_user_admin(app, 'suspend');
                            };

                            $scope.activate = function () {
                                this._do_user_admin(app, 'activate');
                            };

                            $scope.save = function () {

                                Endpoint.post('update', '6', {
                                    'name': $scope.app['name'],
                                    'primary_contact': $scope.app['primary_contact'],
                                    'key': $scope.app['key'],
                                })
                                    .success(function (data) {

                                        update($scope.app, data['entity']);

                                        $scope.rule.update(data['entity']);

                                    });

                            };

                            $scope.cancel = function () {
                                $modalInstance.dismiss('cancel');
                            };

                        }
                    });

                };

                Endpoint.post('read', '6', {
                    'key': app['key']
                }).success(handle);

            }

        };

    }
])
    .controller('AppView', ['$scope', '$stateParams', '$rootScope', '$state',
        function ($scope, $stateParams, $rootScope, $state) {

            var nav = $rootScope.nav;
            var menu = nav['menu'][0]['filters'][0];

            $state.go('app_view_search', {
                'app_id': nav.domain.key,
                'kind': menu['kind'],
                'query': JSON.stringify(menu['query'])
            });

        }
    ])
    .controller('AppSearch', ['$scope', 'Title', 'Endpoint', '$stateParams', '$rootScope', 'RuleEngine', 'search',
        function ($scope, Title, Endpoint, $stateParams, $rootScope, RuleEngine, search) {

            angular.forEach(search.entities, function (value) {
                value.rule = RuleEngine.factory(value);
            });

            var kind = $stateParams['kind'];

            $scope.search = search;
            $scope.fields = SEARCH_KIND_FIELDS[kind];
            $scope.title = SEARCH_KIND_TITLE[kind];
            $scope.add_new = SEARCH_KIND_ADD_NEW[kind];

            $scope.create = function () {

            };

            $scope.update = function (entity) {

            };

        }
    ])
    .controller('AppList', ['$scope', 'App', 'apps', 'Confirm', 'RuleEngine', 'Title',
        function ($scope, App, apps, Confirm, RuleEngine, Title) {

            Title.set('My Apps');

            apps = apps.entities;

            angular.forEach(apps, function (app, key) {
                app.domain.rule = RuleEngine.factory(app.domain); // compile rule engine for each domain in the list
                app.user.rule = RuleEngine.factory(app.user); // compile rule engine for each domain user in the list
            });

            $scope.apps = apps;

            $scope.toggleMainMenu(1);

            $scope.updateApp = function (app) {
                App.update(app);
            };

            $scope.createApp = function () {
                App.create();
            };

        }
    ])
    .run(['$rootScope', '$location', 'Account', 'Endpoint',
        function ($rootScope, $location, Account, Endpoint) {

            $rootScope.nav = {};

            $rootScope.doLogin = function () {
                Account.ask_login(function () {
                    $location.path('/');
                });
            };

            $rootScope.doLogout = function () {

                Account.logout(function () {
                    $location.path('/');
                });

            };

        }
    ]);