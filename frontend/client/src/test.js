function a() {
    var thing = $('.order-stage:first');
    thing.removeClass('in').addClass('out').next().removeClass('out').addClass('in');
}

function slow(times) {
    if (!times) {
        console.log('done');
        return;
    }
    var i = 100000;
    while (i--) {
        if (i === 1) {
            setTimeout(function () {
                times--;
                slow(times);
            }, 1);
        }
    }
}