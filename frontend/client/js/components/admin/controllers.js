(function () {
    'use strict';
    angular.module('app')
        .controller('AdminListCtrl', function ($scope, models, $stateParams, GLOBAL_CONFIG) {
            var kind = $stateParams.kind;

            $scope.config = {};

            $scope.config.titles = GLOBAL_CONFIG.admin.listTitles;

            $scope.config.kind = kind;

            $scope.manage = function (entity) {
                models[kind].manageModal(entity);
            };

            $scope.search = {
                results: [],
                pagination: {}
            };

            $scope.search.pagination = models[kind].paginate({
                kind: kind,
                callback: function (response) {
                    $scope.search.results.extend(response.data.entities);
                }
            });

            $scope.search.pagination.load();


        });
}());
