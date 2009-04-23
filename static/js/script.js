$(function(){
  $('#search-form').submit(function(){
    document.location.href = $(this).attr('action')+encodeURIComponent($('#q').val());
    return false;
  });
  $('#status-form').submit(function(){
    var status_form = $('#status-form');
    status_form.css('display', 'none');
    status_form.after('Status is being updated...');
    return true;
  });
});

function get_tweets(elt) {
  var url = $(elt).attr('href');
  $.get(url, function(data) {
    $('#content').html(data);
  });
}

function reply(in_reply_to_status_id, in_reply_to) {
  showStatusBox();
  var textarea = $('#status');
  textarea.focus();
  textarea.html('@' + in_reply_to + ' ');
  $('#in_reply_to_status_id').remove();
  var hidden_field = $('<input>').attr('id', 'in_reply_to_status_id');
  hidden_field.attr('name', 'in_reply_to_status_id');
  hidden_field.attr('type', 'hidden');
  hidden_field.attr('value', in_reply_to_status_id);
  textarea.after(hidden_field);
}

function showStatusBox() {
  $('#status').empty();
  $('#status-box').hide().show();
}