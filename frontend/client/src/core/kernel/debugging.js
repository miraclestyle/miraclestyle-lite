if (window.DEBUG) {
    function injector(a) {
        return $(document).injector().get(a);
    }
    function $apply() {
        console.time('$apply');
        var $rootScope = injector('$rootScope');
        $rootScope.$apply();
        console.timeEnd('$apply');
    }
}