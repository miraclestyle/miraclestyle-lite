(function () {
    'use strict';

    angular.module('app').config(function (GLOBAL_CONFIG) {

        $.extend(GLOBAL_CONFIG.confirmations, {
            discardWithFieldsRequired: {
                title: 'Discard unsaved changes?',
                message: 'There are some unsaved changes on the form you are trying to close. If you discard them, the item you are trying to add will not be added.',
                text: {
                    primary: 'Discard'
                }
            },
            discard: {
                title: 'Discard unsaved changes?',
                message: 'There are some unsaved changes on the form you are trying to close. If you discard them, the changes will be lost permanently, and the form will revert to previously saved state.',
                text: {
                    primary: 'Discard'
                }
            }
        });

        $.extend(GLOBAL_CONFIG.alerts, {
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
            sort: {
                title: 'How to use this action',
                messages: ['Reorder the item by dragging it within its group.',
                           'Remove the item by dragging it outside the left edge of the screen.'],
                text: {
                    primary: 'Got it'
                }
            }
        });


    });
}());