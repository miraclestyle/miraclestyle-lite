(function () {
    'use strict';
    angular.module('app')
        .factory('recordBrowser', function (models, $modal) {
            return {
                attach: function (config) {
                    return {
                        label: 'History',
                        include: 'core/misc/action.html',
                        action: function () {
                            $modal.open({
                                templateUrl: 'core/models/manage.html',
                                controller: function ($scope) {
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
                                            kind: config.kind,
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
                                                controller: function ($scope) {
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
                                                }
                                            });
                                        }
                                    };

                                    $scope.history.reader.load();
                                }
                            });

                        }
                    };
                }
            };
        });
}());