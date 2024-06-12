<script>
    import { onMount } from 'svelte';

    let USE_WEBCAM = false;

    let videoElement;
    let snapshotElement;
    let annotationsElement;
    let stream;
    let interval;
    let detectionResults = [];

    const colorMap = {
		otter: 'red',
		ball: 'orange',
		person: 'green',
		// Add more object classes and their colors here
	};

    onMount(() => {
        videoElement.addEventListener('play', () => {
            interval = setInterval(captureFrame, 500); // Capture frame every 5 seconds
        });

        videoElement.addEventListener('pause', () => {
            clearInterval(interval);
        });

        videoElement.addEventListener('ended', () => {
            clearInterval(interval);
        });

        if (USE_WEBCAM) {
			startWebcam();
		} else {
			loadPredefinedVideo();
		}
    });

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
		} catch (error) {
			console.error('Error accessing webcam:', error);
		}
	}

    function setCanvasSize() {
		if (videoElement.videoWidth && videoElement.videoHeight) {
			annotationsElement.width = videoElement.videoWidth;
			annotationsElement.height = videoElement.videoHeight;
            snapshotElement.width = videoElement.videoWidth;
			snapshotElement.height = videoElement.videoHeight;
			console.log(`Canvas size set to: ${annotationsElement.width}x${annotationsElement.height}`);
		}
	}

    function loadPredefinedVideo() {
        videoElement.src = '/2024-05-14_13_30_highlight.mp4';
        videoElement.addEventListener('loadedmetadata', setCanvasSize);
    }

    function captureFrame() {
        const context = snapshotElement.getContext('2d');
        context.drawImage(videoElement, 0, 0, snapshotElement.width, snapshotElement.height);
        const frame = snapshotElement.toDataURL('image/jpeg');
        sendFrameToBackend(frame);
        drawDetections();
    }

    async function sendFrameToBackend(frame) {
        try {
			const response = await fetch('http://localhost:8000/detect', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({ image: frame})
			});
			const data = await response.json();
			detectionResults = data;
		} catch (error) {
			console.error('Error sending frame to backend:', error);
		}
    }

    function drawDetections() {
		const context = annotationsElement.getContext('2d');
		context.clearRect(0, 0, annotationsElement.width, annotationsElement.height);

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
</script>

<style>
    .video-container {
        position: relative;
    }
    .annotations-canvas {
        position: absolute;
        top: 0;
        left: 0;
    }
</style>

<div class="video-container">
    {#if !USE_WEBCAM}
        <video bind:this={videoElement} autoplay playsinline controls></video>
    {/if}
    {#if USE_WEBCAM}
        <video bind:this={videoElement} autoplay playsinline></video>
    {/if}
    <canvas bind:this={snapshotElement} style="display: none; pointer-events: none;"></canvas>
    <canvas bind:this={annotationsElement} class="annotations-canvas" style="pointer-events: none;"></canvas>
</div>