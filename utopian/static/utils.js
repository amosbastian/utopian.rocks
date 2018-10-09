var seconds;
var temp;

function countdown() {
  time = document.getElementById('time').innerHTML;
  timeArray = time.split(':')
  seconds = timeToSeconds(timeArray);
  if (seconds == '') {
    temp = document.getElementById('time');
    temp.innerHTML = "00:00:00";
    return;
  }
  seconds--;
  temp = document.getElementById('time');
  temp.innerHTML = secondsToTime(seconds);
  wait = setTimeout(countdown, 1000);
}

function timeToSeconds(timeArray) {
  var minutes = (timeArray[0] * 60) + (timeArray[1] * 1);
  var seconds = (minutes * 60) + (timeArray[2] * 1);
  return seconds;
}

function secondsToTime(secs) {
  var hours = Math.floor(secs / (60 * 60));
  hours = hours < 10 ? '0' + hours : hours;
  var divisor_for_minutes = secs % (60 * 60);
  var minutes = Math.floor(divisor_for_minutes / 60);
  minutes = minutes < 10 ? '0' + minutes : minutes;
  var divisor_for_seconds = divisor_for_minutes % 60;
  var seconds = Math.ceil(divisor_for_seconds);
  seconds = seconds < 10 ? '0' + seconds : seconds;
  return hours + ':' + minutes + ':' + seconds;
}

function votingPower() {
  let vp = parseFloat(document.getElementById('current-vp').innerHTML.replace("%", ""));
  vp += 0.01
  if (vp > 100) {
    vp = 100.0;
  }
  let temp = document.getElementById('current-vp');
  temp.innerHTML = vp.toFixed(2);
  var wait = setTimeout(votingPower, 43200);
}

function filterContributions(category) {
  let contributions = document.getElementsByClassName('contribution');
  let temporaryCategory = category;
  if (temporaryCategory === 'all') { 
    temporaryCategory = '';
  }
  for (let contribution of contributions) {
    contribution.classList.remove('show');
    if (contribution.classList.contains(temporaryCategory) || temporaryCategory === '') {
      contribution.classList.add('show');
    }
  }

  let filterButtons = document.getElementsByClassName('filter-button');
  for (let button of filterButtons) {
    if (!button.classList.contains('category--inactive')) {
      button.classList.add('category--inactive');
    }

    if (button.classList.contains('category--' + category)) {
      button.classList.remove('category--inactive');
    }
  }
}
