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

const contributions = document.getElementsByClassName('contribution');

let filterCategories = [];
let filterButtons;
let allButton;

document.addEventListener("DOMContentLoaded", () => {
  filterButtons = document.querySelectorAll(".filter-button");
  allButton = document.querySelector('.category--all');

  filterButtons.forEach(element => {
    const buttonCategory = element.classList[1].replace('category--', '');
    element.addEventListener('click', () => {
      if (buttonCategory != 'all') {
        element.classList.toggle('category--inactive');
      }
      filterContributions(buttonCategory);
    });
  });
});


function updateCounter() {
  contributionCounter = document.querySelector('.contribution-counter');
  numberContributions = document.querySelectorAll('.show').length;
  contributionCounter.innerHTML = numberContributions;
}

/* Shows all contributions and turn all category buttons to inactive */
function showContributions() {
  for (let contribution of contributions) {
    contribution.classList.add('show');
  }

  filterButtons.forEach(element => {
    const buttonCategory = element.classList[1].replace('category--', '');
    if (buttonCategory != 'all') {
      element.classList.add('category--inactive');
    } else {
      element.classList.remove('category--inactive');
    }
  });
}

/* Show all contributions if category === 'all', else toggle category's 
   contributions */
function filterContributions(category) {
  if (category === 'all') {
    filterCategories = [];
    showContributions();
    updateCounter();
    return;
  } 

  allButton.classList.add('category--inactive');

  if (filterCategories.includes(category)) {
    filterCategories = filterCategories.filter(element => {
      return element !== category;
    });
  } else {
    filterCategories.push(category);
  }

  for (let contribution of contributions) {
    contribution.classList.remove('show');
    const contributionCategory = contribution.classList[1];
    if (filterCategories.includes(contributionCategory)) {
      contribution.classList.add('show');
    }
  }
  updateCounter();
}
