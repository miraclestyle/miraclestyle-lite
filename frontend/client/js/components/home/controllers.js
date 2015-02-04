(function () {
    'use strict';
    angular.module('app')
        .controller('MainMenuCtrl', function ($scope, currentAccount, GLOBAL_CONFIG, $mdSidenav, $timeout) {
            $scope.currentAccount = currentAccount;
            $scope.GLOBAL_CONFIG = GLOBAL_CONFIG;
            $scope.JSON = JSON;

            $scope.closeMenu = function () {
                $timeout(function () {
                    $mdSidenav('left').close();
                });
            };

            $scope.openMenu = function () {
                $timeout(function () {
                    $mdSidenav('left').open();
                });
            };


        })
        .controller('HomePageCtrl', function ($scope, models, modals, $state, $stateParams, $q, modelsMeta) {
            var args = {search: {}},
                defer = $q.defer(),
                promise = defer.promise;
            $scope.sellerDetail = false;
            if ($stateParams.key) {
                args.search.filters = [{field: 'seller_account_key', operator: 'IN', value: $stateParams.key}];
                $scope.sellerDetail = {};
                models['23'].actions.read({
                    account: $stateParams.key,
                    read_arguments: {
                        _feedback: {},
                        _content: {}
                    }
                }).then(function (response) {
                    $.extend($scope.sellerDetail, response.data.entity);
                });

                $scope.viewSeller = function () {
                    models['23'].viewModal($scope.sellerDetail);
                };

            }
            if ($state.current.name === 'collections') {
                promise = models['18'].current();
                promise.then(function (response) {
                    $scope.search.pagination.args.search.filters = [{field: 'ancestor', operator: 'IN', value: response.data.entity.sellers}];
                });
            } else {
                defer.resolve();
            }
            $scope.search = {
                results: [],
                pagination: {}
            };
            $scope.view = function (key) {
                models['31'].viewModal(key);
            };

            $scope.scrollEnd = {loader: false};

            $scope.search.pagination = models['31'].paginate({
                kind: '31',
                args: args,
                config: {
                    normalizeEntity: false
                },
                action: 'public_search',
                complete: function (response) {
                    var results = response.data.entities;
                    models['31'].formatPublicSearchResults(results);
                    $scope.search.results.extend(results);
                }
            });
            $scope.scrollEnd.loader = $scope.search.pagination;
            promise.then(function () {
                $scope.search.pagination.load();
            });

            $scope.bar = {};

            $scope.args = {category: 'ahFkZXZ-eC1hcmNhbnVtLTgwMXIoCxICMjQiIDE5MTk4ZDk4YjI1ZTZjYWQ2OTliNGY3ZTNhZmRlNzljDA'};

            $scope.selectTest = {
                "type": "SuperStringProperty",
                "choices": ["Afghanistan","Albania","Algeria","American Samoa","Andorra","Angola","Anguilla","Antarctica","Antigua and Barbuda","Argentina","Armenia","Aruba","Australia","Austria","Azerbaijan","Bahamas","Bahrain","Bangladesh","Barbados","Belarus","Belgium","Belize","Benin","Bermuda","Bhutan","Bolivia, Plurinational State of","Bonaire, Sint Eustatius and Saba","Bosnia and Herzegovina","Botswana","Bouvet Island","Brazil","British Indian Ocean Territory","Brunei Darussalam","Bulgaria","Burkina Faso","Burundi","Cambodia","Cameroon","Canada","Cape Verde","Cayman Islands","Central African Republic","Chad","Chile","China","Christmas Island","Cocos (Keeling) Islands","Colombia","Comoros","Congo","Congo, The Democratic Republic of the","Cook Islands","Costa Rica","Croatia","Cuba","Curaçao","Cyprus","Czech Republic","Côte d'Ivoire","Denmark","Djibouti","Dominica","Dominican Republic","Ecuador","Egypt","El Salvador","Equatorial Guinea","Eritrea","Estonia","Ethiopia","Falkland Islands (Malvinas)","Faroe Islands","Fiji","Finland","France","French Guiana","French Polynesia","French Southern Territories","Gabon","Gambia","Georgia","Germany","Ghana","Gibraltar","Greece","Greenland","Grenada","Guadeloupe","Guam","Guatemala","Guernsey","Guinea","Guinea-Bissau","Guyana","Haiti","Heard Island and McDonald Islands","Holy See (Vatican City State)","Honduras","Hong Kong","Hungary","Iceland","India","Indonesia","Iran, Islamic Republic of","Iraq","Ireland","Isle of Man","Israel","Italy","Jamaica","Japan","Jersey","Jordan","Kazakhstan","Kenya","Kiribati","Korea, Democratic People's Republic of","Korea, Republic of","Kuwait","Kyrgyzstan","Lao People's Democratic Republic","Latvia","Lebanon","Lesotho","Liberia","Libya","Liechtenstein","Lithuania","Luxembourg","Macao","Macedonia, Republic of","Madagascar","Malawi","Malaysia","Maldives","Mali","Malta","Marshall Islands","Martinique","Mauritania","Mauritius","Mayotte","Mexico","Micronesia, Federated States of","Moldova, Republic of","Monaco","Mongolia","Montenegro","Montserrat","Morocco","Mozambique","Myanmar","Namibia","Nauru","Nepal","Netherlands","New Caledonia","New Zealand","Nicaragua","Niger","Nigeria","Niue","Norfolk Island","Northern Mariana Islands","Norway","Oman","Pakistan","Palau","Palestine, State of","Panama","Papua New Guinea","Paraguay","Peru","Philippines","Pitcairn","Poland","Portugal","Puerto Rico","Qatar","Romania","Russian Federation","Rwanda","Réunion","Saint Barthélemy","Saint Helena, Ascension and Tristan da Cunha","Saint Kitts and Nevis","Saint Lucia","Saint Martin (French part)","Saint Pierre and Miquelon","Saint Vincent and the Grenadines","Samoa","San Marino","Sao Tome and Principe","Saudi Arabia","Senegal","Serbia","Seychelles","Sierra Leone","Singapore","Sint Maarten (Dutch part)","Slovakia","Slovenia","Solomon Islands","Somalia","South Africa","South Georgia and the South Sandwich Islands","South Sudan","Spain","Sri Lanka","Sudan","Suriname","Svalbard and Jan Mayen","Swaziland","Sweden","Switzerland","Syrian Arab Republic","Taiwan, Province of China","Tajikistan","Tanzania, United Republic of","Thailand","Timor-Leste","Togo","Tokelau","Tonga","Trinidad and Tobago","Tunisia","Turkey","Turkmenistan","Turks and Caicos Islands","Tuvalu","Uganda","Ukraine","United Arab Emirates","United Kingdom","United States","United States Minor Outlying Islands","Uruguay","Uzbekistan","Vanuatu","Venezuela, Bolivarian Republic of","Viet Nam","Virgin Islands, British","Virgin Islands, U.S.","Wallis and Futuna","Western Sahara","Yemen","Zambia","Zimbabwe","Åland Islands"],
                "code_name": "order_by_created",
                "required": "true",
                "ui": {
                    "placeholder": "Select...",
                    "writable": true,
                    "args": "bar.far",
                    "parentArgs": "bar",
                    "rootScope": "rootScope",
                    "model": "entity",
                    "name": "order_by_created",
                    "specifics": {
                        "search": true
                    }
                }
            };

            $scope.selectTest2 = {
                "type": "SuperStringProperty",
                "choices": $scope.selectTest.choices.slice(0, 3),
                "code_name": "order_by_created",
                "required": "true",
                "ui": {
                    "placeholder": "Select...",
                    "writable": true,
                    "args": "bar.zar",
                    "parentArgs": "bar",
                    "rootScope": "rootScope",
                    "model": "entity",
                    "name": "order_by_created2"
                }
            };

            $scope.selectTest3 = modelsMeta.get('19').mapped_actions.update['arguments'].addresses.modelclass.country;
            $scope.selectTest5 = modelsMeta.get('19').mapped_actions.update['arguments'].addresses.modelclass.region;
            $scope.selectTest4 = modelsMeta.get('31').mapped_actions.update['arguments']._images.modelclass.pricetags.modelclass._product.modelclass.category;

            angular.forEach(['selectTest3', 'selectTest4', 'selectTest5'], function (t) {
                $scope[t].ui.writable = true;
            });


        });

}());