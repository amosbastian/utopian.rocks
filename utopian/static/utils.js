let clockTimer;
let votingPowerTimer;

function displayTimeLeft(seconds) {
  const timerDisplay = document.getElementById('time');
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor(seconds % 3600 / 60);
  const remainderSeconds = Math.floor(seconds % 3600 % 60);
  const display = `${hours}:${minutes}:${remainderSeconds < 10 ? '0' : ''}${remainderSeconds}`;
  document.title = display;
  timerDisplay.textContent = display;
}

function rechargeTimer() {
  const rechargeTime = document.getElementById('time').innerHTML;
  const timeArray = rechargeTime.split(':').map(number => parseInt(number, 10));

  const [hours, minutes, seconds] = timeArray;
  const totalSeconds = hours * 3600 + minutes * 60 + seconds;
  displayTimeLeft(totalSeconds);

  const now = Date.now();
  const then = now + totalSeconds * 1000;

  clockTimer = setInterval(() => {
    const secondsLeft = Math.round((then - Date.now()) / 1000);
    if (secondsLeft < 0) {
      clearInterval(clockTimer);
      return;
    }
    displayTimeLeft(secondsLeft);
  }, 1000);
}

function displayVotingPower(currentVotingPower) {
  const votingPowerDisplay = document.getElementById('current-vp');
  votingPowerDisplay.textContent = currentVotingPower.toFixed(2);
}

function votingPower() {
  let currentVotingPower = parseFloat(document.getElementById('current-vp').innerHTML.replace('%', ''));

  votingPowerTimer = setInterval(() => {
    currentVotingPower += 0.01;
    if (currentVotingPower > 100.0) {
      clearInterval(votingPowerTimer);
      return;
    }
    displayVotingPower(currentVotingPower);
  }, 43200);
}

const contributions = document.getElementsByClassName('contribution');
let filterCategories = [];
let filterButtons;
let allButton;

document.addEventListener('DOMContentLoaded', () => {
  filterButtons = document.querySelectorAll('.filter-button');
  allButton = document.querySelector('.category--all');

  filterButtons.forEach((element) => {
    const buttonCategory = element.classList[1].replace('category--', '');
    element.addEventListener('click', () => {
      if (buttonCategory != 'all') {
        element.classList.toggle('category--inactive');
      }
      filterContributions(buttonCategory);
    });
  });
});

/* Shows all contributions and turn all category buttons to inactive */
function showContributions() {
  for (const contribution of contributions) {
    contribution.classList.add('show');
  }

  filterButtons.forEach((element) => {
    const buttonCategory = element.classList[1].replace('category--', '');
    if (buttonCategory !== 'all') {
      element.classList.add('category--inactive');
    } else {
      element.classList.remove('category--inactive');
    }
  });
}


function updateCounter() {
  const contributionCounter = document.querySelector('.contribution-counter');
  const numberContributions = document.querySelectorAll('.show').length;
  contributionCounter.innerHTML = numberContributions;
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
    filterCategories = filterCategories.filter(element => element !== category);
  } else {
    filterCategories.push(category);
  }

  for (const contribution of contributions) {
    contribution.classList.remove('show');
    const contributionCategory = contribution.classList[1];
    if (filterCategories.includes(contributionCategory)) {
      contribution.classList.add('show');
    }
  }
  updateCounter();
}
