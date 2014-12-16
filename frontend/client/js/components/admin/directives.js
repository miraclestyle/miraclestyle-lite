(function () {
    'use strict';
    angular.module('app').directive('adminDisplayListItem', function (GLOBAL_CONFIG) {
        return {
            scope: {
                ent: '=adminDisplayListItem'
            },
            restrict: 'A',
            template: '<span ng-include="template"></span>',
            link: function (scope, element, attrs) {
                var template = 'admin/directive/list/default.html';
                if ($.inArray(attrs.adminDisplayListKind, GLOBAL_CONFIG.admin.listDisplayDirective) !== -1) {
                    template = 'admin/directive/list/' + attrs.adminDisplayListKind + '.html';
                }
                scope.template = template;
            }
        };
    });
}());