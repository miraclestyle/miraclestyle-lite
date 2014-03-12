MainApp.factory('Nav', ['$rootScope', '$http', '$location', '$modal', 'Endpoint', 'Title',

    function ($rootScope, $http, $location, $modal, Endpoint, Title) {

        return {
            build_menu: function (params) {

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
            create: function () {
            	
                var that = this;

                var handle = function (data) {

                    var modalInstance = $modal.open({
                        templateUrl: logic_template('nav/create.html'),
                        controller: function ($scope, $modalInstance, RuleEngine) {

                            $scope.rule = RuleEngine.factory(data['entity']);
                            $scope.entity = data['entity'];
                            
                            $scope.save = function () {

                                Endpoint.post('update', '62', $scope.entity)
                                .success(function (data) {
 									 update($scope.entity, data['entity']);
 									 $scope.rule.update($scope.entity);
 							    });
                            };

                            $scope.cancel = function () {
                                $modalInstance.dismiss('cancel');
                            };

                        }
                    });
                };

                Endpoint.post('prepare', '62').success(handle);

            },
            update: function (entity) {
            	
                var that = this;

                var handle = function (data) {

                    var modalInstance = $modal.open({
                        templateUrl: logic_template('nav/update.html'),
                        controller: function ($scope, $modalInstance, RuleEngine) {

                            update(entity, data['entity']);

                            $scope.rule = RuleEngine.factory(data['entity']);

                            $scope.entity = entity;
                            $scope.history = {
                                'model': '62',
                                'args': {
                                    'key': entity['key'],
                                }
                            };
 
                            $scope.save = function () {

                                Endpoint.post('update', '62', $scope.entity)
                                .success(function (data) {

                                        update($scope.entity, data['entity']);
                                        $scope.rule.update($scope.entity);

                                });
                            };

                            $scope.cancel = function () {
                                $modalInstance.dismiss('cancel');
                            };

                        }
                    });

                };

                Endpoint.post('read', '62', {
                    'key': entity['key']
                }).success(handle);

            }

        };

    }
]);