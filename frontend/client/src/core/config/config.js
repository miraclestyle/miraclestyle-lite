(function () {
    'use strict';

    angular.module('app').config(function (GLOBAL_CONFIG) {

        $.extend(GLOBAL_CONFIG.modals.confirmations, {
            discardWithFieldsRequired: {
                title: 'Discard changes?',
                message: 'There are some invalid changes on the form you are trying to leave. If you discard them, the changes will not be applied and will be lost permanently.',
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
            howToSort: {
                title: 'How to use this action',
                messages: ['Reorder the item by dragging it within its group.',
                    'Remove the item by dragging it outside the left edge of the screen.'
                ],
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
            '124-update': {
                condition_type: 'Condition under which this price applies.',
                price_type: 'Price formula that calculates the price.'
            },
            '111-update': {
                condition_type: 'Condition under which this price applies.',
                price_type: 'Price formula that calculates the price.'
            },
            '23-update': {
                name: 'Name of the brand, company or store that you own or represent.',
                logo: 'Click on the right side upload icon to upload logo image of the brand, company, or store that you own or represent.'
            }
        });

        $.extend(GLOBAL_CONFIG.fields.label, {
            search: {
                indexID: 'Search Options',
                ancestor: 'Ancestor',
                operator: 'Operator'
            },
            plugins: {
                kind: 'Rule'
            },
            '124-update': {
                condition_type: 'Condition',
                price_type: 'Price'
            },
            '111-update': {
                condition_type: 'Condition',
                price_type: 'Price'
            },
            '23-update': {
                logo: 'Seller Logo'
            },
            '18-update': {
                notify: 'E-mail me when a catalog is published or discontinued by the seller that I\'m following.'
            }
        });


        $.extend(GLOBAL_CONFIG.fields.emptyHelp, {
            '19-update': {
                addresses: ['Saved addresses are convenience that saves your time and energy during shopping cart checkout. Use saved addresses to populate addressing fields during shopping cart checkout, instead of doing so manually. Your saved addresses will appear in the order you have manually ordered them.',
                    'Click "Add" action to add new address.',
                    'Click on an address to edit address.',
                    'Use drag handle to reorder an address by dragging it within its group.',
                    'Use drag handle to remove an address by dragging it outside the left edge of the screen.'
                ]
            }
        });

        if (!GLOBAL_CONFIG.fields.radioLabel) {
            GLOBAL_CONFIG.fields.radioLabel = {};
        }

        $.extend(GLOBAL_CONFIG.fields.radioLabel, {
            pluginLocation: {
                trueLabel: 'Applies to all locations except to those listed in the Locations section.',
                falseLabel: 'Applies only to the locations listed in the Locations section.'
            }
        });

        $.extend(GLOBAL_CONFIG.subheaders, {
            loginMethods: 'Login Methods',
            productInstances: 'Product Instances',
            catalogImages: 'Images',
            catalogProducts: 'Products',
            collectionSeller: 'Sellers',
            history: 'History',
            sellerContents: 'Contents',
            sellerPlugins: 'Rules'
        });

        $.extend(GLOBAL_CONFIG.emptyHelp, {
            orderBuyerList: ['No recorded orders m8'],
            orderSellerList: ['No recorded orders m8'],
            cartBuyerList: ['No recorded orders m8'],
            cartSellerList: ['No recorded orders m8'],
            catalogList: ['Product catalogs are integral part of Miraclestyle platform. Product catalog is a collection of images that represent products or services to sell. Each image can have multiple price tags attached. Each price tag is custom positioned on the image it is attached to and links to a product or service details. Product or service details contain information detailing the characteristics of the product or service to be sold. Product is integrated with the shopping cart system to allow direct online purchases. Product catalog can be shared and embedded to third party web sites, similar to you tube video for example. Created catalog initially assumes draft state and is not visible to the general public. While in draft state catalog can be edited. Published catalog is accessible to the general public until it expires or is discontinued. With exception of a product "Availability" field, published catalog cannot be edited. However, published catalog can be duplicated and duplicate will initially be in draft state ready for editing. Discontinued catalog is not accessible to the general public, and will eventually be entirely removed from the Miraclestyle. However, products of discontinued catalog will remain accessible for the next 180 days to those who have purchased them. Discontinued catalog cannot be edited or duplicated.',
                'Click "Create" action to create new catalog.',
                'Click on a catalog image to edit catalog.',
                'Click on a catalog view icon, located in the lower right corner of a catalog image, to view catalog as it would appear to the general public.'
            ]
        });

        $.extend(GLOBAL_CONFIG.snackbar.messages, {
            changesSaved: 'Changes saved.'
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
            editVariants: 'Edit Variant',
            home: 'Home',
            buyer: 'Buyer',
            carts: 'Carts',
            orders: 'Orders',
            catalogs: 'Catalogs',
        });
    });
}());
