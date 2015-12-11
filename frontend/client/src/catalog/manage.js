(function () {
    'use strict';
    angular.module('app').run(ng(function (modelsEditor, modelsMeta, modelsConfig, currentAccount, $modal, modals, helpers, $q, GLOBAL_CONFIG, $mdSidenav, $timeout, $state, snackbar, social) {

        modelsConfig(function (models) {
            var recomputeRealPath = function (field1, level) {
                    if (!level) {
                        level = 0;
                    }
                    var field2 = field1.modelclass;
                    angular.forEach(field2, function (value) {
                        if (value.ui.realPath) {
                            var con = field1.ui.realPath.concat();
                            con.push(value.code_name);
                            value.ui.realPath = con;
                            value.ui.initialRealPath = con;
                            if (value.modelclass) {
                                recomputeRealPath(value, level + 1);
                            }
                        }
                    });
                };
            $.extend(models['31'], {
                adminManageModal: function (account, extraConfig) {
                    return this.manageModal(account, undefined, extraConfig);
                },
                manageModal: function (catalog, callback, modalConfig) { // modal dialog for managing the catalog

                    callback = callback || angular.noop;

                    modalConfig = helpers.alwaysObject(modalConfig);

                    var fields = modelsMeta.getActionArguments('31', 'update'),
                        isNew = !angular.isDefined(catalog),
                        afterSave = function ($scope) {
                            $scope.setAction('catalog_upload_images');
                            $scope.dialog.toolbar.templateActionsUrl = 'catalog/manage_actions.html';
                        },
                        afterUploadComplete = function ($scope) {
                            $scope.setAction('update');
                        },
                        noComplete = function ($scope) {
                            afterUploadComplete($scope);
                        },
                        config = {
                            kind: this.kind,
                            action: (isNew ? 'create' : 'update'),
                            modalConfig: modalConfig,
                            fields: _.toArray(fields),
                            toolbar: {
                                templateActionsUrl: (isNew ? false : 'catalog/manage_actions.html'),
                                titleEdit: 'edit31',
                                titleAdd: 'add31'
                            },
                            afterSave: afterSave,
                            afterSaveError: afterSave,
                            afterUploadComplete: afterUploadComplete,
                            afterUploadError: afterUploadComplete,
                            init: function ($scope) {

                                $.extend(fields._images.ui, {
                                    label: false,
                                    specifics: {
                                        setupSortableOptions: function () {
                                            return {
                                                stop: function () {
                                                    if (fields._images.ui.specifics.parentArgs.length) {
                                                        var total = fields._images.ui.specifics.parentArgs[0].sequence,
                                                            dirty,
                                                            scope = fields._images.ui.directiveScope();
                                                        angular.forEach(fields._images.ui.specifics.parentArgs,
                                                            function (ent, i) {
                                                                i = (total - i);
                                                                if (ent.sequence !== i || ent._state === 'deleted') {
                                                                    dirty = true;
                                                                }
                                                                ent.sequence = i;
                                                                ent.ui.access[ent.ui.access.length - 1] = i;
                                                            });

                                                        if (dirty) {
                                                            scope.formSetDirty();
                                                        }
                                                        scope.$broadcast('itemOrderChanged');
                                                        scope.$apply();

                                                    }
                                                }
                                            };
                                        }
                                    }
                                });

                                var updateFields = ['state', 'ui.rule', 'created', 'updated'],
                                    updateState = function (newArgs) {
                                        angular.forEach(['args', 'entity'], function (p) {
                                            helpers.update($scope[p], newArgs, updateFields);
                                        });
                                    };

                                $scope.dequeueChannel = [];
                                $scope.$on('$destroy', function () {
                                    angular.forEach($scope.dequeueChannel, function (cb) {
                                        cb();
                                    });
                                });

                                $scope.$watch('entity.id', function (newValue) {
                                    if (newValue) {
                                        callback($scope.entity);
                                    }
                                });

                                $scope.actions = {
                                    publish: function () {
                                        modals.confirm('publishCatalog',
                                            function () {
                                                models['31'].actions.publish({
                                                    key: $scope.entity.key
                                                }, {
                                                    activitySpinner: true
                                                }).then(function (response) {
                                                    snackbar.showK('catalogPublished');
                                                    updateState(response.data.entity);
                                                });
                                            });
                                    },
                                    discontinue: function () {
                                        modals.confirm('discontinueCatalog',
                                            function () {
                                                models['31'].actions.discontinue({
                                                    key: $scope.entity.key
                                                }, {
                                                    activitySpinner: true
                                                }).then(function (response) {
                                                    snackbar.showK('catalogDiscontinued');
                                                    updateState(response.data.entity);
                                                });
                                            });
                                    },
                                    duplicate: function () {
                                        modals.confirm('duplicateCatalog',
                                            function () {
                                                models['11'].channelNotifications({
                                                    callback: function (response) {
                                                        models['31'].actions.read({
                                                            key: response.catalog_key,
                                                            read_arguments: {
                                                                cover: {}
                                                            }
                                                        }, {
                                                            disableUI: false
                                                        }).then(function (response) {
                                                            snackbar.showK('catalogDuplicated');
                                                            callback(response.data.entity);
                                                        });
                                                    }
                                                }).then(function (response) {
                                                    //$scope.dequeueChannel.push(response.channel[1]);
                                                    models['31'].actions.catalog_duplicate({
                                                        key: $scope.entity.key,
                                                        channel: response.token
                                                    }, {
                                                        activitySpinner: true,
                                                        disableUI: false
                                                    });
                                                });
                                            });
                                    },
                                    sudo: function () {
                                        modals.models.sudo($scope.entity, {
                                            templateUrl: 'catalog/administer.html',
                                            onConfirm: updateState
                                        });
                                    }
                                };
                            },
                            noComplete: noComplete,
                            scope: {
                                historyConfig: true,
                                addProducts: function () {
                                    var parentScope = this;
                                    $modal.open({
                                        templateUrl: 'core/models/manage.html',
                                        windowClass: 'no-overflow',
                                        controller: ng(function ($scope, $timeout) {
                                            var accessImages = angular.copy(parentScope.args.ui.access),
                                                imagesReader,
                                                setupCurrentPricetag,
                                                variantOptions,
                                                addNewPricetag,
                                                removePricetag,
                                                getTitle = function () {
                                                    return 'viewProducts';
                                                };
                                            accessImages.push(fields._images.code_name);
                                            $scope.rootScope = parentScope.rootScope; // pass the rootScope
                                            $scope.config = parentScope.rootScope.config;
                                            $scope.entity = parentScope.entity;
                                            $scope.args = angular.copy(parentScope.args);
                                            $scope.dialog = {
                                                templateBodyUrl: 'catalog/manage_products.html',
                                                toolbar: {
                                                    hideSave: true
                                                }
                                            };
                                            $scope.dequeueChannel = [];
                                            $scope.$on('$destroy', function () {
                                                angular.forEach($scope.dequeueChannel, function (cb) {
                                                    cb();
                                                });
                                            });
                                            $scope.imagesLoaded = false;
                                            $scope.container = {};
                                            $scope.formSetPristine = angular.bind($scope, helpers.form.setPristine);
                                            $scope.formSetDirty = angular.bind($scope, helpers.form.setDirty);
                                            $scope.validateForm = angular.bind($scope, helpers.form.validate);
                                            $scope.fieldProduct = fields._images.modelclass.pricetags.modelclass._product;
                                            $scope.args._images = [];
                                            $scope.config._title_.push(getTitle);
                                            $scope.$on('$destroy', function () {
                                                $scope.config._title_.remove(getTitle);
                                                fields._images._title_.remove(getTitle);
                                                fields._images.modelclass.pricetags._title_.remove(getTitle);
                                                fields._images.modelclass.pricetags.modelclass._product._title_.remove(getTitle);
                                            });
                                            fields._images._title_ = $scope.config._title_.concat();
                                            fields._images.modelclass.pricetags._title_ = fields._images._title_.concat();
                                            $scope.fieldProduct._title_ = fields._images._title_.concat();
                                            $scope.dialog.toolbar.title = helpers.toolbar.buildTitle($scope.config._title_);

                                            $scope.trackPricetags = function (pricetag) {
                                                if (pricetag.key) {
                                                    return pricetag.key;
                                                }
                                                return 'new' + _.uniqueId();
                                            };

                                            imagesReader = models['31'].reader({
                                                key: $scope.args.key,
                                                next: {
                                                    _images: {}
                                                },
                                                access: accessImages,
                                                complete: function (items) {
                                                    $scope.args._images.extend(items);
                                                    $timeout(function () {
                                                        $scope.imagesLoaded = true;
                                                    }, 300);
                                                }
                                            });
                                            variantOptions = $scope.fieldProduct.modelclass._instances.modelclass.variant_options;
                                            if (!variantOptions.ui.specifics) {
                                                variantOptions.ui.specifics = {};
                                            }
                                            variantOptions.ui.specifics.checkboxes = true;
                                            variantOptions.ui.fieldset = true;
                                            if (!variantOptions.ui.specifics) {
                                                variantOptions.ui.specifics = {};
                                            }
                                            variantOptions.ui.specifics.listView = function (item) {
                                                return angular.isObject(item) ? item.full : item;
                                            };
                                            variantOptions.ui.specifics.grouping = function (items) {
                                                var list = [],
                                                    map = {};
                                                angular.forEach(items, function (value) {
                                                    var split = value.split(': '),
                                                        obj = map[split[0]];
                                                    if (!obj) {
                                                        obj = {
                                                            label: split[0],
                                                            items: []
                                                        };
                                                        map[split[0]] = obj;
                                                        list.push(obj);
                                                    }

                                                    obj.items.push({
                                                        name: split[1],
                                                        key: value,
                                                        full: value
                                                    });
                                                });
                                                return list;
                                            };

                                            addNewPricetag = function (image, pricetag) {
                                                image.pricetags.push(pricetag);
                                                var existing = _.findWhere($scope.rootScope.args._images, {
                                                    key: image.key
                                                });
                                                if (!existing) {
                                                    return;
                                                }
                                                existing.pricetags.push(pricetag);
                                            };

                                            removePricetag = function (image, pricetag) {
                                                if (angular.isDefined(pricetag._destroy)) {
                                                    pricetag._destroy();
                                                }
                                                image.pricetags.remove(pricetag);
                                                var existing = _.findWhere($scope.rootScope.args._images, {
                                                    key: image.key
                                                });
                                                if (!existing) {
                                                    return;
                                                }
                                                existing.pricetags.iremove(function (ipricetag) {
                                                    return ipricetag.key === pricetag.key;
                                                });
                                            };
                                            $scope.$stateHiddenLoading = true;
                                            $scope.$on('modalOpened', function () {
                                                imagesReader.load()['finally'](function () {
                                                    $scope.$stateHiddenLoading = false;
                                                    $scope.dialog.toolbar.hideSave = false;
                                                });
                                            });

                                            $scope.onStart = function (event, ui, image, pricetag) {
                                                $(ui.helper).addClass('dragged');
                                                $(ui.helper).find('a').addClass('dragged');
                                                if (angular.isUndefined(pricetag._image)) {
                                                    pricetag._image = $scope.args._images.indexOf(image);
                                                }
                                                $scope.syncStop();
                                            };

                                            $scope.onDrag = function (event, ui, image, pricetag) {};

                                            $scope.droppableOptions = {
                                                accept: '.catalog-new-pricetag',
                                                tolerance: 'pointer',
                                                cancel: "input,textarea,button,select,option,[disabled]"
                                            };

                                            $scope.draggableOptions = {
                                                containment: '.image-slider-outer',
                                                distance: 6,
                                                cancel: "input,textarea,button,select,option,[disabled]"
                                            };

                                            $scope.newPricetagDraggableOptions = {revert: function (element) {
                                                if (!element) {
                                                    return true;
                                                }
                                                var truth = $scope.container.form.$dirty;
                                                if (truth) {
                                                    snackbar.showK('saveChangesFirst');
                                                }
                                                return truth;
                                            }, distance: 10, helper: 'clone'};

                                            $scope.onStop = function (event, ui, image, pricetag) {
                                                setTimeout(function () {
                                                    $(ui.helper).removeClass('dragged');
                                                    $(ui.helper).find('a').removeClass('dragged');
                                                }, 350);
                                                if (pricetag._state === 'deleted') {
                                                    return;
                                                }

                                                var target = $(event.target).parents('.image-slider-item:first'),
                                                    pricetagElement = $(event.target),
                                                    left = parseFloat(pricetagElement.css('left'), 10),
                                                    width = pricetagElement.width(),
                                                    targetWidth = target.width(),
                                                    tolerance = targetWidth - (width + left),
                                                    i = $scope.args._images.indexOf(image),
                                                    cwidth = 0,
                                                    pwidth = 0,
                                                    next,
                                                    extract;
                                                extract = function (what) {
                                                    var newImage,
                                                        exists,
                                                        newParent,
                                                        newPricetag,
                                                        newPositionLeft,
                                                        ocw = 0,
                                                        currentTop = parseFloat($(ui.helper).css('top'), 10);
                                                    next = target;
                                                    cwidth = what ? targetWidth : 0;
                                                    while (true) {
                                                        if (what) {
                                                            i += 1;
                                                            next = next.next();
                                                            cwidth += next.width();
                                                            if (cwidth > left) {
                                                                newParent = next;
                                                                newImage = $scope.args._images[i];
                                                                newPositionLeft = left - (pwidth || targetWidth);
                                                                break;
                                                            }
                                                            if (i > 10000) {
                                                                break;
                                                            }

                                                            pwidth = cwidth;
                                                        } else {
                                                            i -= 1;
                                                            next = next.prev();
                                                            ocw += next.width();
                                                            cwidth -= next.width();
                                                            if (cwidth < left) {
                                                                newParent = next;
                                                                newImage = $scope.args._images[i];
                                                                newPositionLeft = ocw + left;
                                                                break;
                                                            }
                                                            if (i < 0) {
                                                                break;
                                                            }
                                                        }
                                                    }
                                                    if (newImage) {
                                                        pricetag._state = 'deleted';
                                                        pricetagElement.addClass('ng-hide');
                                                        exists = _.findWhere(newImage.pricetags, {
                                                            key: pricetag.key
                                                        });
                                                        if (exists) {
                                                            pricetag = exists;
                                                        }
                                                        pricetag.image_width = newParent.width();
                                                        pricetag.image_height = newParent.height();
                                                        pricetag.position_left = newPositionLeft;
                                                        pricetag.position_top = currentTop;
                                                        pricetag._position_left = newPositionLeft;
                                                        pricetag._position_top = currentTop;
                                                        if (angular.isUndefined(exists)) {
                                                            newPricetag = angular.copy(pricetag);
                                                            newPricetag._state = null;
                                                            newPricetag._must_save = true;
                                                            if (angular.isUndefined(pricetag._image)) {
                                                                newPricetag._image = i;
                                                            }
                                                            addNewPricetag(newImage, newPricetag);
                                                        } else {
                                                            exists._state = null;
                                                        }
                                                    }
                                                };

                                                pricetag.position_top = ui.position.top;
                                                pricetag.position_left = ui.position.left;
                                                pricetag.image_width = target.width();
                                                pricetag.image_height = target.height();
                                                pricetag._position_top = pricetag.position_top;
                                                pricetag._position_left = pricetag.position_left;

                                                $scope.formSetDirty();

                                                if ((tolerance + width) < 3.3) {
                                                    //console.log('must go to next image');
                                                    extract(true);
                                                } else if (left < -8.5) {
                                                    //console.log('must go to the previous image');
                                                    extract();
                                                }

                                                if (!$scope.$$phase) {
                                                    $scope.$apply();
                                                }
                                                $scope.$broadcast('resizePricetags', pricetag);

                                                //$scope.syncStart();

                                            };

                                            $scope.onDrop = function (event, ui, image) {
                                                if ($scope.container.form.$dirty) {
                                                    return;
                                                }
                                                var target_drop = $(event.target),
                                                    posi = target_drop.offset(),
                                                    posi2 = ui.offset,
                                                    rtop = posi2.top - posi.top + 6,
                                                    rleft = posi2.left - posi.left + 4,
                                                    vdom = $('<div style="visibility:hidden;"></div>'),
                                                    newPricetagConfig = {
                                                        position_top: rtop,
                                                        position_left: rleft,
                                                        _image: $scope.args._images.indexOf(image),
                                                        image_width: target_drop.width(),
                                                        image_height: target_drop.height()
                                                    };
                                                vdom.css({
                                                    top: rtop,
                                                    position: 'absolute',
                                                    left: rleft,
                                                    width: ui.draggable.width(),
                                                    height: ui.draggable.height()
                                                });
                                                vdom.appendTo(target_drop);
                                                newPricetagConfig._destroy = function () {
                                                    $timeout(function () {
                                                        vdom.remove();
                                                    }, 2000, false);
                                                };
                                                $scope.createProduct(image, newPricetagConfig, vdom);
                                            };

                                            $scope.imagesReader = imagesReader;

                                            imagesReader.showLoaderAlways = true;

                                            $scope.loadMoreImages = function (callback) {
                                                var promise = imagesReader.load();
                                                if (promise) {
                                                    promise.then(function (response) {
                                                        callback.call(this, response, imagesReader.more);
                                                    });
                                                } else {
                                                    callback.call(this, undefined, imagesReader.more);
                                                }
                                            };

                                            setupCurrentPricetag = function (image, pricetag) {
                                                $scope.image = image;
                                                $scope.pricetag = pricetag;
                                            };

                                            $scope.loadingManageProduct = false;
                                            $scope.lastManageProduct = null;
                                            $scope.manageProduct = function (image, pricetag, $event) {
                                                var syncing = ($scope.syncScheduleNext || $scope.syncLoading),
                                                    dirty = $scope.container.form.$dirty;
                                                if (syncing || dirty) {
                                                    //$scope.lastManageProduct = [image, pricetag, $event];
                                                    snackbar.showK('saveChangesFirst');
                                                    return;
                                                    /*
                                                    return (syncing ? $scope.saveDefer.promise : $scope.save(true)).then(function () {
                                                        image = _.findWhere($scope.args._images, {
                                                            key: image.key
                                                        });
                                                        pricetag = _.findWhere(image.pricetags, {
                                                            key: pricetag.key
                                                        });
                                                        return $scope.realManageProduct(image, pricetag, $event);
                                                    });*/
                                                }
                                                return $scope.realManageProduct(image, pricetag, $event);
                                            };

                                            $scope.realManageProduct = function (image, pricetag, $event) {
                                                if ($scope.loadingManageProduct) {
                                                    return;
                                                }
                                                $scope.loadingManageProduct = true;
                                                setupCurrentPricetag(image, pricetag);
                                                // perform read catalog.images.0.pricetags.0._product
                                                var open = function () {
                                                    return models['31'].actions.read({
                                                        key: $scope.entity.key,
                                                        read_arguments: {
                                                            _images: {
                                                                config: {
                                                                    keys: [image.key]
                                                                },
                                                                pricetags: {
                                                                    config: {
                                                                        keys: [pricetag.key],
                                                                    },
                                                                    _product: {}
                                                                }
                                                            }
                                                        }
                                                    }).then(function (response) {
                                                        var responseEntity = response.data.entity,
                                                            ii = $scope.args._images.indexOf(image),
                                                            product = responseEntity._images[0].pricetags[0]._product,
                                                            shouldAppearDropdown = false,
                                                            oldPricetagIndex = _.findIndex(image.pricetags, function (ipricetag) {
                                                                return ipricetag.key === pricetag.key;
                                                            }),
                                                            realPath = ['_images', ii, 'pricetags', oldPricetagIndex, '_product'];
                                                        if (!$scope.fieldProduct.ui.specifics.toolbar) {
                                                            $scope.fieldProduct.ui.specifics.toolbar = {};
                                                        }
                                                        shouldAppearDropdown = $scope.entity.ui.rule.action.catalog_pricetag_duplicate.executable || $scope.entity.ui.rule.field._images.pricetags.writable;
                                                        $scope.fieldProduct.ui.specifics.toolbar.templateActionsUrl = (shouldAppearDropdown ? 'catalog/product/manage_actions.html' : undefined);
                                                        pricetag._product = product;
                                                        if (!product._stock) {
                                                            product._stock = {
                                                                stocks: []
                                                            };
                                                        }
                                                        product.ui.access = realPath; // override normalizeEntity auto generated path
                                                        $scope.fieldProduct.ui.realPath = realPath; // set same path
                                                        recomputeRealPath($scope.fieldProduct);
                                                        return {
                                                            arg: product,
                                                            defaultArgs: undefined
                                                        };

                                                    })['finally'](function () {
                                                        $scope.loadingManageProduct = false;
                                                    });
                                                };

                                                $scope.fieldProduct.ui.specifics.manage(open, undefined, {
                                                    target: (!$($event.target).hasClass('catalog-pricetag') ? $($event.target).parents('.catalog-pricetag:first').get(0) : $event.target)
                                                });
                                            };

                                            $scope.howToDrag = function ($event) {
                                                modals.alert('howToDropPricetag');
                                            };

                                            $scope.createProduct = function (image, config, target) {
                                                var ii = $scope.args._images.indexOf(image),
                                                    newPricetag = {
                                                        _sequence: image.pricetags.length,
                                                        image_height: config.image_height,
                                                        image_width: config.image_width,
                                                        position_left: config.position_left,
                                                        position_top: config.position_top,
                                                        _position_left: config.position_left,
                                                        _position_top: config.position_top,
                                                        value: {},
                                                        _destroy: config._destroy,
                                                        _product: {
                                                            _stock: {
                                                                stocks: []
                                                            }
                                                        },
                                                        ui: {
                                                            access: ['_images', ii, 'pricetags', image.pricetags.length]
                                                        }
                                                    };
                                                addNewPricetag(image, newPricetag); // append new pricetag to image
                                                setupCurrentPricetag(image, newPricetag); // set current
                                                $scope.fieldProduct.ui.specifics.toolbar.templateActionsUrl = false;
                                                $scope.fieldProduct.ui.realPath = ['_images', ii, 'pricetags', image.pricetags.length - 1, '_product']; // set correct pathing for the new product
                                                recomputeRealPath($scope.fieldProduct);
                                                $scope.fieldProduct.ui.specifics.create(undefined, newPricetag._product, {
                                                    target: target
                                                });
                                            };

                                            $.extend($scope.fieldProduct.ui, {
                                                init: function (field) {
                                                    field.config.ui.specifics.remove = function (product, close) {
                                                        // removing the actual product removes the pricetag actually
                                                        $scope.pricetag._state = 'deleted';
                                                        $scope.formSetDirty();
                                                        close();
                                                    };
                                                },
                                                args: 'pricetag._product',
                                                parentArgs: 'pricetag',
                                                path: ['_images', 'pricetags', '_product'],
                                                render: false,
                                                label: false,
                                                specifics: {
                                                    remoteAutoload: false,
                                                    modal: true,
                                                    removeConfirm: function (arg, close) {
                                                        modals.confirm('removePricetagConfirm', function () {
                                                            $scope.pricetag._state = 'deleted';
                                                            $scope.formSetDirty();
                                                            $timeout(function () {
                                                                close().then(function () {
                                                                    $timeout(function () {
                                                                        $scope.save();
                                                                    });
                                                                });
                                                            });
                                                        });
                                                    },
                                                    beforeSave: function (fieldScope) {
                                                        fieldScope.setAction('update');
                                                        // before saving entity, set the name and unit price for the pricetag.
                                                        var findPricetag = _.last(fieldScope.sendRootArgs._images[0].pricetags);
                                                        findPricetag.value = {
                                                            name: fieldScope.args.name,
                                                            price: fieldScope.args.unit_price
                                                        };
                                                    },
                                                    templateFooterUrl: 'catalog/product/manage_footer.html',
                                                    getRootArgs: function () {
                                                        // root args is data that gets sent with rpc
                                                        return $scope.args;
                                                    },
                                                    afterClose: function (fieldProductScope) {
                                                        // after close hook
                                                        $scope.pricetag._product = null;
                                                        if (!fieldProductScope.args.key) {
                                                            removePricetag($scope.image, $scope.pricetag); // remove the pricetag if we did not commit the product
                                                        }
                                                    },
                                                    afterSave: function (fieldScope) {
                                                        // after save hook
                                                        fieldScope.setAction('product_upload_images');
                                                        var updatedPricetag = fieldScope.response.data.entity._images[0].pricetags[0];
                                                        $scope.fieldProduct.ui.specifics.toolbar.templateActionsUrl = 'catalog/product/manage_actions.html';
                                                        $.extend($scope.pricetag, updatedPricetag); // after save, always update the live pricetag, because there is no way that field scope can access this scope
                                                    },
                                                    afterUploadComplete: function (fieldScope) {
                                                        // after complete hook
                                                        fieldScope.setAction('update');
                                                    },
                                                    noComplete: function (fieldScope) {
                                                        // hook for no complete event - complete event only fires if there are images to be uploaded
                                                        fieldScope.setAction('update');
                                                    },
                                                    duplicate: function () {
                                                        modals.confirm('duplicateCatalogPricetag',
                                                            function () {
                                                                models['11'].channelNotifications({
                                                                    callback: function (response) {
                                                                        models['31'].actions.read({
                                                                            key: response.catalog_key,
                                                                            read_arguments: {
                                                                                _images: {
                                                                                    config: {
                                                                                        keys: [response.image_key]
                                                                                    },
                                                                                    pricetags: {
                                                                                        config: {
                                                                                            keys: [response.pricetag_key]
                                                                                        }
                                                                                    }
                                                                                }
                                                                            }
                                                                        }, {
                                                                            disableUI: false
                                                                        }).then(function (response2) {

                                                                            var image = _.findWhere($scope.args._images, {
                                                                                key: response.image_key
                                                                            });
                                                                            if (image) {
                                                                                angular.forEach(response2.data.entity._images[0].pricetags, function (value, key) {
                                                                                    if (!_.findWhere(image.pricetags, {
                                                                                            key: response.pricetag_key
                                                                                        })) {
                                                                                        console.log(response);
                                                                                        image.pricetags.push(value);
                                                                                    }
                                                                                });
                                                                            }
                                                                            snackbar.showK('productDuplicated');
                                                                        });
                                                                    }
                                                                }).then(function (response) {
                                                                    //$scope.dequeueChannel.push(response.channel[1]);
                                                                    models['31'].actions.catalog_pricetag_duplicate({
                                                                        key: $scope.entity.key,
                                                                        channel: response.token,
                                                                        read_arguments: {
                                                                            _images: {
                                                                                config: {
                                                                                    keys: [$scope.image.key]
                                                                                },
                                                                                pricetags: {
                                                                                    config: {
                                                                                        keys: [$scope.pricetag.key]
                                                                                    }
                                                                                }
                                                                            }
                                                                        }
                                                                    }, {
                                                                        activitySpinner: true,
                                                                        disableUI: false
                                                                    });
                                                                });
                                                            });
                                                    }
                                                }
                                            });

                                            $.extend($scope.fieldProduct.modelclass.images.ui, {
                                                name: 'images'
                                            });

                                            $.extend($scope.fieldProduct.modelclass._instances.modelclass.images.ui, {
                                                name: 'images'
                                            });

                                            $scope.fieldProduct.modelclass.category.ui.specifics = {
                                                search: {
                                                    enabled: true
                                                }
                                            };

                                            $.extend($scope.fieldProduct.modelclass._stock.ui, {
                                                specifics: {
                                                    canOpen: function () {
                                                        var currentFieldScope = $scope.fieldProduct.ui.specifics.getScope(),
                                                            currentArgs = currentFieldScope.args;
                                                        if (!currentArgs.id) {
                                                            snackbar.showK('saveProductFirst');
                                                            return false;
                                                        }
                                                        return true;
                                                    }
                                                }
                                            });

                                            $.extend($scope.fieldProduct.modelclass._stock.modelclass.stocks.ui, {
                                                specifics: {
                                                    cards: true,
                                                    cardView: 'product-stock-configuration-card-view',
                                                    init: function (fieldScope) {
                                                        var variants = $scope.fieldProduct.ui.specifics.getScope().args.variants,
                                                            availability = fieldScope.formBuilder[0].pop(),
                                                            swichables = [],
                                                            save,
                                                            i1 = 0;
                                                        fieldScope.formBuilder[0].empty();
                                                        fieldScope.variantCombination = {};
                                                        angular.forEach(variants, function (value) {
                                                            if (value.allow_custom_value) {
                                                                return;
                                                            }
                                                            try {
                                                                fieldScope.variantCombination[i1] = _.values(fieldScope.args.variant_signature[i1])[0];
                                                            } catch (ignore) {}
                                                            var computeWritable = (function () {
                                                                    var t = [];
                                                                    angular.forEach(fieldScope.args.ui.access, function (value, key) {
                                                                        if (!angular.isNumber(value)) {
                                                                            t.push("['" + value + "']");
                                                                        }
                                                                    });
                                                                    return t.join('');
                                                                }()),
                                                                field = {
                                                                    type: 'SuperStringProperty',
                                                                    choices: (function () {
                                                                        var list = value.options.concat(),
                                                                            values = [{
                                                                                key: '***Any***',
                                                                                name: 'Any'
                                                                            }];
                                                                        angular.forEach(list, function (v) {
                                                                            values.push({
                                                                                key: v,
                                                                                name: v
                                                                            });
                                                                        });
                                                                        return values;
                                                                    }()),
                                                                    code_name: 'variant_choice_' + i1,
                                                                    required: true,
                                                                    ui: {
                                                                        writable: 'entity.ui.rule.field' + computeWritable + '.variant_signature.writable',
                                                                        label: value.name,
                                                                        help: value.description,
                                                                        args: 'variantCombination[' + i1 + ']',
                                                                        attrs: {
                                                                            'ng-change': 'changeVariantCommit()'
                                                                        }
                                                                    }
                                                                };
                                                            swichables.push(field);
                                                            fieldScope.formBuilder[0].push(field);
                                                            i1 += 1;
                                                        });
                                                        fieldScope.formBuilder[0].push(availability);
                                                        fieldScope.changeVariantCommit = function () {
                                                            var i2 = 0;
                                                            angular.forEach(variants, function (value) {
                                                                if (value.allow_custom_value) {
                                                                    return;
                                                                }
                                                                var d = {};
                                                                d[value.name] = fieldScope.variantCombination[i2];
                                                                if (angular.isDefined(fieldScope.args.variant_signature[i2])) {
                                                                    fieldScope.args.variant_signature[i2] = d;
                                                                } else {
                                                                    fieldScope.args.variant_signature.push(d);
                                                                }
                                                                i2 += 1;
                                                            });
                                                        };

                                                        save = fieldScope.save;

                                                        fieldScope.save = function () {
                                                            var match,
                                                                matchStr = JSON.stringify(fieldScope.args.variant_signature);
                                                            angular.forEach(fieldScope.parentArgs, function (value, key) {
                                                                if (JSON.stringify(value.variant_signature) === matchStr) {
                                                                    match = value;
                                                                }
                                                            });
                                                            if (match) {
                                                                $.extend(match, fieldScope.args);
                                                                fieldScope.isNew = false;
                                                                fieldScope.liveArg = match;
                                                            }
                                                            return save();
                                                        };
                                                    }
                                                }
                                            });



                                            $.extend($scope.fieldProduct.modelclass._instances.ui, {
                                                label: GLOBAL_CONFIG.subheaders.productInstances,
                                                path: ['_images', 'pricetags'],
                                                specifics: {
                                                    layoutConfig: [{
                                                        label: GLOBAL_CONFIG.fields.label['28'].variant_options,
                                                        fields: ["variant_options"]
                                                    }, {
                                                        label: 'Details',
                                                        fields: ["code", "description", "unit_price", "weight", "volume"]
                                                    }, {
                                                        fields: ["images"]
                                                    }, {
                                                        fields: ["contents"]
                                                    }],
                                                    cards: true,
                                                    cardView: 'product-instance-card-view',
                                                    getRootArgs: function () {
                                                        return $scope.args;
                                                    },
                                                    beforeSave: function (fieldScope) {
                                                        fieldScope.setAction('update');
                                                    },
                                                    afterSave: function (fieldScope) {
                                                        fieldScope.setAction('product_instance_upload_images');
                                                    },
                                                    afterUploadComplete: function (fieldScope) {
                                                        fieldScope.setAction('update');
                                                    },
                                                    noComplete: function (fieldScope) {
                                                        fieldScope.setAction('update');
                                                    },
                                                    setupSortableOptions: function () {
                                                        return {
                                                            stop: function () {
                                                                var field = $scope.fieldProduct.modelclass._instances,
                                                                    total,
                                                                    dirty,
                                                                    scope = field.ui.directiveScope();
                                                                if (field.ui.specifics.parentArgs.length) {
                                                                    total = field.ui.specifics.parentArgs[0].sequence;
                                                                    angular.forEach(field.ui.specifics.parentArgs,
                                                                        function (ent, i) {
                                                                            i = (total - i);
                                                                            if (ent.sequence !== i || ent._state === 'deleted') {
                                                                                dirty = true;
                                                                            }
                                                                            ent.sequence = i;
                                                                            ent.ui.access[ent.ui.access.length - 1] = i;
                                                                        });
                                                                    if (dirty) {
                                                                        scope.formSetDirty();
                                                                    }
                                                                    scope.$broadcast('itemOrderChanged');
                                                                    scope.$apply();
                                                                }
                                                            }
                                                        };
                                                    },
                                                    canOpen: function () {
                                                        var currentFieldScope = $scope.fieldProduct.ui.specifics.getScope(),
                                                            currentArgs = currentFieldScope.args;
                                                        if (!currentArgs.id) {
                                                            snackbar.showK('saveProductFirst');
                                                            return false;
                                                        }
                                                        if (!currentArgs.variants.length) {
                                                            snackbar.showK('createVariantsFirst');
                                                            return false;
                                                        }
                                                        return true;
                                                    },
                                                    init: function () {
                                                        var currentFieldScope = $scope.fieldProduct.ui.specifics.getScope(),
                                                            currentArgs = currentFieldScope.args,
                                                            choices = [];

                                                        angular.forEach(currentArgs.variants, function (variant) {
                                                            if (variant.allow_custom_value) {
                                                                return;
                                                            }
                                                            angular.forEach(variant.options, function (variantOpt) {
                                                                choices.push(variant.name + ': ' + variantOpt);
                                                            });
                                                        });

                                                        variantOptions.choices = choices;
                                                    },
                                                    excludeFields: ['created', 'sequence']
                                                }
                                            });

                                            $.extend($scope.fieldProduct.modelclass.contents.ui, {
                                                specifics: {}
                                            });

                                            $.extend($scope.fieldProduct.modelclass.images.ui, {
                                                name: 'images',
                                                specifics: {}
                                            });

                                            $.extend($scope.fieldProduct.modelclass.variants.ui, {
                                                specifics: {}
                                            });


                                            if (!$scope.fieldProduct.modelclass.uom.ui.specifics) {
                                                $scope.fieldProduct.modelclass.uom.ui.specifics = {};
                                            }

                                            $scope.fieldProduct.modelclass.uom.ui.specifics.grouping = function (items) {
                                                var grouped = [],
                                                    current;
                                                angular.forEach(items, function (item) {
                                                    if (current && current.label !== item.measurement) {
                                                        current = null;
                                                    }
                                                    if (!current) {
                                                        current = {
                                                            label: item.measurement,
                                                            items: []
                                                        };
                                                        grouped.push(current);
                                                    }

                                                    current.items.push(item);
                                                });

                                                return grouped;
                                            };

                                            $scope.loadingSave = false;

                                            $scope.save = function (hideSnackbar, timeoutDefer, hideSpinner) {
                                                if ($scope.loadingSave) {
                                                    snackbar.showK('saveInProgress');
                                                    return;
                                                }
                                                var promise,
                                                    timeout = timeoutDefer ? timeoutDefer.promise : undefined;
                                                $scope.syncCancelDefer = timeoutDefer;
                                                $scope.loadingSave = true;
                                                $scope.rootScope.config.prepareReadArguments($scope);
                                                promise = models['31'].actions[$scope.args.action_id]($scope.args, {
                                                    activitySpinner: !hideSpinner,
                                                    timeout: timeout
                                                });
                                                promise.then(function (response) {
                                                    if (!$scope.syncScheduleNext) {
                                                        $.extend($scope.entity, response.data.entity);
                                                        var newArgs = $scope.rootScope.config.argumentLoader($scope);
                                                        $.extend(parentScope.args, angular.copy(newArgs));
                                                        $.extend($scope.args, angular.copy(newArgs));
                                                        $scope.formSetPristine();
                                                        /*
                                                        if ($scope.lastManageProduct) {
                                                            var image = $scope.lastManageProduct[0],
                                                                pricetag = $scope.lastManageProduct[1],
                                                                $event = $scope.lastManageProduct[2];
                                                            image = _.findWhere($scope.args._images, {
                                                                key: image.key
                                                            });
                                                            pricetag = _.findWhere(image.pricetags, {
                                                                key: pricetag.key
                                                            });
                                                            $scope.realManageProduct(image, pricetag, $event);
                                                            $scope.lastManageProduct = null;
                                                        }*/
                                                    }
                                                    if (!hideSnackbar) {
                                                        snackbar.showK('changesSaved');
                                                    }
                                                });
                                                promise['finally'](function () {
                                                    $scope.loadingSave = false;
                                                });
                                                return promise;
                                            };
                                            /*
                                            $scope.close = function () {
                                                if ($scope.container.form.$dirty) {
                                                    $scope.syncStop();
                                                    $scope.save();
                                                }
                                                return $scope.$close();
                                            };
                                            */
                                            $scope.close = angular.bind($scope, helpers.form.leave, function () {
                                                $scope.$close();
                                            });
                                            $scope.syncLoading = false;
                                            $scope.syncID = null;
                                            $scope.syncScheduleNext = false;
                                            $scope.syncStop = function () {
                                                clearTimeout($scope.syncID);
                                            };
                                            $scope.syncStart = function (hideSnackbar) {
                                                $scope.syncScheduleNext = true;
                                                $scope.syncStop();
                                                $scope.syncID = setTimeout(function () {
                                                    $scope.sync(false);
                                                }, 1000);
                                            };
                                            $scope.sync = function (hideSnackbar) {
                                                /*if ($scope.syncCancelDefer) {
                                                    $scope.syncCancelDefer.resolve();
                                                }
                                                $scope.save(true, $q.defer());
                                                return;*/
                                                if ($scope.syncLoading) {
                                                    $scope.syncScheduleNext = true;
                                                    return;
                                                }
                                                $scope.syncLoading = true;
                                                $scope.syncScheduleNext = false;
                                                $scope.save(hideSnackbar).then(function (response) {
                                                    $scope.syncLoading = false;
                                                    if ($scope.syncScheduleNext) {
                                                        $scope.sync(hideSnackbar);
                                                    }
                                                    return response;
                                                });
                                            };
                                        })
                                    });

                                },
                                layouts: {
                                    groups: [{
                                        label: false,
                                        fields: ['name', 'discontinue_date'],
                                    }, {
                                        label: GLOBAL_CONFIG.subheaders.catalogImages,
                                        fields: ['_images'],
                                        include: 'core/misc/action.html',
                                        action: function () {
                                            var scope = config.getScope();
                                            helpers.form.wakeUp(scope.container.form);
                                            if (!scope.container.form.$valid) {
                                                snackbar.showK('provideProperValues');
                                                return;
                                            }
                                            modals.fields.remote(config.getScope(), fields._images);
                                        }
                                    }, {
                                        label: GLOBAL_CONFIG.subheaders.catalogProducts,
                                        include: 'core/misc/action.html',
                                        fields: [],
                                        action: function () {
                                            var scope = config.getScope();

                                            if (!scope.entity.cover) {
                                                snackbar.showK('uploadImagesFirst');
                                                return;
                                            }
                                            config.getScope().addProducts();
                                        }
                                    }]
                                }
                            }
                        };

                    if (isNew) {
                        // get current seller
                        models['23'].current().then(function (response) {
                            modelsEditor.create(config).prepare({}, {
                                seller: response.data.entity.key
                            }, {
                                handleError: GLOBAL_CONFIG.backendErrorHandling.sellerProfileNotFound
                            });
                        });

                    } else {
                        modelsEditor.create(config).read(catalog, {
                            key: catalog.key
                        });
                    }

                }
            });

        });
    }));
}());