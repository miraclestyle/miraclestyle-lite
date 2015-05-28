(function () {
    'use strict';
    angular.module('app')
        .factory('recordBrowser', ng(function (models, GLOBAL_CONFIG, $modal) {
            return {
                attach: function (config) {
                    return {
                        label: GLOBAL_CONFIG.subheaders.history,
                        include: 'core/misc/action.html',
                        action: function () {
                            $modal.open({
                                templateUrl: 'core/models/manage.html',
                                controller: ng(function ($scope) {
                                    $scope.dialog = {
                                        templateBodyUrl: 'core/record/list.html',
                                        toolbar: {
                                            hideSave: true,
                                            leftIcon: 'navigation.arrow-back',
                                            title: config.title + ' / History'
                                        }
                                    };
                                    var defaultReaderOpts = {
                                            access: ['_records'],
                                            key: config.key,
                                            next: {
                                                _records: {
                                                    config: {
                                                        more: true,
                                                        search: {
                                                            orders: [{
                                                                field: 'logged',
                                                                operator: 'desc'
                                                            }]
                                                        }
                                                    }
                                                }
                                            },
                                            complete: function (records) {
                                                $scope.history.records.extend(records);
                                            }
                                        };

                                    $.extend(defaultReaderOpts, config.reader);

                                    $scope.close = $scope.$close;

                                    $scope.history = {
                                        records: [],
                                        reader: models[config.kind].reader(defaultReaderOpts),
                                        view: function (record) {
                                            $modal.open({
                                                templateUrl: 'core/models/manage.html',
                                                controller: ng(function ($scope) {
                                                    $scope.record = record;
                                                    $scope.dialog = {};
                                                    $scope.dialog.templateBodyUrl = 'core/record/view_body.html';
                                                    $scope.dialog.toolbar = {
                                                        hideSave: true,
                                                        title: 'Log for date  ' + record.logged
                                                    };
                                                    $scope.close = function () {
                                                        $scope.$close();
                                                    };
                                                })
                                            });
                                        }
                                    };

                                    $scope.history.reader.load();
                                })
                            });

                        }
                    };
                }
            };
        }));
}());