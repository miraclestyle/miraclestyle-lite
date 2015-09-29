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
                title: 'Disconnect the identity?',
                message: 'If this is the only sign in identity connected to your Miraclestyle account, you will permanently lose access to the account and all of its data after this action is completed!',
                text: {
                    primary: 'Disconnect'
                }
            },
            connectSignInMethod: {
                title: 'Connect the identity?',
                message: 'If this sign in identity is already connected to another Miraclestyle account, you will have to disconnect it before you proceed with this action!',
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
                title: 'Confirm sign out',
                message: 'Are you sure you want to sign out?',
                text: {
                    primary: 'Sign out'
                },
            },
            cancelOrder: {
                title: 'Reset the cart?',
                message: 'This cart will be emptied, and all of its settings will be lost after this action is completed.',
                text: {
                    primary: 'Reset'
                }
            },
            toCheckout: {
                title: 'Review the cart?',
                message: 'You won\'t be able to update the cart after this step. However, you will be able to reset the cart, or place an order by making a payment.',
                text: {
                    primary: 'Review'
                }
            },
            publishCatalog: {
                title: 'Publish the catalog?',
                message: 'A published catalog is accessible to the general public and can be shared and embedded to third party websites. With an exception of a product "Availability" field, a published catalog cannot be edited. However, a published catalog can be duplicated, and the duplicate is ready for editing. You will be notified once this action is completed.',
                text: {
                    primary: 'Publish'
                }
            },
            discontinueCatalog: {
                title: 'Discontinue the catalog?',
                message: 'A discontinued catalog is not accessible to the general public and is eventually entirely removed from the Miraclestyle app. However, products of a discontinued catalog remain accessible for the 180 days to those who have purchased them. A discontinued catalog cannot be edited or duplicated. You will be notified once this action is completed.',
                text: {
                    primary: 'Discontinue'
                }
            },
            duplicateCatalogPricetag: {
                title: 'Schedule duplication?',
                message: 'Duplication can take a while to complete! You will be notified once this action is completed.',
                text: {
                    primary: 'Schedule'
                }
            },
            duplicateCatalog: {
                title: 'Schedule duplication?',
                message: 'Duplication can take a while to complete! You will be notified once this action is completed.',
                text: {
                    primary: 'Schedule'
                }
            }
        });

        locals.gotit = {
            primary: 'Got it'
        };

        $.extend(GLOBAL_CONFIG.modals.alerts, {
            howToSort: {
                title: 'How to use this action',
                messages: ['Reorder the item by dragging it within its group.',
                    'Remove the item by dragging it outside the left edge of the screen.'
                ],
                text: locals.gotit
            },
            howToDeleteDragging: {
                title: 'How to use this action',
                message: 'Remove the item by dragging it outside the left edge of the screen.',
                text: locals.gotit
            },
            howToDropPricetag: {
                title: 'How to use this action',
                messages: ['Add a new product to the catalog by dragging the "Add" tag to a catalog image. While dragging, it is preferable to aim the tag dot for the image area that shows the product that the tag will link to. Add one tag per product per catalog.',
                    'Reposition a tag by dragging it within images area.',
                    'Click on a tag to open the "Edit Product" form while editing the catalog.',
                    'Click on a tag to open the product view while viewing the catalog.'
                ],
                text: locals.gotit
            }
        });


        $.extend(GLOBAL_CONFIG.labels, {
            account: {
                active: 'Active',
                suspended: 'Suspended'
            },
            catalog: {
                draft: 'Draft',
                published: 'Published',
                discontinued: 'Discontinued',
                unindex: 'Unindex',
                index: 'Index'
            },
            order: {
                cart: 'Cart',
                checkout: 'Checkout',
                completed: 'Completed',
                canceled: 'Canceled',
                positive: 'Positive',
                negative: 'Negative',
                neutral: 'Neutral',
                revision: 'Review',
                reported: 'Reported',
                sudo: 'Administered',
                review: 'Review'
            }
        });

        locals.fieldhelpForProduct = {
            weight: 'Product weight, expressed in kilograms, per unit of measurement. This field is used by the Carrier rule for calculating delivery costs.',
            volume: 'Product volume, expressed in liters, per unit of measurement. This field is used by the Carrier rule for calculating delivery costs.'
        };

        $.extend(GLOBAL_CONFIG.fields.help, {
            '124-update': {
                condition_type: 'Condition under which this line applies.',
                price_type: 'Price formula that calculates this price.'
            },
            '106': {
                postal_codes: 'Postal codes this location affects. Specify one postal code per line.'
            },
            '108': {
                reciever_email: 'Primary email address for your PayPal account.',
                business: 'Email address on which you want to receive your PayPal payments. This value will be the same as "Receiver Email" in case that you have only one email address associated with your PayPal account.'
            },
            '109': {
                product_codes: 'Specific product codes this rule applies to. Specify one product code per line.',
                address_type: 'Buyer address type this rule applies to.'
            },
            '124': {
                product_codes: 'Specific product codes this line applies to. Specify one product code per line.'
            },
            '117': {
                currency: 'Currency you accept, and your product unit prices are expressed in.'
            },
            '111-update': {
                condition_type: 'Condition under which this price applies.',
                price_type: 'Price formula that calculates this price.'
            },
            '23-update': {
                name: 'Name of the brand, company, or store that you represent.',
                logo: 'Click on the logo above to upload logo image of the brand, company, or store that you represent. Logo must be of 2.4:1 aspect ratio, preferably 2400 pixels wide and 1000 pixels high.'
            },
            '14': {
                name: 'Recipient\'s full name or business name.'
            },
            '107': {
                address_type: 'Buyer address type this rule applies to.'
            },
            '27': locals.fieldhelpForProduct,
            '28': locals.fieldhelpForProduct,
            '31-update': {
                discontinue_date: 'Date when this catalog will be automatically discontinued and become unavailable to the general public.'
            },
            '26': {
                name: 'Name of the variant input control that is visible on the product view.',
                options: 'Options that are available for selection on the variant input control. Specify one option per line.',
                description: 'Brief description visible beneath the variant input control.',
                allow_custom_value: 'If enabled, options defined above will be ignored, and buyers will be able to supply a custom value in the variant input control'
            }
        });

        $.extend(GLOBAL_CONFIG.fields.label, {
            search: {
                indexID: 'Search options',
                ancestor: 'Ancestor',
                operator: 'Operator'
            },
            plugins: {
                kind: 'Rule'
            },
            '28': {
                uom: 'Unit of measurement',
                variant_options: 'Variant combinations',
                weight: 'Weight (kilogram)',
                volume: 'Volume (liter)'
            },
            '27': {
                uom: 'Unit of measurement',
                variant_options: 'Variant combinations',
                weight: 'Weight (kilogram)',
                volume: 'Volume (liter)'
            },
            '112': {
                rules: 'Prices'
            },
            '124': {
                discount_value: 'Discount (%)',
                product_categories: 'Product categories'
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
                logo: 'Seller logo'
            },
            '18-update': {
                notify: 'Receive email notifications when a catalog is published or discontinued by the seller that you are following'
            }
        });

        locals.conditionOperatorSpec = {
            '==': 'equals to',
            '!=': 'is not equal to',
            '>': 'is greater than',
            '<': 'is less than',
            '>=': 'is greater than or equal to',
            '<=': 'is less than or equal to'
        };
        locals.addressTypeSpec = {
            billing: 'Billing',
            shipping: 'Shipping'
        };
        locals.conditionTypeSpec = {
            weight: 'weight',
            volume: 'volume',
            'weight*volume': 'weight multiplied by volume',
            price: 'price',
            quantity: 'quantity'
        };
        $.extend(GLOBAL_CONFIG.fields.translateChoices, {
            '107': {
                address_type: locals.addressTypeSpec
            },
            '109': {
                address_type: locals.addressTypeSpec,
                type: {
                    proportional: 'Proportional (%)',
                    fixed: 'Fixed (Amount)'
                }
            },
            '111': {
                condition_type: locals.conditionTypeSpec,
                condition_operator: locals.conditionOperatorSpec,
                price_type: {
                    fixed: 'fixed',
                    variable: 'varied by'
                },
                price_operator: {
                     weight: 'weight multiplied by',
                     volume: 'volume multiplied by',
                     'weight*volume': 'weight multiplied by volume multiplied by',
                     price: 'price multiplied by',
                     quantity: 'quantity multiplied by'
                 }
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
            '109': {
                carriers: 'seller/help/carriers.html',
                product_categories: 'seller/help/product_categories.html',
                locations: 'seller/help/locations.html'
            },
            '124': {
                product_categories: 'seller/help/product_categories_line.html'
            },
            '113': {
                lines: 'seller/help/carrier_lines.html',
            },
            '112': {
                locations: 'seller/help/locations_line.html',
                prices: 'seller/help/prices.html',
            },
            '126': {
                lines: 'seller/help/discount_lines.html'
            },
            '107': {
                locations: 'seller/help/locations.html'
            },
            '28': {
                images: 'catalog/product/help/images.html',
                contents: 'catalog/product/help/contents.html',
                variants: 'catalog/product/help/variants.html',
                _instances: 'catalog/product/help/instances.html'
            },
            '27': {
                images: 'catalog/product/help/images.html',
                contents: 'catalog/product/help/contents.html',
                variant_options: 'catalog/product/help/variant_options.html'
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
                falseLabel: 'Applies to all locations except those listed in the Locations section',
                trueLabel: 'Applies only to the locations listed in the Locations section'
            }
        });

        $.extend(GLOBAL_CONFIG.subheaders, {
            loginMethods: 'Sign in identities',
            productInstances: 'Variant configurations',
            catalogImages: 'Images',
            catalogProducts: 'Products',
            collectionSeller: 'Sellers',
            history: 'History',
            record: 'Log Entry',
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
            following: 'collection/help/sellers.html',
            sellerProfileCatalogList: 'seller/help/profile_catalogs.html'
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
            uploadImagesFirst: 'Navigate to the "Images" to upload and arrange catalog images first.',
            messangerDisabledWhenEmpty: 'Messenger is disabled for empty shopping carts!',
            feedbackReviewed: 'Feedback reviewed.',
            feedbackReported: 'Feedback reported.',
            feedbackLeft: 'Feedback left.',
            accessDenied: 'Action denied! Your account is not authorized to perform this action.',
            noBuyer: 'No buyer address. You did not provide any buyer information.',
            sellerProfileNotFound: 'Navigate to the "Seller / Settings" to configure seller profile first.',
            productDuplicated: 'Product duplicated.',
            catalogDuplicated: 'Catalog duplicated.'
        });

        $.extend(GLOBAL_CONFIG.toolbar.titles, {
            seller: 'Seller',
            edit31: 'Catalog',
            add31: 'Catalog',
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
            about: 'About',
            acceptable_use_policy: 'Acceptable Use Policy',
            tos: 'Terms of Service',
            copyright_policy: 'Copyright Policy',
            privacy_policy: 'Privacy Policy',
            buyer: 'Buyer',
            carts: 'Carts',
            orders: 'Orders',
            catalogs: 'Catalogs',
            addLines: 'Add Line',
            edit18: 'Following',
            viewAddresses: 'Addresses',
            addAddresses: 'Add Address',
            editAddresses: 'Edit Address',
            addLocations: 'Add Location',
            editLocations: 'Edit Location',
            editLines: 'Edit Line',
            addPrice: 'Add Price',
            addPrices: 'Add Price',
            editPrice: 'Edit Price',
            viewInstances: 'Variant Configurations',
            editInstances: 'Edit Variant Configuration',
            addInstances: 'Add Variant Configuration',
            addContents: 'Add Content',
            editContents: 'Edit Content',
            account: 'Account',
            admin: 'Admin',
            users: 'Accounts',
            aboutRules: 'About Rules',
            addDocuments: 'Add Content',
            editDocuments: 'Edit Content',
            editContent: false,
            sellerProfile: 'Seller Profile'
        });

        if (!GLOBAL_CONFIG.backendErrorHandling) {
            GLOBAL_CONFIG.backendErrorHandling = {};
        }
        $.extend(GLOBAL_CONFIG.backendErrorHandling, {
            sellerProfileNotFound: function (errors) {
                if (errors.not_found && $.inArray('seller', errors.not_found) !== -1) {
                    return GLOBAL_CONFIG.snackbar.messages.sellerProfileNotFound;
                }
                return false;
            },
            action_denied: function (reason) {
                return 'You do not have permission to perform this action.';
            },
            not_found: function (fields) {
                return 'Requested data ' + fields.join(', ') + ' could not be found in database.';
            },
            invalid_image_type: 'You have supplied incorrect type of image format.',
            invalid_model: 'You have requested access to resource that does not exist,',
            invalid_action: 'You have requested access to the action that does not exist.',
            required: function (fields) {
                return 'Some values are missing: ' + fields.join(', ') + '.';
            },
            traceback: function (trace) {
                var parse = $.parseHTML(trace);
                return $(parse).filter('pre').text();
            },
            transaction: function (reason) {
                if (reason === 'timeout') {
                    return 'Transaction was not completed due timeout. Please try again.';
                }
                if (reason === 'failed') {
                    return 'Transaction was not completed due failure. Please try again.';
                }
                return reason;
            }
        });

    }));
}());
