(function () {
    'use strict';
    angular.module('app')
        .run(ng(function (modals, helpers, models, $modal, modelsMeta, snackbar) {
            if (!modals.models) {
                modals.models = {};
            }
            modals.models.sudo = function (entity, config) {
                var defaults = {
                    fullScreen: false,
                    popFrom: false,
                    inDirection: false,
                    outDirection: false,
                    templateUrl: null,
                    cantCloseWithBackdrop: true,
                    controller: ng(function ($scope) {
                        var sudoFields = modelsMeta.getActionArguments(entity.kind, 'sudo');
                        $scope.args = {};
                        $scope.fields = sudoFields;
                        angular.forEach($scope.fields, function (field) {
                            $.extend(field.ui, {
                                writable: true,
                                label: false,
                                attrs: {
                                    'native-placeholder': '',
                                    'class': 'full-width'
                                }
                            });
                            $scope.args[field.code_name] = entity[field.code_name];
                        });

                        $scope.fields.message.ui.placeholder = 'Write a message to the user!';
                        $scope.fields.note.ui.placeholder = 'Write a note to the admins!';
                        $scope.validateForm = angular.bind($scope, helpers.form.validate);

                        $scope.container = {};
                        $scope.config = {};

                        $scope.config.scroll = true;

                        $scope.config.dismiss = function () {
                            return $scope.$close();
                        };

                        $scope.config.text = {
                            primary: 'Ok'
                        };

                        $scope.config.confirm = function () {
                            if ($scope.validateForm()) {
                                var promise = models[entity.kind].actions.sudo($scope.args);
                                promise.then(function (response) {
                                    if (config.onConfirm) {
                                        config.onConfirm(response.data.entity);
                                    }
                                    $scope.config.dismiss();
                                    snackbar.showK('administered');
                                });
                            } else {
                                helpers.form.wakeUp($scope.container.form, false, true);
                            }
                        };
                    })
                };
                $.extend(defaults, config);
                $modal.open(defaults);
            };

            if (!helpers.models) {
                helpers.models = {};
            }
            $.extend(helpers.models, {
                isEntityListEmpty: function (entities, also) {
                    var empty = (!entities || entities.length === 0),
                        emptyFactory;
                    if (!empty) {
                        emptyFactory = 0;
                        angular.forEach(entities, function (value) {
                            var maybe = false;
                            if (also) {
                                maybe = $.inArray(value._state, also) !== -1;
                            }
                            if (value._state === 'deleted' || maybe) {
                                emptyFactory += 1;
                            }
                        });
                        empty = (emptyFactory === entities.length);
                    }
                    return empty;
                }
            });
        }))
        .value('modelsInfo', {})
        .value('currentAccount', {}).factory('modelsMeta', ng(function ($injector, GLOBAL_CONFIG) {
            var modelsMeta = {},
                standardize = function (fields, maker) {
                    angular.forEach(fields, function (field, field_key) {
                        if (field.ui === undefined) {
                            field.ui = {};
                        }
                        if (field.code_name === null) {
                            field.code_name = field_key;
                        }

                        field._maker_ = maker;
                        if (field.modelclass !== undefined) {
                            standardize(field.modelclass, field.modelclass_kind);
                        }
                    });

                };

            modelsMeta.friendlyActionName = function (kind, action_key) {

                var info = this.get(kind),
                    actions,
                    friendlyName;
                if (info === undefined) {
                    return undefined;
                }

                actions = info.actions;

                angular.forEach(actions, function (action) {
                    if (action.key === action_key) {
                        friendlyName = action.id;
                    }
                });

                return friendlyName;
            };

            modelsMeta.getFields = function (kind_id) {
                if (!angular.isDefined(kind_id)) {
                    console.error('provided kind id is not acceptable, got: ' +
                        kind_id);
                    return undefined;
                }
                var info = this.get(kind_id),
                    fields;
                if (!angular.isDefined(info)) {
                    console.error('could not find meta info for kind ' + kind_id);
                    return undefined;
                }

                fields = angular.copy(info.fields);

                standardize(fields, kind_id);

                return fields;
            };

            modelsMeta.getDefaultActionArguments = function (kind, action) {
                var getAction = this.getActionArguments(kind, action),
                    defaultArgs = {};

                angular.forEach(getAction['arguments'], function (arg) {
                    if (arg['default'] !== null) {
                        defaultArgs[arg.code_name] = arg['default'];
                    }

                });

                return defaultArgs;
            };

            modelsMeta.getActionArguments = function (kind_id, action) {
                var info = this.get(kind_id),
                    getAction,
                    actionArguments = {},
                    fields;
                if (!angular.isDefined(info)) {
                    return undefined;
                }
                if (angular.isDefined(action)) {
                    getAction = info.mapped_actions[action];
                    if (!angular.isDefined(getAction)) {
                        console.error('action ' + action + ' not found for kind ' + kind_id);
                        return undefined;
                    }
                    fields = angular.copy(getAction['arguments']);

                    standardize(fields, kind_id + '-' + action);
                    return fields;
                }

                angular.forEach(info.mapped_actions, function (action) {
                    fields = angular.copy(action['arguments']);
                    standardize(fields, kind_id + '-' + action.id);
                    actionArguments[action.id] = fields;
                });

                return actionArguments;

            };

            modelsMeta.getActions = function (kind_id) {
                var info = this.get(kind_id),
                    actions;
                if (!angular.isDefined(info)) {
                    return undefined;
                }
                actions = info.mapped_actions;
                angular.forEach(actions, function (action) {
                    standardize(action['arguments'], kind_id + '-' + action.id);
                });

                return actions;
            };

            modelsMeta.getName = function (kind_id) {
                var info = this.get(kind_id);
                if (!angular.isDefined(info)) {
                    console.error('model name not found for kind ' + kind_id);
                    return undefined;
                }
                return info.name;
            };

            modelsMeta.get = function (kind_id) {

                var modelsInfo = $injector.get('modelsInfo'),
                    kind = modelsInfo[kind_id],
                    fields = {},
                    actions = {},
                    data;

                if (kind === undefined) {
                    console.error('no info for kind ' + kind_id);
                    return undefined;
                }

                angular.forEach(kind, function (value, key) {
                    if (key !== '_actions' && key !== '__name__') {
                        fields[key] = value;
                    }
                });

                angular.forEach(kind._actions, function (action) {
                    actions[action.id] = action;
                });

                data = {
                    actions: kind._actions,
                    mapped_actions: actions,
                    fields: fields,
                    name: kind.__name__
                };

                return data;
            };
            if (GLOBAL_CONFIG.debug) {
                window._modelsMeta = modelsMeta;
            }

            return modelsMeta;

        })).factory('ruleEngine', ng(function (modelsMeta) {

            var ruleEngine = {
                run: function (entity) {
                    var actions = {},
                        inputs = {},
                        kindInfo = modelsMeta.get(entity.kind),
                        actionPermissions = entity._action_permissions,
                        fieldPermissions = entity._field_permissions,
                        ruleActions = kindInfo.actions,
                        config = {
                            action: actions,
                            input: inputs,
                            field: fieldPermissions
                        },
                        actionTranslate = function (actionName) {
                            return actionPermissions[ruleActions[actionName].id];
                        },
                        executable = function (actionName) {
                            var gets = actionTranslate(actionName);
                            return gets.executable;
                        };
                    if (actionPermissions === undefined) {
                        return undefined;
                        // if the permissions are not present, there is no rule engine here...
                    }
                    angular.forEach(ruleActions, function (value, key) {

                        if (!config.action[value.id]) {
                            config.action[value.id] = {};
                        }
                        config.action[value.id].executable = executable(key);

                        angular.forEach(value.arguments, function (argumentValue) {
                            var argument_key = argumentValue.code_name;
                            if (!config.input[value.id]) {
                                config.input[value.id] = {};
                            }
                            config.input[value.id][argument_key] = argumentValue;
                        });

                    });

                    return config;
                }
            };

            return ruleEngine;
        })).factory('modelsUtil', ng(function (modelsMeta, ruleEngine, GLOBAL_CONFIG) {
            // Service used for normalizing entity data that gets retrieved from datastore
            var modelsUtil = {
                normalizeMultiple: function (entities) {
                    angular.forEach(entities, function (entity) {
                        modelsUtil.normalize(entity);
                    });
                },
                argumentsToJson: function (entity, pretty) {
                    var ignore = ['_field_permissions', '_next_read_arguments', '_read_arguments', '_action_permissions', 'ui'];
                    return JSON.stringify(entity,
                        function (key, value) {
                            var val = value,
                                newval;

                            if (angular.isObject(value) && value.ui) {
                                newval = {};
                                angular.forEach(value, function (v, k) {
                                    if ($.inArray(k, ignore) === -1) {
                                        newval[k] = v;
                                    }
                                });
                                val = newval;
                            }

                            if (typeof key === 'string' && key.charAt(0) === '$') {
                                val = undefined;
                            } else if (value && value.document && value.location && value.alert && value.setInterval) {
                                val = '$WINDOW';
                            } else if (value && document === value) {
                                val = '$DOCUMENT';
                            } else if (value && value.$evalAsync && value.$watch) {
                                val = '$SCOPE';
                            }

                            return val;
                        }, pretty ? '  ' : null);
                },
                normalize: function (entity, fields, parent, subentity_field_key, subentity_position, noui) {
                    if (entity.ui && entity.ui.normalized) {
                        return;
                    }

                    if (fields === undefined) {
                        fields = modelsMeta.getFields(entity.kind);
                    }

                    if (noui === undefined) {

                        entity.ui = {};
                        entity.ui.normalized = true;
                        entity.ui.access = [];
                        if (subentity_field_key) {
                            entity.ui.access.extend(parent.ui.access);
                            entity.ui.access.push(subentity_field_key);
                            if (subentity_position !== undefined) {
                                entity.ui.access.push(subentity_position);
                            }

                        }
                        /// ui must be now reserved keyword in datastore and we use it for making ui related functions
                        if (parent === undefined) {
                            entity.ui.rule = ruleEngine.run(entity);
                        }

                    }

                    angular.forEach(fields, function (field) {
                        var defaults = field['default'],
                            value = entity[field.code_name];
                        if (field.type === 'SuperDateTimeProperty' && !defaults) {
                            defaults = new Date();

                        }
                        if (field.repeated && !angular.isArray(defaults)) {
                            defaults = [];
                        }

                        if ((value === undefined || value === null)) {
                            if ((defaults !== null && defaults !== undefined)) {
                                entity[field.code_name] = defaults;
                            }
                        }

                        if (field.type === 'SuperDateTimeProperty' && angular.isString(value)) {
                            entity[field.code_name] = new Date(value);
                        }

                        if (field.is_structured) {
                            if (field.repeated) {
                                angular.forEach(value, function (subentity, i) {
                                    modelsUtil.normalize(subentity, field.modelclass,
                                        entity, field.code_name, i);
                                });
                            } else {

                                if ((value === undefined || value === null)) {
                                    if (field.required) {
                                        value = {
                                            kind: field.modelclass_kind
                                        };
                                        entity[field.code_name] = value;
                                    }
                                }

                                if (!(value === undefined || value === null)) {
                                    modelsUtil.normalize(value, field.modelclass, entity,
                                        field.code_name, undefined, noui);
                                }

                            }
                        }

                    });

                }
            };

            if (GLOBAL_CONFIG.debug) {
                window._modelsUtil = modelsUtil;
            }
            return modelsUtil;
        })).factory('modelsEditor', ng(function ($modal, endpoint, $q, helpers,
            modelsUtil, errorHandling, models, modelsMeta, $timeout, $filter, formInputTypes, recordBrowser, snackbar) {

            var modelsEditor = {
                create: function (config) {
                    var defaultConfig = {
                            showClose: true,
                            closeAfterSave: false,
                            action: 'update',
                            templateBodyUrl: 'core/models/manage_body_default.html',
                            scope: {},
                            fields: [],
                            init: angular.noop,
                            getScope: null,
                            defaultInit: angular.noop,
                            defaultArgumentLoader: function ($scope) {
                                var entityCopy = angular.copy($scope.entity),
                                    actionArguments = modelsMeta.getActionArguments($scope.config.kind, $scope.config.action),
                                    args = {};

                                angular.forEach(actionArguments, function (arg) {
                                    var val = entityCopy[arg.code_name];
                                    // default is only acceptable if its not null or undefined
                                    if (val === undefined && (arg['default'] !== null &&
                                            arg['default'] !== undefined)) {
                                        val = arg['default'];
                                    }
                                    if (val !== undefined) {
                                        // arg can never be "undefined"
                                        args[arg.code_name] = val;
                                    }

                                });
                                if ($scope.entity.key) {
                                    args.key = entityCopy.key;
                                }
                                if ($scope.entity.id) {
                                    args.id = entityCopy.id;
                                }
                                args.ui = entityCopy.ui;
                                // every entity has _read_arguments when retrieved from database
                                // argument loader will attach that to its next rpc
                                // to ensure that entity that has been fetched from database
                                // gets the same read arguments for next rpc
                                if (entityCopy._read_arguments) {
                                    args.read_arguments = entityCopy._read_arguments;
                                }

                                // attaches next read arguments to args too, needed for paging
                                if (entityCopy._next_read_arguments) {
                                    args._next_read_arguments = entityCopy._next_read_arguments;
                                }

                                // attach extra data to args
                                $.extend(args, $scope.withArgs);

                                // attach which action and model should be used in rpc from the config
                                args.action_id = $scope.config.action;
                                args.action_model = $scope.config.kind;
                                return args;
                            },
                            argumentLoader: function ($scope) {
                                return this.defaultArgumentLoader($scope);
                            },
                            defaultPrepareReadArguments: function ($scope) {
                                // it will scan entire args and populate read arguments
                                if (!angular.isObject($scope.args.read_arguments)) {
                                    $scope.args.read_arguments = {};
                                }
                                var readArgs = $scope.args.read_arguments,
                                    parser = function (arg, key, readArgs) {
                                        if (angular.isArray(arg)) {
                                            var path = readArgs[key];
                                            if (!path) {
                                                path = {
                                                    config: {}
                                                };
                                            }

                                            if (!path.config) {
                                                path.config = {};
                                            }

                                            if (arg && angular.isObject(arg[0])) {
                                                path.config.keys = $.map(arg, function (ent) {
                                                    return ent.key;
                                                });
                                            }

                                            readArgs[key] = path;
                                        }
                                    };
                                angular.forEach($scope.args, function (arg, key) {
                                    parser(arg, key, readArgs);
                                });
                            },
                            prepareReadArguments: function ($scope) {
                                this.defaultPrepareReadArguments($scope);
                            }
                        },
                        actionArguments,
                        modelsEditorInstance;

                    // recurse the config adding only what is supplied by the `new_config`
                    helpers.mergeDeep(config, defaultConfig);

                    // load all field specs from the arguments that are going to be used based on action and model provided
                    if (!angular.isDefined(config.fields) && angular.isDefined(config.kind) && angular.isDefined(config.action)) {
                        config.fields = [];
                        actionArguments = modelsMeta.getActionArguments(config.kind, config.action);
                        angular.forEach(actionArguments, function (field) {
                            if (angular.isDefined(config.excludeFields) && $.inArray(field.code_name, config.excludeFields) !== -1) {
                                return;
                            }
                            config.fields.push(field);
                        });

                    }
                    // map out the fields to key-value dict
                    config.keyedFields = {};
                    angular.forEach(config.fields, function (field) {
                        config.keyedFields[field.code_name] = field;
                    });

                    modelsEditorInstance = {
                        config: config,
                        read: function (entity, args, httpConfig) {
                            if (args === undefined) {
                                args = {
                                    key: entity.key
                                };
                            }
                            return this.openPromise(function () {
                                return models[config.kind].actions.read(args, httpConfig);
                            }, entity, args);
                        },
                        prepare: function (entity, args, httpConfig) {
                            return this.openPromise(function () {
                                return models[config.kind].actions.prepare(args, httpConfig);
                            }, entity, args);
                        },
                        openPromise: function (promise, entity, args) {
                            return this.open(entity, args, promise);
                        },
                        open: function (entity, args, promise) {
                            var opener = $modal,
                                fn = 'open',
                                defer = $q.defer(),
                                completePromise = defer.promise,
                                ctrl;
                            ctrl = function ($scope) {
                                var editTitle = 'edit' + config.kind,
                                    addTitle = 'add' + config.kind,
                                    rootTitle,
                                    process;
                                $scope.config = config;
                                $scope.container = {
                                    action: endpoint.url
                                };
                                $scope.$stateHiddenLoading = true;
                                $scope.dialog = {
                                    toolbar: config.toolbar,
                                    templateBodyUrl: config.templateBodyUrl
                                };
                                $scope.entity = entity;
                                if (!config.toolbar) {
                                    config.toolbar = {};
                                }

                                if (angular.isUndefined(config.toolbar.titleEdit)) {
                                    config.toolbar.titleEdit = editTitle;
                                }

                                if (angular.isUndefined(config.toolbar.titleAdd)) {
                                    config.toolbar.titleAdd = addTitle;
                                }
                                rootTitle = function () {
                                    var toolbar = $scope.dialog.toolbar,
                                        out;
                                    if ($scope.entity.id) {
                                        if (angular.isDefined(toolbar.titleEdit)) {
                                            toolbar.title = helpers.toolbar.title(toolbar.titleEdit);
                                        }
                                        out = toolbar.titleEdit;
                                    } else {
                                        if (angular.isDefined(toolbar.titleAdd)) {
                                            toolbar.title = helpers.toolbar.title(toolbar.titleAdd);
                                        }
                                        out = toolbar.titleAdd;
                                    }
                                    return out;
                                };
                                config._title_ = [rootTitle];
                                $scope.$watch('entity.id', rootTitle);
                                rootTitle();
                                process = function ($scope) {
                                    var field,
                                        done = {},
                                        madeHistory = false,
                                        makeHistory = function () {
                                            if (madeHistory || !$scope.entity.id) {
                                                return false;
                                            }
                                            if (!angular.isDefined($scope.historyConfig)) {
                                                $scope.historyConfig = false;
                                            }
                                            if ($scope.historyConfig === true) {
                                                $scope.historyConfig = {
                                                    kind: config.kind,
                                                    key: $scope.entity.key
                                                };
                                            } else {
                                                if ($scope.historyConfig === false) {
                                                    return false;
                                                }
                                            }
                                            madeHistory = true;
                                            var rule = $scope.args.ui.rule.field._records;
                                            $scope.historyConfig.key = $scope.entity.key;
                                            if (rule && rule.visible) {
                                                $scope.layouts.groups.push(recordBrowser.attach($scope.historyConfig));
                                            }
                                        };
                                    config.getScope = function () {
                                        return $scope;
                                    };
                                    modelsUtil.normalize(entity);
                                    $scope.withArgs = args;
                                    $scope.args = config.argumentLoader($scope);
                                    $scope.rootScope = $scope;

                                    $scope.formSetPristine = angular.bind($scope, helpers.form.setPristine);
                                    $scope.formSetDirty = angular.bind($scope, helpers.form.setDirty);
                                    $scope.validateForm = angular.bind($scope, helpers.form.validate);

                                    $scope.setAction = function (action) {
                                        $scope.args.action_id = action;
                                        config.action = action;
                                    };

                                    $scope.save = function (dontShowMessage) {
                                        if (!$scope.validateForm()) {
                                            return false;
                                        }
                                        config.prepareReadArguments($scope);
                                        var promise = models[config.kind].actions[$scope.args.action_id]($scope.args, {
                                            activitySpinner: true
                                        });

                                        promise.then(function (response) {
                                            $.extend($scope.entity, response.data.entity);
                                            var newArgs = config.argumentLoader($scope);
                                            $.extend($scope.args, newArgs);
                                            makeHistory();
                                            if (angular.isDefined(config.afterSave)) {
                                                config.afterSave($scope);
                                            }
                                            $scope.formSetPristine();
                                            if (!dontShowMessage) {
                                                snackbar.showK('changesSaved');
                                            }
                                        }, function (response) {
                                            // here handle error...
                                            if (angular.isDefined(config.afterSaveError)) {
                                                config.afterSaveError($scope, response);
                                            }
                                        });

                                        return promise;
                                    };

                                    $scope.uploadStart = function () {
                                        $scope.activitySpinner.start();
                                    };
                                    $scope.uploadEnd = function () {
                                        $scope.activitySpinner.stop();
                                    };
                                    $scope.uploadComplete = function (response) {
                                        $.extend($scope.entity, response.data.entity);
                                        var newArgs = config.argumentLoader($scope);
                                        $.extend($scope.args, newArgs);
                                        makeHistory();
                                        if (angular.isDefined(config.afterUploadComplete)) {
                                            config.afterUploadComplete($scope);
                                        }
                                        if (config.closeAfterSave) {
                                            $timeout(function () {
                                                $scope.close();
                                            });
                                        }
                                        $scope.formSetPristine();
                                        snackbar.showK('changesSaved');

                                    };

                                    $scope.noComplete = function () {
                                        if (angular.isDefined(config.noComplete)) {
                                            config.noComplete($scope);
                                        }
                                    };

                                    $scope.uploadError = function (response) {
                                        if (angular.isDefined(config.afterUploadError)) {
                                            config.afterUploadError($scope, response);
                                        }
                                    };

                                    $scope.close = angular.bind($scope, helpers.form.leave, function () {
                                        $scope._close_ = undefined;
                                        var promise = $scope.$close();
                                        if (config.afterClose) {
                                            config.afterClose($scope);
                                        }
                                        return promise;
                                    });

                                    $scope._close_ = $scope.close;

                                    angular.forEach(config.fields, function (field) {
                                        field._title_ = config._title_.concat();
                                    });

                                    if (angular.isDefined(config.scope)) {
                                        $.extend($scope, config.scope);
                                    }

                                    $scope.formBuilder = {
                                        '0': []
                                    };

                                    // if no accordions are defined, use the auto accordion builder
                                    if (!angular.isDefined($scope.layouts)) {
                                        $scope.layouts = {
                                            groups: [{
                                                label: false
                                            }]
                                        };

                                        angular.forEach(config.fields, function (field) {
                                            if (field.is_structured && formInputTypes[field.type]) {
                                                if (!field.ui.initialLabel) {
                                                    field.ui.initialLabel = field.ui.label;
                                                }
                                                $scope.layouts.groups.push({
                                                    label: $filter('humanized')((field.ui.initialLabel || field.code_name))
                                                });

                                                field.ui.label = false;

                                                var next = $scope.layouts.groups.length - 1;

                                                if (!angular.isDefined($scope.formBuilder[next])) {
                                                    $scope.formBuilder[next] = [];
                                                    $scope.formBuilder[next].push(field);
                                                }

                                                $scope.layouts.groups[0].disabled = false;
                                            } else {
                                                $scope.formBuilder['0'].push(field);
                                            }
                                        });


                                    } else {
                                        angular.forEach($scope.layouts.groups, function (group, i) {
                                            $scope.formBuilder[i] = [];
                                            if (!angular.isDefined(group.fields)) {
                                                var wait = false;
                                                angular.forEach(config.fields, function (field) {
                                                    if (wait) {
                                                        return;
                                                    }
                                                    if (!done[field.code_name]) {
                                                        done[field.code_name] = 1;
                                                        if (field.is_structured) {
                                                            wait = true;
                                                        }

                                                        $scope.formBuilder[i].push(field);
                                                    }
                                                });
                                            } else {
                                                angular.forEach(group.fields, function (field_key) {
                                                    if (!done[field_key]) {
                                                        field = config.keyedFields[field_key];
                                                        $scope.formBuilder[i].push(field);
                                                        done[field_key] = 1;
                                                    }
                                                });
                                            }
                                        });
                                    }

                                    $scope.$watch('dialog.toolbar.title', function (neww) {
                                        if (angular.isObject($scope.historyConfig)) {
                                            $scope.historyConfig.title = neww;
                                        }
                                    });

                                    // call config constructor, needed for posible after variable setup configurations
                                    config.defaultInit($scope);
                                    config.init($scope);
                                    makeHistory();

                                    $scope.$on('$destroy', function () {
                                        config.getScope = undefined;
                                    });

                                    defer.resolve($scope);

                                    helpers.fields.deferFormBuilderFields($scope.formBuilder).then(function () {
                                        $scope.$stateHiddenLoading = false;
                                    });
                                };
                                if (angular.isFunction(promise)) {
                                    $scope.$state.promise(promise, function ($scope, response) {
                                        $.extend(entity, response.data.entity);
                                        process($scope);
                                    });
                                } else {
                                    $scope.$state.instant(function () {
                                        process($scope);
                                    });
                                }
                            };

                            ctrl.$inject = ['$scope'];

                            opener[fn]($.extend({
                                templateUrl: 'core/models/manage.html',
                                controller: ctrl
                            }, config.modalConfig));

                            return completePromise;
                        }
                    };

                    return modelsEditorInstance;

                }
            };

            return modelsEditor;

        })).factory('modelsConfig', function () {
            // depency config loader
            var callbacks = [];
            return function (callback) {
                if (callback === true) {
                    return callbacks;
                }
                callbacks.push(callback);
            };
        }).factory('models', ng(function (endpoint, modelsMeta, $injector, modelsConfig, helpers, $q, GLOBAL_CONFIG, $rootScope) {
            var models = {}, // all model instances
                modelCreate = function (kind) {
                    // creates a new service based on kind
                    // it will map every action into function which can be called in this way: models['12'].actions.search() etc.
                    var config = {},
                        service = {
                            kind: kind,
                            actions: {},
                            getCacheKey: function (key) {
                                return this.kind + '_' + key;
                            },
                            removeCache: function (key) {
                                return endpoint.removeCache(this.getCacheKey(key));
                            },
                            getCache: function (key) {
                                return endpoint.getCache(this.getCacheKey(key));
                            },
                            setCache: function (key, data) {
                                return endpoint.setCache(this.getCacheKey(key), data);
                            },
                            get: function (key, opts) {
                                if (angular.isDefined(this.actions.search)) {
                                    return this.actions.search({
                                        search: {
                                            keys: [key]
                                        }
                                    }, opts);
                                }

                                console.error('get() relies on actions.search action. use actions.read() instead.');
                            },
                            paginate: function (config) {
                                var that = this,
                                    theConfig = {
                                        args: {
                                            search: {}
                                        },
                                        config: {}
                                    },
                                    searchAction = modelsMeta.getActionArguments(config.kind, 'search'),
                                    paginate = {
                                        loading: false,
                                        more: null,
                                        cursor: null,
                                        firstLoad: (angular.isDefined(config.firstLoad) ? config.firstLoad : true),
                                        loaded: false,
                                        args: theConfig.args,
                                        load: function (loadConfig) {
                                            loadConfig = helpers.alwaysObject(loadConfig);
                                            var promise;
                                            if (!loadConfig.runLast && (this.loading || this.more === false)) {
                                                return false;
                                            }
                                            if (!theConfig.args.search.options) {
                                                theConfig.args.search.options = {};
                                            }
                                            theConfig.args.search.options.start_cursor = loadConfig.runLast ? null : this.cursor;
                                            this.loading = !loadConfig.runLast;
                                            $.extend(theConfig.config, {
                                                disableUI: false
                                            });
                                            promise = that.actions[theConfig.action || 'search'](theConfig.args, theConfig.config);
                                            promise.error(function (response) {
                                                paginate.more = false;
                                                if (config.error) {
                                                    config.error(response);
                                                }
                                                if (loadConfig.runLast) {
                                                    loadConfig.runLast(response);
                                                    return response;
                                                }
                                                return response;
                                            }).then(function (response) {
                                                if (helpers.endpoint.isResponseError(response)) {
                                                    paginate.more = false;
                                                    if (config.error) {
                                                        config.error(response);
                                                    }
                                                    return config.complete.call(this, response);
                                                }
                                                if (loadConfig.runLast) {
                                                    loadConfig.runLast(response);
                                                    return response;
                                                }
                                                paginate.more = response.data.more;
                                                paginate.cursor = response.data.cursor;
                                                if (angular.isFunction(config.complete)) {
                                                    return config.complete.call(this, response);
                                                }
                                                return response;
                                            })['finally'](function (response) {
                                                paginate.loading = false;
                                                paginate.firstLoad = false;
                                                paginate.loaded = true;
                                            });
                                            return promise;
                                        }
                                    };
                                theConfig.args.search = searchAction.search['default'];
                                if (angular.isDefined(config.args)) {
                                    helpers.merge(config.args, theConfig.args);
                                    $.extend(theConfig, config);
                                }
                                return paginate;
                            },
                            reader: function (config) {
                                // reader instance that internally tracks the reader next read arguments.
                                // params provided are config, access, and callback
                                // and path to the structure that the reader will inject/read data
                                if (!angular.isArray(config.access)) {
                                    console.error('path must be array, ' + typeof config.access + ' given');
                                    return;
                                }

                                var fields,
                                    model = this,
                                    canLoadMore = function (nextReadArguments) {
                                        return helpers.getProperty(nextReadArguments, fields.join('.') + '.config.more');
                                    },
                                    init = function (access) {
                                        fields = [];
                                        angular.forEach(access, function (path) {
                                            if (isNaN(parseInt(path, 10))) {
                                                fields.push(path);
                                            }
                                        });
                                    },
                                    reader,
                                    readArgs,
                                    readRootArgs;

                                if (angular.isUndefined(config.next)) {
                                    readArgs = {};
                                    readRootArgs = config.args;
                                    config.next = readArgs;
                                    angular.forEach(config.access, function (part, i) {
                                        // parseInt can produce inconsistent stuff like 10_foo makes 10, so we must avoid names of
                                        // properties in datastore that begin with an number, which we do not
                                        if (!angular.isDefined(readArgs[part]) && isNaN(parseInt(part, 10))) {
                                            readArgs[part] = {
                                                config: {}
                                            };
                                            readArgs = readArgs[part];
                                        }
                                        // produce read path for the rpc
                                        readRootArgs = readRootArgs[part];
                                        if (angular.isUndefined(readRootArgs)) {
                                            return;
                                        }
                                        if (readRootArgs.key !== null && angular.isDefined(readRootArgs.key)) {
                                            if (!angular.isDefined(readArgs.config.keys)) {
                                                readArgs.config.keys = [];
                                            }
                                            readArgs.config.keys.push(readRootArgs.key);
                                        }
                                    });
                                }

                                // fields are now _images, pricetags, _product, _instances
                                init(config.access);

                                reader = {
                                    next: null,
                                    loading: false,
                                    access: config.access,
                                    more: canLoadMore(config.next),
                                    config: config,
                                    loaded: false,
                                    firstLoad: (angular.isDefined(config.firstLoad) ? config.firstLoad : true),
                                    previous: null,
                                    state: function (config) {
                                        this.next = config.next;
                                        if (angular.isDefined(config.access)) {
                                            this.access = config.access;
                                            init(this.access);
                                        }
                                        if (angular.isDefined(config.more)) {
                                            this.more = config.more;
                                        } else {
                                            this.more = canLoadMore(this.next);
                                        }
                                    },
                                    setNextReadArguments: function (nextReadArguments) {
                                        this.next = nextReadArguments;
                                        this.more = canLoadMore(this.next);
                                    },
                                    setAccess: function (access) {
                                        this.access = access;
                                        init(access);
                                        this.more = canLoadMore(this.next);
                                    },
                                    load: function (loadConfig) {
                                        loadConfig = helpers.alwaysObject(loadConfig);
                                        if (angular.isUndefined(loadConfig.runLast) && (this.more === false || this.loading)) {
                                            return false;
                                        }
                                        var that = this,
                                            next = that.next,
                                            promise,
                                            oldNext,
                                            readArgsRpc;

                                        if (!next) {
                                            next = angular.copy(config.next);
                                        }

                                        if (!this.more) {
                                            oldNext = next;
                                            angular.forEach(fields, function (value, key) {
                                                if (angular.isUndefined(next[value])) {
                                                    next[value] = {};
                                                } else {
                                                    next = next[value];
                                                }
                                            });
                                            next = oldNext;
                                        }

                                        if (!loadConfig.hideLoading) {
                                            this.loading = true;
                                        }
                                        readArgsRpc = {
                                            key: config.key,
                                            read_arguments: next
                                        };

                                        if (loadConfig.runLast) {
                                            readArgsRpc = reader.previous || readArgsRpc;
                                        }
                                        if (!loadConfig.rpcOptions) {
                                            loadConfig.rpcOptions = {};
                                        }
                                        $.extend(loadConfig.rpcOptions, {
                                            disableUI: false
                                        });

                                        promise = (config.read ? config.read(next) : (config.kind ? models[config.kind] : model).actions.read(readArgsRpc, loadConfig.rpcOptions));

                                        reader.previous = readArgsRpc;

                                        promise['finally'](function () {
                                            reader.loading = false;
                                            reader.loaded = true;
                                            reader.firstLoad = false;
                                            if (loadConfig.runLastFinally) {
                                                loadConfig.runLastFinally();
                                            }
                                        });
                                        promise.error(function (response) {
                                            that.more = false;
                                            if (config.error) {
                                                config.error(response);
                                            }
                                        });

                                        return promise.then(function (response) {
                                            if (helpers.endpoint.isResponseError(response)) {
                                                that.more = false;
                                                if (config.error) {
                                                    config.error(response);
                                                }
                                                return response;
                                            }
                                            var getAccess = [],
                                                items,
                                                loadedNext;
                                            angular.forEach(that.access, function (part) {
                                                if (!isNaN(parseInt(part, 10))) {
                                                    part = 0;
                                                }
                                                getAccess.push(part);
                                            });
                                            items = helpers.getProperty(response.data.entity, getAccess);

                                            if (loadConfig.runLast) {
                                                loadConfig.runLast(items);
                                                return response;
                                            }

                                            if (angular.isFunction(config.complete)) {
                                                config.complete(items);
                                            }

                                            loadedNext = response.data.entity._next_read_arguments;
                                            that.more = canLoadMore(loadedNext);

                                            if (that.more) {
                                                that.next = loadedNext;
                                            }

                                            return response;
                                        });
                                    }
                                };

                                return reader;

                            }
                        };

                    service.config = config;
                    angular.forEach(modelsMeta.getActions(kind), function (action, action_key) {
                        service.actions[action_key] = function (args, overrideConfig) {
                            var defaultArgs = modelsMeta.getDefaultActionArguments(kind, action_key),
                                defaults = angular.copy(config),
                                cache_key;

                            $.extend(defaultArgs, args);
                            if (angular.isDefined(overrideConfig)) {
                                if (overrideConfig.merge) {
                                    $.extend(defaults, overrideConfig);
                                } else {
                                    defaults = angular.copy(overrideConfig);
                                }
                            }

                            cache_key = config.cache;
                            if (angular.isDefined(defaults) && defaults.cache) {
                                cache_key = defaults.cache;
                            }
                            if (cache_key === true) {
                                // btoa is base64encode built-in, if cache key is true then the cache key will be autogenerated
                                cache_key = kind + '_' + action_key + '_' + window.btoa(angular.toJson(defaultArgs));
                            }
                            //console.log(cache_key, action_key, kind, defaultArgs, defaults);
                            if (!angular.isDefined(cache_key) || cache_key === false) {
                                return endpoint.post(action_key, kind, defaultArgs, defaults);
                            }
                            delete defaults.cache;
                            return endpoint.cached(cache_key, action_key, kind, defaultArgs, defaults);

                        };
                    });
                    return service;
                };

            models.initialized = false;
            models.init = function () {
                if (models.initialized === true) {
                    return;
                }

                var modelsInfo = $injector.get('modelsInfo'),
                    callbacks;

                if (!angular.isDefined(modelsInfo['0'])) {
                    return;
                }

                angular.forEach(modelsInfo, function (meta, kind) {
                    models[kind] = modelCreate(kind);
                });

                callbacks = modelsConfig(true);
                angular.forEach(callbacks, function (callback) {
                    callback(models);
                });

                models.initialized = true;
            };

            if (GLOBAL_CONFIG.debug) {
                window._models = models;
            }

            return models;

        }));
}());
