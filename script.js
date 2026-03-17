let currentSlide = 1;
const totalSlides = 5;

// Feature names in order (matching the 20 features in Demo.py)
const featureNames = [
    'PL_enq_L12m',
    'time_since_recent_enq',
    'tot_enq',
    'CC_enq_L12m',
    'HL_Flag',
    'PL_Flag',
    'CC_Flag',
    'pct_of_active_TLs_ever',
    'time_since_recent_deliquency',
    'recent_level_of_deliq',
    'num_times_delinquent',
    'max_delinquency_level',
    'num_deliq_12mts',
    'num_times_60p_dpd',
    'AGE',
    'Time_With_Curr_Empr',
    'max_unsec_exposure_inPct',
    'pct_currentBal_all_TL',
    'PL_utilization',
    'CC_utilization'
];

function updateProgress() {
    const progress = (currentSlide / totalSlides) * 100;
    document.getElementById('progressBar').style.width = progress + '%';
    document.getElementById('currentStep').textContent = currentSlide;
}

function showSlide(slideNumber) {
    // Hide all slides
    const slides = document.querySelectorAll('.slide');
    slides.forEach(slide => {
        slide.classList.remove('active');
    });
    
    // Show current slide
    const currentSlideElement = document.getElementById('slide' + slideNumber);
    if (currentSlideElement) {
        currentSlideElement.classList.add('active');
    }
    
    updateProgress();
}

function nextSlide() {
    if (validateCurrentSlide()) {
        if (currentSlide < totalSlides) {
            currentSlide++;
            showSlide(currentSlide);
        }
    }
}

function prevSlide() {
    if (currentSlide > 1) {
        currentSlide--;
        showSlide(currentSlide);
    }
}

function validateCurrentSlide() {
    const currentSlideElement = document.getElementById('slide' + currentSlide);
    const inputs = currentSlideElement.querySelectorAll('input, select');
    
    let isValid = true;
    inputs.forEach(input => {
        if (input.value === '' || input.value === null) {
            input.style.borderColor = '#ff6b6b';
            isValid = false;
        } else {
            input.style.borderColor = '#e0e0e0';
        }
    });
    
    if (!isValid) {
        alert('Please fill in all fields before proceeding.');
    }
    
    return isValid;
}

function collectFormData() {
    const formData = {};
    
    featureNames.forEach(featureName => {
        const input = document.getElementById(featureName);
        if (input) {
            const value = input.value;
            // If empty, send empty string (app.py will convert to NaN)
            formData[featureName] = value === '' ? '' : parseFloat(value);
        } else {
            // Feature not found, send empty string
            formData[featureName] = '';
        }
    });
    
    return formData;
}

async function submitForm() {
    if (!validateCurrentSlide()) {
        return;
    }
    
    // Show loading overlay
    document.getElementById('loadingOverlay').classList.add('active');
    
    const formData = collectFormData();
    
    try {
        const response = await fetch('/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        
        const result = await response.json();
        
        // Hide loading overlay
        document.getElementById('loadingOverlay').classList.remove('active');
        
        // Display results
        displayResults(result);
        
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('loadingOverlay').classList.remove('active');
        alert('Error calculating credit score. Please make sure the server is running on http://localhost:5000');
    }
}

function displayResults(result) {
    const score = result.Predicted_Credit_Score;
    const riskCategory = result.Risk_Category;
    
    // Update score display
    document.getElementById('scoreNumber').textContent = score;
    
    // Update risk badge
    const riskBadge = document.getElementById('riskBadge');
    riskBadge.textContent = riskCategory;
    
    // Remove all risk classes
    riskBadge.classList.remove('high-risk-badge', 'medium-risk-badge', 'low-risk-badge', 'very-low-risk-badge');
    
    // Add appropriate risk class
    if (riskCategory === 'High Risk') {
        riskBadge.classList.add('high-risk-badge');
    } else if (riskCategory === 'Medium Risk') {
        riskBadge.classList.add('medium-risk-badge');
    } else if (riskCategory === 'Low Risk') {
        riskBadge.classList.add('low-risk-badge');
    } else if (riskCategory === 'Very Low Risk') {
        riskBadge.classList.add('very-low-risk-badge');
    }
    
    // Hide all slides and show result slide
    const slides = document.querySelectorAll('.slide');
    slides.forEach(slide => {
        slide.classList.remove('active');
    });
    
    document.getElementById('resultSlide').classList.add('active');
    
    // Update progress bar to 100%
    document.getElementById('progressBar').style.width = '100%';
}

function restartForm() {
    // Reset all inputs
    const inputs = document.querySelectorAll('input, select');
    inputs.forEach(input => {
        input.value = '';
        input.style.borderColor = '#e0e0e0';
    });
    
    // Reset to first slide
    currentSlide = 1;
    showSlide(currentSlide);
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    showSlide(1);
    
    // Add enter key support for inputs
    document.querySelectorAll('input').forEach(input => {
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                if (currentSlide < totalSlides) {
                    nextSlide();
                } else {
                    submitForm();
                }
            }
        });
    });
});
