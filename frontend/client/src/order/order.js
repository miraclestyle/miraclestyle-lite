(function () {
    'use strict';
    angular.module('app').directive('sendMessage', function ($parse) {
        return {
            restrict: 'A',
            link: function (scope, element, attrs) {
                var callback = $parse(attrs.sendMessage),
                    root = element.parents('.modal-dialog:first'),
                    textarea,
                    pane,
                    click = function (e) {
                        textarea = root.find('textarea');
                        pane = root.find('.overflow-y');
                        if (textarea.length && textarea.val()) {
                            callback(scope);
                        } else {
                            pane.stop().scrollTo(textarea, 100, function () {
                                textarea.focus();
                            });
                        }
                        e.preventDefault();
                    };

                element.on('click', click);

                scope.$on('$destroy', function () {
                    element.off('click', click);
                });

            }
        };
    }).directive('alwaysScrollToBottom', function ($timeout) {
        return {
            link: function (scope, element, attrs) {
                var cb = function () {
                    element.scrollTop(element[0].scrollHeight);
                };

                scope.$watchGroup(scope.$eval(attrs.alwaysScrollToBottom), function (neww, old) {
                    if (neww !== old) {
                        cb();
                    }
                });
            }
        };
    }).filter('displayTaxes', function () {
        return function (value) {
            var formatted = '';
            if (value) {
                formatted = $.map(value, function (item) {
                    return item.name;
                }).join(', ');
            }
            return formatted;
        };
    }).run(function (modelsMeta, modelsConfig, $modal, modals, helpers, endpoint, $q, $filter, currentAccount, $mdSidenav, $timeout) {
        modelsConfig(function (models) {
            $.extend(models['34'], {
                current: function (sellerKey) {
                    var that = this;
                    return models['19'].current().then(function (response) {
                        var buyer = response.data.entity;
                        return that.actions.view_order({
                            buyer: buyer.key,
                            seller: sellerKey
                        }, {
                            cache: that.getCacheKey('current' + sellerKey),
                            cacheType: 'memory'
                        });
                    });
                },
                adminManageModal: function (order) {
                    return this.manageModal(order, order._seller, undefined, {
                        sellerMode: true
                    });
                },
                manageModal: function (order, seller, buyer, config) {
                    config = helpers.alwaysObject(config);
                    var args, that = this,
                        cartMode = config.cartMode,
                        sellerMode = config.sellerMode,
                        rpc = {};
                    if (!cartMode) {
                        args = {
                            key: order.key,
                            read_arguments: {
                                _lines: {
                                    config: {
                                        limit: 0
                                    }
                                },
                                _seller: {
                                    _feedback: {},
                                    _content: {}
                                },
                                _messages: {
                                    _agent: {}
                                }
                            }
                        };
                    } else {
                        args = {
                            buyer: buyer.key,
                            seller: seller.key,
                            read_arguments: {
                                _seller: {
                                    _feedback: {},
                                    _content: {}
                                },
                                _messages: {
                                    _agent: {}
                                }
                            }
                        };
                    }

                    models['34'].actions[cartMode ? 'view_order' : 'read'](args, rpc).then(function (response) {

                        if (!response.data.entity.id) {
                            modals.alert('cartNotFound');
                            return;
                        }

                        $modal.open({
                            templateUrl: 'order/view.html',
                            popFrom: config.popFrom,
                            controller: function ($scope) {
                                var locals = {
                                    customPlaceholder: null,
                                    updateLiveEntity: function (response) {
                                        var messages = $scope.order._messages;
                                        $.extend($scope.order, response.data.entity);
                                        $scope.order._messages = messages;
                                    },
                                    reactOnStateChange: function (response) {
                                        helpers.update($scope.order, response.data.entity, ['state', 'feedback_adjustment', 'feedback', 'ui']);
                                        locals.reactOnUpdate();
                                    },
                                    reactOnUpdate: function () {
                                        if (order) {
                                            $.extend(order, $scope.order);
                                        }
                                        if (that.getCache('current' + seller.key)) {
                                            that.current(seller.key).then(function (response) {
                                                $.extend(response.data.entity, $scope.order);
                                            });
                                        }
                                    },
                                    logMessageAction: modelsMeta.getActionArguments('34', 'log_message'),
                                    orderUpdateFields: modelsMeta.getActionArguments('34', 'update'),
                                    billingAddressFields: [],
                                    shippingAddressFields: [],
                                    sorter: function (field, prev) {
                                        var indx = models['19'].manageModalFieldsOrder.indexOf(field.code_name),
                                            b = models['19'].manageModalFieldsOrder.indexOf(prev.code_name);
                                        if (indx === -1) {
                                            indx = 99999;
                                        }
                                        return indx - b;
                                    }
                                };

                                angular.forEach(locals.orderUpdateFields.shipping_address.modelclass, function (value) {
                                    $.extend(value.ui, {
                                        args: 'addresses.shipping.' + value.code_name,
                                        parentArgs: 'addresses.shipping',
                                        writable: true
                                    });
                                    locals.shippingAddressFields.push(value);
                                });

                                angular.forEach(locals.orderUpdateFields.billing_address.modelclass, function (value) {
                                    $.extend(value.ui, {
                                        args: 'addresses.billing.' + value.code_name,
                                        parentArgs: 'addresses.billing',
                                        writable: true
                                    });
                                    locals.billingAddressFields.push(value);
                                });

                                locals.billingAddressFields.sort(locals.sorter);
                                locals.shippingAddressFields.sort(locals.sorter);

                                $.extend(locals.logMessageAction.message.ui, {
                                    label: false,
                                    args: 'messages.draft.message',
                                    parentArgs: 'messages.draft',
                                    writable: true,
                                    placeholder: 'Type message here.',
                                    attrs: {
                                        'native-placeholder': '',
                                        'class': 'primary'
                                    }
                                });

                                $scope.dialog = {
                                    toolbar: {
                                        templateRight: 'order/toolbar_actions.html'
                                    }
                                };

                                $scope.$watch('order.state', function (neww, old) {
                                    var title = 'Cart';
                                    if (neww === 'completed') {
                                        title = 'Order';
                                    }
                                    $scope.dialog.toolbar.title = title;
                                });

                                $scope.stage = {
                                    checkout: null,
                                    current: 1,
                                    out: [],
                                    canShowPay: function () {
                                        return $scope.order.state === 'checkout';
                                    },
                                    isOut: function (indx) {
                                        return $.inArray(indx, $scope.stage.out) !== -1;
                                    },
                                    toCheckout: function () {
                                        $scope.stage.out.push(1);
                                        $scope.stage.current = 2;
                                    },
                                    toDeliveryMethod: function () {
                                        var valid = $scope.addresses.form.billing.$valid,
                                            addressing = {
                                                billing_address: $scope.addresses.billing
                                            };
                                        if (!$scope.addresses.sameAsBilling) {
                                            valid = $scope.addresses.form.shipping.$valid;
                                            addressing.shipping_address = $scope.addresses.shipping;
                                        } else {
                                            addressing.shipping_address = $scope.addresses.billing;
                                        }
                                        if (valid) {
                                            $scope.cmd.order.update(addressing).then(function () {
                                                $scope.stage.out.push(2);
                                                $scope.stage.current = 3;
                                            });
                                        } else {
                                            helpers.form.wakeUp($scope.addresses.form.billing);
                                            helpers.form.wakeUp($scope.addresses.form.shipping);
                                        }
                                    },
                                    toReviewOrder: function () {
                                        modals.confirm('toCheckout', function () {
                                            if ($scope.carrier.form.$valid) {
                                                // state = 'checkout' is needed here
                                                $scope.cmd.order.update({
                                                    carrier: $scope.carrier.selected,
                                                    state: 'checkout'
                                                }).then(function () {
                                                    $scope.stage.out.push(3);
                                                    $scope.stage.current = 4;
                                                });
                                            } else {
                                                helpers.form.wakeUp($scope.carrier.form);
                                            }
                                        });
                                    },
                                    complete: function () {
                                        $scope.stage.out = [];
                                        $scope.stage.current = 1;
                                    }
                                };
                                $scope.cmd = {};
                                $scope.container = {};
                                $scope.cartMode = cartMode;
                                $scope.sellerMode = sellerMode;
                                $scope.order = response.data.entity;
                                $scope.seller = seller;
                                $scope.currentAccount = currentAccount;
                                $scope.addresses = {
                                    sameAsBilling: true,
                                    form: {},
                                    shipping: {},
                                    billing: {},
                                    browse: function (type) {
                                        var parentScope = $scope;
                                        models['19'].current().then(function (response) {
                                            $modal.open({
                                                backdrop: true,
                                                fullScreen: false,
                                                templateUrl: 'order/browse_addresses.html',
                                                controller: function ($scope) {
                                                    $scope.addresses = response.data.entity.addresses;
                                                    $scope.select = function (ent) {
                                                        angular.forEach(ent, function (value, key) {
                                                            parentScope.addresses[type][key] = value;
                                                        });
                                                        $scope.$close();
                                                    };
                                                    $scope.manage = function () {
                                                        models['19'].manageModal(response.data.entity.parent.key, function () {
                                                            models['19'].current().then(function (response) {
                                                                $scope.addresses = response.data.entity.addresses;
                                                            });
                                                        });
                                                    };
                                                }
                                            });
                                        });
                                    },
                                    fields: {
                                        shipping: locals.shippingAddressFields,
                                        billing: locals.billingAddressFields,
                                        sameAsBilling: {
                                            type: 'SuperBooleanProperty',
                                            code_name: 'sameAsBilling',
                                            ui: {
                                                writable: true,
                                                parentArgs: 'addresses',
                                                args: 'addresses.sameAsBilling',
                                                specifics: {
                                                    type: 'checkbox'
                                                }
                                            }
                                        }
                                    }
                                };

                                $scope.payment = {
                                    method: $scope.order.payment_method
                                };

                                $scope.carrier = {
                                    selected: $scope.order.carrier ? $scope.order.carrier.reference : null,
                                    available: (response.data.carriers ? response.data.carriers : []),
                                    form: null
                                };

                                $scope.format = {
                                    variantLabel: function (variant) {
                                        return Object.keys(variant)[0];
                                    },
                                    variantValue: function (variant) {
                                        return variant[$scope.format.variantLabel(variant)];
                                    }
                                };

                                $scope.messages = {
                                    reader: models['34'].reader({
                                        kind: '34',
                                        key: $scope.order.key,
                                        next: {
                                            _messages: angular.copy($scope.order._next_read_arguments._messages)
                                        },
                                        access: ['_messages'],
                                        complete: function (items) {
                                            $scope.order._messages.prepend(items);
                                        }
                                    }),
                                    toggling: false,
                                    open: false,
                                    draft: {
                                        message: null,
                                        key: $scope.order.key
                                    },
                                    field: locals.logMessageAction.message,
                                    nav: function () {
                                        return $mdSidenav('right_messages');
                                    },
                                    sent: false,
                                    send: function (action) {
                                        models['34'].actions[action]($scope.messages.draft).then(function (response) {
                                            $scope.messages.draft.message = '';
                                            $scope.messages.sent = !$scope.messages.sent;
                                            $scope.order._messages.push(response.data.entity._messages[0]);
                                            locals.reactOnStateChange(response);
                                        });
                                    },
                                    logMessage: function () {
                                        return this.send('log_message');
                                    },
                                    close: function () {
                                        return $scope.message.toggle(true);
                                    },
                                    toggle: function (close) {
                                        if ($scope.messages.toggling) {
                                            return;
                                        }
                                        var it = $scope.messages.nav(),
                                            isOpen = it.isOpen();
                                        $scope.messages.toggling = true;
                                        if (close === true) {
                                            isOpen = true;
                                        }
                                        $timeout(function () {
                                            it[isOpen ? 'close' : 'open']().then(function () {
                                                $scope.messages.toggling = false;
                                                $scope.messages.open = !isOpen;
                                            });
                                        });
                                    },
                                };

                                $scope.feedback = {
                                    canShowButton: function () {
                                        var maybe = false;
                                        angular.forEach(['leave_feedback', 'review_feedback', 'sudo_feedback'], function (k) {
                                            if (!maybe) {
                                                maybe = $scope.order.ui.rule.action[k].executable;
                                            }
                                        });
                                        return maybe;
                                    },
                                    showAction: function () {
                                        var parentScope = $scope,
                                            leaveFeedbackArgs = modelsMeta.getActionArguments('34', 'leave_feedback');
                                        $.extend(leaveFeedbackArgs.message.ui, {
                                            writable: true,
                                            parentArgs: 'feedback',
                                            args: 'feedback.message',
                                            label: false,
                                            placeholder: 'Please, write comment here. Comments appear in the messages feed.',
                                            attrs: {
                                                'native-placeholder': '',
                                                'class': 'full-width'
                                            }
                                        });
                                        if ($scope.order.ui.rule.action.leave_feedback.executable || $scope.order.ui.rule.action.sudo_feedback.executable) {
                                            $modal.open({
                                                fullScreen: false,
                                                inDirection: false,
                                                outDirection: false,
                                                templateUrl: 'order/leave_feedback.html',
                                                controller: function ($scope) {
                                                    $scope.config = {};
                                                    $scope.feedback = {
                                                        form: null,
                                                        messageField: leaveFeedbackArgs.message,
                                                        message: '',
                                                        choice: 'neutral',
                                                        choices: [{
                                                            key: 'positive'
                                                        }, {
                                                            key: 'negative'
                                                        }, {
                                                            key: 'neutral'
                                                        }]
                                                    };
                                                    $scope.config.dismiss = function () {
                                                        return $scope.$close();
                                                    };

                                                    $scope.config.text = {
                                                        primary: 'Leave Feedback'
                                                    };

                                                    $scope.config.confirm = function () {
                                                        if ($scope.feedback.form.$valid) {
                                                            models['34'].actions[parentScope.order.ui.rule.action.leave_feedback.executable ? 'leave_feedback' : 'sudo_feedback']({
                                                                key: parentScope.order.key,
                                                                message: $scope.feedback.message,
                                                                feedback: $scope.feedback.choice
                                                            }).then(function (response) {
                                                                parentScope.order._messages.push(response.data.entity._messages[0]);
                                                                locals.reactOnStateChange(response);
                                                                $scope.config.dismiss();
                                                            });
                                                        } else {
                                                            helpers.form.wakeUp($scope.feedback.form);
                                                        }
                                                    };
                                                }
                                            });
                                        } else {
                                            $modal.open({
                                                fullScreen: false,
                                                inDirection: false,
                                                outDirection: false,
                                                templateUrl: 'order/seller_feedback.html',
                                                controller: function ($scope) {
                                                    $scope.config = {};
                                                    $scope.feedback = {
                                                        form: null,
                                                        messageField: leaveFeedbackArgs.message,
                                                        message: '',
                                                        choice: 'review_feedback',
                                                        choices: [{
                                                            key: 'review_feedback',
                                                            name: 'Review Feedback',
                                                            help: 'Ask Buyer to review feedback.'
                                                        }, {
                                                            key: 'report_feedback',
                                                            name: 'Report Feedback',
                                                            help: 'Ask Admin to intervene.'
                                                        }]
                                                    };
                                                    $scope.config.dismiss = function () {
                                                        return $scope.$close();
                                                    };

                                                    $scope.config.text = {
                                                        primary: 'Leave Feedback'
                                                    };

                                                    $scope.order = parentScope.order;

                                                    $scope.config.confirm = function () {
                                                        if ($scope.feedback.form.$valid) {
                                                            models['34'].actions[$scope.feedback.choice]({
                                                                key: parentScope.order.key,
                                                                message: $scope.feedback.message
                                                            }).then(function (response) {
                                                                parentScope.order._messages.push(response.data.entity._messages[0]);
                                                                locals.reactOnStateChange(response);
                                                                $scope.config.dismiss();
                                                            });
                                                        } else {
                                                            helpers.form.wakeUp($scope.feedback.form);
                                                        }
                                                    };
                                                }
                                            });
                                        }
                                    }
                                };

                                $scope.cmd.order = {
                                    update: function (extra) {
                                        var data = {
                                            key: $scope.order.key,
                                            payment_method: $scope.payment.method,
                                            _lines: $scope.order._lines
                                        };
                                        $.extend(data, extra);
                                        return models['34'].actions.update(data).then(function (response) {
                                            locals.updateLiveEntity(response);
                                            locals.reactOnUpdate();
                                            $scope.carrier.available = response.data.carriers;
                                            $scope.carrier.selected = response.data.entity.carrier ? response.data.entity.carrier.reference : null;
                                        });
                                    },
                                    cancel: function () {
                                        if ($scope.order.state === 'checkout') {
                                            modals.confirm('cancelOrder', function () {
                                                models['34'].actions.cancel({
                                                    key: $scope.order.key
                                                }).then(function (response) {
                                                    models['34'].removeCache('current' + seller.key);
                                                    $scope.close();
                                                });
                                            });
                                        }
                                    }
                                };

                                $scope.cmd.line = {
                                    view: function (line) {
                                        var path = line.product._reference;
                                        models['31'].viewProductModal(path.parent.parent.parent.key,
                                            path.parent.parent.key, path.pricetag.key,
                                            line.product.variant_signature, {
                                                events: {
                                                    addToCart: locals.updateLiveEntity
                                                }
                                            });
                                    },
                                    remove: function (line) {
                                        line.quantity = 0;
                                        line._state = 'deleted';
                                    }
                                };

                                $scope.cmd.seller = {
                                    view: function () {
                                        models['23'].viewModal($scope.seller);
                                    }
                                };

                                $scope.close = function () {
                                    $scope.$close();
                                };

                                $scope.lineDrag = {
                                    options: {
                                        disabled: false,
                                        axis: 'x',
                                        handle: '.sort-handle',
                                        distance: 8,
                                        stop: function (e, ui) {
                                            $scope.$apply();
                                        }
                                    },
                                    whatSortMeans: function () {
                                        modals.alert('howToDeleteLine');
                                    },
                                    onDrag: function (e, ui, line) {
                                        var deleteMode,
                                            division,
                                            helperWidth = ui.helper.width();
                                        division = ui.offset.left + helperWidth;
                                        if (division < (helperWidth / 2)) {
                                            deleteMode = true;
                                        }
                                        if (line) {
                                            if (deleteMode) {
                                                ui.helper.addClass('about-to-delete');
                                            } else {
                                                ui.helper.removeClass('about-to-delete');
                                            }
                                        }
                                    },
                                    onStop: function (e, ui, line) {
                                        if (ui.helper.hasClass('about-to-delete')) {
                                            ui.helper.animate({
                                                left: (ui.helper.width() * 2) * -1
                                            }, function () {
                                                $scope.cmd.line.remove(line);
                                                $scope.cmd.order.update();
                                            });
                                        } else {
                                            ui.helper.animate(ui.originalPosition, function () {
                                                ui.helper.attr('style', '');
                                            });
                                        }
                                    }
                                };

                                if ($scope.order.state === 'checkout' || $scope.order.state === 'completed') {
                                    $scope.stage.out.extend([1, 2, 3]);
                                    $scope.stage.current = 4;
                                    $scope.stage.checkout = 1;
                                }

                                $scope.notifyUrl = helpers.url.abs('api/order/complete/paypal');
                                $scope.completePath = helpers.url.abs('payment/completed/' + $scope.order.key);
                                $scope.cancelPath = helpers.url.abs('payment/canceled/' + $scope.order.key);

                            }
                        });


                    });

                }
            });

        });


    });
}());
