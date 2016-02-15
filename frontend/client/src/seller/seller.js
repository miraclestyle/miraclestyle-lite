(function () {
    'use strict';
    var notEmpty = function (val) {
        return angular.isString(val) || angular.isNumber(val);
    };
    angular.module('app').controller('SellerInfo', ng(function ($scope, $state, $stateParams, models) {
        $scope.site.toolbar.hidden = true;
        models['23'].viewProfileModal($stateParams.key, {
            inDirection: false,
            outDirection: false,
            afterClose: function () {
                $state.go('home');
            }
        });
    })).controller('SellerEmbedInfo', ng(function ($scope, $stateParams, $state, models) {
        $scope.site.toolbar.hidden = true;
        models['23'].viewProfileModal($stateParams.key, {
            hideClose: true,
            inDirection: false,
            outDirection: false
        });
    })).directive('addressRuleLocationListView', function () {
        return {
            scope: {
                val: '=addressRuleLocationListView'
            },
            templateUrl: 'seller/address_rule_location_list_view.html',
            controller: ng(function ($scope) {
                $scope.notEmpty = notEmpty;
                $scope.postalCodes = function (postalCodes) {
                    return postalCodes.join(', ');
                };

            })
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
            controller: ng(function ($scope) {
                $scope.notEmpty = notEmpty;

            })
        };
    }).controller('SellerManagementController', ng(function ($scope, endpoint, currentAccount, models) {

        $scope.settings = function () {
            models['23'].manageModal(currentAccount.key);
        };

    })).controller('SellCatalogsController', ng(function ($scope, modals, helpers, currentAccount, modelsEditor, modelsMeta, snackbar, models, modelsUtil, $rootScope) {

        $scope.setPageToolbarTitle('seller.catalogs');

        var newEntity = function (entity) {
            if (!entity.key) {
                return;
            }
            var find = _.findWhere($scope.search.results, {
                    key: entity.key
                });
            if (!find) {
                $scope.search.results.unshift(entity);
            } else {
                $.extend(find, entity);
            }
        };

        $scope.$watch(function maybeRemoveSearchResult() {
            var maybe = false;
            $scope.search.results.iremove(function (ent) {
                var truth = (!ent.id || ent.state === 'discontinued');
                if (!maybe) {
                    maybe = truth;
                }
                return truth;
            });
            return maybe;
        }, angular.noop);

        $scope.create = function ($event) {
            models['31'].manageModal(undefined, newEntity, {
                popFrom: helpers.clicks.realEventTarget($event.target)
            });
        };

        $scope.preview = function (key, $event) {
            models['31'].previewModal(key, {
                popFrom: helpers.clicks.realEventTarget($event.target),
                track: helpers.track.events.catalogSellerCatalogs
            });
        };

        $scope.manage = function (entity, $event) {
            models['31'].manageModal(entity, newEntity, {
                popFrom: helpers.clicks.realEventTarget($event.target)
            });
        };

        $scope.search = {
            results: [],
            loader: {}
        };

        models['23'].current().then(function (response) {
            var sellerEntity = response.data.entity;
            $scope.search.loader = models['31'].paginate({
                kind: '31',
                args: {
                    search: {
                        ancestor: sellerEntity.key,
                        filters: [{
                            field: 'state',
                            operator: 'IN',
                            value: ['draft', 'published', 'indexed']
                        }],
                        orders: [{
                            field: 'created',
                            operator: 'desc'
                        }, {
                            field: 'key',
                            operator: 'desc'
                        }]
                    }
                },
                complete: function (response) {
                    $scope.search.results.extend(response.data.entities);
                }
            });
            $scope.search.loader.load();
        });

    })).controller('SellOrdersController', ng(function ($scope, modals, modelsEditor, snackbar, helpers, currentAccount, GLOBAL_CONFIG, modelsMeta, models, modelsUtil, $state) {

        var carts = $state.current.name === 'sell-carts',
            isSellerOrderView = _.string.startsWith($state.current.name, 'seller-'),
            wait = null,
            loaded = false,
            viewOpts = {
                inDirection: false,
                outDirection: false,
                track: helpers.track.noop.cartBuyerCarts,
                afterClose: function () {
                    $state.go('sell-orders');
                }
            },
            maybeOpenOrder = function () {
                if (loaded) {
                    return;
                }
                if (wait) {
                    clearTimeout(wait);
                }
                wait = setTimeout(function () {
                    var find = {
                        key: $state.params.key
                    }, order = _.findWhere($scope.search.results, find);
                    loaded = true;
                    if (order) {
                        return $scope.view(order, false, viewOpts);
                    }
                    models['34'].manageModal(find, undefined, undefined, viewOpts);
                }, 300);

            };

        $scope.setPageToolbarTitle('seller.' + (carts ? 'carts' : 'orders'));

        $scope.listHelp = (carts ? GLOBAL_CONFIG.emptyHelp.cartSellerList : GLOBAL_CONFIG.emptyHelp.orderSellerList);


        $scope.search = {
            results: [],
            loader: {},
            loaded: false
        };

        $scope.$watch(function maybeRemoveSearchResult() {
            var maybe = false;
            $scope.search.results.iremove(function (ent) {
                var truth = (!ent.id || ent._state === 'deleted') || (ent.state === 'order' && carts);
                if (!maybe) {
                    maybe = truth;
                }
                return truth;
            });
            return maybe;
        }, angular.noop);

        $scope.view = function (order, $event, viewOpts) {
            var opts = {
                sellerMode: carts,
                events: {
                    newOrder: function (order) {
                        $scope.search.results.push(order);
                    }
                },
                track: helpers.track.noop.cartBuyerCarts,
                popFrom: helpers.clicks.realEventTarget($event.target)
            };
            if (viewOpts) {
                opts = viewOpts;
            }
            models['34'].manageModal(order, order._seller, undefined, opts);
        };

        models['23'].current().then(function (response) {
            var sellerEntity = response.data.entity;
            $scope.search.loader = models['34'].paginate({
                kind: '34',
                args: {
                    search: {
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
                    ignoreErrors: 2
                },
                complete: function (response) {
                    var errors = response.data.errors;
                    if (!errors) {
                        $scope.search.results.extend(response.data.entities);
                    }

                    if (isSellerOrderView) {
                        maybeOpenOrder();
                    }
                }
            });
            $scope.search.loader.load();
        });
    })).run(ng(function (modelsConfig, modelsMeta,
        modelsEditor, formInputTypes, underscoreTemplate, $state, $stateParams, $modal, modals, social, helpers, $q, $timeout, currentAccount, $filter, dateFilter, GLOBAL_CONFIG, snackbar) {

        var pluginName = function (kind) {
            var find = GLOBAL_CONFIG.fields.translateChoices.rules.kind[kind];
            return angular.isDefined(find) ? find : kind;
        };

        modelsConfig(function (models) {
            formInputTypes.SuperPluginStorageProperty = function (info) {
                //info.config.repeated = true;
                //return this.SuperLocalStructuredProperty(info);
                var config = info.config,
                    kinds = config.kinds,
                    rootFormSetDirty = helpers.callable(info.scope.formSetDirty),
                    lineSpec = function () {
                        return {
                            listView: 'default-line-list-view',
                            listConfig: {
                                perLine: 2
                            }
                        };
                    },
                    exclusionSpec = function () {
                        return {
                            ui: {
                                specifics: {
                                    type: 'radio',
                                    trueLabel: GLOBAL_CONFIG.fields.radioLabel.pluginLocation.trueLabel,
                                    falseLabel: GLOBAL_CONFIG.fields.radioLabel.pluginLocation.falseLabel
                                }
                            }
                        };
                    },
                    groupBy = function (what, label, help) {
                        return {
                            ui: {
                                groupBy: what,
                                groupHelp: help,
                                groupLabel: label,
                                label: false
                            }
                        };
                    },
                    locationSpec = function () {
                        return {
                            listView: 'address-rule-location-list-view',
                            sortFields: ['country', 'region', 'postal_codes'],
                            listConfig: {
                                calculate: function (ent, i) {
                                    var lines = 0;
                                    angular.forEach(['country', 'region', 'postal_codes'], function (k) {
                                        var maybe = ent[k];
                                        if (maybe && maybe.length) {
                                            lines += 1;
                                        }
                                    });
                                    return lines === i;
                                }
                            },
                            beforeSave: function ($scope, info) {
                                var promises = [],
                                    updatedAddress = $scope.args,
                                    promise;
                                if (updatedAddress.region && (!updatedAddress._region || (updatedAddress.region !== updatedAddress._region.key))) {
                                    promise = models['13'].get(updatedAddress.region, updatedAddress.country);
                                    promise.then(function (region) {
                                        if (region) {
                                            updatedAddress._region = region;
                                        }
                                    });
                                    promises.push(promise);
                                }

                                if (updatedAddress.country && (!updatedAddress._country || (updatedAddress.country !== updatedAddress._country.key))) {
                                    promise = models['12'].get(updatedAddress.country);
                                    promise.then(function (country) {
                                        if (country) {
                                            updatedAddress._country = country;
                                        }
                                    });

                                    promises.push(promise);
                                }
                                if (promises.length) {
                                    return $q.all(promises);
                                }
                                return false;
                            }
                        };
                    },
                    defaultSpecifics = {
                        aboutPlugins: function () {
                            $modal.open({
                                templateUrl: 'core/models/manage.html',
                                controller: ng(function ($scope) {
                                    $scope.dialog = {
                                        templateBodyUrl: 'seller/help/plugins.html',
                                        toolbar: {
                                            hideSave: true,
                                            hideRight: true,
                                            leftIcon: 'arrow_back',
                                            title: helpers.toolbar.title('seller.settings.aboutRules')
                                        }
                                    };

                                    $scope.$state.instant(function () {
                                        $scope.appear = true;
                                    });
                                })
                            });
                        },
                        setupSortableOptions: function () {
                            return {
                                disabled: false,
                                start: function (e, ui) {
                                    info.scope.$broadcast('itemOrderStarted');
                                },
                                cancel: 'input,textarea,button,select,option,[disabled]',
                                distance: 6,
                                axis: false,
                                containment: false,
                                whatSortMeans: function () {
                                    modals.alert('howToSort');
                                },
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
                                    if (division < (helperWidth / 2)) {
                                        deleteMode = true;
                                    }
                                    if (item) {
                                        if (deleteMode) {
                                            ui.helper.addClass('about-to-delete');
                                            item._state = 'deleted';
                                            info.scope.formSetDirty();
                                        } else {
                                            ui.helper.removeClass('about-to-delete');
                                            item._state = null;
                                        }
                                    }
                                    info.scope.$broadcast('itemOrderSorting');
                                },
                                stop: function (e, ui) {
                                    var dirty;
                                    angular.forEach(config.ui.specifics.parentArgs,
                                        function (ent, i) {
                                            i = ((config.ui.specifics.parentArgs.length - 1) - i);
                                            if (ent._sequence !== i || ent._state === 'deleted') {
                                                dirty = true;
                                            }
                                            ent._sequence = i;
                                            if (ent.ui) {
                                                ent.ui.access[ent.ui.access.length - 1] = i;
                                            }
                                        });
                                    if (dirty) {
                                        info.scope.formSetDirty();
                                    }
                                    info.scope.$broadcast('itemOrderChanged');
                                    info.scope.$apply();
                                }
                            };
                        },
                        pluginFieldOverrides: {
                            '113': {
                                lines: {
                                    ui: {
                                        specifics: lineSpec()
                                    },
                                    modelclass: {
                                        prices: {
                                            ui: {
                                                specifics: {
                                                    toolbar: {
                                                        titleEdit: 'editPrice',
                                                        titleAdd: 'addPrice'
                                                    },
                                                    listView: 'carrier-line-rule-list-view',
                                                    listConfig: {
                                                        perLine: 2
                                                    }
                                                }
                                            },
                                            modelclass: {
                                                condition_type: groupBy('conditional', GLOBAL_CONFIG.fields.label['111-update'].condition_type, GLOBAL_CONFIG.fields.help['111-update'].condition_type),
                                                condition_operator: groupBy('conditional'),
                                                condition_value: groupBy('conditional'),
                                                price_type: groupBy('price', GLOBAL_CONFIG.fields.label['111-update'].price_type, GLOBAL_CONFIG.fields.help['111-update'].price_type),
                                                price_operator: helpers.extendDeep(groupBy('price'), {
                                                    ui: {
                                                        active: 'args.price_type !== \'fixed\''
                                                    }
                                                }),
                                                price_value: groupBy('price')
                                            }
                                        },
                                        exclusion: exclusionSpec(),
                                        locations: {
                                            ui: {
                                                specifics: locationSpec()
                                            }
                                        }
                                    }
                                }
                            },
                            '114': {
                                spacetext: {
                                    ui: {
                                        label: GLOBAL_CONFIG.subheaders.stripeWithConfidence,
                                        text: 'seller/help/stripe.html'
                                    }
                                }
                            },
                            '107': {
                                exclusion: exclusionSpec(),
                                locations: {
                                    ui: {
                                        specifics: locationSpec()
                                    }
                                }
                            },
                            '126': {
                                lines: {
                                    ui: {
                                        specifics: lineSpec()
                                    },
                                    modelclass: {
                                        product_categories: {
                                            ui: {
                                                specifics: {
                                                    search: {
                                                        enabled: true
                                                    }
                                                }
                                            }
                                        },
                                        condition_type: groupBy('conditional', GLOBAL_CONFIG.fields.label['124-update'].condition_type, GLOBAL_CONFIG.fields.help['124-update'].condition_type),
                                        condition_operator: groupBy('conditional'),
                                        condition_value: groupBy('conditional')
                                    }
                                }
                            },
                            '109': {
                                product_categories: {
                                    ui: {
                                        specifics: {
                                            search: {
                                                enabled: true
                                            }
                                        }
                                    }
                                },
                                carriers: {
                                    ui: {
                                        specifics: {
                                            checkboxes: true,
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
                                exclusion: exclusionSpec(),
                                locations: {
                                    ui: {
                                        specifics: locationSpec()
                                    }
                                }
                            }
                        },
                        showType: pluginName,
                        kind: undefined,
                        selectKinds: {
                            type: 'SuperStringProperty',
                            _maker_: 'rules',
                            choices: kinds,
                            required: true,
                            ui: {
                                args: 'info.kind',
                                label: GLOBAL_CONFIG.fields.label.plugins.kind,
                                attrs: {
                                    'ng-change': 'setNewArg()'
                                },
                                writable: true,
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
                                controller: ng(function ($scope, modelsUtil) {
                                    var getTitle,
                                        resetFormBuilder = function () {
                                            $scope.layouts = {
                                                groups: [{
                                                    label: false
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
                                    config.ui.specifics.toolbar = {
                                        leftIcon: 'arrow_back',
                                        hideSave: true,
                                        hideRight: true
                                    };
                                    if (angular.isUndefined(config.ui.specifics.toolbar.titleAdd)) {
                                        config.ui.specifics.toolbar.titleAdd = 'add' + helpers.toolbar.makeTitle(config.code_name);
                                    }
                                    if (angular.isUndefined(config.ui.specifics.toolbar.titleEdit)) {
                                        config.ui.specifics.toolbar.titleEdit = 'edit' + helpers.toolbar.makeTitle(config.code_name);
                                    }
                                    getTitle = function () {
                                        return config.ui.specifics.toolbar['title' + ($scope.isNew ? 'Add' : 'Edit')];
                                    };
                                    config._title_.push(getTitle);
                                    $scope.isNew = false;
                                    if (!arg) {
                                        arg = {};
                                        $scope.isNew = true;
                                    } else {
                                        modelsUtil.normalize(arg, undefined, config.ui.specifics.entity, config.code_name,
                                            config.ui.specifics.parentArgs.length);
                                    }
                                    $scope.$watch('isNew', function () {
                                        config.ui.specifics.toolbar.title = helpers.toolbar.buildTitle(config._title_);
                                    });
                                    $scope.info = {
                                        build: true
                                    };
                                    $scope.$stateHiddenLoading = true;
                                    $scope.container = {};
                                    $scope.config = config;
                                    $scope.$on('$destroy', function () {
                                        config._title_.remove(getTitle);
                                        config.ui.specifics.getScope = undefined;
                                    });
                                    $scope.$state.instant(function () {
                                        $scope.setNewArg = function () {
                                            if ($scope.info.kind !== 0 && $scope.args.kind !== $scope.info.kind) {
                                                arg = {
                                                    kind: $scope.info.kind
                                                };
                                                modelsUtil.normalize(arg, undefined, config.ui.specifics.entity, config.code_name,
                                                    config.ui.specifics.parentArgs.length, false);
                                                $scope.isNew = true;

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
                                            if (kind === '114') {
                                                angular.forEach(fields, function (field, i) {
                                                    field.name = (parseInt(field.name, 10) * 2).toString();
                                                });
                                                fields.push({
                                                    type: 'SpaceWithText',
                                                    name: '5',
                                                    code_name: 'spacetext',
                                                    ui: {}
                                                });

                                                fields.push({
                                                    _maker_: '114',
                                                    type: 'SuperStringProperty',
                                                    name: fields.length * 2 + 1,
                                                    code_name: 'webhook_endpoint',
                                                    required: false,
                                                    ui: {}
                                                });

                                                $scope.args.webhook_endpoint = helpers.url.abs('api/order/notify/stripe');
                                            }
                                            fields.sort(helpers.fields.sorter);
                                            config.ui.specifics.fields = fields;
                                            angular.forEach(fields, function (field) {
                                                helpers.fields.applyGlobalConfig(field);
                                                field._title_ = config._title_.concat();
                                                field.ui.name = 'plugin.' + field.code_name;
                                                field.ui.writable = true;
                                                var extra = getPluginFieldOverrides(kind, field.code_name),
                                                    next;
                                                if (extra) {
                                                    helpers.extendDeep(field, extra);
                                                }
                                                if (helpers.fields.isFieldset(field) && formInputTypes[field.type]) {
                                                    $scope.layouts.groups.push({
                                                        label: field.ui.label || $filter('humanized')(field.code_name),
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

                                            $scope.$stateHiddenLoading = true;
                                            helpers.fields.deferFormBuilderFields($scope.formBuilder).then(function () {
                                                $scope.$stateHiddenLoading = false;
                                            });
                                        };

                                        $scope.args = angular.copy(arg);
                                        $scope.parentArgs = config.ui.specifics.parentArgs;
                                        $scope.entity = config.ui.specifics.entity;
                                        $scope.rootFormSetDirty = rootFormSetDirty;
                                        $scope.formSetDirty = angular.bind($scope, helpers.form.setDirty);
                                        $scope.formSetPristine = angular.bind($scope, helpers.form.setPristine);
                                        $scope.validateForm = angular.bind($scope, helpers.form.validate);


                                        if ($scope.args && $scope.args.kind) {
                                            $scope.info.kind = $scope.args.kind;
                                            $scope.getFormBuilder();

                                        } else {
                                            $scope.$stateHiddenLoading = false;
                                        }
                                        $scope.close = function () {
                                            if (!$scope.container.form.$dirty) {
                                                return $scope.$close();
                                            }
                                            var save = $scope.save();
                                            if (save) {
                                                return save.then(function () {
                                                    $scope._close_ = undefined;
                                                    return $scope.$close();
                                                });
                                            }
                                            return modals.confirm('discardWithFieldsRequired', $scope.$close);
                                        };

                                        $scope._close_ = $scope.close;

                                        $scope.save = function () {
                                            var promise,
                                                complete,
                                                saveCompleteDefer = $q.defer(),
                                                saveCompletePromise = saveCompleteDefer.promise;
                                            if (!$scope.validateForm() || !$scope.info.kind) {
                                                return;
                                            }

                                            if (angular.isFunction(config.ui.specifics.beforeSave)) {
                                                //promise = 
                                                config.ui.specifics.beforeSave($scope, info);
                                            }

                                            complete = function () {
                                                var newPromise = null,
                                                    total = 0;
                                                if ($scope.isNew) {
                                                    $scope.parentArgs.unshift($scope.args);
                                                    $scope.isNew = false;
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

                                            $scope.isNew = false;

                                            return saveCompletePromise;

                                        };
                                    });
                                })
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

                if (config.ui.specifics.setupSortableOptions) {
                    config.ui.specifics.sortableOptions = config.ui.specifics.setupSortableOptions();
                }

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
                makeSellerDetails: function (seller, config) {
                    config = helpers.alwaysObject(config);
                    var removedOrAdded = config.removedOrAdded;
                    return (function ($scope) {
                        var sellerUrl = $state.engineHref('seller-info', {
                                key: seller.parent.key
                            }, {
                                absolute: true
                            }),
                            embedSellerUrl = $state.engineHref('embed-seller-info', {
                                key: seller.parent.key
                            }, {
                                absolute: true
                            }),
                            sellerLogo = helpers.url.handleProtocol(seller.logo.serving_url);
                        $scope.seller = seller;
                        $scope.menu = {};
                        helpers.sideNav.setup($scope.menu, 'right_seller_details');

                        $scope.socialMeta = {
                            facebook: {
                                'u': sellerUrl
                            },
                            twitter: {
                                url: sellerUrl,
                                text: $scope.seller.name
                            },
                            pinterest: {
                                url: sellerUrl,
                                media: sellerLogo,
                                description: $scope.seller.name
                            },
                            googleplus: {
                                url: sellerUrl
                            },
                            reddit: {
                                url: sellerUrl,
                                title: $scope.seller.name
                            },
                            linkedin: {
                                url: sellerUrl,
                                title: $scope.seller.name
                            },
                            tumblr: {
                                url: sellerUrl,
                                name: $scope.seller.name
                            }
                        };

                        $scope.viewContent = function (content) {
                            var track = $scope.getTrack();
                            track.openSellerContent();
                            $modal.open({
                                templateUrl: 'core/misc/content_view.html',
                                controller: ng(function ($scope) {
                                    $scope.$state.instant(function () {
                                        $scope.plainText = true;
                                        $scope.content = content;
                                    });

                                    $scope.close = function () {
                                        track.closeSellerContent();
                                        $scope.$close();
                                    };
                                })
                            });
                        };

                        return $scope;
                    }({}));
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
                    fields._plugin_group.ui.label = false;
                    $.extend(fields._plugin_group.modelclass.plugins.ui, {
                        label: false
                    });
                    fields.logo.ui.specifics = {
                        displayImageConfig: {
                            size: 240,
                            defaultImage: 'defaultLogo'
                        }
                    };
                    config = {
                        kind: this.kind,
                        action: 'update',
                        fields: _.toArray(fields),
                        toolbar: {
                            submitNative: true,
                            titleEdit: 'seller.settings',
                            titleAdd: 'seller.settings'
                        },
                        modalConfig: {
                            inDirection: false,
                            outDirection: false
                        },
                        excludeFields: ['account', 'read_arguments'],
                        argumentLoader: function ($scope) {
                            var args = this.defaultArgumentLoader($scope);
                            args.account = accountKey;
                            args.read_arguments = read_arguments;
                            return args;
                        },
                        scope: {
                            layouts: {
                                groups: [{
                                    label: false,
                                    fields: ['name', 'logo'],
                                }, {
                                    label: GLOBAL_CONFIG.subheaders.sellerPlugins,
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

    }));

}());
