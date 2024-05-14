<script>
	import { onMount, onDestroy } from 'svelte';

	let videoElement;
	let canvasElement;
	let stream;
	let detectionResults = [];

	const colorMap = {
		person: 'red',
		bus: 'blue',
		car: 'green',
		// Add more object classes and their colors here
	};

	async function startWebcam() {
		try {
			const constraints = {
				video: {
					width: { ideal: 1280 },  // Set your desired width here
					height: { ideal: 720 },  // Set your desired height here
					facingMode: "user" // Use "environment" for back camera on mobile devices
				}
			};
			stream = await navigator.mediaDevices.getUserMedia(constraints);
			videoElement.srcObject = stream;
			videoElement.addEventListener('loadedmetadata', setCanvasSize);
			await videoElement.play();
			captureFrames();
			drawCanvas();
		} catch (error) {
			console.error('Error accessing webcam:', error);
		}
	}

	function setCanvasSize() {
		if (videoElement.videoWidth && videoElement.videoHeight) {
			canvasElement.width = videoElement.videoWidth;
			canvasElement.height = videoElement.videoHeight;
			canvasElement.style.width = '100%';
			canvasElement.style.height = 'auto';
			console.log(`Canvas size set to: ${canvasElement.width}x${canvasElement.height}`);
		}
	}

	function captureFrames() {
		setInterval(async () => {
			const context = canvasElement.getContext('2d');
			context.drawImage(videoElement, 0, 0, canvasElement.width, canvasElement.height);
			const imageData = canvasElement.toDataURL('image/jpeg');
			await sendFrameToBackend(imageData);
		}, 1000); // Adjust the interval as needed
	}

	async function sendFrameToBackend(imageData) {
		try {
			const response = await fetch('http://localhost:8000/detect', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({ image: imageData })
			});
			const data = await response.json();
			detectionResults = data;
		} catch (error) {
			console.error('Error sending frame to backend:', error);
		}
	}

	function drawDetections() {
		const context = canvasElement.getContext('2d');
		context.clearRect(0, 0, canvasElement.width, canvasElement.height);
		context.drawImage(videoElement, 0, 0, canvasElement.width, canvasElement.height);

		detectionResults.forEach(result => {
			const color = colorMap[result.object] || 'yellow'; // Default to yellow if object class not in colorMap
			context.strokeStyle = color;
			context.lineWidth = 2;
			context.strokeRect(result.xmin, result.ymin, result.xmax - result.xmin, result.ymax - result.ymin);

			context.font = '16px Arial';
			context.fillStyle = color;
			const text = `${result.object} (${(result.confidence * 100).toFixed(1)}%)`;
			context.fillText(text, result.xmin, result.ymin > 20 ? result.ymin - 5 : result.ymin + 20);
		});
	}

	function drawCanvas() {
		const context = canvasElement.getContext('2d');

		function draw() {
			context.clearRect(0, 0, canvasElement.width, canvasElement.height);
			context.drawImage(videoElement, 0, 0, canvasElement.width, canvasElement.height);
			drawDetections();
			requestAnimationFrame(draw);
		}

		requestAnimationFrame(draw);
	}

	onMount(() => {
		startWebcam();
	});

	onDestroy(() => {
		if (stream) {
			stream.getTracks().forEach(track => track.stop());
		}
	});
</script>

<main>
	<h1>People Watching</h1>
	<video bind:this={videoElement} autoplay playsinline style="display: none;"></video>
	<canvas bind:this={canvasElement}></canvas>
</main>

<style>
	main {
		text-align: center;
		padding: 1em;
	}

	canvas {
		width: 100%;  /* Ensures responsiveness while maintaining high resolution */
		border: 1px solid black; /* Optional, adds border around the canvas */
	}

	h1 {
		color: #ff3e00;
		text-transform: lowercase;
		font-size: 2em;
		font-weight: 100;
	}

	.detection {
		margin: 1em 0;
		font-size: 1.2em;
		color: #333;
	}
</style>
