
function openModal() {
    document.querySelector('.cta-btn').style.display = 'none';  
    document.getElementById('assessment-modal').style.display = 'block';  
  }

  function closeModal() {
    document.querySelector('.cta-btn').style.display = 'inline-block';  
    document.getElementById('assessment-modal').style.display = 'none';  
  }

 
  async function takeAssessment() {
    const assessmentID = document.getElementById('assessment-id').value;
  
    if (assessmentID) {
      try {
        const response = await fetch('http://localhost:5000/api/validate-assessment', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ assessmentId: assessmentID }),
        });
  
        const data = await response.json();
  
        if (response.ok) {
          alert(data.message);
          window.location.href = 'face-recognition.html'; // Redirect to face recognition
        } else {
          alert(data.message); // Show the backend error message
        }
      } catch (error) {
        console.error('Error:', error);
        alert('Failed to connect to the server. Please try again later.');
      }
    } else {
      alert('Please enter an Assessment ID.');
    }
  }
  