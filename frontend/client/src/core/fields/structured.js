(function () {
    'use strict';
    angular.module('app')
        .run(ng(function (helpers, modals, $modal, GLOBAL_CONFIG, $q) {
            $.extend(modals, {
                fields: {
                    remote: function (scope, field, config) {
                        $modal.open({
                            scope: scope,
                            templateUrl: 'core/models/manage.html',
                            controller: ng(function ($scope) {
                                var save = scope.save,
                                    complete = scope.uploadComplete,
                                    getTitle,
                                    initial = true;
                                getTitle = function () {
                                    return 'view' + helpers.toolbar.makeTitle(field.code_name);
                                };
                                $scope.$stateHiddenLoading = true;
                                field.ui.specifics.readerDefer = $q.defer();
                                field.ui.specifics.readerDefer.promise.then(function () {
                                    $scope.$stateHiddenLoading = false;
                                    $scope.dialog.toolbar.hideSave = false;
                                });
                                field._title_.push(getTitle);
                                $scope.dialog = {
                                    templateBodyUrl: 'core/models/manage_body_default.html',
                                    toolbar: {
                                        hideSave: true
                                    }
                                };
                                $scope.parentContainer = $scope.container;
                                $scope.container = {};
                                $scope.close = angular.bind($scope, helpers.form.leave, function () {
                                    $scope.formSetPristine();
                                    return $scope.$close();
                                });
                                $scope.formSetDirty = angular.bind($scope, helpers.form.setDirty);
                                $scope.formSetPristine = angular.bind($scope, helpers.form.setPristine);
                                $scope.formBuilder = {
                                    '0': [field]
                                };
                                $scope.layouts = {
                                    groups: [{
                                        label: false
                                    }]
                                };
                                $scope.$on('itemDelete', function () {
                                    $scope.formSetDirty();
                                });
                                $scope.$watch('parentContainer.form.$dirty', function (neww, old) {
                                    if (initial) {
                                        initial = false;
                                        return;
                                    }
                                    if (neww) {
                                        $scope.formSetDirty();
                                    } else {
                                        $scope.formSetPristine();
                                    }
                                });

                                $scope.$watch('entity.id', function () {
                                    $scope.dialog.toolbar.title = helpers.toolbar.buildTitle(field._title_);
                                });

                                $scope.save = function (dontShowMessage) {
                                    var maybePromise = save.call(scope, dontShowMessage);
                                    if (maybePromise) {
                                        maybePromise.then(function () {
                                            $scope.formSetPristine();
                                        });
                                    }
                                    return maybePromise;
                                };
                                $scope.uploadComplete = function (response) {
                                    complete.call(scope, response);
                                    $scope.formSetPristine();
                                };

                                $scope.$on('$destroy', function () {
                                    if (angular.isArray(field.ui.specifics.parentArgs)) {
                                        field.ui.specifics.parentArgs.empty();
                                    }
                                    field._title_.remove(getTitle);
                                });
                            })
                        });
                    }
                }
            });
        })).run(ng(function (formInputTypes, underscoreTemplate, $timeout, $parse,
            endpoint, modelsMeta, models, $q, $filter, $modal, helpers,
            errorHandling, modals, GLOBAL_CONFIG, snackbar) {

            $.extend(formInputTypes, {
                SuperLocalStructuredProperty: function (info) {
                    var config = info.config,
                        fields = [],
                        newFields = [],
                        modelFields = config.modelclass,
                        defaultFields = _.toArray(modelFields),
                        noSpecifics = !angular.isDefined(config.ui.specifics),
                        newSort = [],
                        defaults,
                        defaultSortable,
                        findWhereByLayoutConfig,
                        buildPaths,
                        rootArgs,
                        rootFormSetDirty = helpers.callable(info.scope.formSetDirty),
                        list = {
                            secondary: true,
                            perLine: 1,
                            clickable: true,
                            calculate: function (ent, p) {
                                return parseInt(p, 10) === parseInt(this.perLine, 10);
                            }
                        };
                    config.ui.fieldset = true;

                    if (!config.ui.specifics.toolbar) {
                        config.ui.specifics.toolbar = {};
                    }

                    if (!config.ui.specifics.remoteOpts) {
                        config.ui.specifics.remoteOpts = {};
                    }

                    config.ui.specifics.sortMode = true;
                    defaultFields = defaultFields.sort(helpers.fields.sorter);

                    if (noSpecifics || !config.ui.specifics.fields) {
                        config.ui.specifics.fields = defaultFields;
                        if (config.ui.specifics.sortFields) {
                            angular.forEach(config.ui.specifics.sortFields, function (key) {
                                newSort.push(_.findWhere(config.ui.specifics.fields, {
                                    code_name: key
                                }));
                            });

                            config.ui.specifics.fields = newSort;
                        }
                    }

                    if (!noSpecifics && config.ui.specifics.excludeFields) {
                        angular.forEach(config.ui.specifics.fields, function (field, i) {
                            if ($.inArray(field.code_name, config.ui.specifics.excludeFields) === -1) {
                                newFields.push(field);
                            }
                        });
                        config.ui.specifics.fields = newFields;
                    }

                    defaults = {
                        fields: fields,
                        addNewText: 'Add',
                        addText: '{{config.ui.specifics.addNewText}}'
                    };

                    if (config.ui.specifics.listConfig) {
                        $.extend(list, config.ui.specifics.listConfig);
                    }

                    config.ui.specifics.listConfig = list;

                    // merge defaults into the
                    angular.forEach(defaults, function (value, key) {
                        if (config.ui.specifics[key] === undefined) {
                            config.ui.specifics[key] = value;
                        }
                    });

                    config.ui.specifics.parentArgs = info.scope.$eval(config.ui.args);
                    config.ui.specifics.entity = info.scope.$eval(config.ui.model);
                    config.ui.specifics.rootScope = info.scope.$eval(config.ui.rootScope);

                    if (!config.ui.specifics.sortableOptions) {
                        config.ui.specifics.sortableOptions = {};
                    }

                    defaultSortable = {
                        disabled: false,
                        start: function (e, ui) {
                            info.scope.$broadcast('itemOrderStarted');
                        },
                        axis: false,
                        distance: 6,
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
                                    if (ent._state === 'deleted' || ent._sequence !== i) {
                                        dirty = true;
                                    }
                                    ent._sequence = i;
                                    ent.ui.access[ent.ui.access.length - 1] = i;
                                });
                            if (dirty) {
                                info.scope.formSetDirty();
                            }
                            info.scope.$broadcast('itemOrderChanged');
                            info.scope.$apply();
                        }
                    };
                    if (config.ui.specifics.setupSortableOptions) {
                        config.ui.specifics.sortableOptions = config.ui.specifics.setupSortableOptions();
                    }
                    // add default sorting config
                    $.extend(defaultSortable, config.ui.specifics.sortableOptions);
                    config.ui.specifics.sortableOptions = defaultSortable;
                    // disables sorting if the field is not writable
                    // writableCompiled is as-is specification
                    config.ui.init.add('checkDisabledStateForSortable', function () {
                        var fieldIsWritable = $parse(config.ui.writableCompiled + '');
                        config.ui.specifics.sortableOptions.disabled = !fieldIsWritable(info.scope);
                    });
                    // watches list of arguments args != new
                    info.scope.$watch(config.ui.args, function (neww, old) {
                        if (neww !== old) {
                            config.ui.specifics.parentArgs = neww;
                        }
                    });

                    buildPaths = function () {
                        // builds form fields
                        // it appends needed paths depending on hierarchy depth
                        config.ui.specifics.formBuilder = [];
                        angular.forEach(config.ui.specifics.fields, function (field) {
                            var copyWritable = angular.copy(config.ui.writable);

                            if (angular.isArray(copyWritable)) {
                                copyWritable.push((field.ui.writableName ? field.ui.writableName : field.code_name));
                            }

                            field.ui.path = [];
                            field.ui.path.extend(config.ui.path);
                            field.ui.path.push(field.code_name);
                            field.ui.realPath = [];
                            field.ui.realPath.extend(config.ui.realPath);
                            field.ui.realPath.push(field.code_name);
                            if (!angular.isDefined(field.ui.name)) {
                                field.ui.name = config.ui.name + '.' + field.code_name;
                            }
                            field.ui.writable = copyWritable;
                            config.ui.specifics.formBuilder.push(field);
                        });
                    };

                    buildPaths();

                    if (angular.isUndefined(config.ui.specifics.toolbar.titleAdd)) {
                        config.ui.specifics.toolbar.titleAdd = 'add' + helpers.toolbar.makeTitle(config.code_name);
                    }
                    if (angular.isUndefined(config.ui.specifics.toolbar.titleEdit)) {
                        config.ui.specifics.toolbar.titleEdit = 'edit' + helpers.toolbar.makeTitle(config.code_name);
                    }

                    if (config.ui.specifics.remote) {
                        // construct reference to root arguments
                        rootArgs = (config.ui.specifics.getRootArgs ? config.ui.specifics.getRootArgs() : config.ui.specifics.rootScope.args);
                        // assign "load more" logic
                        if (config.repeated && rootArgs.id && info.scope.args.id) {

                            config.ui.specifics.reader = models[rootArgs.action_model].reader({
                                kind: rootArgs.action_model,
                                key: rootArgs.key,
                                args: rootArgs,
                                access: config.ui.realPath,
                                complete: function (items) {
                                    if (!angular.isArray(config.ui.specifics.parentArgs)) {
                                        return;
                                    }
                                    config.ui.specifics.parentArgs.extend(items);
                                }
                            });
                            // apply direct reader settings if any
                            if (angular.isDefined(config.ui.specifics.readerSettings)) {
                                config.ui.specifics.reader.state(config.ui.specifics.readerSettings);
                            }

                            if ((angular.isUndefined(config.ui.specifics.remoteAutoload) || config.ui.specifics.remoteAutoload)) {
                                if (angular.isArray(config.ui.specifics.parentArgs)) {
                                    config.ui.specifics.parentArgs.empty();
                                }
                                $timeout(function () {
                                    config.ui.specifics.reader.load()['finally'](function () {
                                        if (config.ui.specifics.readerDefer) {
                                            config.ui.specifics.readerDefer.resolve();
                                        }
                                    });
                                }, 100, false);
                            }

                        }
                    }

                    if (!config.repeated && config.ui.specifics.modal !== true) {

                        config.ui.specifics.SingularCtrl = ng(function ($scope) {
                            $scope.args = config.ui.specifics.parentArgs;
                            info.scope.$watchCollection(config.ui.args, function (neww, old) {
                                $.extend($scope.args, neww);
                            });
                            config.ui.specifics.getScope = function () {
                                return $scope;
                            };
                            var getTitle = function () {
                                return config.ui.specifics.toolbar.titleEdit;
                            };
                            config._title_.push(getTitle);
                            angular.forEach(config.ui.specifics.fields, function (field) {
                                field._title_ = config._title_.concat();
                            });
                            $scope.$on('$destroy', function () {
                                config._title_.remove(getTitle);
                                config.ui.specifics.getScope = undefined;
                            });
                        });

                    } else {

                        config.ui.specifics.remove = function (arg) {
                            arg._state = 'deleted';
                            info.scope.$emit('itemDelete', arg);
                            info.scope.$broadcast('itemDelete', arg);
                            rootFormSetDirty();
                        };

                        // generic manage dialog that handles editing of remote and local structured properties
                        config.ui.specifics.manage = function (arg, defaultArgs, modalSettings) {

                            buildPaths(); // force path rebuild

                            modalSettings = helpers.alwaysObject(modalSettings);

                            $modal.open({
                                popFrom: (modalSettings && modalSettings.target ? helpers.clicks.realEventTarget(modalSettings.target) : undefined),
                                template: underscoreTemplate.get(config.ui.specifics.templateUrl || 'core/fields/manage_structured.html')({
                                    config: config
                                }),
                                inDirection: modalSettings.inDirection,
                                outDirection: modalSettings.outDirection,
                                controller: ng(function ($scope, modelsUtil) {
                                    var process, getTitle;

                                    $scope.isNew = (arg ? false : true);
                                    $scope.container = {
                                        action: endpoint.url
                                    };
                                    getTitle = function () {
                                        return config.ui.specifics.toolbar['title' + ($scope.isNew ? 'Add' : 'Edit')];
                                    };

                                    config._title_.push(getTitle);

                                    $scope.$watch('isNew', function () {
                                        config.ui.specifics.toolbar.title = helpers.toolbar.buildTitle(config._title_);
                                    });
                                    process = function ($scope) {
                                        var length = (config.ui.specifics.modal ? 0 : (config.ui.specifics.parentArgs ? config.ui.specifics.parentArgs.length : 0)),
                                            formBuilder = {
                                                '0': []
                                            },
                                            fieldsMap = {},
                                            groupBysIndx = [],
                                            groupBysMap = {},
                                            getResult = function (response, access) {
                                                var accessPath = [],
                                                    value,
                                                    isNewAndRepeated = ($scope.isNew && config.repeated);
                                                angular.forEach(access, function (path, i) {
                                                    var parse = parseInt(path, 10);
                                                    if (!isNaN(parse)) {
                                                        path = 0;
                                                    }
                                                    accessPath.push(path);
                                                });
                                                if (isNewAndRepeated) {
                                                    accessPath.pop();
                                                }
                                                value = helpers.getProperty(response.data.entity, accessPath);
                                                if (isNewAndRepeated && value.length) {
                                                    value = _.findWhere(value, {
                                                        _state: 'created'
                                                    });
                                                }

                                                return value;
                                            };

                                        angular.forEach(config.ui.specifics.formBuilder, function (value) {
                                            fieldsMap[value.code_name] = value;
                                        });

                                        config.ui.specifics.getScope = function () {
                                            return $scope;
                                        };

                                        $scope.rootFormSetDirty = rootFormSetDirty;
                                        $scope.formSetDirty = angular.bind($scope, helpers.form.setDirty);
                                        $scope.formSetPristine = angular.bind($scope, helpers.form.setPristine);

                                        $scope.response = null;
                                        $scope.config = config;
                                        if (!arg) {
                                            arg = {
                                                kind: config.modelclass_kind,
                                                _sequence: length
                                            };
                                            modelsUtil.normalize(arg, config.modelclass,
                                                config.ui.specifics.entity, config.code_name,
                                                length);
                                            if (angular.isDefined(defaultArgs)) {
                                                $.extend(arg, defaultArgs);
                                            }
                                        } else if (!config.ui.specifics.modal && arg.ui) {
                                            length = _.last(arg.ui.access);
                                        }


                                        if (angular.isDefined(arg.ui)) {
                                            arg.ui.access = angular.copy(config.ui.realPath);
                                            if (!config.ui.specifics.modal) {
                                                arg.ui.access.push(length);
                                            }
                                        }

                                        $scope.layouts = {
                                            groups: [{
                                                label: false
                                            }]
                                        };

                                        $scope.formBuilder = formBuilder;
                                        $scope.liveArg = arg;
                                        $scope.args = angular.copy($scope.liveArg);
                                        $scope.parentArgs = config.ui.specifics.parentArgs;
                                        $scope.rootScope = config.ui.specifics.rootScope;
                                        $scope.entity = config.ui.specifics.entity;
                                        if (config.ui.specifics.remote) {
                                            $scope.close = angular.bind($scope, helpers.form.leave, function () {
                                                var promise = $scope.$close();
                                                if (config.ui.specifics.afterClose) {
                                                    config.ui.specifics.afterClose($scope);
                                                }
                                                return promise;
                                            });

                                        } else {
                                            $.extend(config.ui.specifics.toolbar, {
                                                leftIcon: (config.ui.specifics.cards ? 'close' : 'arrow_back'),
                                                hideSave: true
                                            });
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
                                                } else {
                                                    return modals.confirm('discardWithFieldsRequired', $scope.$close);
                                                }
                                            };

                                            $scope._close_ = $scope.close;
                                        }

                                        $scope.validateForm = angular.bind($scope, helpers.form.validate);
                                        $scope.$on('$destroy', function () {
                                            config.ui.specifics.getScope = undefined;
                                        });
                                        if (config.ui.specifics.layoutConfig) {
                                            delete formBuilder['0'];
                                            $scope.layouts = {
                                                groups: []
                                            };
                                            angular.forEach(config.ui.specifics.layoutConfig, function (value, key) {
                                                var firstField = fieldsMap[value.fields[0]];
                                                $scope.layouts.groups.push({
                                                    label: value.label || (firstField.label || $filter('humanized')(firstField.code_name))
                                                });
                                            });
                                        }
                                        findWhereByLayoutConfig = function (field) {
                                            var layout = config.ui.specifics.layoutConfig,
                                                needle,
                                                i;
                                            for (i = layout.length - 1; i >= 0; i--) {
                                                if ($.inArray(field.code_name, layout[i].fields) !== -1) {
                                                    needle = i;
                                                    break;
                                                }
                                            }
                                            return needle;
                                        };
                                        angular.forEach(config.ui.specifics.formBuilder, function (field) {
                                            var gr, group, next;
                                            helpers.fields.applyGlobalConfig(field);
                                            if (!field.ui.initialRealPath) {
                                                field.ui.initialRealPath = angular.copy(field.ui.realPath);
                                            } else {
                                                field.ui.realPath = angular.copy(field.ui.initialRealPath);
                                            }
                                            field.ui.realPath.pop();
                                            if (!config.ui.specifics.modal) {
                                                field.ui.realPath.push(length);
                                            }
                                            field.ui.realPath.push(field.code_name);
                                            if (field.ui.groupBy) {
                                                field.ui.hideMessages = true;
                                                if (!groupBysMap[field.ui.groupBy]) {
                                                    gr = {
                                                        ui: {
                                                            group: {
                                                                help: field.ui.groupHelp,
                                                                label: field.ui.groupLabel,
                                                                name: field.ui.groupBy,
                                                                fields: [],
                                                                messages: function () {
                                                                    var messages = {
                                                                        help: true
                                                                    };
                                                                    angular.forEach(gr.ui.group.fields, function (field) {
                                                                        if (field.ui.form.hasErrors() && field.ui.form.field().$dirty) {
                                                                            messages = field.ui.form.messages();
                                                                        }
                                                                    });
                                                                    return messages;
                                                                },
                                                                shouldShowMessages: function () {
                                                                    return true;
                                                                }
                                                            }
                                                        }
                                                    };
                                                    groupBysMap[field.ui.groupBy] = gr;
                                                    groupBysIndx.push(field.ui.groupBy);
                                                    if (config.ui.specifics.layoutConfig) {
                                                        next = findWhereByLayoutConfig(field);
                                                        if (!angular.isDefined(formBuilder[next])) {
                                                            formBuilder[next] = [];
                                                        }
                                                        formBuilder[next].push(gr);
                                                    } else {
                                                        formBuilder['0'].push(gr);
                                                    }
                                                }
                                                groupBysMap[field.ui.groupBy].ui.group.fields.push(field);
                                                return;
                                            }
                                            if (config.ui.specifics.layoutConfig) {
                                                next = findWhereByLayoutConfig(field);
                                                if (!angular.isDefined(formBuilder[next])) {
                                                    formBuilder[next] = [];
                                                }
                                                formBuilder[next].push(field);
                                                // this is manual layout config, skip this part
                                                return;
                                            }
                                            if (helpers.fields.isFieldset(field) && formInputTypes[field.type]) {
                                                group = {
                                                    label: field.ui.label || $filter('humanized')(field.code_name)
                                                };
                                                if (_.string.contains(field.type, 'Remote')) {
                                                    group.include = 'core/misc/action.html';
                                                    group.action = function () {
                                                        var test = true;
                                                        if (field.ui.specifics && field.ui.specifics.canOpen) {
                                                            test = field.ui.specifics.canOpen();
                                                        }
                                                        if (test) {
                                                            modals.fields.remote($scope, field);
                                                        }
                                                    };
                                                }
                                                $scope.layouts.groups.push(group);

                                                next = $scope.layouts.groups.length - 1;

                                                if (!angular.isDefined(formBuilder[next])) {
                                                    formBuilder[next] = [];
                                                }
                                                formBuilder[next].push(field);
                                            } else {
                                                formBuilder['0'].push(field);
                                            }
                                        });

                                        if (config.ui.specifics.remote) {

                                            // reference to args that get sent
                                            $scope.rootArgs = rootArgs;
                                            $scope.setAction = function (action) {
                                                // internal helper to set the action to be executed
                                                $scope.sendRootArgs.action_id = action;
                                            };
                                            // copy of root args used for packing the customized arguments
                                            $scope.sendRootArgs = {};
                                            $scope.save = function (dontShowMessage) {
                                                if (!$scope.validateForm()) { // check if the form is valid
                                                    return false;
                                                }
                                                var promise,
                                                    prepare = function () {
                                                        var readArgs = {},
                                                            readRootArgs = $scope.rootArgs,
                                                            readRootArgsAsList,
                                                            parentArgsPath = $scope.args.ui.access,
                                                            fieldList,
                                                            traceDeep,
                                                            lastPart = [];
                                                        // set this args as single item in array
                                                        // delete all remote structured property from rpc data
                                                        readRootArgs = angular.copy(readRootArgs);
                                                        helpers.setProperty(readRootArgs, parentArgsPath, $scope.args);
                                                        if (config.ui.additionalRealPaths) {
                                                            angular.forEach(config.ui.additionalRealPaths, function (path) {
                                                                helpers.setProperty(readRootArgs, path, $scope.args);
                                                            });
                                                        }
                                                        $scope.sendRootArgs = readRootArgs;
                                                        angular.forEach($scope.rootScope.config.fields, function (field) {
                                                            if (_.string.contains(field.type, 'RemoteStructured') && field.code_name !== $scope.args.ui.access[0]) {
                                                                delete readRootArgs[field.code_name];
                                                            }
                                                        });
                                                        readRootArgs.read_arguments = readArgs;
                                                        angular.forEach(parentArgsPath, function (part, i) {
                                                            // parseInt can produce inconsistent stuff like 10_foo makes 10, so we must avoid names of
                                                            // properties in datastore that begin with an number
                                                            if (!angular.isDefined(readArgs[part]) && isNaN(parseInt(part, 10))) {
                                                                readArgs[part] = {
                                                                    config: {}
                                                                };
                                                                readArgs = readArgs[part];
                                                                lastPart.push(part);
                                                            }
                                                            // produce read path for the rpc
                                                            readRootArgs = readRootArgs[part];
                                                            if (angular.isArray(readRootArgs)) {
                                                                readRootArgsAsList = readRootArgs;
                                                            } else {
                                                                var extraReadPath = lastPart.join('.'),
                                                                    extraRead,
                                                                    extraReadClone;
                                                                if (config.ui.specifics.remoteOpts.read && config.ui.specifics.remoteOpts.read[extraReadPath]) {
                                                                    extraRead = config.ui.specifics.remoteOpts.read[extraReadPath];
                                                                }
                                                                if (angular.isDefined(readRootArgsAsList)) {
                                                                    extraReadClone = readRootArgsAsList.concat();
                                                                    readRootArgsAsList.empty();
                                                                    readRootArgsAsList.push(readRootArgs);
                                                                    if (extraRead) {
                                                                        extraRead(extraReadClone, readRootArgsAsList);
                                                                    }
                                                                    extraReadClone = null;

                                                                    readRootArgsAsList = undefined;
                                                                }
                                                                if (readRootArgs.key !== null && angular.isDefined(readRootArgs.key)) {
                                                                    if (!angular.isDefined(readArgs.config.keys)) {
                                                                        readArgs.config.keys = [];
                                                                    }
                                                                    readArgs.config.keys.push(readRootArgs.key);

                                                                }
                                                            }
                                                        });

                                                        traceDeep = function (readRootArgs, readArgs) {
                                                            if (readRootArgs && readRootArgs.key) {
                                                                fieldList = modelsMeta.getFields(readRootArgs.kind);
                                                                angular.forEach(fieldList, function (field) {
                                                                    if (field.is_structured && _.string.contains(field.type, 'RemoteStructured')) {
                                                                        var keys = [],
                                                                            newReadArgs = {
                                                                                config: {
                                                                                    keys: keys
                                                                                }
                                                                            };
                                                                        if (field.repeated) {
                                                                            angular.forEach(readRootArgs[field.code_name], function (ent) {
                                                                                if (ent.key) {
                                                                                    keys.push(ent.key);
                                                                                    traceDeep(ent, newReadArgs);
                                                                                }
                                                                            });
                                                                        }
                                                                        readArgs[field.code_name] = newReadArgs;
                                                                    }
                                                                });
                                                            } else if (angular.isArray(readRootArgs)) {
                                                                angular.forEach(readRootArgs, function (readRootArg) {
                                                                    traceDeep(readRootArg, readArgs);
                                                                });
                                                            }
                                                        };

                                                        traceDeep(readRootArgs, readArgs);
                                                    };

                                                prepare();
                                                if (config.ui.specifics.beforeSave) {
                                                    config.ui.specifics.beforeSave($scope);
                                                }
                                                // create rpc from root args's action model and action id
                                                promise = models[$scope.sendRootArgs.action_model].actions[$scope.sendRootArgs.action_id]($scope.sendRootArgs, {
                                                    activitySpinner: true
                                                });
                                                promise.then(function (response) {
                                                    $scope.response = response;
                                                    var keepAccess = angular.copy($scope.args.ui.access),
                                                        // set zero-in access path, example _images.0.pricetags.0._product.0._instances.0
                                                        value;
                                                    if (config.ui.specifics.remoteOpts.response) {
                                                        value = config.ui.specifics.remoteOpts.response(response);
                                                    } else {
                                                        value = getResult(response, keepAccess);
                                                    }
                                                    $.extend($scope.args, value); // modify current args
                                                    $scope.args.ui.access = keepAccess; // reference back original access path
                                                    if ($scope.isNew) {
                                                        if (config.repeated) {
                                                            $scope.parentArgs.unshift($scope.args); // preappend arg if they are new
                                                        }
                                                        $scope.isNew = false;
                                                    }
                                                    $.extend(arg, $scope.args); // modify provided args, usually come from the parent's scope
                                                    // re-run prepare to ensure proper paths for complete hook
                                                    prepare();
                                                    if (angular.isDefined(config.ui.specifics.afterSave)) {
                                                        config.ui.specifics.afterSave($scope);
                                                    }
                                                    $scope.formSetPristine();
                                                    if (!dontShowMessage) {
                                                        snackbar.showK('changesSaved');
                                                    }

                                                }, function (response) {
                                                    if (angular.isDefined(config.ui.specifics.afterSaveError)) {
                                                        config.ui.specifics.afterSaveError($scope, response);
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
                                                $scope.response = response;
                                                var keepAccess = angular.copy($scope.args.ui.access),
                                                    value = getResult(response, keepAccess);

                                                $.extend($scope.args, value);
                                                $scope.args.ui.access = keepAccess;
                                                if (angular.isDefined(config.ui.specifics.afterUploadComplete)) {
                                                    config.ui.specifics.afterUploadComplete($scope);
                                                }
                                                $scope.formSetPristine();

                                                snackbar.showK('changesSaved');
                                            };

                                            $scope.noComplete = function () {
                                                // fired when the scope.complete() does not get fired i.e. when no files were sent for upload
                                                if (angular.isDefined(config.ui.specifics.noComplete)) {
                                                    config.ui.specifics.noComplete($scope);
                                                }
                                                $scope.formSetPristine();
                                            };

                                            $scope.uploadError = function (response) {
                                                // fired when it failed to send http-form-data rpc
                                                if (angular.isDefined(config.ui.specifics.afterUploadError)) {
                                                    config.ui.specifics.afterUploadError($scope, response);
                                                }
                                                $scope.formSetPristine();
                                            };


                                        } else {


                                            $scope.save = function () {
                                                if (!$scope.validateForm()) { // check if the form is valid
                                                    return false;
                                                }
                                                if ($scope.container.form.$dirty) {
                                                    $scope.rootFormSetDirty();
                                                }
                                                var promise = null,
                                                    saveCompleteDefer = $q.defer(),
                                                    saveCompletePromise = saveCompleteDefer.promise,
                                                    complete = function () {
                                                        var completePromise = null,
                                                            total = 0;

                                                        if (config.repeated) {
                                                            if ($scope.isNew) {
                                                                $scope.parentArgs.unshift($scope.args);
                                                                $scope.isNew = false;
                                                                total = $scope.parentArgs.length - 1;
                                                                angular.forEach($scope.parentArgs, function (item, i) {
                                                                    i = total - i;
                                                                    item._sequence = i;
                                                                    item.sequence = i;
                                                                });
                                                            } else {
                                                                $.extend($scope.liveArg, $scope.args);
                                                            }
                                                        }

                                                        if (angular.isFunction(config.ui.specifics.afterSave)) {
                                                            completePromise = config.ui.specifics.afterSave($scope, info);
                                                        }

                                                        if (completePromise && completePromise.then) {
                                                            completePromise.then(function () {
                                                                $scope.formSetPristine();
                                                                saveCompleteDefer.resolve();
                                                                if (config.closeAfterSave) {
                                                                    $scope.close();
                                                                }
                                                            });
                                                        } else {
                                                            $scope.formSetPristine();
                                                            saveCompleteDefer.resolve();
                                                            if (config.closeAfterSave) {
                                                                $scope.close();
                                                            }
                                                        }

                                                    };

                                                if (angular.isFunction(config.ui.specifics.beforeSave)) {
                                                    promise = config.ui.specifics.beforeSave($scope, info);
                                                }

                                                if (promise && promise.then) {
                                                    promise.then(complete);
                                                } else {
                                                    complete();
                                                }
                                                return saveCompletePromise;

                                            };
                                        }

                                        // construct direct scope
                                        if (config.ui.specifics.scope) {
                                            $.extend($scope, config.ui.specifics.scope);
                                        }

                                        // call constructor
                                        if (angular.isFunction(config.ui.specifics.init)) {
                                            config.ui.specifics.init($scope);
                                        }

                                        angular.forEach(config.ui.specifics.fields, function (field) {
                                            field._title_ = config._title_.concat();
                                        });

                                        $scope.$on('$destroy', function () {
                                            config._title_.remove(getTitle);
                                            config.ui.specifics.remoteOpts = {};
                                            config.ui.additionalRealPaths = null;
                                        });

                                    };
                                    if (angular.isFunction(arg)) {
                                        $scope.$state.promise(arg, function ($scope, response) {
                                            arg = response.arg;
                                            defaultArgs = response.defaultArgs;
                                            modalSettings = response.modalSettings;
                                            process($scope);
                                        });
                                    } else {
                                        process($scope);
                                    }
                                })
                            });
                        };

                        if (angular.isUndefined(config.ui.specifics.create)) {
                            config.ui.specifics.create = config.ui.specifics.manage;
                        }

                        info.scope.$on('$destroy', function () {
                            config.ui.specifics.create = undefined;
                            config.ui.specifics.sortableOptions = {};
                        });

                    }

                    return 'structured_' + (config.repeated ? 'repeated' : 'single');
                },
                _RemoteStructuredPropery: function (info) {
                    var config = info.config;
                    config.ui.specifics.remote = true;
                },
                SuperStructuredProperty: function (info) {
                    return this.SuperLocalStructuredProperty(info);
                },
                SuperRemoteStructuredProperty: function (info) {
                    this._RemoteStructuredPropery(info);
                    var ret = this.SuperLocalStructuredProperty(info);
                    return ret;
                },
                SuperImageLocalStructuredProperty: function (info) {
                    this.SuperLocalStructuredProperty(info);
                    if (!info.config.ui.specifics.displayImageConfig) {
                        info.config.ui.specifics.displayImageConfig = {
                            size: 360
                        };
                    }
                    if (!info.config.ui.specifics.sortableOptions) {
                        info.config.ui.specifics.sortableOptions = {};
                    }
                    $.extend(info.config.ui.specifics.sortableOptions, {
                        axis: false,
                        containment: false
                    });
                    return 'image';
                },
                SuperImageStructuredProperty: function (info) {
                    if (!info.config.ui.specifics.sortableOptions) {
                        info.config.ui.specifics.sortableOptions = {};
                    }
                    $.extend(info.config.ui.specifics.sortableOptions, {
                        axis: false,
                        containment: false
                    });
                    return this.SuperImageLocalStructuredProperty(info);
                },
                SuperImageRemoteStructuredProperty: function (info) {
                    this._RemoteStructuredPropery(info);
                    var ret = this.SuperImageLocalStructuredProperty(info);
                    return ret;
                }
            });

        }));
}());
