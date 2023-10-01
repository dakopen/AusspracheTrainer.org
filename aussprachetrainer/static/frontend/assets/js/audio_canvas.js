const canvas = document.getElementById("visualizer");
const ctx = canvas.getContext("2d");

const audioContext = new AudioContext();
const analyser = audioContext.createAnalyser();
analyser.fftSize = 2048;
const bufferLength = analyser.frequencyBinCount;
const dataArray = new Uint8Array(bufferLength);

let mediaRecorder;
let chunks = [];

const startRecording = () => {
  chunks = [];
  mediaRecorder = new MediaRecorder(stream);
  mediaRecorder.addEventListener("dataavailable", (event) => {
    chunks.push(event.data);
  });
  mediaRecorder.start();
};

const stopRecording = () => {
  mediaRecorder.stop();
};

let stream;
navigator.mediaDevices.getUserMedia({ audio: true })
  .then((userStream) => {
    stream = userStream;
    const audio = document.createElement("audio");
    audio.srcObject = stream;
    audio.play();
    const source = audioContext.createMediaStreamSource(stream);
    source.connect(analyser);
  })
  .catch((error) => {
    console.error(error);
  });

let x = canvas.width / 2 - document.getElementById("record-button").offsetWidth / 2;

let lastMeanFrequency = 0;
let animationFrameId;
let counter = 0;

let isRecording = false;

// Event listener for record button
const recButton = document.getElementById("record-button");

recButton.addEventListener("click", () => {
  isRecording = !isRecording;
  if (isRecording) {
    startRecording();
    animationFrameId = requestAnimationFrame(draw);
    recButton.innerText = 'Stop';
  } else {
    stopRecording();
    cancelAnimationFrame(animationFrameId);
    recButton.innerText = 'Record';
  }
});

function draw() {
  if (!isRecording) return;
  
  const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.putImageData(imageData, -1, 0);
  
  analyser.getByteFrequencyData(dataArray);
  const meanFrequency = dataArray.reduce((a, b) => a + b) / bufferLength;
  
  const smoothFrequency = (lastMeanFrequency + meanFrequency) / 2;

  if (counter <= 1) {
    const yHeight = Math.max((smoothFrequency / 64) * canvas.height / 2, 1);
    const y = canvas.height / 2 - yHeight;
    const yMirrored = canvas.height / 2 + yHeight;

    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.lineTo(x, yMirrored);
    ctx.strokeStyle = 'var(--lila)';
    ctx.stroke();
  } else if (counter <= 3) {
    // Gap
  } else {
    counter = 0;
  }

  counter++;
  lastMeanFrequency = meanFrequency;
  animationFrameId = requestAnimationFrame(draw);
}