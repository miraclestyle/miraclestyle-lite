angular.module('app').config(['$stateProvider',
function($stateProvider) {
  
  'use strict';
  
  var default_resolves = {
    current_account : ['Endpoint', '$rootScope',
    function(Endpoint, $rootScope) {
      Endpoint.current_account().then(function(response) {
        var account = response.data;
        $rootScope.current_account = account;
        return account;
      });

    }]
  };

  $stateProvider.state('home', {
    url : '/',
    templateUrl : 'home/index.html',
    controller : 'HomePage',
    resolve: default_resolves
  }).state('login', {
    url : '/login/:provider',
    controller : 'LoginPage'
  }).state('sell-catalogs', {
    url : '/sell/catalogs',
    controller : 'SellCatalogs',
    templateUrl : 'catalog/list.html',
    resolve : default_resolves
  })
  .state('tests', {
    url : '/tests/:what',
    controller : 'Tests',
    templateUrl : function (stateParams) {
      return 'tests/' + stateParams.what + '.html';
    },
    resolve : default_resolves
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
    controller : 'AdminSearch',
    resolve : default_resolves
  });

}]);
