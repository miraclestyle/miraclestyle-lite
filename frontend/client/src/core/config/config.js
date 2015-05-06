(function () {
    'use strict';

    angular.module('app').config(function (GLOBAL_CONFIG) {

        $.extend(GLOBAL_CONFIG.modals.confirmations, {
            discardWithFieldsRequired: {
                title: 'Discard unsaved changes?',
                message: 'There are some unsaved changes on the form you are trying to close. If you discard them, the item you are trying to add will not be added.',
                text: {
                    primary: 'Discard'
                }
            },
            disconnectSignInMethod: {
                title: 'Disconnect this method?',
                message: 'If this is the only sign in method connected to your Miraclestyle account, you will permanently lose access to the account and all of it\'s data once this action is completed!',
                text: {
                    primary: 'Disconnect'
                }
            },
            connectSignInMethod: {
                title: 'Connect this method?',
                message: 'If this sign in method is already connected to another Miraclestyle account you will have to disconnect it before you proceed with this acction!',
                text: {
                    primary: 'Connect'
                }
            },
            discard: {
                title: 'Discard unsaved changes?',
                message: 'There are some unsaved changes on the form you are trying to close. If you discard them, the changes will be lost permanently, and the form will revert to previously saved state.',
                text: {
                    primary: 'Discard'
                }
            },
            maybeLogout: {
                title: 'Confirm Logout',
                message: 'Are you sure you want to logout?',
                text: {
                    primary: 'Logout'
                },
            }
        });

        $.extend(GLOBAL_CONFIG.modals.alerts, {
            forbidden: {
                title: 'Action Denied',
                message: 'Action you tried to perform is forbidden for this account.'
            },
            noBuyer: {
                title: 'Buyer address required',
                message: 'You did not provide any buyer information.'
            },
            noImagesInCatalog: {
                title: 'Upload Images',
                message: 'Catalog has no images, add some in order to administer products.'
            },
            howToSort: {
                title: 'How to use this action',
                messages: ['Reorder the item by dragging it within its group.',
                           'Remove the item by dragging it outside the left edge of the screen.'],
                text: {
                    primary: 'Got it'
                }
            },
            howToDeleteLine: {
                title: 'How to use this action',
                message: 'Remove the item by dragging it outside the left edge of the screen.',
                text: {
                    primary: 'Got it'
                }
            }
        });


        $.extend(GLOBAL_CONFIG.labels, {
            order: {
                checkout: 'Checkout',
                completed: 'Completed',
                cart: 'Cart',
                sudo: 'Administered',
                review: 'Review',
                reported: 'Reported',
                positive: 'Positive',
                negative: 'Negative',
                neutral: 'Neutral'
            }
        });

        $.extend(GLOBAL_CONFIG.fields.help, {
            '23-update': {
                name: 'Name of the brand, company or store that you own or represent.',
                logo: 'Click on the right side upload icon to upload logo image of the brand, company, or store that you own or represent.'
            }
        });

        $.extend(GLOBAL_CONFIG.fields.label, {
            '23-update': {
                logo: 'Seller Logo'
            }
        });

        $.extend(GLOBAL_CONFIG.toolbar.titles, {
            seller: 'Seller',
            edit31: 'Edit Catalog',
            add31: 'Create Catalog',
            viewImages: 'Images',
            viewProducts: 'Products',
            editProduct: 'Edit Product',
            addProduct: 'Add Product',
            editPluginGroup: false,
            settings: 'Settings',
            addPlugins: 'Add Rule',
            editPlugins: 'Edit Rule',
            addVariants: 'Add Variant',
            editVariants: 'Edit Variant'
        });


    });
}());