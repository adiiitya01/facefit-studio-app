// Check login state on page load
document.addEventListener('DOMContentLoaded', () => {
    const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
    const username = localStorage.getItem('username');
    const loginLink = document.getElementById('login-link');
    const logoutLink = document.getElementById('logout-link');
    const loginMessage = document.getElementById('login-message');
    const detectButton = document.getElementById('detect-button');

    if (isLoggedIn) {
        loginLink.style.display = 'none';
        logoutLink.style.display = 'inline';
        loginMessage.style.display = 'block';
        document.getElementById('logged-in-username').textContent = username;
        detectButton.disabled = false;
    } else {
        loginLink.style.display = 'inline';
        logoutLink.style.display = 'none';
        loginMessage.style.display = 'none';
        detectButton.disabled = true;
        alert('Please log in to detect your face shape.');
        window.location.href = 'login.html';
    }
});

// Logout functionality
document.getElementById('logout-link').addEventListener('click', function(e) {
    e.preventDefault();
    localStorage.removeItem('isLoggedIn');
    localStorage.removeItem('username');
    localStorage.removeItem('faceShape');
    localStorage.removeItem('lastRecommendations');
    alert('Logged out successfully!');
    window.location.href = 'login.html';
});

let detectedFaceShape = localStorage.getItem('faceShape');

function startFaceDetection() {
    const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
    if (!isLoggedIn) {
        alert('Please log in to detect your face shape.');
        window.location.href = 'login.html';
        return;
    }

    if (detectedFaceShape) {
        displayResults(detectedFaceShape);
        return;
    }

    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = 'image/*';
    fileInput.onchange = (e) => {
        const file = e.target.files[0];
        if (file) {
            showLoading();
            const reader = new FileReader();
            reader.onload = (event) => {
                const img = document.getElementById('face-preview');
                img.src = event.target.result;

                const formData = new FormData();
                formData.append('image', file);

                fetch('http://localhost:5000/analyze-face', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    hideLoading();
                    if (data.error) {
                        alert(data.error);
                        return;
                    }
                    detectedFaceShape = data.face_shape;
                    localStorage.setItem('faceShape', detectedFaceShape);
                    localStorage.setItem('lastRecommendations', JSON.stringify(data.recommendations));
                    displayResults(detectedFaceShape, data.recommendations);
                })
                .catch(error => {
                    hideLoading();
                    console.error('Error:', error);
                    alert('Failed to analyze face shape. Please ensure the backend server is running.');
                });
            };
            reader.readAsDataURL(file);
        }
    };
    fileInput.click();
}

function showLoading() {
    document.getElementById('loading').style.display = 'block';
    document.getElementById('detect-button').disabled = true;
}

function hideLoading() {
    document.getElementById('loading').style.display = 'none';
    document.getElementById('detect-button').disabled = false;
}

function displayResults(faceShape, recommendations) {
    const outline = document.getElementById('face-outline');
    const resultsDiv = document.getElementById('results');
    const faceShapeResult = document.getElementById('face-shape-result');
    const hairstyleResult = document.getElementById('hairstyle-result');
    const fashionResult = document.getElementById('fashion-result');
    const gogglesResult = document.getElementById('goggles-result');

    outline.style.display = 'block';
    resultsDiv.style.display = 'block';

    faceShapeResult.textContent = faceShape;
    hairstyleResult.textContent = recommendations?.hairstyle || 'No hairstyle recommendation';
    fashionResult.textContent = recommendations?.fashion_tip || 'No fashion tip';
    gogglesResult.textContent = recommendations?.goggles || 'No goggles recommendation';
}

function resetDetection() {
    detectedFaceShape = null;
    localStorage.removeItem('faceShape');
    document.getElementById('results').style.display = 'none';
    document.getElementById('face-outline').style.display = 'none';
    document.getElementById('face-preview').src = 'https://via.placeholder.com/150';
}