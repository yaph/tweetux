function get_tweets(elt) {
  var url = $(elt).attr('href');
  $.get(url, function(data) {
    $('#content').html(data);
  });
}