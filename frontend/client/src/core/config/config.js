(function () {
    'use strict';

    angular.module('app').config(ng(function (GLOBAL_CONFIG) {
        var locals = {};

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
            },
            cancelOrder: {
                title: 'Reset shopping cart?',
                message: 'This cart will be emptied and all of its settings will be lost after completing this action.',
                text: {
                    primary: 'Reset'
                }
            },
            toCheckout: {
                title: 'Review shopping cart?',
                message: 'You won\'t be able to update this cart while reviewing it. However, you will be able to reset the cart, or place an order by making a payment.',
                text: {
                    primary: 'Review'
                }
            },
            publishCatalog: {
                title: 'Publish catalog?',
                message: 'Published catalog is accessible to the general public until it expires or is discontinued. With exception of a product "Availability" field, published catalog cannot be edited. However, published catalog can be duplicated and duplicate will initially be in draft state ready for editing. You will be notified once this action is completed.',
                text: {
                    primary: 'Publish'
                }
            },
            discontinueCatalog: {
                title: 'Discontinue catalog?',
                message: 'Discontinued catalog is not accessible to the general public, and will eventually be entirely removed from the Miraclestyle. However, products of discontinued catalog will remain accessible for the next 180 days to those who have purchased them. Discontinued catalog cannot be edited or duplicated. You will be notified once this action is completed.',
                text: {
                    primary: 'Discontinue'
                }
            },
            duplicateCatalog: {
                title: 'Schedule duplication?',
                message: 'Duplication can take a while to complete! You will be notified once this action is completed.',
                text: {
                    primary: 'Schedule'
                }
            },
            sellerProfileNotFound: {
                title: 'No seller information provided',
                message: 'You must configure your seller profile in order to do this.',
                text: {
                    primary: 'Configure'
                }
            }
        });

        locals.gotit = {
            primary: 'Got it'
        };

        $.extend(GLOBAL_CONFIG.modals.alerts, {
            forbidden: {
                title: 'Action Denied',
                message: 'Action you tried to perform is forbidden for this account.',
                text: locals.gotit
            },
            noBuyer: {
                title: 'Buyer address required',
                message: 'You did not provide any buyer information.',
                text: locals.gotit
            },
            howToSort: {
                title: 'How to use this action',
                messages: ['Reorder the item by dragging it within its group.',
                    'Remove the item by dragging it outside the left edge of the screen.'],
                text: locals.gotit
            },
            howToDeleteLine: {
                title: 'How to use this action',
                message: 'Remove the item by dragging it outside the left edge of the screen.',
                text: locals.gotit
            },
            howToDropPricetag: {
                title: 'How to use this action',
                messages: ['Add new product to the catalog by dragging the "Add" tag to a catalog image. While dragging, it is preferable to aim the tag dot for the image area that shows the product that the tag will link to. Add one tag per product per catalog.',
                    'Reposition a tag by dragging it within images area.',
                    'Click a tag to open the "Edit Product" form while editing the catalog.',
                    'Click a tag to open the product view while viewing the catalog.'
                ],
                text: locals.gotit
            }
        });


        $.extend(GLOBAL_CONFIG.labels, {
            order: {
                checkout: 'Checkout',
                completed: 'Completed',
                cart: 'Cart',
                canceled: 'Canceled',
                sudo: 'Administered',
                review: 'Review',
                reported: 'Reported',
                positive: 'Positive',
                negative: 'Negative',
                neutral: 'Neutral',
                revision: 'Review'
            }
        });

        $.extend(GLOBAL_CONFIG.fields.help, {
            '124-update': {
                condition_type: 'Condition under which this price applies.',
                price_type: 'Price formula that calculates the price.'
            },
            '106': {
                postal_codes: 'Range of postal codes this location affects. Specify one postal code per line.'
            },
            '108': {
                reciever_email: 'Primary email address of your PayPal account.',
                business: 'Email address on which you want to receive your PayPal payments. This value will be the same as "Receiver Email" in case that you have only one email address associated with your PayPal account.'
            },
            '109': {
                carriers: 'Carriers, if any, to which this rule applies.',
                product_categories: 'Product categories to which this rule applies.',
                product_codes: 'Specific product codes to which this rule applies. Specify one product code per line.',
                address_type: 'Buyer address type this rule applies to.'
            },
            '124': {
                product_categories: 'Product categories to which this rule applies.',
                product_codes: 'Specific product codes to which this rule applies. Specify one product code per line.'
            },
            '117': {
                currency: 'Currency you accept, and your product prices are expressed in.'
            },
            '111-update': {
                condition_type: 'Condition under which this price applies.',
                price_type: 'Price formula that calculates the price.'
            },
            '23-update': {
                name: 'Name of the brand, company, or store that you own or represent.',
                logo: 'Click on the logo above to upload logo image of the brand, company, or store that you own or represent. Logo must be of 2.4:1 aspect ratio, preferably 2400 pixels wide and 1000 pixels high.'
            },
            '14': {
                name: 'Recipient\'s full name, or business name.'
            },
            '107': {
                address_type: 'Buyer address type this rule applies to.'
            },
            '31-update': {
                discontinue_date: 'Date when this catalog will be automatically discontinued and become unavailable to the general public.'
            },
            '26': {
                name: 'Name of the variant input control that will be visible on the product view.',
                options: 'Options that will be available for selection on the variant input control. Specify one option per line.',
                description: 'Brief description visible beneath the variant input control.',
                allow_custom_value: 'If enabled, options defined above will be ignored, and buyers will be able to supply custom value in variant input control.'
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
            '28': {
                uom: 'Unit Of Measurement',
                weight_uom: 'Weight Unit Of Measurement',
                volume_uom: 'Volume Unit Of Measurement',
            },
            '27': {
                uom: 'Unit Of Measurement',
                weight_uom: 'Weight Unit Of Measurement',
                volume_uom: 'Volume Unit Of Measurement',
            },
            '112': {
                rules: 'Prices'
            },
            '124': {
                discount_value: 'Discount (%)'
            },
            '31-update': {
                discontinue_date: 'Expiration Date'
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

        locals.conditionOperatorSpec = {
            '<=': 'is less than or equals to',
            '>=': 'is greater than or equals to',
            '==': 'equals to',
            '<': 'less than',
            '>': 'greater than'
        };
        locals.addressTypeSpec = {
            shipping: 'Shipping',
            billing: 'Billing'
        };
        $.extend(GLOBAL_CONFIG.fields.translateChoices, {
            '107': {
                address_type: locals.addressTypeSpec
            },
            '109': {
                address_type: locals.addressTypeSpec,
                type: {
                    percent: 'Proportional (%)',
                    fixed: 'Fixed (Amount)'
                }
            },
            '111': {
                condition_operator: locals.conditionOperatorSpec,
                price_operator: {
                    weight: 'weight multiplied by',
                    quantity: 'quantity multiplied by',
                    'weight*volume': 'weight multiplied by volume multiplied by',
                    volume: 'volume multiplied by',
                    price: 'price multiplied by'
                },
            },
            '124': {
                condition_operator: locals.conditionOperatorSpec
            },
            rules: {
                kind: {
                    '109': 'Tax',
                    '126': 'Discount',
                    '107': 'Address',
                    '117': 'Currency',
                    '108': 'PayPal',
                    '113': 'Carrier'
                }
            }
        });


        $.extend(GLOBAL_CONFIG.fields.emptyHelp, {
            '19-update': {
                addresses: 'buyer/help/addresses.html'
            },
            '31-update': {
                _images: 'catalog/help/images.html'
            },
            '28': {
                images: 'catalog/product/help/images.html',
                contents: 'catalog/product/help/contents.html',
                variants: 'catalog/product/help/variants.html',
                _instances: 'catalog/product/help/instances.html'
            },
            '27': {
                images: 'catalog/product/help/images.html',
                contents: 'catalog/product/help/contents.html'
            },
            '21': {
                documents: 'seller/help/contents.html'
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
            productInstances: 'Variant Configurations',
            catalogImages: 'Images',
            catalogProducts: 'Products',
            collectionSeller: 'Sellers',
            history: 'History',
            sellerContents: 'Contents',
            sellerPlugins: 'Rules'
        });

        $.extend(GLOBAL_CONFIG.emptyHelp, {
            orderSellerList: 'seller/help/orders.html',
            cartSellerList: 'seller/help/carts.html',
            orderBuyerList: 'buyer/help/orders.html',
            cartBuyerList: 'buyer/help/carts.html',
            catalogList: 'catalog/help/list.html',
            cart: 'order/help/empty.html',
            following: 'collection/help/sellers.html'
        });

        $.extend(GLOBAL_CONFIG.snackbar.messages, {
            changesSaved: 'Changes saved.',
            cartUpdated: 'Cart updated.',
            catalogPublished: 'Catalog published.',
            catalogDiscontinued: 'Catalog discontinued.',
            duplicationInProgressCatalog: 'Catalog scheduled for duplication.',
            administered: 'Administered.',
            identityDisconnected: 'Identity disconnected.',
            identityConnected: 'Identity connected.',
            createVariantsFirst: 'Create some variants first.',
            saveProductFirst: 'Save product first.',
            provideProperValues: 'Provide proper values in the form fields first!',
            uploadImagesFirst: 'Use "Images" dialog to upload and arrange catalog images first.',
            messangerDisabledWhenEmpty: 'Messenger is disabled for empty shopping carts!',
            feedbackReviewed: 'Feedback reviewed.',
            feedbackReported: 'Feedback reported.',
            feedbackLeft: 'Feedback left.'
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
            addLines: 'Add Line',
            edit18: 'Following',
            viewAddresses: 'Addresses',
            addAddresses: 'Add Address',
            editAddresses: 'Edit Address',
            addLocations: 'Add Locations',
            editLines: 'Edit Lines',
            addPrice: 'Add Price',
            editPrice: 'Edit Price',
            viewInstances: 'Variant Configurations',
            editInstances: 'Edit Variant Configuration',
            addInstances: 'Add Variant Configuration',
            addContents: 'Add Content',
            editContents: 'Edit Content',
            account: 'Account',
            admin: 'Admin',
            users: 'Users',
            aboutRules: 'About Rules',
            addDocuments: 'Add Content',
            editDocuments: 'Edit Content',
            editContent: false,
            sellerProfile: 'Seller Profile'
        });

    }));
}());
