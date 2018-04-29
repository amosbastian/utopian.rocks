var substringMatcher = function(strs) {
  return function findMatches(q, cb) {
    var matches, substringRegex;

    // an array that will be populated with substring matches
    matches = [];

    // regex used to determine if a string contains the substring `q`
    substrRegex = new RegExp(q, 'i');

    // iterate through the pool of strings and for any string that
    // contains the substring `q`, add it to the `matches` array
    $.each(strs, function(i, str) {
      if (substrRegex.test(str)) {
        matches.push(str);
      }
    });

    cb(matches);
  };
};

$('#community-managers .typeahead').typeahead({
  hint: true,
  highlight: true,
  minLength: 1
},
{
  name: 'manager',
  source: substringMatcher(managers)
});

$('#moderators .typeahead').typeahead({
  hint: true,
  highlight: true,
  minLength: 1
},
{
  name: 'moderator',
  source: substringMatcher(moderators)
});

$('#contributors .typeahead').typeahead({
  hint: true,
  highlight: true,
  minLength: 1
},
{
  name: 'contributor',
  source: substringMatcher(contributors)
});

$('#projects .typeahead').typeahead({
  hint: true,
  highlight: true,
  minLength: 1
},
{
  name: 'project',
  source: substringMatcher(projects)
});

$('#search .typeahead').typeahead({
  hint: true,
  highlight: true,
  minLength: 1
},
{
  name: 'manager',
  source: substringMatcher(managers),
  templates: {
    header: '<p class="search-dataset">Community managers</p>'
  }
},
{
  name: 'moderator',
  source: substringMatcher(moderators),
  templates: {
    header: '<p class="search-dataset">Moderators</p>'
  }
}
,{
  name: 'contributor',
  source: substringMatcher(contributors),
  templates: {
    header: '<p class="search-dataset">Contributors</p>'
  }
}
,{
  name: 'project',
  source: substringMatcher(projects),
  templates: {
    header: '<p class="search-dataset">Projects</p>'
  }
});
