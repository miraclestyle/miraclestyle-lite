(function () {
    'use strict';
    angular.module('app')
        .controller('AdminListCtrl', function ($scope, models, $stateParams, GLOBAL_CONFIG, searchBuilder, $state, $rootScope) {

            var kind = $stateParams.kind,
                query = null,
                args = {};

            try {
                query = JSON.parse($stateParams.query);
                args = query;
            } catch (ignore) {}

            $scope.config = {
                titles: GLOBAL_CONFIG.admin.listTitles,
                kind: kind
            };

            $rootScope.pageTitle = 'Administer ' + $scope.config.titles[kind];

            $scope.manage = function (entity) {
                models[kind].manageModal(entity);
            };
            $scope.search = searchBuilder.create();
            $.extend($scope.search, {
                doSearch: function () {
                    $state.go('admin-list', {
                        kind: this.kind,
                        query: JSON.stringify({
                            search : this.send
                        })
                    });
                },
                results: [],
                pagination: models[kind].paginate({
                    args: args,
                    kind: kind,
                    callback: function (response) {
                        $scope.search.results.extend(response.data.entities);
                    }
                })
            });

            $scope.search.kind = kind;
            if (!query) {
                query = $scope.search.pagination.args;
            }
            $scope.search.changeKindUI();
            if (query) {
                $scope.search.setSearch(kind, query.search);
            }
            $scope.scrollEnd = {loader: $scope.search.pagination};
            $scope.search.pagination.load();


        });
}());
