compare = function (sampler) {

    'use strict';

    var $ = window.jQuery || window.$;

    if (!$ && window.angular) {
        $ = angular.element;
    }

    function gets(element) {
        var styles = [];

        // The DOM Level 2 CSS way
        //
        if (window.getComputedStyle) {
            var cs = window.getComputedStyle(element, ''),
                i = 0,
                k;
            if (cs.length !== 0) {
                for (i = 0; i < cs.length; i++) {
                    styles.push([cs.item(i), cs.getPropertyValue(cs.item(i))]);
                }
            } else {
                for (k in cs) {
                    if (cs.hasOwnProperty(k)) {
                        styles.push([k, cs[k]]);
                    }
                }
            }
        } else if (element.currentStyle) {
            var cs = element.currentStyle;
            for (var k in cs) {
                styles.push([k, cs[k]]);
            }
        }

        return styles;
    }

    if (!document.getElementById('jqueryget') || !window.jQuery && false) {
        var script = document.createElement('script');
        script.src = 'https://ajax.googleapis.com/ajax/libs/jquery/2.1.3/jquery.min.js';
        script.id = 'jqueryget';
        document.body.appendChild(script);
    }

    function comparator() {
        var c = document.getElementById('comparator');
        if (!c) {
            $(document.body).append('<textarea id="comparator"></textarea>');
        }
        return document.getElementById('comparator');
    }


    setTimeout(function () {
        if (!sampler) {
            $(document.body).append('<style>#comparator {z-index: 4000; height: 20px; bottom: 0px;}</style>');
        }
        $(document).on('keydown', function (e) {
            if (e.ctrlKey && e.which === 68 && g0()) {
                var what = g0(),
                    spawn = JSON.stringify(what ? gets(what) : null, null, '\t');
                if (sampler) {
                    comparator().value = spawn;
                    comparator().select();
                    console.log('target element', what, 'copying', document.execCommand('copy'));
                } else {
                    var list1 = JSON.parse(spawn),
                        list2 = JSON.parse(comparator().value || null),
                        maplist1 = {},
                        maplist2 = {},
                        keys = [],
                        diff = {};

                    $.each(list1, function () {
                        maplist1[this[0]] = this[1];
                        if (keys.indexOf() === -1) {
                            keys.push(this[0]);
                        }
                    });
                    $.each(list2, function () {
                        maplist2[this[0]] = this[1];
                        if (keys.indexOf() === -1) {
                            keys.push(this[0]);
                        }
                    });

                    $.each(keys, function () {
                        if (maplist1[this] !== maplist2[this]) {
                            diff[this] = '' + maplist1[this] + ' | ' + maplist2[this];
                        }
                    });

                    console.log('target element', what, 'found differences in', diff);
                }
            }
        });
    }, 2000);
}

g0 = function () {
    return $0;
}
