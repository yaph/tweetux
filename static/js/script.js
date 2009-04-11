$(function(){
  if (top !== self) top.location.href = self.location.href;
});

function get_tweets(elt) {
  var url = $(elt).attr('href');
  $.get(url, function(data) {
    $('#content').html(data);
  });
}