(function () {
    'use strict';
    angular.module('app').directive('adminListViewItem', function (GLOBAL_CONFIG) {
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