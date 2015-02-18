(function () {
    'use strict';
    angular.module('app')
        .controller('HistoryListingCtrl', function ($scope, models, $modal) {

            var config = $scope.historyConfig,
                loaded = false,
                defaultReaderOpts = {
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

            $scope.history = {
                records: [],
                reader: models[config.kind].reader(defaultReaderOpts),
                view: function (record) {
                    $modal.open({
                        templateUrl: 'core/form/manage_entity.html',
                        controller: function ($scope) {
                            $scope.record = record;
                            $scope.dialog = {};
                            $scope.dialog.templateBodyUrl = 'core/misc/history_view_body.html';
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

            $scope.$watch('accordion.open', function (opened, oldState) {
                if (opened && !loaded && $scope.history.reader.config.key) {
                    $scope.history.reader.load();
                    loaded = true;
                }
            });

            $scope.$watch('entity.key', function (old, neww) {
                if (old !== neww) {
                    $scope.history.reader.config.key = neww;
                }
            });

        });
}());
