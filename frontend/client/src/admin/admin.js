(function () {
    'use strict';
    angular.module('app')
        .controller('AdminListCtrl', function ($scope, models, $stateParams, GLOBAL_CONFIG, searchBuilder, $state, $rootScope, helpers) {

            var kind = $stateParams.kind,
                query = null,
                args = {};

            try {
                query = helpers.url.jsonFromUrlsafe($stateParams.query);
                args = query;
            } catch (ignore) {}

            $scope.config = {
                titles: GLOBAL_CONFIG.admin.listTitles,
                kind: kind
            };

            $rootScope.pageTitle = 'Administer ' + $scope.config.titles[kind];

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


        }).directive('adminListViewItem', function (GLOBAL_CONFIG) {
            return {
                scope: {
                    ent: '=adminListViewItem'
                },
                restrict: 'A',
                template: '<span ng-include="template"></span>',
                link: function (scope, element, attrs) {
                    var template = 'admin/list_view/default.html';
                    if ($.inArray(attrs.adminListViewKind, GLOBAL_CONFIG.admin.listViewDirective) !== -1) {
                        template = 'admin/list_view/' + attrs.adminListViewKind + '.html';
                    }
                    scope.template = template;
                }
            };
        });
}());