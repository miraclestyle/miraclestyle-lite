(function () {
    'use strict';
    angular.module('app')
        .controller('AdminListCtrl', function ($scope, models, $stateParams, GLOBAL_CONFIG, searchBuilder, $state, helpers) {

            var kind = $stateParams.kind,
                query = null,
                args = {},
                getMaybeTemplate = GLOBAL_CONFIG.admin.listViewDirective[kind];

            try {
                query = helpers.url.jsonFromUrlsafe($stateParams.query);
                args = query;
            } catch (ignore) {}

            $scope.config = {
                titles: GLOBAL_CONFIG.admin.listTitles,
                kind: kind
            };

            $scope.maybeTemplate = (getMaybeTemplate === true ? 'admin/list_view/' + kind + '.html' : getMaybeTemplate);

            $scope.setPageToolbarTitle('admin.' + $scope.config.titles[kind]);

            $scope.manage = function (entity) {
                models[kind].adminManageModal(entity);
            };
            $scope.search = searchBuilder.create();
            $.extend($scope.search, {
                doSearch: function () {
                    $state.go('admin-list', {
                        kind: this.kind,
                        query: helpers.url.jsonToUrlsafe({
                            search : this.send
                        })
                    });
                },
                results: [],
                pagination: models[kind].paginate({
                    args: args,
                    kind: kind,
                    complete: function (response) {
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