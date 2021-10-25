/*
 * Place a 'target' on an image - if the image is cropped (detail header image)
 * the focus of the image is on display.
 * Note: The image cropping library expects the focus point in percent, while
 * everything on the DOM (with this plugin) is calculated in pixels.
 */
(function ($) {

    var settings = null;

    $.addFocusPoint = function (options) {
        var defaults = {
            button: $("#set-target"),
            cross: $("#cross"),
            inputField: $("#id_qg_image-0-image_target"),
            imageContainer: $(".image-preview"),
            container: $(".tech-figure-container")
        };
        settings = $.extend( {}, defaults, options );

        settings.container.hover(
            function () {
                settings.button.show();
                showTarget();
            }, function () {
                settings.button.hide()
            }
        );
    };

    function showTarget() {
        // show 'target' indicator for focus point and register click events.
        settings.button.click(function (event) {
            event.preventDefault();
            settings.cross.css("visibility", "visible");
            settings.imageContainer.bind("click", function (event) {
                setTarget($(this), event);
            });
            // initial position 'target' if available.
            if (settings.inputField.val().length != 0) {
                // percent to pixels
                var splitCoords = settings.inputField.val().split(',');
                var x = getPixels(settings.imageContainer.width(), parseInt(splitCoords[0]));
                var y = getPixels(settings.imageContainer.height(), parseInt(splitCoords[1]));
                setPosition(x, y);
            }
            // show image in full height
            settings.imageContainer.css("max-height", "");
            settings.container.css("max-height", "");
        });
    }

    function setPosition(x, y) {
        // set position of the 'target' in pixels.
        settings.cross.css({"left": x, "top": y});
        settings.cross.data("left", x);
        settings.cross.data("top", y);
    }

    function setTarget(element, event) {
        // calculate offset
        var x = event.pageX - element.offset().left;
        var y = event.pageY - element.offset().top;
        setPosition(x, y);
        // set target in percent as value
        settings.inputField.val(
            getPercent(settings.imageContainer.width(), x) + ","  +
            getPercent(settings.imageContainer.height(), y)
        );
    }

    function getPercent(base, x) {
        return Math.round(x * 100 / base);
    }

    function getPixels(base, x) {
        return x * base / 100;
    }
}(jQuery));
