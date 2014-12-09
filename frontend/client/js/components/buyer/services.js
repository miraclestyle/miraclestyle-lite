(function () {
    'use strict';
    angular.module('app').run(function ($window, modelsEditor, modelsMeta, $q, modelsConfig) {

        modelsConfig(function (models) {

            models['19'].settingsModal = function (account_key) {
                var fields = modelsMeta.getActionArguments(this.kind, 'update'),
                    addressFields = fields.addresses.modelclass,
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
                            'street', 'name', 'email', 'telephone',
                            'default_shipping', 'default_billing'],
                        beforeSave: function ($scope, info) {
                            var promises = [],
                                updated_address = $scope.args,
                                promise;
                            if (updated_address.region && (!updated_address._region || (updated_address.region !== updated_address._region.key))) {
                                promise = models['13'].get(updated_address.region);
                                promise.then(function (response) {
                                    if (response.data.entities.length) {
                                        updated_address._region = response.data.entities[0];
                                    }

                                });

                                promises.push(promise);
                            }

                            if (updated_address.country && (!updated_address._country || (updated_address.country !== updated_address._country.key))) {
                                promise = models['12'].actions.search(undefined, {
                                    cache: true
                                });
                                promise.then(function (response) {
                                    if (response.data.entities.length) {
                                        var country = _.findWhere(response.data.entities, {
                                            key: updated_address.country
                                        });
                                        if (angular.isDefined(country)) {
                                            updated_address._country = country;
                                        }

                                    }

                                });

                                promises.push(promise);
                            }

                            angular.forEach($scope.parentArgs, function (address) {
                                if (updated_address.default_billing || updated_address.default_shipping) {
                                    if (updated_address !== address) {

                                        if (updated_address.default_billing) {
                                            address.default_billing = false;
                                        }

                                        if (updated_address.default_shipping) {
                                            address.default_shipping = false;
                                        }
                                    }

                                }

                            });
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
                        args.account = account_key;
                        return args;
                    }
                };

                modelsEditor.create(config).read({}, {
                    account: account_key
                });

            };

        });

    });
}());