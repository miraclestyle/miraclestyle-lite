(function () {
    'use strict';
    angular.module('app')
        .controller('HistoryListingCtrl', function ($scope, models) {

            var config = $scope.historyConfig,
                loaded = false,
                defaultReaderOpts = {
                    access: ['_records'],
                    key: config.key,
                    next: {_records: {config: {more: true}}},
                    kind: config.kind,
                    complete: function (records) {
                        $scope.history.records.extend(records);
                    }
                };

            $.extend(defaultReaderOpts, config.reader);

            $scope.history = {
                records: [],
                reader: models[config.kind].reader(defaultReaderOpts)
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