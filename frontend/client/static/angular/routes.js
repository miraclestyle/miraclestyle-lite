angular.module('app').config(['$stateProvider',
function($stateProvider) {
 

  $stateProvider.state('home', {
    url : '/',
    templateUrl : 'home/index.html',
    controller : 'HomePage'
  }).state('login', {
    url : '/login/:provider',
    controller : 'LoginPage'
  }).state('sell-catalogs', {
    url : '/sell/catalogs',
    controller : 'SellCatalogs',
    templateUrl : 'catalog/list.html'
  })
  .state('tests', {
    url : '/tests/:what',
    controller : 'Tests',
    templateUrl : function (stateParams) {
      return 'tests/' + stateParams.what + '.html';
    }
  })
  .state('admin_search', {
    url : '/admin/search/:kind/:query',
    templateUrl : function(stateParams) {

      var defaults = 'admin/search.html',
          config;

      if (stateParams.kind !== undefined) {
        config = ADMIN_SEARCH_KIND_CONFIG[stateParams.kind];
        if (config && config.templateUrl) {
          defaults = config.templateUrl;
        }
      }

      return defaults;
    },
    controller : 'AdminSearch'
  });

}]);
