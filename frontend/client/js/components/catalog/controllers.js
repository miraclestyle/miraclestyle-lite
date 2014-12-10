(function () {
    'use strict';
    // code for account
    angular.module('app')
        .controller('SellCatalogsCtrl', function ($scope, modals, modelsEditor, modelsMeta, models, modelsUtil) {

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

            $scope.manage = function (entity) {
                models['31'].manageModal(entity, newEntity);
            };

            $scope.search = {
                results: []
            };

            models['23'].current().then(function (response) {
                var args = modelsMeta.getActionArguments('31', 'search'),
                    sellerEntity = response.data.entity;
                args.search['default'].ancestor = response.data.entity.key;
                models['31'].actions.search({
                    search: args.search['default']
                }, {
                    ignoreErrors: true
                }).then(function (response) {
                    var errors = response.data.errors;
                    if (errors) {
                        if (errors['not_found_' + sellerEntity.key]) {
                            modals.alert('You need to update your seller details before making any catalogs!');
                        }
                    } else {
                        $scope.search.results = response.data.entities;
                    }
                });
            });
        });

}());
