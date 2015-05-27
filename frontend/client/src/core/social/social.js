(function () {
    'use strict';
    angular.module('app').factory('social', function ($modal, GLOBAL_CONFIG) {
        var social = {
            share: function (meta, embed) {
                $modal.open({
                    templateUrl: 'core/social/share.html',
                    controller: function ($scope) {
                        $scope.socials = [{
                            name: 'Facebook',
                            key: 'facebook',
                            command: 'https://www.facebook.com/sharer.php?s=100&p[url]={p[url]}&p[images][0]={p[images][0]}&p[title]={p[title]}&p[summary]={p[summary]}',
                            require: ['href']
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
                            return '/client/dist/static/social/' + (soc.icon || soc.name.toLowerCase()) + '.png';
                        };

                        $scope.share = function (soc) {
                            var w = $(window).width() / 1.3,
                                h = $(window).height() / 1.3,
                                left = (screen.width / 2) - (w / 2),
                                top = (screen.height / 2) - (h / 2),
                                link = soc.command,
                                popup;
                            angular.forEach(soc.require, function (key) {
                                var hasit = meta[soc.key][key];
                                if (angular.isUndefined(hasit)) {
                                    link = link.replace('&' + key + '={' + key + '}', '');
                                    link = link.replace('?' + key + '={' + key + '}', '');
                                } else {
                                    link = link.replace('{' + key + '}', encodeURIComponent(meta[soc.key][key]));
                                }
                            });
                            popup = window.open(link, 'Share to ' + soc.name, 'toolbar=no, location=no, directories=no, status=no, menubar=no, scrollbars=1, resizable=no, copyhistory=no, width=' + w + ', height=' + h + ', top=' + top + ', left=' + left);
                            popup.focus();
                            return popup;
                        };

                        $scope.container = {};

                        $scope.embed = {
                            enabled: embed,
                            values: {
                                width: '100%',
                                height: '100%',
                                code: ''
                            },
                            setCode: function () {
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
                                    args: 'embed.values.width',
                                    parentArgs: 'embed.values',
                                    attrs: {
                                        'ng-change': 'embed.setCode()'
                                    }
                                }

                            }, {
                                type: 'SuperStringProperty',
                                code_name: 'height',
                                required: true,
                                ui: {
                                    writable: true,
                                    args: 'embed.values.height',
                                    parentArgs: 'embed.values',
                                    attrs: {
                                        'ng-change': 'embed.setCode()'
                                    }
                                }

                            }, {
                                type: 'SuperTextProperty',
                                code_name: 'code',
                                ui: {
                                    writable: true,
                                    args: 'embed.values.code',
                                    parentArgs: 'embed.values',
                                    attrs: {
                                        readonly: 'true',
                                        onclick: 'this.select()'
                                    }
                                }

                            }]
                        };

                        $scope.embed.setCode();
                        $scope.close = $scope.$close;
                    }
                });
            }
        };
        if (GLOBAL_CONFIG.debug) {
            window._social = social;
        }
        return social;
    });

}());
