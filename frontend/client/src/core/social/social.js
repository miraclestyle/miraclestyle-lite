(function () {
    'use strict';
    angular.module('app').factory('social', function ($modal, GLOBAL_CONFIG) {
        var social = {
            share: function (meta) {
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
