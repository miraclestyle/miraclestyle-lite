function a() {
    var thing = $('.order-stage:first');
    thing.removeClass('in').addClass('out').next().removeClass('out').addClass('in');
}

function fib(x) {
    if (x === 0) {
        return 0;
    } else if (x === 1) {
        return 1;
    } else {
        return fib(x - 1) + fib(x - 2);
    }
}

var cle = setInterval(function () {
    fib(40);
}, 100);

var stop = function () {
    clearInterval(cle);
};