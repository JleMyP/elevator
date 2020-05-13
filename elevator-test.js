var DIRECTION_DOWN = -1
var DIRECTION_NONE = 0
var DIRECTION_UP = 1

// Do not implement this, this is just hardware API
function HardwareElevator() {}

HardwareElevator.prototype = {
    moveUp: function () {},    // Start moving elevator up
    moveDown: function () {},  // Start moving elevator down
    stopAndOpenDoors: function () {}, // Stop elevator at current floor and open doors
    getCurrentFloor: function () {},
    getCurrentDirection: function () {}
}

function Elevator () {
    this.hw = new HardwareElevator();
    this.hw.addEventListener("doorsClosed", _.bind(this.onDoorsClosed, this));
    this.hw.addEventListener("beforeFloor", _.bind(this.onBeforeFloor, this));
}

Elevator.prototype = {
    onDoorsClosed: function (floor) {
    },

    onBeforeFloor: function (floor, direction) {
    },

    floorButtonPressed: function (floor, direction) {
    },

    cabinButtonPressed: function (floor) {
    }
}
