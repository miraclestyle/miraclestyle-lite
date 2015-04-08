(function () {
    'use strict';
    var notEmpty = function (val) {
        return angular.isString(val) || angular.isNumber(val);
    };
    angular.module('app').directive('addressRuleLocationListView', function () {
        return {
            scope: {
                val: '=addressRuleLocationListView'
            },
            templateUrl: 'seller/address_rule_location_list_view.html',
            controller: function ($scope) {
                $scope.notEmpty = notEmpty;
                $scope.postalCodes = function (postalCodes) {
                    return postalCodes.join(', ');
                };

            }
        };
    }).directive('defaultLineListView', function () {
        return {
            scope: {
                val: '=defaultLineListView'
            },
            templateUrl: 'seller/default_line_list_view.html'
        };
    }).directive('carrierLineRuleListView', function () {
        return {
            scope: {
                val: '=carrierLineRuleListView'
            },
            templateUrl: 'seller/carrier_line_rule_list_view.html',
            controller: function ($scope) {
                $scope.notEmpty = notEmpty;

            }
        };
    }).directive('pluginListView', function (modelsMeta) {
        return {
            scope: {
                val: '=pluginListView'
            },
            templateUrl: 'seller/plugin_list_view.html',
            controller: function ($scope) {
                $scope.pluginName = function (kind) {
                    return modelsMeta.getName(kind);
                };
            }
        };
    }).controller('SellerManagementCtrl', function ($scope, endpoint,
        currentAccount, models) {

        $scope.settings = function () {
            models['23'].manageModal(currentAccount.key);
        };

    }).controller('SellCatalogsCtrl', function ($scope, modals, modelsEditor, modelsMeta, models, modelsUtil, $rootScope) {

        $rootScope.pageTitle = 'Sell Catalogs';

        var newEntity = function (entity) {
            if (!_.findWhere($scope.search.results, {
                    key: entity.key
                })) {
                $scope.search.results.unshift(entity);
            }
        };

        $scope.create = function () {
            models['31'].manageModal(undefined, newEntity);
        };

        $scope.preview = function (key, config) {
            config.targetEvent.target = $(config.targetEvent.target).parents('.grid-item:first').get(0);
            models['31'].previewModal(key, config);
        };

        $scope.manage = function (entity, config) {
            models['31'].manageModal(entity, newEntity, config);
        };

        $scope.search = {
            results: [],
            pagination: {}
        };

        $scope.scrollEnd = {
            loader: false
        };

        models['23'].current().then(function (response) {
            var sellerEntity = response.data.entity;
            $scope.search.pagination = models['31'].paginate({
                kind: '31',
                args: {
                    search: {
                        ancestor: sellerEntity.key
                    }
                },
                config: {
                    ignoreErrors: true
                },
                complete: function (response) {
                    var errors = response.data.errors;
                    if (errors) {
                        if (errors['not_found_' + sellerEntity.key]) {
                            modals.alert('You do not have any seller information yet.');
                        }
                    } else {
                        $scope.search.results.extend(response.data.entities);
                    }
                }
            });
            $scope.scrollEnd.loader = $scope.search.pagination;
            $scope.search.pagination.load();
        });

    }).controller('SellOrdersCtrl', function ($scope, modals, modelsEditor, modelsMeta, models, modelsUtil, $rootScope, $state) {

        var carts = $state.current.name === 'sell-carts';

        $rootScope.pageTitle = 'Seller ' + (carts ? 'Carts' : 'Orders');

        $scope.search = {
            results: [],
            pagination: {}
        };

        $scope.scrollEnd = {
            loader: false
        };

        $scope.view = function (order) {
            models['34'].manageModal(order, order._seller, undefined, {
                sellerMode: carts
            });
        };

        models['23'].current().then(function (response) {
            var sellerEntity = response.data.entity;
            $scope.search.pagination = models['34'].paginate({
                kind: '34',
                args: {
                    search: {
                        // {field: 'state', operator: 'IN', value: (carts ? ['cart', 'checkout'] : ['completed', 'canceled'])}
                        filters: [{
                            field: 'seller_reference',
                            operator: '==',
                            value: sellerEntity.key
                        }],
                        orders: [{
                            field: 'updated',
                            operator: 'desc'
                        }]
                    }
                },
                config: {
                    ignoreErrors: true
                },
                complete: function (response) {
                    var errors = response.data.errors;
                    if (errors) {
                        if (errors['not_found_' + sellerEntity.key]) {
                            modals.alert('You do not have any seller information yet.');
                        }
                    } else {
                        $scope.search.results.extend(response.data.entities);
                    }
                }
            });
            $scope.scrollEnd.loader = $scope.search.pagination;
            $scope.search.pagination.load();
        });
    }).run(function ($window, modelsConfig, modelsMeta,
        modelsEditor, formInputTypes, underscoreTemplate, $modal, modals, helpers, $q, $timeout, currentAccount, $filter, dateFilter) {

        modelsConfig(function (models) {
            formInputTypes.SuperPluginStorageProperty = function (info) {
                //info.config.repeated = true;
                //return this.SuperLocalStructuredProperty(info);
                var config = info.config,
                    kinds = $.map(config.kinds, function (kind_id) {
                        var name = modelsMeta.getName(kind_id);
                        return {
                            key: kind_id,
                            name: name
                        };
                    }),
                    rootFormSetDirty = helpers.callable(info.scope.formSetDirty),
                    lineSpec = {
                        listView: 'default-line-list-view'
                    },
                    locationSpec = {
                        listView: 'address-rule-location-list-view',
                        sortFields: ['country', 'region', 'postal_codes'],
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

                            if (updatedAddress.country && ((!updatedAddress._country) || (updatedAddress.country !== updatedAddress._country.key))) {
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
                    },
                    defaultSpecifics = {
                        sortableOptions: {
                            disabled: false,
                            start: function (e, ui) {
                                info.scope.$broadcast('itemOrderStarted');
                            },
                            axis: false,
                            containment: false,
                            whatSortMeans: modals.howToSort,
                            handle: '.sort-handle',
                            tolerance: 'pointer',
                            helper: 'clone',
                            sort: function (e, ui) {
                                var deleteMode,
                                    division,
                                    helperWidth = ui.helper.width(),
                                    itemScope = ui.item.scope(),
                                    item = itemScope.$eval(ui.item.attr('current-item'));
                                division = ui.offset.left + helperWidth;
                                if (division < (helperWidth / 1.5)) {
                                    deleteMode = true;
                                }
                                if (item) {
                                    if (deleteMode) {
                                        ui.helper.addClass('about-to-delete');
                                        item._state = 'deleted';
                                    } else {
                                        ui.helper.removeClass('about-to-delete');
                                        item._state = null;
                                    }
                                }
                                info.scope.$broadcast('itemOrderSorting');
                            },
                            stop: function (e, ui) {
                                var cmp = [],
                                    cmp2 = [];
                                angular.forEach(config.ui.specifics.parentArgs,
                                    function (ent, i) {
                                        cmp.push(ent._sequence);
                                        i = ((config.ui.specifics.parentArgs.length - 1) - i);
                                        cmp2.push(i);
                                        ent._sequence = i;
                                        if (ent.ui) {
                                            ent.ui.access[ent.ui.access.length - 1] = i;
                                        }
                                    });
                                if (!cmp.equals(cmp2)) {
                                    rootFormSetDirty();
                                }
                                info.scope.$broadcast('itemOrderChanged');
                                info.scope.$apply();
                            }
                        },
                        pluginFieldOverrides: {
                            '113': {
                                lines: {
                                    ui: {
                                        specifics: lineSpec
                                    },
                                    modelclass: {
                                        rules: {
                                            ui: {
                                                specifics: {
                                                    listView: 'carrier-line-rule-list-view'
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
                            '126': {
                                lines: {
                                    ui: {
                                        specifics: lineSpec
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
                            type: 'SuperStringProperty',
                            choices: kinds,
                            ui: {
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
                            rootFormSetDirty();
                        },
                        create: function () {
                            return this.manage();
                        },
                        manage: function (arg) {

                            if (!angular.isDefined(config.ui.specifics.templateUrl)) {
                                config.ui.specifics.templateUrl = 'core/fields/manage_structured.html';
                            }

                            $modal.open({
                                template: underscoreTemplate.get(config.ui.specifics.templateUrl)({
                                    config: config
                                }),
                                controller: function ($scope, modelsUtil) {
                                    var is_new = false,
                                        inflector = $filter('inflector'),
                                        resetFormBuilder = function () {
                                            $scope.layouts = {
                                                closeOthers: true,
                                                groups: [{
                                                    label: false,
                                                    disabled: false,
                                                    open: true
                                                }]
                                            };
                                            $scope.formBuilder = {
                                                '0': [config.ui.specifics.selectKinds]
                                            };
                                        },
                                        getPluginFieldOverrides = function (kind_id, field) {
                                            var gets = defaultSpecifics.pluginFieldOverrides[kind_id];
                                            if (angular.isDefined(gets) && angular.isDefined(gets[field])) {
                                                return angular.copy(gets[field]);
                                            }
                                            return {};
                                        };

                                    if (!arg) {
                                        arg = {};
                                    } else {
                                        modelsUtil.normalize(arg, undefined, config.ui.specifics.entity, config.code_name,
                                                config.ui.specifics.parentArgs.length);
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
                                            modelsUtil.normalize(arg, undefined, config.ui.specifics.entity, config.code_name,
                                                config.ui.specifics.parentArgs.length, false);
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
                                            fields = modelsMeta.getFields(kind),
                                            realTotal = 0,
                                            found = false;
                                        fields = _.toArray(fields);
                                        fields.sort(helpers.fields.sorter);
                                        config.ui.specifics.fields = fields;
                                        angular.forEach(fields, function (field) {
                                            field.ui.name = 'plugin.' + field.code_name;
                                            field.ui.writable = true;
                                            var extra = getPluginFieldOverrides(kind, field.code_name),
                                                next;
                                            if (extra) {
                                                helpers.extendDeep(field, extra);
                                            }
                                            if (field.is_structured && formInputTypes[field.type]) {
                                                $scope.layouts.groups.push({
                                                    label: inflector((field.ui.label || field.code_name), 'humanize'),
                                                    disabled: false,
                                                    open: false
                                                });

                                                field.ui.label = false;
                                                next = $scope.layouts.groups.length - 1;

                                                if (!angular.isDefined($scope.formBuilder[next])) {
                                                    $scope.formBuilder[next] = [];
                                                    $scope.formBuilder[next].push(field);
                                                }
                                                $scope.layouts.groups[0].disabled = false;
                                            } else {
                                                $scope.formBuilder['0'].push(field);
                                            }
                                        });

                                        angular.forEach($scope.layouts.groups, function (group, i) {
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
                                    $scope.rootFormSetDirty = rootFormSetDirty;
                                    $scope.formSetDirty = angular.bind($scope, helpers.form.setDirty);
                                    $scope.formSetPristine = angular.bind($scope, helpers.form.setPristine);
                                    $scope.validateForm = angular.bind($scope, helpers.form.validate);

                                    if ($scope.args && $scope.args.kind) {
                                        $scope.info.kind = $scope.args.kind;
                                        $scope.getFormBuilder();

                                    }

                                    config.ui.specifics.toolbar = {
                                        leftIcon: 'navigation.arrow-back',
                                        hideSave: true
                                    };
                                    $scope.close = function () {
                                        var save = $scope.save();
                                        if (save) {
                                            save.then(function () {
                                                $scope.__close__ = undefined;
                                                $scope.$close();
                                            });
                                        } else {
                                            modals.confirm({
                                                confirm: $scope.$close,
                                                message: 'This data will not be saved because there are some fields required. Discard?',
                                                text: {
                                                    ok: 'Discard'
                                                }
                                            });
                                        }
                                    };

                                    $scope.__close__ = $scope.close;

                                    $scope.save = function () {
                                        var promise,
                                            complete,
                                            saveCompleteDefer = $q.defer(),
                                            saveCompletePromise = saveCompleteDefer.promise;
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
                                                is_new = false;
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
                                                    saveCompleteDefer.resolve();
                                                });
                                            } else {
                                                saveCompleteDefer.resolve();
                                            }

                                        };

                                        if ($scope.container.form.$dirty) {
                                            rootFormSetDirty();
                                        }
                                        if (promise && promise.then) {
                                            promise.then(complete);

                                        } else {
                                            complete();

                                        }

                                        return saveCompletePromise;

                                    };

                                }
                            });
                        }
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
                        templateUrl: 'core/models/manage.html',
                        controller: function ($scope, currentAccount) {
                            var cartData;
                            $scope.seller = seller;
                            $scope.dialog = {
                                templateBodyUrl: 'seller/view_body.html',
                                toolbar: {
                                    templateActionsUrl: 'seller/view_actions.html',
                                    hideSave: true
                                }
                            };
                            $scope.layouts = {
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

                            if ($scope.seller._feedback && $scope.seller._feedback.feedbacks) {
                                cartData = [];

                                angular.forEach($scope.seller._feedback.feedbacks, function (feedback) {
                                    feedback.positive_count = _.random(0, 100);
                                    feedback.negative_count = _.random(0, 100);
                                    feedback.neutral_count = _.random(0, 100);
                                    cartData.push({
                                        c: [{
                                            v: dateFilter(feedback.date, 'MMM')
                                        }, {
                                            v: feedback.positive_count
                                        }, {
                                            v: feedback.negative_count
                                        }, {
                                            v: feedback.neutral_count
                                        }]
                                    });

                                });

                                $scope.chartConfig = {
                                    type: "ColumnChart",
                                    data: {
                                        cols: [{
                                            id: "months",
                                            label: "Months",
                                            type: "string"
                                        }, {
                                            id: "positive",
                                            label: "Positive",
                                            type: "number"
                                        }, {
                                            id: "negative",
                                            label: "Negative",
                                            type: "number"
                                        }, {
                                            id: "neutral",
                                            label: "Neutral",
                                            type: "number"
                                        }],
                                        rows: cartData
                                    },
                                    options: {
                                        colors: ['green', 'red', 'gray'],
                                        series: {
                                            0: {
                                                axis: 'positive'
                                            },
                                            1: {
                                                axis: 'negative'
                                            },
                                            3: {
                                                axis: 'neutral'
                                            }
                                        },
                                        axes: {
                                            y: {
                                                positive: {
                                                    label: 'Positive'
                                                },
                                                negative: {
                                                    label: 'Negative',
                                                    side: 'right'
                                                },
                                                neutral: {
                                                    label: 'Neutral',
                                                    side: 'right'
                                                }
                                            }
                                        }
                                    }
                                };


                                $scope.feedbackStats = (function () {
                                    var positive_count = 0,
                                        neutral_count = 0,
                                        negative_count = 0,
                                        positive_average,
                                        negative_average,
                                        neutral_average,
                                        score,
                                        values = [];

                                    positive_average = parseFloat((positive_count / (positive_count + negative_count)) * 100).toFixed(1);
                                    negative_average = parseFloat((negative_count / (negative_count + positive_count)) * 100).toFixed(1);
                                    neutral_average = parseFloat((neutral_count / (neutral_count + negative_count + positive_count)) * 100).toFixed(1);

                                    if ((positive_count - negative_count) > 0) {
                                        score = positive_count - negative_count;
                                    } else {
                                        score = 0;
                                    }
                                    values[0] = positive_count;
                                    values[1] = neutral_count;
                                    values[2] = negative_count;
                                    values[3] = positive_average;
                                    values[4] = negative_average;
                                    values[5] = neutral_average;
                                    values[6] = score;
                                    return values;
                                }());
                            }


                            $scope.viewContent = function (content) {
                                $modal.open({
                                    templateUrl: 'core/models/manage.html',
                                    controller: function ($scope) {
                                        $scope.dialog = {
                                            templateBodyUrl: 'core/misc/content_view_body.html',
                                            toolbar: {
                                                hideSave: true
                                            }
                                        };
                                        $scope.content = content;
                                        $scope.close = function () {
                                            $scope.$close();
                                        };
                                    }
                                });
                            };

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
                                        //modals.alert('Successfully ' + (removed ? 'removed seller from your' : 'added seller to your') +  ' colleciton.');
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
                                $scope.$close();
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
                manageModal: function (accountKey) {
                    var fields = modelsMeta.getActionArguments(this.kind, 'update'),
                        config;
                    fields._content.ui.label = false;
                    fields._content.modelclass.documents.ui = {
                        label: false,
                        specifics: {
                            listView: 'content-list-view',
                            listConfig: {
                                perLine: 1
                            }
                        }
                    };
                    fields._plugin_group.modelclass.plugins.ui = {
                        label: false,
                        specifics: {
                            listView: 'plugin-list-view'
                        }
                    };
                    fields.logo.ui.label = 'Select Logo';
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
                        toolbar: {
                            submitNative: true
                        },
                        excludeFields: ['account', 'read_arguments'],
                        argumentLoader: function ($scope) {
                            var args = this.defaultArgumentLoader($scope);
                            args.account = accountKey;
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
                            layouts: {
                                closeOthers: true,
                                groups: [{
                                    label: false,
                                    open: true,
                                    key: false,
                                    fields: ['name', 'logo'],
                                }, {
                                    label: 'Contents',
                                    fields: ['_content']
                                }, {
                                    label: 'Plugins',
                                    fields: ['_plugin_group'],
                                }]
                            }
                        }
                    };

                    modelsEditor.create(config).read({}, {
                        account: accountKey,
                        read_arguments: read_arguments
                    });

                }
            });

        });

    });

}());