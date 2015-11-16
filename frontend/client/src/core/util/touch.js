/*!
 * jQuery UI Touch Punch 0.2.3
 *
 * Copyright 2011–2014, Dave Furfero
 * Dual licensed under the MIT or GPL Version 2 licenses.
 *
 * Depends:
 *  jquery.ui.widget.js
 *  jquery.ui.mouse.js
 */
(function ($) {

  // Detect touch support
  $.support.touch = 'ontouchend' in document || 'onpointerdown' in document || 'onMSPointerDown' in document;
 
  // Ignore browsers without touch support
  if (!$.support.touch) {
    return;
  }

  var mouseProto = $.ui.mouse.prototype,
      _mouseInit = mouseProto._mouseInit,
      _mouseDestroy = mouseProto._mouseDestroy,
      startX, startY,
      touchHandled,
      pointer,
      lastPointer,
      getEventPoint,
      updatePointerState,
      makeStartPointer,
      typesMatch;

  /**
   * Simulate a mouse event based on a corresponding touch event
   * @param {Object} event A touch event
   * @param {String} simulatedType The corresponding mouse event
   */
  function simulateMouseEvent (event, simulatedType) {

    // Ignore multi-touch events
    if (event.originalEvent.touches.length > 1) {
      return;
    }

    event.preventDefault();

    var touch = event.originalEvent.changedTouches[0],
        simulatedEvent = document.createEvent('MouseEvents');
    
    // Initialize the simulated mouse event using the touch event's coordinates
    simulatedEvent.initMouseEvent(
      simulatedType,    // type
      true,             // bubbles                    
      true,             // cancelable                 
      window,           // view                       
      1,                // detail                     
      touch.screenX,    // screenX                    
      touch.screenY,    // screenY                    
      touch.clientX,    // clientX                    
      touch.clientY,    // clientY                    
      false,            // ctrlKey                    
      false,            // altKey                     
      false,            // shiftKey                   
      false,            // metaKey                    
      0,                // button                     
      null              // relatedTarget              
    );
    simulatedEvent.jqueryui = true;
    // Dispatch the simulated event to the target element
    var target = event.target;
    // Dispatch the simulated event to the target element
    if (simulatedType === 'mousemove') {
      // Special handling for mouse move: fire on element at the current location instead:
      var elementAtPoint = document.elementFromPoint(event.clientX, event.clientY);
      if (elementAtPoint !== null) {
          target = elementAtPoint;
      }
    }

    target.dispatchEvent(simulatedEvent);
  }

  mouseProto.state = {};

  /**
   * Handle the jQuery UI widget's touchstart events
   * @param {Object} event The widget element's touchstart event
   */
  mouseProto._touchStart = function (event) {

    if (!getEventPoint) {
      getEventPoint = window.touchHelpers.getEventPoint;
      updatePointerState = window.touchHelpers.updatePointerState;
      makeStartPointer = window.touchHelpers.makeStartPointer;
      typesMatch = window.touchHelpers.typesMatch;
    }

    var self = this;

    // Ignore the event if another widget is already being handled
    if (touchHandled || !self._mouseCapture(event.originalEvent.changedTouches[0])) {
      return;
    }

    // Set the flag to prevent other widgets from inheriting the touch event
    touchHandled = true;

    self._startedMove = event.timeStamp;

    // Track movement to determine if interaction was a click
    self._touchMoved = false;

    // Track starting event
    startX = event.originalEvent.touches[0].screenX;
    startY = event.originalEvent.touches[0].screenY;

    // Simulate the mouseover event
    simulateMouseEvent(event, 'mouseover');

    // Simulate the mousemove event
    simulateMouseEvent(event, 'mousemove');

    // Simulate the mousedown event
    simulateMouseEvent(event, 'mousedown');

    if (pointer || self.state.isRunning) {
      return;
    }


    self.state.isRunning = true;

    var now = +Date.now();

    // iOS & old android bug: after a touch event, a click event is sent 350 ms later.
    // If <400ms have passed, don't allow an event of a different type than the previous event
    if (lastPointer && !typesMatch(event, lastPointer) && (now - lastPointer.endTime < 1500)) {
      return;
    }

    pointer = makeStartPointer(event);
  };

  mouseProto._touchDistanceMet = function (pointer) {
    return pointer.distance >= this.options.distance;
  };

  /**
   * Handle the jQuery UI widget's touchmove events
   * @param {Object} event The document's touchmove event
   */
  mouseProto._touchMove = function (event) {

    var self = this;

    if (!(!pointer || !typesMatch(event, pointer))) {
      updatePointerState(event, pointer);
    }

    // Ignore event if not handled
    if (!touchHandled) {
      return;
    }

    // Ignore event if no change in position from starting event
    var endX = event.originalEvent.touches[0].screenX,
        endY = event.originalEvent.touches[0].screenY;

    if (startX === endX && startY === endY) {
      self._touchMoved = false;
      return;
    }
 
    // Interaction was not a click
    self._touchMoved = true;

    // Simulate the mousemove event
    simulateMouseEvent(event, 'mousemove');
  };

  /**
   * Handle the jQuery UI widget's touchend events
   * @param {Object} event The document's touchend event
   */
  mouseProto._touchEnd = function (event) {

    var self = this;

    if (!(!pointer || !typesMatch(event, pointer))) {
        updatePointerState(event, pointer);
        pointer.endTime = +Date.now();
    }


    // Ignore event if not handled
    if (!touchHandled) {
      lastPointer = pointer;
      pointer = null;
      return;
    }

    // Simulate the mouseup event
    simulateMouseEvent(event, 'mouseup');

    // Simulate the mouseout event
    simulateMouseEvent(event, 'mouseout') || event;

    if (!self._touchMoved || !self._touchDistanceMet(pointer) && self.state.isRunning) {
      // Simulate the click event
      simulateMouseEvent(event, 'click');
    }

    self._touchMoved = false;

    // Unset the flag to allow other widgets to inherit the touch event
    touchHandled = false;

    lastPointer = pointer;
    pointer = null;

    self.state.isRunning = false;
  };

  /**
   * A duck punch of the $.ui.mouse _mouseInit method to support touch events.
   * This method extends the widget with bound touch event handlers that
   * translate touch events to mouse events and pass them to the widget's
   * original mouse event handling methods.
   */
  mouseProto._mouseInit = function () {
    
    var self = this;

    // Delegate the touch handlers to the widget's element
    self.element.bind({
      touchstart: $.proxy(self, '_touchStart'),
      touchmove: $.proxy(self, '_touchMove'),
      touchend: $.proxy(self, '_touchEnd')
    });

  if(msieversion()){
    self.element.css('-ms-touch-action', 'none'); //This will be required only in case of the IE
  }

    // Call the original $.ui.mouse init method
    _mouseInit.call(self);
  };

  /**
   * Remove the touch event handlers
   */
  mouseProto._mouseDestroy = function () {
    
    var self = this;

    self._touchMoved = false;

    // Delegate the touch handlers to the widget's element
    self.element.unbind({
      touchstart: $.proxy(self, '_touchStart'),
      touchmove: $.proxy(self, '_touchMove'),
      touchend: $.proxy(self, '_touchEnd')
    });

    // Call the original $.ui.mouse destroy method
    _mouseDestroy.call(self);
  };

})(jQuery);