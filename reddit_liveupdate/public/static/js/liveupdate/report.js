!function(r, Backbone, $, _) {
  'use strict'

  var exports = r.liveupdate.report = {}

  exports.ReportForm = Backbone.View.extend({
    el: '#report',

    events: {
      'click .report-button': 'onOpen',
      'click .cancel': 'onCancel',
      'change input[type=radio]': 'onReportTypeSelected',
      'submit': 'onSubmit',
    },

    initialize: function() {
      this.$button = this.$el.children('.report-button')
      this.$form = this.$el.children('form')
    },

    _setFormVisibility: function(formVisible) {
      this.$button.toggle(!formVisible)
      this.$form.toggle(formVisible)
    },

    onOpen: function() {
      this._setFormVisibility(true)
    },

    onCancel: function(ev) {
      this._setFormVisibility(false)
      ev.preventDefault()
    },

    onReportTypeSelected: function() {
      this.$('[type=submit]').prop('disabled', false)
    },

    onSubmit: function(ev) {
      var _this = this
      var $radio = this.$el.find('input[type=radio]:checked')
      var reportType = $radio.val()
      var reportDescription = $radio.parent().text()

      this.$el.text(r._('submitting report…'))

      r.ajax({
        type: 'POST',
        dataType: 'json',
        url: '/api/live/' + r.config.liveupdate_event + '/report',
        data: {
          'type': reportType,
        },
      }).then(function() {
        _this.$el.html(r.templates.make('liveupdate/reported', {
          text: r._('you reported this stream for: %(violation)s').format({
            violation: reportDescription,
          }),
        }))
      })

      ev.preventDefault()
    },
  })
}(r, Backbone, jQuery, _)
