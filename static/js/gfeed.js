google.load("feeds", "1");

function lookupDone(result) {
  // Make sure we didn't get an error.
  if (!result.error && result.url != null) {
    var url = result.url;
    var feed = new google.feeds.Feed(url);
    // Calling load sends the request off.  It requires a callback function.
    feed.load(feedLoaded);
  }
}

// Our callback function, for when a feed is loaded.
function feedLoaded(result) {
  if (!result.error) {
    // Grab the container we will put the results into
    var container = document.getElementById('user_feed');
    container.innerHTML = '';

    var html = '<h4>Recent Posts</h4><ul>';
    for (var i = 0; i < result.feed.entries.length; i++) {
      var entry = result.feed.entries[i];
      html += '<li><a href="' + entry.link + '">' + entry.title + '</a></li>';
    }
    html += '</ul>';
    container.innerHTML = html;
  }
}

function OnLoad() {
  // The page to lookup a feed on.
  var url = document.getElementById('user_url').innerHTML;

  // Go find it!  Call lookupDone when the search is complete.
  google.feeds.lookupFeed(url, lookupDone);
}

google.setOnLoadCallback(OnLoad);