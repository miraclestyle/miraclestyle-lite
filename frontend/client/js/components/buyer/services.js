(function () {
    'use strict';
    angular.module('app').run(function ($window, modelsEditor, modelsMeta, $q, modelsConfig, currentAccount, endpoint) {

        modelsConfig(function (models) {

            $.extend(models['19'], {
                current: function (args) {
                    if (!args) {
                        args = {};
                    }
                    args.account = currentAccount.key;
                    return this.actions.read(args, {
                        cache: this.getCacheKey('current'),
                        cacheType: 'memory'
                    });
                },
                manageModal: function (accountKey) {
                    var fields = modelsMeta.getActionArguments(this.kind, 'update'),
                        addressFields = fields.addresses.modelclass,
                        that = this,
                        config;
                    fields.addresses.ui = {
                        label: false,
                        specifics: {
                            addText: 'Add Address',
                            listFields: [{
                                label: 'Address'
                            }],
                            showListItem: 'buyer-address-display',
                            sortFields: ['country', 'region', 'city', 'postal_code',
                                'street', 'name', 'email', 'telephone'],
                            afterSave: function () {
                                endpoint.removeCache(that.getCacheKey('current'));
                            },
                            init: function ($scope) {

                                var remove = $scope.config.ui.specifics.remove;

                                $scope.config.ui.specifics.remove = function () {
                                    remove.apply(this, arguments);
                                };

                            },
                            beforeSave: function ($scope, info) {
                                var promises = [],
                                    updatedAddress = $scope.args,
                                    promise;
                                if (updatedAddress.region && (!updatedAddress._region || (updatedAddress.region !== updatedAddress._region.key))) {
                                    promise = models['13'].get(updatedAddress.region);
                                    promise.then(function (response) {
                                        if (response.data.entities.length) {
                                            updatedAddress._region = response.data.entities[0];
                                        }

                                    });

                                    promises.push(promise);
                                }

                                if (updatedAddress.country && (!updatedAddress._country || (updatedAddress.country !== updatedAddress._country.key))) {
                                    promise = models['12'].actions.search(undefined, {
                                        cache: true
                                    });
                                    promise.then(function (response) {
                                        if (response.data.entities.length) {
                                            var country = _.findWhere(response.data.entities, {
                                                key: updatedAddress.country
                                            });
                                            if (angular.isDefined(country)) {
                                                updatedAddress._country = country;
                                            }

                                        }

                                    });

                                    promises.push(promise);
                                }
                                if (promises.length) {
                                    return $q.all(promises);
                                }

                                return false;

                            }

                        }
                    };

                    addressFields.country.ui.placeholder = 'Select address country (e.g., USA). This value is Required!';
                    addressFields.region.ui.placeholder = 'Select address region (e.g., California). This value is Optional!';
                    addressFields.city.ui.placeholder = 'Type in address city name (e.g., Beverly Hills). This value is Required!';
                    addressFields.postal_code.ui.placeholder = 'Type in address postal code (e.g., 90210). This value is Required!';
                    addressFields.street.ui.placeholder = 'Type in address street (e.g., Rodeo Drive). This value is Required!';
                    addressFields.name.ui.placeholder = 'Type in contact name (e.g., John Doe). This value is Required!'; // example
                    addressFields.email.ui.placeholder = 'Type in contact email (e.g., johndoe@example.com). This value is Optional.';
                    addressFields.telephone.ui.placeholder = 'Type in contact telephone number. Prefix phone with plus (+) sign, and all calling codes, starting with country code (e.g., ). This value is Optional.';

                    config = {
                        fields: [fields.addresses],
                        kind: this.kind,
                        action: 'update',
                        excludeFields: ['account', 'read_arguments'],
                        argumentLoader: function ($scope) {
                            var args = this.defaultArgumentLoader($scope);
                            args.account = accountKey;
                            return args;
                        }
                    };

                    modelsEditor.create(config).read({}, {
                        account: accountKey
                    });
                }
            });

        });

    });
}());
