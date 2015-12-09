(function () {
    'use strict';
    angular.module('app').run(ng(function (modelsConfig, helpers, modelsMeta) {
        modelsConfig(function (models) {
            models['12'].config.cache = true;
            models['12'].get = function (key, opts) {
                opts = helpers.alwaysObject(opts);
                $.extend(opts, {
                    cache: 'all_countries',
                    cacheType: 'local'
                });
                return this.actions.search({
                    orders: [{
                        operator: "asc",
                        field: "name"
                    }],
                    filters: [{
                        operator: "==",
                        field: "active",
                        value: true
                    }]
                }, opts).then(function (response) {
                    return _.findWhere(response.data.entities, {
                        key: key
                    });
                });
            };

            var get13 = models['13'].get;
            models['13'].get = function (key, countryKey, opts) {
                if (!countryKey) {
                    return get13.apply(this, arguments);
                }
                opts = helpers.alwaysObject(opts);
                $.extend(opts, {
                    cache: countryKey + '_all_regions',
                    cacheType: 'local'
                });
                return this.actions.search({
                    "search": {
                        "ancestor": countryKey,
                        "filters": [{
                            "value": true,
                            "field": "active",
                            "operator": "=="
                        }],
                        "orders": [{
                            "field": "name",
                            "operator": "asc"
                        }]
                    }
                }, opts).then(function (response) {
                    return _.findWhere(response.data.entities, {
                        key: key
                    });
                });
            };

        });

    }));
}());
