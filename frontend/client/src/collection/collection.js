(function () {
    'use strict';
    angular.module('app').run(ng(function (modelsConfig, endpoint, $state, modals, currentAccount, modelsMeta, GLOBAL_CONFIG, modelsEditor, helpers, $timeout, snackbar) {
        modelsConfig(function (models) {
            var read_arguments = {
                _sellers: {
                    _content: {},
                    _feedback: {}
                }
            };

            $.extend(models['18'], {
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
                manageModal: function (accountKey, modalConfig) {
                    if (!modalConfig) {
                        modalConfig = {};
                    }
                    var fields = modelsMeta.getActionArguments(this.kind, 'update'),
                        config;
                    config = {
                        kind: this.kind,
                        action: 'update',
                        fields: _.toArray(fields),
                        toolbar: {
                            hideSave: true,
                            titleEdit: 'buyer.edit18'
                        },
                        modalConfig: modalConfig,
                        templateBodyUrl: 'collection/manage_body.html',
                        excludeFields: ['account', 'read_arguments'],
                        init: function ($scope) {
                            $scope.$watch('args.notify', function (neww, old) {
                                if (neww !== old) {
                                    $scope.save().then(function () {
                                        snackbar.showK('changesSaved');
                                        $scope.entity._sellers.iremove(function (seller) {
                                            return $.inArray(seller.key, $scope.entity.sellers) === -1;
                                        });
                                        models['18'].current().then(function (response) {
                                            $.extend(response.data.entity, $scope.entity);
                                        });
                                    });
                                }
                            });

                            $scope.collectionDrag = {
                                options: {
                                    disabled: false,
                                    handle: '.sort-handle',
                                    distance: 10,
                                    stop: function (e, ui) {
                                        $scope.$apply();
                                    }
                                },
                                whatSortMeans: function () {
                                    modals.alert('howToDeleteDragging');
                                },
                                onStart: function (e, ui, seller) {
                                    $(ui.helper).find('.sort-handle').addClass('dragged');
                                },
                                onDrag: function (e, ui, seller) {
                                    var deleteMode,
                                        division,
                                        helperWidth = ui.helper.width();
                                    division = ui.offset.left + helperWidth;
                                    if (division < (helperWidth / 2)) {
                                        deleteMode = true;
                                    }
                                    if (seller) {
                                        if (deleteMode) {
                                            ui.helper.addClass('about-to-delete');
                                        } else {
                                            ui.helper.removeClass('about-to-delete');
                                        }
                                    }
                                },
                                onStop: function (e, ui, seller) {
                                    if (ui.helper.hasClass('about-to-delete')) {
                                        ui.helper.animate({
                                            left: (ui.helper.width() * 2) * -1
                                        }, function () {
                                            $timeout(function () {
                                                $scope.remove(seller);
                                            });
                                        });
                                    } else {
                                        ui.helper.animate(ui.originalPosition, function () {
                                            ui.helper.attr('style', '');
                                        });
                                    }
                                }
                            };
                        },
                        scope: {
                            remove: function (seller) {
                                var scope = this,
                                    sellers;
                                scope.args.sellers.remove(seller.key);
                                scope.entity._sellers.remove(seller);
                                sellers = scope.entity._sellers.concat();
                                scope.save().then(function () {
                                    snackbar.showK('changesSaved');
                                    scope.entity._sellers = sellers;
                                    models['23'].decrementGlobalSellerStack(seller.key, scope.args.notify);
                                    models['18'].current().then(function (response) {
                                        var collection = response.data.entity;
                                        collection.sellers.remove(seller.key);
                                        return collection;
                                    });
                                });
                            },
                            view: function (seller, $event) {
                                models['23'].viewProfileModal(seller.parent.key, {
                                    popFrom: helpers.clicks.realEventTarget($event.target),
                                    inDirection: false,
                                    sellerDetails: {
                                        removedOrAdded: function (updatedCollection, inCollection) {
                                            if (!inCollection) {
                                                seller._state = 'deleted';
                                            } else {
                                                seller._state = null;
                                            }
                                        }
                                    },
                                    outDirection: false
                                });
                            },
                            layouts: {
                                groups: [{
                                    label: false
                                }, {
                                    label: GLOBAL_CONFIG.subheaders.collectionSeller
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