angular.module('app').filter('displayProvider', function (LOGIN_PROVIDERS) {
  return function (value) {
    var splits = value.split('-'),
      out = '';
    if (splits && splits[1]) {
      out = LOGIN_PROVIDERS[splits[1]];
    }
    return out;
  };
});