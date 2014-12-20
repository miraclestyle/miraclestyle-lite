(function () {
    'use strict';
    // code for account
    angular.module('app')
        .controller('SellCatalogsCtrl', function ($scope, modals, modelsEditor, modelsMeta, models, modelsUtil, visualAid) {

            var newEntity = function (entity) {
                if (!_.findWhere($scope.search.results, {
                        key: entity.key
                    })) {
                    $scope.search.results.unshift(entity);
                }
            };

            $scope.create = function () {
                models['31'].manageModal(undefined, newEntity);
            };

            $scope.preview = function (key) {
                models['31'].previewModal(key);
            };

            $scope.manage = function (entity) {
                models['31'].manageModal(entity, newEntity);
            };


            $scope.search = {
                results: [],
                pagination: {}
            };

            $scope.scrollEnd = {loader: false};

            models['23'].current().then(function (response) {
                var sellerEntity = response.data.entity;
                $scope.search.pagination = models['31'].paginate({
                    kind: '31',
                    args: {
                        search: {
                            ancestor: sellerEntity.key
                        }
                    },
                    config: {
                        ignoreErrors: true
                    },
                    callback: function (response) {
                        var errors = response.data.errors;
                        if (errors) {
                            if (errors['not_found_' + sellerEntity.key]) {
                                modals.alert('You do not have any seller information yet.');
                            }
                        } else {
                            $scope.search.results.extend(response.data.entities);
                        }
                    }
                });
                $scope.scrollEnd.loader = $scope.search.pagination;
                $scope.search.pagination.load();
            });

        });

}());
