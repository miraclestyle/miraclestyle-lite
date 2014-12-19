(function () {
    'use strict';
    angular.module('app').run(function ($window, modelsConfig, modelsMeta,
        modelsEditor, formInputTypes, underscoreTemplate, $modal, modals, helpers, $q, $timeout, currentAccount, $filter) {

        modelsConfig(function (models) {
            formInputTypes.SuperPluginStorageProperty = function (info) {
                var config = info.config,
                    kinds = $.map(config.kinds, function (kind_id) {
                        var name = modelsMeta.getName(kind_id);
                        return {
                            key: kind_id,
                            name: name
                        };
                    }),
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
                        sortableOptions: {
                            disabled: false,
                            start: function (e, ui) {
                                info.scope.$broadcast('itemOrderStarted');
                            },
                            whatSortMeans: function () {
                                modals.alert('Grab the button to start sorting.');
                            },
                            handle: '.sort-handle',
                            sort: function (e, ui) {
                                var sample = ui.placeholder.next();
                                if (sample.length) {
                                    ui.placeholder.width(sample.width()).height(sample.height());
                                }
                                info.scope.$broadcast('itemOrderSorting');
                            }
                        },
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
                            arg._state = 'deleted';
                            info.scope.$emit('itemDelete', arg);
                            info.scope.$broadcast('itemDelete', arg);
                        },
                        create: function () {
                            return this.manage();
                        },
                        manage: function (arg) {

                            if (!angular.isDefined(config.ui.specifics.templateUrl)) {
                                config.ui.specifics.templateUrl = 'underscore/form/modal/plugins.html';
                            }

                            $modal.open({
                                template: underscoreTemplate.get(config.ui.specifics.templateUrl)({
                                    config: config
                                }),
                                controller: function ($scope, $modalInstance, modelsUtil) {
                                    var is_new = false,
                                        inflector = $filter('inflector'),
                                        resetFormBuilder = function () {
                                            $scope.accordions = {
                                                closeOthers: true,
                                                groups: [{
                                                    label: 'General',
                                                    disabled: false,
                                                    open: true
                                                }]
                                            };
                                            $scope.formBuilder = {
                                                '0': [config.ui.specifics.selectKinds]
                                            };
                                        };

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
                                            modelsUtil.normalize(arg, undefined, config.ui.specifics.entity, config.code_name,
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

                                    resetFormBuilder();

                                    $scope.getFormBuilder = function () {
                                        resetFormBuilder();
                                        var kind = $scope.info.kind,
                                            settingsFields = config.ui.specifics.fields,
                                            fields = modelsMeta.getFields(kind),
                                            realTotal = 0,
                                            found = false;
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
                                            var extra = getPluginFieldOverrides(kind, field.code_name),
                                                next;
                                            if (extra) {
                                                helpers.extendDeep(field, extra);
                                            }

                                            if (field.is_structured && formInputTypes[field.type]) {
                                                $scope.accordions.groups.push({
                                                    label: inflector((field.ui.label || field.code_name), 'humanize'),
                                                    disabled: false,
                                                    open: false
                                                });

                                                field.ui.label = false;

                                                next = $scope.accordions.groups.length - 1;

                                                if (!angular.isDefined($scope.formBuilder[next])) {
                                                    $scope.formBuilder[next] = [];
                                                    $scope.formBuilder[next].push(field);
                                                }

                                                $scope.accordions.groups[0].disabled = false;
                                            } else {
                                                $scope.formBuilder['0'].push(field);
                                            }
                                        });

                                        angular.forEach($scope.accordions.groups, function (group, i) {
                                            if ($scope.formBuilder[i].length) {
                                                realTotal += 1;
                                            }
                                            if (found !== false) {
                                                return;
                                            }
                                            if ($scope.formBuilder[i].length) {
                                                group.open = true;
                                                found = group;
                                            } else {
                                                group.open = false;
                                            }
                                        });

                                        if (realTotal === 1) {
                                            found.disabled = true;
                                        }

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

                                    $scope.validateForm = function () {
                                        if (!$scope.container.form.$valid) {
                                            $scope.$broadcast('invalidForm');
                                            return false;
                                        }
                                        return true;
                                    };

                                    $scope.save = function () {
                                        var promise, complete;
                                        if (!$scope.validateForm()) {
                                            return;
                                        }

                                        if (angular.isFunction(config.ui.specifics.beforeSave)) {
                                            promise = config.ui.specifics.beforeSave($scope, info);
                                        }

                                        complete = function () {
                                            var newPromise = null,
                                                total = 0;
                                            if (is_new) {
                                                $scope.parentArgs.unshift($scope.args);
                                                total = $scope.parentArgs.length;
                                                angular.forEach($scope.parentArgs, function (item, i) {
                                                    i = total - i;
                                                    item._sequence = i;
                                                });
                                            } else {
                                                $.extend(arg, $scope.args);
                                            }

                                            if (angular.isFunction(config.ui.specifics.afterSave)) {
                                                newPromise = config.ui.specifics.afterSave($scope, info);
                                            }

                                            if (newPromise && newPromise.then) {
                                                newPromise.then(function () {
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
                    },
                    getPluginFieldOverrides = function (kind_id, field) {
                        var gets = defaultSpecifics.pluginFieldOverrides[kind_id];
                        if (angular.isDefined(gets) && angular.isDefined(gets[field])) {
                            return gets[field];
                        }
                        return {};
                    };

                config.ui.specifics.parentArgs = info.scope.$eval(config.ui.args);
                config.ui.specifics.entity = info.scope.$eval(config.ui.model);

                info.scope.$watch(config.ui.args, function (neww, old) {

                    if (neww !== old) {
                        config.ui.specifics.parentArgs = neww;
                    }
                });

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
                _content: {
                    documents: {}
                },
                _plugin_group: {}
            };

            $.extend(models['23'], {
                viewModal: function (seller, removedOrAdded) {
                    $modal.open({
                        templateUrl: 'entity/modal/editor.html',
                        controller: function ($scope, currentAccount, $modalInstance) {
                            $scope.seller = seller;
                            $scope.config = {
                                templateBodyUrl: 'seller/modal/view_body.html',
                                templateFooterUrl: 'seller/modal/view_footer.html'
                            };
                            $scope.accordions = {
                                closeOthers: true,
                                groups: [{
                                    label: $scope.seller.name,
                                    open: true
                                }, {
                                    label: 'Feedback'
                                }]
                            };
                            $scope.alreadyInCollection = false;
                            $scope.loadedCollection = models['18'].current().then(function (response) {
                                var collection = response.data.entity;
                                if ($.inArray($scope.seller.key, collection.sellers) !== -1) {
                                    $scope.alreadyInCollection = true;
                                }
                                return collection;
                            });

                            $scope.toggleCollection = function () {
                                $scope.loadedCollection.then(function (collection) {
                                    var loadedCollection = collection,
                                        removed = false;
                                    if ($scope.alreadyInCollection) {
                                        removed = true;
                                        loadedCollection.sellers.remove($scope.seller.key);
                                    } else {
                                        loadedCollection.sellers.unshift($scope.seller.key);
                                    }
                                    models['18'].actions.update({
                                        account: currentAccount.key,
                                        sellers: loadedCollection.sellers,
                                        notify: loadedCollection.notify
                                    }).then(function (newResponse) {
                                        var updatedCollection = newResponse.data.entity;
                                        modals.alert('Successfully ' + (removed ? 'removed seller from your' : 'added seller to your') +  ' colleciton.');
                                        $scope.alreadyInCollection = !removed;
                                        // update cache
                                        $.extend(loadedCollection, updatedCollection);
                                        if (angular.isFunction(removedOrAdded)) {
                                            removedOrAdded(updatedCollection, $scope.alreadyInCollection);
                                        }
                                    });
                                });
                            };

                            $scope.close = function () {
                                $modalInstance.dismiss('close');
                            };
                        },
                    });
                },
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
                manageModal: function (account_key) {
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

                    config = {
                        kind: this.kind,
                        action: 'update',
                        fields: _.toArray(fields),
                        excludeFields: ['account', 'read_arguments'],
                        argumentLoader: function ($scope) {
                            var args = this.defaultArgumentLoader($scope);
                            args.account = account_key;
                            if (args._content === null) {
                                args._content = {
                                    kind: '21',
                                    documents: []
                                };
                            }
                            args.read_arguments = read_arguments;
                            return args;
                        },
                        scope: {
                            accordions: {
                                closeOthers: true,
                                groups: [{
                                    label: 'General',
                                    open: true,
                                    key: 'general',
                                    fields: ['name', 'logo'],
                                }, {
                                    label: 'Plugins',
                                    fields: ['_plugin_group'],
                                },  {
                                    label: 'Contents',
                                    fields: ['_content']
                                }]
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
