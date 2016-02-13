(function () {
    'use strict';
    angular.module('app').factory('social', ng(function ($modal, GLOBAL_CONFIG, helpers) {
        var social = {
            share: function ($scope, meta, embed, link, config) {
                config = helpers.alwaysObject(config);
                var track = config.track;
                if (!$scope.share) {
                    $scope.share = {};
                }
                return (function ($scope) {

                    if (!$scope.menu) {
                        $scope.menu = {};
                        helpers.sideNav.setup($scope.menu, 'sharer');
                        $scope.menu.stateChanged = function (v1, v2) {
                            var track = $scope.menu.getTracker();
                            if (v1) {
                                track.openShareDrawer();
                            } else {
                                track.closeShareDrawer();
                            }
                        };
                    }

                    $scope.menu.getTracker = function () {
                        return track;
                    };

                    $scope.socials = [{
                        name: 'Facebook',
                        key: 'facebook',
                        command: 'https://www.facebook.com/sharer.php?u={u}',
                        require: ['u']
                    }, {
                        name: 'Twitter',
                        key: 'twitter',
                        command: 'https://twitter.com/intent/tweet?text={text}&url={url}',
                        require: ['url', 'text']
                    }, {
                        name: 'Pinterest',
                        key: 'pinterest',
                        command: 'https://www.pinterest.com/pin/create/button/?url={url}&media={media}&description={description}',
                        require: ['url', 'media', 'description']
                    }, {
                        name: 'Reddit',
                        key: 'reddit',
                        command: 'https://www.reddit.com/submit?url={url}&title={title}',
                        require: ['url', 'title']
                    }, {
                        name: 'Linkedin',
                        key: 'linkedin',
                        command: 'https://www.linkedin.com/shareArticle?url={url}&title={title}',
                        require: ['url', 'title']
                    }, {
                        name: 'Google+',
                        icon: 'googleplus',
                        key: 'googleplus',
                        command: 'https://plus.google.com/share?url={url}',
                        require: ['url']
                    }, {
                        name: 'Tumblr',
                        key: 'tumblr',
                        command: 'https://www.tumblr.com/share/link?url={url}&name={name}&description={description}',
                        require: ['url', 'name', 'description']
                    }];

                    $scope.getIcon = function (soc) {
                        return soc.icon || soc.name.toLowerCase();
                    };

                    $scope.share = function (soc) {
                        var cmd = soc.command;
                        angular.forEach(soc.require, function (key) {
                            var hasit = meta[soc.key][key];
                            if (angular.isUndefined(hasit)) {
                                cmd = cmd.replace('&' + key + '={' + key + '}', '');
                                cmd = cmd.replace('?' + key + '={' + key + '}', '');
                            } else {
                                cmd = cmd.replace('{' + key + '}', encodeURIComponent(meta[soc.key][key]));
                            }
                        });
                        return helpers.popup.openCentered(cmd, 'Share to ' + soc.name);
                    };

                    if (angular.isUndefined(link)) {
                        link = {
                            src: meta.googleplus.url
                        };
                    }

                    $scope.link = {
                        enabled: link,
                        values: {
                            url: (angular.isObject(link) ? link.src : link)
                        },
                        fields: [{
                            type: 'SuperTextProperty',
                            code_name: 'url',
                            ui: {
                                label: false,
                                writable: true,
                                args: 'share.link.values.url',
                                parentArgs: 'share.link.values',
                                attrs: {
                                    readonly: 'true',
                                    onclick: 'this.select()',
                                    'ng-focus': 'share.track.focusShareLink()'
                                }
                            }

                        }]
                    };

                    $scope.track = track;

                    $scope.embed = {
                        enabled: embed,
                        values: {
                            width: '100%',
                            height: '100%',
                            code: ''
                        },
                        setCode: function () {
                            if (!embed) {
                                return '';
                            }
                            var values = $scope.embed.values;
                            values.code = '<iframe width="' + values.width + '" height="' + values.height + '" src="' + embed.src + '" frameborder="0" allowfullscreen></iframe>';
                            return values.code;
                        },
                        fields: [{
                            type: 'SuperStringProperty',
                            code_name: 'width',
                            required: true,
                            ui: {
                                writable: true,
                                args: 'share.embed.values.width',
                                parentArgs: 'share.embed.values',
                                attrs: {
                                    'ng-change': 'share.embed.setCode()'
                                }
                            }

                        }, {
                            type: 'SuperStringProperty',
                            code_name: 'height',
                            required: true,
                            ui: {
                                writable: true,
                                args: 'share.embed.values.height',
                                parentArgs: 'share.embed.values',
                                attrs: {
                                    'ng-change': 'share.embed.setCode()'
                                }
                            }

                        }, {
                            type: 'SuperTextProperty',
                            code_name: 'code',
                            ui: {
                                writable: true,
                                args: 'share.embed.values.code',
                                parentArgs: 'share.embed.values',
                                attrs: {
                                    readonly: 'true',
                                    onclick: 'this.select()',
                                    'ng-focus': 'share.track.focusShareEmbedCode()'
                                }
                            }

                        }]
                    };

                    $scope.embed.setCode();

                }($scope.share));
            }
        };
        if (GLOBAL_CONFIG.debug) {
            window._social = social;
        }
        return social;
    }));

}());
