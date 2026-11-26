'use strict';
const clock = document.querySelector('[data-target]');
if (clock) {
  const target = Date.parse(clock.dataset.target);
  const rings = [...clock.querySelectorAll('.ring')];
  const label = document.getElementById('clock-label');
  const originalLabel = label.textContent;
  const london = new Intl.DateTimeFormat('en-CA', {year:'numeric', month:'2-digit', day:'2-digit', timeZone:'Europe/London'});
  function update() {
    const seconds = Math.max(0, Math.ceil((target-Date.now())/1000));
    const values = [Math.floor(seconds/86400), Math.floor(seconds/3600)%24, Math.floor(seconds/60)%60, seconds%60];
    const cycles = [365,24,60,60];
    rings.forEach((ring,i) => {
      const text = String(values[i]).padStart(i === 0 ? 1 : 2,'0');
      if (ring.firstElementChild.textContent !== text) {
        ring.firstElementChild.textContent = text;
        ring.style.setProperty('--progress', Math.min(100, 100*values[i]/cycles[i])+'%');
      }
    });
    label.textContent = seconds ? originalLabel : london.format(new Date()) >= clock.dataset.end ? 'Your holiday memories' : 'Your holiday is here';
  }
  update();
  setInterval(update,1000);
}
