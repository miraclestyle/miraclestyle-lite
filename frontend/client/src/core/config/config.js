(function () {
    'use strict';

    angular.module('app').config(ng(function (GLOBAL_CONFIG, $injector) {
        var locals = {};

        locals.guideByHost = {
            'localhost:9982': 'aiBkZXZ-dGhlbWlyYWNsZXN0eWxlLXRlc3Rpbmctc2l0ZXIsCxICMTEYgICAgID4hQkMCxICMjMiBnNlbGxlcgwLEgIzMRiAgICAgMqgCQw'
        };

        GLOBAL_CONFIG.guideKey = locals.guideByHost[window.location.host];

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
                message: 'If this is the only sign in identity connected to your MIRACLESTYLE account, you will permanently lose access to the account and all of its data after this action is completed!',
                text: {
                    primary: 'Disconnect'
                }
            },
            removePricetagConfirm: {
                title: 'Remove the product?',
                message: 'The product will be permanently removed from the catalog! You will be notified once this action is completed.',
                text: {
                    primary: 'Remove'
                }
            },
            connectSignInMethod: {
                title: 'Connect the identity?',
                message: 'If this sign in identity is already connected to another MIRACLESTYLE account, you will have to disconnect it before you proceed with this action!',
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
            deleteCart: {
                title: 'Empty the cart at once?',
                message: 'If you empty the cart all of its items and settings will be lost permanently.',
                text: {
                    primary: 'Empty'
                }
            },
            deleteOrder: {
                title: 'Delete the order?',
                message: 'This order will be deleted, and all of its settings will be lost after this action is completed.',
                text: {
                    primary: 'Delete'
                }
            },
            convertToOrder: {
                title: 'Place your order and pay?',
                message: 'If you click on "PAY", a new purchase order will be generated in your "Buyer / Orders" section, and you will be automatically redirected to a payment gateway web page to complete the payment transaction for the new purchase order.',
                text: {
                    primary: 'Pay'
                }
            },
            publishCatalog: {
                title: 'Publish the catalog?',
                message: 'A published catalog is accessible to the general public and can be shared and embedded to third party websites. With an exception of a product "Stock configurations", a published catalog cannot be edited. However, a published catalog can be duplicated, and the duplicate is ready for editing. You will be notified once this action is completed.',
                text: {
                    primary: 'Publish'
                }
            },
            discontinueCatalog: {
                title: 'Discontinue the catalog?',
                message: 'A discontinued catalog is not accessible to anyone and is entirely removed from the MIRACLESTYLE app after 15 days. You will be notified once this action is completed.',
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

        locals.catalogActions = function () {
            return {
                openCatalog: "open catalog",
                closeCatalog: "close catalog",
                openCatalogDrawer: "open catalog drawer",
                closeCatalogDrawer: "close catalog drawer",
                loadMoreCatalogImages: "load more catalog images",
                openCatalogShareDrawer: "open catalog share drawer",
                closeCatalogShareDrawer: "close catalog share drawer",
                focusCatalogShareLink: "focus catalog share link",
                focusCatalogShareEmbedCode: "focus catalog share embed code",
            };
        };

        locals.productActions = function () {
            return {
                openProduct: "open product",
                closeProduct: "close product",
                openProductDrawer: "open product drawer",
                closeProductDrawer: "close product drawer",
                changeProductVariantOption: "change product variant option",
                focusProductCustomVariant: "focus product custom variant",
                changeProductQuantity: "change product quantity",

                addToCartSuccess: "add to cart success",
                addToCartFail: "add to cart fail",
                updateCartSuccess: "update cart success",
                updateCartFail: "update cart fail",

                openProductShareDrawer: "open product share drawer",
                closeProductShareDrawer: "close product share drawer",
                focusProductShareLink: "focus product share link",
            };
        };

        locals.cartActions = function () {
            return {
                openCart: "open cart",
                closeCart: "close cart",
                initiateEmptyCart: "initiate empty cart",
                confirmEmptyCart: "confirm empty cart",
                cancelEmptyCart: "cancel empty cart",
                proceedToCheckoutSuccess: "proceed to checkout success",
                proceedToCheckoutFail: "proceed to checkout fail",
                selectShippingMethodSuccess: "select shipping method success",
                selectShippingMethodFail: "select shipping method fail",
                reviewCartSuccess: "review cart success",
                reviewCartFail: "review cart fail",
                payWithCardSuccess: "pay with card success",
                payWithCardFail: "pay with card fail",
                paySuccess: "pay success",
                payFail: "pay fail",
                openMessages: "open messages",
                closeMessages: "close messages",
                sendMessageSuccess: "send message success",
                sendMessageFail: "send message fail",
                openSellerDrawer: "open seller drawer",
                closeSellerDrawer: "close seller drawer",
                useSavedAddressForShipping: "use saved address for shipping",
                useSavedAddressForBilling: "use saved address for billing",

                removeLineSuccess: "remove line success",
                removeLineFail: "remove line fail"
            };
        };

        locals.sellerActions = function () {
            return {};
        };

        locals.makeActions = function (category, fn) {
            var maker = fn();
            angular.forEach(maker, function (value, key) {
                maker[key] = [category, value];
            });
            return maker;
        };

        $.extend(GLOBAL_CONFIG.tracker, {

            catalogHome: locals.makeActions('Home', locals.catalogActions),
            catalogSellerCatalogs: locals.makeActions('Seller / Catalogs', locals.catalogActions),
            catalogLink: locals.makeActions('Link', locals.catalogActions),
            catalogLinkByProduct: locals.makeActions('Link', locals.catalogActions),
            catalogEmbed: locals.makeActions('Embed', locals.catalogActions),

            productHomeCatalog: locals.makeActions('Home / Catalog', locals.productActions),
            productSellerCatalogsCatalog: locals.makeActions('Seller / Catalogs / Catalog', locals.productActions),
            productLinkCatalog: locals.makeActions('Link / Catalog', locals.productActions),
            productEmbedCatalog: locals.makeActions('Embed / Catalog', locals.productActions),
            productHomeCatalogCart: locals.makeActions('Home / Catalog / Cart', locals.productActions),
            productSellerCatalogsCatalogCart: locals.makeActions('Seller / Catalogs / Catalog / Cart', locals.productActions),
            productLinkCatalogCart: locals.makeActions('Link / Catalog / Cart', locals.productActions),
            productEmbedCatalogCart: locals.makeActions('Embed / Catalog / Cart', locals.productActions),
            productBuyerCartsCart: locals.makeActions('Buyer / Carts / Cart', locals.productActions),
            productLink: locals.makeActions('Link', locals.productActions),

            sellerHomeCatalog: locals.makeActions('Home / Catalog', locals.sellerActions),
            sellerSellerCatalogsCatalog: locals.makeActions('Seller / Catalogs / Catalog', locals.sellerActions),
            sellerLinkCatalog: locals.makeActions('Link / Catalog', locals.sellerActions),
            sellerEmbedCatalog: locals.makeActions('Embed / Catalog', locals.sellerActions),
            sellerHomeCatalogCart: locals.makeActions('Home / Catalog / Cart', locals.sellerActions),
            sellerSellerCatalogsCatalogCart: locals.makeActions('Seller / Catalogs / Catalog / Cart', locals.sellerActions),
            sellerLinkCatalogCart: locals.makeActions('Link / Catalog / Cart', locals.sellerActions),
            sellerEmbedCatalogCart: locals.makeActions('Embed / Catalog / Cart', locals.sellerActions),
            sellerBuyerCartsCart: locals.makeActions('Buyer / Carts / Cart', locals.sellerActions),
            sellerLink: locals.makeActions('Link', locals.sellerActions),

            cartHomeCatalog: locals.makeActions('Home / Catalog', locals.cartActions),
            cartSellerCatalogsCatalog: locals.makeActions('Seller / Catalogs / Catalog', locals.cartActions),
            cartLinkCatalog: locals.makeActions('Link / Catalog', locals.cartActions),
            cartEmbedCatalog: locals.makeActions('Embed / Catalog', locals.cartActions),
            cartBuyerCarts: locals.makeActions('Buyer / Carts', locals.cartActions)

        });

        GLOBAL_CONFIG.tracker.catalogHome.product = GLOBAL_CONFIG.tracker.productHomeCatalog;
        GLOBAL_CONFIG.tracker.catalogSellerCatalogs.product = GLOBAL_CONFIG.tracker.productSellerCatalogsCatalog;
        GLOBAL_CONFIG.tracker.catalogLink.product = GLOBAL_CONFIG.tracker.productLinkCatalog;
        GLOBAL_CONFIG.tracker.catalogLinkByProduct.product = GLOBAL_CONFIG.tracker.productLink;
        GLOBAL_CONFIG.tracker.catalogEmbed.product = GLOBAL_CONFIG.tracker.productEmbedCatalog;

        GLOBAL_CONFIG.tracker.catalogHome.cart = GLOBAL_CONFIG.tracker.cartHomeCatalog;
        GLOBAL_CONFIG.tracker.catalogSellerCatalogs.cart = GLOBAL_CONFIG.tracker.cartSellerCatalogsCatalog;
        GLOBAL_CONFIG.tracker.catalogLink.cart = GLOBAL_CONFIG.tracker.cartLinkCatalog;
        GLOBAL_CONFIG.tracker.catalogLinkByProduct.cart = GLOBAL_CONFIG.tracker.cartLinkCatalog;
        GLOBAL_CONFIG.tracker.catalogEmbed.cart = GLOBAL_CONFIG.tracker.cartEmbedCatalog;

        GLOBAL_CONFIG.tracker.cartHomeCatalog.product = GLOBAL_CONFIG.tracker.productHomeCatalogCart;
        GLOBAL_CONFIG.tracker.cartSellerCatalogsCatalog.product = GLOBAL_CONFIG.tracker.productSellerCatalogsCatalogCart;
        GLOBAL_CONFIG.tracker.cartLinkCatalog.product = GLOBAL_CONFIG.tracker.productLinkCatalogCart;
        GLOBAL_CONFIG.tracker.cartEmbedCatalog.product = GLOBAL_CONFIG.tracker.productEmbedCatalogCart;
        GLOBAL_CONFIG.tracker.cartBuyerCarts.product = GLOBAL_CONFIG.tracker.productBuyerCartsCart;

        GLOBAL_CONFIG.tracker.cartHomeCatalog.seller = GLOBAL_CONFIG.tracker.sellerHomeCatalogCart;
        GLOBAL_CONFIG.tracker.cartSellerCatalogsCatalog.seller = GLOBAL_CONFIG.tracker.sellerSellerCatalogsCatalogCart;
        GLOBAL_CONFIG.tracker.cartLinkCatalog.seller = GLOBAL_CONFIG.tracker.sellerLinkCatalogCart;
        GLOBAL_CONFIG.tracker.cartEmbedCatalog.seller = GLOBAL_CONFIG.tracker.sellerEmbedCatalogCart;
        GLOBAL_CONFIG.tracker.cartBuyerCarts.seller = GLOBAL_CONFIG.tracker.sellerBuyerCartsCart;

        GLOBAL_CONFIG.tracker.catalogHome.seller = GLOBAL_CONFIG.tracker.sellerHomeCatalog;
        GLOBAL_CONFIG.tracker.catalogSellerCatalogs.seller = GLOBAL_CONFIG.tracker.sellerSellerCatalogsCatalog;
        GLOBAL_CONFIG.tracker.catalogLink.seller = GLOBAL_CONFIG.tracker.sellerLinkCatalog;
        GLOBAL_CONFIG.tracker.catalogLinkByProduct.seller = GLOBAL_CONFIG.tracker.sellerLinkCatalog;
        GLOBAL_CONFIG.tracker.catalogEmbed.seller = GLOBAL_CONFIG.tracker.sellerEmbedCatalog;


        $.extend(GLOBAL_CONFIG.labels, {
            account: {
                active: 'Active',
                suspended: 'Suspended'
            },
            catalog: {
                draft: 'Draft',
                published: 'Published',
                indexed: 'Indexed',
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
                review: 'Review',
                null: 'Unpaid'
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
            '114': {
                webhook_endpoint: 'Live webhook endpoint that you have to setup in your Stripe account settings. For more details read the "Sell with confidence" on this form.',
                secret_key: 'Live secret key that you can find in your Stripe account settings. Once you save the settings, this value will be encrypted before it is stored in the MIRACLESTYLE app database. For more details read the "Sell with confidence" on this form.',
                publishable_key: 'Live publishable key that you can find in your Stripe account settings.'
            },
            order: {
                card_exp: 'Card expiration printed on the front of your card.',
                cvc: 'Card verification code printed on the back of your card.'
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
                logo: 'Click on the logo above to upload logo image of the brand, company, or store that you represent. Logo must be of 2.4:1 aspect ratio, preferably 720 pixels wide and 300 pixels high.'
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
                discontinued_date: 'Date when this catalog will be automatically discontinued and become unavailable to the general public.'
            },
            '26': {
                name: 'Name of the variant input control that is visible on the product view.',
                options: 'Options that are available for selection on the variant input control. Specify one option per line.',
                description: 'Brief description visible beneath the variant input control.',
                allow_custom_value: 'If enabled, options defined above will be ignored, and buyers will be able to supply a custom value in the variant input control'
            }
        });

        $.extend(GLOBAL_CONFIG.fields.validationErrors, {
            invalid_card_number: 'Invalid card number.',
            invalid_card_cvc: 'Invalid cvc.',
            invalid_card_date: 'Invalid card date.'
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
            order: {
                cvc: 'CVC',
                card_exp: 'Card expiration (MM / YY)',
            },
            '28': {
                uom: 'Unit of measurement',
                variant_options: 'Select all variant options you want this configuration to be matched with',
                weight: 'Weight (kilogram)',
                volume: 'Volume (liter)',
                _stock: 'Stock configurations'
            },
            '27': {
                uom: 'Unit of measurement',
                weight: 'Weight (kilogram)',
                volume: 'Volume (liter)'
            },
            '109': {
                carriers: 'Carriers this rule applies to'
            },
            '112': {
                rules: 'Prices'
            },
            '124': {
                discount_value: 'Discount (%)',
                product_categories: 'Product categories'
            },
            '31-update': {
                discontinued_date: 'Expiration date'
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
        $.extend(GLOBAL_CONFIG.fields.translateChoices, {
            '107': {
                address_type: locals.addressTypeSpec
            },
            '133': {
                availability: {
                    'in stock': 'In stock',
                    'out of stock': 'Out of stock',
                    'preorder': 'Preorder',
                    'available for order': 'Available for order'
                }
            },
            '109': {
                address_type: locals.addressTypeSpec,
                type: {
                    proportional: 'Proportional (%)',
                    fixed: 'Fixed (Amount)'
                }
            },
            '111': {
                condition_type: {
                    weight: 'weight',
                    volume: 'volume',
                    'weight*volume': 'weight multiplied by volume',
                    price: 'net total'
                },
                condition_operator: locals.conditionOperatorSpec,
                price_type: {
                    fixed: 'fixed',
                    variable: 'varied by'
                },
                price_operator: {
                    weight: 'weight multiplied by',
                    volume: 'volume multiplied by',
                    'weight*volume': 'weight multiplied by volume multiplied by',
                    price: 'net total multiplied by'
                }
            },
            '124': {
                condition_type: {
                    price: 'product subtotal',
                    quantity: 'product quantity'
                },
                condition_operator: locals.conditionOperatorSpec
            },
            rules: {
                kind: {
                    '109': 'Tax',
                    '126': 'Discount',
                    '107': 'Address',
                    '117': 'Currency',
                    '108': 'PayPal',
                    '113': 'Carrier',
                    '114': 'Stripe'
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
            '134': {
                stocks: 'catalog/product/help/stock_configurations.html',
            },
            '107': {
                locations: 'seller/help/locations.html'
            },
            '28': {
                images: 'catalog/product/help/images.html',
                variants: 'catalog/product/help/variants.html',
                _instances: 'catalog/product/help/instances.html'
            },
            '27': {
                images: 'catalog/product/help/images.html',
                variant_options: 'catalog/product/help/variant_options.html'
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

        $.extend(GLOBAL_CONFIG.misc.text, {
            leaveUnsaved: 'You have unsaved changes.'
        });

        $.extend(GLOBAL_CONFIG.subheaders, {
            loginMethods: 'Sign in identities',
            productInstances: 'Variant configurations',
            catalogImages: 'Images',
            catalogProducts: 'Products',
            history: 'History',
            record: 'Log Entry',
            sellerPlugins: 'Rules',
            stripeWithConfidence: 'Sell with confidence'
        });

        $.extend(GLOBAL_CONFIG.emptyHelp, {
            orderSellerList: 'seller/help/orders.html',
            cartSellerList: 'seller/help/carts.html',
            orderBuyerList: 'buyer/help/orders.html',
            cartBuyerList: 'buyer/help/carts.html',
            catalogList: 'catalog/help/list.html',
            cartMessages: 'order/help/messages.html',
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
            identityTaken: 'This identity is already connected to another MIRACLESTYLE account.',
            identityConnected: 'Identity connected.',
            identityConnectionCanceled: 'Connecting identity canceled.',
            failedGeneratingAuthorizaitonUrl: 'Failed accessing identity, please try again.',
            identityConnectionFailed: 'Connecting identity failed.',
            createVariantsFirst: 'Create some variants first.',
            saveProductFirst: 'Save product first.',
            provideProperValues: 'Provide proper values in the form fields first!',
            uploadImagesFirst: 'Navigate to the "Images" to upload and arrange catalog images first.',
            messangerDisabledWhenEmpty: 'Messenger is disabled for empty shopping carts!',
            accessDenied: 'Action denied! Your account is not authorized to perform this action.',
            noBuyer: 'No buyer address. You did not provide any buyer information.',
            sellerProfileNotFound: 'Navigate to the "Seller / Settings" to configure seller profile first.',
            productDuplicated: 'Product duplicated.',
            catalogDuplicated: 'Catalog duplicated.',
            errorWithTraceback: 'Server errored with traceback.',
            actionFailedCheckForm: 'Action failed! Inspect the form for errors.',
            orderPaymentSuccessProgress: 'Order processing is in pogress.',
            orderPaymentSuccessProgressCanceled: 'Payment canceled.',
            orderPaymentSuccessProgressCompleted: 'Payment completed.',
            orderPaymentSuccessProgressRefunded: 'Payment refunded.',
            orderPaymentSuccessProgressPending: 'Payment pending.',
            orderPaymentSuccessProgressMismatched: 'Payment mismatched.',
            sellerProhibtsAddress: 'The seller prohibits one of the addresses that you have supplied.',
            productOutOfStock: 'Product out of stock.',
            saveChangesFirst: 'Save changes first.',
            loginSuccess: 'Signed in.',
            loginFailed: 'Sign in failed!',
            loggedOut: 'Signed out.',
            loginCanceled: 'Sign in canceled.',
            youAreNotSignedIn: 'You are not signed in.',
            saveInProgress: 'Please wait, save in progress.',
            orderNotFound: 'This order does not exist.',
            catalogNotFound: 'This catalog does not exist.',
            catalogProductNotFound: 'This catalog product does not exist.',
            rejectedAccountAccess: 'You rejected access to your account.',
            incorrectAccessToken: 'Incorrect access token. Please try again.',
            takenByOtherAccount: 'This identity is already connected to another MIRACLESTYLE account.',
            failedGettingEmail: 'E-mail not provided by the provider.',
            incorrectLinkSettings: 'Incorrect link settings.',
            failedAuthentication: 'Failed authentication with the provider.',
            outOfStockLinesRemoved: 'Some of the products on the order were out of stock and have been removed from the order.',
            invalidCsrf: 'Invalid request. Please reload your browser.',
            orderPaymentNoPaymentMethodSupplied: 'Payments are not admitted at this moment.',
            orderPaymentFailed: 'An error occurred on the server.',
            orderPaymentInvalidNumber: 'The card number is not a valid credit card number.',
            orderPaymentInvalidExpiryMonth: 'The card\'s expiration month is invalid.',
            orderPaymentInvalidExpiryYear: 'The card\'s expiration year is invalid.',
            orderPaymentInvalidCVC: 'The card\'s security code is invalid.',
            orderPaymentIncorrectNumber: 'The card number is incorrect.',
            orderPaymentExpiredCard: 'The card has expired.',
            orderPaymentIncorrectCVC: 'The card\'s security code is incorrect.',
            orderPaymentIncorrectZip: 'The card\'s zip code failed validation.',
            orderPaymentCardDeclined: 'The card was declined.',
            orderPaymentMissing: 'There is no card on a customer that is being charged.',
            orderPaymentProcessingError: 'An error occurred while processing the card.',
            orderPaymentCardSuccess: 'Payment completed.'
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
            viewStock: 'Stock Configurations',
            editStock: false,
            editStocks: 'Edit Stock Configuration',
            addStocks: 'Add Stock Configuration',
            settings: 'Settings',
            addPlugins: 'Add Rule',
            editPlugins: 'Edit Rule',
            addVariants: 'Add Variant',
            editVariants: 'Edit Variant',
            home: 'Home',
            about: 'About',
            acceptable_use_policy: 'Acceptable Use Policy',
            tos: 'Terms of Service',
            support: 'Support',
            copyright_policy: 'Copyright & Trademark',
            privacy_policy: 'Privacy Policy',
            buyer: 'Buyer',
            carts: 'Carts',
            orders: 'Orders',
            catalogs: 'Catalogs',
            addLines: 'Add Line',
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
            account: 'Account',
            admin: 'Admin',
            users: 'Accounts',
            aboutRules: 'About Rules',
            sellerProfile: 'Seller Profile',
            payWithConfidence: 'Pay With Confidence'
        });

        if (!GLOBAL_CONFIG.backendErrorHandling) {
            GLOBAL_CONFIG.backendErrorHandling = {};
        }


    })).run(ng(function (GLOBAL_CONFIG, currentAccount, models, $state, $timeout, snackbar) {
        $.extend(GLOBAL_CONFIG.backendErrorHandling, {
            sellerProfileNotFound: function (errors) {
                if (errors.not_found && $.inArray('seller', errors.not_found) !== -1) {
                    return GLOBAL_CONFIG.snackbar.messages.sellerProfileNotFound;
                }
                return false;
            },
            orderNotFound: function (errors) {
                if (errors.not_found || errors.malformed_key) {
                    return GLOBAL_CONFIG.snackbar.messages.orderNotFound;
                }
                return false;
            },
            catalogNotFound: function (errors) {
                if (errors.not_found || errors.malformed_key) {
                    return GLOBAL_CONFIG.snackbar.messages.catalogNotFound;
                }
                return false;
            },
            productOutOfStock: function (errors) {
                if (errors.plugin_error && $.inArray('product_out_of_stock', errors.plugin_error) !== -1) {
                    return GLOBAL_CONFIG.snackbar.messages.productOutOfStock;
                }
                return false;
            },
            internal_server_error: function (errors) {
                return 'An error occurred on the server.';
            },
            action_denied: function () {
                return 'You do not have permission to perform this action.';
            },
            not_found: function (fields) {
                return 'Requested data ' + fields.join(', ') + ' could not be found in the database.';
            },
            invalid_csrf: function () {
                return GLOBAL_CONFIG.snackbar.messages.invalidCsrf;
            },
            invalid_image_type: 'You have supplied incorrect type of image format.',
            invalid_model: 'You have requested access to resource that does not exist,',
            invalid_action: 'You have requested access to the action that does not exist.',
            required: function (fields) {
                return 'Some values are missing: ' + fields.join(', ') + '.';
            },
            connection_refused: function () {
                return 'Failed to establish connection.';
            },
            invalid_response: function () {
                return 'Server failed to respond, please try again.';
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
