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
  name: 'managers',
  source: substringMatcher(managers)
});

$('#moderators .typeahead').typeahead({
  hint: true,
  highlight: true,
  minLength: 1
},
{
  name: 'moderators',
  source: substringMatcher(moderators)
});

$('#contributors .typeahead').typeahead({
  hint: true,
  highlight: true,
  minLength: 1
},
{
  name: 'contributors',
  source: substringMatcher(contributors)
});

$('#projects .typeahead').typeahead({
  hint: true,
  highlight: true,
  minLength: 1
},
{
  name: 'projects',
  source: substringMatcher(projects)
});