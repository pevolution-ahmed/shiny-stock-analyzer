
// Define mojs shapes and thire properties
const burst1 = new mojs.Burst({
  left: 0, top: 0,
  count: 7,
  radius: { 50: 250 },
  children: {
    fill: 'white',
    shape: 'polygon',
    stroke: { 'white': '#A50710' },
    strokeWidth: 4,
    radius: 'rand(30, 60)',
    radiusY: 0,
    scale: { 1: 0 },
    pathScale: 'rand(.5, 1)',
    degree: 360,
    isForce3d: true
  }
});

const COLORS = {
  RED: '#FD5061',
  YELLOW: '#FFCEA5',
  BLACK: '#29363B',
  WHITE: 'white',
  VINOUS: '#A50710'
}

const DURATION = 500;
const constrain = document.body.querySelector('#js-constrain');

const showBase = new mojs.Shape({
  fill: 'none',
  parent: constrain,
  radius: 20,
  x: { [-150]: 0, easing: 'cubic.out' },
  y: { [90]: 0, easing: 'cubic.out' },
  isForce3d: true,
  duration: DURATION + 400
});

const circle = new mojs.Shape({
  fill: COLORS.WHITE,
  parent: showBase.el,
  radius: 50,
  scale: { .4: 1 },
  duration: 650,
  opacity: { .5: 0 },
  delay: DURATION + 100,
  isForce3d: true,
  easing: 'cubic.out'
});

const showUp = new mojs.Shape({
  fill: 'none',
  stroke: COLORS.WHITE,
  parent: showBase.el,
  radius: { 0: 10 },
  angle: { 560: 270 },
  strokeWidth: { 0: 22, easing: 'cubic.inout' },
  strokeDasharray: '100%',
  strokeDashoffset: { '-100%': '0%', easing: 'cubic.in' },
  strokeLinecap: 'round',
  duration: DURATION,
})
  .then({
    scale: .75,
    duration: 250
  })
  .then({
    scale: 1,
    duration: 300
  })
  .then({
    scale: .5,
    duration: 300
  });

const angle = 250;
const bubbles = new mojs.Burst({
  parent: showUp.el,
  count: 3,
  degree: 15,
  angle: { [90 + angle]: 280 + angle },
  y: { 0: -15 },
  x: { 0: 35 },
  radius: { 0: 70 },
  timeline: { delay: 300 },
  children: {
    radius: [10, 7],
    fill: COLORS.WHITE,
    pathScale: 'rand(.5, 1.5)',
    duration: 600,
    isForce3d: true,
  }
});

const angle2 = -340;
const bubbles2 = new mojs.Burst({
  parent: showUp.el,
  count: 3,
  degree: 25,
  angle: { [90 + angle2]: 280 + angle2 },
  y: { 0: 15 },
  radius: { 0: 50 },
  timeline: { delay: 0 },
  children: {
    radius: [10, 7],
    fill: COLORS.WHITE,
    // scale:        { 1 : 0 },
    pathScale: 'rand(.5, 1.5)',
    duration: 600,
    isForce3d: true,
  }
});

function waitForElm(selector) {
  return new Promise(resolve => {
    if (document.querySelector(selector)) {
      return resolve(document.querySelector(selector));
    }

    const observer = new MutationObserver(mutations => {
      if (document.querySelector(selector)) {
        resolve(document.querySelector(selector));
        observer.disconnect();
      }
    });

    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
  });
}



const timeline = new mojs.Timeline({ delay: 200, speed: .5, isSoftHide: true, });

timeline
  .add(
    showBase, circle, showUp,
    bubbles, bubbles2
  );

  // Wait for the stock Ichimoku widget to appear, then pause the animation by playing it backward.
waitForElm("#stock_Ichimoku_widget  .user-select-none").then((elm) => {
  timeline.replayBackward()

});
window.addEventListener('load', function (e) {
  timeline.replay()
})

document.addEventListener('click', function
  (e) {
  burst1.
    tune({ x: e.pageX, y: e.pageY }).
    generate().
    replay();

});