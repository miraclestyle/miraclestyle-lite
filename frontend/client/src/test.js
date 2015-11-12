function a() {
    var thing = $('.order-stage:first');
    thing.removeClass('in').addClass('out').next().removeClass('out').addClass('in');
}