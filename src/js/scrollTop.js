/*
 * Fix position of row with toc and help when scrolling.
 */
$(function () {

    var container = $("#scroll-fixed-top");
    var headerHeight = $('.page-header').height();

    $(window).scroll(function () {
        if ($(window).scrollTop() >= headerHeight) {
            container.css({"position": "fixed"});
        } else {
            container.css({"position": "relative"});
        }
    });
});
