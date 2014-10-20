!function(r, Backbone, $, _) {
  'use strict'

  var exports = r.liveupdate.activity = {}

  var INTERVAL = 10 * 60 * 1000

  exports.ActivityTracker = Backbone.View.extend({
    initialize: function() {
      this.reportsSent = 0
      this.reportPending = false

      $(document).on('visibilitychange', $.proxy(this.onVisibilityChange, this))
      this.reportActivity()
    },

    onVisibilityChange: function() {
      if (!document.hidden && this.reportPending) {
        this.reportActivity()
      }
    },

    reportActivity: function() {
      if (document.hidden) {
        this.reportPending = true
        return
      }

      var pixel
      var delay

      pixel = new Image()
      pixel.src = '//' + r.config.liveupdate_pixel_domain +
        '/live/' + r.config.liveupdate_event + '/pixel.png' +
        '?rand=' + Math.random()
      this.reportsSent += 1
      this.reportPending = false

      delay = Math.floor(INTERVAL - (INTERVAL * Math.random() / 2))
      setTimeout(_.bind(this.reportActivity, this), delay)
    },
  })
}(r, Backbone, jQuery, _)
