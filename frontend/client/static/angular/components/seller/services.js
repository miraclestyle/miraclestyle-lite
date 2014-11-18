(function () {
    'use strict';
    angular.module('app').run(function ($window, modelsConfig, modelsMeta,
        modelsEditor, formInputTypes, underscoreTemplate, $modal, helpers, $q, $timeout, currentAccount) {

        modelsConfig(function (models) {
            formInputTypes.SuperPluginStorageProperty = function (info) {
                var config = info.config,
                    kinds = $.map(config.kinds, function (kind_id) {
                        var name = modelsMeta.getModelName(kind_id);
                        return {
                            key: kind_id,
                            name: name
                        };
                    });

                config.ui.specifics.parentArgs = info.scope.$eval(config.ui.args);
                config.ui.specifics.entity = info.scope.$eval(config.ui.model);

                info.scope.$watch(config.ui.args, function (neww, old) {

                    if (neww !== old) {
                        config.ui.specifics.parentArgs = neww;
                    }
                });

                var getPluginFieldOverrides = function (kind_id, field) {
                        var gets = defaultSpecifics.pluginFieldOverrides[kind_id];
                        if (angular.isDefined(gets) && angular.isDefined(gets[field])) {
                            return gets[field];
                        }
                        return {};
                    },
                    locationSpec = {
                        showListItem: 'address-rule-location-display',
                        listFields: [{
                            label: 'Location'
                        }],
                        sortFields: ['country', 'region', 'city', 'postal_code_from', 'postal_code_to'],
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

                            if (updated_address.country && ((!updated_address._country) || (updated_address.country !== updated_address._country.key))) {
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

                            if (promises.length) {
                                return $q.all(promises);
                            }

                            return false;

                        }
                    },
                    defaultSpecifics = {
                        pluginFieldOverrides: {
                            '113': {
                                lines: {
                                    ui: {
                                        specifics: {
                                            onlyListFields: ['name', 'active']
                                        }
                                    },
                                    modelclass: {
                                        rules: {
                                            ui: {
                                                specifics: {
                                                    listFields: [{
                                                        label: 'Condition',
                                                        key: 'condition'
                                                    }, {
                                                        label: 'Price',
                                                        key: 'price'
                                                    }],
                                                    showListItem: 'carrier-line-rule-display'
                                                }
                                            }
                                        },
                                        locations: {
                                            ui: {
                                                specifics: locationSpec
                                            }
                                        }
                                    }
                                }
                            },
                            '107': {
                                locations: {
                                    ui: {
                                        specifics: locationSpec
                                    }
                                }
                            },
                            '109': {
                                carriers: {
                                    ui: {
                                        specifics: {
                                            entities: function () {
                                                if (!config.ui.specifics.parentArgs) {
                                                    return [];
                                                }
                                                return $.map(config.ui.specifics.parentArgs,
                                                    function (item) {
                                                        if (item.active && item.kind === '113') {
                                                            return {
                                                                key: item.key,
                                                                name: item.name
                                                            };

                                                        }

                                                    });
                                            }
                                        }
                                    }
                                },
                                locations: {
                                    ui: {
                                        specifics: locationSpec
                                    }
                                }
                            }
                        },
                        showType: function (kind) {
                            return _.findWhere(kinds, {
                                key: kind
                            }).name;
                        },
                        kind: undefined,
                        selectKinds: {
                            type: 'SuperKeyProperty',
                            ui: {
                                specifics: {
                                    entities: kinds
                                },
                                args: 'info.kind',
                                label: 'Plugins',
                                attrs: {
                                    'ng-change': 'setNewArg()'
                                },
                                writable: true
                            },
                            code_name: 'kind'
                        },
                        remove: function (arg) {
                            config.ui.specifics.parentArgs.remove(arg);
                        },
                        manage: function (arg) {

                            if (!angular.isDefined(config.ui.specifics.templateUrl)) {
                                config.ui.specifics.templateUrl = 'underscore/form/modal/plugins.html';
                            }

                            $modal.open({
                                template: underscoreTemplate.get(config.ui.specifics.templateUrl)({
                                    config: config
                                }),
                                controller: function ($scope, $modalInstance,
                                    modelsUtil) {
                                    var is_new = false;

                                    if (!arg) {
                                        arg = {};
                                    }
                                    $scope.info = {
                                        build: true
                                    };
                                    $scope.config = config;
                                    $scope.setNewArg = function () {
                                        if ($scope.info.kind !== 0 && $scope.args.kind !== $scope.info.kind) {
                                            arg = {
                                                kind: $scope.info.kind
                                            };
                                            var length = config.ui.specifics.parentArgs.length;
                                            modelsUtil.normalize(arg, undefined, config.ui
                                                .specifics.entity, config.code_name,
                                                length, false);
                                            is_new = true;

                                            $scope.args = arg;
                                            $scope.getFormBuilder();
                                            $scope.info.build = false;

                                            $timeout(function () {
                                                $scope.info.build = true;
                                                $scope.$apply();
                                            }, 100);

                                        }
                                    };

                                    $scope.pluginTemplate = 'seller/plugin/default.html';
                                    $scope.formBuilder = [];
                                    $scope.getFormBuilder = function () {
                                        $scope.formBuilder = [];
                                        var kind = $scope.info.kind,
                                            settingsFields = config.ui.specifics.fields,
                                            fields = modelsMeta.getModelFields(kind);
                                        fields = _.toArray(fields);
                                        fields.sort(helpers.fieldSorter);
                                        if (settingsFields) {
                                            if (settingsFields[kind]) {
                                                fields = settingsFields[kind];
                                            }
                                        }

                                        angular.forEach(fields, function (field) {

                                            field.ui.formName = 'plugin_' + field.code_name;
                                            field.ui.writable = true;
                                            var extra = getPluginFieldOverrides(kind, field.code_name);
                                            if (extra) {
                                                $.extend(true, field, extra);
                                            }

                                            $scope.formBuilder.push(field);
                                        });
                                    };

                                    $scope.container = {};
                                    $scope.args = angular.copy(arg);
                                    // entity.addreses.0.address
                                    $scope.parentArgs = config.ui.specifics.parentArgs;
                                    // entity.addresses
                                    $scope.entity = config.ui.specifics.entity;

                                    if ($scope.args && $scope.args.kind) {
                                        $scope.info.kind = $scope.args.kind;
                                        $scope.getFormBuilder();

                                    }

                                    $scope.close = function () {
                                        $modalInstance.dismiss('cancel');
                                    };

                                    $scope.save = function () {

                                        if (!$scope.container.form.$valid) {
                                            return;
                                        }
                                        var promise, complete;
                                        if (angular.isFunction(config.ui.specifics.beforeSave)) {
                                            promise = config.ui.specifics.beforeSave($scope, info);
                                        }

                                        complete = function () {
                                            promise = null;
                                            if (is_new) {
                                                $scope.parentArgs.unshift($scope.args);
                                                var total = $scope.parentArgs.length;
                                                angular.forEach($scope.parentArgs, function (item, i) {
                                                    i = total - i;
                                                    item._sequence = i;
                                                    item.sequence = i;
                                                });
                                            } else {
                                                $.extend(arg, $scope.args);
                                            }

                                            if (angular.isFunction(config.ui.specifics.afterSave)) {
                                                promise = config.ui.specifics.afterSave($scope, info);
                                            }

                                            if (promise && promise.then) {
                                                promise.then(function () {
                                                    $scope.close();
                                                });
                                            } else {
                                                $scope.close();
                                            }

                                        };

                                        if (promise && promise.then) {
                                            promise.then(complete);

                                        } else {
                                            complete();

                                        }

                                    };

                                }
                            });
                        }
                    };

                angular.forEach(defaultSpecifics, function (v, k) {
                    if (config.ui.specifics[k] === undefined) {
                        config.ui.specifics[k] = v;
                    }
                });

                return 'plugins';
            };
        });


        modelsConfig(function (models) {
            var read_arguments = {
                _address: {},
                _content: {},
                _plugin_group: {}
            };

            $.extend(models['23'], {
                current: function (args) {
                    if (!args) {
                        args = {};
                    }
                    args.account = currentAccount.key;
                    return this.actions.read(args, {
                        cache: 'currentSeller',
                        cacheType: 'memory'
                    });
                },
                settingsModal: function (account_key) {
                    var fields = modelsMeta.getActionArguments(this.kind, 'update'), config;
                    fields._content.ui.label = false;
                    fields._content.modelclass.documents.ui = {
                        label: false,
                        specifics: {
                            addText: 'Add Content',
                            listFields: [{
                                label: 'Title',
                                key: 'title'
                            }]
                        }
                    };
                    fields.logo.ui.specifics = {
                        displayImageConfig: {
                            size: 240
                        }
                    };
                    fields._plugin_group.ui.label = false;
                    fields.address.ui.specifics = {
                        sortFields: ['country', 'region', 'city',
                            'postal_code', 'street', 'email', 'telephone'],
                    };

                    config = {
                        kind: this.kind,
                        action: 'update',
                        fields: fields,
                        excludeFields: ['account', 'read_arguments'],
                        templateBodyUrl: 'seller/settings.html',
                        argumentLoader: function ($scope) {
                            var args = this.defaultArgumentLoader($scope);
                            args.account = account_key;
                            args.read_arguments = read_arguments;
                            return args;
                        },
                        scope: {
                            accordions: {
                                closeOthers: true,
                                general: {
                                    label: 'General',
                                    open: true
                                },
                                plugins: {
                                    label: 'Plugins',
                                    open: false
                                },
                                contents: {
                                    label: 'Contents',
                                    open: false
                                }
                            }
                        }
                    };

                    modelsEditor.create(config).read({}, {
                        account: account_key,
                        read_arguments: read_arguments
                    });

                }
            });

        });

    });
}());
